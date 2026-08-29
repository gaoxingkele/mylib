# P1 Stage-6 post-build finalizer (project-local candidate)

## Identity

- Parent harness: Paper Harness at `bad680f` before this card's declaration-alias patch.
- Project: `powergrid_benchmark/paper_projects/mintou_p1_dstar_gru_dispatch`.
- Recovery plan: P1 `plan_v12`, stage `s6r4`.
- Accepted recovery commit: `90b11a03`; checkout-stability follow-ups: `a1211b59` and `d9020ff3`.
- Scope: release engineering only. Scientific results, prose, claims, figures, citations, and experiment decisions were frozen.

## Mutable surface

- Harness configuration: acceptance-check ordering.
- Project runtime: deterministic LaTeX environment, post-build release construction, render QA, and terminal validation.
- Project source-control policy: LF checkout attributes for text artifacts whose raw identity is gated.
- Scientific experiment and manuscript content were not mutable.

## Pathology and repair

Pathology tuple:

`(runtime/config, packaging before final latex_build + workspace-local MiKTeX state + checkout mtime/line-ending identity)`

Repair:

1. Run scientific-continuity checks before compilation.
2. Compile under fixed `SOURCE_DATE_EPOCH`, `FORCE_SOURCE_DATE`, and `TZ`.
3. Build the release payload only after the final compile.
4. Bind visual QA to the exact PDF SHA-256.
5. Independently re-render and verify every payload/source hash.
6. Use content hashes and ordered execution as provenance; do not use checkout mtimes.
7. Stabilize gated text artifacts with project-scoped LF attributes.

## Gate ledger

| Gate | Result | Evidence |
|---|---|---|
| Validity | PASS | Frozen scientific comparison passed; 2,310 result rows, 240 trajectories, five derived tables, and no non-timing scientific drift. |
| Activation | PASS | The repair removed real false failures in isolated Windows worktrees and produced a clean accepted Stage-6 candidate. |
| Deterministic build | PASS | Three fresh-checkout compilations were byte-identical at PDF SHA-256 `bb61e0b1b20a3e9192bc05c640eb8c8895b0b0c24d8f2255c56fd4c4ff983c5c`. |
| Artifact closure | PASS | Nine pages, 87 manifested source files, raw main/package PDF identity, raw main/package TeX identity, semantic-text identity, and independent render identity passed. |
| Paired-z / significance | NOT APPLICABLE | This was one sealed project recovery, not a replicated harness benchmark. No significance claim is licensed. |
| Train/held-out separation | NOT ESTABLISHED | P1 supplied the development incident and validation case; no independent held-out project has yet tested the repair. |

## Bank decision

Keep as a project-local recovery card and reusable design candidate. Do not admit it to a global elite/default bank until multiple independent projects activate the same pathology and a held-out comparison shows no regression in scientific-continuity, build, and artifact gates.
