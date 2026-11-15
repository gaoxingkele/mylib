# Meta rubric v1.0

This is a local advisory rubric, NOT a calibrated journal acceptance model.
Freeze version and weights for each before/after pair. Do not tune them to favor
the revision. Ratings: 0 absent/contradictory; 1 major weakness; 2 partial support;
3 adequately supported within stated scope with residual limitations;
4 strong, directly verified support. Integers only. Unknown is null, not zero.

| ID | Dimension | Weight | Evidence to examine |
|---|---|---:|---|
| I1 | Information problem and contribution | 15 | Gap, RQs, distinction from known properties |
| I2 | Theory and executable mechanism | 15 | Definitions, assumptions, implementation alignment |
| I3 | Data and external validity | 15 | Provenance, visibility, independent units, task diversity |
| I4 | Comparisons and diagnostic controls | 15 | Baselines, matched resources, component isolation |
| I5 | Statistics and inferential scope | 10 | Denominators, dependence, uncertainty, multiplicity |
| I6 | Cross-section narrative and prose | 15 | Abstract/RQ/results/conclusion consistency and paragraph functions |
| I7 | Current-version reproducibility | 5 | Current artifacts, independent build, data access, release binding |
| I8 | Presentation and source integrity | 5 | Legibility, labels, citations, figure/table identity |
| I9 | Author/transfer readiness | 5 | Current approval, truthful statements, exclusivity and portal requirements |

For complete ratings, total = sum(weight × rating / 4), out of 100.
Scientific subtotal I1–I6 is reported separately out of 85; I7–I9 out of 15.
If any dimension is null, report assessed weight and partial points; do not
renormalize or present a complete total. Never map score ranges to acceptance.

## Meta record fields

At minimum: source SHA, locator, unit type, rhetorical role, atomic claim,
supporting evidence locator, evidence status, assumption, comparison scope,
cross-section target, discrepancy, review status. Quantitative fields include
equation type/function; algorithm L1/L2/L3; experiment vs configuration vs
independent-unit counts; paragraph/section lengths with tokenization convention;
figure/table type and semantic role. Missing fields remain unassessed, not zero.

Coverage is multidimensional: parsed-text partition, paragraph boundaries,
visual objects, semantic edges, citation truth, experimental reproducibility.
Completing one does not prove the others. Use full-text denominators only when
the parser/version and complete mapping are actually available.

## Review-to-revision record

Each finding: ID, severity, source anchor, observation, consequence, repair,
verification test, status (open/partial/closed), and residual risk. Each score
requires evidence and a short reason. The post score may remain unchanged
after a useful small edit: it must not cross an anchor threshold without cause.
Retain pre-scores and pre-edit SHA; never reconstruct a favorable baseline later.
