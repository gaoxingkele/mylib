---
name: pcmp
description: Use when targeting Protection and Control of Modern Power Systems (PCMP) or deciding whether a power-system protection/control/fault/stability manuscript fits it. Diamond OA (no APC), very fast review, high IF — but scope is genuinely protection-and-control-centric. Encodes fit, evidence bar, review speed, submission, desk-reject risks, and re-routing.
---

# Protection and Control of Modern Power Systems (PCMP)

## Journal positioning

PCMP is a **diamond open-access (NO APC — free to publish)** power-systems journal, now published by **IEEE (on IEEE Xplore, migrated from SpringerOpen ~2024)**. Among the power venues in this skill it is the **standout on the user's two priorities: free + fastest review + highest IF/Q1** — but its scope is genuinely **protection, control, fault, and stability** centric, so fit is the gating question, not cost or speed. Treat this as a **fit / framing** tool; the live IEEE Xplore author page wins (fee/template/timeline are in flux after the publisher move).

- Metrics (as-of 2026-07 — **verify on the IEEE Xplore PCMP page, punumber 10352418 / Clarivate JCR**): IF ≈ **11.9** (sources vary; unambiguously high), **Q1** in Electrical & Electronic Eng., Energy Eng. & Power Tech., and Safety/Reliability; CiteScore ≈ 22.8. Indexed SCIE, Scopus, EI. Selective (~66 articles/yr).

## When to trigger

- The author has power-system **protection / relay / fault diagnosis-location / stability / control / resilience** work (including data-driven/ML applied to those) and wants a free, fast, high-IF Q1 home.
- A power paper needs the best speed-and-cost option and has a genuine protection/control angle.

## Scope & fit

- New theories/technologies in **protection and control of modern power systems**: relay protection, fault diagnosis & location, stability & control, DER/renewable integration, grid resilience, and increasingly **data-driven/AI methods applied to protection and control** (ML fault classification, adaptive protection, cyber-physical security).
- **Strong power×CS/AI fit ONLY when the CS/AI serves protection/control/fault/stability.** A pure ML/forecasting or general smart-grid optimization paper with **no protection/control angle is a scope desk-reject risk** — route it to CSEE JPES, Energies, or IEEE Access instead.

## Venue-specific calibration

- **Reviewer lens:** power-protection/control specialists; the contribution must advance protection/control/fault/stability, with rigorous validation (simulation + ideally hardware/field data).
- Distinctive fingerprint: relay protection · fault diagnosis & location · power system control · stability · resilience · adaptive protection · DER integration · cyber-physical security · fast review · diamond OA.
- Official anchor: IEEE Xplore PCMP journal page (punumber 10352418).

## Method & evidence bar

- Sound, reproducible methods with strong validation (PSCAD/EMTP/RTDS simulation, and where possible experimental/field data); clear comparison to existing protection/control schemes.
- For AI-in-protection: justify why the data-driven method beats conventional protection and address reliability/robustness (protection cannot fail).

### Distilled patterns — power-grid open-data corpus (2026-07)

Almost none of the local open-data corpus is PCMP-native (`../../resources/powergrid-open-data-corpus-distill.md`). **Do not force** load forecasting, learning-OPF, or EV charging into PCMP. Only route when the paper’s core is **protection / fault / stability / cascading control** (e.g., PMU-event → protection decision, cascading-failure defense with protection scheme comparison). Otherwise prefer Energies / IEEE Access / OAJPE / CSEE JPES.

## Structure & house style

- Original research + review articles; **use the current IEEE/PCMP template from the Xplore author page** (post-migration format; historically Springer-style). Submission via **ScholarOne**.

## APC, open access & indexing

- **APC: none — diamond/full OA, free to publish** (as-of 2026-07 — **confirm on the IEEE Xplore page given the recent publisher move**). Fully OA; SCIE + Scopus + EI indexed; high-IF Q1.

## Review process & timeline (a key advantage)

- Peer-reviewed (single-blind typical — verify post-migration). **Average review ≈ 4 weeks — the fastest of the power journals in this skill.** Verify the current median-to-first-decision on the official page since the IEEE migration may have changed the workflow.

## Special / topical

- Occasional guest-edited topical issues under IEEE editorial oversight; same review bar. Check the Xplore page for open calls.

## Official-cycle checklist

- Open the IEEE Xplore PCMP journal/author page and confirm: **fee (should be $0)**, template, submission link (ScholarOne), blinding model, current JCR IF/quartile, and scope statement.
- If the live official instructions conflict with this skill, the official instructions win.

## Pre-submission self-check

- [ ] The core contribution is in **protection / control / fault / stability / resilience** (not generic ML/forecasting).
- [ ] Validation is rigorous (simulation + ideally hardware/field), with comparison to existing schemes.
- [ ] Reliability/robustness of any AI-based protection is explicitly addressed.
- [ ] Using the current IEEE/PCMP template; submitted via ScholarOne.
- [ ] Confirmed free-to-publish status and current scope on the live IEEE Xplore page.

## Common desk-reject triggers

- Off-scope: pure ML/forecasting or general smart-grid work with no protection/control angle.
- Weak validation; no comparison to existing protection/control methods.
- Reliability concerns unaddressed for an AI-based protection scheme.

## Re-routing decision

- Higher-selectivity: **IEEE T-Power Delivery, T-Power Systems, T-Smart Grid, T-Sustainable Energy**.
- Broader smart-grid/big-data/AI-in-power without a protection angle: **CSEE JPES, MDPI Energies, IEEE Access, OAJPE, MPCE (J. of Modern Power Systems and Clean Energy)**.

## Output format

```text
[Target] Protection and Control of Modern Power Systems (PCMP)
[Fit] High / Medium / Low (one-line: is there a genuine protection/control/fault/stability angle?)
[Cost/Speed] Free (diamond OA) · ~4-week review (verify)
[Contribution type] protection / fault-diagnosis / stability-control / AI-in-protection / review
[Main evidence gap] <validation / scheme-comparison / robustness fix>
[Official items to re-check] fee($0) / template / ScholarOne / JCR IF-quartile / scope
[Top rejection risk] off-scope (no protection/control angle) / weak validation
[Re-route suggestion] <CSEE JPES / Energies / IEEE Access if no protection angle; a Transactions if highly novel>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official IEEE Xplore page. Index: `../../resources/journal-roster.md`; selection guide: `../../resources/journal-selection-guide.md`._
