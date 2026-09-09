[CmdletBinding()]
param(
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'manifest.json'),
    [string]$InstallRoot = (Join-Path $env:USERPROFILE '.grok\skills'),
    [string]$ProjectRoot = ''
)

# Install patent-family junctions into Grok skill roots.
# User: ~/.grok/skills  (grok_user_skills in manifest.json)
# Project: <repo>/.grok/skills  (paa router + project_only)
# Never junction the whole paa/ tree — recursive SKILL.md discovery would duplicate nested skills.

$ErrorActionPreference = 'Stop'

function Get-FullPath {
    param([Parameter(Mandatory)][string]$Path, [string]$BasePath)
    if ([IO.Path]::IsPathRooted($Path)) {
        return [IO.Path]::GetFullPath($Path)
    }
    return [IO.Path]::GetFullPath((Join-Path $BasePath $Path))
}

function Assert-PathUnderRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root
    )
    $rootPrefix = $Root.TrimEnd('\') + '\'
    if (-not $Path.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify a link outside the mylib source boundary: $Path"
    }
}

function Remove-MylibLink {
    param(
        [Parameter(Mandatory)][string]$LinkPath,
        [Parameter(Mandatory)][string]$RepoRoot
    )
    if (-not (Test-Path -LiteralPath $LinkPath)) {
        return $false
    }

    $item = Get-Item -LiteralPath $LinkPath -Force
    if ($item.LinkType -notin @('Junction', 'SymbolicLink')) {
        throw "Refusing to replace a real directory or file: $LinkPath"
    }

    $rawTarget = [string]$item.Target[0]
    $target = Get-FullPath -Path $rawTarget -BasePath $item.Parent.FullName
    Assert-PathUnderRoot -Path $target -Root $RepoRoot
    if ($item.PSIsContainer) {
        [IO.Directory]::Delete($LinkPath, $false)
    }
    else {
        [IO.File]::Delete($LinkPath)
    }
    return $true
}

function Install-JunctionSet {
    param(
        [Parameter(Mandatory)][string]$InstallRootFull,
        [Parameter(Mandatory)]$Entries,
        [Parameter(Mandatory)][string]$RepoRoot
    )

    if (-not (Test-Path -LiteralPath $InstallRootFull)) {
        New-Item -ItemType Directory -Path $InstallRootFull | Out-Null
    }

    $created = @()
    $kept = @()
    foreach ($entry in $Entries) {
        $linkPath = Join-Path $InstallRootFull $entry.Name
        if (Test-Path -LiteralPath $linkPath) {
            $item = Get-Item -LiteralPath $linkPath -Force
            if ($item.LinkType -notin @('Junction', 'SymbolicLink')) {
                throw "Install path is occupied by a real directory or file: $linkPath"
            }
            $currentTarget = Get-FullPath -Path ([string]$item.Target[0]) -BasePath $item.Parent.FullName
            if ($currentTarget.Equals($entry.Source, [StringComparison]::OrdinalIgnoreCase)) {
                $kept += $entry.Name
                continue
            }
            Remove-MylibLink -LinkPath $linkPath -RepoRoot $RepoRoot | Out-Null
        }

        New-Item -ItemType Junction -Path $linkPath -Target $entry.Source | Out-Null
        $created += $entry.Name
    }
    return [pscustomobject]@{ Created = $created; Kept = $kept }
}

$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifestDir = Split-Path -Parent $manifestFile
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $manifestDir '..')).Path
$installRootFull = [IO.Path]::GetFullPath($InstallRoot)
$manifest = Get-Content -LiteralPath $manifestFile -Encoding utf8 -Raw | ConvertFrom-Json

$wanted = @()
if ($null -ne $manifest.grok_user_skills) {
    $wanted = @($manifest.grok_user_skills)
}

$resolvedSkills = @()
foreach ($entry in $manifest.skills) {
    $name = [string]$entry.name
    if ($wanted.Count -gt 0 -and $wanted -notcontains $name) {
        continue
    }
    $source = Get-FullPath -Path ([string]$entry.source) -BasePath $manifestDir
    Assert-PathUnderRoot -Path $source -Root $repoRoot
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Skill source does not exist: $source"
    }
    $skillFile = Join-Path $source 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Skill source has no SKILL.md: $source"
    }
    $resolvedSkills += [pscustomobject]@{ Name = $name; Source = $source }
}

$userResult = Install-JunctionSet -InstallRootFull $installRootFull -Entries $resolvedSkills -RepoRoot $repoRoot

Write-Output "Grok user skill links repaired."
Write-Output "Install root: $installRootFull"
Write-Output "Kept: $($userResult.Kept.Count); created/repointed: $($userResult.Created.Count)"
if ($userResult.Created.Count -gt 0) { Write-Output ("Created/repointed: " + ($userResult.Created -join ', ')) }

if (-not $ProjectRoot) {
    $cwd = (Get-Location).Path
    if ((Test-Path -LiteralPath (Join-Path $cwd 'CLAUDE.md')) -and (Test-Path -LiteralPath (Join-Path $cwd 'knowledge'))) {
        $ProjectRoot = $cwd
    }
}

if ($ProjectRoot) {
    $projectRootFull = [IO.Path]::GetFullPath($ProjectRoot)
    $projectSkillsRoot = Join-Path $projectRootFull '.grok\skills'
    $projectEntries = @()

    $paaRouter = Get-FullPath -Path 'routers/paa' -BasePath $manifestDir
    Assert-PathUnderRoot -Path $paaRouter -Root $repoRoot
    $projectEntries += [pscustomobject]@{ Name = 'paa'; Source = $paaRouter }

    foreach ($entry in $manifest.project_only) {
        $source = Get-FullPath -Path ([string]$entry.source) -BasePath $manifestDir
        Assert-PathUnderRoot -Path $source -Root $repoRoot
        $projectEntries += [pscustomobject]@{ Name = [string]$entry.name; Source = $source }
    }

    $projectResult = Install-JunctionSet -InstallRootFull $projectSkillsRoot -Entries $projectEntries -RepoRoot $repoRoot
    Write-Output "Grok project skill links repaired."
    Write-Output "Project root: $projectSkillsRoot"
    Write-Output "Kept: $($projectResult.Kept.Count); created/repointed: $($projectResult.Created.Count)"
    if ($projectResult.Created.Count -gt 0) { Write-Output ("Created/repointed: " + ($projectResult.Created -join ', ')) }
}
