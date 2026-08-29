# aicoding/mylib — shared skill & paper library

## Canonical library root

- The only maintained source root is `D:/aicoding/mylib`.
- The legacy sibling directory named `Lib` is retired and must not be used by runtime links, scripts, or documentation.
- User-level Codex skills are installed as junctions into curated sources under this repository.

## Patent application toolkit

- Entry: `paa/README.md` and `paa/SKILL.md`
- Portable skills: `paa/skills/`
  - `cn-patent-application-cluster` — Codex-native CNIPA mining, drafting, review, and packaging workflow
  - `incopat-search` — real incoPat prior-art retrieval
  - `patent-grant-scorer` — AHP+SEM grant-readiness scoring
  - `cnipa-drafting-workflow` — CNIPA drafting and examiner-loop workflow
  - `patent-disclosure-skill` — project material to technical-disclosure workflow
- Companion Codex agents: `paa/agents/cn-patent-*.toml`
- Inventory, installation paths, provenance, and secret-handling rules: `paa/PATENT_TOOLKIT.md`
- Patent-specific plugin scan: `paa/plugins/README.md`

The library contains templates and code only. Runtime credentials, `.env`
files, incoPat token caches, and local account files are intentionally excluded.

## ResearchStudio-Idea (arXiv:2607.04439)
- Code: `ResearchStudio/` (sparse/full clone of microsoft/ResearchStudio)
- Skill source: `ResearchStudio/ResearchStudio-Idea`; Codex installs only the three selected leaf skills.
- Paper PDF: `papers/ResearchStudio-Idea_2607.04439.pdf`
- Agent skill junctions: `~/.claude/skills/{idea_spark,paper_search,scoop_check}`

Method used by powergrid journal distill: outcome-grounded **pattern cards**
(definition / operational signature / when-to-apply / evidence expectations /
failure modes), paper tagging, and journal-level composition profiles.

## RepLLM (arXiv:2509.21074, SIGCOMM 2026)
- Paper PDF: `papers/RepLLM_2509.21074.pdf`
- Library entry: `RepLLM/` (skill + CPA schema; **upstream code not public**)
- Skill source: `RepLLM/`.
- Agent skill: `~/.claude/skills/repllm-content-parse` (junction)

Powergrid reuse: **Content Parsing only** → structured `paper.json` evidence
geometry for journal distill (`repllm_cpa_journal_distill.py`). Do **not** mass-run
Architecture/Code/Audit agents on the OA journal corpus.

## HarnessBank (arXiv:2607.13683, EverMind)
- Paper PDF: `papers/HarnessBank_2607.13683.pdf`
- Library entry: `HarnessBank/` (skill + powergrid adapt note; **upstream code not released yet**)
- Skill source: `HarnessBank/`.
- Agent skill: `~/.claude/skills/harnessbank-gated-evolution` (junction)

Powergrid reuse: **gated credit + WHERE×WHY gene bank** for evolving research-agent
harnesses (prompts/tools/runtime/recovery), not as a paper-drafting engine. See
`HarnessBank/powergrid_adapt_note.md`.

## Auto-Empirical-Research-Skills (AERS)
- Repo: `Auto-Empirical-Research-Skills/` (cloned from `brycewang-stanford/Auto-Empirical-Research-Skills`)
- Scope: very large catalog (skills + tools + workflows) for empirical research.
- Integration strategy: **selective absorption**, not full import.
- Bridge skill: `skills/AERS-powergrid-bridge/SKILL.md`

Useful absorbed modules for paper writing:
- literature tooling orchestration (`71 ... literature-review-tools`)
- citation verification (`62 ... citation-checker`)
- figure/table audit (`54 ... figure-table-audit`)
- bilingual de-AIGC (`48 ... de-AIGC-skills`)
- optional post-draft pipeline orchestrator (`67 ... paper-pipeline`)

## Graph Wiki
- Entry: `LLM_Wiki/README.md`
- Graph: `LLM_Wiki/graph.md`
- Nodes: `LLM_Wiki/nodes.md`
- Playbooks: `LLM_Wiki/playbooks.md`

## Powergrid paper capabilities (mirrored from project)
- `Paper_CCF/` — journal skills (copy of `~/.claude/skills/Paper_CCF`)
- `ARA/` — ARA orchestration skill
- `powergrid_paper/` — literature scripts, distill metadata, CMC style, journal templates
- Details: `powergrid_paper/README.md`
- Note: PDF corpora remain in `D:/aicoding/powergrid_benchmark/papers/literature/` (not mirrored)

## Codex + Academic Research Skills (ARS)
- Digest: `Codex-Academic-Research/` (姿势 + ARS 用法 + 电网 playbooks)
- Upstream suite: `Academic-Research-Skills-Codex/` → skill `academic-research-suite` (v0.1.24)
- Installed: `~/.codex/skills/academic-research-suite` and `~/.claude/skills/academic-research-suite`
- Bridge: `skills/codex-ars-powergrid/SKILL.md`
- Verify: new chat should list **one** ARS entry named `academic-research-suite`

## Claude user-level skills backup
- `claude-user-skills/` — mirror of `~/.claude/skills/` (9 skills: ARA/paper ×4,
  proposal ×3, anysearch, codex-review-loop), synced 2026-08-25
- Credentials excluded: `anysearch/.env` intentionally not mirrored

## Codex user-level backup
- `codex-user-skills/` — mirror of `~/.codex/skills/` (42 skills), synced 2026-08-25
- `codex-user-agents/` — mirror of `~/.codex/agents/` (18 role prompts), synced 2026-08-25
- Credentials excluded: `~/.codex/{auth.json,secrets/,cap_sid}` never mirrored

## Claude plugins backup
- `claude-plugins/` — `superpowers/` plugin + `marketplaces/`
  (claude-plugins-official, ralph-loop-setup) + install index JSONs, synced 2026-08-25
- Runtime cache (`plugins/cache/`) excluded
