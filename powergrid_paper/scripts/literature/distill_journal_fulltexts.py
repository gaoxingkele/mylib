# -*- coding: utf-8 -*-
"""Distill review/style patterns from journal full-text PDFs into Paper_CCF skills."""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
SKILL_ROOT = Path.home() / ".claude/skills/Paper_CCF/journals"
DISTILL_MD = Path.home() / ".claude/skills/Paper_CCF/resources/target-journals-2026-batch-distill.md"
OUT_NOTES = META / "journal_fulltext_distill_notes.md"

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader  # type: ignore

POWER_RE = re.compile(
    r"\b(power|grid|electric|energy|battery|bess|photovoltaic|wind|load forecast|"
    r"smart.?grid|opf|dispatch|transformer|substation|renewable)\b",
    re.I,
)
ALGO_RE = re.compile(
    r"\b(algorithm|neural|deep learning|machine learning|optimization|cnn|lstm|"
    r"transformer|xgboost|reinforcement|graph neural|forecast)\b",
    re.I,
)


def extract(pdf: Path, max_pages: int = 5) -> dict:
    try:
        r = PdfReader(str(pdf))
        pages = min(len(r.pages), max_pages)
        text = "\n".join((r.pages[i].extract_text() or "") for i in range(pages))
        n_pages = len(r.pages)
    except Exception as e:
        return {"file": pdf.name, "error": str(e)}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = ""
    for ln in lines[:20]:
        if len(ln) > 25 and not ln.lower().startswith("this work is licensed"):
            if "doi" in ln.lower() or "creativecommons" in ln.lower():
                continue
            title = ln[:200]
            break
    kw = ""
    m = re.search(r"Keywords?\s*[:：]\s*(.+)", text, re.I)
    if m:
        kw = re.sub(r"\s+", " ", m.group(1))[:240]
    abstract = ""
    m2 = re.search(
        r"Abstract\s*[:：]?\s*(.{120,1500}?)(?:\n\s*Keywords|\n\s*1[\.\s]|Introduction)",
        text,
        re.I | re.S,
    )
    if m2:
        abstract = re.sub(r"\s+", " ", m2.group(1))[:700]
    blob = (title + " " + kw + " " + abstract + " " + " ".join(lines[:40])).lower()
    return {
        "file": pdf.name,
        "pages": n_pages,
        "title": title,
        "keywords": kw,
        "abstract": abstract,
        "power_hit": bool(POWER_RE.search(blob)),
        "algo_hit": bool(ALGO_RE.search(blob)),
        "has_baseline_word": bool(re.search(r"baseline|compared with|comparison", blob)),
        "has_ablation_word": bool(re.search(r"ablation|sensitivity", blob)),
        "has_dataset_word": bool(re.search(r"dataset|data set|benchmark|ieee\s*\d+", blob)),
        "error": "",
    }


def patterns_for(records: list[dict]) -> str:
    ok = [r for r in records if not r.get("error")]
    if not ok:
        return "_No readable PDFs._\n"
    n = len(ok)
    pages = [r["pages"] for r in ok if r.get("pages")]
    avg_p = sum(pages) / len(pages) if pages else 0
    power_n = sum(1 for r in ok if r["power_hit"])
    algo_n = sum(1 for r in ok if r["algo_hit"])
    base_n = sum(1 for r in ok if r["has_baseline_word"])
    abl_n = sum(1 for r in ok if r["has_ablation_word"])
    data_n = sum(1 for r in ok if r["has_dataset_word"])
    lines = [
        f"- Full-text sample: **n={n}** (avg ~{avg_p:.0f} pages in first-pass extract).",
        f"- Topic mix in sample: power/energy-related ≈ {power_n}/{n}; algorithm/ML ≈ {algo_n}/{n}.",
        f"- Lexical signals (first pages): baseline/comparison ≈ {base_n}/{n}; "
        f"ablation/sensitivity ≈ {abl_n}/{n}; dataset/benchmark ≈ {data_n}/{n}.",
        "- Observed acceptance-style cues from titles/keywords/abstracts:",
    ]
    # list up to 5 titles
    for r in ok[:8]:
        tag = []
        if r["power_hit"]:
            tag.append("power")
        if r["algo_hit"]:
            tag.append("algo")
        t = r["title"] or r["file"]
        lines.append(f"  - [{','.join(tag) or 'other'}] {t[:110]}")
    lines.append(
        "- Practical bar inferred: complete method stack + quantitative comparison; "
        "incremental named combinations common; claims should match reported metrics."
    )
    return "\n".join(lines) + "\n"


