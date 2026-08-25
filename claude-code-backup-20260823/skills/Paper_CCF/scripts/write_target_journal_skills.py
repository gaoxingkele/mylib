# -*- coding: utf-8 -*-
"""One-shot writer for 2026-08 target-journal skill batch."""
from pathlib import Path

J = Path(__file__).resolve().parents[1] / "journals"


def w(slug: str, content: str) -> None:
    p = J / slug / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")
    print("wrote", slug, "chars", len(content))


FOOT = "\n---\n_Metrics as-of 2026-08 snapshot; official pages always win._\n"

MDPI_COMMON = "Read `../../resources/mdpi-common.md` for the shared MDPI model."


def mdpi_skill(
    slug,
    name,
    description,
    issn,
    positioning,
    metrics,
    trigger,
    calibration,
    evidence,
    distill,
    apc_review,
    desk,
    output,
):
    body = f"""---
name: {slug}
description: {description}
---

# {name}

## Journal positioning

{positioning}

{MDPI_COMMON}

- Metrics (as-of 2026-08 — **verify on the journal homepage**): {metrics}

## When to trigger / scope

{trigger}

## Venue-specific calibration

{calibration}

## Method & evidence bar / house style

{evidence}

MDPI Word/LaTeX template, IMRaD, numbered refs (see `../../resources/mdpi-common.md`).

### Distilled patterns

{distill}

## APC / review / Special Issues

{apc_review}

## Official-cycle checklist / pre-submission self-check

- Open the journal homepage, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`. Official pages win.
- [ ] Scope sentence is honest. [ ] Evidence matches claims. [ ] Data Availability + ethics/COI complete. [ ] Correct Section/SI.

## Common desk-reject triggers / re-routing

{desk}

## Output format

```text
{output}
```
{FOOT}"""
    w(slug, body)


mdpi_skill(
    "mdpi-information",
    "Information (MDPI)",
    "Use when targeting MDPI Information or routing information-systems / knowledge / data / applied AI manuscripts to a fast OA CS venue. Encodes scope, soundness bar, APC, indexing, SI dynamics. Read ../../resources/mdpi-common.md first.",
    "2078-2489",
    "Information (est. 2010, ISSN 2078-2489, monthly, gold OA) is MDPI’s broad **information science & technology** journal — data, knowledge, communication, and applied computing. Fit on **methodological soundness + clear information/CS contribution**, not breakthrough novelty. Affiliated with IS4SI (member APC discounts).",
    "IF ≈ **4.3** (2025 JCR); JCR **Q2** Computer Science, Information Systems; CiteScore Q1 Information Systems. APC ≈ **CHF 1,800**. Median first decision ≈ **18.7 days**; acceptance→publication ≈ **3.8 days**. Indexed Scopus, ESCI/WoS, Ei Compendex, dblp. Homepage: https://www.mdpi.com/journal/information",
    """- Applied **information systems, knowledge graphs, IR, data mining, applied ML/AI** with an information/data/knowledge framing.
- Power×CS: forecasting / KG / RAG for utility docs — **foreground the information/computing contribution** (else Energies/Electronics).
- Weak fit: pure power planning with no IS/CS core.""",
    '**Reviewer lens:** Is the information/computing method sound and validated? Fingerprint: information systems · knowledge · data · applied AI · fast OA · Special Issues. Official anchor: mdpi.com/journal/information.',
    "Named datasets/baselines for algorithmic claims; mandatory Data Availability Statement.",
    "No dedicated 10-paper full-text cache yet (`../../resources/target-journals-2026-batch-distill.md`). Calibrate like sibling MDPI CS titles: incremental method combo + ≥2–3 baselines + clear IS angle.",
    "APC ≈ CHF 1,800 after acceptance. Single-blind, ≥2 reviewers, ~19 d first decision. Heavy SI volume — vet Guest Editors.",
    """- Desk: no information/CS contribution; thin unvalidated demo; poor English/format.
- Re-route: Algorithms / Mathematics (theory); Energies (energy-primary); IEEE Access / Scientific Reports (megajournal); Electronics.""",
    """[Target] Information (MDPI)
[Fit] High / Medium / Low (information/CS contribution primary?)
[Cost/Speed] ~CHF 1,800 · ~19d · IF~4.3 Q2 (verify)
[Main evidence gap] <baselines / data statement / IS framing>
[Re-route] Algorithms | Electronics | Energies | IEEE Access""",
)

