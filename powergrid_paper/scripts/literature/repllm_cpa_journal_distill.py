# -*- coding: utf-8 -*-
"""RepLLM Content-Parsing (CPA) enriched journal distill over ALL literature PDFs.

Adapts RepLLM (arXiv:2509.21074, SIGCOMM 2026) **Content Parsing + Shared Memory
paper.json** only — NOT Architecture/Code/Audit reproduction.

Pipeline:
  PDF → CPA-lite paper.json → section-scoped signals → IdeaSpark pattern tags
  → patch Paper_CCF journal skills + write corpus artifacts.

Depends on journal slug mapping shared with ideaspark_fullcorpus_journal_distill.py.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIT = ROOT / "papers/literature"
META = LIT / "target_journal_related/metadata"
OUT_JSON_DIR = META / "repllm_cpa_paper_json"
OUT_SUMMARY = META / "repllm_cpa_journal_distill.json"
OUT_NOTES = META / "repllm_cpa_journal_distill_notes.md"
OUT_LIT = META / "repllm_cpa_lit_tables"
BATCH_MD = Path.home() / ".claude/skills/Paper_CCF/resources/repllm-cpa-journal-distill.md"
SKILL_ROOT = Path.home() / ".claude/skills/Paper_CCF/journals"
SECTION_HEADER = "### RepLLM-CPA structured evidence (full local corpus, 2026-08)"
LIB_NOTE = Path(r"D:/aicoding/mylib/RepLLM/journal_adapt_note.md")

# Reuse mapping + patterns from IdeaSpark full-corpus script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ideaspark_fullcorpus_journal_distill import (  # noqa: E402
    IDEA_PATTERNS,
    JOURNAL_PATTERNS,
    discover_pdfs,
    infer_slug_from_path,
    infer_slug_from_text,
    score_patterns,
)


def infer_slug(pdf: Path, text: str) -> str | None:
    """Prefer path; for text, require DOI/ISSN-like cues (avoid bare 'Algorithms'/'Information')."""
    path_slug = infer_slug_from_path(pdf)
    if path_slug:
        return path_slug
    head = text[:12000]
    # DOI / distinctive venue strings only (skip megajournal bare-name false positives)
    strict = [
        (re.compile(r"10\.3390/app", re.I), "mdpi-applied-sciences"),
        (re.compile(r"10\.3390/en\d", re.I), "mdpi-energies"),
        (re.compile(r"10\.3390/electronics", re.I), "mdpi-electronics"),
        (re.compile(r"10\.3390/sensors", re.I), "mdpi-sensors"),
        (re.compile(r"10\.3390/sustainability", re.I), "mdpi-sustainability"),
        (re.compile(r"10\.3390/math", re.I), "mdpi-mathematics"),
        (re.compile(r"10\.3390/algorithms", re.I), "mdpi-algorithms"),
        (re.compile(r"10\.3390/atmosphere", re.I), "mdpi-atmosphere"),
        (re.compile(r"10\.3390/fi\d", re.I), "mdpi-future-internet"),
        (re.compile(r"10\.3390/info", re.I), "mdpi-information"),
        (re.compile(r"10\.3390/machines", re.I), "mdpi-machines"),
        (re.compile(r"10\.3390/remotesensing", re.I), "mdpi-remote-sensing"),
        (re.compile(r"10\.3390/sym\d", re.I), "mdpi-symmetry"),
        (re.compile(r"10\.32604/cmc", re.I), "tsp-cmc"),
        (re.compile(r"10\.1038/s41598", re.I), "nature-scientific-reports"),
        (re.compile(r"10\.7717/peerj-cs", re.I), "peerj-computer-science"),
        (re.compile(r"10\.1002/cpe\.", re.I), "wiley-ccpe"),
        (re.compile(r"10\.1109/JIOT", re.I), "ieee-internet-of-things-journal"),
        (re.compile(r"10\.1109/ACCESS", re.I), "ieee-access"),
        (re.compile(r"10\.1016/j\.est\.", re.I), "elsevier-journal-of-energy-storage"),
        (re.compile(r"10\.14569/IJACSA", re.I), "ijacsa"),
        (re.compile(r"Discover Computing", re.I), "springer-discover-computing"),
    ]
    for cre, slug in strict:
        if cre.search(head):
            return slug
    return None


def tag_patterns(blob: str) -> tuple[list[str], list[str]]:
    idea_hits = score_patterns(blob.lower(), IDEA_PATTERNS)
    jour_hits = score_patterns(blob.lower(), JOURNAL_PATTERNS)
    idea = [p for p, _ in idea_hits[:3]] or ["outside_taxonomy"]
    journal = [p for p, _ in jour_hits[:3]]
    return idea, journal

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # type: ignore

HEADING_RE = re.compile(
    r"(?m)^\s*(?:(\d+(?:\.\d+){0,3})|[IVXLC]+)\.?\s+([A-Z][A-Za-z0-9 ,\-/&()]{2,80})\s*$"
    r"|^\s*((?:Introduction|Related Work|Materials and Methods|Methods?|Methodology|"
    r"Proposed Method|Problem Formulation|Experimental Setup|Experiments?|Results?|"
    r"Discussion|Conclusions?|Conclusion|Case Study|Data Availability|References))\s*$",
    re.I,
)
FIG_RE = re.compile(r"(?im)^\s*Figure\s+(\d+[A-Za-z]?)\.?\s*[:.\-–—]?\s*(.{10,200})$")
TAB_RE = re.compile(r"(?im)^\s*Table\s+(\d+[A-Za-z]?)\.?\s*[:.\-–—]?\s*(.{10,200})$")
ALG_RE = re.compile(r"(?im)^\s*Algorithm\s+(\d+)\.?\s*[:.\-–—]?\s*(.{5,200})$")
EQ_RE = re.compile(r"(?m)^\s*\(\s*(\d+(?:\.\d+)*)\s*\)\s*$|Eq(?:uation)?\.?\s*\(?(\d+)\)?", re.I)

ROLE_MAP = [
    ("intro", re.compile(r"introduction|background", re.I)),
    ("related", re.compile(r"related\s+work|literature", re.I)),
    ("method", re.compile(r"method|model|framework|formulation|proposed|approach|materials", re.I)),
    ("experiments", re.compile(r"experiment|result|evaluation|case\s+study|simulation|numerical", re.I)),
    ("discussion", re.compile(r"discussion|limitation", re.I)),
    ("conclusion", re.compile(r"conclusion|summary|future\s+work", re.I)),
    ("data_avail", re.compile(r"data\s+availability|code\s+availability|supplementary", re.I)),
]


def extract_pages(pdf: Path, max_pages: int = 14) -> tuple[int, str]:
    try:
        r = PdfReader(str(pdf))
        n = len(r.pages)
        text = "\n".join((r.pages[i].extract_text() or "") for i in range(min(n, max_pages)))
        return n, text
    except Exception as e:
        return 0, f"ERROR:{e}"


def split_sections(text: str) -> list[dict]:
    # Drop bibliography tail
    cut = re.search(r"(?im)^\s*(?:References|Bibliography|Acknowledgments?)\s*$", text)
    body = text[: cut.start()] if cut else text
    matches = list(HEADING_RE.finditer(body))
    sections: list[dict] = []
    if not matches:
        return [{"id": "s0", "title": "Body", "level": 1, "text": body[:12000], "refs": {}}]
    for i, m in enumerate(matches):
        title = (m.group(2) or m.group(3) or "").strip()
        num = m.group(1) or ""
        level = num.count(".") + 1 if num else 1
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        if len(chunk) < 40 and not title:
            continue
        sid = f"s{i+1}"
        sections.append(
            {
                "id": sid,
                "title": (f"{num} {title}" if num else title)[:120],
                "level": level,
                "text": chunk[:8000],
                "refs": {"figures": [], "tables": [], "algorithms": [], "equations": []},
            }
        )
    return sections or [{"id": "s0", "title": "Body", "level": 1, "text": body[:12000], "refs": {}}]


def collect_multimodal(text: str) -> dict:
    figures = [{"id": f"f{m.group(1)}", "caption": m.group(2).strip()} for m in FIG_RE.finditer(text)]
    tables = [{"id": f"t{m.group(1)}", "caption": m.group(2).strip()} for m in TAB_RE.finditer(text)]
    algorithms = [{"id": f"a{m.group(1)}", "caption": m.group(2).strip()} for m in ALG_RE.finditer(text)]
    equations = []
    for m in EQ_RE.finditer(text):
        eid = m.group(1) or m.group(2)
        if eid:
            equations.append({"id": f"e{eid}", "latex_or_text": m.group(0).strip()[:80]})
    # dedupe by id keep first
    def dedupe(items):
        seen, out = set(), []
        for it in items:
            if it["id"] in seen:
                continue
            seen.add(it["id"])
            out.append(it)
        return out

    return {
        "figures": dedupe(figures)[:40],
        "tables": dedupe(tables)[:40],
        "algorithms": dedupe(algorithms)[:20],
        "equations": dedupe(equations)[:60],
    }


def attach_crossrefs(sections: list[dict], multi: dict) -> None:
    fig_ids = {x["id"] for x in multi["figures"]}
    tab_ids = {x["id"] for x in multi["tables"]}
    alg_ids = {x["id"] for x in multi["algorithms"]}
    for sec in sections:
        t = sec["text"]
        for fid in fig_ids:
            num = fid[1:]
            if re.search(rf"\b(?:Fig(?:ure)?\.?\s*{re.escape(num)})\b", t, re.I):
                sec["refs"]["figures"].append(fid)
        for tid in tab_ids:
            num = tid[1:]
            if re.search(rf"\b(?:Table\.?\s*{re.escape(num)})\b", t, re.I):
                sec["refs"]["tables"].append(tid)
        for aid in alg_ids:
            num = aid[1:]
            if re.search(rf"\b(?:Algorithm\.?\s*{re.escape(num)})\b", t, re.I):
                sec["refs"]["algorithms"].append(aid)


def section_roles(sections: list[dict]) -> dict[str, bool]:
    roles = {k: False for k, _ in ROLE_MAP}
    for sec in sections:
        title = sec["title"]
        for key, cre in ROLE_MAP:
            if cre.search(title):
                roles[key] = True
    return roles


def evidence_signals(text: str, sections: list[dict], roles: dict) -> dict:
    exp_text = "\n".join(s["text"] for s in sections if ROLE_MAP[3][1].search(s["title"]) or ROLE_MAP[2][1].search(s["title"]))
    scope = exp_text or text
    return {
        "has_baseline_table": bool(
            re.search(r"\b(baseline|compared\s+with|comparison\s+with|SOTA|state[- ]of[- ]the[- ]art)\b", scope, re.I)
        ),
        "has_ablation": bool(re.search(r"\bablation\b", scope, re.I)),
        "has_dataset_name": bool(
            re.search(
                r"\b(dataset|IEEE\s+\d+-bus|PJM|ISO[- ]NE|UCI|open[- ]?data|benchmark)\b",
                scope,
                re.I,
            )
        ),
        "has_data_availability": bool(
            re.search(r"\b(data\s+availability|available\s+upon\s+request|zenodo|figshare)\b", text, re.I)
        ),
        "has_code_availability": bool(
            re.search(r"\b(code\s+availability|github\.com|gitlab\.com|supplementary\s+code|source\s+code)\b", text, re.I)
        ),
        "section_roles": roles,
        "n_figures": 0,
        "n_tables": 0,
        "n_algorithms": 0,
        "n_equations": 0,
    }


def cpa_parse(pdf: Path) -> dict:
    n_pages, text = extract_pages(pdf)
    if text.startswith("ERROR:") or len(text) < 200:
        return {
            "source_pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
            "n_pages": n_pages,
            "sections": [],
            "figures": [],
            "tables": [],
            "algorithms": [],
            "equations": [],
            "signals": {"error": text[:200]},
            "tag_text": text[:5000],
        }
    sections = split_sections(text)
    multi = collect_multimodal(text)
    attach_crossrefs(sections, multi)
    roles = section_roles(sections)
    signals = evidence_signals(text, sections, roles)
    signals["n_figures"] = len(multi["figures"])
    signals["n_tables"] = len(multi["tables"])
    signals["n_algorithms"] = len(multi["algorithms"])
    signals["n_equations"] = len(multi["equations"])
    # Prefer method+experiments for IdeaSpark tagging (RepLLM cross-ref expansion idea)
    focus = []
    for sec in sections:
        if any(cre.search(sec["title"]) for _, cre in ROLE_MAP[2:4]):
            focus.append(sec["title"] + "\n" + sec["text"])
            # expand captions referenced
            for fid in sec["refs"].get("figures", []):
                cap = next((x["caption"] for x in multi["figures"] if x["id"] == fid), "")
                if cap:
                    focus.append(f"[Fig {fid}] {cap}")
            for tid in sec["refs"].get("tables", []):
                cap = next((x["caption"] for x in multi["tables"] if x["id"] == tid), "")
                if cap:
                    focus.append(f"[Table {tid}] {cap}")
    tag_text = "\n".join(focus) if focus else text
    return {
        "source_pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        "n_pages": n_pages,
        "sections": sections,
        "figures": multi["figures"],
        "tables": multi["tables"],
        "algorithms": multi["algorithms"],
        "equations": multi["equations"],
        "signals": signals,
        "tag_text": tag_text[:20000],
    }


def skill_block(slug: str, summary: dict) -> str:
    roles = summary["section_role_rates"]
    return "\n".join(
        [
            SECTION_HEADER,
            "",
            f"- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; "
            f"code at `D:/aicoding/mylib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).",
            f"- Sample: **n={summary['n']}** mapped local PDFs.",
            f"- Section presence rates: intro **{100*roles.get('intro',0):.0f}%**, method **{100*roles.get('method',0):.0f}%**, "
            f"experiments/results **{100*roles.get('experiments',0):.0f}%**, conclusion **{100*roles.get('conclusion',0):.0f}%**.",
            f"- Multimodal density (mean/paper): figures **{summary['mean_figures']:.1f}**, tables **{summary['mean_tables']:.1f}**, "
            f"algorithms **{summary['mean_algorithms']:.1f}**, equation markers **{summary['mean_equations']:.1f}**.",
            f"- CPA evidence signals: baseline cues **{100*summary['baseline_rate']:.0f}%**, ablation **{100*summary['ablation_rate']:.0f}%**, "
            f"dataset/benchmark **{100*summary['dataset_rate']:.0f}%**, data-availability **{100*summary['das_rate']:.0f}%**, "
            f"code-availability **{100*summary['code_rate']:.0f}%**.",
            f"- CPA-scoped IdeaSpark dominant move: `{summary['dominant_idea']}` · journal-house: `{summary['dominant_journal']}`.",
            "- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.",
            "",
        ]
    )


def patch_skill(slug: str, block: str) -> bool:
    path = SKILL_ROOT / slug / "SKILL.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if SECTION_HEADER in text:
        pre, rest = text.split(SECTION_HEADER, 1)
        # cut until next ### or ## at beginning of line after our block
        m = re.search(r"\n(?=### |\n## )", rest)
        if m:
            text = pre.rstrip() + "\n\n" + block + rest[m.start() + 1 :]
        else:
            text = pre.rstrip() + "\n\n" + block
    else:
        # insert after IdeaSpark section if present, else after Venue-specific calibration
        anchor = "### ResearchStudio-Idea acceptance patterns"
        if anchor in text:
            # append after that whole section: find next ### or ## following it
            idx = text.find(anchor)
            m = re.search(r"\n(?=### |\n## )", text[idx + len(anchor) :])
            if m:
                at = idx + len(anchor) + m.start()
                text = text[:at] + "\n" + block + text[at:]
            else:
                text = text.rstrip() + "\n\n" + block
        else:
            text = text.rstrip() + "\n\n" + block
    path.write_text(text, encoding="utf-8")
    return True


def main():
    OUT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    OUT_LIT.mkdir(parents=True, exist_ok=True)

    pdfs = discover_pdfs()
    print(f"discovered {len(pdfs)} PDFs", flush=True)

    by_slug: dict[str, list] = defaultdict(list)
    map_rows = []
    unmapped = 0

    for i, pdf in enumerate(pdfs, 1):
        paper = cpa_parse(pdf)
        # strip tag_text before disk write
        disk = {k: v for k, v in paper.items() if k != "tag_text"}
        slug_guess_path = None
        # write per-pdf json keyed by hash of relative path
        rel = str(pdf.relative_to(ROOT)).replace("\\", "/")
        key = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:16] + "_" + re.sub(r"[^a-zA-Z0-9]+", "_", pdf.stem)[:40]
        (OUT_JSON_DIR / f"{key}.json").write_text(json.dumps(disk, ensure_ascii=False, indent=2), encoding="utf-8")

        n_pages, head = paper["n_pages"], paper.get("tag_text") or ""
        # Prefer path + early PDF pages for venue cues (DOI often on page 1)
        _, page1 = extract_pages(pdf, max_pages=2)
        raw_for_slug = page1 + "\n" + ("\n".join(s.get("text", "")[:400] for s in paper.get("sections", [])[:2]) or head)
        slug = infer_slug(pdf, raw_for_slug)
        idea, journal = tag_patterns(head)
        if not slug:
            unmapped += 1
            map_rows.append({"pdf": rel, "slug": "", "idea": idea[0] if idea else "", "status": "unmapped"})
        else:
            row = {
                "pdf": rel,
                "slug": slug,
                "n_pages": n_pages,
                "idea": idea,
                "journal": journal,
                "signals": paper["signals"],
                "n_sections": len(paper["sections"]),
            }
            by_slug[slug].append(row)
            map_rows.append(
                {
                    "pdf": rel,
                    "slug": slug,
                    "idea": idea[0] if idea else "outside_taxonomy",
                    "status": "mapped",
                }
            )
        if i % 25 == 0:
            print(f"  …{i}/{len(pdfs)} mapped_slugs={len(by_slug)}", flush=True)

    print(f"mapped journals={len(by_slug)} unmapped={unmapped}", flush=True)

    all_json = {}
    notes = [
        "# RepLLM-CPA journal distill (full local corpus)",
        "",
        "Method: RepLLM Content Parsing only (arXiv:2509.21074). Full code-reproduction agents not run.",
        f"Lib: `D:/aicoding/mylib/RepLLM`. PDFs: `{LIT.as_posix()}`.",
        "",
    ]
    batch = [
        "# RepLLM-CPA structured evidence — journal index",
        "",
        "| slug | n | method% | experiments% | baseline% | ablation% | DAS% | code% | dominant_idea |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for slug in sorted(by_slug):
        rows = by_slug[slug]
        n = len(rows)
        idea_c = Counter((r["idea"][0] if r["idea"] else "outside_taxonomy") for r in rows)
        jour_c = Counter((r["journal"][0] if r["journal"] else "outside_taxonomy") for r in rows)
        role_sums = defaultdict(int)
        for r in rows:
            for k, v in (r["signals"].get("section_roles") or {}).items():
                if v:
                    role_sums[k] += 1
        summary = {
            "n": n,
            "dominant_idea": idea_c.most_common(1)[0][0],
            "dominant_journal": jour_c.most_common(1)[0][0],
            "baseline_rate": sum(1 for r in rows if r["signals"].get("has_baseline_table")) / n,
            "ablation_rate": sum(1 for r in rows if r["signals"].get("has_ablation")) / n,
            "dataset_rate": sum(1 for r in rows if r["signals"].get("has_dataset_name")) / n,
            "das_rate": sum(1 for r in rows if r["signals"].get("has_data_availability")) / n,
            "code_rate": sum(1 for r in rows if r["signals"].get("has_code_availability")) / n,
            "mean_figures": sum(r["signals"].get("n_figures", 0) for r in rows) / n,
            "mean_tables": sum(r["signals"].get("n_tables", 0) for r in rows) / n,
            "mean_algorithms": sum(r["signals"].get("n_algorithms", 0) for r in rows) / n,
            "mean_equations": sum(r["signals"].get("n_equations", 0) for r in rows) / n,
            "section_role_rates": {k: role_sums[k] / n for k in ("intro", "method", "experiments", "conclusion")},
            "idea_dist": dict(idea_c),
            "journal_dist": dict(jour_c),
        }
        # lit table
        lit_lines = [
            f"# CPA lit_table — `{slug}`",
            "",
            "`pdf` | pages | sections | figs/tabs/algs | idea | house | baseline | ablation | DAS | code",
            "---|---:|---:|---|---|---|:---:|:---:|:---:|:---:",
        ]
        for r in rows:
            sig = r["signals"]
            lit_lines.append(
                f"`{Path(r['pdf']).name}` | {r['n_pages']} | {r['n_sections']} | "
                f"{sig.get('n_figures',0)}/{sig.get('n_tables',0)}/{sig.get('n_algorithms',0)} | "
                f"{','.join(r['idea'][:2]) or '-'} | {','.join(r['journal'][:2]) or '-'} | "
                f"{'Y' if sig.get('has_baseline_table') else 'n'} | "
                f"{'Y' if sig.get('has_ablation') else 'n'} | "
                f"{'Y' if sig.get('has_data_availability') else 'n'} | "
                f"{'Y' if sig.get('has_code_availability') else 'n'}"
            )
        (OUT_LIT / f"{slug}_lit_table.md").write_text("\n".join(lit_lines) + "\n", encoding="utf-8")

        block = skill_block(slug, summary)
        patched = patch_skill(slug, block)
        print(f"=== {slug} n={n} patched={patched} ===", flush=True)
        all_json[slug] = summary
        notes.append(f"## {slug}\n\n{block}")
        batch.append(
            f"| `{slug}` | {n} | {100*summary['section_role_rates'].get('method',0):.0f}% | "
            f"{100*summary['section_role_rates'].get('experiments',0):.0f}% | "
            f"{100*summary['baseline_rate']:.0f}% | {100*summary['ablation_rate']:.0f}% | "
            f"{100*summary['das_rate']:.0f}% | {100*summary['code_rate']:.0f}% | `{summary['dominant_idea']}` |"
        )

    notes.append(f"## unmapped\n\nn={unmapped}\n")
    OUT_NOTES.write_text("\n".join(notes), encoding="utf-8")
    OUT_SUMMARY.write_text(json.dumps(all_json, ensure_ascii=False, indent=2), encoding="utf-8")
    BATCH_MD.write_text("\n".join(batch) + "\n", encoding="utf-8")

    # index pointer in Paper_CCF
    skill_idx = Path.home() / ".claude/skills/Paper_CCF/SKILL.md"
    if skill_idx.exists():
        t = skill_idx.read_text(encoding="utf-8")
        needle = "**RepLLM-CPA 结构化证据蒸馏**"
        line = (
            "8. **RepLLM-CPA 结构化证据蒸馏**（Content Parsing → `paper.json`，非代码复现）→ "
            "`resources/repllm-cpa-journal-distill.md`；各刊 `SKILL.md` 内 "
            "`### RepLLM-CPA structured evidence`。详见 `D:/aicoding/mylib/RepLLM/`。\n"
        )
        if needle not in t:
            # insert after ideaspark item if present
            if "ideaspark-fullcorpus-journal-distill.md" in t:
                t = t.replace(
                    "ideaspark-fullcorpus-journal-distill.md`。细表/卡片在仓库 `papers/literature/target_journal_related/metadata/ideaspark_fullcorpus_*`。\n",
                    "ideaspark-fullcorpus-journal-distill.md`。细表/卡片在仓库 `papers/literature/target_journal_related/metadata/ideaspark_fullcorpus_*`。\n"
                    + line,
                )
            else:
                t = t.rstrip() + "\n\n" + line
            skill_idx.write_text(t, encoding="utf-8")

    res_readme = Path.home() / ".claude/skills/Paper_CCF/resources/README.md"
    if res_readme.exists():
        rt = res_readme.read_text(encoding="utf-8")
        if "repllm-cpa-journal-distill.md" not in rt:
            rt = rt.rstrip() + (
                "\n- `repllm-cpa-journal-distill.md` — RepLLM Content-Parsing (CPA) evidence "
                "geometry over the full local PDF corpus; per-paper `paper.json` under "
                "`powergrid_benchmark/.../metadata/repllm_cpa_paper_json/`.\n"
            )
            res_readme.write_text(rt, encoding="utf-8")

    print("wrote", OUT_NOTES, flush=True)
    print("wrote", OUT_SUMMARY, flush=True)
    print("wrote", BATCH_MD, flush=True)
    print("paper.json count", len(list(OUT_JSON_DIR.glob("*.json"))), flush=True)


if __name__ == "__main__":
    main()
