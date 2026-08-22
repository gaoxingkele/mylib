# Adapter: Codex CLI

For OpenAI Codex CLI, plugins follow a manifest-driven pattern. Below is the rough shape; check
the latest Codex CLI docs for the current schema.

## Manifest (e.g. `plugin.json`)

```json
{
  "name": "paa",
  "version": "1.0.0",
  "description": "Patent Application Artifact — patent-specific adaptation of ARA with four hard gates",
  "instructions_file": "./README.md",
  "tools": {
    "Bash": ["python *", "git *", "ls *", "mkdir *"],
    "Read": ["*"],
    "Write": ["*"],
    "Edit": ["*"],
    "Glob": ["*"],
    "Grep": ["*"]
  },
  "triggers": [
    "compile patent", "build patent artifact", "PAA", "patent四件套结构化",
    "专利撰写结构化", "patent application artifact"
  ],
  "entrypoints": {
    "compile": "./README.md",
    "validate": "./scripts/validate.py",
    "scaffold": "./scripts/scaffold.py"
  }
}
```

## Installation (approximate)

```bash
# Place the skill directory where Codex CLI scans
mkdir -p ~/.codex/skills/paa
cp -r <this-skill-dir>/* ~/.codex/skills/paa/
```

Then `codex plugin load paa` or similar (verify with Codex CLI docs).

## Behavior

When triggered, Codex CLI loads `./README.md` as the instructions, plus references/ on demand.
The scripts (`scaffold.py`, `validate.py`) are invoked via Bash.

## Note

This adapter's plugin.json is a template — verify the actual schema against your Codex CLI version.