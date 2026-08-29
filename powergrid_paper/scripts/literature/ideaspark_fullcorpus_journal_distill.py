# -*- coding: utf-8 -*-
"""Full-corpus IdeaSpark journal distill over ALL local literature PDFs.

Discovers PDFs under papers/literature/, maps each to a Paper_CCF journal slug
(path heuristics + text/DOI cues), then induces IdeaSpark-style acceptance
pattern cards and patches matching skills.

Method: ResearchStudio-Idea / IdeaSpark (arXiv:2607.04439) @ D:/aicoding/mylib
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIT = ROOT / "papers/literature"
META = LIT / "target_journal_related/metadata"
OUT_LIT = META / "ideaspark_fullcorpus_lit_tables"
OUT_CARDS = META / "ideaspark_fullcorpus_pattern_cards"
OUT_MD = META / "ideaspark_fullcorpus_distill_notes.md"
OUT_JSON = META / "ideaspark_fullcorpus_distill.json"
OUT_MAP = META / "ideaspark_fullcorpus_pdf_journal_map.csv"
SKILL_ROOT = Path.home() / ".claude/skills/Paper_CCF/journals"
BATCH_MD = Path.home() / ".claude/skills/Paper_CCF/resources/ideaspark-fullcorpus-journal-distill.md"
SECTION_HEADER = "### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)"

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # type: ignore

# Import pattern catalogs from the focused script by redefining (keep self-contained)
# --- IdeaSpark 15 + journal-house patterns (same as ideaspark_journal_pattern_distill) ---
IDEA_PATTERNS = {
    "assumption_audit_and_pivot": {
        "name": "Audit and Pivot an Assumption",
        "alias": "Audit the load-bearing assumption and pivot",
        "sig": "identify implicit assumption → relax/violate → re-derive",
        "re": re.compile(
            r"\b(assumption|relax(?:ed|ing)?|counterexample|weaker\s+condition|"
            r"without\s+assuming|drop(?:ping)?\s+the\s+assumption)\b",
            re.I,
        ),
    },
    "architectural_operator_substitution": {
        "name": "Substitute the Operator or Representation",
        "alias": "Substitute the operator or representation",
        "sig": "expensive operator → cheaper surrogate → preserve property",
        "re": re.compile(
            r"\b(replac(?:e|ing)|substitut|instead\s+of\s+(?:attention|lstm|transformer)|"
            r"lightweight|efficient\s+(?:variant|alternative)|surrogate)\b",
            re.I,
        ),
    },
    "generative_process_redesign": {
        "name": "Liberate a Fixed Generative Component",
        "alias": "Liberate a fixed generative component",
        "sig": "fixed pipeline component → treat as free variable → redesign",
        "re": re.compile(
            r"\b(redesign|pipeline|end[- ]to[- ]end|stage(?:d|s)?|iterative\s+process|"
            r"generative\s+(?:process|model)|diffusion|denoising)\b",
            re.I,
        ),
    },
    "controlled_diagnostic_design": {
        "name": "Design a Confound-Isolating Diagnostic",
        "alias": "Design a confound-isolating diagnostic",
        "sig": "confound → controlled instances → isolate true property",
        "re": re.compile(
            r"\b(ablation|sensitivity\s+analy|confound|diagnostic|fair\s+comparison|"
            r"controlled\s+experiment|leakage)\b",
            re.I,
        ),
    },
    "unify_into_shared_representation": {
        "name": "Unify Heterogeneous Inputs into One Space",
        "alias": "Unify heterogeneous inputs in one space",
        "sig": "heterogeneous inputs → shared representation → uniform model",
        "re": re.compile(
            r"\b(multi[- ]?modal|shared\s+representation|unified\s+(?:model|framework)|"
            r"joint\s+(?:embedding|learning)|heterogeneous)\b",
            re.I,
        ),
    },
    "reframe_as_solvable_object": {
        "name": "Reframe as a Solvable Object",
        "alias": "Reformulate the unsolved as a solvable object",
        "sig": "intractable problem → well-studied object → existing solvers",
        "re": re.compile(
            r"\b(formulate[sd]?|reformulat|cast\s+as|integer\s+program|MILP|game[- ]theoretic|"
            r"optimization\s+problem|as\s+a\s+(?:graph|matching|scheduling))\b",
            re.I,
        ),
    },
    "self_supervised_signal_engineering": {
        "name": "Manufacture the Supervisory Signal",
        "alias": "Manufacture the supervisory signal",
        "sig": "missing labels → manufacture signal → train/adapt",
        "re": re.compile(
            r"\b(self[- ]supervised|pseudo[- ]label|unlabeled|semi[- ]supervised|"
            r"contrastive|pretext)\b",
            re.I,
        ),
    },
    "structural_prior_encoding": {
        "name": "Encode Structure by Construction",
        "alias": "Encode structure by construction",
        "sig": "known structure → bake into operators → satisfied by construction",
        "re": re.compile(
            r"\b(physics[- ]informed|by\s+construction|topology|graph\s+neural|"
            r"invarian(?:t|ce)|symmetry|power\s+flow\s+constraint|kirchhoff)\b",
            re.I,
        ),
    },
    "algebraic_equivalence_unification": {
        "name": "Prove Equivalence to Unify",
        "alias": "Prove equivalence to unify methods",
        "sig": "two methods → prove equivalence → unify",
        "re": re.compile(
            r"\b(equivalen(?:ce|t)|unify|unification|special\s+case|prov(?:e|es|ed)\s+that|"
            r"theorem|lemma)\b",
            re.I,
        ),
    },
    "heterogeneous_decomposition": {
        "name": "Decompose for Differentiated Treatment",
        "alias": "Decompose heterogeneity for differentiated treatment",
        "sig": "heterogeneity → partition → differentiated treatment",
        "re": re.compile(
            r"\b(decompos(?:e|ition)|cluster(?:ing)?|segment(?:ation)?|hierarchical|"
            r"multi[- ]scale|partition)\b",
            re.I,
        ),
    },
    "decompose_and_delegate": {
        "name": "Decompose and Delegate to Solvers",
        "alias": "Decompose and delegate to solvers",
        "sig": "hard problem → subproblems → specialized solvers",
        "re": re.compile(
            r"\b(multi[- ]agent|delegat|modular|pipeline\s+of|sub[- ]?problem|"
            r"coordinator|solver)\b",
            re.I,
        ),
    },
    "relax_discrete_search_to_continuous": {
        "name": "Relax Discrete Search to Continuous",
        "alias": "Relax discrete search to continuous",
        "sig": "discrete search → continuous relaxation → optimize",
        "re": re.compile(
            r"\b(relax(?:ation|ed)?|continuous\s+relax|differentiable|soft(?:max)?|"
            r"Gumbel|surrogate\s+loss)\b",
            re.I,
        ),
    },
    "adapt_via_conditioning": {
        "name": "Adapt by Conditioning, Not Retraining",
        "alias": "Adapt by conditioning, not retraining",
        "sig": "new condition → condition/adapters → avoid full retrain",
        "re": re.compile(
            r"\b(few[- ]shot|adapter|LoRA|conditioning|prompt|transfer\s+learning|"
            r"domain\s+adapt|fine[- ]tun)\b",
            re.I,
        ),
    },
    "characterize_limit_then_surpass": {
        "name": "Characterize a Limit, Then Surpass It",
        "alias": "Characterize the limit, then surpass it",
        "sig": "prove limit → design method that surpasses",
        "re": re.compile(
            r"\b(lower\s+bound|upper\s+bound|limitation\s+of|impossibility|"
            r"theoretical\s+limit|surpass)\b",
            re.I,
        ),
    },
    "targeted_self_supervised_objective": {
        "name": "Design a Property-Targeting Pretext Objective",
        "alias": "Design a property-targeting pretext objective",
        "sig": "target property → pretext objective → transfer",
        "re": re.compile(
            r"\b(pretext|pretraining\s+objective|masked|reconstruction\s+loss|"
            r"auxiliary\s+(?:task|loss))\b",
            re.I,
        ),
    },
}

JOURNAL_PATTERNS = {
    "named_stack_plus_case": {
        "name": "Named Method Stack + Utility/IEEE Case",
        "alias": "Ship a named stack validated on a named case",
        "sig": "name the stack → public/IEEE/utility case → metrics table → optional ablation",
        "when": "Applied CS×energy venues",
        "success": [
            "Method components are named.",
            "Named dataset/case present.",
            "Comparison table with ≥2 baselines.",
        ],
        "fail": [
            "Combination novelty without gap.",
            "Private-only data.",
            "No baseline table.",
        ],
        "re": re.compile(
            r"\b(IEEE\s*\d+|baseline|compared\s+with|proposed\s+(?:method|model|framework)|"
            r"case\s+study|MAE|RMSE|F1|accuracy)\b",
            re.I,
        ),
    },
    "survey_or_review_synthesis": {
        "name": "Survey / Taxonomy Synthesis",
        "alias": "Organize a field into a usable taxonomy",
        "sig": "scope → taxonomy → open challenges",
        "when": "Review-friendly OA journals",
        "success": ["Inclusion criteria", "Taxonomy tables", "Forward challenges"],
        "fail": ["Unstructured dump", "No coverage statement"],
        "re": re.compile(r"\b(review|survey|taxonomy|literature)\b", re.I),
    },
    "hardware_or_field_validation": {
        "name": "Hardware / Field Validation First",
        "alias": "Lead with bench or field evidence",
        "sig": "setup → measurement → compare",
        "when": "Machines / Sensors / applied engineering",
        "success": ["Reproducible physical setup", "Measured results primary"],
        "fail": ["Simulation-only hardware claims"],
        "re": re.compile(
            r"\b(experimental\s+setup|prototype|test\s*bench|hardware|field\s+test|"
            r"measurement|laboratory)\b",
            re.I,
        ),
    },
    "systems_security_or_iot_stack": {
        "name": "Systems / IoT / Security Stack",
        "alias": "End-to-end system with threat or deployment story",
        "sig": "system/threat model → architecture → eval",
        "when": "IoT / Future Internet / CCPE / Access security",
        "success": ["Threat/system model", "Realistic traces + resource metrics"],
        "fail": ["Bake-off without system narrative"],
        "re": re.compile(
            r"\b(IoT|SCADA|cyber|attack|intrusion|edge|latency|throughput|"
            r"blockchain|cloud)\b",
            re.I,
        ),
    },
    "storage_or_energy_device_review": {
        "name": "Energy Storage / Device Technology",
        "alias": "Technology-centered energy storage synthesis",
        "sig": "technology → properties → applications → outlook",
        "when": "Energy Storage / Energies / Unconventional Resources",
        "success": ["Parameter tables", "Application + limits"],
        "fail": ["Generic AI without device physics"],
        "re": re.compile(
            r"\b(battery|BESS|flywheel|supercapacitor|thermal\s+storage|SOH|SOC|"
            r"electrochem|coalbed|CCUS|reservoir)\b",
            re.I,
        ),
    },
    "power_system_planning_ops": {
        "name": "Power-System Planning / Operations Case",
        "alias": "Grid planning or ops on named network",
        "sig": "grid case → method → cost/reliability metrics",
        "when": "Energies / CSEE JPES / OAJPE / PCMP / Energy Reports",
        "success": ["Named bus/test system", "Operational or planning KPIs"],
        "fail": ["Generic ML on ETT with thin grid sentence"],
        "re": re.compile(
            r"\b(unit\s+commitment|optimal\s+power\s+flow|distribution\s+network|"
            r"transmission\s+expansion|resilience|dispatch|load\s+forecast|"
            r"microgrid|renewable\s+integrat)\b",
            re.I,
        ),
    },
}

# text/DOI cues → Paper_CCF slug
JOURNAL_CUES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"10\.3390/app|Applied Sciences|applsci", re.I), "mdpi-applied-sciences"),
    (re.compile(r"10\.3390/en\d|Energies\b|energies-", re.I), "mdpi-energies"),
    (re.compile(r"10\.3390/electronics|Electronics\b", re.I), "mdpi-electronics"),
    (re.compile(r"10\.3390/sensors|Sensors\b", re.I), "mdpi-sensors"),
    (re.compile(r"10\.3390/sustainability", re.I), "mdpi-sustainability"),
    (re.compile(r"10\.3390/math|Mathematics\b", re.I), "mdpi-mathematics"),
    (re.compile(r"10\.3390/algorithms|Algorithms\b", re.I), "mdpi-algorithms"),
    (re.compile(r"10\.3390/atmosphere|Atmosphere\b", re.I), "mdpi-atmosphere"),
    (re.compile(r"10\.3390/fi\d|Future Internet", re.I), "mdpi-future-internet"),
    (re.compile(r"10\.3390/info|Information\b", re.I), "mdpi-information"),
    (re.compile(r"10\.3390/machines|Machines\b", re.I), "mdpi-machines"),
    (re.compile(r"10\.3390/remotesensing|Remote Sensing", re.I), "mdpi-remote-sensing"),
    (re.compile(r"10\.3390/sym\d|Symmetry\b", re.I), "mdpi-symmetry"),
    (re.compile(r"10\.32604/cmc|Computers?, Materials? (&|and) Continua|\bCMC\b", re.I), "tsp-cmc"),
    (re.compile(r"10\.1038/s41598|Scientific Reports", re.I), "nature-scientific-reports"),
    (re.compile(r"10\.7717/peerj-cs|PeerJ Computer Science", re.I), "peerj-computer-science"),
    (re.compile(r"10\.1007/s\d+|Discover Computing", re.I), "springer-discover-computing"),
    (re.compile(r"10\.1002/cpe\.|Concurrency and Computation|CCPE", re.I), "wiley-ccpe"),
    (re.compile(r"10\.1109/JIOT|Internet of Things Journal", re.I), "ieee-internet-of-things-journal"),
    (re.compile(r"10\.1109/ACCESS|IEEE Access", re.I), "ieee-access"),
    (re.compile(r"10\.1109/OAJPE|Open Access Journal of Power", re.I), "ieee-oajpe"),
    (re.compile(r"10\.1016/j\.est\.|Journal of Energy Storage", re.I), "elsevier-journal-of-energy-storage"),
    (re.compile(r"10\.1016/j\.egyr\.|Energy Reports", re.I), "elsevier-energy-reports"),
    (re.compile(r"10\.1016/j\.heliyon|Heliyon", re.I), "elsevier-heliyon"),
    (re.compile(r"10\.1016/j\.uncres|Unconventional Resources", re.I), "keai-unconventional-resources"),
    (re.compile(r"10\.14569/IJACSA|IJACSA", re.I), "ijacsa"),
    (re.compile(r"CSEE Journal of Power|CSEE JPES", re.I), "csee-jpes"),
    (re.compile(r"Protection and Control of Modern Power|PCMP", re.I), "pcmp"),
    (re.compile(r"Frontiers in Energy Research", re.I), "frontiers-energy-research"),
]

PATH_SLUG = {
    "fulltext_by_journal": None,  # child dir is slug
    "cmc_pdfs": "tsp-cmc",
    "applied_sciences_power_ai_10": "mdpi-applied-sciences",
    "applied_sciences_power_grid_recent": "mdpi-applied-sciences",
}


def extract_text(pdf: Path, max_pages: int = 6) -> tuple[int, str]:
    try:
        r = PdfReader(str(pdf))
        n = len(r.pages)
        text = "\n".join((r.pages[i].extract_text() or "") for i in range(min(n, max_pages)))
        return n, text
    except Exception as e:
        return 0, f"ERROR:{e}"


def infer_slug_from_path(pdf: Path) -> str | None:
    parts = pdf.parts
    # .../fulltext_by_journal/<slug>/file.pdf
    if "fulltext_by_journal" in parts:
        i = parts.index("fulltext_by_journal")
        if i + 1 < len(parts):
            return parts[i + 1]
    if "cmc_pdfs" in parts:
        return "tsp-cmc"
    if "applied_sciences_power_ai_10" in parts or "applied_sciences_power_grid_recent" in parts:
        return "mdpi-applied-sciences"
    # filename prefix slug__
    m = re.match(r"([a-z0-9\-]+)__", pdf.name)
    if m and (SKILL_ROOT / m.group(1)).exists():
        return m.group(1)
    return None


def infer_slug_from_text(text: str) -> str | None:
    head = text[:12000]
    for cre, slug in JOURNAL_CUES:
        if cre.search(head):
            return slug
    return None


def guess_title(text: str, fallback: str) -> str:
    for ln in text.splitlines()[:30]:
        s = ln.strip()
        if 25 <= len(s) <= 180:
            low = s.lower()
            if any(x in low for x in ("creative commons", "doi", "http", "received", "abstract", "keywords", "arxiv")):
                continue
            return s
    return fallback[:120]


def extract_abstract(text: str) -> str:
    m = re.search(
        r"Abstract\s*[:：]?\s*(.{80,1600}?)(?:\n\s*Keywords|\n\s*1[\.\s]|Introduction)",
        text,
        re.I | re.S,
    )
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def score_patterns(blob: str, catalog: dict) -> list[tuple[str, int]]:
    hits = []
    for pid, meta in catalog.items():
        n = len(meta["re"].findall(blob))
        if n:
            hits.append((pid, n))
    hits.sort(key=lambda x: -x[1])
    return hits


def bottleneck_guess(blob: str) -> str:
    rules = [
        (r"forecast|prediction|load", "forecasting accuracy / uncertainty"),
        (r"optimiz|dispatch|scheduling|opf|unit commitment", "optimization / dispatch tractability"),
        (r"fault|anomaly|detection|diagnos", "detection under noise/imbalance"),
        (r"security|attack|intrusion|privacy", "security/privacy under adversaries"),
        (r"storage|battery|SOH|SOC", "storage modeling / lifetime"),
        (r"IoT|edge|latency", "edge resource / latency"),
        (r"planning|expansion|resilience", "planning / resilience under uncertainty"),
        (r"remote\s+sensing|satellite|atmosphere", "sensing / atmospheric confounds"),
    ]
    for pat, label in rules:
        if re.search(pat, blob, re.I):
            return label
    return "application gap vs prior method stacks"


def tag_paper(pdf: Path, slug: str, text: str, n_pages: int) -> dict:
    title = guess_title(text, pdf.stem)
    abstract = extract_abstract(text)
    blob = (title + "\n" + abstract + "\n" + text[:12000]).lower()
    idea_hits = score_patterns(blob, IDEA_PATTERNS)
    jour_hits = score_patterns(blob, JOURNAL_PATTERNS)
    primary = idea_hits[0][0] if idea_hits else "outside_taxonomy"
    supporting = [p for p, _ in idea_hits[1:3]]
    j_primary = jour_hits[0][0] if jour_hits else ""
    tags = [primary] + supporting
    if j_primary:
        tags.append(j_primary)
    return {
        "file": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        "slug": slug,
        "error": "",
        "pages": n_pages,
        "title": title,
        "abstract": abstract[:400],
        "primary_pattern": primary,
        "supporting_patterns": supporting,
        "journal_pattern": j_primary,
        "pattern_tags": tags,
        "bottleneck": bottleneck_guess(blob),
        "open_issue": "generalization / data access / stronger baselines still open"
        if re.search(r"future\s+work|limitation", blob, re.I)
        else "saturation risk if only incremental stacking",
        "has_baseline": bool(re.search(r"baseline|compared with|comparison", blob)),
        "has_ablation": bool(re.search(r"ablation|sensitivity", blob)),
        "has_dataset": bool(re.search(r"dataset|ieee\s*\d+|benchmark", blob)),
    }


def write_lit_table(slug: str, rows: list[dict]) -> None:
    OUT_LIT.mkdir(parents=True, exist_ok=True)
    path = OUT_LIT / f"{slug}_lit_table.md"
    lines = [
        f"# lit_table — `{slug}` (full local corpus, IdeaSpark-adapted)\n",
        "paper_id | venue | title | ideation pattern tags | bottleneck | open issue | retrieved_via",
        "---|---|---|---|---|---|---",
    ]
    for r in rows:
        if r.get("error"):
            continue
        tags = ", ".join(r.get("pattern_tags") or [])
        title = (r.get("title") or "").replace("|", "/")[:100]
        lines.append(
            f"`{Path(r['file']).name}` | {slug} | {title} | {tags} | "
            f"{r.get('bottleneck','')} | {r.get('open_issue','')} | local_fulltext"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_cards(slug: str, rows: list[dict]) -> dict:
    ok = [r for r in rows if not r.get("error")]
    idea_c = Counter(r["primary_pattern"] for r in ok)
    jour_c = Counter(r["journal_pattern"] for r in ok if r.get("journal_pattern"))
    combo = Counter()
    for r in ok:
        tags = [t for t in r.get("pattern_tags") or [] if t in IDEA_PATTERNS]
        if len(tags) >= 2:
            combo[tuple(sorted(tags[:2]))] += 1

    card_dir = OUT_CARDS / slug
    card_dir.mkdir(parents=True, exist_ok=True)
    ov = [
        f"# Acceptance pattern overview — `{slug}` (full local corpus)\n",
        f"n={len(ok)} PDFs · method: ResearchStudio-Idea / IdeaSpark (arXiv:2607.04439)\n",
        "## IdeaSpark primary distribution\n",
        "| pattern_id | n | name |",
        "|---|---:|---|",
    ]
    for pid, n in idea_c.most_common():
        ov.append(f"| `{pid}` | {n} | {IDEA_PATTERNS.get(pid, {}).get('name', pid)} |")
    ov += ["\n## Journal-house distribution\n", "| pattern_id | n | name |", "|---|---:|---|"]
    for pid, n in jour_c.most_common():
        ov.append(f"| `{pid}` | {n} | {JOURNAL_PATTERNS.get(pid, {}).get('name', pid)} |")
    ov.append("\n## Companion combos\n")
    for (a, b), n in combo.most_common(8):
        ov.append(f"- `{a}` + `{b}` ×{n}")
    if not combo:
        ov.append("- (sparse)")
    (card_dir / "overview.md").write_text("\n".join(ov) + "\n", encoding="utf-8")

    for pid, n in idea_c.most_common(5):
        if pid not in IDEA_PATTERNS:
            continue
        meta = IDEA_PATTERNS[pid]
        examples = [r for r in ok if r["primary_pattern"] == pid][:5]
        card = [
            f"# {meta['name']}",
            f"_id: `{pid}` · journal=`{slug}` · primary_count={n}_\n",
            f"**Operational signature**. {meta['sig']}\n",
            f"**When to apply in `{slug}`**. When accepted local papers execute this move.\n",
            "## Success conditions",
            "- Named bottleneck closed by the operational signature.",
            "- Venue-appropriate evidence (baselines/case/figures).",
            "- Explicit differentiation vs nearest prior.\n",
            "## Failure modes",
            "- Mechanical wrapper of known modules.",
            "- Confounded or single-toy evidence.",
            "- Untouched true bottleneck.\n",
            "## Local examples",
        ]
        for e in examples:
            card.append(f"- {e['title'][:110]} — {e['bottleneck']}")
        (card_dir / f"{pid}.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    for pid, n in jour_c.most_common(4):
        if pid not in JOURNAL_PATTERNS:
            continue
        meta = JOURNAL_PATTERNS[pid]
        card = [
            f"# {meta['name']}",
            f"_id: `{pid}` · journal=`{slug}` · count={n}_\n",
            f"**Operational signature**. {meta['sig']}\n",
            f"**When to apply**. {meta['when']}\n",
            "## Success conditions",
            *[f"- {x}" for x in meta["success"]],
            "\n## Failure modes",
            *[f"- {x}" for x in meta["fail"]],
        ]
        (card_dir / f"{pid}.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    return {
        "n": len(ok),
        "idea_dist": dict(idea_c),
        "journal_dist": dict(jour_c),
        "combos": ["+".join(k) for k, _ in combo.most_common(5)],
        "dominant_idea": idea_c.most_common(1)[0][0] if idea_c else "outside_taxonomy",
        "dominant_journal": jour_c.most_common(1)[0][0] if jour_c else "",
        "baseline_rate": sum(1 for r in ok if r.get("has_baseline")) / max(len(ok), 1),
        "ablation_rate": sum(1 for r in ok if r.get("has_ablation")) / max(len(ok), 1),
        "dataset_rate": sum(1 for r in ok if r.get("has_dataset")) / max(len(ok), 1),
        "pages_mean": round(sum(r.get("pages") or 0 for r in ok) / max(len(ok), 1), 1),
    }


def skill_block(slug: str, summary: dict) -> str:
    if summary["n"] == 0:
        return "_No mapped local PDFs for this journal in the full corpus pass._\n"
    di, dj = summary["dominant_idea"], summary["dominant_journal"]
    top_idea = ", ".join(
        f"`{k}`×{v}" for k, v in sorted(summary["idea_dist"].items(), key=lambda kv: -kv[1])[:6]
    )
    top_jour = ", ".join(
        f"`{k}`×{v}" for k, v in sorted(summary["journal_dist"].items(), key=lambda kv: -kv[1])[:5]
    ) or "n/a"
    combos = ", ".join(f"`{c}`" for c in summary["combos"][:5]) or "sparse"
    return "\n".join(
        [
            f"- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass "
            f"over `papers/literature/**` → `D:/aicoding/mylib/ResearchStudio/ResearchStudio-Idea`.",
            f"- Sample: **n={summary['n']}** mapped local PDFs (mean ~{summary['pages_mean']} pages extracted).",
            f"- **Dominant IdeaSpark move:** `{di}` — *{IDEA_PATTERNS.get(di, {}).get('name', di)}*.",
            f"- **Dominant journal-house move:** `{dj or 'n/a'}` — "
            f"*{JOURNAL_PATTERNS.get(dj, {}).get('name', dj or 'n/a')}*.",
            f"- IdeaSpark primary distribution: {top_idea}.",
            f"- Journal-house distribution: {top_jour}.",
            f"- Attested multi-pattern combos: {combos}.",
            f"- Evidence readiness: baseline **{summary['baseline_rate']:.0%}**, "
            f"ablation **{summary['ablation_rate']:.0%}**, dataset/benchmark **{summary['dataset_rate']:.0%}**.",
            "- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → "
            "audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.",
            f"- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/{slug}/overview.md`, "
            f"`metadata/ideaspark_fullcorpus_lit_tables/{slug}_lit_table.md`.",
        ]
    ) + "\n"


def patch_skill(slug: str, block: str) -> bool:
    path = SKILL_ROOT / slug / "SKILL.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_sec = (
        f"{SECTION_HEADER}\n\n{block}\n"
        f"Corpus: all discoverable PDFs under `papers/literature/` mapped to `{slug}`.\n"
    )
    # replace full-corpus section if present; else replace prior ideaspark section; else insert
    if SECTION_HEADER in text:
        text = re.sub(
            rf"{re.escape(SECTION_HEADER)}.*?(?=\n## |\n### [^R]|\Z)",
            new_sec + "\n",
            text,
            count=1,
            flags=re.S,
        )
    elif "### ResearchStudio-Idea acceptance patterns" in text:
        text = re.sub(
            r"### ResearchStudio-Idea acceptance patterns.*?(?=\n## |\n### [^R]|\Z)",
            new_sec + "\n",
            text,
            count=1,
            flags=re.S,
        )
    elif "### Distilled deep structure" in text:
        m = re.search(r"### Distilled deep structure.*?(?=\n## |\n### |\Z)", text, flags=re.S)
        if m:
            text = text[: m.end()] + "\n" + new_sec + text[m.end() :]
        else:
            text = text.rstrip() + "\n\n" + new_sec
    else:
        m = re.search(r"\n## (APC|Review|Official|Common desk|Desk|Method)", text)
        if m:
            text = text[: m.start()] + "\n" + new_sec + text[m.start() :]
        else:
            text = text.rstrip() + "\n\n" + new_sec
    path.write_text(text, encoding="utf-8")
    return True


def discover_pdfs() -> list[Path]:
    pdfs = []
    for p in LIT.rglob("*.pdf"):
        if any(x in p.parts for x in ("_probe", "openalex_raw")):
            continue
        pdfs.append(p)
    return sorted(pdfs)


def main():
    META.mkdir(parents=True, exist_ok=True)
    pdfs = discover_pdfs()
    print(f"discovered {len(pdfs)} PDFs under {LIT}", flush=True)

    by_slug: dict[str, list[dict]] = defaultdict(list)
    map_rows = []
    unmapped = 0
    seen_hash: set[str] = set()

    for i, pdf in enumerate(pdfs, 1):
        # dedupe by content hash of first 64KB
        try:
            h = hashlib.sha1(pdf.read_bytes()[:65536]).hexdigest()
        except Exception:
            h = pdf.name
        if h in seen_hash:
            continue
        seen_hash.add(h)

        slug = infer_slug_from_path(pdf)
        n_pages, text = extract_text(pdf)
        if text.startswith("ERROR:"):
            map_rows.append({"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "slug": "", "via": "error"})
            continue
        via = "path"
        if not slug:
            slug = infer_slug_from_text(text)
            via = "text" if slug else ""
        if not slug:
            unmapped += 1
            map_rows.append(
                {
                    "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                    "slug": "unmapped",
                    "via": "none",
                    "title": guess_title(text, pdf.stem)[:80],
                }
            )
            if i % 40 == 0:
                print(f"  …{i}/{len(pdfs)} unmapped_so_far={unmapped}", flush=True)
            continue

        # only keep journals we have skills for OR still produce cards
        rec = tag_paper(pdf, slug, text, n_pages)
        by_slug[slug].append(rec)
        map_rows.append(
            {
                "pdf": rec["file"],
                "slug": slug,
                "via": via,
                "title": rec["title"][:80],
                "primary_pattern": rec["primary_pattern"],
            }
        )
        if i % 25 == 0:
            print(f"  …{i}/{len(pdfs)} mapped_slugs={len(by_slug)}", flush=True)

    # write map csv
    import csv

    with OUT_MAP.open("w", encoding="utf-8", newline="") as f:
        fields = sorted({k for r in map_rows for k in r})
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(map_rows)

    print(f"mapped journals={len(by_slug)} unmapped={unmapped}", flush=True)

    all_json = {}
    md = [
        "# IdeaSpark full-corpus journal distill (2026-08)\n",
        f"Scanned `{LIT}` — {len(pdfs)} PDFs, {len(seen_hash)} unique, "
        f"{sum(len(v) for v in by_slug.values())} tagged into journals, {unmapped} unmapped.\n",
        "Method: ResearchStudio-Idea / IdeaSpark (arXiv:2607.04439) @ `D:/aicoding/mylib`.\n",
    ]
    batch = [
        "# IdeaSpark full-corpus journal distill\n",
        "Induced from ALL local literature PDFs under `powergrid_benchmark/papers/literature/`.\n",
        "| slug | n | dominant_idea | dominant_house | baseline% | skill |",
        "|---|---:|---|---|---:|:---:|",
    ]

    for slug in sorted(by_slug):
        rows = by_slug[slug]
        print(f"=== {slug} n={len(rows)} ===", flush=True)
        write_lit_table(slug, rows)
        summary = build_cards(slug, rows)
        block = skill_block(slug, summary)
        patched = patch_skill(slug, block)
        print(f"  patched={patched} dominant={summary['dominant_idea']}", flush=True)
        all_json[slug] = {"summary": summary, "n_papers": len(rows)}
        md.append(f"## {slug}\n\n{block}")
        batch.append(
            f"| `{slug}` | {summary['n']} | `{summary['dominant_idea']}` | "
            f"`{summary['dominant_journal']}` | {100*summary['baseline_rate']:.0f}% | "
            f"{'Y' if patched else 'N'} |"
        )

    # unmapped note
    md.append(
        f"## unmapped\n\nn={unmapped} PDFs (mostly arXiv seeds / ambiguous venue). "
        f"See `{OUT_MAP.name}`.\n"
    )
    batch.append(f"\nUnmapped PDFs: **{unmapped}** (see `ideaspark_fullcorpus_pdf_journal_map.csv`).\n")

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(all_json, ensure_ascii=False, indent=2), encoding="utf-8")
    BATCH_MD.write_text("\n".join(batch), encoding="utf-8")
    print("wrote", OUT_MD, flush=True)
    print("wrote", OUT_JSON, flush=True)
    print("wrote", BATCH_MD, flush=True)
    print("wrote", OUT_MAP, flush=True)


if __name__ == "__main__":
    main()
