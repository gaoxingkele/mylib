---
name: ieee-access
description: Use when targeting IEEE Access or deciding whether an engineering/CS manuscript fits this venue. Encodes the soundness-not-novelty criterion, the binary accept/reject review model, APC/OA facts, scope across all IEEE fields, submission checks, desk-reject risks, and re-routing. IEEE Access is a journal, not a conference.
---

# IEEE Access

## Journal positioning

IEEE Access is IEEE's multidisciplinary **gold open-access "megajournal"** (est. 2013, ISSN 2169-3536, continuous online publication, 100k+ articles). The single most important thing to internalize: **it reviews for technical/scientific SOUNDNESS and quality, NOT for novelty, impact, or significance.** A rigorous, correct, clearly-presented paper that a selective IEEE Transactions would reject as "not novel enough" can be a good fit here — *if the work is methodologically sound.* Treat this skill as a **fit / venue-selection / framing** tool; the live official pages (bibliometrics, APC, guide-for-authors) win over anything here, because APC, IF, quartile, and policies change yearly.

- Metrics (2025 JCR, as-of 2026-07 — **verify on https://ieeeaccess.ieee.org/about/bibliometrics/**): Impact Factor ≈ **4.2**, **Q2**; CiteScore ≈ **9.3**. IF history matters: peaked ~9.0 (2020, Q1) in the pandemic citation surge, fell to ~3.4–3.9 (2022–2024), recovered to ~4.2. Quartile slipped Q1→Q2. Do not quote the old ~9.0 to an author.
- Indexed in SCIE, Scopus, Ei Compendex, DOAJ, Inspec.

## When to trigger

- The author names IEEE Access as the target, or asks "where can I publish this solid-but-not-groundbreaking IEEE-scope paper fast, open access."
- A paper was rejected from a selective IEEE Transactions for "insufficient novelty" but is technically sound.
- Broad, interdisciplinary, or application-heavy engineering/CS work that crosses IEEE fields needs a venue read.
- The author needs a fast, predictable decision with the IEEE brand and can pay the APC.

## Scope & fit

- **All IEEE fields of interest** — strongest volumes in AI/computational intelligence, computers & information processing, communications, signal processing, power & energy.
- Application-oriented and interdisciplinary/boundary-crossing work is explicitly welcome, including work spanning multiple IEEE fields.
- Out of scope: anything with no IEEE field-of-interest tie (pure non-engineering natural science, clinical medicine, humanities/social science). Route elsewhere.

## Venue-specific calibration

- **Reviewer lens:** "Is this correct, complete, reproducible, clearly written, and of interest to readers?" — NOT "is this the first/best." Frame contributions around **rigor and validation**, not novelty claims.
- **"Incremental" is not fatal here; "incremental AND not rigorously validated" is.** Solid engineering, complete experiments, honest limitations win.
- Distinctive fingerprint: binary accept/reject · soundness-not-novelty · IEEE OA megajournal · rapid ~4-week review · single-blind · all-IEEE-fields · continuous publication · no page limit · guest-edited Special Sections · one-resubmission limit.
- Official anchor domain: ieeeaccess.ieee.org. Quote rules only after opening the current bibliometrics/APC/author pages.

## Method & evidence bar

- Correct, reproducible methods; adequate baselines/validation for the claims; clear presentation.
- Report data, settings, and limitations so a reviewer can judge soundness rather than take claims on faith.
- Reproducibility initiative available (share code/data) — use it; it strengthens the soundness case.
- Clarity/English is an explicit acceptance criterion — poor writing is a common reject cause even for sound work.

## Distilled review standards (4 published power/load papers full-text + 10 contingency-class abstracts — as-of 2026-07, small sample, extrapolate with care)

The observed acceptance function ≈ **sound method × self-consistent evidence chain × complete narrative** (gap → contribution → experiment → limitation), not novelty height or statistical perfection (records in `paper_reviews/corpus/distill_fullpaper/ieee_access.md`):

- **Novelty in practice:** all 4 full-text papers are component combinations / scenario adaptations with "first time in literature" framing; numbered contribution lists (3–6 bullets) are a near-rigid convention. "Not distinct from prior publication" remains the official red line, but "not novel enough" is the wrong standard for this venue.
- **Community norms set the statistics bar:** metaheuristics papers ship 50+ independent runs + Wilcoxon/Friedman + convergence/boxplots; **accepted DL papers ship 4–6 baselines with zero significance tests and zero multi-run reporting.** A pure internal-scenario comparison (no external baseline) passed for a framework/evaluation paper. Explicit fairness statements (unified compute budget, parameter-count alignment) appeared in 2/4 and read as a strength.
- **Not required in practice:** open code (0/4), elegant English (2/4 accepted papers have typos/repeated paragraphs/MT-flavored prose — "understandable" sufficed), private-data release.
- **Real slip-throughs reviewers missed in accepted papers** (self-check these): random 90/10 splits on time-series data (leakage), proxy dataset–task mismatch, dense self-citation rings, seemingly revision-stage padded citations, evidence-free generalization claims in conclusions ("extends to medical imaging/finance"), near-zero hyperparameter disclosure.

### Supplement — power-grid open-data corpus (90 unique OA/arXiv PDFs, 2026-07)

Local cache mapped 49 public power datasets → OA targets; **IEEE Access is the #2 most frequent OA target (43/49 dataset rows)** after Energies. Distill notes: `../../resources/powergrid-open-data-corpus-distill.md`.

- **High-fit genres here:** learning-OPF / GNN-OPF (PGLib, OPFData, PGLearn), battery SOH on NASA/CALCE/Oxford, EV charging (ACN-Data), load/price transformers on ETT/OPSD, electricity-theft detectors, PMU-event ML.
- **What strengthens soundness for this corpus:** name the public benchmark + split protocol; 3–6 numbered contributions; ≥3 named baselines for forecasting/theft; IEEE-bus / scenario self-comparison is acceptable for OPF/RL when claims are about feasibility/control not SOTA MAE.
- **Do not oversell novelty:** corpus methods are overwhelmingly combinations (PINN+battery, GNN+OPF, CNN-LSTM+theft). Frame rigor/reproducibility; Access reviewers punish unsupported generalization more than modest Δ%.

## Structure & house style

- Use the dedicated **IEEE Access LaTeX/Word template** (distinct from Transactions templates); template compliance is checked at intake.
- Recommended length **under ~20 pages** for readability, but there is **no hard page limit and no overlength charge**.
- ORCID required/strongly encouraged; graphical abstract and supplementary/multimedia supported (Best Video Award exists).

## APC, open access & indexing

- **APC ≈ US $2,160** per article + local taxes, **as-of 2026-07 — verify at https://ieeeaccess.ieee.org/about/article-processing-charges/** (it has risen $1,750 → $1,995 → $2,160 over time). No page/overlength charges.
- Discounts: IEEE member ~5%, IEEE Society member ~20% total; low-income-country discounts (World Bank tiers); students not eligible for the member discount. Institutional OA agreements may cover it.
- APC due after acceptance / before final publication (not at submission).

## Review process & timeline (the differentiator)

- **BINARY decision model:** reviewers + the Associate Editor recommend only **Accept or Reject** — there is **no major/minor-revision ping-pong**. A reject usually comes with constructive feedback and (often) encouragement to revise and resubmit.
- **One resubmission** is generally allowed after a (conditional) reject, with a mandatory point-by-point response; a second rejection is typically final.
- **Single-blind**; each paper handled by an **Associate Editor** with **≥2 independent reviewers**.
- **Timeline:** advertised **~4 weeks to first decision**, ~4–6 weeks submission-to-publication (verify current SLA). Acceptance rate ~20%.
- **Vs traditional IEEE Transactions:** Transactions judge novelty+significance+soundness over multi-round revisions across months; Access strips this to a single soundness gate in weeks, fully OA. Trade-off: fast, but the binary model gives less room to iteratively rescue a borderline paper — so submit when it is already solid.
- Submit via IEEE **Author Portal / ScholarOne**; CrossCheck/iThenticate integrity screening.

## Special Sections dynamics

- **Special Sections** = themed, guest-edited topical calls (open CFP ~4–6 months), proposed via the editorial board. Same binary/soundness review as regular articles; papers grouped as "Topics" on IEEE Xplore with an intro editorial.
- Differ from MDPI Special Issues: gated by IEEE Access editorial oversight and the soundness bar; fewer and more curated; Xplore-Topic grouped rather than issue-based.

## Official-cycle checklist

- Open https://ieeeaccess.ieee.org/ and the current **bibliometrics**, **APC**, **stages-of-peer-review**, and **author** pages.
- Re-check: current APC + taxes/discounts, current IF/quartile/CiteScore, template version, ORCID/graphical-abstract rules, integrity/duplicate-submission policy, resubmission rules, and any Special Section CFP deadlines.
- If the live official instructions conflict with this skill, the official instructions win.

## Pre-submission self-check

- [ ] The contribution is **technically sound, complete, and reproducible** — not merely novel-sounding.
- [ ] English/clarity is strong enough that a reviewer never struggles to follow the method.
- [ ] Baselines/validation adequately support every claim; limitations stated honestly.
- [ ] It is genuinely within an IEEE field of interest.
- [ ] No self-plagiarism/text recycling; not under concurrent submission elsewhere.
- [ ] You accept a binary decision (no revision loop) and the paper is already in near-final shape.

## Common desk-reject / reject triggers

- Poor English / unclear presentation.
- Insufficient rigor — weak experiments, missing baselines, unsupported claims.
- Out of IEEE scope.
- Self-plagiarism / duplicate or concurrent submission (CrossCheck).
- Framed as incremental **without** demonstrating soundness.

## Re-routing decision

- Genuinely novel/high-impact → a **selective IEEE Transactions** (TPAMI, TIP, TSP, TNNLS, TII, TWC, TVT, TPWRS, TC, TKDE) — slower, novelty-gated, higher prestige.
- Same soundness-not-novelty philosophy elsewhere → **Scientific Reports**, **PLOS ONE**, **IEEE Open Journal** series, **Heliyon**, or MDPI **Electronics / Applied Sciences / Sensors**.
- Early/incremental/demo work → the relevant **IEEE flagship conference** (ICC/GLOBECOM, CVPR/ICCV, ICASSP, PES GM) — see the conference profiles in this skill.

## Output format

```text
[Target] IEEE Access
[Fit] High / Medium / Low (one-line reason grounded in SOUNDNESS, not novelty)
[Contribution type] system / method / empirical / application / survey(meeting criteria) / other
[Soundness gaps] <the experiments/validation/clarity fixes needed before the binary gate>
[Official items to re-check] APC / IF-quartile / template / integrity / resubmission / Special Section CFP
[Top rejection risk] English-clarity / rigor / scope / self-plagiarism
[Re-route suggestion] <selective Transactions if truly novel; conference if early; sibling OA if better scope>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on ieeeaccess.ieee.org before quoting. See `../../resources/journal-roster.md`._
