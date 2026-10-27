# C-MARS Gen-1 strict novelty (negative card)

## Identity

- Parent release: baseline `h0`.
- Candidate: `g1_agent_strict_novelty` / `blind_strict_novelty_v0`.
- Surface: agent.
- Source chain: agent_framework multi-scenario evolution (handoff 2026-10-25).

## Mutable surface

- `novelty_strict=true`: every claim is treated as undifferentiated prior work.

## Pathology

`(agent, indiscriminate novelty accusations)` — raises a novelty issue on every claim instead of only on claims the artifact marks with `novelty_gap`.

## Gate ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| Outer validity | FAIL | Outer validity collapsed to ~0.12 vs parent ~0.73; reason `outer validity collapse relative to inner gate`. |
| Rollback | YES | Released outer scores unchanged after reject. |

## Bank decision

Keep as a **negative / do-not-recombine** card. Agent-surface improvements must be narrower than “flag all claims”.