mdpi_skill(
    "mdpi-symmetry",
    "Symmetry (MDPI)",
    "Use when targeting MDPI Symmetry or deciding whether a manuscript’s contribution is genuinely about symmetry/asymmetry. Not a generic CS dump venue. Read ../../resources/mdpi-common.md.",
    "2073-8994",
    "Symmetry (ISSN 2073-8994, monthly, gold OA) covers **symmetry/asymmetry phenomena** across natural sciences and related mathematics/engineering. Gating rule: a **real symmetry/asymmetry, invariance, or structure-preserving** contribution — not keyword stuffing.",
    "IF ≈ **2.2**; JCR **Q2 Multidisciplinary Sciences**; CiteScore Q1 General Mathematics. APC ≈ **CHF 2,400**. First decision ≈ **16.3 days**. Indexed SCIE, Scopus, Inspec. Homepage: https://www.mdpi.com/journal/symmetry",
    """- Group/symmetry methods in ML, graph/network symmetry, symmetry-aware optimization, physical/chemical symmetry.
- Power×CS: only if **mathematical symmetry** (equivariant GNN, symmetric OPF) is the claimed contribution — else Energies/Mathematics/Algorithms.
- Weak fit: generic DL forecasting.""",
    '**Reviewer lens:** "Where is the symmetry and why does it matter?" Fingerprint: symmetry/asymmetry · invariance · equivariance · multidisciplinary.',
    "Explicit symmetry definition + proof or constructive argument; ablations that stress the symmetry property.",
    "Full-text power corpus not cached. Do **not** route generic smart-grid papers here. See `../../resources/target-journals-2026-batch-distill.md`.",
    "APC ≈ CHF 2,400; ~16 d first decision; SI common.",
    """- Desk: no genuine symmetry content.
- Re-route: Mathematics | Algorithms | Energies | Electronics | IEEE Access.""",
    """[Target] Symmetry (MDPI)
[Fit] High / Medium / Low (symmetry/asymmetry core?)
[Cost/Speed] ~CHF 2,400 · ~16d · IF~2.2
[Re-route] Mathematics | Algorithms | Energies | IEEE Access""",
)

mdpi_skill(
    "mdpi-remote-sensing",
    "Remote Sensing (MDPI)",
    "Use when targeting MDPI Remote Sensing for EO/GIS/satellite/UAV sensing manuscripts, including renewable resource assessment from remote data. Sensing/EO must be central. Read ../../resources/mdpi-common.md.",
    "2072-4292",
    "Remote Sensing (ISSN 2072-4292, semimonthly, gold OA) is a **high-volume Q1 geoscience/EO** journal. Affiliated societies (RSSJ, JSPRS) get APC discounts.",
    "IF ≈ **4.1**; **Q1** Geosciences, Multidisciplinary. APC ≈ **CHF 2,700**. First decision ≈ **24.3 days**. Indexed SCIE, Scopus, Ei, GeoRef, dblp. Homepage: https://www.mdpi.com/journal/remotesensing",
    """- Satellite/aerial/UAV sensing, retrieval algorithms, irradiance/solar resource from EO, corridor monitoring.
- Power×CS: **GHI/DNI, PV potential mapping** — EO method primary; pure meter-data forecasting → Energies.
- Weak fit: non-spatial grid ML.""",
    '**Reviewer lens:** sensor/product clarity + validation against ground truth. Fingerprint: EO · retrieval · GIS · validation.',
    "Name sensor/product (Sentinel, Landsat, Himawari, …), dates, processing chain, RMSE/MAE/bias vs priors.",
    "Align with NSRDB/ERA5-style open exemplars in `../../resources/powergrid-open-data-corpus-distill.md`.",
    "APC ≈ CHF 2,700; ~24 d first decision; large SI ecosystem.",
    """- Desk: no remote-sensing data/method.
- Re-route: Atmosphere | Energies | Sensors | IEEE TGRS.""",
    """[Target] Remote Sensing (MDPI)
[Fit] High / Medium / Low (EO/sensing central?)
[Cost/Speed] ~CHF 2,700 · ~24d · IF~4.1 Q1
[Re-route] Atmosphere | Energies | Sensors | IEEE TGRS""",
)

