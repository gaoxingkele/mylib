---
name: paa-patent-toolkit
description: Route PAA, PatentARA, patent search, grant scoring, R&D initiation review, competitive landscape, technology-route comparison, company innovation assessment, and NPL work to the mylib toolkit. Use for PAA artifacts/gates, PatSnap/智慧芽, incoPat, prior-art search, 研发立项评审, 竞争格局, 技术路线对比, or 企业科创力评估; load only the required module.
---

# PAA patent toolkit router

The single source of truth is this repo (`D:/aicoding/mylib`). Every tool
endpoint (Claude Code / Codex / Kimi / Grok Build) junctions into it — never copy skills
into per-tool directories. Load only the module needed for the current task.
Grok: `~/.grok/skills` + project `.grok/skills` via `skill-runtime/repair_grok_skills.ps1`;
parent session orchestrates (Grok subagents cannot nest). See `paa/adapters/grok.md`.

## Module map

| Need | Read |
|---|---|
| PAA artifact structure, gates, seals, validation | `paa/SKILL.md`, then the directly named file under `paa/references/` |
| PatSnap/智慧芽 patent + paper search, original-text fetch, legal status | `paa/skills/patsnap-search/SKILL.md` |
| incoPat search/API/permissions | `paa/skills/incopat-search/SKILL.md` |
| Free patent search + original-text verification + seed-expansion pipeline (no key for search/fetch) | `paa/skills/google-patents-search/SKILL.md` |
| Specific project/proposal initiation, novelty boundary, innovation-point review | `paa/skills/rd-initiation-review/SKILL.md` |
| Multi-player discovery, competitor tiers, route matrix, whitespace analysis | `paa/skills/competitive-landscape/SKILL.md` |
| Route-set comparison, selection, TRL/maturity, opportunity scan | `paa/skills/tech-route-comparison/SKILL.md` |
| Single-company innovation assessment or technical due diligence via Company Intelligence MCP | `paa/skills/company-innovation-assessment/SKILL.md` |
| AHP/SEM grant score | `paa/skills/patent-grant-scorer/SKILL.md` |
| CNIPA drafting workflow | `paa/skills/cnipa-drafting-workflow/SKILL.md` |
| Patent disclosure extraction | `paa/skills/patent-disclosure-skill/SKILL.md` |
| NPL prior-art routing (papers as references) | `paa/skills/npl-prior-art-search/SKILL.md` |
| Playwright four-site browser review | `paa/skills/browser-multi-model-review/SKILL.md` |
| Full application cluster internals | `paa/skills/cn-patent-application-cluster/SKILL.md` |
| PatentARA engine or integration | `paa/engine/patent_ara/README.md`, then only the relevant source/test |
| Academic search skills | `skills/<name>/SKILL.md` (academic-search, paper-search-pro, paper_search, papers-skill, scholar-search, literature-search, …) |
| Specialist agent behavior | the matching file under `paa/agents/` |

Route by decision object: a concrete proposal → `rd-initiation-review`; multiple players →
`competitive-landscape`; two or more routes without a player focus → `tech-route-comparison`;
one legal entity's innovation capability → `company-innovation-assessment`. These research
reports do not replace claim-level prior-art search, FTO analysis, or PAA gates.

## Retrieval policy

- Patent leg: use `paa/skills/incopat-search/SKILL.md` and/or
  `paa/skills/patsnap-search/SKILL.md` according to credentials, interface scope, and coverage;
  important conclusions should use a second independent database where practical. **When these
  structured routes are unavailable or an independent re-search axis is needed, use
  `paa/skills/google-patents-search/SKILL.md`** — free, no key for search/fetch.
  That skill is **HTTP/API only (never browser automation)**: backend `google` (site JSON via
  curl_cffi), `patentscope` (WIPO official, keyless fallback), `tavily` (relay: pulls the same
  public page's full text / searches inside patents.google.com when the local egress is
  503-blocked by Google — needs `TAVILY_API_KEY`), `bigquery`
  (`patents-public-data`, Google's official programmatic route, needs GCP credentials).
  `gp_pipeline.py` runs the whole recall→fetch→verify chain from a seed publication:
  axes = seed citations / similar documents / BigQuery embedding neighbours / keyword,
  and it records every unavailable axis honestly instead of reporting "no prior art".
  That skill also owns the *original-text* gate: `gp_fetch.py` upgrades a hit to
  `evidence_level=original-text`, and `gp_verify.py` must return `all_verified=true` before any
  publication is quoted as X/Y/A prior art.
- NPL leg: use PatSnap paper search and route via
  `paa/skills/npl-prior-art-search/SKILL.md` — multi-source sweep by default, Chinese/CCF via
  academic-search, deep scans via paper-search-pro, citation tracing via scholar-search/openalexcli.
- Agent prior-art review may additionally use Tavily and Brave for public-web
  discovery when their API keys are available.
- Keep search snippets and model comparison output `source-degraded`; fetch original text before
  formal comparison or X/Y/A classification, and never invent publication numbers.
- Record provider/query/URL or endpoint/code/message so provider failures and
  quota exhaustion remain auditable. "Not found" never means "does not exist".

## Editing policy

When changing mylib, inspect callers first, use portable paths and interpreter
commands, preserve credentials outside version control, and run the closest
validator/tests after the change.
