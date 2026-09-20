# Patent Toolkit Inventory

> Inventory created: 2026-08-25; paths and retrieval policy re-audited: 2026-08-27
>
> Source project: `D:/aicoding/zhuanlishenqing`
>
> Source commit inspected: `ab7c88794a8befa926ea373775fde4063767f557`

## Included capabilities

| Type | Name | Library path | Purpose |
|---|---|---|---|
| Framework/skill | PAA | `paa/` | Four-layer patent application artifact with evidence and four hard gates |
| Engine | PatentARA | `paa/engine/patent_ara/` | Claim decomposition, incoPat enrichment, element review, CNIPA gates, scoring, and PAA export |
| Codex skill | cn-patent-application-cluster | `paa/skills/cn-patent-application-cluster/` | CNIPA patent mining, drafting, review, and packaging |
| Claude-compatible skill | incopat-search | `paa/skills/incopat-search/` | Real incoPat search, claims, specification, legal and value APIs |
| Claude-compatible skill | patent-grant-scorer | `paa/skills/patent-grant-scorer/` | AHP+SEM grant-readiness assessment |
| Claude-compatible skill | cnipa-drafting-workflow | `paa/skills/cnipa-drafting-workflow/` | CNIPA drafting rules and examiner loop |
| Claude-compatible skill | patent-disclosure-skill | `paa/skills/patent-disclosure-skill/` | Project documents/code to technical disclosure |
| Claude-compatible skill | browser-multi-model-review | `paa/skills/browser-multi-model-review/` | Playwright MCP control of Gemini/ChatGPT/Grok/Perplexity for independent highest-model reviews |
| Codex role set | cn-patent-* | `paa/agents/` | Orchestrator, disclosure, prior-art, claim, specification, examiner, packager roles |
| Slash commands | patent, evolve-patent-system | `paa/commands/` | One-shot full-pipeline entry; system-evolution outer loop (`.claude/commands/`) |

The four pre-existing skills were compared to the source project on
2026-08-25. Their `SKILL.md` files and all safe source files were identical, so
they were retained without needless rewrites. The Codex-native cluster and its
seven companion role prompts were added in this sync.

## Codex installation

Prefer a lightweight project router that reads the required module directly
from `D:/aicoding/mylib/paa`. This avoids recursively exposing every nested
`SKILL.md` to the model context. If a standalone copy is required, copy only
the cluster and role prompts into the target repository:

```powershell
Copy-Item -Recurse paa/skills/cn-patent-application-cluster <repo>/.codex/skills/
Copy-Item paa/agents/cn-patent-*.toml <repo>/.codex/agents/
```

The `cn-patent-application-cluster` skill references the role prompts in the
project `.codex/agents/` directory, so install both parts.

For the maintained user-level runtime, run:

```powershell
& D:/aicoding/mylib/skill-runtime/repair_codex_skills.ps1
python D:/aicoding/mylib/skill-runtime/audit_skill_paths.py
```

The runtime installs a lightweight `paa` router and independent leaf skills; it never junctions the
whole `paa/` directory into the user skill root.

## Grok Build installation

Grok scans `.claude/skills` (compat) **and** `.grok/skills`. The Claude project
junction `.claude/skills/paa` still points at the full `paa/` tree for relative
paths; Grok would recursively register nested `SKILL.md` files. Install the
native Grok roots so the **router** wins by name:

```powershell
& D:/aicoding/mylib/skill-runtime/repair_grok_skills.ps1 -ProjectRoot <repo>
```

- User `~/.grok/skills/`: patent leaf skills listed in `skill-runtime/manifest.json` → `grok_user_skills`, plus the `paa` router (never the whole tree).
- Project `<repo>/.grok/skills/`: `paa` router + `cn-patent-application-cluster` + `paa-patent-toolkit`.
- Specialist agents stay in `<repo>/.claude/agents/` (Grok loads them as `spawn_subagent` types). Parent session orchestrates; children cannot nest.
- Workflow: `<repo>/.grok/workflows/cn-patent.rhai` (`/cn-patent`).
- Adapter: `paa/adapters/grok.md`.

Python on this machine is `D:/Python/Python314/python.exe`.

## Claude-compatible installation

Copy the desired skill directory into `<repo>/.claude/skills/` or the user's
Claude skills directory. Keep credentials local to the installed runtime.

## Plugin inventory

No patent-specific `.codex-plugin/plugin.json` or
`.claude-plugin/plugin.json` was present in the source project's project-level
or user-level plugin roots during the 2026-08-25 scan. No synthetic plugin was
created merely to satisfy packaging. See `paa/plugins/README.md`.

## Security boundary

The sync explicitly excludes:

- `.env` and `.env.*`;
- `credentials.json`;
- `.token_cache.json`;
- `__pycache__/` and `*.pyc`;
- nested `.git/` metadata.

`incopat-search/scripts/credentials.example.json` remains as a schema-only
template. Real credentials must never be committed.

## Verification

Run the Codex cluster's deterministic checks against a draft:

```powershell
python paa/skills/cn-patent-application-cluster/scripts/patent_static_check.py <draft.md>
python paa/skills/cn-patent-application-cluster/scripts/claim_formal_check.py <claims.md> --json
```

Validate a PAA artifact:

```powershell
python paa/scripts/validate.py <paa-case-dir>
```
