# Regression direction set

Purpose: after any prompt/pipeline change, replay a FIXED set of directions that
differ in problem shape and confirm the pipeline still behaves correctly on
every shape — not just the shape the change was designed for. A change that
helps method-shaped ideas but breaks theory-shaped ones is a regression, not an
improvement.

## How to replay cheaply

Phase 0 (retrieval) and Phase 1 (bottleneck) are the expensive, largely
deterministic-in-value stages. Reuse them:

1. Pick a past run of the direction (any completed run whose `phase0/` and
   `phase1/` exist).
2. Create a fresh run dir and copy ONLY `phase0/` and `phase1/` into it.
3. Replay from Phase 2.1 onward (`next` will route you there).
4. To isolate a generation-side change, additionally pin Phase 2.1 by copying
   `phase2_select/` too, so 2.2/2.3 variance is the only thing measured.

Never commit run dirs; they are local fixtures.

## Criteria are PROPERTY-level, not content-level

The generator is stochastic: two replays legitimately produce different ideas.
Judging "did it produce the same (or a specific) idea" is meaningless. Judge
structural properties of whatever idea it produced. The deterministic subset of
these properties is checked by `scripts/regression_check.py <run_dir>`; the
judgment-level ones (marked ⚖) need a human or fresh-context LLM read.

## The directions (cover all four shapes)

### D1 — method + statistics shape (e.g. speculative-decoding verification scheduling)
The mechanism consumes SAMPLED observations under a feedback loop, so the
observation-model premise, estimand declaration, and T5 naive comparison must
all fire with real content.
- regression_check: BLOCK 2 branch declared; T5 verdict present with a numeric
  divergence; verdict=patched ⇒ refined_candidate.json exists; claims mapped.
- ⚖ if branch (i): the shipped mechanism is NOT the naive version with
  cosmetics (T5 divergence is non-trivial and traced to the declared obstacle);
  statistical guarantee claims carry an executed-mc arbitration with a
  measured number.

### D2 — generative / perception shape (e.g. diffusion image watermarking)
Claims here are often constructive ("residual is exactly zero by
construction"), not statistical. The grading must NOT misapply Monte Carlo to
non-statistical claims.
- regression_check: claim_step_map entries have valid strength_grade values
  when present; no `executed-mc` arbitration on claims with no sampling
  distribution.
- ⚖ guarantee-grade wording ("exact", "zero") is either `established` by a
  construction step or downgraded/conditioned — never left as a bare assertion.

### D3 — systems / scheduling shape (e.g. serving-time compute allocation)
Mechanisms are procedural; the T2 dry-run and degenerate probes carry the load.
- regression_check: dry_run has computed_quantities; when an execution tool was
  available, dry_run.execution.mode is `executed` with script+output.
- ⚖ T3 probes cover the resource-exhaustion edges (queue empty, budget 0,
  all-identical requests), not just generic empty-set probes.

### D4 — theory shape (e.g. transformer single-particle dynamics / equivalence results)
The MANDATORY n/a-path test: this direction must exercise every conditional
escape WITHOUT fabrication.
- regression_check: no fabricated naive_comparison — T5 verdict `n_a` requires
  a non-empty reasoning; observation-model premise either real or the literal
  n/a form; stakes clauses exist on every gap.
- ⚖ stakes are allowed to be purely intellectual costs (invalid conclusions,
  non-transfer) — the pipeline must NOT have forced a fake practitioner
  scenario; theorem-shaped claims are graded `conditional` with proof
  obligations, not "verified" by a dry run.

### D5 (optional) — cross-modal robotics / embodied shape
Exercises the thin-corpus declaration path (few domain-adjacent exemplars in
the pattern corpus).
- ⚖ thinness is declared in how_closed rather than papered over; audit judged
  against abstract Step-by-Step moves.

## Pass rule

A change ships only if regression_check is green on ALL replayed directions and
no ⚖ criterion regressed relative to the pre-change replay of the same
direction. One direction improving while another regresses = do not ship;
find the conditional formulation that spares the regressed shape.
