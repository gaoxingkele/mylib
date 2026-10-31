# Scientific quality comparison: claim-specific controls

Calibration: 2026-10-31.2. Local advisory method, not an Information editorial rule.

Use after `standards-and-evidence.md` and `rejection-reaudit.md` when comparing a manuscript with published full texts. The local evidence audit is `F:/aicoding/powergrid_benchmark/reviews/information_reaudit_20261031/FULLTEXT_QUALITY_REVIEW_ZH.md`, with scope/hashes in `FULLTEXT_COVERAGE.json`. Main evidence sections were examined across ten papers; bibliography, supplements, every introductory paragraph, visual layouts and executions were not exhaustively checked. This is not a complete replication corpus.

## Compare evidence functions, not artifact counts

For each paper, write: central question → claimed construct → operational measurement → intervention/comparator → independent unit → result → strongest surviving alternative explanation → smallest discriminating next experiment.

Review the published comparator with the same skepticism as the target. Admission to a journal does not validate a particular analysis, supply a quality floor, or identify why another article was rejected. A recent chronological sample without rejected controls cannot estimate acceptance predictors. Separate reviews, conceptual frameworks, diagnostic studies and algorithmic claims.

Count an experiment by the question it resolves, not its table rows, plots, seeds or repeated samples. Replotting one matrix in five figures is one evidence source. A planned control is zero completed evidence. A limitation disclosure improves claim calibration but does not repair a biased estimator or a missing comparison.

## Mechanism attribution

1. **Positive outcome:** ask whether extra supervision, input information, candidate count, output length, optimization budget or calibration explains it. The minimal control must match the suspected cause, not merely carry a baseline name.
2. **Negative outcome:** distinguish inactive code, ineffective implementation, invalid construct, insensitive endpoint and bounded evidence of no useful effect. Inspect existing controls before requesting new ones.
3. **Diagnostic papers:** require a useful, testable lesson beyond describing many unsuccessful revisions. Ask what competing explanation was actually excluded.
4. **Oracle or expert structure:** use as an explicitly labeled diagnostic upper bound. Cross automatic/expert structure with component on/off; do not present oracle performance as deployable performance.
5. **Synthetic positive controls:** test whether the pipeline can detect a planted effect, then assess whether generation and reference construction make success tautological. They do not establish real-domain validity.
6. **Error-stage counts:** identify where failures occur. They do not by themselves identify causes or the number recoverable by a proposed remedy.

## Endpoint and statistical checks

- Gate precision P(correct | pass) is prevalence- and difficulty-dependent. A precision ratio across backbones is not a ratio of discriminative information. Request correct/incorrect × pass/reject counts, retention/specificity, and controlled error mixtures.
- Equal answer coverage can support a policy-risk comparison even if answered sets differ; disclose overlap and subgroup coverage. It does not establish an intrinsic classifier effect on identical cases.
- Same aggregate count does not mean identical errors. Preserve paired item transitions.
- A scale-free metric need not be invariant to nonlinear transformations. Record whether predictions and targets were inverse-transformed before computing MAPE/R² or other reported metrics.
- Time-series interpolation must respect forecast origin and data availability. A future right endpoint may leak information even with otherwise chronological train/test splits.
- Non-overlapping blocks do not automatically imply independence; replacing n by a block count does not guarantee valid uncertainty. Identify the estimand and dependence assumptions.
- Training seeds, queries, templates, schemas, reports and institutional series are different uncertainty units. More seeds or bootstrap draws cannot replace more independent domains.
- Rules satisfied by construction, structural coverage, annotation consensus and available audit logs are not independent evidence of semantic truth or task benefit.

## Contribution visibility and fair advantage claims

Read title, abstract, contribution list, primary result and conclusion together. They must describe the same completed study, endpoint and scope. A decisive new verified study may require updating the headline; historical instructions to freeze headlines must not prevent evidence-consistent revision. Preserve negative findings and evidence history in accessible supplementary material.

Do not infer provenance, reproducibility or deterministic execution from method-family labels. Extractive rerankers can retain source IDs; local learned models can be frozen and rerun. Distinguish zero generative/API calls from zero inference or computation cost. Equal call/token ceilings do not establish equal realized resource consumption.

## Regression cases from the local audit

- MA-SQLGrid final has five physical calls in its full live allocation and already reports the 42/6/33/99 pool decomposition. Reject reviews asserting only three calls or no tie analysis.
- Its 240-query study already describes shared ceilings, fresh role-removal generation, saved-call reallocation and expert-semantic endpoints. Audit underlying records; do not erase these designs from the review or assume that prose proves execution.
- Its 87.5% versus 41.8% gate precision cannot establish twice the discriminative information.
- C2GES r31 already includes normalized ablation, word-budget controls, learned/LLM comparators and constructed positive path effects. Remaining real-domain semantic validation must not be misreported as absence of all controls.
- Information 1073 and 1077 illustrate same-input/simple-rule and calibrated-constant controls; 1070 illustrates unclosed supervision overlap; 1069 illustrates why mathematical claims require independent scrutiny. These are claim-specific examples, not acceptance standards.

## Deliverable

Give verified findings, plausible risks and unknown editorial reasons separately. Every major finding needs a source anchor, consequence, existing mitigating evidence and a repair criterion. Keep source identity and coverage ledger. Do not raise evidence-quality ratings when only prose or formatting changed.
