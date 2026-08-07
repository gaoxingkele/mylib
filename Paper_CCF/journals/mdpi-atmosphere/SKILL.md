---
name: mdpi-atmosphere
description: Use when targeting MDPI Atmosphere for atmospheric science, air quality, meteorology, and climate–energy coupling where the atmosphere is the object of study. Read ../../resources/mdpi-common.md.
---

# Atmosphere (MDPI)

## Journal positioning

Atmosphere (ISSN 2073-4433, monthly, gold OA) covers **atmospheric science** — meteorology, air quality, aerosols, atmospheric chemistry/physics, climate applications.

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **2.6**; CiteScore ~Q2 Environmental Science (misc.). APC ≈ **CHF 2,400**. First decision ≈ **19.7 days**. Indexed SCIE, Scopus, Ei, GEOBASE. Homepage: https://www.mdpi.com/journal/atmosphere

## When to trigger / scope

- Weather/climate modeling, air pollution, atmospheric retrievals, extreme weather.
- Power×CS: wind/solar meteorological drivers only if **atmosphere is primary**; EO-primary → Remote Sensing; grid-primary → Energies.
- Weak fit: load forecasting with weather as one feature among many.

## Venue-specific calibration

**Reviewer lens:** atmospheric datasets + physical consistency. Fingerprint: meteorology · air quality · climate applications.

## Method & evidence bar / house style

ERA5/station networks; standard atmospheric metrics; leakage-safe temporal splits for ML.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~27 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 0/10.
- Lexical signals (first pages): baseline/comparison ≈ 3/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 2/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [other] Interpreting Mobile and Handheld Air Sensor Readings in
  - [power] Carbonaceous Particulate Matter Emitted from a Pellet-Fired
  - [other] Review of Sunset OC/EC Instrument Measurements During the
  - [other] The Fire and Smoke Model Evaluation Experiment—A Plan for
  - [other] Volatile Organic Compound Emissions from Prescribed Burning
  - [other] Gas-Phase Reaction of trans-2-Methyl-2-butenal with Cl:
  - [other] Quantifying the Public Health Benefits of Reducing Air Pollution:
  - [other] Regional and Urban-Scale Environmental Influences of Oceanic
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-atmosphere/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-atmosphere/`.
- **Length:** pages mean/median **26.7/27.5** (range 19–32); words mean/median **9311/8746**.
- **Structure:** sections mean **13.8**; paragraphs mean **63.0**; words/paragraph mean/median **143.8/144.6**.
- **Artifacts:** formulas≈**12.4**; figures≈**9.1**; tables≈**2.9**; block-diagrams≈**0.3** (mentions). Block-diagram sections: other×1, 2.1 Pellet Fuels×1, abstract×1, Abstract×1, back×1, References×1.
- **Experiment load:** datasets mentioned≈**0.7**/paper; named algorithms≈**0.9**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'moderate': 3, 'solid': 6, 'strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **96** words / **4.3** sentences; dominant pattern: `missing` (top patterns [('missing', 5), ('descriptive', 2), ('gap/background', 2)]).
- **Conclusion craft:** mean **186** words; dominant pattern: `limitations` (top [('limitations', 4), ('missing', 3), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~840 words / ~6.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~37 words / ~1.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~447 words / ~3.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~610 words / ~4.7 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~369 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Atmosphere, Basel, Author, Page, EPA Author Manuscript EPA, Author Manuscript EPA Author, Manuscript, October, Health, PubMed, July, March.
- **Frequent named algorithms:** GA(6), Adam(2), attention(1).
- **Frequent dataset/benchmark cues:** dataset(4), Dataset(1), UCI(1), data set(1).
- **Common sentence openings:** `EPA Author Manuscript EPA Author Manuscript`; `Environmental Protection Agency Research Triangle Park`; `Environmental Protection Agency Washington DC USA`; `Conflicts of Interest The authors declare`; `Author manuscript available in PMC October`; `Author Manuscript Author Manuscript Author Manuscript`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-atmosphere/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=12** mapped local PDFs (mean ~24.5 pages extracted).
- **Dominant IdeaSpark move:** `outside_taxonomy` — *outside_taxonomy*.
- **Dominant journal-house move:** `survey_or_review_synthesis` — *Survey / Taxonomy Synthesis*.
- IdeaSpark primary distribution: `outside_taxonomy`×7, `heterogeneous_decomposition`×1, `adapt_via_conditioning`×1, `generative_process_redesign`×1, `unify_into_shared_representation`×1, `structural_prior_encoding`×1.
- Journal-house distribution: `survey_or_review_synthesis`×5, `systems_security_or_iot_stack`×2, `named_stack_plus_case`×2, `hardware_or_field_validation`×2.
- Attested multi-pattern combos: sparse.
- Evidence readiness: baseline **67%**, ablation **17%**, dataset/benchmark **33%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-atmosphere/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-atmosphere_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-atmosphere`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **70%**, experiments/results **90%**, conclusion **70%**.
- Multimodal density (mean/paper): figures **0.9**, tables **0.2**, algorithms **0.0**, equation markers **1.1**.
- CPA evidence signals: baseline cues **20%**, ablation **0%**, dataset/benchmark **0%**, data-availability **30%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `outside_taxonomy`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 2,400; ~20 d first decision.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: no atmospheric science content.
- Re-route: Remote Sensing | Energies | Sensors.

## Output format

```text
[Target] Atmosphere (MDPI)
[Fit] High / Medium / Low (atmosphere primary?)
[Cost/Speed] ~CHF 2,400 · ~20d · IF~2.6
[Re-route] Remote Sensing | Energies | Sensors
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
