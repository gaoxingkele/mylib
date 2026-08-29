---
name: wiley-ccpe
description: Use when targeting Concurrency and Computation Practice and Experience (Wiley) for parallel/distributed/HPC/cloud/edge systems and concurrent algorithms. Encodes hybrid model, scope around concurrency, and evidence expectations.
---

# Concurrency and Computation: Practice and Experience (CCPE)

## Journal positioning

CCPE (Wiley, ISSN 1532-0626 / 1532-0634) publishes original research and reviews on **parallel and distributed computing**, HPC, computational/data science, AI/ML systems, big data, security, cloud/edge/fog, green and quantum computing — with **concurrency/distributed systems practice** as the connective tissue. Homepage: https://onlinelibrary.wiley.com/journal/15320634.

- Metrics (as-of 2026-08 — **verify Wiley/Clarivate**): IF historically ~**1.5** range; Scopus CiteScore ~**5.4** (Scimago) — confirm current JCR. Hybrid journal (subscription + OA option).

## When to trigger / scope

- Parallel algorithms, distributed systems, cloud/edge scheduling, concurrent ML training/serving, HPC practice.
- Power×CS: **distributed grid simulation, edge scheduling for DER fleets, concurrent optimization** — concurrency must be real.
- Weak fit: single-threaded forecasting notebook.

## Venue-specific calibration

- **Reviewer lens:** scalability, concurrency correctness/performance, experimental methodology on parallel platforms.
- Fingerprint: Wiley · hybrid · practice & experience · parallel/distributed.

## Method & evidence bar / house style

- Speedup/scalability curves, platform specs, baselines; Wiley author guidelines; data availability encouraged.
- OA APC if choosing gold OA — **verify current Wiley OA price** for CCPE (varies by agreement).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~18 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 3/10; algorithm/ML ≈ 5/10.
- Lexical signals (first pages): baseline/comparison ≈ 3/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 4/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power,algo] CONCURRENCY AND COMPUTATION: PRACTICE AND EXPERIENCE
  - [power] Received: 19 March 2018 Revised: 9 July 2018 Accepted: 10 July 2018
  - [algo] Received: 15 April 2019 Revised: 4 July 2019 Accepted: 13 August 2019
  - [other] Received: 30 November 2021 Revised: 28 July 2022 Accepted: 29 August 2022
  - [algo] Received: 10 November 2021 Revised: 20 January 2022 Accepted: 23 January 2022
  - [other] Received: 12 March 2022 Revised: 1 July 2022 Accepted: 8 August 2022
  - [other] Received: 29 January 2022 Revised: 7 June 2022 Accepted: 19 August 2022
  - [algo] Received: 11 December 2021 Revised: 30 March 2022 Accepted: 6 May 2022
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/wiley-ccpe/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/wiley-ccpe/`.
- **Length:** pages mean/median **17.7/17.5** (range 9–27); words mean/median **5842/4517**.
- **Structure:** sections mean **22.7**; paragraphs mean **34.7**; words/paragraph mean/median **197.4/143.2**.
- **Artifacts:** formulas≈**20.8**; figures≈**6.1**; tables≈**2.7**; block-diagrams≈**1.8** (mentions). Block-diagram sections: other×8, 3.2 Overall system architecture×1, method×1, 3.1 Featureselectioninslavenodesusingpro×1, 2 ANALYSING LCLS DATA AT NERSC×1, 2.1 Transferring Data to NERSC×1.
- **Experiment load:** datasets mentioned≈**1.2**/paper; named algorithms≈**2.0**/paper; baseline signal **5/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 5, 'very_strong': 1, 'moderate': 2, 'thin': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **33** words / **1.5** sentences; dominant pattern: `missing` (top patterns [('missing', 6), ('descriptive', 1), ('gap/background', 1)]).
- **Conclusion craft:** mean **150** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 7), ('restate contribution', 2), ('restate contribution → limitations → future work', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~533 words / ~3.9 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~453 words / ~3.5 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~205 words / ~1.6 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~610 words / ~4.7 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~126 words / ~1.5 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** COVID-19, Therefore, Here, Furthermore, However, According, Moreover, Hence, SPRINT, September, Copyright, John Wiley.
- **Frequent named algorithms:** CNN(3), Adam(2), SGD(2), attention(2), Random Forest(1), random forest(1), ADAM(1), ResNet(1).
- **Frequent dataset/benchmark cues:** dataset(6), benchmark(4), Dataset(1), data set(1).
- **Common sentence openings:** `Exper DOI cpe PARALLEL PERMUTATION TESTING`; `CONCURRENCY AND COMPUTATION PRACTICE AND EXPERIENCE`; `Exper Published online June in Wiley`; `DOI cpe SPECIAL ISSUE PAPER Optimization`; `Sloan1 Muriel Mewissen2 Thorsten Forster2 Michal`; `The amount of data produced by`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/wiley-ccpe/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~17.7 pages extracted).
- **Dominant IdeaSpark move:** `heterogeneous_decomposition` — *Decompose for Differentiated Treatment*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `heterogeneous_decomposition`×5, `assumption_audit_and_pivot`×2, `self_supervised_signal_engineering`×1, `controlled_diagnostic_design`×1, `outside_taxonomy`×1.
- Journal-house distribution: `named_stack_plus_case`×5, `hardware_or_field_validation`×2, `systems_security_or_iot_stack`×2, `survey_or_review_synthesis`×1.
- Attested multi-pattern combos: `generative_process_redesign+heterogeneous_decomposition`, `architectural_operator_substitution+heterogeneous_decomposition`, `algebraic_equivalence_unification+assumption_audit_and_pivot`, `architectural_operator_substitution+self_supervised_signal_engineering`.
- Evidence readiness: baseline **50%**, ablation **20%**, dataset/benchmark **60%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/wiley-ccpe/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/wiley-ccpe_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `wiley-ccpe`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **70%**, experiments/results **80%**, conclusion **50%**.
- Multimodal density (mean/paper): figures **5.3**, tables **1.3**, algorithms **0.1**, equation markers **2.2**.
- CPA evidence signals: baseline cues **10%**, ablation **0%**, dataset/benchmark **40%**, data-availability **10%**, code-availability **30%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Desk-reject / re-routing

- No concurrency/distributed angle.
- Re-route: IEEE TPDS / cluster computing venues; Future Internet; IEEE Access; Algorithms.

## Output format

```text
[Target] CCPE (Wiley)
[Fit] High / Medium / Low (concurrency/distributed central?)
[Model] Hybrid · verify OA APC
[Re-route] Future Internet | IEEE Access | Algorithms | TPDS-class
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
