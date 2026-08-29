# paper_harness Build Report

## Version 0.2.5 — 2026-08-13

### Locked legacy incident preservation

- adds an explicit `retry --preserve-locked-worktree` mode;
- records the excluded incident directory and a retry nonce in the timeline;
- derives a fresh Windows worktree target without deleting the locked site;
- full smoke suite: 18 passing tests.

## Version 0.2.4 — 2026-08-13

### Isolated-source acceptance environment

- custom Python checks prepend an existing `<worktree>/src` to `PYTHONPATH`;
- candidate checks no longer depend on the main checkout or global package state;
- a regression test imports a package available only inside the worktree;
- full smoke suite: 17 passing tests.

## Version 0.2.3 — 2026-08-13

### Timeout process-tree containment

- launches each real transport call in a distinct process group/session;
- terminates only that controlled process tree after a transport timeout;
- prevents timed-out Codex runner descendants from retaining worktree handles;
- adds a regression test for tree cleanup; full smoke suite: 16 passing tests.

This change is prospective. It does not force-terminate or clean any pre-existing
orphan process or paper worktree.

## Version 0.2.2 — 2026-08-13

### Deep-optimization recovery additions

- separated sparse-checkout `read_only_paths` from `allowed_write_paths`;
- made the Codex stage timeout configurable with `PAPER_HARNESS_CODEX_TIMEOUT`;
- added a repository-level cross-process lock for serialized `accept` merges;
- codified timed-out WIP patch exclusion and scientific-field rerun comparison;
- expanded the smoke suite to 15 passing tests.

## Version 0.2.0 — 2026-08-13

Experience distilled from MA-SQLGrid, C²GES, and the six Mintou manuscript audits was converted into an explicit
evidence-alignment contract and reviewer protocol.

Implemented changes:

- full-manuscript review coverage with manuscript SHA and structured issue/claim matrices;
- monorepo-aware Git worktrees and collision-free branch names;
- preflight refusal for untracked or dirty paper baselines;
- exactly one candidate stage at a time;
- automatic candidate commit after checks and cross-paper-scope drift rejection;
- corrected nested-manuscript LaTeX working directory;
- manuscript-scoped placeholder checks instead of recursive archive scanning;
- narrative structure, graphic, PDF, and mojibake/meta-narrative checks;
- strict refusal to approve a plan modified after registration;
- updated planner/executor/attribution prompts with non-fabrication and evidence-boundary rules.

Verification command:

```powershell
python D:\aicoding\mylib\paper_harness\tests\test_smoke.py
```

Result: 12 tests passed in mock mode, including Hard Gate negative tests, sequential stage control, monorepo sparse
worktree resolution, explicit failure retry, live-run lease preservation, untracked-manuscript refusal, full review
coverage, and missing-graphic detection.

Known operational boundary: existing untracked paper directories must be placed under an explicitly committed Git
baseline before `run`; read-only `review` remains available before that step.
