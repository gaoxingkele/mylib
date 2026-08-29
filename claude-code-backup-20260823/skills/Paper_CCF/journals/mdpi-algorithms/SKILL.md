---
name: mdpi-algorithms
description: Use when targeting MDPI Algorithms for algorithm design, analysis, or empirical algorithmics. Algorithm contribution must be central. Read ../../resources/mdpi-common.md.
---

# Algorithms (MDPI)

## Journal positioning

Algorithms (ISSN 1999-4893, monthly, gold OA) focuses on **algorithm design, analysis, and applications**. The **algorithm itself** must be the primary contribution.

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **2.6**; JCR **Q2** CS Theory & Methods; CiteScore Q1 Computational Mathematics. APC ≈ **CHF 1,800**. First decision ≈ **17.6 days**. Indexed Scopus, ESCI/WoS, Ei. Homepage: https://www.mdpi.com/journal/algorithms

## When to trigger / scope

- New/improved algorithms, hybridization with analysis, benchmarking, metaheuristics with algorithmic claims.
- Power×CS: OPF/UC/forecasting **framed as algorithmic contribution**; energy-application-primary → Energies.
- Weak fit: off-the-shelf sklearn case study.

## Venue-specific calibration

**Reviewer lens:** Is there a clear algorithmic delta with baselines/ablation? Fingerprint: algorithms · complexity · empirical algorithmics.

## Method & evidence bar / house style

Pseudocode; complexity or ablation; ≥3 named baselines for empirical claims; sensitivity for metaheuristics.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~27 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 8/10.
- Lexical signals (first pages): baseline/comparison ≈ 1/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 3/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power] Learning over Knowledge-Base Embeddings for Recommendation
  - [algo] From the Quantum Approximate
  - [algo] /gid00030/gid00035/gid00032/gid00030/gid00038/gid00001/gid00033/gid00042/gid00045/gid00001
  - [power] Algorithmic Design of Geometric Data for Molecular Potential
  - [algo] Departments of Computational Medicine, Human Genetics, and Statistics, University of California,
  - [algo] Citation: Tahir, N.U.A.; Zhang, Z.;
  - [algo] Anomaly Detection in High-Dimensional Time Series Data with
  - [algo] Finding Multiple Optimal Solutions to an Integer Linear Program
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-algorithms/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-algorithms/`.
- **Length:** pages mean/median **26.6/22.0** (range 4–51); words mean/median **9510/7756**.
- **Structure:** sections mean **17.2**; paragraphs mean **64.0**; words/paragraph mean/median **145.4/147.2**.
- **Artifacts:** formulas≈**42.4**; figures≈**5.6**; tables≈**2.9**; block-diagrams≈**0.2** (mentions). Block-diagram sections: method×1, 2.1 The Original Quantum Approximate Opt×1, experiment×1, 4 Discussion×1.
- **Experiment load:** datasets mentioned≈**2.0**/paper; named algorithms≈**2.5**/paper; baseline signal **9/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 1, 'moderate': 3, 'strong': 3, 'thin': 1, 'very_strong': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 9, 'mixed': 1}).
- **Abstract craft:** mean **148** words / **6.7** sentences; dominant pattern: `missing` (top patterns [('missing', 3), ('gap/background → method claim', 2), ('gap/background → method claim → quantitative result', 1)]).
- **Conclusion craft:** mean **147** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 3), ('missing', 3), ('restate contribution', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~853 words / ~6.2 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~663 words / ~5.0 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~632 words / ~4.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~558 words / ~4.1 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~216 words / ~1.8 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Algorithms, Author Manuscript Author Manuscript, Author, However, While, Page, February, Hamming, Here, Algorithm, Hence, August.
- **Frequent named algorithms:** attention(4), GA(3), SVM(3), CNN(2), SGD(1), ResNet(1), TRansformer(1), Transformer(1).
- **Frequent dataset/benchmark cues:** dataset(7), Dataset(4), benchmark(3), data set(2), Benchmark(2), IEEE 1998(1), IEEE 2020(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `Author manuscript available in PMC August`; `Author manuscript available in PMC February`; `Learning over Knowledge-Base Embeddings for Recommendation`; `However structured knowledge bases exhibit unique`; `When the explicit knowl- edge about`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-algorithms/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=34** mapped local PDFs (mean ~19.3 pages extracted).
- **Dominant IdeaSpark move:** `heterogeneous_decomposition` — *Decompose for Differentiated Treatment*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `heterogeneous_decomposition`×8, `structural_prior_encoding`×4, `outside_taxonomy`×4, `assumption_audit_and_pivot`×4, `architectural_operator_substitution`×3, `relax_discrete_search_to_continuous`×3.
- Journal-house distribution: `named_stack_plus_case`×10, `survey_or_review_synthesis`×8, `systems_security_or_iot_stack`×6, `power_system_planning_ops`×5, `storage_or_energy_device_review`×2.
- Attested multi-pattern combos: `algebraic_equivalence_unification+architectural_operator_substitution`, `algebraic_equivalence_unification+heterogeneous_decomposition`, `heterogeneous_decomposition+structural_prior_encoding`, `decompose_and_delegate+heterogeneous_decomposition`, `assumption_audit_and_pivot+generative_process_redesign`.
- Evidence readiness: baseline **53%**, ablation **3%**, dataset/benchmark **62%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-algorithms/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-algorithms_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-algorithms`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **80%**, experiments/results **50%**, conclusion **50%**.
- Multimodal density (mean/paper): figures **1.8**, tables **1.0**, algorithms **0.5**, equation markers **3.4**.
- CPA evidence signals: baseline cues **60%**, ablation **0%**, dataset/benchmark **50%**, data-availability **30%**, code-availability **10%**.
- CPA-scoped IdeaSpark dominant move: `architectural_operator_substitution` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 1,800; ~18 d first decision; SI common.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: application-only; weak baselines.
- Re-route: Mathematics | Information | Energies | Electronics | IEEE Access.

## Output format

```text
[Target] Algorithms (MDPI)
[Fit] High / Medium / Low (algorithm = contribution?)
[Cost/Speed] ~CHF 1,800 · ~18d · IF~2.6
[Re-route] Mathematics | Information | Energies | IEEE Access
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