mdpi_skill(
    "mdpi-algorithms",
    "Algorithms (MDPI)",
    "Use when targeting MDPI Algorithms for algorithm design, analysis, or empirical algorithmics. Algorithm contribution must be central. Read ../../resources/mdpi-common.md.",
    "1999-4893",
    "Algorithms (ISSN 1999-4893, monthly, gold OA) focuses on **algorithm design, analysis, and applications**. The **algorithm itself** must be the primary contribution.",
    "IF ≈ **2.6**; JCR **Q2** CS Theory & Methods; CiteScore Q1 Computational Mathematics. APC ≈ **CHF 1,800**. First decision ≈ **17.6 days**. Indexed Scopus, ESCI/WoS, Ei. Homepage: https://www.mdpi.com/journal/algorithms",
    """- New/improved algorithms, hybridization with analysis, benchmarking, metaheuristics with algorithmic claims.
- Power×CS: OPF/UC/forecasting **framed as algorithmic contribution**; energy-application-primary → Energies.
- Weak fit: off-the-shelf sklearn case study.""",
    '**Reviewer lens:** Is there a clear algorithmic delta with baselines/ablation? Fingerprint: algorithms · complexity · empirical algorithmics.',
    "Pseudocode; complexity or ablation; ≥3 named baselines for empirical claims; sensitivity for metaheuristics.",
    "Mirror Energies/Access metaheuristic norms: baselines + sensitivity expected. See `../../resources/target-journals-2026-batch-distill.md`.",
    "APC ≈ CHF 1,800; ~18 d first decision; SI common.",
    """- Desk: application-only; weak baselines.
- Re-route: Mathematics | Information | Energies | Electronics | IEEE Access.""",
    """[Target] Algorithms (MDPI)
[Fit] High / Medium / Low (algorithm = contribution?)
[Cost/Speed] ~CHF 1,800 · ~18d · IF~2.6
[Re-route] Mathematics | Information | Energies | IEEE Access""",
)

mdpi_skill(
    "mdpi-future-internet",
    "Future Internet (MDPI)",
    "Use when targeting MDPI Future Internet for internet technologies, networking, IoT protocols, edge/cloud. Network/Internet framing must be central. Read ../../resources/mdpi-common.md.",
    "1999-5903",
    "Future Internet (ISSN 1999-5903, monthly, gold OA) covers **Internet technologies and the information society** — protocols, architectures, IoT networking, edge/cloud, networked security.",
    "IF ≈ **4.6**; JCR **Q2** CS Information Systems; CiteScore Q1 Computer Networks. APC ≈ **CHF 1,800**. First decision ≈ **15 days**. Indexed Scopus, ESCI/WoS, Ei, dblp. Homepage: https://www.mdpi.com/journal/futureinternet",
    """- Next-gen Internet, SDN/NFV, IoT networking, edge AI delivery, smart services.
- Power×CS: **AMI/DER communication, edge inference** — Internet/IoT stack primary; selective systems → IEEE IoT Journal; pure power flow → Energies.
- Weak fit: offline ML on CSV with no network architecture.""",
    '**Reviewer lens:** architecture + protocol/latency/security evaluation. Fingerprint: Internet · IoT networking · edge/cloud.',
    "Architecture diagram; protocol/latency/throughput or security metrics; testbed or trace-driven evaluation.",
    "Prefer IEEE IoT-J when selectivity/IEEE brand matter; Future Internet for faster cheaper OA. See `../../resources/target-journals-2026-batch-distill.md`.",
    "APC ≈ CHF 1,800; ~15 d first decision.",
    """- Desk: no Internet/network contribution.
- Re-route: IEEE IoT Journal | Sensors | Information | Energies | IEEE Access.""",
    """[Target] Future Internet (MDPI)
[Fit] High / Medium / Low (Internet/IoT/network central?)
[Cost/Speed] ~CHF 1,800 · ~15d · IF~4.6
[Re-route] IEEE IoT-J | Sensors | Information | Energies""",
)

