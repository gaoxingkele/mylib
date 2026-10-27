# C-MARS g7 stable replay (cross-repo release card)

## Identity

- Parent harness: C-MARS seed `h0` / `blind_only_v0` at agent_framework `3818948` lineage tip `e8c5870` (handoff `docs/handoff-2026-10-25.md`).
- Candidate id: `g7_stable_replay`.
- Harness id: `blind_inquiry_strict_v0`.
- Scope: review-runtime release only. Does not rewrite Paper Harness stage plans, LaTeX builds, or manuscript prose.
- Linked hosts in this repo: `paper_harness` (protocol), `proposal-writing` (`validate_review_basis.py`), `paa/agents/cn-patent-examiner.toml`.

## Mutable surface

Accepted stack after seven single-surface rounds (Evaluator and ReviewSpec digests frozen):

- Skill: inquiry on score-span conflict; proposal basis applicability; patent claim-term anchors.
- Harness: `enable_inquiry=true`, `inquiry_score_span=1.0`.
- Context: `compress_context=false` (settled-claim deletion rejected at Gen-4).
- Agent: `novelty_strict=false` (strict-novelty over-reach rejected at Gen-1).

Frozen ReviewSpec digests (agent_framework):

| Scenario | Example | Digest prefix |
| --- | --- | --- |
| Paper | `reviewspec/examples/computer_science_paper.yaml` | `3667cb2b…` |
| Proposal | `reviewspec/examples/research_proposal_seed_grant.yaml` | `91673305…` |
| Patent | `reviewspec/examples/cn_patent_application.yaml` | `60f88bc0…` |

## Pathology and repair

Pathology tuples repaired along the release chain:

1. `(agent, indiscriminate novelty accusations)` → rejected; keep non-strict novelty.
2. `(skill/harness, missing conflict-triggered inquiry)` → accept inquiry + span 1.0.
3. `(context, drop settled claims and erase disagreement edges)` → rejected; keep full claim context.
4. `(skill, proposal hard requirements from guidance-standard metadata)` → accept basis skill gated by `validate_review_basis.py`.
5. `(skill, claim terms without paragraph/drawing/embodiment anchors)` → accept patent anchor skill.

## Gate ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| Validity (synthetic paper outer) | PASS | Released outer paper validity 0.727 → 1.0; Gen-7 holds 1.0. |
| Proposal basis outer | PASS | Naive fixture 0 → skilled fixture 1 via mylib `validate_review_basis.py`. |
| Patent anchor outer | PASS | Synthetic anchor fixture 0 → 1. |
| Invariance | PASS | `invariance_ok=1.0` on accepted releases. |
| Convergence | PASS | Generations 6 and 7 released outer `{paper,proposal,patent}` identical. |
| ReviewSpec / Evaluator freeze | PASS | `reviewspec_changed=false`; no evaluator-surface mutation. |
| Paired-z / significance | NOT APPLICABLE | Deterministic heuristic chain, not a replicated LLM benchmark. |
| Reportable external bench | NOT ESTABLISHED | Scores are synthetic / fixture; PeerReview Bench miniset remains `reportable: false`. |

## Bank decision

Admit as a **cross-repo methodology elite** for review-runtime SPRA: default starting release when evolving C-MARS from mylib hosts.

Do **not** treat as a global paper-writing default inside Paper Harness stages until a held-out PeerReview Bench (or equivalent) outer gate is reportable and the disagreement-preserving context candidate is re-scored on that gate.

Replay: `C:\aicoding\agent_framework` → `run_pipeline(..., generations=7)` → `converged=true`, candidate `g7_stable_replay`.
