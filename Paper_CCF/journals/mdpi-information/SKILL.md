---
name: mdpi-information
description: Assess MDPI Information fit, manuscript quality and submission readiness using official criteria and separately identified full-text observations. Use for Information journal selection, writing calibration or pre-submission review; do not infer acceptance probability from published examples.
metadata:
  calibration_version: "2026-09-22.1"
---

# Information (MDPI)

## Current calibration — required before assessment

Read `references/standards-and-evidence.md` for Information reviews and writing adaptation. It separates official rules, four DOI-verified full-text observations, and local review recommendations. Its evidence constraints supersede the legacy corpus heuristics below and any blanket soundness-only or SCIE claims in shared references.

Do not turn published-paper averages into minimum page, figure, equation, baseline or experiment counts. Do not infer acceptance rates, guaranteed easier acceptance, or journal-wide quality from these selected papers. A polished negative-result paper still needs a meaningful question and evidence supporting its diagnostic lesson.

## Field calibration — MA-SQLGrid upgrade case (2026-09-22, local observation)

Source: `Codex-Academic-Research/digests/mdpi-information-upgrade-2026-09.md`. One real cycle: an Applied Sciences manuscript migrated to *Information*, revised through two independent reviewer-style passes, benchmarked against same-journal and same-domain comparators, reduced from 42 to 30 pages, then returned to 31 pages when four relocated result figures were consolidated into one main-text overview.

- **Observed accepted-article length band (not a rule):** 16, 19, 21 and 33 pages for four *Information* full texts; 18, 24, 24, 24, 24 and 34 pages for nine sampled research PDFs. The journal states no maximum length and its APC does not scale with pages.
- **Display density is the reviewer-visible quantity.** Same-domain comparators carried 6 figures + 6 tables (SQL-GRID, 18 pages) and 1 figure + 8 tables (DKA-SQL). A 30-page manuscript with 2 figures + 6 tables was scored as display-sparse by an internal benchmark review; the fix was a four-panel results overview, not more prose.
- **Rules distilled from that cycle (apply as practice, not as journal requirements):**
  1. Length reduction relocates displays, never deletes them; register tables and figures separately and finish by proving every shipped figure file is referenced somewhere.
  2. A consolidated figure is re-plotted from frozen shipped summaries, its renderer ships with the submission, and no printed value is transcribed by hand.
  3. The supplementary PDF ships together with the markdown it was rendered from, byte-identical, and every archive file is declared in its manifest.
  4. Decide whether new experiments enter the paper with criteria pre-registered before the results are read; headline and abstract-level claims stay unchanged.
  5. Visible-evidence class (synthetic/development-visible · public non-domain · unseen expert-adjudicated) is stated with every conclusion, and unfinished external-validity work is named in Limitations with a route rather than hidden behind polish.
- **Deterministic audit for these items:** `Codex-Academic-Research/tools/manuscript_display_audit.py` (pages, overfull, undefined refs, float inventory, unreferenced labels, orphan figures, last-page headroom, tex/pdf/docx hashes, supplement dual-source equality).

## Meta review and revision loop

For an explicit meta-deconstruction scoring/revision/rescoring request, use
`C:/Users/10175/.codex/skills/paper-meta-review/SKILL.md` and its versioned rubric.
Keep initial and final scores on the same weights, bind manuscript hashes, and
preserve the atlas coverage limitations. This optional local score is advisory,
not a replacement for the evidence reference or an acceptance probability.

## Journal positioning

Information (est. 2010, ISSN 2078-2489, monthly, gold OA) covers information science and technology, data, knowledge and communication. Assess a clear information/CS contribution, novelty, significance and scientific soundness together; the official reviewer criteria do not waive novelty. Incremental or diagnostic work must explain what new knowledge it establishes. Affiliated with IS4SI (member APC discounts).

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **4.3** (2025 JCR); JCR **Q2** Computer Science, Information Systems; CiteScore Q1 Information Systems. APC ≈ **CHF 1,800**. Median first decision ≈ **18.7 days**; acceptance→publication ≈ **3.8 days**. Indexed Scopus, ESCI/WoS, Ei Compendex, dblp. Homepage: https://www.mdpi.com/journal/information

## When to trigger / scope

- Applied **information systems, knowledge graphs, IR, data mining, applied ML/AI** with an information/data/knowledge framing.
- Power×CS: forecasting / KG / RAG for utility docs — **foreground the information/computing contribution** (else Energies/Electronics).
- Weak fit: pure power planning with no IS/CS core.

## Venue-specific calibration

**Reviewer lens:** Is the information/computing method sound and validated? Fingerprint: information systems · knowledge · data · applied AI · fast OA · Special Issues. Official anchor: mdpi.com/journal/information.

## Method & evidence bar / house style

Named datasets/baselines for algorithmic claims; mandatory Data Availability Statement.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

**Legacy extraction observations, not current acceptance standards.** The following older n=10/n=30 mappings and parser-derived rates have not been revalidated against every source in the September calibration. Extraction artifacts, mixed article types and sample selection can distort counts. Preserve for provenance only; do not use the labels `strong` or `very_strong`, missing-keyword rates, or corpus averages to score a manuscript or relax its evidence requirements.