mdpi_skill(
    "mdpi-atmosphere",
    "Atmosphere (MDPI)",
    "Use when targeting MDPI Atmosphere for atmospheric science, air quality, meteorology, and climate–energy coupling where the atmosphere is the object of study. Read ../../resources/mdpi-common.md.",
    "2073-4433",
    "Atmosphere (ISSN 2073-4433, monthly, gold OA) covers **atmospheric science** — meteorology, air quality, aerosols, atmospheric chemistry/physics, climate applications.",
    "IF ≈ **2.6**; CiteScore ~Q2 Environmental Science (misc.). APC ≈ **CHF 2,400**. First decision ≈ **19.7 days**. Indexed SCIE, Scopus, Ei, GEOBASE. Homepage: https://www.mdpi.com/journal/atmosphere",
    """- Weather/climate modeling, air pollution, atmospheric retrievals, extreme weather.
- Power×CS: wind/solar meteorological drivers only if **atmosphere is primary**; EO-primary → Remote Sensing; grid-primary → Energies.
- Weak fit: load forecasting with weather as one feature among many.""",
    '**Reviewer lens:** atmospheric datasets + physical consistency. Fingerprint: meteorology · air quality · climate applications.',
    "ERA5/station networks; standard atmospheric metrics; leakage-safe temporal splits for ML.",
    "Use NSRDB/ERA5-style notes in `../../resources/powergrid-open-data-corpus-distill.md` when energy coupling is present.",
    "APC ≈ CHF 2,400; ~20 d first decision.",
    """- Desk: no atmospheric science content.
- Re-route: Remote Sensing | Energies | Sensors.""",
    """[Target] Atmosphere (MDPI)
[Fit] High / Medium / Low (atmosphere primary?)
[Cost/Speed] ~CHF 2,400 · ~20d · IF~2.6
[Re-route] Remote Sensing | Energies | Sensors""",
)

# Non-MDPI journals
w(
    "tsp-cmc",
    """---
name: tsp-cmc
description: Use when targeting Computers, Materials & Continua (CMC, Tech Science Press) or deciding whether an applied CS/AI/materials-informatics manuscript fits this gold-OA journal. Encodes scope, IF/APC, house style, AI-disclosure expectations, and distill patterns from a local 10-paper power/algorithm corpus.
---

# Computers, Materials & Continua (CMC) — Tech Science Press

## Journal positioning

CMC (ISSN 1546-2218 print / 1546-2226 online, monthly, **gold OA**, CC BY) is TSP’s broad journal spanning **computer networks, AI, big data, SE, multimedia, cybersecurity, IoT, materials genome / multifunctional materials modeling**. It is a **mid-tier SCIE** venue: sound, complete applied papers with named method stacks routinely clear; groundbreaking novelty is not required. This skill is a **fit / framing** tool; official pages win.

- Metrics (as-of 2026-08 — **verify at https://www.techscience.com/journal/cmc**): SCI IF ≈ **2.4** (2025); Scopus CiteScore ≈ **6.6**; SNIP ≈ 0.777. Indexed SCIE, Scopus, Ei Compendex, Inspec, etc. APC ≈ **US$1,600** (TSP APC table — verify https://www.techscience.com/ndetail/apc).

## When to trigger / scope

- Applied **AI/ML, NLP, security, IoT, smart-grid informatics, materials/ continuum modeling with computation**.
- Power×CS: load forecasting, grid fault prediction, smart-grid anomaly/graph learning — strong local fit (see distill).
- Weak fit: pure power-system planning without CS/AI method; ultra-selective theory.

## Venue-specific calibration

- **Reviewer lens:** completeness of method + experiments + readable TSP template more than flagship novelty.
- Distinctive fingerprint: Tech Science Press · DOI `10.32604/cmc.*` · CC BY · Received/Accepted/Published dates on page 1 · AI drafting disclosure expected when LLMs used (TSP policy) · **do not invent gold labels with AI**.
- Official anchor: techscience.com/journal/cmc.

## Method & evidence bar

- Named architecture/algorithm stack; comparison tables; figures for architecture/ablation/attention; Data Availability / ethics / funding / COI.
- English must be workable; template compliance checked.

### Distilled review standards (10 local full-text PDFs, 2024–2026)

Corpus: `powergrid_benchmark/papers/literature/target_journal_related/cmc_pdfs/` (notes in `../../resources/target-journals-2026-batch-distill.md`).

- **Genres that clear:** (1) power load forecasting (clustering + BiGRU/attention stacks); (2) smart-grid anomaly via multi-expert graph learning; (3) meteorology→grid fault XGBoost with feature enhancement; (4) LLM/RAG/NER/security applied CS.
- **Novelty floor:** incremental **named combinations** (FE-XGBoost, Stacking-BiGRU-CBAM, RAG+LLM) with gap statement — not new theory.
- **Evidence floor:** datasets (public or constructed) + baselines + metrics (MAE/RMSE/F1/accuracy) + ablation or attention/feature analysis. Length typically **14–25 pages** (up to ~32 for agent systems).
- **House style signals:** TSP article header, author emails, Received/Accepted/Published line, CC BY footer.
- **Integrity:** if LLM used for writing, disclose per TSP; never present AI-simulated labels as human gold.

## Review process & timeline

- Peer-reviewed OA continuous publication. Expect **weeks-to-a-few-months** full cycle (verify current stats with editor/office). Single-blind typical of TSP engineering titles (confirm on instructions).
- APC charged after acceptance (~US$1,600).

## Official-cycle checklist / pre-submission self-check

- Open techscience.com/journal/cmc + APC + author instructions; download current TSP template.
- [ ] Scope is CS/AI/materials-informatics (not pure power engineering). [ ] Method stack named and validated. [ ] AI-use / drafting disclosure if applicable. [ ] Figures readable in TSP two-column/production style.

## Common desk-reject / re-routing

- Out of scope; incomplete experiments; poor English/template; integrity flags.
- Re-route: faster IEEE brand → **IEEE Access**; energy-primary → **Energies / Energy Reports**; selective IoT → **IEEE IoT Journal**; Nature-brand soundness → **Scientific Reports**; cheaper CS OA → **Discover Computing / PeerJ CS / Information**.

## Output format

```text
[Target] CMC (Tech Science Press)
[Fit] High / Medium / Low (applied CS/AI completeness)
[Cost/Speed] ~US$1,600 APC · mid-tier SCIE IF~2.4 (verify)
[Main evidence gap] <baselines / ablation / disclosure>
[Top rejection risk] scope / thin stack / integrity
[Re-route] IEEE Access | Energies | Scientific Reports | Discover Computing
```
"""
    + FOOT,
)

