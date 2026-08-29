[CmdletBinding()]
param(
    [string]$ManifestPath = (Join-Path $PSScriptRoot 'manifest.json'),
    [string]$InstallRoot = (Join-Path $env:USERPROFILE '.codex\skills')
)

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
        # PowerShell 7 can throw a NullReferenceException for Remove-Item on a Windows junction.
        # Directory.Delete(path, false) removes only the reparse point after the target check above.
        [IO.Directory]::Delete($LinkPath, $false)
    }
    else {
        [IO.File]::Delete($LinkPath)
    }
    return $true
}

$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifestDir = Split-Path -Parent $manifestFile
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $manifestDir '..')).Path
$installRootFull = [IO.Path]::GetFullPath($InstallRoot)
$manifest = Get-Content -LiteralPath $manifestFile -Encoding utf8 -Raw | ConvertFrom-Json

if (-not (Test-Path -LiteralPath $installRootFull)) {
    New-Item -ItemType Directory -Path $installRootFull | Out-Null
}

$resolvedSkills = @()
foreach ($entry in $manifest.skills) {
    $source = Get-FullPath -Path ([string]$entry.source) -BasePath $manifestDir
    Assert-PathUnderRoot -Path $source -Root $repoRoot
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Skill source does not exist: $source"
    }

    $skillFile = Join-Path $source 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) {
        throw "Skill source has no SKILL.md: $source"
    }

    $header = Get-Content -LiteralPath $skillFile -Encoding utf8 -TotalCount 40
    $nameLine = $header | Where-Object { $_ -match '^name\s*:' } | Select-Object -First 1
    $frontmatterName = (($nameLine -replace '^name\s*:\s*', '').Trim(' ', '"', "'"))
    if ($frontmatterName -cne [string]$entry.name) {
        throw "Manifest name '$($entry.name)' does not match frontmatter '$frontmatterName' at $skillFile"
    }

    $resolvedSkills += [pscustomobject]@{
        Name = [string]$entry.name
        Source = $source
    }
}

$removed = @()
foreach ($legacyName in $manifest.legacy_links) {
    $legacyPath = Join-Path $installRootFull ([string]$legacyName)
    if (Remove-MylibLink -LinkPath $legacyPath -RepoRoot $repoRoot) {
        $removed += [string]$legacyName
    }
}

$created = @()
$kept = @()
foreach ($entry in $resolvedSkills) {
    $linkPath = Join-Path $installRootFull $entry.Name
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
        Remove-MylibLink -LinkPath $linkPath -RepoRoot $repoRoot | Out-Null
    }

    New-Item -ItemType Junction -Path $linkPath -Target $entry.Source | Out-Null
    $created += $entry.Name
}

Write-Output "Codex skill links repaired."
Write-Output "Install root: $installRootFull"
Write-Output "Kept: $($kept.Count); created/repointed: $($created.Count); removed legacy/resource links: $($removed.Count)"
if ($created.Count -gt 0) { Write-Output ("Created/repointed: " + ($created -join ', ')) }
if ($removed.Count -gt 0) { Write-Output ("Removed: " + ($removed -join ', ')) }
