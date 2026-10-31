---
type: Protocol
title: Comparative multiscale manuscript review
status: active
updated: 2026-10-31
owner: llm
tags: [peer-review, comparative-review, paragraph, section, experiment, narrative]
source_paths:
  - D:/aicoding/mylib/Paper_CCF/resources/evidence-calibrated-review.md
confidence: medium
---

# Comparative multiscale manuscript review v2

Use this protocol with `evidence-calibrated-review.md` and one venue profile. It is designed for detailed comparison with published papers and for detecting problems that aggregate rubrics miss: a fluent but unnecessary paragraph, an incoherent sequence of good experiments, version-history inflation, or a title and evidence base that no longer describe the same study.

It does not estimate acceptance probability. Published papers are accepted-only convenience samples, not rejected controls or a journal threshold. The manuscript must first pass its own soundness checks; comparison then calibrates presentation and evidence expectations.

## 1. Freeze versions and the comparison unit

- Bind manuscript version, source hash, reading PDF, supplements, article type and target venue.
- For a “latest papers” sample, record the metadata query and sampling timestamp. Do not sort on a year-only publication field and call it chronology.
- Preserve DOI, title, publisher URL, local hash, page count, parser and actual version statement in the PDF. A Crossref `vor` link may resolve to an accepted manuscript that says it is not fully edited; do not silently upgrade it to the final version of record.
- Distinguish preprint, accepted manuscript and final publisher layout. Do not use an old preprint date as the formal publication date.
- Select comparators by task, article type and evidentiary role, not only journal name. A hardware proof, an algorithm benchmark and an evaluation-method paper need different evidence.

## 2. Build the evidence-linked comparison table

Minimum manuscript paragraph fields:

```text
paper_id, paragraph_id, source_hash, source_lines_or_page_span,
section_id, previous_output, rhetorical_role, argument_action, output_to_next,
terminology_entities, evidence_links, writing_0_4, section_0_4,
issue_codes, comparator_ids, verdict, review_note, confidence
```

Keep tables, equations, captions and administrative declarations outside the prose denominator. Research-question and contribution lists may be separate units. PDF blocks are only paragraph candidates for published papers; source-document blank-line paragraphs are preferable for manuscripts.

Useful section fields:

```text
input_promise, section_task, output_to_next, required_by_claim_or_experiment,
duplicated_function, missing_function, score_0_4, evidence_anchors
```

Useful experiment fields:

```text
RQ, estimand, analysis_unit, data_roles, selection_boundary, evaluation_boundary,
strongest_comparator, controlled_difference, confounders, metric, failure_rule,
negative_results, cost, supported_claim, unsupported_claim
```

Never replace unknown values with zero. Use `not_assessed`, `not_reported`, `not_applicable`, `extraction_failed` and `uncertain` distinctly.

## 3. Review at five linked scales

### A. Paragraph writing

Ask what the paragraph does, not merely whether it is grammatical.

- Is there one center and a complete local action: motivate, define, derive, contrast, report, qualify or synthesize?
- Are technical terms bound to an entity, equation, algorithm, measurement or explicit assumption?
- Does the paragraph depend on a previous promise and produce information needed next?
- Is it necessary in the main text, or is it version history, resource accounting or repeated caveating?

Long paragraphs, dense numbers and cautious wording are review cues, not automatic defects. Penalize the loss of the center, not negative results or honest uncertainty.

### B. Section function and quality

- What independent argumentative task does the section complete?
- Does it introduce a needed object, prove a needed property, answer a question or interpret a result?
- Is its function already performed elsewhere? Can the reader identify its output without reading the supplement's version history?
- Are headings organized by research questions rather than by the chronology of revisions?

A section can be rigorous and still need relocation. “Move to supplement” is a presentation judgment, not deletion of evidence.

### C. Experiment design

Create an RQ-by-evidence matrix before counting experiments. Each row must state the alternative explanation that the design can reject. Separate:

- mechanism/implementation checks;
- component attribution;
- complete-predictor comparison;
- robustness/generalization;
- engineering or field validation;
- reproducibility/record reconstruction.

Do not pool these into an experiment count. Seeds, datasets, scenarios, checkpoints and reanalysis rows are not independent systems by default. Check selection exposure across rounds, not only within a single split.

### D. Experimental effect and strength

Evaluate point estimate, effect scale, direction, uncertainty, dependence, adverse cases, cost and external validity separately. Distinguish:

- a numerically active mechanism from a useful mechanism;
- lower approximation error from a better downstream decision;
- source calibration from target confirmation;
- development evidence from independent confirmation;
- a descriptive screen from a calibrated population interval.

Negative and null results are not defects. Selective reporting, incompatible estimands and claims that exceed the evidence are defects.

### E. Section semantics and the academic idea

For Related Work, ask whether each literature cluster changes a design choice and whether the final gap follows from the reviewed evidence.

For Abstract + Introduction, ask for one sentence that a non-author can repeat: known difficulty → specific insight → evaluated object → main finding → boundary. Check that the same object dominates the title, contributions, method and conclusion.

For the framework/method chapter, reconstruct:

```text
object -> assumptions -> definitions -> algorithm/derivation -> executable mapping
-> what is actually proved -> what is not implied -> matching validation
```

Local algebra need not produce a global performance theorem. Do not demand extra theory when the actual contribution is evaluation or engineering, but do not let formulas serve as decoration.

## 4. Gates before weighted or ordinal comparison