w(
    "springer-discover-computing",
    """---
name: springer-discover-computing
description: Use when targeting Discover Computing (Springer Nature Discover series; formerly Information Retrieval Journal) for broad computer-science open-access work under a soundness-oriented Discover model. Encodes APC discount window, SCIE indexing, scope, and re-routing.
---

# Discover Computing (Springer Nature)

## Journal positioning

Discover Computing (eISSN **2948-2992**) is a **fully gold OA** journal in Springer Nature’s **Discover** series. It continues / rebrands **Information Retrieval Journal** (moved OA 2024) and considers articles across **broad computer science** (theories, AI/ML, cybersecurity, IR/information systems, and more). Discover journals emphasize **rigorous, representative, wide-reaching** work — closer to **soundness + completeness** than flagship novelty. Fit/framing tool; official pages win.

- Metrics (as-of 2026-08 — **verify https://link.springer.com/journal/10791**): Indexed **SCIE, Scopus, DOAJ, DBLP**; IF ≈ **1.9** (2026 JCR release under Discover Computing; Q3 CS Information Systems — verify). CiteScore 2024 ≈ **3.2** (legacy lineage). Formerly IR Journal IF ~1.7.

## When to trigger / scope

- Broad CS / IR / applied AI needing **Springer Nature OA** with Discover series branding.
- Power×CS: evidence retrieval, forecasting algorithms, cybersecurity for energy IT — frame as **CS contribution**.
- Weak fit: pure energy-systems engineering without CS core.

## Venue-specific calibration

- **Reviewer lens:** methodological validity and clarity across a broad CS audience.
- Fingerprint: Discover series · gold OA · broad CS · SCIE · IR heritage · APC discount window.
- Official anchor: link.springer.com/journal/10791.

## Method & evidence bar / house style

- Sound methods, adequate related work, reproducible experiments for empirical claims; SN TeX/Word guidelines; data availability encouraged.
- Article types follow Discover Computing / SN instructions (research articles; check current list).

### Distilled patterns

No local 10-paper full-text cache yet. Treat like a **soundness OA CS** venue below PeerJ-CS prestige narratives but with SN indexing. See `../../resources/target-journals-2026-batch-distill.md`.

## APC, OA & timeline

- **Discounted APC through 31 Dec 2026** (publisher announcement): ≈ **€1,140 / $1,520 / £1,040**; thereafter standard ≈ **€1,890 / $2,190 / £1,590** — **verify on journal OA funding page**. Institutional OA agreements may cover.
- Review timelines vary (Discover series aims for efficient review; not MDPI-15-day). Check current stats on the journal site.

## Desk-reject / re-routing

- Out-of-scope non-CS; incomplete methods.
- Re-route: PeerJ Computer Science; MDPI Information/Algorithms; IEEE Access; Scientific Reports; selective ACM/IEEE conferences for novelty-driven CS.

## Output format

```text
[Target] Discover Computing (Springer Nature)
[Fit] High / Medium / Low (broad CS soundness)
[Cost/Speed] discounted APC until 2026-12-31 (verify) · SCIE IF~1.9
[Re-route] PeerJ CS | Information | IEEE Access | Sci Rep
```
"""
    + FOOT,
)

