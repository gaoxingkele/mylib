# -*- coding: utf-8 -*-
"""Induce IdeaSpark-style acceptance pattern cards from local journal full-texts.

Adapted from ResearchStudio-Idea / IdeaSpark (arXiv:2607.04439):
  evidence grounding → strategy signature → pattern tagging → operational cards
  → journal-level composition profile → patch Paper_CCF skills.

Corpus: papers/literature/target_journal_related/fulltext_by_journal/<slug>/*.pdf
Outputs:
  metadata/ideaspark_journal_lit_tables/<slug>_lit_table.md
  metadata/ideaspark_journal_pattern_cards/<slug>/overview.md (+ per-pattern snippets)
  metadata/ideaspark_journal_distill_notes.md
  metadata/ideaspark_journal_distill.json
  patches each ~/.claude/skills/Paper_CCF/journals/<slug>/SKILL.md
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
OUT_LIT = META / "ideaspark_journal_lit_tables"
OUT_CARDS = META / "ideaspark_journal_pattern_cards"
OUT_MD = META / "ideaspark_journal_distill_notes.md"
OUT_JSON = META / "ideaspark_journal_distill.json"
SKILL_ROOT = Path.home() / ".claude/skills/Paper_CCF/journals"
BATCH_MD = Path.home() / ".claude/skills/Paper_CCF/resources/target-journals-2026-batch-distill.md"
LIB_NOTE = Path(r"D:/aicoding/lib/papers/ResearchStudio-Idea_journal_adapt_note.md")

SECTION_HEADER = "### ResearchStudio-Idea acceptance patterns (local corpus, 2026-08)"

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # type: ignore

# IdeaSpark 15 patterns (ids from ResearchStudio-Idea) + journal-house patterns
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

# Journal-house acceptance patterns (powergrid OA venue lens)
JOURNAL_PATTERNS = {
    "named_stack_plus_case": {
        "name": "Named Method Stack + Utility/IEEE Case",
        "alias": "Ship a named stack validated on a named case",
        "sig": "name the stack → public/IEEE/utility case → metrics table → optional ablation",
        "when": "Applied CS×energy venues (CMC, Energies-adjacent, Information, Discover Computing)",
        "success": [
            "Method components are named (not anonymous 'improved CNN').",
            "At least one named dataset/case (IEEE bus, public load series, utility anonymized).",
            "Comparison table with ≥2 baselines and explicit metrics.",
        ],
        "fail": [
            "Novelty claimed as 'first combination' without gap statement.",
            "Only private data with no public proxy or sensitivity.",
            "No baseline table; only self-comparison of variants.",
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
        "sig": "scope the literature → taxonomy/framework → open challenges",
        "when": "Broad OA journals that accept reviews (Symmetry, Atmosphere, Future Internet, Sci Rep reviews)",
        "success": [
            "Explicit inclusion criteria / search protocol.",
            "Taxonomy tables or comparison dimensions.",
            "Forward-looking challenges tied to gaps.",
        ],
        "fail": [
            "Unstructured paper dump without axis.",
            "No dates/coverage statement.",
        ],
        "re": re.compile(r"\b(review|survey|taxonomy|literature|state[- ]of[- ]the[- ]art\s+review)\b", re.I),
    },
    "hardware_or_field_validation": {
        "name": "Hardware / Field Validation First",
        "alias": "Lead with bench or field evidence",
        "sig": "device/field setup → measurement → compare simulation/SOTA",
        "when": "Machines, Sensors, applied engineering tracks",
        "success": [
            "Physical setup described with enough detail to reproduce.",
            "Measured results primary; simulation secondary.",
        ],
        "fail": [
            "Simulation-only 'hardware' claims.",
            "Missing uncertainty / sensor specs.",
        ],
        "re": re.compile(
            r"\b(experimental\s+setup|prototype|test\s*bench|hardware|field\s+test|"
            r"measurement|laboratory)\b",
            re.I,
        ),
    },
    "systems_security_or_iot_stack": {
        "name": "Systems / IoT / Security Stack",
        "alias": "End-to-end system with threat or deployment story",
        "sig": "system model → threat/requirements → architecture → eval on traces",
        "when": "IEEE IoT Journal, Future Internet, CCPE, Information security tracks",
        "success": [
            "Clear system/threat model figure.",
            "Realistic traces or public datasets; latency/resource metrics.",
        ],
        "fail": [
            "Algorithm bake-off without system narrative.",
            "Toy network scale only.",
        ],
        "re": re.compile(
            r"\b(IoT|SCADA|cyber|attack|intrusion|edge|latency|throughput|"
            r"blockchain|cloud)\b",
            re.I,
        ),
    },
    "storage_or_energy_device_review": {
        "name": "Energy Storage / Device Technology Review",
        "alias": "Technology-centered energy storage synthesis",
        "sig": "technology class → properties/applications → comparison → outlook",
        "when": "Journal of Energy Storage, Unconventional Resources",
        "success": [
            "Technology parameters tabulated.",
            "Application scenarios and limitations stated.",
        ],
        "fail": [
            "Generic AI forecasting pasted onto storage without device physics.",
        ],
        "re": re.compile(
            r"\b(battery|BESS|flywheel|supercapacitor|thermal\s+storage|SOH|SOC|"
            r"electrochem|coalbed|CCUS|reservoir)\b",
            re.I,
        ),
    },
}


def extract_text(pdf: Path, max_pages: int = 8) -> tuple[int, str]:
    try:
        r = PdfReader(str(pdf))
        n = len(r.pages)
        pages = min(n, max_pages)
        text = "\n".join((r.pages[i].extract_text() or "") for i in range(pages))
        return n, text
    except Exception as e:
        return 0, f"ERROR:{e}"


def guess_title(text: str, fallback: str) -> str:
    for ln in text.splitlines()[:25]:
        s = ln.strip()
        if len(s) < 20 or len(s) > 200:
            continue
        low = s.lower()
        if any(x in low for x in ("creative commons", "doi", "http", "received", "abstract", "keywords")):
            continue
        return s
    return fallback[:120]


def extract_abstract(text: str) -> str:
    m = re.search(
        r"Abstract\s*[:：]?\s*(.{80,1800}?)(?:\n\s*Keywords|\n\s*1[\.\s]|Introduction)",
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
        (r"forecast|prediction|load", "forecasting accuracy / uncertainty under nonstationarity"),
        (r"optimiz|dispatch|scheduling|opf", "optimization tractability / constraint satisfaction"),
        (r"fault|anomaly|detection|diagnos", "detection reliability under noise/imbalance"),
        (r"security|attack|intrusion|privacy", "security/privacy under realistic adversaries"),
        (r"storage|battery|SOH|SOC", "storage modeling / lifetime / market coupling"),
        (r"IoT|edge|latency|bandwidth", "edge resource / latency / communication limits"),
        (r"remote\s+sensing|satellite|atmosphere", "sensing quality / atmospheric confounders"),
    ]
    for pat, label in rules:
        if re.search(pat, blob, re.I):
            return label
    return "application gap / incomplete method stack vs prior baselines"


def open_issue_guess(blob: str) -> str:
    if re.search(r"future\s+work|limitation|however|although", blob, re.I):
        return "generalization / scalability / data access still open"
    return "saturation risk if only incremental stacking without new diagnostic"


def tag_paper(pdf: Path) -> dict:
    n_pages, text = extract_text(pdf)
    if text.startswith("ERROR:"):
        return {"file": pdf.name, "error": text[6:], "pages": 0}
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
        "file": pdf.name,
        "error": "",
        "pages": n_pages,
        "title": title,
        "abstract": abstract[:500],
        "primary_pattern": primary,
        "supporting_patterns": supporting,
        "journal_pattern": j_primary,
        "pattern_tags": tags,
        "bottleneck": bottleneck_guess(blob),
        "open_issue": open_issue_guess(blob),
        "idea_scores": dict(idea_hits[:5]),
        "journal_scores": dict(jour_hits[:3]),
        "has_baseline": bool(re.search(r"baseline|compared with|comparison", blob)),
        "has_ablation": bool(re.search(r"ablation|sensitivity", blob)),
        "has_dataset": bool(re.search(r"dataset|ieee\s*\d+|benchmark", blob)),
    }


def write_lit_table(slug: str, rows: list[dict]) -> Path:
    OUT_LIT.mkdir(parents=True, exist_ok=True)
    path = OUT_LIT / f"{slug}_lit_table.md"
    lines = [
        f"# lit_table — `{slug}` (IdeaSpark-adapted tagging)\n",
        "paper_id | year_month | venue | title | ideation pattern tags | bottleneck this paper targets | open issue / unresolved gap | resolves_problem | retrieved_via",
        "---|---|---|---|---|---|---|---|---",
    ]
    for r in rows:
        if r.get("error"):
            continue
        # year from filename if present
        ym = "noyear"
        m = re.search(r"__(\d{4})__", r["file"])
        if m:
            ym = f"{m.group(1)}-01"
        tags = ", ".join(r.get("pattern_tags") or [])
        title = (r.get("title") or r["file"]).replace("|", "/")
        lines.append(
            f"`{r['file']}` | {ym} | {slug} | {title[:100]} | {tags} | "
            f"{r.get('bottleneck','')} | {r.get('open_issue','')} |  | local_fulltext"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_journal_cards(slug: str, rows: list[dict]) -> dict:
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

    # overview
    ov = [
        f"# Acceptance pattern overview — `{slug}`\n",
        f"Induced from **n={len(ok)}** local full-text PDFs using ResearchStudio-Idea / IdeaSpark method "
        f"(arXiv:2607.04439): strategy tagging → pattern distribution → operational cards.\n",
        "## IdeaSpark pattern distribution (primary)\n",
        "| pattern_id | n | name |",
        "|---|---:|---|",
    ]
    for pid, n in idea_c.most_common():
        name = IDEA_PATTERNS.get(pid, {}).get("name", pid)
        ov.append(f"| `{pid}` | {n} | {name} |")
    ov.append("\n## Journal-house pattern distribution\n")
    ov.append("| pattern_id | n | name |")
    ov.append("|---|---:|---|")
    for pid, n in jour_c.most_common():
        name = JOURNAL_PATTERNS.get(pid, {}).get("name", pid)
        ov.append(f"| `{pid}` | {n} | {name} |")
    ov.append("\n## Attested companion combos (pairwise primary+support)\n")
    if combo:
        for (a, b), n in combo.most_common(8):
            ov.append(f"- `{a}` + `{b}` ×{n}")
    else:
        ov.append("- (sparse multi-tag co-occurrence in this sample)")
    (card_dir / "overview.md").write_text("\n".join(ov) + "\n", encoding="utf-8")

    # top idea pattern cards for this journal
    for pid, n in idea_c.most_common(5):
        if pid not in IDEA_PATTERNS:
            continue
        meta = IDEA_PATTERNS[pid]
        examples = [r for r in ok if r["primary_pattern"] == pid][:4]
        card = [
            f"# {meta['name']}",
            f"_id: `{pid}` · journal=`{slug}` · primary_count={n}_\n",
            f"**Plain alias**. _{meta['alias']}_\n",
            f"**Operational signature**. {meta['sig']}\n",
            f"**When to apply (in `{slug}`)**. When local accepted papers in this venue execute this move "
            f"(see examples). Prefer composing with a journal-house pattern below.\n",
            "## Success conditions (from local accepted sample)",
            "- Contribution names a concrete bottleneck and closes it with the operational signature above.",
            "- Evidence matches venue bar (baselines / case / figures) as observed in tagged papers.",
            "- Differentiation stated vs nearest prior stack (not only 'we combine X+Y').\n",
            "## Failure modes (desk-reject risks adapted from IdeaSpark reject lessons)",
            "- Pattern executed as a mechanical wrapper of known modules without new identifying structure.",
            "- Preservation/claims supported only by a single toy case or confounded ablation.",
            "- True bottleneck left untouched while swapping a surface operator.\n",
            "## Local examples",
        ]
        for e in examples:
            card.append(f"- {e['title'][:110]} (`{e['file'][:40]}…`) — bottleneck: {e['bottleneck']}")
        (card_dir / f"{pid}.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    # journal-house cards
    for pid, n in jour_c.most_common(3):
        if pid not in JOURNAL_PATTERNS:
            continue
        meta = JOURNAL_PATTERNS[pid]
        card = [
            f"# {meta['name']}",
            f"_id: `{pid}` · journal=`{slug}` · count={n}_\n",
            f"**Plain alias**. _{meta['alias']}_\n",
            f"**Operational signature**. {meta['sig']}\n",
            f"**When to apply**. {meta['when']}\n",
            "## Success conditions",
            *[f"- {x}" for x in meta["success"]],
            "\n## Failure modes",
            *[f"- {x}" for x in meta["fail"]],
        ]
        (card_dir / f"{pid}.md").write_text("\n".join(card) + "\n", encoding="utf-8")

    dominant_idea = idea_c.most_common(1)[0][0] if idea_c else "outside_taxonomy"
    dominant_journal = jour_c.most_common(1)[0][0] if jour_c else ""
    return {
        "n": len(ok),
        "idea_dist": dict(idea_c),
        "journal_dist": dict(jour_c),
        "combos": ["+".join(k) for k, _ in combo.most_common(5)],
        "dominant_idea": dominant_idea,
        "dominant_journal": dominant_journal,
        "baseline_rate": sum(1 for r in ok if r.get("has_baseline")) / max(len(ok), 1),
        "ablation_rate": sum(1 for r in ok if r.get("has_ablation")) / max(len(ok), 1),
        "dataset_rate": sum(1 for r in ok if r.get("has_dataset")) / max(len(ok), 1),
    }


def skill_block(slug: str, summary: dict) -> str:
    if summary["n"] == 0:
        return (
            "_No local PDFs — cannot induce IdeaSpark-style acceptance cards. "
            "See `D:/aicoding/lib` ResearchStudio-Idea skill suite for the method; "
            "retry after OA mirrors for this venue are available._\n"
        )
    di = summary["dominant_idea"]
    dj = summary["dominant_journal"]
    di_name = IDEA_PATTERNS.get(di, {}).get("name", di)
    dj_name = JOURNAL_PATTERNS.get(dj, {}).get("name", dj or "n/a")
    top_idea = ", ".join(
        f"`{k}`×{v}" for k, v in sorted(summary["idea_dist"].items(), key=lambda kv: -kv[1])[:5]
    )
    top_jour = ", ".join(
        f"`{k}`×{v}" for k, v in sorted(summary["journal_dist"].items(), key=lambda kv: -kv[1])[:4]
    ) or "n/a"
    combos = ", ".join(f"`{c}`" for c in summary["combos"][:4]) or "sparse"
    lines = [
        f"- Method: **ResearchStudio-Idea / IdeaSpark** pattern induction (arXiv:2607.04439), "
        f"adapted to journal acceptance corpus (`D:/aicoding/lib/skills/ResearchStudio-Idea`).",
        f"- Sample: **n={summary['n']}** local PDFs → lit_table + pattern cards under "
        f"`papers/literature/target_journal_related/metadata/ideaspark_journal_*`.",
        f"- **Dominant IdeaSpark move:** `{di}` — *{di_name}*.",
        f"- **Dominant journal-house move:** `{dj or 'n/a'}` — *{dj_name}*.",
        f"- IdeaSpark primary distribution: {top_idea}.",
        f"- Journal-house distribution: {top_jour}.",
        f"- Attested multi-pattern combos: {combos}.",
        f"- Evidence readiness rates: baseline **{summary['baseline_rate']:.0%}**, "
        f"ablation/sensitivity **{summary['ablation_rate']:.0%}**, "
        f"dataset/benchmark cue **{summary['dataset_rate']:.0%}**.",
        "- **How to use when writing for this venue:**",
        f"  1. Pick the anchor bottleneck; select ≥1 IdeaSpark pattern (prefer `{di}`) "
        f"composed with journal-house `{dj or 'named_stack_plus_case'}`.",
        "  2. Instantiate the operational signature; name the differentiation vs nearest prior.",
        "  3. Audit against card failure modes (wrapper stacking, confound, untouched bottleneck).",
        "  4. Package evidence to match the observed readiness rates above.",
        f"- Cards: `metadata/ideaspark_journal_pattern_cards/{slug}/overview.md`.",
    ]
    return "\n".join(lines) + "\n"


def patch_skill(slug: str, block: str) -> bool:
    path = SKILL_ROOT / slug / "SKILL.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_sec = (
        f"{SECTION_HEADER}\n\n{block}\n"
        f"Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/{slug}/`.\n"
    )
    if SECTION_HEADER in text:
        text = re.sub(
            rf"{re.escape(SECTION_HEADER)}.*?(?=\n## |\n### [^R]|\Z)",
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


def main():
    META.mkdir(parents=True, exist_ok=True)
    all_json = {}
    md = [
        "# IdeaSpark-adapted journal acceptance distill (2026-08)\n",
        "Source method: ResearchStudio-Idea (arXiv:2607.04439) installed at `D:/aicoding/lib`.\n",
        "Pipeline: local PDF full-text → strategy/bottleneck cues → tag with 15 IdeaSpark patterns "
        "+ journal-house patterns → lit_table + operational cards → Paper_CCF skill sections.\n",
    ]
    batch_rows = []

    for d in sorted(PDF_ROOT.glob("*")):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        pdfs = sorted(d.glob("*.pdf"))[:12]
        print(f"=== {d.name} n={len(pdfs)} ===", flush=True)
        rows = []
        for pdf in pdfs:
            print(" ", pdf.name[:70], flush=True)
            rows.append(tag_paper(pdf))
        write_lit_table(d.name, rows)
        summary = build_journal_cards(d.name, rows)
        block = skill_block(d.name, summary)
        patched = patch_skill(d.name, block)
        print(f"  patched={patched} dominant={summary.get('dominant_idea')}", flush=True)
        all_json[d.name] = {"summary": summary, "papers": rows}
        md.append(f"## {d.name}\n\n{block}")
        batch_rows.append((d.name, summary))

    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(all_json, ensure_ascii=False, indent=2), encoding="utf-8")

    # append batch overview section
    extra = [
        "\n## ResearchStudio-Idea / IdeaSpark acceptance-pattern distill\n",
        "Method borrowed from `D:/aicoding/lib/skills/ResearchStudio-Idea` (arXiv:2607.04439).\n",
        "| slug | n | dominant_idea | dominant_journal_house | baseline% |",
        "|---|---:|---|---|---:|",
    ]
    for slug, s in batch_rows:
        extra.append(
            f"| `{slug}` | {s['n']} | `{s.get('dominant_idea','')}` | "
            f"`{s.get('dominant_journal','')}` | {100*s.get('baseline_rate',0):.0f}% |"
        )
    if BATCH_MD.exists():
        prev = BATCH_MD.read_text(encoding="utf-8")
        if "## ResearchStudio-Idea" in prev:
            prev = re.split(r"\n## ResearchStudio-Idea.*", prev, maxsplit=1)[0].rstrip()
        BATCH_MD.write_text(prev + "\n" + "\n".join(extra) + "\n", encoding="utf-8")
    else:
        BATCH_MD.write_text("\n".join(extra) + "\n", encoding="utf-8")

    LIB_NOTE.parent.mkdir(parents=True, exist_ok=True)
    LIB_NOTE.write_text(
        "\n".join(
            [
                "# ResearchStudio-Idea → powergrid journal distill adaptation\n",
                "Paper: https://arxiv.org/abs/2607.04439",
                "Code: D:/aicoding/lib/ResearchStudio/ResearchStudio-Idea",
                "Skills: D:/aicoding/lib/skills/ResearchStudio-Idea (+ ~/.claude/skills junctions)\n",
                "## What we reused",
                "- 15 ideation pattern vocabulary + operational-signature thinking",
                "- lit_table tagging schema (pattern tags / bottleneck / open issue)",
                "- Pattern cards with success conditions + failure modes",
                "- Multi-pattern composition (companion combos)\n",
                "## What we changed for journals",
                "- Corpus = accepted OA full-texts per target journal (not Oral/Reject conference labels)",
                "- Added journal-house patterns (named stack+case, survey, hardware, IoT/security, storage)",
                "- Outputs feed Paper_CCF `journals/*/SKILL.md` for manuscript routing/writing\n",
                f"Run script: `{ROOT}/scripts/literature/ideaspark_journal_pattern_distill.py`",
            ]
        ),
        encoding="utf-8",
    )
    print("wrote", OUT_MD, flush=True)
    print("wrote", OUT_JSON, flush=True)
    print("wrote", LIB_NOTE, flush=True)


if __name__ == "__main__":
    main()
