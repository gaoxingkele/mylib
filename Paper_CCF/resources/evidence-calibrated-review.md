---
type: Protocol
title: Evidence-calibrated manuscript review
status: active
updated: 2026-10-01
owner: llm
tags: [peer-review, evidence, calibration]
source_paths:
  - D:/aicoding/mylib/Paper_CCF/resources/worked-examples/lightgmem-review-distill.md
confidence: medium
---

# Evidence-calibrated manuscript review

Use with one selected Paper_CCF venue profile for manuscript reviews and review
reports. For venue selection alone, do not run this audit. Scale depth to the
claims and available evidence; this is not a fixed experiment wishlist.

## Establish the evidence boundary

- Record the manuscript version, explicit literature cutoff if supplied, available
  supplement/code/data, and the intended contribution. Do not infer a submission
  date from a folder name or confuse a review revision with a manuscript revision.
- Read the manuscript first when independence is requested. If other reviews have
  already been seen, disclose that fact. A fresh agent can provide an independent
  lane when useful, but do not label the whole synthesis a strict blind review.
- Use existing reviews as hypotheses. Recheck important criticisms against the
  complete relevant paragraph, formula, table caption, and experiment settings.
  Do not rank reviewer expertise from style, length, identity, or rejection severity.
- Track evidence as **observed**, **inferred**, or **unavailable**. "Not in the main
  paper" differs from "not provided" when a supplement is referenced but inaccessible.

## Build the claim-to-evidence chain

Before drafting a recommendation, make a small working ledger of the critical
claims and checks actually performed. It need not appear in the final report or
be written to disk. Each entry records the source inputs, scope, result, and
whether the check was completed or blocked by unavailable evidence. Listing
"arithmetic should be checked" is not a completed numerical check when the
displayed values are already supplied. For a short review, prioritize a few
decisive checks over a broad list of proposed future experiments.

For numerical claims, collect the available operands and reported values and run
the [number audit helper](../scripts/audit_review_numbers.py) when local Python is
available, or perform an equivalent explicit calculation. The helper accepts a
JSON ledger of sums, ratios and differences with display resolution, rounding
assumption and source location; it has no external dependencies. Execute it and
read the results before writing a cost/accuracy judgment. Do not pass off a planned
calculation as performed. Align units and populations first: the tool checks the
provided numbers, not the source transcription, experimental fairness or truth.

```text
python D:/aicoding/mylib/Paper_CCF/scripts/audit_review_numbers.py /path/to/numeric-ledger.json
```

The bounded review exercise has a companion
[construction-cost ledger](../tests/fixtures/construction-cost-ledger.json).
Confirm its inputs against the excerpts, execute the audit, then interpret the
result within the review. This ledger contains input numbers, not review verdicts.
`rounding: nearest` is an explicit assumption; use `unknown` when the display rule
is not established. `rounding_possible` is not a proof of the author's rounding
procedure. A valid audit exits 0 even when it finds a mismatch; input errors exit 2.
For sums/differences, `nearest` assumes independently displayed operands and result
share the supplied resolution. For ratios, operands are treated as the given exact
counts/values and only the reported ratio is rounded. The helper does not propagate
uncertainty from rounded ratio operands; use raw counts or a separate interval
calculation when that uncertainty can affect the judgment.
See [helper tests](../tests/test_audit_review_numbers.py) for the supported input
boundary and arithmetic behaviors, rather than extending it into a significance test.

For each recommendation-critical claim, identify its scope, proposed mechanism,
supporting experiment/proof, strongest comparator, and decisive missing control.
Check three separate links: mechanism validity, empirical utility, and generality.
Benchmark leadership does not itself prove mechanism attribution; a useful system
integration is not automatically unoriginal because its components are established.

A useful finding record is:

> Claim/location → direct observation → inference and plausible alternative →
> impact on the claim → current status/confidence → author question or decisive check.

Keep only fields that help the reader assess that finding. A recommendation should
follow the strongest material issues, not a count of minor shortcomings.

## Mechanism-level reasoning

For algorithms with mutable state, trace what each stage reads, creates, changes,
and commits. Inspect filtering, snapshots, execution ordering and reconciliation.
Static partitions or disjoint heuristic keys need not imply semantic independence.
Conversely, that observation does not invalidate the static set equation itself.

Construct a minimal conditional counterexample when helpful. Check that it satisfies
the actual filtering thresholds, candidate rules and execution scope; do not silently
assume every ambiguous input reaches the expensive resolver. State assumptions and
whether the error is demonstrated, plausible, or contradicted by supplied evidence.
An approximate method can be soundly motivated by a measured error-cost tradeoff;
do not demand a universal equivalence proof when the manuscript claims approximation.