w(
    "peerj-computer-science",
    """---
name: peerj-computer-science
description: Use when targeting PeerJ Computer Science for open-access CS manuscripts under a soundness/developmental review model, including APC vs lifetime membership options and USENIX partnership context.
---

# PeerJ Computer Science

## Journal positioning

PeerJ Computer Science is a **gold OA** journal covering **42 CS subject areas**, emphasizing **high-quality, developmental peer review**, transparent optional open reviews, and strong author service. Soundness and clarity matter more than Nature/NeurIPS-level novelty. Homepage: https://peerj.com/computer-science/.

- Metrics (as-of 2026-08 — **verify on PeerJ**): Indexed Scopus / WoS (confirm current JIF on Clarivate). Community reputation: legitimate OA CS venue; prestige moderate vs selective IEEE/ACM.

## When to trigger / scope

- Any mainstream CS topic needing OA + constructive review; USENIX-linked authors may see partnership benefits.
- Power×CS: applied ML/systems/security for energy IT with CS framing.
- Weak fit: pure materials/energy engineering.

## Venue-specific calibration

- **Reviewer lens:** developmental — fixable weaknesses expected to be revised, not instantly rejected for incrementalism.
- Fingerprint: PeerJ · CC BY options · optional open peer review · APC **or** lifetime membership · USENIX partnership.

## Method & evidence bar / house style

- Clear claims, adequate experiments/proofs for the contribution type; PeerJ submission system; data/code encouraged.
- Payment: **APC ≈ US$2,155** **or** individual **lifetime publishing membership** (publish yearly for life across PeerJ journals) — verify current pricing.

### Distilled patterns

No local 10-paper power full-text cache. Calibrate as soundness OA CS. See `../../resources/target-journals-2026-batch-distill.md`.

## Desk-reject / re-routing

- Non-CS scope; fatal methodological flaws.
- Re-route: Discover Computing (cheaper discount window); IEEE Access; MDPI Information; Scientific Reports; selective conferences.

## Output format

```text
[Target] PeerJ Computer Science
[Fit] High / Medium / Low
[Cost] APC ~US$2,155 or lifetime membership (verify)
[Re-route] Discover Computing | IEEE Access | Information
```
"""
    + FOOT,
)

w(
    "ieee-internet-of-things-journal",
    """---
name: ieee-internet-of-things-journal
description: Use when targeting IEEE Internet of Things Journal (IoT-J) — a selective hybrid IEEE journal for IoT architectures, protocols, services, and applications. Encodes novelty+system evidence bar, page charges, hybrid OA APC, and review timelines.
---

# IEEE Internet of Things Journal (IoT-J)

## Journal positioning

IEEE Internet of Things Journal (ISSN 2327-4662) is a **selective, high-IF hybrid** journal jointly published by IEEE Sensors Council, ComSoc, Computer Society, and Signal Processing Society. It publishes advances and reviews on **IoT system architecture, enabling technologies, communication/networking, services/applications, and social implications**. Unlike MDPI Future Internet, **novelty, system significance, and IoT centrality** are gated.

- Metrics (as-of 2026-08 — **verify https://ieee-iotj.org/**): IF ≈ **8.7–8.9** (**Q1**); 5-year IF ~9+. Average submission→first decision ≈ **6.9 weeks**; submission→ePublication ≈ **14.5 weeks**. Acceptance rate roughly ~20% (secondary reports — verify).

## When to trigger / scope

- IoT architectures, protocols, edge intelligence, sensing+network stacks, smart-city/smart-grid **as IoT systems**.
- Power×CS: DER/AMI/edge state estimation, LLM-aided edge learning for distribution sensing — must be **IoT-system framed**.
- Weak fit: offline ML on CSV; pure power markets; non-networked algorithms → Energies / Algorithms / Access.

## Venue-specific calibration

- **Reviewer lens:** IoT contribution + rigorous evaluation (testbed, traces, large-scale sim) + comparison to recent IoT-J/ComSoc baselines.
- Fingerprint: selective IEEE · hybrid OA · page charges · single-blind · ORCID required · IoT centrality.
- Official: ieee-iotj.org + Author Guidelines PDF.

## Method & evidence bar / house style

- System/architecture contribution clear in abstract; threat/scale model if security; reproducible settings; strong related work vs recent IoT-J papers.
- IEEE template; **mandatory page charge ~US$175/page after first 8 pages** (verify guidelines). ORCID for all authors. Plagiarism screening. ≥2 independent reviewers, single-blind.

## APC / hybrid OA

- Traditional subscription track: **no OA APC** (subscribers access).
- OA track: APC ≈ **US$2,695** for 2025 submissions (2024 was $2,495) — verify current. IEEE/Society member discounts may apply (not for students). Overlength page charges separate.

### Distilled patterns

Local corpus has IoT-J candidates (e.g. LLM-aided edge learning for distribution SE on SimBench-class topics) but few open PDFs. Expect **system diagram + edge/cloud split + metrics under IoT constraints**. See `../../resources/target-journals-2026-batch-distill.md`.

## Desk-reject / re-routing

- Not IoT-centric; incremental app without system novelty; weak evaluation.
- Re-route: Future Internet / Sensors (faster OA); IEEE Access (soundness); TII / TNSM / Sensors Journal (siblings); Energies (energy-primary).

## Output format

```text
[Target] IEEE Internet of Things Journal
[Fit] High / Medium / Low (IoT system novelty?)
[Cost/Speed] hybrid; OA ~US$2,695 + page charges · ~7 wk first decision · IF~8.7 Q1
[Main evidence gap] <testbed / IoT baselines / overlength plan>
[Re-route] Future Internet | Sensors | IEEE Access | TII
```
"""
    + FOOT,
)

