# Chapter × journal scoring (v3)

For repeated revision, cross-review adjudication, paragraph comparators, or
sample-rank tracking, also read
`D:/aicoding/mylib/Paper_CCF/resources/comparative-revision-calibration.md`.
That protocol extends workflow and provenance, not this scale or its weights.

Use when the user requests chapter scores against a target journal and a fixed
reference corpus. The maintained library copy is
`D:/aicoding/mylib/Paper_CCF/resources/chapter-journal-scoring-v3.md`.

## Bind and freeze

Bind exact reader-facing manuscript/SI hashes, official journal requirements
with verification date, reference IDs/DOIs/PDF hashes and version, sampling
rule, reading coverage, reviewers and rubric. Preserve earlier raw scores.
Accepted author versions and final publisher versions can both inform content;
do not confuse a stale author header with publisher acceptance evidence.
An accepted-only convenience sample cannot estimate an acceptance threshold,
probability or causal reasons for acceptance. Readable published errors do not
become acceptable practice. Extraction failures remain unknown, not author faults.

Use functional modules: title/abstract, introduction, related work, methods/
theory, design, results, discussion, conclusion. Combined headings are valid;
map the functions instead of penalizing the absence of a heading. Paragraph,
equation, figure, table and citation checks remain separate coverage records;
chapter scoring alone is not exhaustive object verification.

## Preserve comparability

For an existing eight-dimension 0–5 model, keep its dimension weights as matrix
column margins. Prespecify chapter row allocations before viewing new totals.
The bundled `assets/chapter-journal-100-v3.json` is the validated Mintou example,
not an official journal standard. Row weights 8/12/10/20/18/16/10/6 sum100;
column margins15/15/15/15/15/10/10/5 preserve that case's v2 model.
Other projects may freeze different weights; never tune them to achieve90.
When adapting the example, rebind manuscript facts and the unchanged-input
declaration; copying weights does not copy verified input identity. The helper
records the declaration but does not itself verify manuscript file hashes.
Installed paths are relative to the skill root. The library mirror's example
rubric and executable are in `D:/aicoding/mylib/Codex-Academic-Research/tools/`
as `chapter-journal-100-v3.json` and `chapter_score.py` respectively.

For each nonzero cell give integer0–5 or null, exact PDF page/section/object
anchors, strength, unresolved limitation and a root-cause ID. Scores mean:
0 absent/contradictory on readable evidence; 1 major deficit; 2 weak support;
3 consequential unresolved gap; 4 adequate support for the stated question;
5 strong specific reader-verifiable support. Counts of formulas, experiments,
pages, artifact hashes and caveats earn no points by themselves. A negative
result is not a defect. Honest caveats do not improve external validity.

Score adequacy against the actual stated question. Do not assign a consequential
deficit solely because a retrospective diagnosis lacks field deployment, a
pointwise interval lacks joint coverage, or a bounded result lacks universal
generalization that the paper does not claim. Conversely, narrowing a claim
does not establish its scientific contribution: assess that separately. Unknown
review coverage (e.g. citations not checked) is not an author defect. Preserve
raw scores and record evidence-based adjudication patches separately, including
the primary→adjudicated change and any reviewer conflict of interest.

`chapter100 = 100 × sum(weight × rating/5)/chapter_weight`;
`total100 = sum(all weight × rating/5)`.
Nulls reduce known coverage; report partial points and known weight with no
renormalized complete total. Replicate old dimension ratings into their cells:
this counterfactual must exactly reconstruct each old total. New−old decomposes
as `sum(weight × (new_rating−old_dimension_rating)/5)`. Weight contribution is
zero when margins are unchanged. On unchanged manuscripts this measures a
refined assessment, not a manuscript quality improvement/decline.

## Calibrate and check logic

For each journal's fixed10, record each functional chapter's quality anchors,
locators, genre, strengths, flaws, text/visual/math coverage and uncertainty.
One functional rating per reference module is useful, but differs in resolution
from a manuscript's cell-weighted row: comparisons are descriptive. Report
effective n, median and inclusive IQR; unknowns excluded. Prefer task/genre
matched comparators and explain the actual difference, not just IDs. A sample
median is not a bar to lower standards or a percentile-based acceptance rule.
Different reader depth/reviewer severity confounds cross-journal sample ranks.

Check separately: scope, distinct contribution, central validity; then seven
edges: abstract↔question, literature→gap, question→method, method→design,
design→result, result→discussion, discussion→conclusion. Each needs two anchors
and supported/partial/missing/contradictory status. Do not hide a central failure
behind a high mean or invent a numeric cap. Identify duplicate root causes;
explain their different functional consequences without an extra global penalty.
Normalize label meanings before comparing seats. Distinguish evidence of a
finite knowledge increment, sufficient nearest-work positioning, and confirmed
central inference failure; “supported with positioning gap” and “partial” may
describe the same facts. Keep raw labels and paired evidence rather than count
them as objective pass/fail votes.

Independent agents may use the same frozen rubric when requested/authorized.
Separate drafting and reviewing seats, freeze raw judgments before old-number
comparison, and disclose informed/not-blind review. Rotating agents is not
human peer review or external-model diversity. A subset double rating supports
only subset agreement, not a full inter-rater reliability claim. Reconcile
disagreements against evidence, not a target total.

## Machine-readable review and execution

Input review: `{cards:[{paper,journal_code,reading_scope,chapters:{Ckey:{
functional_mapping:[{pages,heading}],reference_ids:[...],cells:{Dkey:{rating,
anchors:[...],strength,deficit,root_cause_id:[...]}}}},gates,logic_edges}]}`.
Use exact chapter/dimension keys from the frozen rubric; include every nonzero
cell once. JSON must have unique keys. Reference files have `cards:[{id,
journal_code,modules:{Ckey:{rating,...}}}]`; the legacy EN alias
`reader_visible_quality_score` is supported. Baseline cards use `journal`,
`ratings`, `score_100` and matching dimension weights.

Run `scripts/chapter_score.py --rubric <json> --cards <raw files...>
--baseline <old.json> --references <reference files...> --out <output-dir>`.
It validates row/column margins, rating range and bools, required cell keys,
duplicate cards, anchors, old-total reconstruction and delta conservation.
It writes totals, chapters, dimensions and reference summaries; it cannot
determine whether an anchor is scientifically sufficient. Preserve raw hashes,
reviewer disagreements, gate findings and a prose assessment alongside outputs.

## Journal-rule correction

IEEE Access permits modest novelty but still requires a distinct contribution
and a clear advance, supported by rigorous experiments and conclusions. It is
not a correctness-only journal. Verified2026-11-11 against
[official reviewer guidelines](https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/).
Recheck current primary rules before a new submission task. The correction
addresses an overstatement in the local profile, not a demonstrated new policy.
