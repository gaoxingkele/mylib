---
name: paa-patent-toolkit
description: Route PAA, PatentARA, patent grant scoring, incoPat, and NPL academic-search work to the mylib toolkit. Use when a task explicitly mentions PAA, PatentARA, grant-score validation, PAA artifacts/gates, incoPat integration, or NPL prior-art search; load only the required module.
---

# PAA patent toolkit router

The single source of truth is this repo (`D:/aicoding/mylib`). Every tool
endpoint (Claude Code / Codex / Kimi) junctions into it — never copy skills
into per-tool directories. Load only the module needed for the current task.

## Module map

| Need | Read |
|---|---|
| PAA artifact structure, gates, seals, validation | `paa/SKILL.md`, then the directly named file under `paa/references/` |
| incoPat search/API/permissions | `paa/skills/incopat-search/SKILL.md` |
| AHP/SEM grant score | `paa/skills/patent-grant-scorer/SKILL.md` |
| CNIPA drafting workflow | `paa/skills/cnipa-drafting-workflow/SKILL.md` |
| Patent disclosure extraction | `paa/skills/patent-disclosure-skill/SKILL.md` |
| NPL prior-art routing (papers as references) | `paa/skills/npl-prior-art-search/SKILL.md` |
| Full application cluster internals | `paa/skills/cn-patent-application-cluster/SKILL.md` |
| PatentARA engine or integration | `paa/engine/patent_ara/README.md`, then only the relevant source/test |
| Academic search skills | `skills/<name>/SKILL.md` (academic-search, paper-search-pro, paper_search, papers-skill, scholar-search, literature-search, …) |
| Specialist agent behavior | the matching file under `paa/agents/` |

## Retrieval policy

- Patent leg: incoPat API first (real data, no fabricated pn).
- NPL leg: route via `paa/skills/npl-prior-art-search/SKILL.md` — multi-source
  sweep by default, Chinese/CCF via academic-search, deep scans via
  paper-search-pro, citation tracing via scholar-search/openalexcli.
- Agent prior-art review may additionally use Tavily and Brave for public-web
  discovery when their API keys are available.
- Keep search snippets `source-degraded`; do not use them as verified patent
  text or invent publication numbers.
- Record provider/query/URL or endpoint/code/message so provider failures and
  quota exhaustion remain auditable.

## Editing policy

When changing mylib, inspect callers first, use portable paths and interpreter
commands, preserve credentials outside version control, and run the closest
validator/tests after the change.