w(
    "ijacsa",
    """---
name: ijacsa
description: Use when targeting IJACSA (International Journal of Advanced Computer Science and Applications, The SAI Organization) — a low-to-mid Scopus/ESCI OA CS journal. Encode APC, claimed double-blind process, indexing, and reputation caveats for committee-sensitive authors.
---

# International Journal of Advanced Computer Science and Applications (IJACSA)

## Journal positioning

IJACSA (The Science and Information Organization, eISSN 2156-5570) is a **gold OA monthly** CS journal covering mainstream computer science and AI applications. It is **indexed** (Scopus CiteScore ≈ **3.4** Q3; WoS **ESCI** JIF ≈ **1.1** Q3 — as-of 2026-08 snapshots) but sits at **low-to-mid prestige**; some committees discount SAI titles. Advise authors **transparently**. Homepage: https://thesai.org/Publications/IJACSA.

## When to trigger / scope

- Broad CS/AI application papers needing indexed OA at relatively low APC.
- Power×CS: only if CS method is clear; energy-primary better at Energies/Access.
- Prefer stronger venues when 评职/graduation requires Q1/high reputation.

## Venue-specific calibration

- Publisher claims **double-blind** review and ~**15%** acceptance — treat as self-reported; still apply soundness standards yourself.
- Fingerprint: SAI · low APC · ESCI/Scopus · broad CS · reputation-sensitive.

## Method & evidence bar / house style

- Standard IMRaD CS paper; baselines for empirical ML; English clarity.
- APC (verify CFP): Standard ≈ **GBP £800**; student/reviewer ≈ **£750**; optional hardcopy certificate add-on.

### Distilled patterns

No curated local power full-text set. Do not treat as equivalent to IEEE Access/PeerJ for reputation. See `../../resources/target-journals-2026-batch-distill.md`.

## Desk-reject / re-routing

- Prefer **IEEE Access, PeerJ CS, Discover Computing, MDPI Information** when budget allows and reputation matters.
- Energy-primary → Energies / Energy Reports.

## Output format

```text
[Target] IJACSA (The SAI)
[Fit] High / Medium / Low (with reputation caveat)
[Cost] ~£800 APC · ESCI IF~1.1 / Scopus CS~3.4 (verify)
[Re-route] IEEE Access | PeerJ CS | Discover Computing | Information
```
"""
    + FOOT,
)

