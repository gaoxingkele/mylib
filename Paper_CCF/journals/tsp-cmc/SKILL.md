---
name: tsp-cmc
description: Use when targeting Computers, Materials & Continua (CMC, Tech Science Press) or deciding whether an applied CS/AI/materials-informatics manuscript fits this gold-OA journal. Encodes scope, IF/APC, house style, AI-disclosure expectations, and distill patterns from a local 10-paper power/algorithm corpus.
---

# Computers, Materials & Continua (CMC) — Tech Science Press

## Journal positioning

CMC (ISSN 1546-2218 print / 1546-2226 online, monthly, **gold OA**, CC BY) is TSP’s broad journal spanning **computer networks, AI, big data, SE, multimedia, cybersecurity, IoT, materials genome / multifunctional materials modeling**. It is a **mid-tier SCIE** venue: sound, complete applied papers with named method stacks routinely clear; groundbreaking novelty is not required. This skill is a **fit / framing** tool; official pages win.

- Metrics (as-of 2026-08 — **verify at https://www.techscience.com/journal/cmc**): SCI IF ≈ **2.4** (2025); Scopus CiteScore ≈ **6.6**; SNIP ≈ 0.777. Indexed SCIE, Scopus, Ei Compendex, Inspec, etc. APC ≈ **US$1,600** (TSP APC table — verify https://www.techscience.com/ndetail/apc).

## When to trigger / scope

- Applied **AI/ML, NLP, security, IoT, smart-grid informatics, materials/ continuum modeling with computation**.
- Power×CS: load forecasting, grid fault prediction, smart-grid anomaly/graph learning — strong local fit (see distill).
- Weak fit: pure power-system planning without CS/AI method; ultra-selective theory.

## Venue-specific calibration

- **Reviewer lens:** completeness of method + experiments + readable TSP template more than flagship novelty.
- Distinctive fingerprint: Tech Science Press · DOI `10.32604/cmc.*` · CC BY · Received/Accepted/Published dates on page 1 · AI drafting disclosure expected when LLMs used (TSP policy) · **do not invent gold labels with AI**.
- Official anchor: techscience.com/journal/cmc.

## Method & evidence bar

- Named architecture/algorithm stack; comparison tables; figures for architecture/ablation/attention; Data Availability / ethics / funding / COI.
- English must be workable; template compliance checked.

### Distilled review standards (10 local full-text PDFs, 2024–2026)

Corpus: `powergrid_benchmark/papers/literature/target_journal_related/cmc_pdfs/` (notes in `../../resources/target-journals-2026-batch-distill.md`).

- **Genres that clear:** (1) power load forecasting (clustering + BiGRU/attention stacks); (2) smart-grid anomaly via multi-expert graph learning; (3) meteorology→grid fault XGBoost with feature enhancement; (4) LLM/RAG/NER/security applied CS.
- **Novelty floor:** incremental **named combinations** (FE-XGBoost, Stacking-BiGRU-CBAM, RAG+LLM) with gap statement — not new theory.
- **Evidence floor:** datasets (public or constructed) + baselines + metrics (MAE/RMSE/F1/accuracy) + ablation or attention/feature analysis. Length typically **14–25 pages** (up to ~32 for agent systems).
- **House style signals:** TSP article header, author emails, Received/Accepted/Published line, CC BY footer.
- **Integrity:** if LLM used for writing, disclose per TSP; never present AI-simulated labels as human gold.

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~20 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 3/10; algorithm/ML ≈ 5/10.
- Lexical signals (first pages): baseline/comparison ≈ 6/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 6/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [algo] whichpermitsunrestricteduse,distribution,andreproductioninanymedium,providedthe
  - [other] ChineseNamedEntityRecognitionMethodforMuskDeerDomainBasedon
  - [other] UtilizingFine-TuningofLargeLanguageModelsforGeneratingSynthetic
  - [power,algo] Short-TermElectricityLoadForecastingBasedonT-CFSFDPClusteringand
  - [other] EnhancingDetectionofAI-GeneratedText:ARetrieval-Augmented
  - [algo] Retrieval-AugmentedLargeLanguageModelforAWSCloudThreatDetection
  - [other] MitigatingAdversarialObfuscationinNamedEntityRecognitionwithRobust
  - [power,algo] Multi-ExpertCollaborationBasedInformationGraphLearningforAnomaly
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/tsp-cmc/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/tsp-cmc/`.
- **Length:** pages mean/median **20.0/18.5** (range 14–32); words mean/median **5584/5168**.
- **Structure:** sections mean **13.9**; paragraphs mean **39.1**; words/paragraph mean/median **141.4/142.6**.
- **Artifacts:** formulas≈**13.7**; figures≈**5.9**; tables≈**4.2**; block-diagrams≈**1.7** (mentions). Block-diagram sections: other×8, experiment×2, 4 DatasetsandExperiments×1, 2 ContributionandScope×1, 4.7 PromptEngineeringStrategies×1, 5 ExperimentalSetup×1.
- **Experiment load:** datasets mentioned≈**2.2**/paper; named algorithms≈**5.7**/paper; baseline signal **9/10**; ablation/sensitivity **5/10**; strength histogram: {'very_strong': 6, 'solid': 1, 'strong': 3}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **152** words / **5.9** sentences; dominant pattern: `gap/background` (top patterns [('gap/background', 2), ('gap/background → method claim → quantitative result', 2), ('gap/background → quantitative result', 2)]).
- **Conclusion craft:** mean **203** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 4), ('restate findings', 3), ('limitations', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~596 words / ~4.3 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~842 words / ~6.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~179 words / ~1.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~502 words / ~3.9 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~462 words / ~3.4 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** ComputMaterContin, LLMs, China, However, BERT, Therefore, Specifically, F1-score, Zhang, XGBoost, Wang, Thus.
- **Frequent named algorithms:** BERT(5), CNN(5), attention(5), transformer(5), LSTM(5), Transformer(3), Adam(3), BiLSTM(3).
- **Frequent dataset/benchmark cues:** dataset(10), Dataset(5), benchmark(3), data set(1), Kaggle(1), kaggle(1), Benchmark(1).
- **Common sentence openings:** `This study investigates how text classification`; `Focusing on significant challenge in the`; `The adopted methodology encompasses comprehensive approach`; `Experiments conducted on text datasets in`; `The results indicate that the integration`; `Contributions of this work include the`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/tsp-cmc/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~20.0 pages extracted).
- **Dominant IdeaSpark move:** `structural_prior_encoding` — *Encode Structure by Construction*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `structural_prior_encoding`×3, `generative_process_redesign`×3, `heterogeneous_decomposition`×2, `outside_taxonomy`×1, `algebraic_equivalence_unification`×1.
- Journal-house distribution: `named_stack_plus_case`×5, `systems_security_or_iot_stack`×3, `survey_or_review_synthesis`×2.
- Attested multi-pattern combos: `adapt_via_conditioning+algebraic_equivalence_unification`, `generative_process_redesign+unify_into_shared_representation`, `adapt_via_conditioning+generative_process_redesign`, `self_supervised_signal_engineering+structural_prior_encoding`, `generative_process_redesign+heterogeneous_decomposition`.
- Evidence readiness: baseline **90%**, ablation **30%**, dataset/benchmark **90%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/tsp-cmc/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/tsp-cmc_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `tsp-cmc`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=20** mapped local PDFs.
- Section presence rates: intro **30%**, method **70%**, experiments/results **90%**, conclusion **20%**.
- Multimodal density (mean/paper): figures **1.5**, tables **3.5**, algorithms **0.2**, equation markers **3.4**.
- CPA evidence signals: baseline cues **60%**, ablation **30%**, dataset/benchmark **80%**, data-availability **0%**, code-availability **10%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Review process & timeline

- Peer-reviewed OA continuous publication. Expect **weeks-to-a-few-months** full cycle (verify current stats with editor/office). Single-blind typical of TSP engineering titles (confirm on instructions).
- APC charged after acceptance (~US$1,600).

## Official-cycle checklist / pre-submission self-check

- Open techscience.com/journal/cmc + APC + author instructions; download current TSP template.
- [ ] Scope is CS/AI/materials-informatics (not pure power engineering). [ ] Method stack named and validated. [ ] AI-use / drafting disclosure if applicable. [ ] Figures readable in TSP two-column/production style.

## Common desk-reject / re-routing

- Out of scope; incomplete experiments; poor English/template; integrity flags.
- Re-route: faster IEEE brand → **IEEE Access**; energy-primary → **Energies / Energy Reports**; selective IoT → **IEEE IoT Journal**; Nature-brand soundness → **Scientific Reports**; cheaper CS OA → **Discover Computing / PeerJ CS / Information**.

## Output format

```text
[Target] CMC (Tech Science Press)
[Fit] High / Medium / Low (applied CS/AI completeness)
[Cost/Speed] ~US$1,600 APC · mid-tier SCIE IF~2.4 (verify)
[Main evidence gap] <baselines / ablation / disclosure>
[Top rejection risk] scope / thin stack / integrity
[Re-route] IEEE Access | Energies | Scientific Reports | Discover Computing
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
