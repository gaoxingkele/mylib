---
type: Protocol
title: Evidence-calibrated manuscript review
status: active
updated: 2026-10-28
owner: llm
tags: [peer-review, evidence, calibration]
source_paths:
  - D:/aicoding/mylib/Paper_CCF/resources/worked-examples/lightgmem-review-distill.md
  - D:/aicoding/mylib/Paper_CCF/resources/worked-examples/agms-pvbev-aaai-review-distill.md
  - D:/aicoding/mylib/Paper_CCF/resources/worked-examples/aaai26-published-check-calibration.md
confidence: medium
---

# Evidence-calibrated manuscript review

Use with one selected Paper_CCF venue profile for manuscript reviews and review
reports. For venue selection alone, do not run this audit. Scale depth to the
claims and available evidence; this is not a fixed experiment wishlist.
For paragraph-, section- and experiment-level comparison with published papers,
add [comparative-multiscale-review.md](comparative-multiscale-review.md), whose
gates cover one-idea alignment, experiment coherence, terminology substance and
research-history inflation.

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
- A reproducibility checklist may exist only on the submission form. Check each
  affirmative answer against the manuscript when that form is in the materials.
  If it is absent, the alleged conflict is unavailable. Use N/A when a question
  does not apply. A checklist mismatch is a reporting gap, not misconduct.

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
If a claimed sampler reports a hit or coverage rate, state the empty-return fraction.
A rate below one half means the module is inactive at most of its sites. Leave this
check inactive when the manuscript does not report a hit or coverage rate. Accepted
papers are not required to contain one.
A covariance built only from points on one ray has rank at most one. Using its
inverse as a 2D Gaussian is an algebraic gap unless the manuscript states a
transverse scale, footprint, or regularizer. That gap is not an observed crash.
Do not apply it to a covariance defined as R S S^T R^T with a diagonal scale.
When compositing changes a standard front-to-back or back-to-front direction,
name both the convention and the scalar that orders items from different cameras.
Camera-relative depths are not automatically one shared order. Leave the check
inactive when the manuscript does not define that ordering.

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
  and wall-clock ratios from algorithmic acceleration. When prose puts a percent
  sign on an IoU, NDS, mAP, or rate change, recompute both the point difference
  and the relative change, and bind the sentence to the row, stage, modality, and
  resolution it names. AAAI-26 published papers use both conventions: a percent
  can equal the point difference, or it can equal the relative change. Either
  match is consistent. If it matches neither, leave the unit unresolved. Do not
  rename the unit before the check. A one-decimal mean of several displayed
  deltas may be ordinary rounding. For an efficiency claim, report the absolute
  difference and the relative difference from the same operands, and keep that
  pair tied to the row's accuracy setting. A small throughput drop beside a
  metric gain is an operating point, including on accepted papers. It is not
  itself a rejection condition.
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

For a pretrained backbone, record the initialization task and whether the
comparison systems received it. Naming the initialization dataset, and saying
that comparison systems follow that practice, satisfies the check. A missing
per-baseline initialization column is common in accepted papers. It becomes a
main issue when the manuscript credits an initialization the baselines did not
receive. A sentence in which the manuscript itself credits those weights is
direct evidence. The public checkpoint's dataset is a separate, labeled inference.
A figure that shows only the proposed output and ground truth does not show an
improvement over a baseline. When criticizing quantization, keep the manuscript's
own qualifier and compare cell size with the stated baseline resolution. Use a
size the manuscript states, or one that its stated range and cell count determine.
Do not invent a size it does not give. A one-token resolution mismatch is a
configuration question when the ablation score still matches a named column of
another table. Do not treat that table as unusable. A state-of-the-art margin
from one table must stay on that table. Do not let the sentence attach it to a
stronger-backbone comparison whose own margin is smaller.

For structural or LLM-rated metrics, inspect definition, denominator, annotation
provenance and judge protocol. Overlapping memberships can change counting; a
metric of 1.00 is not by itself evidence of circular normalization. Temporal,
streaming or deployment extensions are optional unless needed by a central claim.

## Literature and novelty

Prefer a small set of demonstrably relevant primary papers to a name dump. Explain
the technical delta and comparability of tasks, models and budgets. If only a
summary is available, label the comparison provisional; do not assert unexamined
systems dominate on a common protocol. A family-level state-of-the-art claim
needs the direct same-family system, not only the cited baseline. Numbers that
appear only in another review stay unverified until the source paper and protocol
are checked. Before accepting a same-modality ranking, compare the bibliography
title and the manuscript's own description with the table's modality cell.
An adapted standard component still needs its source citation. A missing citation
is a credit and clarity issue, not by itself a novelty decision. Check public
availability against an explicit manuscript cutoff. Later work can inform a current
revision without making its absence a fault of the original submission. Verify
live venue policies separately.

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
5. Does a rebuttal question ask for evidence the paper already has, or for a new
   study? Official comments sometimes ask only for the former. A wish list in an
   accepting review is not an acceptance threshold. Do not average one case's
   scores into a venue cutoff. Recompute a reviewer's category win count.

For a PDF, verify both text preservation and rendered pages with the applicable
artifact skill. No new agent/tool/service is required by this review method.

## Calibration case and replay

- [LightGMEM distillation](worked-examples/lightgmem-review-distill.md): source-backed
  lessons, including mistakes in the source reviews and in our own review.
  This is evaluator/reference material, not input for the bounded replay.
- [AGMS and PV-BEV distillation](worked-examples/agms-pvbev-aaai-review-distill.md):
  AAAI-27 phase reviews and a first-round rejection pair. Use the review actions.
  Do not reuse the 5.60 mean, individual scores, or the rejection stance as a cutoff.
  This pair was not turned into a fresh-session replay.
- [AAAI-26 published calibration](worked-examples/aaai26-published-check-calibration.md):
  the same checks run on five published AAAI-26 papers. Use it to separate a
  consistent percent convention, an inactive check, and a real scope error.
  The numeric ledger is `tests/fixtures/aaai26-published-ledger.json`.
- [Bounded review exercise](../tests/fixtures/review-calibration.md): raw excerpts for
  a fresh-session replay. Give the exercise and this method, not the case conclusions.
  Validate the resulting decisions, not exact wording or a predetermined verdict.
  One case is evidence of local improvement, not proof of general reviewer superiority.