- **G0 readability/definitions**: a central object or computation is not determined by the file under review.
- **G1 one academic idea**: title, abstract, RQs, methods and conclusion do not converge on one contribution.
- **G2 claim–evidence fit**: score is offered as mechanism, local property as universal performance, or exposed development data as independent confirmation.
- **G3 experiment coherence**: experiments do not answer the current RQ or merely accumulate versions and resource counts.
- **G4 terminology substance**: branded terms lack stable entities, inputs/outputs or executable meaning.
- **G5 narrative closure**: literature is a name dump, a method lacks a corresponding test, or the conclusion hides adverse evidence/adds claims.
- **G6 submission facts**: authors, rights, access, disclosures and adoption remain unresolved.

G0/G1/G2/G4 cannot be averaged away by strong experiments or prose. G3 normally requires restructuring. G6 is reported separately from the scientific-text verdict.

## 5. Research-history and experiment-inflation diagnostics

Flag these patterns explicitly:

1. Introduction lists RQs or contributions in the order they were added during revisions.
2. Method and result section numbers grow by appending each new study rather than by question.
3. Abstract emphasizes a later experiment while the title emphasizes an earlier method.
4. Every result paragraph repeats AC/SC, seed, run, opportunity, hash or replay counts.
5. Internal IDs and supplement keys replace scientific roles in the main narrative.
6. Limitations are appended separately for each historical branch instead of being grouped by validity threat.
7. Reproducibility receipts occupy more main-text space than the scientific finding they support.

These are not reasons to delete adverse results. Preserve all outcomes and move lineage, full matrices and resource ledgers to supplements with stable links.

## 6. Scoring and decision

Use 0–4 ordinal judgments only as advisory anchors:

- 0 = missing or contradictory;
- 1 = central failure;
- 2 = partial support with major weakness;
- 3 = adequate within explicit limitations;
- 4 = strong, direct and evidence-linked.

Do not compute an acceptance verdict by averaging the five dimensions. Report each dimension, failed gates and evidence coverage. Use the venue's actual labels; for IEEE Access use only:

- `Accept, minor edits permitted`;
- `Reject, updates required before resubmission`;
- `Reject, resubmission not permitted`.

Separate scientific-text verdict from submission readiness. Record whether the work was read in full, section-calibrated, automatically screened, independently reviewed or checked only by the same informed assistant. Do not call a same-model, same-assistant synthesis a blind panel.

## 7. Deliverables and acceptance tests

A complete review should contain:

- corpus manifest with actual version statements and hashes;
- published-paper profiles with evidence anchors and cautions;
- paragraph and section tables;
- RQ-by-experiment matrix and claim–evidence ledger;
- failed gates, dimension judgments and venue-calibrated verdict;
- prioritized revision actions with acceptance tests;
- explicit review limitations and unassessed scope.

A revision recommendation is accepted only when its intended test is meaningful: e.g. one sentence now identifies the same object in title, abstract, RQ, method and conclusion; every main experiment has one RQ and one alternative explanation; all adverse outcomes remain linked after relocation; no main-text claim depends on an internal version ID to be understood.

## 8. Figures, tables and visual evidence

Treat figures and tables as evidence, not decoration. Build the inventory before judging it: figure/table label, final-PDF page, source line, caption, producing source, first callout, linked RQ/claim, and whether source data or a numeric audit exists.

Use two visual scales:

- full-paper thumbnails for chart density, section rhythm, evidence order and main-line visibility;
- high-resolution pages for font size, axes, units, legends, grayscale/color-blind readability, panels, table notes and internal labels.

For every main figure/table, answer:

- Which RQ and exact claim does it support?
- Does a mechanism diagram show inputs, state changes and outputs, rather than only names?
- Does a result table have one estimand and one main contrast, with units, sample, uncertainty and exclusions in its notes?
- Can the caption be understood without hunting through the text?
- Are adverse directions, UNKNOWN cases and dependence limits visible?
- Is the object a genuine engineering validation, an illustrative example, or a reconstruction? Do not confuse them.

Do not infer exact unlabeled values from a plot. Mark `VISUAL READ ONLY - AUTHOR VERIFY` when source data are unavailable. A readable oversized table can still fail through information architecture: mixed evidence generations, internal IDs and unrelated control families should be split or moved to SI. Do not use a fixed row-count threshold as a substitute for judgment.

## 9. Evidence distillation and authorial rhythm

Use published papers as teachers for evidence patterns, not as prose to imitate. Distill four layers:

1. argument skeleton: problem → insight → validation → outcome → boundary;
2. evidence function: which alternative explanation each experiment/figure/table can reject;
3. visual pattern: mechanism diagrams, one-contrast tables, regime plots and engineering photo-plus-measurement chains;
4. language rhythm: short claim sentences and only those longer mechanism sentences that carry real conditions or reasoning.

Keep a negative-distillation blacklist: grammar defects, cross-task score comparisons, pseudo-replication, decorative figures, giant lookup tables, unsupported precision and hidden adverse results. Publication does not make those behaviors valid.

Evaluate AI-like writing in this order:

- P0 unsupported content, contradictions and claim-scope drift;
- P1 templated reasoning, concept stacks without causal progression, RQs appended by revision history, evidence detached from the claim;
- P2 uniform cadence, repeated connectors, mechanical triads, inflated nominalizations and formatting habits.

Sentence-length CV, short/long alternation, repeated openers and vocabulary lists are review leads, not authorship detectors. Do not force sentence variation, insert colloquialisms or errors, synonym-spin, or delete required uncertainty. First repair the scientific chain; then restore natural cadence by giving each paragraph one genuine action. A fluent paragraph with no necessary role remains a defect.

A multimodal review additionally ships the figure/table inventory, thumbnail manifest, key-page visual findings, sentence-rhythm candidates and protected-content comparison. Acceptance requires that each main display has a named RQ and claim, captions are self-contained, visual-only values are marked for verification, and no adverse result disappears during visual or narrative distillation.
