---
name: ieee-internet-of-things-journal
description: Use when targeting IEEE Internet of Things Journal (IoT-J) — a selective hybrid IEEE journal for IoT architectures, protocols, services, and applications. Encodes novelty+system evidence bar, page charges, hybrid OA APC, and review timelines.
---

# IEEE Internet of Things Journal (IoT-J)

## Journal positioning

IEEE Internet of Things Journal (ISSN 2327-4662) is a **selective, high-IF hybrid** journal jointly published by IEEE Sensors Council, ComSoc, Computer Society, and Signal Processing Society. It publishes advances and reviews on **IoT system architecture, enabling technologies, communication/networking, services/applications, and social implications**. Unlike MDPI Future Internet, **novelty, system significance, and IoT centrality** are gated.

- Metrics (as-of 2026-08 — **verify https://ieee-iotj.org/**): IF ≈ **8.7–8.9** (**Q1**); 5-year IF ~9+. Average submission→first decision ≈ **6.9 weeks**; submission→ePublication ≈ **14.5 weeks**. Acceptance rate roughly ~20% (secondary reports — verify).

## When to trigger / scope

- IoT architectures, protocols, edge intelligence, sensing+network stacks, smart-city/smart-grid **as IoT systems**.
- Power×CS: DER/AMI/edge state estimation, LLM-aided edge learning for distribution sensing — must be **IoT-system framed**.
- Weak fit: offline ML on CSV; pure power markets; non-networked algorithms → Energies / Algorithms / Access.

## Venue-specific calibration

- **Reviewer lens:** IoT contribution + rigorous evaluation (testbed, traces, large-scale sim) + comparison to recent IoT-J/ComSoc baselines.
- Fingerprint: selective IEEE · hybrid OA · page charges · single-blind · ORCID required · IoT centrality.
- Official: ieee-iotj.org + Author Guidelines PDF.

## Method & evidence bar / house style

- System/architecture contribution clear in abstract; threat/scale model if security; reproducible settings; strong related work vs recent IoT-J papers.
- IEEE template; **mandatory page charge ~US$175/page after first 8 pages** (verify guidelines). ORCID for all authors. Plagiarism screening. ≥2 independent reviewers, single-blind.

## APC / hybrid OA

- Traditional subscription track: **no OA APC** (subscribers access).
- OA track: APC ≈ **US$2,695** for 2025 submissions (2024 was $2,495) — verify current. IEEE/Society member discounts may apply (not for students). Overlength page charges separate.

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~10 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 8/10.
- Lexical signals (first pages): baseline/comparison ≈ 2/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 3/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power] 15796 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021
  - [other] 15694 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021
  - [algo] IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 12, JUNE 15, 2021 9603
  - [algo] IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021 15847
  - [algo] IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021 15855
  - [algo] 15884 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021
  - [algo] 15652 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 21, NOVEMBER 1, 2021
  - [power,algo] 12826 IEEE INTERNET OF THINGS JOURNAL, VOL. 8, NO. 16, AUGUST 15, 2021
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/ieee-internet-of-things-journal/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/ieee-internet-of-things-journal/`.
- **Length:** pages mean/median **10.4/9.5** (range 8–21); words mean/median **7032/6342**.
- **Structure:** sections mean **8.9**; paragraphs mean **47.6**; words/paragraph mean/median **145.0/144.6**.
- **Artifacts:** formulas≈**7.2**; figures≈**8.5**; tables≈**0.0**; block-diagrams≈**0.7** (mentions). Block-diagram sections: other×5, I I NTRODUCTION×2, III COVID-19×1, 5 TREC-COVID ad×1, 3 An integrated IoT-enabled machine lear×1.
- **Experiment load:** datasets mentioned≈**4.1**/paper; named algorithms≈**3.3**/paper; baseline signal **9/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 2, 'strong': 2, 'very_strong': 6}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **0** words / **0.0** sentences; dominant pattern: `missing` (top patterns [('missing', 10)]).
- **Conclusion craft:** mean **0** words; dominant pattern: `missing` (top [('missing', 10)]).
- **Chapter size/role (corpus means):**
  - **method**: avg ~408 words / ~3.0 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~1133 words / ~7.8 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
- **Frequent terms:** COVID-19, IEEE INTERNET, THINGS JOURNAL, IEEE, Internet, University, NOVEMBER, IoMT, Things, Online, Available, However.
- **Frequent named algorithms:** attention(6), CNN(5), SVM(4), LSTM(3), ResNet(2), XGBoost(2), random forest(2), PSO(2).
- **Frequent dataset/benchmark cues:** data set(8), IEEE 2020(5), dataset(4), IEEE 2021(3), Kaggle(3), DATA SET(3), benchmark(3), data
set(2).
- **Common sentence openings:** `IEEE INTERNET OF THINGS JOURNAL VOL`; `These value-added sensors have revolutionized the`; `These embedded sensors could also be`; `Governments and regulators are turning to`; `The outbreak of COVID-19 in December`; `The use of embedded sensors could`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/ieee-internet-of-things-journal/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~10.4 pages extracted).
- **Dominant IdeaSpark move:** `generative_process_redesign` — *Liberate a Fixed Generative Component*.
- **Dominant journal-house move:** `systems_security_or_iot_stack` — *Systems / IoT / Security Stack*.
- IdeaSpark primary distribution: `generative_process_redesign`×3, `controlled_diagnostic_design`×3, `architectural_operator_substitution`×2, `outside_taxonomy`×1, `unify_into_shared_representation`×1.
- Journal-house distribution: `systems_security_or_iot_stack`×7, `named_stack_plus_case`×2, `survey_or_review_synthesis`×1.
- Attested multi-pattern combos: `architectural_operator_substitution+generative_process_redesign`, `architectural_operator_substitution+controlled_diagnostic_design`, `decompose_and_delegate+generative_process_redesign`, `generative_process_redesign+heterogeneous_decomposition`, `controlled_diagnostic_design+unify_into_shared_representation`.
- Evidence readiness: baseline **40%**, ablation **20%**, dataset/benchmark **90%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/ieee-internet-of-things-journal/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/ieee-internet-of-things-journal_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `ieee-internet-of-things-journal`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **0%**, method **10%**, experiments/results **40%**, conclusion **0%**.
- Multimodal density (mean/paper): figures **0.0**, tables **0.0**, algorithms **0.4**, equation markers **0.4**.
- CPA evidence signals: baseline cues **80%**, ablation **0%**, dataset/benchmark **40%**, data-availability **0%**, code-availability **10%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `systems_security_or_iot_stack`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Desk-reject / re-routing

- Not IoT-centric; incremental app without system novelty; weak evaluation.
- Re-route: Future Internet / Sensors (faster OA); IEEE Access (soundness); TII / TNSM / Sensors Journal (siblings); Energies (energy-primary).

## Output format

```text
[Target] IEEE Internet of Things Journal
[Fit] High / Medium / Low (IoT system novelty?)
[Cost/Speed] hybrid; OA ~US$2,695 + page charges · ~7 wk first decision · IF~8.7 Q1
[Main evidence gap] <testbed / IoT baselines / overlength plan>
[Re-route] Future Internet | Sensors | IEEE Access | TII
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
