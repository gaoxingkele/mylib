# paa/engine — Provenance & Sync Policy

`paa/engine/patent_ara/` is a **vendored copy** of the PatentARA Python
pipeline. Upstream source of truth:

```
D:\aicoding\zhuanlishenqing\patent_ara
```

## Sync policy

- **Do not develop here.** Feature work and bugfixes land in the upstream
  working project first; this copy is refreshed wholesale afterwards.
- No credentials are vendored: Incopat/DeepSeek secrets are read at runtime
  from an external `credentials.json` / env vars (see engine README), and
  `credentials.json` is gitignored at repo root.

## Relationship to the rest of paa/

Two layers, same rules, different consumers — intentionally NOT merged:

| Concern | Spec layer (LLM workflow) | Engine layer (Python pipeline) |
|---|---|---|
| Four gates | `paa/scripts/validate.py` — static checks on the on-disk PAA directory | `patent_ara/gates.py` (GateKeeper) — runtime checks on the in-memory model + eval report |
| Incopat | `paa/skills/incopat-search/` — skill + CLI script | `patent_ara/incopat_integration.py` — OOP integrator with citation→element binding |
| AHP-SEM | `paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py` — standalone scorer | `patent_ara/scorer_integration.py` — delegates to the scorer via subprocess |
| Spec scaffolding | `paa/scripts/scaffold.py` | n/a (engine's `export_paa()` emits the same structure) |

The gate-rule overlap is deliberate defense-in-depth: the on-disk validator
must stay independent of whatever produced the artifact.

**If gate rules change (add/remove/redefine), update BOTH implementations in
the same change** — `validate.py` gates and `gates.py` GateKeeper must stay
rule-for-rule consistent.
