# Paper Harness Reviewer Protocol

Review the manuscript as a scientific argument, not as an artifact inventory.

1. Reconstruct the chain `title -> problem -> gap -> contributions -> method -> experiments -> statistics -> discussion -> conclusion`.
2. For each load-bearing claim, record the manuscript location, the evidence that supports it, and the exact inference boundary.
3. Separate implementation evidence, mechanism activity, endpoint improvement, external validity, and human or operational utility.
4. A negative result is not a defect. Penalize concealment, inconsistent direction, weak controls, or an unsupported branded claim—not the absence of SOTA.
5. Never infer missing facts. Author metadata, funding, expert review, experiments, citations, and numerical results must be verified from available evidence or marked blocked.
6. Use the venue profile as a calibrated standard. Do not impose conference-style novelty or statistical rituals when the target journal does not require them.
7. Every major issue must have a concrete acceptance test. Suggestions for new experiments must state the estimand, control, analysis unit, and conclusion they would license.
8. Version histories, hashes, incident logs, and conformance records support reproducibility but should not displace the research story in the main text.
9. Review the file under review, and record the specific claim. "The file could not be read" is not a finding. A finding names the metric, equation, baseline, interval, or sentence that conflicts with a table. A formula that exists only in an unreviewed sibling source does not repair the file under review. A truncated definition or an operator that does not determine the calculation is a soundness gap, not a font nit. Do not collapse several reviewers' distinct points into one extraction failure. Figure readability is a finding only when that review actually could not see the figure; it is not automatically shared.
10. A negative or null result is still not a defect. A reproducibility claim that the manuscript itself says is not yet archived is a claim-evidence conflict. "Accepted papers often omit code" does not erase that conflict. Identical high-precision values in two dataset tables are a check against the archive, not an automatic copy-error finding.

The JSON issue matrix is evidence-preserving: distinguish manuscript evidence, reviewer inference, and proposed action.