- Full-text sample: **n=10** (avg ~26 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 9/10.
- Lexical signals (first pages): baseline/comparison ≈ 1/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 2/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power,algo] A Review on Energy Consumption Optimization
  - [other] SDN-Based Intrusion Detection System for Early
  - [algo] Text Classiﬁcation Algorithms: A Survey
  - [algo] Albumentations: fast and ﬂexible image
  - [algo] COVID-19 Public Sentiment Insights and Machine
  - [power,algo] fastai: A Layered API for Deep Learning
  - [algo] An Ambient Intelligence-Based Human Behavior Monitoring
  - [algo] /gid00030/gid00035/gid00032/gid00030/gid00038/gid00001/gid00033/gid00042/gid00045/gid00001
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-information/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-information/`.
- **Length:** pages mean/median **26.5/23.5** (range 4–68); words mean/median **11516/11366**.
- **Structure:** sections mean **22.1**; paragraphs mean **58.4**; words/paragraph mean/median **225.6/149.4**.
- **Artifacts:** formulas≈**28.0**; figures≈**11.3**; tables≈**3.6**; block-diagrams≈**2.6** (mentions). Block-diagram sections: other×9, introduction×1, 1 Introduction×1, 6.1 Text and Document Feature Extraction×1, conclusion×1, 8 Conclusions×1.
- **Experiment load:** datasets mentioned≈**2.9**/paper; named algorithms≈**5.6**/paper; baseline signal **6/10**; ablation/sensitivity **1/10**; strength histogram: {'very_strong': 4, 'solid': 3, 'strong': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **131** words / **5.2** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 3), ('gap/background', 2), ('missing', 2)]).
- **Conclusion craft:** mean **224** words; dominant pattern: `limitations` (top [('limitations', 2), ('restate contribution → limitations', 2), ('missing', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1001 words / ~7.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~484 words / ~3.7 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~641 words / ~4.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~1157 words / ~6.9 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~430 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Information, However, Equation, There, Here, FOR PEER REVIEW, Appendix, HVAC, Number, Total, Articles, Algorithms.
- **Frequent named algorithms:** attention(9), Attention(4), CNN(4), random forest(3), Adam(3), LSTM(3), SVM(3), BERT(3).
- **Frequent dataset/benchmark cues:** dataset(8), Dataset(5), benchmark(4), Kaggle(2), kaggle(2), Mendeley(1), IEEE 2015(1), IEEE 1998(1).
- **Common sentence openings:** `To the best of knowledge no`; `Information doi FOR PEER REVIEW www`; `In the literature various techniques have`; `The goal of each technique was`; `Researchers have addressed the issue with`; `To the best of our knowledge`.
- **Use limitation:** section budgets and artifact density above are descriptive extraction outputs only. Allocate space according to the actual contribution and evidence; never add formulas or figures merely to match these averages. Use the current calibration reference for writing decisions.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-information/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=30** mapped local PDFs (mean ~18.0 pages extracted).
- **Dominant IdeaSpark move:** `heterogeneous_decomposition` — *Decompose for Differentiated Treatment*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `heterogeneous_decomposition`×7, `generative_process_redesign`×5, `structural_prior_encoding`×4, `outside_taxonomy`×3, `algebraic_equivalence_unification`×2, `assumption_audit_and_pivot`×2.
- Journal-house distribution: `named_stack_plus_case`×12, `survey_or_review_synthesis`×7, `power_system_planning_ops`×3, `systems_security_or_iot_stack`×3, `hardware_or_field_validation`×2.
- Attested multi-pattern combos: `assumption_audit_and_pivot+structural_prior_encoding`, `assumption_audit_and_pivot+generative_process_redesign`, `algebraic_equivalence_unification+assumption_audit_and_pivot`, `heterogeneous_decomposition+self_supervised_signal_engineering`, `algebraic_equivalence_unification+decompose_and_delegate`.
- Evidence readiness: baseline **37%**, ablation **10%**, dataset/benchmark **63%**.
- **Use limitation:** these inferred pattern labels may suggest questions to examine; do not match evidence rates or present them as editorial preferences. Verify the actual bottleneck, contribution and controls independently.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-information/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-information_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-information`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **90%**, method **60%**, experiments/results **50%**, conclusion **10%**.
- Multimodal density (mean/paper): figures **5.7**, tables **2.3**, algorithms **0.0**, equation markers **1.8**.
- CPA evidence signals: baseline cues **40%**, ablation **10%**, dataset/benchmark **70%**, data-availability **10%**, code-availability **30%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 1,800 after acceptance. Single-blind, ≥2 reviewers, ~19 d first decision. Heavy SI volume — vet Guest Editors.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: no information/CS contribution; thin unvalidated demo; poor English/format.
- Re-route: Algorithms / Mathematics (theory); Energies (energy-primary); IEEE Access / Scientific Reports (megajournal); Electronics.

## Output format

For a comprehensive assessment, use the current reference's dimension matrix and prioritized findings, including source anchors, repair criteria and unverified items. The brief routing card below is not a full review. Report the profile version and manuscript SHA; separate scientific quality, build/package readiness and author/portal actions. Do not invent a calibrated score, panel consensus or probability of acceptance.

```text
[Target] Information (MDPI)
[Fit] High / Medium / Low (information/CS contribution primary?)
[Cost/Speed] ~CHF 1,800 · ~19d · IF~4.3 Q2 (verify)
[Main evidence gap] <baselines / data statement / IS framing>
[Re-route] Algorithms | Electronics | Energies | IEEE Access
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
