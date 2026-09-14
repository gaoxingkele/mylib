# Information：文章要求、发表样本与评审尺度

Calibration version: 2026-09-12.1. Refresh current policies when making a new submission recommendation. This reference is shared across projects; the SQL case is evidence for calibration, not the universal task.

## 1. Evidence hierarchy

1. **Official**: journal scope and instructions, publisher reviewer/ethics/data policies. Record retrieval date and distinguish a journal-specific page from publisher-wide guidance.
2. **Observed**: verified published articles. Describe the particular task, study type and evidence; publication does not validate every claim or reveal the editor's acceptance threshold.
3. **Recommended**: local risk controls and reviewer judgments. Explain why the actual manuscript needs them; do not call them publisher mandates.

Access failures remain visible. A sibling journal's instructions are not Information's instructions. An extraction cue's absence is not proof that an experiment is absent. Never report an acceptance probability or an "easier than Applied Sciences" ranking without suitable outcome data and denominators.

## 2. Official anchors checked 2026-09-12

| Source | Supported requirement or fact | Boundary |
|---|---|---|
| [Information aims and scope](https://www.mdpi.com/journal/information/about) | Information/data/knowledge/communication remit; experimental and theoretical work; sufficient experimental detail for reproduction; no maximum manuscript length | No maximum is not a reason to retain repetition; no official minimum number of pages, equations or figures was established |
| [MDPI reviewer guidelines, §7.5](https://www.mdpi.com/reviewers?authAll=true) | Review novelty, scope, significance, presentation, soundness, reader interest and overall merit; negative findings about a valid hypothesis can have value | Publisher-wide criteria, not an Information acceptance formula; soundness does not waive originality or significance |
| [Information homepage](https://www.mdpi.com/journal/information) and [EI list](https://www.mdpi.com/about/journals/compendex) | Ei Compendex, Scopus, ESCI are listed | ESCI is not SCIE; verify institutional recognition and eventual article indexing separately |
| [Information instructions](https://www.mdpi.com/journal/information/instructions) | Primary submission-policy endpoint | Direct automated retrieval was unavailable in this calibration; do not certify the full current checklist from a sibling journal |
| [MDPI layout](https://www.mdpi.com/authors/layout) and [MDPI LaTeX template](https://www.overleaf.com/latex/templates/mdpi-article-template/fcpwsspfzsph) | Use the appropriate journal option and a coherent reference/section style | About-200-word single-paragraph abstract and 3–10 keywords are template/common-style targets pending journal-specific confirmation, not inferred acceptance thresholds |

APC, quartile and median turnaround remain dated snapshots in the parent profile; recheck them if cost or speed matters. A published-paper median excludes unsuccessful submissions and is not an acceptance-time promise. No new acceptance-rate dataset was obtained.

## 3. DOI-verified full-text calibration sample

The four purposefully selected Information papers span different study types. They do not constitute a representative or rejection-controlled sample. Full text, metadata/OA records and SHA-256 are retained in the calibration archive below.

| Paper | Transferable strengths | Do not imitate |
|---|---|---|
| Wardani et al., 2026, [SQL Query Description / SQL-PLAS](https://doi.org/10.3390/info17010065), 33 pages | Concrete actors and interfaces; generation and student use evaluated separately; explicit limitations | Inferring learning gains or reduced workload without the corresponding controlled outcome; treating rating agreement as accuracy |
| Avignone et al., 2025, [ER-schema descriptions](https://doi.org/10.3390/info16050368), 19 pages | Operational definitions of schema constructs; RQ-to-metric links; examples showing structural misinterpretation | Treating fluent text or overlap metrics as semantic faithfulness; extrapolating from one larger-schema example |
| Çetinkaya, 2025, [Learnability validation](https://doi.org/10.3390/info16110960), 16 pages | Separates internal prediction, external agreement and expert comparison; analyzes disagreements | Promoting learnability to truth, model agreement to independent ground truth, or uncalibrated thresholds to universal rules |
| Gharbi, 2020, [Multi-agent cooperation](https://doi.org/10.3390/info11050271), 21 pages | Explicit agent/task/resource definitions; concrete protocol and model properties | Promoting existential reachability to universal liveness or a small model check to implementation-wide reliability |

Provenance archive: `D:/aicoding/powergrid_benchmark/paper_projects/CMC/MA-SQLGrid/02_Revision_and_QA/06_Information_Rewrite/literature/`. Read `sql_schema_distillation.md` and `validation_coordination_distillation.md` there for page-based detail, and `manifest.json` for file identity. These are agent readings, not human-read attestations. If the archive is absent elsewhere, use the DOI originals; do not pretend local page anchors were checked.

### What “publication level” can responsibly mean

These cases show multiple viable evidence forms: operational task definitions, controlled or bounded empirical analyses, explicit system protocols, and formal properties under stated assumptions. They do **not** show that every article needs a new theorem, a fixed benchmark count, or SOTA performance. Conversely, naming a framework, compiling a PDF or disclosing limitations does not establish a meaningful contribution. Evaluate what readers learn beyond the particular implementation. Negative results are not an automatic defect, but require a valid question, interpretable controls, honest scope and a useful explanation of failure.

### Writing calibration

Prefer task → ambiguity/bottleneck → operational mechanism → test → result → limit. Use specific actors and functional verbs; pair quantitative claims with comparison, denominator and scope. Use formulas only to define or derive something that changes the reader's understanding. Distinguish measured effects, deductive properties, plausible explanations and future work. Do not copy phrases, inflate certainty, pad citations to the target journal, or conceal unfavorable baselines.

## 4. Comprehensive review dimensions (local rubric, not official score)

Record each dimension as supported / partial / insufficient / unverified / not applicable, with an exact text, equation, table, file or scoped absence anchor.

| ID | Dimension | Decision-relevant checks |
|---|---|---|
| I1 | Scope and contribution | Identify the information-science question and the new knowledge; distinguish a method, diagnostic study, benchmark or application paper |
| I2 | Theory and mechanisms | Definitions, assumptions and proofs valid; implementation corresponds to the model; elementary properties not sold as substantive theoretical novelty; observed correlations not causal identification |
| I3 | Data and validity | Provenance, legal access, unit of analysis, split/visibility chronology, meaningful diversity; synthetic data and LLM labels explicitly identified; model labels never substituted for qualified human validation |
| I4 | Comparisons and diagnosis | Controls match the claim and budget; compare strongest relevant executed baselines, not only weak controls; isolate mechanisms and distinguish post-hoc probes from prospective evidence |
| I5 | Statistics | Recompute available ratios, paired changes and multiplicity; respect dependency clusters, estimand and interval meaning; distinguish descriptive p-values from confirmation; non-rejection is not equivalence |
| I6 | Claims and prose | Abstract/RQ/results/conclusion align; result and limitation coexist; avoid both overselling and repetitive defensive prose; audit cited-task relevance |
| I7 | Reproducibility | Current manuscript, code, evaluator, results, figures, environment and release identifiers agree; distinguish local tests from public-package reproducibility; restricted data have a lawful reconstruction/access path |
| I8 | Presentation | Legible figures/tables, correct denominators/labels/references, appropriate template, no placeholders; no page-count quality proxy |
| I9 | Integrity and transfer readiness | Accurate authorship/AI/data/ethics statements, permission boundaries, no duplicate submission; distinguish new draft approval and release from historical ones; inspect refusal letter before claiming a known rejection cause |

The counter-argument pass must ask: if the headline mechanism fails, what generalizable or bounded new information survives? Conversely, do not demand a positive outcome or unrelated new experiment just to make a diagnostic paper look like a performance paper.

## 5. Decision and reporting discipline

- Separate **scope fit**, **scientific readiness**, **technical/package readiness** and **author/portal actions**. An EI requirement concerns recognition, not a relaxed science bar.
- Findings include severity, anchor, consequence, repair action and closure evidence. A proposed experiment is not an already completed result.
- Distinguish demonstrated defects from unverified items and legitimate scope limitations. Do not manufacture a critical failure simply because deployment or a human study was not claimed.
- Use readiness language such as “substantial revision recommended” or “ready for author submission consideration with residual risk”; do not impersonate an actual editor's decision.
- Disclose reviewer provenance. An agent that wrote the paper is not an independent blinded reviewer; multiple inline perspectives are not independent votes. If an invoked review workflow's blind/panel contract cannot be satisfied, label that contract unavailable rather than generating a false pass; provide a clearly identified evidence-based advisory review instead.
- For a readiness conclusion, identify the strongest unresolved issue, not merely total checklist counts. No automatic acceptance threshold or numeric score-to-probability conversion.

## 6. Regression cases for this calibration

1. A 28-page paper with 12 tables and three elementary propositions: no automatic pass on length or theory count; assess what the properties explain and what evidence supports the claim.
2. A method loses to its best baseline: do not hide the baseline or automatically reject all negative research; assess the controlled diagnostic contribution.
3. Synthetic cases plus multi-LLM agreement: not real operational data or independent expert labels.
4. A clean build linked to an older release: build pass may coexist with incomplete current-release reproducibility.
5. An EI-only author: Information can satisfy the stated indexing floor when current listing is verified; this says nothing about easy acceptance or the author's institution-specific rules.
