---
name: mdpi-mathematics
description: Use when targeting the MDPI journal Mathematics or deciding whether a manuscript with a genuine mathematical contribution (theorem/proof, rigorous model, convergence/complexity, well-founded numerical/optimization/ML-theory method) fits it. Applied-ML papers with no mathematical novelty are scope rejects. Read ../../resources/mdpi-common.md for the shared MDPI model.
---

# Mathematics (MDPI)

## Journal positioning

Mathematics (est. 2013, SCIE-indexed since 2018, ISSN 2227-7390, semimonthly, gold OA) covers the broad mathematical sciences, pure and applied. Gating fit rule: **there must be a genuine mathematical contribution** — a theorem/proof, a rigorously analyzed model, convergence/complexity results, or a well-founded numerical/optimization/ML-theory method — not merely "we used math / ran a model." Read `../../resources/mdpi-common.md` first for the shared MDPI model.

- Metrics (as-of 2026-07 — **verify at https://www.mdpi.com/journal/mathematics**): IF ≈ **2.3** (Q1 Mathematics, top ~10%), CiteScore ≈ **4.6** (Q1 General Mathematics); APC ≈ **CHF 2,600**; median ≈ **17.4 days** to first decision. Indexed SCIE, Scopus.

## When to trigger / scope & section fit

- Work whose contribution is mathematical: optimization theory, numerical methods, ML theory/algorithms with analysis, probability/statistics, dynamical systems, fuzzy/decision systems, network science, engineering mathematics.
- Restructured (2025) into ~13 MSC-aligned Sections including **Computational and Applied Mathematics**, **Mathematics and Computer Science**, **Engineering Mathematics**, **Probability and Statistics**, Fuzzy Sets & Decision, Network Science. **Verify at `/journal/mathematics/sections`.**
- **Power×CS/AI fit:** route optimization/numerical/ML-theory contributions via the CS/computational/engineering-math Sections — the **mathematical rigor** must be the contribution.

## Venue-specific calibration

- **Reviewer lens:** "Is there a formal/rigorous mathematical result or method, correctly proven/analyzed?" Fingerprint: optimization · theorem/proof · numerical methods · probability · dynamical systems · algorithms · fuzzy systems · applied mathematics.

### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=4** mapped local PDFs (mean ~14.0 pages extracted).
- **Dominant IdeaSpark move:** `algebraic_equivalence_unification` — *Prove Equivalence to Unify*.
- **Dominant journal-house move:** `survey_or_review_synthesis` — *Survey / Taxonomy Synthesis*.
- IdeaSpark primary distribution: `algebraic_equivalence_unification`×1, `outside_taxonomy`×1, `unify_into_shared_representation`×1, `generative_process_redesign`×1.
- Journal-house distribution: `survey_or_review_synthesis`×2, `named_stack_plus_case`×1, `power_system_planning_ops`×1.
- Attested multi-pattern combos: `structural_prior_encoding+unify_into_shared_representation`, `generative_process_redesign+reframe_as_solvable_object`.
- Evidence readiness: baseline **75%**, ablation **0%**, dataset/benchmark **75%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-mathematics/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-mathematics_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-mathematics`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=5** mapped local PDFs.
- Section presence rates: intro **80%**, method **60%**, experiments/results **100%**, conclusion **40%**.
- Multimodal density (mean/paper): figures **2.4**, tables **1.4**, algorithms **0.0**, equation markers **5.2**.
- CPA evidence signals: baseline cues **20%**, ablation **0%**, dataset/benchmark **20%**, data-availability **0%**, code-availability **20%**.
- CPA-scoped IdeaSpark dominant move: `algebraic_equivalence_unification` · journal-house: `outside_taxonomy`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.


## Method & evidence bar / house style

- Correct proofs / rigorous analysis (convergence, complexity, error bounds); reproducible numerics. MDPI Word/LaTeX template, MDPI numbered refs (see `../../resources/mdpi-common.md`).

### Distilled patterns — power-grid open-data corpus (2026-07)

Only a thin slice of the corpus belongs here: **OPF/UC formulations with genuine math (convergence, complexity, discrete optimization theory)** — not “we trained a GNN on PGLib” (`../../resources/powergrid-open-data-corpus-distill.md`). Empirical ML-OPF / forecasting → Energies / IEEE Access / Mathematics is a desk-reject risk without theorems or formal analysis.

## APC / review / Special Issues

- APC ≈ CHF 2,600 after acceptance (verify). Single-blind, ≥2 reviewers, ~17.4 d first decision, 1–2 short revision rounds. Section + heavy Special-Issue model — pick an on-scope SI; vet Guest-Editor invitations.

## Official-cycle checklist / pre-submission self-check

- Open `/journal/mathematics`, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`; verify APC, IF/quartile, Section list. Official pages win.
- [ ] There is a **genuine mathematical contribution** (theorem/analysis/method), not just applied use of math. [ ] Proofs/analysis are correct and complete. [ ] Correct Section / on-scope SI. [ ] Notation and rigor meet a math-reviewer bar.

## Common desk-reject triggers

- Applied ML/engineering with **no mathematical novelty** ("we ran a model"); hand-wavy or incomplete proofs; out of Section scope.

## Re-routing decision

- **MDPI Axioms / Symmetry / Algorithms**, **Applied Mathematics and Computation (Elsevier)**; if the contribution is applied-engineering rather than mathematical → **MDPI Applied Sciences / Electronics** or **IEEE Access**.

## Output format

```text
[Target] Mathematics (MDPI)
[Fit] High / Medium / Low (one-line: is there a genuine mathematical contribution?)
[Cost/Speed] ~CHF 2,600 · ~17-day first decision
[Main evidence gap] <proof-completeness / analysis / Section-fit fix>
[Best-fit Section] <Computational/Applied Math, Math & CS, Engineering Math, ...>
[Top rejection risk] no-math-novelty / incomplete-proofs / scope
[Re-route suggestion] <Axioms/Symmetry/Algorithms; Applied Sciences/IEEE Access if applied-eng>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Shared MDPI model: `../../resources/mdpi-common.md`; index: `../../resources/journal-roster.md`; selection guide: `../../resources/journal-selection-guide.md`._