w(
    "wiley-ccpe",
    """---
name: wiley-ccpe
description: Use when targeting Concurrency and Computation Practice and Experience (Wiley) for parallel/distributed/HPC/cloud/edge systems and concurrent algorithms. Encodes hybrid model, scope around concurrency, and evidence expectations.
---

# Concurrency and Computation: Practice and Experience (CCPE)

## Journal positioning

CCPE (Wiley, ISSN 1532-0626 / 1532-0634) publishes original research and reviews on **parallel and distributed computing**, HPC, computational/data science, AI/ML systems, big data, security, cloud/edge/fog, green and quantum computing — with **concurrency/distributed systems practice** as the connective tissue. Homepage: https://onlinelibrary.wiley.com/journal/15320634.

- Metrics (as-of 2026-08 — **verify Wiley/Clarivate**): IF historically ~**1.5** range; Scopus CiteScore ~**5.4** (Scimago) — confirm current JCR. Hybrid journal (subscription + OA option).

## When to trigger / scope

- Parallel algorithms, distributed systems, cloud/edge scheduling, concurrent ML training/serving, HPC practice.
- Power×CS: **distributed grid simulation, edge scheduling for DER fleets, concurrent optimization** — concurrency must be real.
- Weak fit: single-threaded forecasting notebook.

## Venue-specific calibration

- **Reviewer lens:** scalability, concurrency correctness/performance, experimental methodology on parallel platforms.
- Fingerprint: Wiley · hybrid · practice & experience · parallel/distributed.

## Method & evidence bar / house style

- Speedup/scalability curves, platform specs, baselines; Wiley author guidelines; data availability encouraged.
- OA APC if choosing gold OA — **verify current Wiley OA price** for CCPE (varies by agreement).

### Distilled patterns

No local 10-paper cache. See `../../resources/target-journals-2026-batch-distill.md`.

## Desk-reject / re-routing

- No concurrency/distributed angle.
- Re-route: IEEE TPDS / cluster computing venues; Future Internet; IEEE Access; Algorithms.

## Output format

```text
[Target] CCPE (Wiley)
[Fit] High / Medium / Low (concurrency/distributed central?)
[Model] Hybrid · verify OA APC
[Re-route] Future Internet | IEEE Access | Algorithms | TPDS-class
```
"""
    + FOOT,
)

w(
    "elsevier-journal-of-energy-storage",
    """---
name: elsevier-journal-of-energy-storage
description: Use when targeting Journal of Energy Storage (Elsevier) for batteries, BESS, thermal/mechanical/electrical storage, grid integration of storage, and storage markets/control. Encodes high-IF selective hybrid bar and storage-centrality gate.
---

# Journal of Energy Storage (Elsevier)

## Journal positioning

Journal of Energy Storage (ISSN 2352-152X) is Elsevier’s **high-IF, storage-centric** hybrid journal covering **all aspects of energy storage** — technologies, modelling, grid integration, sizing/management, markets/policy, testing/safety. Storage must be the **object of study**, not a side component.

- Metrics (as-of 2026-08 — **verify ScienceDirect / Clarivate**): IF ≈ **9.8–10.7** (**Q1** Energy). Hybrid; OA APC ≈ **US$3,690** (2026 secondary snapshot — verify). Desk rejection meaningful (~30–40% reported); median first decision often **4–8 weeks** (secondary — verify).

## When to trigger / scope

- Batteries/BESS, supercapacitors, thermal/mechanical/chemical storage, V2G, storage markets (FCR/aFRR), sizing & EMS, LCA/safety of storage.
- Power×CS: RL/optimization for BESS, market-based EMS — **storage performance/integration evidence required**.
- Weak fit: general power forecasting without storage; pure materials chemistry better at specialized electrochemistry journals.

## Venue-specific calibration

- **Reviewer lens:** storage KPIs (efficiency, cycle life, SOC, degradation, cost) + baselines under fair conditions.
- Fingerprint: Elsevier · high IF · storage-central · hybrid OA expensive · scenario/techno-economic depth.

## Method & evidence bar / house style

- Clear storage technology + duty cycle; benchmark vs peer systems; units consistency; cycling/stability where claimed; Elsevier guide for authors (EM/Editorial Manager).
- Cover letter should state the storage advance (stability, integration, cost, control).

### Distilled patterns

Local open-data map flags **M5BAT / European balancing BESS** companions toward this venue (`../../resources/powergrid-open-data-corpus-distill.md`). Market+SOC+grid service papers fit; thin ML wrappers without storage metrics do not.

## Desk-reject / re-routing

- Incremental without storage novelty; missing benchmarks; scope mismatch.
- Re-route: Energies / Energy Reports (faster/cheaper OA); Applied Energy / Energy (selective); IEEE T-Sustainable Energy / Smart Grid; Batteries (MDPI).

## Output format

```text
[Target] Journal of Energy Storage (Elsevier)
[Fit] High / Medium / Low (storage-central + KPIs?)
[Cost/Speed] hybrid; OA ~US$3.7k · IF~10 Q1 · weeks-months
[Re-route] Energies | Energy Reports | Applied Energy | IEEE TSG/TSTE
```
"""
    + FOOT,
)

w(
    "keai-unconventional-resources",
    """---
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

### Distilled patterns

No power-grid full-text corpus expected. See `../../resources/target-journals-2026-batch-distill.md`.

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
"""
    + FOOT,
)

print("ALL DONE")
