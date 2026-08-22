# Adapter: Claude Code

The Claude Code adapter is `./SKILL.md` at the skill root. It follows Claude Code's standard SKILL.md
format with YAML frontmatter:

```yaml
---
name: paa
description: |
  PAA (Patent Application Artifact) ...
allowed-tools: Read, Write, Edit, Bash(python *|git *|ls *|mkdir *), Glob, Grep, Task
---
```

When placed in `~/.claude/skills/paa/` (or `.claude/skills/paa/` in a project), Claude Code will
automatically discover and load `SKILL.md` when the user invokes `/paa`.

## Invocation patterns

- **Slash command**: `/paa` then agent reads README.md, references/, etc.
- **Direct invocation**: user requests "build a PAA" or "validate my patent drafting" and the agent
  picks up this skill via trigger keywords in the description.

## Customization

If you want different allowed-tools, override at the SKILL.md frontmatter. The core content is in
`./README.md` — load that as instructions.