Entity counts alone do not establish identical graphs or assignments. Different QA
scores alone do not establish a concurrency bug: generation, judging and sampling
may vary. Prefer state/assignment agreement or error measurements with a controlled
resolver, then separate downstream generation and judge variability.

## Numerical and experimental cross-checks

- Recompute available claim-critical ratios, sums, differences, win counts and
  rankings before judging the quantitative evidence. Use a calculator or short
  local calculation where needed; record the operands and result, not just a
  generic request for transparent tables. Include consequential verified
  inconsistencies in the findings, while separating clerical errors from reasons
  to reject a central scientific claim.
  Separate percentages from percentage points, call counts from token/money costs,
  and wall-clock ratios from algorithmic acceleration.
- Before declaring conflicting values, align population/problem set, configuration,
  retrieval/judge, aggregation, and run/version. An unexplained mismatch can be an
  important clarity issue without proving data corruption.
- Distinguish total entities from community-covered entities or other subsets.
  Overall accuracy may be sample-weighted, not a mean of category scores.
- Respect displayed precision. For three independently nearest-rounded input,
  output and total values at unit u, an additive discrepancy up to 1.5u is possible.
  If the rounding rule is unknown, call it a possible explanation, not a proof.
  A much larger discrepancy needs the original counts or a corrected definition.
- Inspect the unit of the intervention and the unit of uncertainty: one conversation
  does not establish cross-conversation generality; correlated questions may require
  clustered/paired analysis. Tiny point-estimate wins need uncertainty information,
  not an invented significance threshold or a claim that the gain is zero.
- Locate actual ablations before requesting them. Distinguish removing a component,
  varying its algorithm, and controlling it across competing systems. Credit controls
  already present, then ask for the specific remaining causal comparison.

## Cost, quality and attribution

Check construction and query boundaries, measured workload, totals versus means,
backbone models, hardware, concurrency/rate limits, retries, caching and whether
baseline results were rerun or quoted. Do not assert these factors caused a speedup
without evidence. Fewer LLM calls is useful evidence, but varying call tasks and
prompt lengths can still change the cost-quality interpretation.

Compare against the strongest quality and relevant efficiency competitors; do not
require every new system. When retrieval/reranking differs, distinguish a valid
fixed-retrieval internal ablation from a cross-system attribution claim. Report
the measured quality-cost operating point rather than implying universal dominance.

For structural or LLM-rated metrics, inspect definition, denominator, annotation
provenance and judge protocol. Overlapping memberships can change counting; a
metric of 1.00 is not by itself evidence of circular normalization. Temporal,
streaming or deployment extensions are optional unless needed by a central claim.

## Literature and novelty

Prefer a small set of demonstrably relevant primary papers to a name dump. Explain
the technical delta and comparability of tasks, models and budgets. If only a
summary is available, label the comparison provisional; do not assert unexamined
systems dominate on a common protocol. Check public availability against an explicit
manuscript cutoff. Later work can inform a current revision without making its
absence a fault of the original submission. Verify live venue policies separately.

## Deliver and challenge the review

Include concrete strengths, prioritized findings with locations, actionable author
questions, limitations of the review and a venue-calibrated recommendation. Follow
the requested language and format; omit platform chrome and feedback forms from
an exported review. Do not invent official numeric scores or acceptance probabilities.

Before delivery, challenge each major finding:

1. Is there a paragraph, supplement reference, existing ablation, subset definition,
   stochastic explanation or alternate aggregation that changes the judgment?
2. Does the proposed fix test the claimed mechanism, or merely expand the paper?
3. Is a conditional risk being reported as an observed flaw? Is a documentation
   gap being presented as misconduct, an implementation bug, or an automatic reject?
4. Would the recommendation remain the same after removing stylistic/minor issues?

For a PDF, verify both text preservation and rendered pages with the applicable
artifact skill. No new agent/tool/service is required by this review method.

## Calibration case and replay

- [LightGMEM distillation](worked-examples/lightgmem-review-distill.md): source-backed
  lessons, including mistakes in the source reviews and in our own review.
  This is evaluator/reference material, not input for the bounded replay.
- [Bounded review exercise](../tests/fixtures/review-calibration.md): raw excerpts for
  a fresh-session replay. Give the exercise and this method, not the case conclusions.
  Validate the resulting decisions, not exact wording or a predetermined verdict.
  One case is evidence of local improvement, not proof of general reviewer superiority.
