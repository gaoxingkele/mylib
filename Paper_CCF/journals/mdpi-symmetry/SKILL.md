---
name: mdpi-symmetry
description: Use when targeting MDPI Symmetry or deciding whether a manuscript’s contribution is genuinely about symmetry/asymmetry. Not a generic CS dump venue. Read ../../resources/mdpi-common.md.
---

# Symmetry (MDPI)

## Journal positioning

Symmetry (ISSN 2073-8994, monthly, gold OA) covers **symmetry/asymmetry phenomena** across natural sciences and related mathematics/engineering. Gating rule: a **real symmetry/asymmetry, invariance, or structure-preserving** contribution — not keyword stuffing.

Read `../../resources/mdpi-common.md` for the shared MDPI model.

- Metrics (as-of 2026-08 — **verify on the journal homepage**): IF ≈ **2.2**; JCR **Q2 Multidisciplinary Sciences**; CiteScore Q1 General Mathematics. APC ≈ **CHF 2,400**. First decision ≈ **16.3 days**. Indexed SCIE, Scopus, Inspec. Homepage: https://www.mdpi.com/journal/symmetry

## When to trigger / scope

- Group/symmetry methods in ML, graph/network symmetry, symmetry-aware optimization, physical/chemical symmetry.
- Power×CS: only if **mathematical symmetry** (equivariant GNN, symmetric OPF) is the claimed contribution — else Energies/Mathematics/Algorithms.
- Weak fit: generic DL forecasting.

## Venue-specific calibration

**Reviewer lens:** "Where is the symmetry and why does it matter?" Fingerprint: symmetry/asymmetry · invariance · equivariance · multidisciplinary.

## Method & evidence bar / house style

Explicit symmetry definition + proof or constructive argument; ablations that stress the symmetry property.

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=10** (avg ~29 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 3/10; algorithm/ML ≈ 2/10.
- Lexical signals (first pages): baseline/comparison ≈ 3/10; ablation/sensitivity ≈ 0/10; dataset/benchmark ≈ 0/10.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power] Spontaneous Symmetry Breaking and Nambu–Goldstone Bosons
  - [power] arXiv:1503.00442v1  [hep-th]  2 Mar 2015
  - [other] Stability of Spline-Type Systems in the Abelian Case
  - [other] Some Generating Functions for q-Polynomials
  - [power] Revisiting a negative cosmological constant from low-redshift data
  - [other] Terminating Basic Hypergeometric Representations and
  - [algo] Increased Asymmetry of Trunk, Pelvis, and Hip Motion during
  - [other] Finite Element Analysis of an Implant-Supported FDP with
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-symmetry/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=10** PDFs under `fulltext_by_journal/mdpi-symmetry/`.
- **Length:** pages mean/median **28.8/21.0** (range 14–87); words mean/median **14936/5756**.
- **Structure:** sections mean **23.0**; paragraphs mean **100.3**; words/paragraph mean/median **145.3/145.6**.
- **Artifacts:** formulas≈**74.2**; figures≈**6.0**; tables≈**1.4**; block-diagrams≈**0.0** (mentions). Block-diagram sections: rarely lexicalized.
- **Experiment load:** datasets mentioned≈**0.5**/paper; named algorithms≈**1.3**/paper; baseline signal **6/10**; ablation/sensitivity **0/10**; strength histogram: {'solid': 3, 'moderate': 4, 'thin': 2, 'very_strong': 1}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 8, 'mixed': 2}).
- **Abstract craft:** mean **103** words / **4.3** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 7), ('missing', 2), ('gap/background', 1)]).
- **Conclusion craft:** mean **212** words; dominant pattern: `restate contribution` (top [('restate contribution', 3), ('limitations', 2), ('short wrap-up', 2)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~843 words / ~6.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~689 words / ~5.0 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~564 words / ~4.0 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~376 words / ~2.6 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Symmetry, Basel, Author, Page, Theorem, Author Manuscript Author Manuscript, PubMed, However, Phys, Planck, Refs, Lett.
- **Frequent named algorithms:** attention(4), GA(3), Ga(2), gA(1), Adam(1), Bert(1), bert(1).
- **Frequent dataset/benchmark cues:** dataset(2), Dataset(1), benchmark(1), data set(1).
- **Common sentence openings:** `Author Manuscript Author Manuscript Author Manuscript`; `NIST Author Manuscript NIST Author Manuscript`; `Spontaneous Symmetry Breaking and Nambu Goldstone`; `focus on manifestations of spontaneously broken`; `Topics covered include Introduction to the`; `Speci examples in both relativistic and`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-symmetry/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=12** mapped local PDFs (mean ~27.3 pages extracted).
- **Dominant IdeaSpark move:** `structural_prior_encoding` — *Encode Structure by Construction*.
- **Dominant journal-house move:** `survey_or_review_synthesis` — *Survey / Taxonomy Synthesis*.
- IdeaSpark primary distribution: `structural_prior_encoding`×9, `algebraic_equivalence_unification`×1, `assumption_audit_and_pivot`×1, `heterogeneous_decomposition`×1.
- Journal-house distribution: `survey_or_review_synthesis`×7, `named_stack_plus_case`×3, `hardware_or_field_validation`×1.
- Attested multi-pattern combos: `algebraic_equivalence_unification+structural_prior_encoding`, `heterogeneous_decomposition+structural_prior_encoding`, `reframe_as_solvable_object+structural_prior_encoding`, `architectural_operator_substitution+assumption_audit_and_pivot`.
- Evidence readiness: baseline **25%**, ablation **0%**, dataset/benchmark **8%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-symmetry/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-symmetry_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-symmetry`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=10** mapped local PDFs.
- Section presence rates: intro **100%**, method **40%**, experiments/results **40%**, conclusion **40%**.
- Multimodal density (mean/paper): figures **0.9**, tables **0.5**, algorithms **0.0**, equation markers **6.4**.
- CPA evidence signals: baseline cues **40%**, ablation **0%**, dataset/benchmark **0%**, data-availability **30%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `structural_prior_encoding` · journal-house: `survey_or_review_synthesis`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

APC ≈ CHF 2,400; ~16 d first decision; SI common.

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

- Desk: no genuine symmetry content.
- Re-route: Mathematics | Algorithms | Energies | Electronics | IEEE Access.

## Output format

```text
[Target] Symmetry (MDPI)
[Fit] High / Medium / Low (symmetry/asymmetry core?)
[Cost/Speed] ~CHF 2,400 · ~16d · IF~2.2
[Re-route] Mathematics | Algorithms | Energies | IEEE Access
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
