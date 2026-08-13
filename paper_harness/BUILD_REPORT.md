# paper_harness Build Report

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
python D:\aicoding\Lib\paper_harness\tests\test_smoke.py
```

Result: 10 tests passed in mock mode, including Hard Gate negative tests, sequential stage control, monorepo worktree
resolution, untracked-manuscript refusal, full review coverage, and missing-graphic detection.

Known operational boundary: existing untracked paper directories must be placed under an explicitly committed Git
baseline before `run`; read-only `review` remains available before that step.
