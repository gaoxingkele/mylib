# Patent Toolkit Inventory

> Updated: 2026-08-25
>
> Source project: `D:/aicoding/zhuanlishenqing`
>
> Source commit inspected: `ab7c88794a8befa926ea373775fde4063767f557`

## Included capabilities

| Type | Name | Library path | Purpose |
|---|---|---|---|
| Framework/skill | PAA | `paa/` | Four-layer patent application artifact with evidence and four hard gates |
| Codex skill | cn-patent-application-cluster | `paa/skills/cn-patent-application-cluster/` | CNIPA patent mining, drafting, review, and packaging |
| Claude-compatible skill | incopat-search | `paa/skills/incopat-search/` | Real incoPat search, claims, specification, legal and value APIs |
| Claude-compatible skill | patent-grant-scorer | `paa/skills/patent-grant-scorer/` | AHP+SEM grant-readiness assessment |
| Claude-compatible skill | cnipa-drafting-workflow | `paa/skills/cnipa-drafting-workflow/` | CNIPA drafting rules and examiner loop |
| Claude-compatible skill | patent-disclosure-skill | `paa/skills/patent-disclosure-skill/` | Project documents/code to technical disclosure |
| Codex role set | cn-patent-* | `paa/agents/` | Orchestrator, disclosure, prior-art, claim, specification, examiner, packager roles |
| Slash commands | patent, evolve-patent-system | `paa/commands/` | One-shot full-pipeline entry; system-evolution outer loop (`.claude/commands/`) |

The four pre-existing skills were compared to the source project on
2026-08-25. Their `SKILL.md` files and all safe source files were identical, so
they were retained without needless rewrites. The Codex-native cluster and its
seven companion role prompts were added in this sync.

## Codex installation

Copy the cluster and role prompts into a target repository:

```powershell
Copy-Item -Recurse paa/skills/cn-patent-application-cluster <repo>/.codex/skills/
Copy-Item paa/agents/cn-patent-*.toml <repo>/.codex/agents/
```

The `cn-patent-application-cluster` skill references the role prompts in the
project `.codex/agents/` directory, so install both parts.

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
