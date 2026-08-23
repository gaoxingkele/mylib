#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build data/venues.json — the machine-readable export of the Paper_CCF skill.

Single source of truth = the authored profiles under ../journals and ../skills plus
../resources/conference-roster.md. This script re-emits the structured, machine-readable
view so OTHER PROJECTS (e.g. paper_reviews) can consume Paper_CCF programmatically.

Regenerate after editing profiles/roster:  py build_venues.py

All metrics are 2026-07 snapshots flagged verify=True; the authored SKILL.md profile
(profile_path) remains the human-readable source of nuance and caveats.
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # the Paper_CCF skill dir
ROSTER = os.path.join(ROOT, "resources", "conference-roster.md")
OUT = os.path.join(HERE, "venues.json")

AS_OF = "2026-07"

# --- 15 journals: structured records mirroring the authored journals/<slug>/SKILL.md ---
# decision_model: binary | tiered | collaborative | soundness  (paper_reviews wants binary|tiered)
# power_cs_fit: high | medium | low ;  level: top|strong|standard|regional (paper_reviews strictness)
JOURNALS = [
  {
    "slug": "ieee-access", "name": "IEEE Access", "publisher": "IEEE", "oa_model": "gold",
    "decision_model": "binary", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2160, "currency": "USD", "note": "per article; verify"},
    "metrics": {"impact_factor": 4.2, "quartile": "Q2", "citescore": 9.3},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "~4 weeks", "to_publication": "~4-6 weeks",
               "binary": True, "notes": "one resubmission after a (conditional) reject; no revision ping-pong"},
    "power_cs_fit": "high", "core_rule": "soundness NOT novelty; binary Accept/Reject",
    "aims_scope": "IEEE's multidisciplinary gold-OA megajournal across all IEEE fields; judged on technical soundness/quality, not novelty or impact.",
    "hard_gates": ["english_fatal", "technical_fatal", "unfair_comparison_fatal", "retracted_refs", "not_distinct", "out_of_scope"],
    "desk_reject": ["poor English/clarity", "insufficient rigor/validation", "out of IEEE scope",
                    "self-plagiarism/duplicate submission", "incremental without soundness"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "no_concurrent_submission": True, "min_reviews": 2},
    "neighbors": ["selective IEEE Transactions", "nature-scientific-reports", "elsevier-heliyon", "mdpi-electronics"],
    "fingerprint": ["binary accept/reject", "soundness-not-novelty", "IEEE OA megajournal", "rapid ~4-week review", "all IEEE fields"],
    "official_url": "https://ieeeaccess.ieee.org/",
  },
  {
    "slug": "pcmp", "name": "Protection and Control of Modern Power Systems", "publisher": "IEEE (ex-SpringerOpen)",
    "oa_model": "diamond", "decision_model": "tiered", "level": "strong", "free_to_publish": True,
    "apc": {"amount": 0, "currency": None, "note": "diamond OA, free; confirm on IEEE Xplore after publisher migration"},
    "metrics": {"impact_factor": 11.9, "quartile": "Q1", "citescore": 22.8},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind (verify)", "first_decision": "~4 weeks", "to_publication": None,
               "notes": "fastest power journal here; selective ~66 articles/yr"},
    "power_cs_fit": "high", "core_rule": "FREE + fastest + highest IF, but scope = protection/control/fault/stability ONLY",
    "scope_constraint": "protection, control, fault diagnosis/location, stability, resilience (incl. AI applied to these)",
    "aims_scope": "New theories/technologies in protection and control of modern power systems: relay protection, fault diagnosis/location, stability & control, DER integration, resilience, and data-driven/AI methods applied to protection/control.",
    "hard_gates": [],
    "desk_reject": ["off-scope: generic ML/forecasting with no protection/control angle", "weak validation / no scheme comparison", "AI-protection reliability unaddressed"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "neighbors": ["csee-jpes", "ieee-oajpe", "mdpi-energies", "ieee-access", "IEEE T-Power Delivery/Power Systems/Smart Grid"],
    "fingerprint": ["relay protection", "fault diagnosis", "stability control", "diamond OA (free)", "fast review", "Q1"],
    "official_url": "https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=10352418",
  },
  {
    "slug": "csee-jpes", "name": "CSEE Journal of Power and Energy Systems", "publisher": "CSEE + IEEE",
    "oa_model": "gold", "decision_model": "tiered", "level": "strong", "free_to_publish": False,
    "apc": {"amount": 120, "currency": "USD", "per": "page", "note": "CNY 800 / USD 120 per page from 2026-01-01; verify"},
    "metrics": {"impact_factor": 5.9, "quartile": "Q1", "citescore": 12.8},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "~60-80 days (~2-3 months)", "to_publication": "~26 weeks",
               "notes": "~40% desk-rejected at preliminary examination; rapid-communication fast-track exists"},
    "power_cs_fit": "high", "core_rule": "broad smart-grid / data-driven power; Q1 society journal on IEEE Xplore",
    "aims_scope": "All aspects of power & energy systems incl. renewable integration, power electronics, integrated/multi-energy systems, sensing/big-data, and energy cyber-physical systems.",
    "hard_gates": [],
    "desk_reject": ["weak significance (hits ~40% desk-reject gate)", "thin power-system contribution (pure algorithm)", "out of power/energy scope"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "neighbors": ["pcmp", "ieee-oajpe", "mdpi-energies", "ieee-access", "IEEE T-Power Systems/Smart Grid"],
    "fingerprint": ["smart grid", "data-driven power", "power electronics", "energy cyber-physical", "Q1 society journal"],
    "official_url": "https://www.csee.org.cn/english/APC/",
  },
  {
    "slug": "ieee-oajpe", "name": "IEEE Open Access Journal of Power and Energy", "publisher": "IEEE PES",
    "oa_model": "gold", "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2160, "currency": "USD", "note": "2026 submissions; rises yearly; verify"},
    "metrics": {"impact_factor": 2.8, "quartile": "Q1 (Scimago; JCR borderline Q1/Q2)", "citescore": 2.9},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "not published (verify)", "to_publication": "~10 weeks (soft estimate)",
               "notes": "rejected papers barred from resubmission for 3 months"},
    "power_cs_fit": "medium", "core_rule": "power systems + IEEE brand; APC-funded (not free)",
    "aims_scope": "Planning, design, operation, and control of equipment and power systems for generation, transmission, distribution, storage, and usage of electric energy.",
    "hard_gates": [],
    "desk_reject": ["weak/insufficient validation", "out of power scope", "incremental with thin practical relevance"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "neighbors": ["pcmp", "csee-jpes", "ieee-access", "mdpi-energies", "IEEE T-Smart Grid/Power Systems"],
    "fingerprint": ["power systems", "PMU/data analytics", "renewable integration", "IEEE PES", "gold OA"],
    "official_url": "https://ieeeaccess.ieee.org/",
  },
  {
    "slug": "mdpi-energies", "name": "Energies", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2600, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 4.0, "quartile": "Q2 (Energy & Fuels)", "citescore": 7.3},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "~16-17 days", "to_publication": "~3-4 days after acceptance",
               "notes": "MDPI SuSy; Section + heavy Special-Issue model; DORA (negative results ok)"},
    "power_cs_fit": "high", "core_rule": "broad energy engineering with a clear application; DORA; major-revision norm",
    "aims_scope": "MDPI's broad gold-OA energy journal: energy engineering, power systems, renewables, storage, efficiency, conversion, fuels, techno-economic and energy-policy analysis.",
    "hard_gates": [],
    "desk_reject": ["no clear energy relevance / out of scope", "unvalidated incremental simulation", "poor English/formatting", "missing data-availability statement", "excessive self-citation"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["ieee-access", "csee-jpes", "elsevier-energy-reports", "mdpi-sustainability", "Applied Energy / Renewable Energy (Elsevier)"],
    "fingerprint": ["energy systems", "power systems / smart grid", "storage", "techno-economic", "gold OA", "Special-Issue-driven"],
    "official_url": "https://www.mdpi.com/journal/energies",
  },
  {
    "slug": "mdpi-electronics", "name": "Electronics", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2400, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 2.9, "quartile": "Q2 (EE)", "citescore": 6.1},
    "indexing": ["SCIE", "Scopus", "EI", "DBLP"],
    "review": {"model": "single-blind", "first_decision": "~15 days", "to_publication": "~3 days after acceptance",
               "notes": "~16 Sections + Special Issues"},
    "power_cs_fit": "high", "core_rule": "applied EE/CS, soundness over novelty; section-routed",
    "aims_scope": "The science of electronics and its applications: EE/electronic engineering, computer science, embedded/IoT, power/industrial electronics, communications/networks, circuits, semiconductors, control, and AI/ML applied to electronic systems.",
    "hard_gates": [],
    "desk_reject": ["pure theory/math with no electronics/computing system", "clinical/biomedical (wrong venue)", "too preliminary / no evaluation", "wrong Section", "poor English"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["ieee-access", "mdpi-sensors", "mdpi-applied-sciences", "IEEE T-IE/T-PEL/T-CAS", "IET journals"],
    "fingerprint": ["applied AI/ML", "embedded/IoT", "power & industrial electronics", "semiconductors", "communications & networks"],
    "official_url": "https://www.mdpi.com/journal/electronics",
  },
  {
    "slug": "mdpi-applied-sciences", "name": "Applied Sciences", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2400, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 2.9, "quartile": "~Q2 (Eng. Multidisciplinary)", "citescore": 6.1},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "~15-16 days", "to_publication": "~3 days after acceptance",
               "notes": "~32 Sections + Special Issues; desk-rejects out-of-scope in ~7 days"},
    "power_cs_fit": "medium", "core_rule": "very broad applied science/eng; application over theory; section-routed",
    "aims_scope": "Very broad multidisciplinary applied natural sciences and engineering; emphasis on applications and experimental/numerical validation over pure theory.",
    "hard_gates": [],
    "desk_reject": ["purely theoretical / no application", "validated only under idealized conditions", "missing/narrow benchmark comparisons", "topic outside any Section", "incremental least-publishable-unit"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["ieee-access", "mdpi-electronics", "mdpi-sensors", "nature-scientific-reports", "elsevier-heliyon"],
    "fingerprint": ["multidisciplinary", "applied engineering", "application over theory", "experimental validation", "Section-routed"],
    "official_url": "https://www.mdpi.com/journal/applsci",
  },
  {
    "slug": "mdpi-sensors", "name": "Sensors", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2600, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 3.5, "quartile": "Q2 (Instruments & Instrumentation)", "citescore": 8.2},
    "indexing": ["SCIE", "Scopus", "EI"],
    "review": {"model": "single-blind", "first_decision": "~18 days", "to_publication": "~3 days after acceptance"},
    "power_cs_fit": "medium", "core_rule": "sensing/measurement must be CENTRAL (grid monitoring/PMU/IoT)",
    "aims_scope": "Science and technology of sensors, sensing systems, and their applications; the sensing/measurement/transduction element must be central.",
    "hard_gates": [],
    "desk_reject": ["pure ML/algorithm with no real sensing element", "generic IoT/networking with no measurement contribution", "wrong Section", "off-scope Special Issue"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["mdpi-electronics", "mdpi-applied-sciences", "ieee-access", "IEEE Sensors Journal", "Measurement (Elsevier)"],
    "fingerprint": ["sensing", "measurement", "IoT", "condition monitoring", "PMU", "sensor networks"],
    "official_url": "https://www.mdpi.com/journal/sensors",
  },
  {
    "slug": "mdpi-machines", "name": "Machines", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2400, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 2.5, "quartile": "mid (Q1 Control by CiteScore)", "citescore": 4.7},
    "indexing": ["SCIE", "Scopus"],
    "review": {"model": "single-blind", "first_decision": "~16 days", "to_publication": "~3 days after acceptance"},
    "power_cs_fit": "medium", "core_rule": "concrete machine/drive/control system required",
    "aims_scope": "Machinery, mechanical engineering, and machine/mechatronic systems: electrical machines & drives, motor control, mechatronics/robotics, machine fault diagnosis/condition monitoring, powertrain.",
    "hard_gates": [],
    "desk_reject": ["generic AI/optimization/signal-processing with no physical machine/drive/control system", "weak validation", "out of Section scope"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["mdpi-electronics", "mdpi-energies", "ieee-access", "MDPI Actuators", "IEEE T-Industrial Electronics/Power Electronics"],
    "fingerprint": ["electrical machines", "motor drives", "control", "mechatronics", "fault diagnosis", "condition monitoring"],
    "official_url": "https://www.mdpi.com/journal/machines",
  },
  {
    "slug": "mdpi-mathematics", "name": "Mathematics", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2600, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 2.3, "quartile": "Q1 (Mathematics)", "citescore": 4.6},
    "indexing": ["SCIE", "Scopus"],
    "review": {"model": "single-blind", "first_decision": "~17 days", "to_publication": "~3 days after acceptance"},
    "power_cs_fit": "low", "core_rule": "genuine mathematical contribution required (optimization / ML theory)",
    "aims_scope": "Broad mathematical sciences, pure and applied; a genuine mathematical contribution (theorem/proof, rigorous model, convergence/complexity, well-founded numerical/optimization/ML-theory method) is required.",
    "hard_gates": [],
    "desk_reject": ["applied ML/engineering with no mathematical novelty ('we ran a model')", "hand-wavy/incomplete proofs", "out of Section scope"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["mdpi-applied-sciences", "ieee-access", "MDPI Axioms/Symmetry/Algorithms", "Applied Mathematics and Computation (Elsevier)"],
    "fingerprint": ["optimization", "theorem/proof", "numerical methods", "ML theory", "probability", "dynamical systems"],
    "official_url": "https://www.mdpi.com/journal/mathematics",
  },
  {
    "slug": "mdpi-sustainability", "name": "Sustainability", "publisher": "MDPI", "oa_model": "gold",
    "decision_model": "tiered", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2400, "currency": "CHF", "note": "after acceptance; verify"},
    "metrics": {"impact_factor": 3.3, "quartile": "Q2 (Environmental/Green)", "citescore": 8.0},
    "indexing": ["SCIE", "Scopus"],
    "review": {"model": "single-blind", "first_decision": "~17 days", "to_publication": "~4 days after acceptance"},
    "power_cs_fit": "medium", "core_rule": "substantive sustainability / SDG angle required (not decorative)",
    "aims_scope": "Environmental, economic, and social sustainability and sustainable development; the sustainability/SDG/impact angle must be substantive.",
    "hard_gates": [],
    "desk_reject": ["pure engineering/ML with only a token 'sustainable' mention", "sustainability claim asserted but not evidenced", "out of Section scope"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True, "dora_signatory": True},
    "neighbors": ["mdpi-energies", "mdpi-applied-sciences", "ieee-access", "Renewable & Sustainable Energy Reviews / J. Cleaner Production (Elsevier)"],
    "fingerprint": ["sustainability", "SDGs", "renewable energy", "energy policy", "smart grid", "environmental impact"],
    "official_url": "https://www.mdpi.com/journal/sustainability",
  },
  {
    "slug": "elsevier-energy-reports", "name": "Energy Reports", "publisher": "Elsevier", "oa_model": "gold",
    "decision_model": "tiered", "level": "strong", "free_to_publish": False,
    "apc": {"amount": 3040, "currency": "USD", "note": "Elsevier list; some sources ~2360; get personalized quote"},
    "metrics": {"impact_factor": 6.4, "quartile": "Q1 (Energy & Fuels)", "citescore": None, "note": "IF ~6.3-6.6, historically volatile"},
    "indexing": ["SCIE", "Scopus", "EI", "DOAJ"],
    "review": {"model": "single-blind", "first_decision": "not published (weeks to ~1-2 mo)", "to_publication": "~16 weeks",
               "notes": "tight ~20-day revised-manuscript window; gold-OA companion to Energy/Applied Energy"},
    "power_cs_fit": "high", "core_rule": "AI-for-energy; energy contribution (not the algorithm) must be the point",
    "aims_scope": "Broad energy research incl. power systems, smart grids, energy informatics, forecasting, and AI/ML/optimization applied to energy; Elsevier gold-OA companion to Energy and Applied Energy.",
    "hard_gates": [],
    "desk_reject": ["thin energy-domain contribution (pure algorithm)", "scope drift", "weak validation", "poor English/structure"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "flags": ["2024 retractions tied to fictitious authorship; verify current WoS coverage"],
    "neighbors": ["mdpi-energies", "ieee-access", "frontiers-energy-research", "Applied Energy / Energy (Elsevier)"],
    "fingerprint": ["AI-for-energy", "power systems & smart grids", "gold-OA companion", "Q1 Energy & Fuels", "fast-ish"],
    "official_url": "https://www.sciencedirect.com/journal/energy-reports",
  },
  {
    "slug": "frontiers-energy-research", "name": "Frontiers in Energy Research", "publisher": "Frontiers", "oa_model": "gold",
    "decision_model": "collaborative", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2695, "currency": "CHF", "note": "Type A; Type B CHF 2195; verify"},
    "metrics": {"impact_factor": 2.58, "quartile": "Q2 (some sources Q3)", "citescore": 5.0},
    "indexing": ["SCIE", "Scopus", "DOAJ"],
    "review": {"model": "collaborative/interactive (named reviewers, Review Forum)", "first_decision": None, "to_publication": "~12 weeks",
               "notes": "avg review <~90 days; AIRA AI integrity pre-check; reviewer/editor names published"},
    "power_cs_fit": "medium", "core_rule": "section-based; route power+CS via Smart Grids / Energy Systems Engineering sections",
    "aims_scope": "Broad energy journal in ~16 specialty sections; power+CS/AI routes via Smart Grids, Process and Energy Systems Engineering, and Sustainable Energy Systems sections.",
    "hard_gates": [],
    "desk_reject": ["out-of-section scope", "AIRA integrity flag", "insufficient methodology per reviewer checklist"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "flags": ["contested reputation (2015 Beall's list, later offline); JCR-2023 Frontiers-wide IF cuts; present as reputable-but-debated"],
    "neighbors": ["mdpi-energies", "ieee-access", "elsevier-energy-reports"],
    "fingerprint": ["interactive/collaborative review", "named reviewers", "section-based", "smart grids section", "AIRA integrity AI"],
    "official_url": "https://www.frontiersin.org/journals/energy-research",
  },
  {
    "slug": "nature-scientific-reports", "name": "Scientific Reports", "publisher": "Nature Portfolio", "oa_model": "gold",
    "decision_model": "soundness", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 2850, "currency": "USD", "note": "verify"},
    "metrics": {"impact_factor": 3.8, "quartile": "Q1 (Multidisciplinary)", "citescore": 5.8},
    "indexing": ["SCIE", "Scopus", "PMC", "DOAJ"],
    "review": {"model": "single-blind", "first_decision": "~20 days (first editorial touch only)", "to_publication": "~4-6 months full cycle",
               "notes": "NOT fast despite marketed first-decision; soundness-not-novelty; multiple revision rounds common"},
    "power_cs_fit": "medium", "core_rule": "soundness NOT novelty; broad; stable indexing; NOT fast",
    "aims_scope": "One of the largest journals; all natural sciences, medicine, psychology, and engineering; judged solely on scientific/technical validity, not importance/impact. Original research only (not standalone reviews).",
    "hard_gates": [],
    "desk_reject": ["methodological/statistical flaws", "insufficient data/controls", "out of scope (pure review / specialist venue)", "weak reporting/ethics"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True, "data_availability_required": True},
    "neighbors": ["ieee-access", "elsevier-heliyon", "mdpi-applied-sciences", "PLOS ONE", "Nature Communications (higher tier)"],
    "fingerprint": ["soundness-not-novelty", "Nature Portfolio megajournal", "all sciences + engineering", "NOT fast", "PLOS ONE analog"],
    "official_url": "https://www.nature.com/srep/",
  },
  {
    "slug": "elsevier-heliyon", "name": "Heliyon", "publisher": "Cell Press / Elsevier", "oa_model": "gold",
    "decision_model": "soundness", "level": "standard", "free_to_publish": False,
    "apc": {"amount": 1950, "currency": "USD", "note": "verify"},
    "metrics": {"impact_factor": 3.4, "quartile": "uncertain (WoS on-hold)", "citescore": 4.0},
    "indexing": ["Scopus (active)"],
    "review": {"model": "section editors + external (single-blind)", "first_decision": "moderate/variable by section", "to_publication": None},
    "power_cs_fit": "medium", "core_rule": "soundness-based; dedicated Engineering & Computer Science sections; cheaper",
    "aims_scope": "Large multidisciplinary soundness-based megajournal with named sections incl. Heliyon Engineering and Heliyon Computer Science.",
    "hard_gates": [],
    "desk_reject": ["methodological weakness", "poor reporting", "out-of-section scope", "integrity/ethics concerns"],
    "policies": {"ai_use_disclosure": True, "ethics_required": True},
    "flags": ["INDEXING RISK: Web of Science / SCIE ON HOLD since 2024-09 (unresolved into 2026); 2025 retraction surge (~392); confirm live WoS status before relying on it"],
    "indexing_risk": True,
    "neighbors": ["nature-scientific-reports", "mdpi-applied-sciences", "ieee-access", "PLOS ONE"],
    "fingerprint": ["Cell Press megajournal", "Engineering & CS sections", "soundness-based", "cheaper APC", "WoS on-hold"],
    "official_url": "https://www.cell.com/heliyon/home",
  },
]

