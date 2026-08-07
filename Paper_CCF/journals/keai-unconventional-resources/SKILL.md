---
name: keai-unconventional-resources
description: Use when targeting Unconventional Resources (KeAi / Elsevier) for unconventional oil/gas/geo-energy resources. Warn power-grid ML authors about scope mismatch; encode low/waived APC window and quarterly schedule.
---

# Unconventional Resources (KeAi / Elsevier)

## Journal positioning

Unconventional Resources is a **peer-reviewed, fully OA** journal owned by **KeAi**, published with Elsevier infrastructure, focused on **unconventional hydrocarbon and related geo-energy resources** (shale, tight oil/gas, CBM, hydrate, enhanced recovery, related geology/engineering). **Not** a general power-systems or CS journal.

- OA policy (as-of 2026-08 — **verify https://www.keaipublishing.com/en/journals/unconventional-resources/**): APC **waived for submissions before 1 Apr 2026**; thereafter APC ≈ **US$700**. Quarterly since 2025. CC BY / CC BY-NC-ND options per KeAi OA statement.

## When to trigger / scope

- Unconventional oil/gas geology, drilling, stimulation, reservoir engineering, related AI **for subsurface resources**.
- Power×CS authors: **usually Low fit** unless the manuscript is genuinely about unconventional resource systems (not grid dispatch).

## Venue-specific calibration

- **Reviewer lens:** geoscience/petroleum engineering soundness.
- Fingerprint: KeAi · low/waived APC window · unconventional hydrocarbons · quarterly.

## Method & evidence bar

- Field/lab/simulation evidence appropriate to petroleum/geo-energy; KeAi/Elsevier author instructions.

### Distilled full-text patterns (local corpus, 2026-08)

_No readable PDFs._

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/keai-unconventional-resources/`.

### Distilled deep structure & style (local corpus, 2026-08)

_No local full-text PDFs yet (0/10)._ ScienceDirect OA `/pdf` endpoints return **403** via aria2c/cloudscraper/proxy and direct; Unpaywall/OpenAlex locations resolve only to Elsevier hosts; no EuropePMC or arXiv title mirrors found for the sampled works. Until mirrors appear, calibrate from official aims/scope + APC pages only — do not invent corpus-level page/figure budgets.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/keai-unconventional-resources/`.


### ResearchStudio-Idea acceptance patterns (local corpus, 2026-08)

_No local PDFs — cannot induce IdeaSpark-style acceptance cards. See `D:/aicoding/lib` ResearchStudio-Idea skill suite for the method; retry after OA mirrors for this venue are available._

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/keai-unconventional-resources/`.


## Desk-reject / re-routing

- Grid ML / CS papers without unconventional-resource scope → **Energies, Energy Reports, Journal of Energy Storage, IEEE Access**.
- Broader energy → Energies; storage → J. Energy Storage.

## Output format

```text
[Target] Unconventional Resources (KeAi)
[Fit] High / Medium / Low (almost always Low for grid-CS)
[Cost] APC waived until 2026-04-01 then ~US$700 (verify)
[Re-route] Energies | Energy Reports | J. Energy Storage | IEEE Access
```

---
_Metrics as-of 2026-08 snapshot; official pages always win._
