---
name: mdpi-sensors
description: Use when targeting the MDPI journal Sensors or deciding whether a sensing/measurement/IoT/monitoring manuscript fits it. The sensing/measurement element must be central, not incidental. Read ../../resources/mdpi-common.md for the shared MDPI model.
---

# Sensors (MDPI)

## Journal positioning

Sensors (est. 2001, ISSN 1424-8220, semimonthly, gold OA) is one of MDPI's largest journals — the science/technology of **sensors, sensing systems, and their applications**. The gating fit rule: **the sensing / measurement / transduction element must be central**, not a token wrapper around a generic ML paper. Fast, single-blind, section-routed OA. Read `../../resources/mdpi-common.md` first for the shared MDPI model.

- Metrics (as-of 2026-07 — **verify at https://www.mdpi.com/journal/sensors**): IF ≈ **3.5** (Q2, Instruments & Instrumentation), CiteScore ≈ **8.2** (Q1 Instrumentation); APC ≈ **CHF 2,600**; median ≈ **17.8 days** to first decision. Indexed SCIE, Scopus, EI.

## When to trigger / scope & section fit

- Work whose contribution is a **sensor, sensing system, sensor network, measurement method, or sensor-data processing** — physical/chemical/bio/optical/electronic sensors, wearables, remote sensing, IoT sensing, condition/health monitoring, fault diagnosis via sensors.
- Sections include: Physical/Chemical/Bio/Optical/Electronic Sensors; Sensor Networks; Remote Sensors; Intelligent Sensors; Sensing & Imaging; Wearables; Navigation/Positioning; Fault Diagnosis & Sensors; Internet of Things. **Verify current list at `/journal/sensors/sections`.**
- **Power×CS/IoT fit:** strong for grid/asset condition monitoring, PMU/measurement, edge/IoT sensing, sensor-data ML — if the sensing element is the contribution.

## Venue-specific calibration

- **Reviewer lens:** "Is there a genuine sensing/measurement contribution, soundly validated?" Fingerprint: sensing · measurement · IoT · wearables · signal processing · remote sensing · condition monitoring · sensor networks.

### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=1** mapped local PDFs (mean ~17.0 pages extracted).
- **Dominant IdeaSpark move:** `generative_process_redesign` — *Liberate a Fixed Generative Component*.
- **Dominant journal-house move:** `hardware_or_field_validation` — *Hardware / Field Validation First*.
- IdeaSpark primary distribution: `generative_process_redesign`×1.
- Journal-house distribution: `hardware_or_field_validation`×1.
- Attested multi-pattern combos: `decompose_and_delegate+generative_process_redesign`.
- Evidence readiness: baseline **0%**, ablation **0%**, dataset/benchmark **100%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-sensors/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-sensors_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-sensors`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=8** mapped local PDFs.
- Section presence rates: intro **100%**, method **100%**, experiments/results **100%**, conclusion **100%**.
- Multimodal density (mean/paper): figures **9.0**, tables **4.0**, algorithms **0.0**, equation markers **0.0**.
- CPA evidence signals: baseline cues **0%**, ablation **0%**, dataset/benchmark **0%**, data-availability **0%**, code-availability **100%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `systems_security_or_iot_stack`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.


## Method & evidence bar / house style

- Sound, reproducible; real sensor data/experiments where possible; mandatory Data Availability Statement. MDPI Word/LaTeX template, IMRaD, MDPI numbered refs (see `../../resources/mdpi-common.md`).

## Distilled patterns — power-grid open-data corpus (2026-07)

For power×CS work, Sensors fits when **PMU / IoT metering / condition-monitoring sensing is the contribution** (`../../resources/powergrid-open-data-corpus-distill.md`).

- Strong dataset anchors in the local cache: LBNL PMU event library, GridSTAGE synthetic PMU, smart-meter sensing for NILM/theft **only if** the sensing/measurement pipeline is central.
- Evidence floor: real or high-fidelity sensor traces + detection/estimation metrics + comparison class; state sampling rate, noise, and placement assumptions.
- If the paper is topology RL on Grid2Op or pure OPF learning → **not Sensors** (IEEE Access / Energies / OAJPE).

## APC / review / Special Issues

- APC ≈ CHF 2,600 after acceptance (verify). Single-blind, ≥2 reviewers, ~17.8 d first decision, ~3 d to publication, 1–2 short revision rounds. Section + heavy Special-Issue model — pick an on-scope SI; vet Guest-Editor invitations.

## Official-cycle checklist / pre-submission self-check

- Open `/journal/sensors`, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`; verify APC, IF/quartile, Section list. Official pages win.
- [ ] The **sensing/measurement element is central** (not a generic ML paper). [ ] Sound validation with real sensor data. [ ] Correct Section / on-scope SI. [ ] Data Availability + ethics complete; complete, polished manuscript.

## Common desk-reject triggers

- Pure ML/algorithm with **no real sensing element**; generic IoT/networking with no measurement contribution; wrong Section; off-scope SI.

## Re-routing decision

- **IEEE Sensors Journal** (higher-selectivity), **MDPI Electronics / Remote Sensing**, **Measurement (Elsevier)**, **IEEE Access**.

## Output format

```text
[Target] Sensors (MDPI)
[Fit] High / Medium / Low (one-line: is the sensing/measurement element central?)
[Cost/Speed] ~CHF 2,600 · ~18-day first decision
[Main evidence gap] <real-sensor-data / validation / Section-fit fix>
[Best-fit Section] <one of the Sensors Sections>
[Top rejection risk] no-real-sensing / scope-Section
[Re-route suggestion] <IEEE Sensors J. / Electronics / Measurement / IEEE Access>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Shared MDPI model: `../../resources/mdpi-common.md`; index: `../../resources/journal-roster.md`; selection guide: `../../resources/journal-selection-guide.md`._
