# Adapter: Grok Build (xAI)

Grok discovers skills, agents, commands, and workflows from both its own
`.grok/` trees and Claude-compatible `.claude/` trees. Do **not** copy skill
bodies into Grok directories. Junction the mylib sources, the same way Codex
and Claude do.

## What Grok already loads from this patent repo

| Kind | Path | Notes |
|---|---|---|
| Project rules | `CLAUDE.md`, `.grok/rules/` | Always on |
| Slash commands | `.claude/commands/patent.md`, `evolve-patent-system.md` | `/patent`, `/evolve-patent-system` |
| Specialist agents | `.claude/agents/*.md` | `spawn_subagent` types: `patent-orchestrator`, `disclosure-analyst`, `prior-art-researcher`, `claim-drafter`, `specification-drafter`, `drawings-planner`, `abstract-drafter`, `terminology-keeper`, `quality-reviewer`, `patentability-examiner`, `patent-evolver` |
| Claude-compat skills | `.claude/skills/*` junctions | High priority; `paa` here currently points at the **full** `mylib/paa` tree |
| Native Grok skills | `~/.grok/skills/*` and `<repo>/.grok/skills/*` | Installed by `skill-runtime/repair_grok_skills.ps1` |
| Workflow | `<repo>/.grok/workflows/cn-patent.rhai` | `/cn-patent` or `/workflow cn-patent` |

Grok deduplicates skills by name. Project `.grok/skills/paa` (the lightweight
router) **must** shadow `.claude/skills/paa` (the full tree) so recursive
discovery does not register every nested `paa/skills/*/SKILL.md` twice.

## Installation

From this repo, or any directory that contains `CLAUDE.md` + `knowledge/`:

```powershell
& D:/aicoding/mylib/skill-runtime/repair_grok_skills.ps1 -ProjectRoot D:/aicoding/zhuanlishenqing
```

This creates junctions only (never copies):

- User: `~/.grok/skills/{paa,incopat-search,cnipa-drafting-workflow,patent-disclosure-skill,patent-grant-scorer,npl-prior-art-search,claims-drafting,specification-writing,patent-pipeline}`
- Project: `<repo>/.grok/skills/{paa,cn-patent-application-cluster,paa-patent-toolkit}`

`paa` at both scopes points at `mylib/skill-runtime/routers/paa`, **not** the
whole `mylib/paa` directory.

## Invocation

- **One-shot slash:** `/patent <案件名> [disclosure|draft|review|finalize|paa]`
- **Deterministic fan-out:** `/cn-patent` with `args.case_name` (optional `args.stage`)
- **Say it in Chinese:** 「帮我写专利」「草拟权利要求」「PAA 打包」— Grok should
  load `cnipa-drafting-workflow` / `paa` and spawn the specialist agents
- **Prior art:** `incopat-search` (real API) + `npl-prior-art-search` (papers)

## Grok-specific operating rules

1. **Parent is the orchestrator.** Grok subagents cannot spawn subagents
   (depth = 1). Do **not** spawn `patent-orchestrator` as a child and expect it
   to call the other experts. The main session (or the `cn-patent` workflow)
   calls `disclosure-analyst` → `prior-art-researcher` → `claim-drafter` → …
   directly.
2. **Python:** `D:/Python/Python314/python.exe`. The Microsoft Store `python`
   stub is unusable. Some skill docs still say `D:/Python314/python.exe`;
   rewrite that path when executing.
3. **incoPat:** `D:/aicoding/mylib/paa/skills/incopat-search/scripts/incopat_api.py`
   with credentials in that folder's gitignored `credentials.json`.
4. **PAA validate:**
   `D:/Python/Python314/python.exe D:/aicoding/mylib/paa/scripts/validate.py output/<案件>/paa`
5. **Static claim check:**
   `D:/Python/Python314/python.exe D:/aicoding/mylib/paa/skills/cn-patent-application-cluster/scripts/patent_static_check.py <draft.md>`
6. **No fabricated publication numbers.** Every cited pn needs
   `evidence/prior_art_search/<pn>.json` from a real API response.

## Tool mapping (Claude agent frontmatter → Grok)

Claude agent files keep their original `tools:` / `model:` frontmatter. Grok
ignores unknown model ids (`opus`/`sonnet`) and inherits the parent model.
Map Claude tool names when reading those files:

| Claude | Grok |
|---|---|
| Read / Glob | `read_file`, `list_dir` |
| Grep | `grep` |
| Write / Edit | `write`, `search_replace` |
| Bash | `run_terminal_command` |
| WebSearch / WebFetch | `web_search`, `web_fetch` |
| Agent / Task | `spawn_subagent` (parent only) |
| TodoWrite | `todo_write` |

## Validation after a compile

- Every cited pn has `evidence/prior_art_search/<pn>.json`
- `validate.py` four gates pass
- `patent_static_check.py` / `claim_formal_check.py` on the claims draft
