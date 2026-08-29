---
name: nature-scientific-reports
description: Use when targeting Scientific Reports (Nature Portfolio) or deciding whether a technically-sound multidisciplinary manuscript fits it. Soundness-not-novelty, Nature-branded megajournal — but honestly NOT fast (multi-month full cycle). Encodes fit, evidence bar, review model/speed, submission, desk-reject risks, and re-routing.
---

# Scientific Reports (Nature Portfolio)

## Journal positioning

Scientific Reports (Springer Nature, est. 2011, ISSN 2045-2322, gold OA CC BY) is one of the world's largest journals — a **soundness-not-novelty megajournal** (the PLOS ONE model) covering all natural sciences, medicine, psychology, and **engineering**. Manuscripts are judged solely on **scientific/technical validity and rigor**, explicitly **not** on perceived importance or impact. Good broad, stably-indexed, Nature-branded home and a friendly re-route target — **but be honest: it is NOT fast.** This is a **fit / framing** tool; official pages win.

- Metrics (as-of 2026-07 — **verify at https://www.nature.com/srep/**): IF ≈ **3.8–3.9** (drifted down from a ~4.3–4.6 peak), **Q1 Multidisciplinary Sciences**; CiteScore ≈ 5.8. Stably indexed SCIE, Scopus, PMC, DOAJ. APC ≈ **US$2,850** (verify).

## When to trigger / scope & fit

- Technically solid **original research** that is incremental, cross-disciplinary, negative/null, or replication, and doesn't need a high-impact narrative; broad indexed visibility desired.
- A **re-route/cascade target** after rejection from a selective Nature/discipline journal (transfer-friendly within Nature Portfolio).
- **Engineering / electrical / power / CS / AI in scope** (subject areas, not named standalone sections). Does **not** publish standalone narrative reviews as a primary type.

## Venue-specific calibration

- **Reviewer lens:** "Is it methodologically valid and rigorously supported?" — **not** "is it novel/important." Fingerprint: soundness-not-novelty · Nature Portfolio megajournal · single-blind · all natural sciences + engineering · Q1 multidisciplinary · CC BY · high-volume · not-fast · PLOS ONE analog.

## Method & evidence bar / house style

- Watertight methods/analysis/controls; mandatory data-availability and reporting-standards/ethics statements. Format-neutral at initial submission; Nature LaTeX/Word templates; submission via the Nature platform.

## Distilled patterns — power-grid open-data corpus (2026-07)

Local Nature OA exemplars + routing map (`../../resources/powergrid-open-data-corpus-distill.md`):

- **Scientific Reports fit (example in cache):** electricity-theft DL on SGCC smart-meter traces — soundness path = public/utility dataset + class-imbalance treatment (e.g. augmentation) + CNN/LSTM (or stronger) vs named baselines + F1/AUC. Novelty can be incremental; methods must be watertight.
- **Sibling Scientific Data (not a separate skill yet):** SDWPF wind-farm dataset paper (Sci Data 2024) — contribution is the **dataset + documentation + baseline task**, not a SOTA model. If the manuscript’s value is releasing/benchmarking a grid dataset (OPFData, PGLearn, large synthetic grids, ERA5 energy CF), prefer **Scientific Data** over Scientific Reports.
- **Vs IEEE Access:** same soundness philosophy; Access is faster for EE/CS authors who want IEEE branding; Sci Rep wins for multidisciplinary/Nature-brand visibility and stable Q1 multidisciplinary indexing.
- **Avoid:** standalone narrative reviews; thin ML papers without controls, imbalance handling, or leakage-safe splits on meter time series.

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~13 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 2/10; algorithm/ML ≈ 3/10.
- Lexical signals (first pages): baseline/comparison ≈ 1/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 1/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power] Lead Iodide Perovskite Sensitized
  - [algo] www.nature.com/scientificreports
  - [other] www.nature.com/scientificreports
  - [other] www.nature.com/scientificreports
  - [other] www.nature.com/scientificreports
  - [algo] www.nature.com/scientificreports
  - [algo] From Louvain to Leiden: guaranteeing well-connected communities
  - [power] www.nature.com/scientificreports
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/nature-scientific-reports/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/nature-scientific-reports/`.
- **Length:** pages mean/median **12.7/12.0** (range 7–25); words mean/median **7270/6774**.
- **Structure:** sections mean **8.7**; paragraphs mean **48.3**; words/paragraph mean/median **145.7/145.6**.
- **Artifacts:** formulas≈**35.7**; figures≈**20.8**; tables≈**0.8**; block-diagrams≈**0.2** (mentions). Block-diagram sections: experiment×1, Results×1.
- **Experiment load:** datasets mentioned≈**0.8**/paper; named algorithms≈**0.5**/paper; baseline signal **7/10**; ablation/sensitivity **0/10**; strength histogram: {'moderate': 2, 'solid': 7, 'strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 7, 'mixed': 3}).
- **Abstract craft:** mean **0** words / **0.0** sentences; dominant pattern: `missing` (top patterns [('missing', 10)]).
- **Conclusion craft:** mean **37** words; dominant pattern: `missing` (top [('missing', 8), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~628 words / ~4.0 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~741 words / ~5.4 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~847 words / ~6.2 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~449 words / ~3.0 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** However, Phys, Scientific  RepoRts, Golgi, After, Supplementary Fig, Brazil, PbI3, TiO2, CH3NH3, Aldrich, MeOTAD.
- **Frequent named algorithms:** attention(4), SVM(1).
- **Frequent dataset/benchmark cues:** benchmark(2), dataset(2), NREL(1), BenchMark(1), data set(1), Benchmark(1).
- **Common sentence openings:** `Lead Iodide Perovskite Sensitized All-Solid-State Submicron`; `Moser Michael Gra tzel2 Nam-Gyu Park`; `We report on solid-state mesoscopic heterojunction`; `The perovskite NPs were produced by`; `Illumination with standard AM-1 sunlight generated`; `Femto second laser studies combined with`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/nature-scientific-reports/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=10** mapped local PDFs (mean ~12.7 pages extracted).
- **Dominant IdeaSpark move:** `outside_taxonomy` — *outside_taxonomy*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `outside_taxonomy`×6, `generative_process_redesign`×3, `heterogeneous_decomposition`×1.
- Journal-house distribution: `named_stack_plus_case`×3, `survey_or_review_synthesis`×2, `hardware_or_field_validation`×1.
- Attested multi-pattern combos: `generative_process_redesign+heterogeneous_decomposition`, `algebraic_equivalence_unification+heterogeneous_decomposition`.
- Evidence readiness: baseline **40%**, ablation **0%**, dataset/benchmark **10%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/nature-scientific-reports/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/nature-scientific-reports_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `nature-scientific-reports`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=11** mapped local PDFs.
- Section presence rates: intro **9%**, method **82%**, experiments/results **64%**, conclusion **27%**.
- Multimodal density (mean/paper): figures **5.0**, tables **1.1**, algorithms **0.1**, equation markers **0.5**.
- CPA evidence signals: baseline cues **36%**, ablation **0%**, dataset/benchmark **36%**, data-availability **36%**, code-availability **18%**.
- CPA-scoped IdeaSpark dominant move: `outside_taxonomy` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Review process & timeline (be honest about speed)

- **Single-blind**, large Editorial Board + external referees. Nature markets a short **median first editorial decision (~20 days)**, but that is the first editorial touch — the **full review-to-acceptance cycle is typically multi-month (~4–6 months)**, often with multiple revision rounds because acceptance requires the analysis to be watertight. Acceptance rate ~50–57% (verify). **If raw turnaround is the goal, IEEE Access is faster for engineering/power/CS.**

## Fit signals, reputation nuance & pitfalls

- **Submit when:** sound, broad, cross-disciplinary work; want Nature-brand + stable indexing; a soundness-based re-route.
- **Reputation nuance:** legitimate, SCIE-indexed, Nature-branded, stable — but **prestige is moderate**; some committees discount megajournals (and may conflate it with *Nature*). Slower than the marketed first-decision number suggests.
- **Common rejections:** methodological/statistical flaws, insufficient data/controls, out-of-scope (pure review, or better suited to a specialist venue), weak reporting/ethics — **not** "insufficiently novel."

## Official-cycle checklist / pre-submission self-check

- Open nature.com/srep + about/APC pages; verify APC, IF/quartile, article types, reporting/ethics requirements. Official pages win.
- [ ] The work is **methodologically watertight** (soundness is the whole bar). [ ] You accept a **multi-month** timeline (not fast). [ ] Data-availability + reporting-standards + ethics statements complete. [ ] It is original research (not a standalone review).

## Re-routing decision

- Faster (engineering/power/CS): **IEEE Access**. Same soundness model: **PLOS ONE, Heliyon (check WoS status), MDPI Applied Sciences**. Higher tier (selective): **Nature Communications, Communications Engineering/Physics, PNAS Nexus**. Power-specific: **IEEE Access, MDPI Energies/Electronics, IET**.

## Output format

```text
[Target] Scientific Reports (Nature Portfolio)
[Fit] High / Medium / Low (one-line: soundness + broad-audience fit)
[Cost/Speed] ~US$2,850 APC · NOT fast (~4–6 mo full cycle; ~20-day first editorial touch only)
[Contribution type] original-research (incremental/cross-disciplinary/null/replication ok)
[Main evidence gap] <method/statistics/controls/reporting fix>
[Official items to re-check] APC / IF-quartile / reporting-standards / article types
[Top rejection risk] methodological-rigor / out-of-scope(review) / reporting-ethics
[Re-route suggestion] <IEEE Access if speed matters; PLOS ONE/Applied Sciences same model; Nature Comms if novel>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Index: `../../resources/journal-roster.md`; selection guide: `../../resources/journal-selection-guide.md`._
