---
name: mdpi-energies
description: Use when targeting the MDPI journal Energies or deciding whether an energy/power manuscript fits it. Encodes energy-scope fit, the applied-evidence bar, APC/OA facts, MDPI's single-blind fast review, Special-Issue dynamics, submission checks, desk-reject risks, and re-routing. Read ../../resources/mdpi-common.md for the shared MDPI model.
---

# Energies (MDPI)

## Journal positioning

Energies is MDPI's **flagship, broad energy** journal (est. 2008, ISSN 1996-1073, semimonthly, gold OA, ~6,500 articles/year). It rewards **applied energy engineering with a clear system/application** — generation, conversion, storage, grids/power systems, efficiency, fuels, techno-economic and energy-policy analysis with quantitative results. It is a fast, high-volume open-access venue: judge fit on **methodological soundness + clear energy relevance**, not on novelty alone. This skill is a **fit / framing** tool; the live official pages win. First read `../../resources/mdpi-common.md` for the shared MDPI model (SuSy, single-blind, Sections + Special Issues, APC-after-acceptance, reputation nuance).

- Metrics (as-of 2026-07 — **verify at https://www.mdpi.com/journal/energies**): IF ≈ **4.0** (2024 JCR), category **Energy & Fuels**, roughly **Q2** (JCR) / Q1–Q2 (Scimago by subcategory); CiteScore ≈ **7.3**. Indexed SCIE, Scopus, Ei Compendex, Inspec.

## When to trigger

- The author names Energies, or asks whether a power/energy paper fits a fast OA journal.
- Broad or cross-cutting energy work (systems, storage, grids, renewables, efficiency, policy) needs a venue read.
- A hydrogen/battery/wind/solar-specific paper needs routing between Energies and a narrower MDPI sibling.

## Scope & section fit

- Covers the **full energy field**: supply, conversion, dispatch/distribution, storage, efficiency, and end use — engineering, modeling/simulation, techno-economic and policy analysis. Section-routed (electrical power & energy systems, renewables, storage, conversion, efficiency, hydrogen, smart grids, fuels/combustion, thermal, energy economics & policy, CCUS).
- **Weak/out of scope:** work with no clear energy application; pure materials chemistry, pure economics, or environmental studies lacking an energy-system tie — reroute to a sibling.
- **Vs siblings:** use Energies for broad/cross-cutting energy work; route hydrogen/battery/wind/solar-specific papers to Hydrogen / Batteries / Wind / Solar (MDPI). Sustainability and Applied Sciences overlap for applied/policy-flavored work.

## Venue-specific calibration

- **Reviewer lens:** applied energy specialists checking soundness, reproducibility, adequate literature grounding, and a concrete energy application/quantitative result — not groundbreaking novelty.
- Distinctive fingerprint: energy systems · renewable energy · power systems / smart grid · storage & batteries · conversion & efficiency · hydrogen & fuel cells · techno-economic analysis · energy modeling/simulation · fuels & combustion · energy policy · gold OA / fast · Special-Issue-driven.
- Official anchor domain: mdpi.com/journal/energies.

### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=36** mapped local PDFs (mean ~24.9 pages extracted).
- **Dominant IdeaSpark move:** `generative_process_redesign` — *Liberate a Fixed Generative Component*.
- **Dominant journal-house move:** `power_system_planning_ops` — *Power-System Planning / Operations Case*.
- IdeaSpark primary distribution: `generative_process_redesign`×9, `reframe_as_solvable_object`×7, `heterogeneous_decomposition`×6, `structural_prior_encoding`×5, `adapt_via_conditioning`×2, `relax_discrete_search_to_continuous`×2.
- Journal-house distribution: `power_system_planning_ops`×17, `named_stack_plus_case`×11, `survey_or_review_synthesis`×4, `storage_or_energy_device_review`×3, `hardware_or_field_validation`×1.
- Attested multi-pattern combos: `generative_process_redesign+reframe_as_solvable_object`, `generative_process_redesign+heterogeneous_decomposition`, `heterogeneous_decomposition+reframe_as_solvable_object`, `assumption_audit_and_pivot+reframe_as_solvable_object`, `reframe_as_solvable_object+relax_discrete_search_to_continuous`.
- Evidence readiness: baseline **50%**, ablation **31%**, dataset/benchmark **50%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-energies/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-energies_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-energies`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=36** mapped local PDFs.
- Section presence rates: intro **100%**, method **92%**, experiments/results **69%**, conclusion **6%**.
- Multimodal density (mean/paper): figures **5.4**, tables **2.9**, algorithms **0.1**, equation markers **10.5**.
- CPA evidence signals: baseline cues **36%**, ablation **0%**, dataset/benchmark **33%**, data-availability **8%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Method & evidence bar

- Sound, reproducible methodology with **validation** (experimental, numerical, or against real data) — not an unvalidated simulation.
- Mandatory Data Availability Statement; share data/code where possible.
- Adequate, current literature review; avoid excessive self-citation / citation stuffing (an integrity flag).

## Distilled review standards (34 published power-systems papers, full-text, 2023–2026 — as-of 2026-07)

What actually clears review in this journal (power/energy planning-dispatch-forecasting corpus; per-paper records in `paper_reviews/corpus/distill_fullpaper/`):

- **Novelty floor:** a nameable mechanism-combination / framework integration / modest algorithm improvement tied to a gap statement. **Zero of 31 research papers introduced a fundamentally new algorithm**; ≤5% improvement passes if honestly reported. Reviewers check "is this combination genuinely undone" rather than "is this groundbreaking."
- **Experiments floor:** ≥1 identifiable test case + scenario/scheme self-comparison + **sensitivity analysis (near-mandatory; its absence is the top major-revision trigger)**. Single test system is the norm (~2/3); external algorithm baselines appear in only ~half of accepted papers (planning papers pass on scenario self-comparison alone). Forecasting papers face a higher bar: ≥3 baselines + component comparisons + multiple metrics.
- **Not required in practice:** statistical significance tests (0/29 accepted papers), 30-run protocols, open code (1/34), public data (confidential utility data is routinely accepted with a template Data Availability statement).
- **Hard floor:** Funding / COI / Data Availability / Author Contributions all present (100%); utility-company funding+authorship+data "three-in-one" is normal when disclosed.
- **What published papers still get away with** (worth pre-submission self-checking): irrelevant padded citations, corresponding-author self-citations at the top of the reference list, title–case-study mismatch, contradictory funding statements, hybrid algorithms with no per-component justification, inflated percentages on self-defined metrics.

### Supplement — power-grid open-data corpus (90 unique OA/arXiv PDFs, 2026-07)

Across the curated dataset→OA map, **Energies is the #1 catch-all target (46/49 dataset rows)**. Distill notes: `../../resources/powergrid-open-data-corpus-distill.md`.

- **Highest-density topics in the local cache:** battery/BESS (SOH, markets, aFRR), wind/solar CF & WPF, load forecasting (ETT/UCI/Ausgrid/Elia), DER/SimBench-style distribution studies, production-cost / RTS-GMLC companions.
- **Evidence that travels well to Energies:** clear energy-system application sentence in abstract; validation on named public data or IEEE/SimBench cases; sensitivity or scenario analysis (still the common major-revision ask); Data Availability pointing to DOI/GitHub.
- **Genre split:** forecasting papers need named baselines + MAE/RMSE/MAPE; planning/BESS-market papers can pass on techno-economic / scenario self-comparison without a DL leaderboard.
- **Weak fit:** pure CS time-series method papers that only mention “energy” once — route to IEEE Access or keep the energy contribution primary.

## Structure & house style

- MDPI Word/LaTeX template; IMRaD; MDPI numbered reference style; abstract ~200 words, 3–8 keywords. (Details in `../../resources/mdpi-common.md`.)

## APC, open access & indexing

- **APC ≈ CHF 2,600**, charged only after acceptance, **as-of 2026-07 — verify at https://www.mdpi.com/journal/energies/apc**. IOAP/society/reviewer discounts and case-by-case waivers apply.
- Fully gold OA (CC BY); indexed SCIE + Scopus + EI (see positioning for metrics + verify).

## Review process & timeline

- Single-blind, ≥2 reviewers, MDPI workflow (pre-check → Academic/Section/Guest Editor → review → revision → production).
- Median **~16–17 days** to first decision; ~3–4 days acceptance→publication; usually 1–2 short revision rounds. Verify at `/journal/energies/stats`.

## Special Issues dynamics

- A large share of Energies content publishes via **Guest-Editor Special Issues** (hundreds open concurrently). Same review standard, same APC, same indexing. Pick an SI whose scope and Guest Editors genuinely fit; vet unsolicited SI invitations (see `../../resources/mdpi-common.md`).

## Official-cycle checklist

- Open `/journal/energies`, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`.
- Re-check current APC, IF/quartile, Section list, data-availability and ethics rules, and whether a matching Special Issue is open. Official pages win.

## Pre-submission self-check

- [ ] Clear **energy application/relevance** stated up front (not a generic method paper).
- [ ] Methodology is sound and **validated**; claims match the evidence.
- [ ] Correct Section (and, if used, a genuinely on-scope Special Issue) selected.
- [ ] Data Availability Statement + ethics/COI/funding complete; references current, self-citation modest.
- [ ] English and MDPI formatting clean; manuscript is complete (short revision windows).

## Common desk-reject triggers

- No clear energy relevance / out of scope (pure chemistry, economics, or CS without an energy tie).
- Incremental, unvalidated simulation; poor English/formatting; missing data statement.
- Inadequate literature review; excessive self-citation; suspected paper-mill / undisclosed-AI content.

## Re-routing decision

- Higher-selectivity energy (Elsevier): **Applied Energy, Energy, Renewable Energy, RSER, Energy Conversion & Management, Journal of Energy Storage, Journal of Power Sources, Int. J. Hydrogen Energy**.
- IEEE power/electrical: **T-Power Systems, T-Power Electronics, T-Sustainable Energy, T-Smart Grid, T-Energy Conversion** (novelty-gated).
- MDPI siblings by specificity: **Sustainability, Applied Sciences, Batteries, Hydrogen, Fuels, Electricity, Solar, Wind, Processes**.
- Broad OA alternatives: **Energy Reports, Energy Science & Engineering, IEEE Access**.

## Output format

```text
[Target] Energies (MDPI)
[Fit] High / Medium / Low (one-line reason: energy relevance + soundness)
[Contribution type] system / modeling / experimental / techno-economic / policy / review
[Main evidence gap] <validation / data / baseline / literature fix needed>
[Official items to re-check] APC / IF-quartile / Section / Special Issue / data & ethics statements
[Top rejection risk] scope / validation / English / self-citation
[Re-route suggestion] <selective energy journal, IEEE Transactions, or MDPI sibling>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Shared MDPI model: `../../resources/mdpi-common.md`; index: `../../resources/journal-roster.md`._
