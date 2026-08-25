---
name: mdpi-information
description: Use when targeting MDPI Information or routing information-systems / knowledge / data / applied AI manuscripts to a fast OA CS venue. Encodes scope, soundness bar, APC, indexing, SI dynamics. Read ../../resources/mdpi-common.md first.
---

# Information (MDPI)

## Journal positioning

Information (est. 2010, ISSN 2078-2489, monthly, gold OA) is MDPI’s broad **information science & technology** journal — data, knowledge, communication, and applied computing. Fit on **methodological soundness + clear information/CS contribution**, not breakthrough novelty. Affiliated with IS4SI (member APC discounts).

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
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-information/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=30** mapped local PDFs (mean ~18.0 pages extracted).
- **Dominant IdeaSpark move:** `heterogeneous_decomposition` — *Decompose for Differentiated Treatment*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `heterogeneous_decomposition`×7, `generative_process_redesign`×5, `structural_prior_encoding`×4, `outside_taxonomy`×3, `algebraic_equivalence_unification`×2, `assumption_audit_and_pivot`×2.
- Journal-house distribution: `named_stack_plus_case`×12, `survey_or_review_synthesis`×7, `power_system_planning_ops`×3, `systems_security_or_iot_stack`×3, `hardware_or_field_validation`×2.
- Attested multi-pattern combos: `assumption_audit_and_pivot+structural_prior_encoding`, `assumption_audit_and_pivot+generative_process_redesign`, `algebraic_equivalence_unification+assumption_audit_and_pivot`, `heterogeneous_decomposition+self_supervised_signal_engineering`, `algebraic_equivalence_unification+decompose_and_delegate`.
- Evidence readiness: baseline **37%**, ablation **10%**, dataset/benchmark **63%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-information/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-information_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-information`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
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

```text
[Target] Information (MDPI)
[Fit] High / Medium / Low (information/CS contribution primary?)
[Cost/Speed] ~CHF 1,800 · ~19d · IF~4.3 Q2 (verify)
[Main evidence gap] <baselines / data statement / IS framing>
[Re-route] Algorithms | Electronics | Energies | IEEE Access
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