# paper_reviews decision_threshold convention: binary->6.0, else 5.5 (broad soundness megajournals 6.0)
def pr_threshold(dm):
    return 6.0 if dm in ("binary", "soundness") else 5.5

def pr_decision_model(dm):
    return "binary" if dm == "binary" else "tiered"

def parse_conferences(path):
    confs = []
    if not os.path.exists(path):
        return confs
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not re.match(r"^\|\s*\d+\s*\|", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            slug = cells[1].strip("`")
            if slug == "cs-ai-conference-workflow":
                continue
            confs.append({
                "slug": slug, "type": "conference", "acronym": cells[3],
                "name": cells[2], "area": cells[4], "official_url": cells[5],
                "selectivity": "conference (novelty-gated)",
                "profile_path": f"skills/{slug}/SKILL.md",
            })
    return confs

def main():
    for j in JOURNALS:
        j["type"] = "journal"
        j["as_of"] = AS_OF
        j["verify"] = True
        j["profile_path"] = f"journals/{j['slug']}/SKILL.md"
        j["paper_reviews"] = {
            "venue": j["slug"].replace("-", "_"),
            "full_name": j["name"],
            "level": j["level"],
            "decision_model": pr_decision_model(j["decision_model"]),
            "decision_threshold": pr_threshold(j["decision_model"]),
            "aims_scope": j["aims_scope"],
            "policies": j["policies"],
            "alt_venues": j["neighbors"],
        }
    confs = parse_conferences(ROSTER)
    data = {
        "schema": "paper_ccf/venues@1",
        "as_of": AS_OF,
        "source": "Paper_CCF skill (~/.claude/skills/Paper_CCF); authored SKILL.md profiles are the human-readable source of truth",
        "verify_note": "All IF/quartile/APC/review-times are 2026-07 snapshots; verify on each official_url before quoting.",
        "counts": {"journals": len(JOURNALS), "conferences": len(confs)},
        "journals": JOURNALS,
        "conferences": confs,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}: {len(JOURNALS)} journals + {len(confs)} conferences")

if __name__ == "__main__":
    main()
