---
name: mdpi-remote-sensing
description: Use when targeting MDPI Remote Sensing for EO/GIS/satellite/UAV sensing manuscripts, including renewable resource assessment from remote data. Sensing/EO must be central. Read ../../resources/mdpi-common.md.
---

# Remote Sensing (MDPI)

## Journal positioning

Remote Sensing (ISSN 2072-4292, semimonthly, gold OA) is a **high-volume Q1 geoscience/EO** journal. Affiliated societies (RSSJ, JSPRS) get APC discounts.

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **4.1**; **Q1** Geosciences, Multidisciplinary. APC ≈ **CHF 2,700**. First decision ≈ **24.3 days**. Indexed SCIE, Scopus, Ei, GeoRef, dblp. Homepage: https://www.mdpi.com/journal/remotesensing

## When to trigger / scope

- Satellite/aerial/UAV sensing, retrieval algorithms, irradiance/solar resource from EO, corridor monitoring.
- Power×CS: **GHI/DNI, PV potential mapping** — EO method primary; pure meter-data forecasting → Energies.
- Weak fit: non-spatial grid ML.

## Venue-specific calibration

**Reviewer lens:** sensor/product clarity + validation against ground truth. Fingerprint: EO · retrieval · GIS · validation.

## Method & evidence bar / house style

Name sensor/product (Sentinel, Landsat, Himawari, …), dates, processing chain, RMSE/MAE/bias vs priors.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~28 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 1/10; algorithm/ML ≈ 5/10.
- Lexical signals (first pages): baseline/comparison ≈ 2/10; ablation/sensitivity ≈ 1/10; dataset/benchmark ≈ 2/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [other] How Universal Is the Relationship between Remotely Sensed
  - [other] Atmospheric Correction Inter-comparison eXercise
  - [other] Decision-Tree, Rule-Based, and Random Forest Classification of
  - [other] High-Throughput Phenotyping of Canopy Cover and
  - [algo] Global Sensitivity Analysis of Leaf-Canopy-Atmosphere RTMs:
  - [algo] A Satellite-Based Spatio-Temporal Machine Learning
  - [algo] Assessment of Workﬂow Feature Selection on Forest
  - [other] A Survey of Active Learning for Quantifying Vegetation Traits
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-remote-sensing/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-remote-sensing/`.
- **Length:** pages mean/median **27.8/28.5** (range 13–44); words mean/median **10377/11119**.
- **Structure:** sections mean **18.5**; paragraphs mean **58.4**; words/paragraph mean/median **292.8/148.6**.
- **Artifacts:** formulas≈**11.8**; figures≈**9.4**; tables≈**3.8**; block-diagrams≈**0.9** (mentions). Block-diagram sections: introduction×2, 1 Introduction×2, back×2, References×2, other×2, conclusion×1.
- **Experiment load:** datasets mentioned≈**2.1**/paper; named algorithms≈**1.9**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'strong': 7, 'solid': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **187** words / **7.9** sentences; dominant pattern: `quantitative result` (top patterns [('quantitative result', 3), ('missing', 3), ('gap/background', 1)]).
- **Conclusion craft:** mean **250** words; dominant pattern: `limitations` (top [('limitations', 4), ('short wrap-up', 3), ('missing', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~948 words / ~6.8 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~470 words / ~3.5 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~441 words / ~3.3 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~585 words / ~4.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Remote Sens, Basel, Author, Page, Gaussian, RMSE, NDVI, However, July, NASA Author Manuscript NASA, Author Manuscript NASA Author, Manuscript.
- **Frequent named algorithms:** Random Forest(4), random forest(4), GA(3), Random forest(2), random 
forest(2), Adam(1), SVM(1), XGboost(1).
- **Frequent dataset/benchmark cues:** dataset(9), data set(4), Dataset(2), open data(2), Data Set(1), Data
set(1), benchmark(1), Open Data(1).
- **Common sentence openings:** `NASA Author Manuscript NASA Author Manuscript`; `NASA Public Access Author manuscript Remote`; `Published in final edited form as`; `Author manuscript available in PMC September`; `Europe PMC Funders Author Manuscripts Europe`; `How Universal Is the Relationship between`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-remote-sensing/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~27.8 pages extracted).
- **Dominant IdeaSpark move:** `generative_process_redesign` — *Liberate a Fixed Generative Component*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `generative_process_redesign`×4, `outside_taxonomy`×2, `reframe_as_solvable_object`×1, `architectural_operator_substitution`×1, `unify_into_shared_representation`×1, `self_supervised_signal_engineering`×1.
- Journal-house distribution: `named_stack_plus_case`×5, `systems_security_or_iot_stack`×3, `hardware_or_field_validation`×1, `survey_or_review_synthesis`×1.
- Attested multi-pattern combos: `assumption_audit_and_pivot+generative_process_redesign`, `generative_process_redesign+reframe_as_solvable_object`.
- Evidence readiness: baseline **30%**, ablation **30%**, dataset/benchmark **80%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-remote-sensing/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-remote-sensing_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-remote-sensing`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **90%**, experiments/results **90%**, conclusion **40%**.
- Multimodal density (mean/paper): figures **3.5**, tables **1.3**, algorithms **0.0**, equation markers **1.7**.
- CPA evidence signals: baseline cues **10%**, ablation **0%**, dataset/benchmark **30%**, data-availability **40%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 2,700; ~24 d first decision; large SI ecosystem.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: no remote-sensing data/method.
- Re-route: Atmosphere | Energies | Sensors | IEEE TGRS.

## Output format

```text
[Target] Remote Sensing (MDPI)
[Fit] High / Medium / Low (EO/sensing central?)
[Cost/Speed] ~CHF 2,700 · ~24d · IF~4.1 Q1
[Re-route] Atmosphere | Energies | Sensors | IEEE TGRS
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
