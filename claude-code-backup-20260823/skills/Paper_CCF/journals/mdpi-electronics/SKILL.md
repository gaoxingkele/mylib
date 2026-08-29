---
name: mdpi-electronics
description: Use when targeting the MDPI journal Electronics or deciding whether an EE/CS manuscript fits it. Encodes section-scope fit, the soundness-over-novelty evidence bar, APC/OA facts, MDPI single-blind fast review, Section + Special-Issue dynamics, submission checks, desk-reject risks, and re-routing. Read ../../resources/mdpi-common.md for the shared MDPI model.
---

# Electronics (MDPI)

## Journal positioning

Electronics is MDPI's broad **"science of electronics and its applications"** journal (est. 2012, ISSN 2079-9292, semimonthly, gold OA). It spans electrical/electronic engineering **and** computer science — a large fraction of accepted papers are CS/AI-flavored (deep learning, computer vision, cybersecurity, IoT). Reviewers weight **technical soundness, reproducibility, and completeness** more than groundbreaking novelty, so incremental-but-rigorous applied ML/systems work is often publishable here even when a top-tier CS venue would reject it for novelty. This skill is a **fit / framing** tool; official pages win. Read `../../resources/mdpi-common.md` first for the shared MDPI model.

- Metrics (as-of 2026-07 — **verify at https://www.mdpi.com/journal/electronics**): IF ≈ **2.9**, **Q2** in *Engineering, Electrical & Electronic* (JCR); CiteScore ≈ **6.1** (Q1 by CiteScore in several EE/CS subfields). Indexed SCIE, Scopus, Ei Compendex, DBLP, Inspec. (Ignore the "3.82" figure on aggregators — not the Clarivate IF.)

## When to trigger

- The author names Electronics, or asks where a sound applied EE/CS/AI systems paper can publish fast, open access.
- Applied ML/DL on signals or hardware, embedded/IoT, power/industrial electronics, communications/networks, circuits, semiconductors, or control needs a venue read.
- A CS/AI paper rejected for "insufficient novelty" is technically solid and needs a soundness-based home.

## Scope & section fit

- Covers electrical & electronic engineering, computer science/information systems, applied physics, electronic materials/devices, semiconductors/microelectronics, power & industrial electronics, optoelectronics, control, signal/image processing, communications & networks, embedded/IoT, and **AI/ML applied to electronic systems**.
- **Section-routed** (~16 Sections, each with its own board): Artificial Intelligence; Bioelectronics; Circuit & Signal Processing; Computer Science & Engineering; Electrical & Autonomous Vehicles; Electronic Materials/Devices; Electronic Multimedia; Industrial Electronics; Microelectronics; Microwave & Wireless Communications; Networks; Optoelectronics; Power Electronics; Semiconductor Devices; Systems & Control Engineering; General. **Verify the current list at `/journal/electronics/sections`.**
- **Out of scope:** pure theory/mathematics with no electronics/computing system; clinical/biomedical work better suited to a bioengineering venue.

## Venue-specific calibration

- **Reviewer lens:** "Is this sound, complete, reproducible, and matched to a Section?" — frame around **engineering validation**, not novelty claims alone.
- Distinctive fingerprint: gold OA · high-volume · single-blind · fast (~15-day first decision) · Special-Issue-driven · Section-routed · applied AI/ML + embedded/IoT · power & industrial electronics · semiconductors/microelectronics · communications & networks · SCIE + Scopus.
- Official anchor domain: mdpi.com/journal/electronics.

### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.
- Sample: **n=16** mapped local PDFs (mean ~21.6 pages extracted).
- **Dominant IdeaSpark move:** `heterogeneous_decomposition` — *Decompose for Differentiated Treatment*.
- **Dominant journal-house move:** `power_system_planning_ops` — *Power-System Planning / Operations Case*.
- IdeaSpark primary distribution: `heterogeneous_decomposition`×5, `reframe_as_solvable_object`×4, `unify_into_shared_representation`×2, `decompose_and_delegate`×1, `architectural_operator_substitution`×1, `structural_prior_encoding`×1.
- Journal-house distribution: `power_system_planning_ops`×8, `named_stack_plus_case`×5, `survey_or_review_synthesis`×2, `systems_security_or_iot_stack`×1.
- Attested multi-pattern combos: `generative_process_redesign+reframe_as_solvable_object`, `decompose_and_delegate+generative_process_redesign`, `structural_prior_encoding+unify_into_shared_representation`, `heterogeneous_decomposition+unify_into_shared_representation`, `heterogeneous_decomposition+reframe_as_solvable_object`.
- Evidence readiness: baseline **44%**, ablation **6%**, dataset/benchmark **44%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-electronics/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-electronics_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-electronics`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=15** mapped local PDFs.
- Section presence rates: intro **100%**, method **100%**, experiments/results **80%**, conclusion **20%**.
- Multimodal density (mean/paper): figures **7.4**, tables **3.2**, algorithms **0.0**, equation markers **8.1**.
- CPA evidence signals: baseline cues **33%**, ablation **0%**, dataset/benchmark **33%**, data-availability **20%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `named_stack_plus_case`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## Method & evidence bar

- Sound, reproducible methods with adequate experiments/baselines; complete methodology; honest limitations.
- Mandatory Data Availability Statement; share code/data (FAIR) — strengthens a soundness-based acceptance.
- For applied-ML papers: report datasets, splits, hyperparameters, and comparisons; avoid leaderboard-only framing.

## Distilled review standards (15 published power-systems papers, full-text, 2023–2026 — as-of 2026-07)

What actually clears review (power/energy corpus; per-paper records in `paper_reviews/corpus/distill_fullpaper/electronics.md`):

- **The novelty anchor is on the algorithm/IT side**, not the application domain: 11/15 papers sell an ML-architecture combination or metaheuristic improvement; the power scenario is the carrier. Zero fundamentally new algorithms. The reviewer question is "is each component justified," not "is the problem new." Physics-modeling depth is judged more leniently than in energy journals (non-real price parameters were accepted with a caveat).
- **Experiments floor:** 1 case study + ≥1 comparison class + quantified metrics (forecasting papers: ≥2 of MAE/RMSE/MAPE). Norm: ~3 baselines + component comparisons (rarely called "ablation") . Floor that still passes: self-only comparison (e.g., LSTM vs GRU) or zero baselines.
- **Not required in practice:** significance tests (0/15), baseline-tuning fairness statements (0/14), multi-run mean±std (1/14), open code or public data links (0/15 — providing either exceeds every accepted sample).
- **Hard floor:** Funding / COI / Author Contributions complete; grid-utility funding/affiliation (9/15) is routine when disclosed per-author.
- **Real slip-throughs to self-check** (found in accepted papers): abstract typos reversing a metric's direction, quantified claims without a controlled comparison, Data Availability statements that contradict actual data use, half-disclosed hyperparameters.

### Supplement — power-grid open-data corpus (2026-07)

Corpus routing puts Electronics on **PMU/event detection, DGA/transformer diagnosis, edge metering, and battery SOH with an EE/signal angle** (see `../../resources/powergrid-open-data-corpus-distill.md`).

- Sell the **algorithm/IT + measurement/signal** contribution; keep the power case as the carrier (matches this journal’s existing distill: novelty on the EE/CS side).
- Prefer LBNL-PMU / GridSTAGE / public DGA tables over anonymous SCADA dumps; report detection metrics (F1/AUC) or SOH MAE with ≥1 baseline class.
- If the paper is pure load-forecasting on ETT with no hardware/signal story → **Energies / Energy Reports / IEEE Access** instead.

## Structure & house style

- MDPI Word/LaTeX template; IMRaD; MDPI numbered references; abstract + keywords. (Details in `../../resources/mdpi-common.md`.)

## APC, open access & indexing

- **APC ≈ CHF 2,400**, charged only after acceptance, **as-of 2026-07 — verify at https://www.mdpi.com/journal/electronics/apc**. IOAP/society/reviewer discounts + case-by-case waivers.
- Fully gold OA (CC BY); indexed SCIE + Scopus + EI + DBLP.

## Review process & timeline

- Single-blind, ≥2 reviewers; Section/Guest Editor handling. Median **~15 days** to first decision; ~3 days acceptance→publication; usually 1–2 short revision rounds. Verify at `/journal/electronics/stats`.

## Section + Special Issue dynamics

- Two axes: permanent **Sections** and time-bound **Special Issues** (Guest-Editor-led); a very large share of content publishes via SIs (thousands open). Same review/APC/indexing. Choose the right Section and an on-scope SI; vet unsolicited SI invitations (see `../../resources/mdpi-common.md`).

## Official-cycle checklist

- Open `/journal/electronics`, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`.
- Re-check current APC, IF/quartile, the Section list, data/ethics rules, and open Special Issues. Official pages win.

## Pre-submission self-check

- [ ] There is a clear **electronics/computing system** angle (not pure theory).
- [ ] Methods are sound, reproducible, and validated with adequate baselines/experiments.
- [ ] Correct **Section** selected (and, if used, a genuinely on-scope Special Issue).
- [ ] Data Availability Statement + ethics/COI/funding complete; formatting/English clean.
- [ ] Manuscript is complete and near-final (short revision windows).

## Common desk-reject triggers

- Pure theory/mathematics with no system; out-of-scope biomedical/clinical.
- Too preliminary / lacking evaluation; poor English; incomplete data statement.
- Wrong Section; off-scope Special Issue; excessive self-citation.

## Re-routing decision

- **IEEE Access** (broad EE/CS OA, soundness model), **Sensors / Applied Sciences / Micromachines / Machines / Information / Future Internet / AI (MDPI)**.
- Topic-specific higher-selectivity: **IEEE T-IE, T-PEL, T-CAS, T-CSVT, T-NNLS, T-IFS**; **IET** Electronics Letters / Circuits Devices & Systems / Power Electronics / Communications / Computer Vision.
- If the contribution is novelty-driven and better as a conference paper, see the CS conference profiles in this skill.

## Output format

```text
[Target] Electronics (MDPI)
[Fit] High / Medium / Low (one-line reason: soundness + Section match)
[Contribution type] applied-ML / systems / circuits / power-electronics / communications / control / other
[Main evidence gap] <experiment / baseline / reproducibility / data-statement fix>
[Best-fit Section] <one of the ~16 Sections>
[Official items to re-check] APC / IF-quartile / Section list / Special Issue / data & ethics
[Top rejection risk] scope-Section / evaluation-rigor / English / self-citation
[Re-route suggestion] <IEEE Access, MDPI sibling, IEEE Transactions, or a conference>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Shared MDPI model: `../../resources/mdpi-common.md`; index: `../../resources/journal-roster.md`._
