# C-MARS Gen-4 settled-claim curation (negative card)

## Identity

- Parent release: `g3_harness_tighter_trigger` (inquiry on, span 1.0).
- Candidate: `g4_context_settled_claim_curation` / `blind_inquiry_context_v0`.
- Surface: context.
- Source chain: agent_framework multi-scenario evolution (handoff 2026-10-25).

## Mutable surface

- `compress_context=true`: drop claims that already have evidence filed and are not critical.

## Pathology

`(context, drop settled claims and erase disagreement edges)` — removing archived evidence-bearing claims also removes the score-span conflict that triggers inquiry, so stale accusations survive and outer validity falls back toward the blind baseline (~0.727 from 1.0).

## Gate ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| Outer validity | FAIL | Rejected with `no improvement over baseline` relative to parent outer 1.0. |
| Rollback | YES | Released outer stayed at paper=1.0, proposal=0, patent=0 at that step. |

## Bank decision

Keep as a **negative / do-not-recombine** card. Next context mutations must **preserve disagreement edges** (conflict anchors, minority vetoes, open issues), not delete settled claims wholesale.
