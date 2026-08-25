---
name: mdpi-future-internet
description: Use when targeting MDPI Future Internet for internet technologies, networking, IoT protocols, edge/cloud. Network/Internet framing must be central. Read ../../resources/mdpi-common.md.
---

# Future Internet (MDPI)

## Journal positioning

Future Internet (ISSN 1999-5903, monthly, gold OA) covers **Internet technologies and the information society** — protocols, architectures, IoT networking, edge/cloud, networked security.

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **4.6**; JCR **Q2** CS Information Systems; CiteScore Q1 Computer Networks. APC ≈ **CHF 1,800**. First decision ≈ **15 days**. Indexed Scopus, ESCI/WoS, Ei, dblp. Homepage: https://www.mdpi.com/journal/futureinternet

## When to trigger / scope

- Next-gen Internet, SDN/NFV, IoT networking, edge AI delivery, smart services.
- Power×CS: **AMI/DER communication, edge inference** — Internet/IoT stack primary; selective systems → IEEE IoT Journal; pure power flow → Energies.
- Weak fit: offline ML on CSV with no network architecture.

## Venue-specific calibration

**Reviewer lens:** architecture + protocol/latency/security evaluation. Fingerprint: Internet · IoT networking · edge/cloud.

## Method & evidence bar / house style

Architecture diagram; protocol/latency/throughput or security metrics; testbed or trace-driven evaluation.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~27 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 3/10.
- Lexical signals (first pages): baseline/comparison ≈ 1/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 2/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [other] Nederlandse Organisatie voor
  - [other] This is a peer-reviewed, final published version of the following document, © 2013 by the
  - [power,algo] Dynamic Cost-Aware Routing of Web Requests
  - [other] Internet of Nano-Things, Things and Everything:
  - [power,algo] SCADA System Testbed for Cybersecurity Research
  - [algo] StegNet: Mega Image Steganography Capacity with
  - [other] Blockchain based Decentralized Applications: Technology Review and
  - [other] /gid00030/gid00035/gid00032/gid00030/gid00038/gid00001/gid00033/gid00042/gid00045/gid00001
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-future-internet/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-future-internet/`.
- **Length:** pages mean/median **27.4/27.5** (range 15–45); words mean/median **11585/11276**.
- **Structure:** sections mean **25.3**; paragraphs mean **49.9**; words/paragraph mean/median **415.0/238.0**.
- **Artifacts:** formulas≈**9.1**; figures≈**9.1**; tables≈**2.4**; block-diagrams≈**0.5** (mentions). Block-diagram sections: other×4, back×1, References×1, 4 Architecture×1, 4.2 Separable Convolution with Residual ×1, 5.2 Decentralized application implementa×1.
- **Experiment load:** datasets mentioned≈**1.7**/paper; named algorithms≈**2.5**/paper; baseline signal **8/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 4, 'thin': 1, 'very_strong': 3, 'strong': 1, 'moderate': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 10}).
- **Abstract craft:** mean **160** words / **7.0** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 5), ('method claim', 2), ('gap/background', 2)]).
- **Conclusion craft:** mean **272** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 4), ('restate contribution', 3), ('limitations → future work', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~700 words / ~5.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **related_work**: avg ~262 words / ~2.2 paragraphs；核心写法：分主题综述 + 与本文差异句；少图表
  - **method**: avg ~291 words / ~2.1 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~420 words / ~3.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
- **Frequent terms:** Future Internet, However, Internet, Author, Moreover, Thus, Proceedings, Things, Cloud, June, Author Manuscript Author Manuscript, Page.
- **Frequent named algorithms:** attention(4), GA(2), CNN(2), Adam(2), ResNet(2), Attention(2), ga(1), Random
Forest(1).
- **Frequent dataset/benchmark cues:** dataset(5), benchmark(3), Dataset(2), Benchmark(2), ETTH(1), IEEE 802(1), IEEE 2012(1), IEEE 11073(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `We present both frameworks from the`; `The aim is to discuss and`; `We compare selected properties of both`; `Based on this comparison we evaluate`; `ONGERUBRICEERD ONGERUBRICEERD Nederlandse Organisatie voor toegepast-natuurwetenschappelijk`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-future-internet/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~27.4 pages extracted).
- **Dominant IdeaSpark move:** `generative_process_redesign` — *Liberate a Fixed Generative Component*.
- **Dominant journal-house move:** `systems_security_or_iot_stack` — *Systems / IoT / Security Stack*.
- IdeaSpark primary distribution: `generative_process_redesign`×3, `outside_taxonomy`×2, `controlled_diagnostic_design`×1, `unify_into_shared_representation`×1, `heterogeneous_decomposition`×1, `reframe_as_solvable_object`×1.
- Journal-house distribution: `systems_security_or_iot_stack`×5, `survey_or_review_synthesis`×4, `named_stack_plus_case`×1.
- Attested multi-pattern combos: `architectural_operator_substitution+generative_process_redesign`, `reframe_as_solvable_object+unify_into_shared_representation`, `generative_process_redesign+heterogeneous_decomposition`, `heterogeneous_decomposition+reframe_as_solvable_object`.
- Evidence readiness: baseline **40%**, ablation **0%**, dataset/benchmark **30%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-future-internet/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-future-internet_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-future-internet`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **70%**, experiments/results **40%**, conclusion **30%**.
- Multimodal density (mean/paper): figures **5.5**, tables **1.7**, algorithms **0.0**, equation markers **1.3**.
- CPA evidence signals: baseline cues **40%**, ablation **0%**, dataset/benchmark **20%**, data-availability **0%**, code-availability **10%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `survey_or_review_synthesis`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 1,800; ~15 d first decision.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: no Internet/network contribution.
- Re-route: IEEE IoT Journal | Sensors | Information | Energies | IEEE Access.

## Output format

```text
[Target] Future Internet (MDPI)
[Fit] High / Medium / Low (Internet/IoT/network central?)
[Cost/Speed] ~CHF 1,800 · ~15d · IF~4.6
[Re-route] IEEE IoT-J | Sensors | Information | Energies
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