SECTION_HEADER = "### Distilled full-text patterns (local corpus, 2026-08)"


def patch_skill(slug: str, block: str) -> bool:
    path = SKILL_ROOT / slug / "SKILL.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_sec = f"{SECTION_HEADER}\n\n{block}\nCorpus path: `papers/literature/target_journal_related/fulltext_by_journal/{slug}/`.\n"
    if SECTION_HEADER in text:
        # replace existing section until next ## or ###
        text = re.sub(
            rf"{re.escape(SECTION_HEADER)}.*?(?=\n## |\n### [^D]|\Z)",
            new_sec + "\n",
            text,
            count=1,
            flags=re.S,
        )
    elif "### Distilled patterns" in text:
        text = text.replace("### Distilled patterns", new_sec + "\n### Distilled patterns (prior notes)", 1)
    else:
        # insert before ## APC or ## Review or ## Official
        m = re.search(r"\n## (APC|Review|Official|Common desk)", text)
        if m:
            i = m.start()
            text = text[:i] + "\n" + new_sec + text[i:]
        else:
            text = text.rstrip() + "\n\n" + new_sec
    path.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    META.mkdir(parents=True, exist_ok=True)
    by_slug: dict[str, list[dict]] = {}
    for d in sorted(PDF_ROOT.glob("*")):
        if not d.is_dir():
            continue
        recs = []
        for pdf in sorted(d.glob("*.pdf"))[:12]:
            print("extract", d.name, pdf.name[:50])
            recs.append(extract(pdf))
        by_slug[d.name] = recs

    md_parts = ["# Journal full-text distill notes (2026-08)\n", f"Root: `{PDF_ROOT}`\n"]
    summary_rows = []
    for slug, recs in by_slug.items():
        ok = [r for r in recs if not r.get("error")]
        block = patterns_for(recs)
        md_parts.append(f"## {slug}\n\n{block}")
        patched = patch_skill(slug, block)
        summary_rows.append({"slug": slug, "n_pdf": len(ok), "skill_patched": patched})
        print(f"patched {slug}: {patched} n={len(ok)}")

    OUT_NOTES.write_text("\n".join(md_parts), encoding="utf-8")

    # refresh batch distill md overview
    overview = [
        "# Target-journal batch distill notes (2026-08)\n",
        "Full-text PDFs under `powergrid_benchmark/papers/literature/target_journal_related/fulltext_by_journal/<slug>/`.\n",
        "Per-journal extraction notes: `metadata/journal_fulltext_distill_notes.md`.\n",
        "Each `journals/<slug>/SKILL.md` contains a **Distilled full-text patterns** section.\n",
        "\n## Counts\n",
        "| slug | n_pdf | skill_patched |",
        "|---|---:|:---:|",
    ]
    for r in summary_rows:
        overview.append(f"| `{r['slug']}` | {r['n_pdf']} | {r['skill_patched']} |")
    overview.append(
        "\n**Note:** Publisher stampPDF hosts (MDPI/IEEE/Elsevier/Wiley) often 403 in this environment; "
        "downloads prefer arXiv / PMC / institutional / PeerJ / Nature OA mirrors of the same works.\n"
    )
    DISTILL_MD.write_text("\n".join(overview), encoding="utf-8")
    print("wrote", OUT_NOTES)
    print("wrote", DISTILL_MD)


if __name__ == "__main__":
    main()
