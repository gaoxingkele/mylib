"""Manuscript display, page-budget and packaging audit.

Distilled from the MA-SQLGrid Information upgrade (2026-09): the failure modes
that actually cost a review round were (a) figures relocated during a length
reduction and then lost, (b) a rendered supplement drifting from its shipped
markdown source, and (c) page-count decisions made without measuring how full
the final page already was.

This script answers, deterministically and from the compiled artifact:

  * pages, overfull boxes, undefined references/citations (parsed from the log)
  * how full the final page is, so "will adding one figure cost a page?" is arithmetic
  * the figure/table inventory, unreferenced float labels, and references with no target
  * orphan image files: shipped but referenced nowhere
  * sha256 of tex/pdf/docx and of the delivery archives
  * whether the shipped supplement markdown is byte-identical to its build source

Usage (all paths relative to --project unless absolute):

    python -B manuscript_display_audit.py --project <paper_dir> \
        --tex paper_information.tex --log paper_information.log \
        --figure-root figures --supplement-zip ../supp.zip \
        --supplement-source build_supplementary/_source.md \
        --json audit.json

Exit code 0 when no check fails; 1 otherwise (use --allow-warn to never fail).
Only the Python standard library is required; pypdf enables the page-fill check
and is otherwise skipped with a warning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

FLOAT_RE = re.compile(r"\\begin\{(figure|table)\*?\}(.*?)\\end\{\1\*?\}", re.S)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
REF_RE = re.compile(r"\\(?:ref|autoref|eqref|Cref|cref)\{([^}]+)\}")
INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
PAGES_RE = re.compile(r"Output written on .*?\((\d+) pages")
IMAGE_SUFFIXES = {".pdf", ".png", ".svg", ".jpg", ".jpeg", ".eps"}
BOX_BOTTOM_PT = 60.0  # MDPI text block bottom margin, used only for a headroom estimate
NAME_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.(?:pdf|png|svg|jpe?g|eps))", re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def strip_comments(tex: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", tex)


def audit_floats(tex: str) -> dict:
    floats = []
    for index, match in enumerate(FLOAT_RE.finditer(tex), 1):
        kind, body = match.group(1), match.group(2)
        label = LABEL_RE.search(body)
        caption = re.search(r"\\caption\{(.{0,160})", body, re.S)
        floats.append(
            {
                "kind": kind,
                "order": index,
                "label": label.group(1) if label else None,
                "caption": re.sub(r"\s+", " ", caption.group(1)).strip() if caption else None,
                "references_figure": bool(INCLUDE_RE.search(body)),
            }
        )
    counts = {kind: sum(1 for f in floats if f["kind"] == kind) for kind in ("figure", "table")}
    labels_in_floats = {f["label"] for f in floats if f["label"]}
    all_labels = set(LABEL_RE.findall(tex))
    refs = set()
    for group in REF_RE.findall(tex):
        refs.update(part.strip() for part in group.split(","))
    return {
        "counts": counts,
        "floats": floats,
        "unreferenced_float_labels": sorted(labels_in_floats - refs),
        "references_without_target": sorted(refs - all_labels),
    }


def resolve_graphics(tex_dir: Path, targets: list[str]) -> list[dict]:
    resolved = []
    for raw in targets:
        candidate = (tex_dir / raw).resolve()
        found = None
        for option in (candidate, *(candidate.with_suffix(s) for s in sorted(IMAGE_SUFFIXES))):
            if option.is_file():
                found = option
                break
        resolved.append(
            {
                "reference": raw,
                "path": str(found) if found else None,
                "exists": found is not None,
                "sha256": sha256(found) if found else None,
            }
        )
    return resolved


def audit_orphans(figure_root: Path, sources: list[str]) -> dict:
    haystack = "\n".join(sources)
    images = sorted(
        p for p in figure_root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    # A figure is referenced when any file with the same stem is named anywhere:
    # SVG/PNG/PDF renderings of one figure share a stem, so naming the PDF covers them.
    referenced_stems = {Path(token.replace("\\", "/")).stem for token in NAME_RE.findall(haystack)}
    orphans = [p.as_posix() for p in images if p.stem not in referenced_stems]
    return {
        "image_files": len(images),
        "referenced_stems": len(referenced_stems),
        "orphans": orphans,
    }


def audit_log(log: Path) -> dict:
    if not log.is_file():
        return {"available": False}
    text = log.read_text(encoding="utf-8", errors="replace")
    pages = PAGES_RE.findall(text)
    return {
        "available": True,
        "pages": int(pages[-1]) if pages else None,
        "overfull": len(re.findall(r"Overfull \\hbox", text)),
        "undefined_references": len(re.findall(r"LaTeX Warning: Reference", text)),
        "undefined_citations": len(re.findall(r"LaTeX Warning: Citation", text)),
        "errors": len(re.findall(r"^! ", text, re.M)),
    }


def audit_last_page(pdf: Path) -> dict:
    try:
        import pypdf
    except ImportError:  # pragma: no cover - environment dependent
        return {"available": False, "reason": "pypdf not installed"}
    if not pdf.is_file():
        return {"available": False, "reason": "pdf missing"}
    reader = pypdf.PdfReader(str(pdf))
    last = reader.pages[-1]
    baselines: list[float] = []
    last.extract_text(
        visitor_text=lambda t, cm, tm, fd, fs: baselines.append(float(tm[5]))
        if t and t.strip()
        else None
    )
    real = sorted(y for y in baselines if y > 30)
    if not real:
        return {"available": False, "reason": "no text on last page"}
    return {
        "available": True,
        "pages": len(reader.pages),
        "last_page_lowest_baseline_pt": round(real[0], 1),
        "last_page_top_baseline_pt": round(real[-1], 1),
        "headroom_pt": round(real[0] - BOX_BOTTOM_PT, 1),
        "full_page": real[0] - BOX_BOTTOM_PT < 12.0,
    }


def audit_supplement(zip_path: Path | None, source_md: Path | None) -> dict:
    if zip_path is None or source_md is None:
        return {"checked": False}
    result: dict = {"checked": True, "zip": str(zip_path), "source": str(source_md)}
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        result["files"] = len(names)
        shipped_md = next((n for n in names if n.endswith("Supplementary_Materials.md")), None)
        if shipped_md:
            shipped = zf.read(shipped_md)
            result["shipped_md"] = shipped_md
            result["md_matches_source"] = shipped == source_md.read_bytes()
            result["md_bytes"] = len(shipped)
        manifest = next((n for n in names if n.endswith("SUPPLEMENT_MANIFEST.json")), None)
        if manifest:
            declared = {rec["path"] for rec in json.loads(zf.read(manifest))["files"]}
            actual = {n for n in names if not n.endswith("/")}
            result["declared_minus_actual"] = sorted(declared - actual)
            result["actual_minus_declared"] = sorted(
                actual - declared - {manifest, "SHA256SUMS.txt"}
            )
    return result


def build_report(args: argparse.Namespace) -> dict:
    project = Path(args.project).resolve()
    tex_path = (project / args.tex) if not Path(args.tex).is_absolute() else Path(args.tex)
    tex = strip_comments(tex_path.read_text(encoding="utf-8"))
    supplement_sources = []
    for extra in args.supplement_text or []:
        candidate = (project / extra) if not Path(extra).is_absolute() else Path(extra)
        if candidate.is_file():
            supplement_sources.append(candidate.read_text(encoding="utf-8", errors="replace"))

    log_path = (project / args.log) if args.log else tex_path.with_suffix(".log")
    pdf_path = tex_path.with_suffix(".pdf")
    docx_path = tex_path.with_suffix(".docx")
    figure_root = (project / args.figure_root) if args.figure_root else project / "figures"

    floats = audit_floats(tex)
    graphics = resolve_graphics(tex_path.parent, INCLUDE_RE.findall(tex))
    report = {
        "project": str(project),
        "tex": str(tex_path),
        "floats": floats,
        "graphics": graphics,
        "missing_graphics": [g["reference"] for g in graphics if not g["exists"]],
        "log": audit_log(log_path),
        "last_page": audit_last_page(pdf_path),
        "supplement": audit_supplement(
            Path(args.supplement_zip) if args.supplement_zip else None,
            Path(args.supplement_source) if args.supplement_source else None,
        ),
        "identities": {},
    }
    if figure_root.is_dir():
        report["orphans"] = audit_orphans(
            figure_root, [tex, *supplement_sources, *[g["reference"] for g in graphics]]
        )
    for path in (tex_path, pdf_path, docx_path):
        if path.is_file():
            report["identities"][path.name] = {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
    return report


def failures(report: dict) -> list[str]:
    problems = []
    log = report["log"]
    if log.get("available"):
        for key, label in (
            ("errors", "compile errors"),
            ("overfull", "overfull boxes"),
            ("undefined_references", "undefined references"),
            ("undefined_citations", "undefined citations"),
        ):
            if log.get(key):
                problems.append(f"{label}: {log[key]}")
    if report["missing_graphics"]:
        problems.append(f"missing graphics: {report['missing_graphics'][:5]}")
    if report["floats"]["references_without_target"]:
        problems.append(f"refs without target: {report['floats']['references_without_target'][:5]}")
    if report["floats"]["unreferenced_float_labels"]:
        problems.append(f"float labels never referenced: {report['floats']['unreferenced_float_labels'][:5]}")
    if report.get("orphans", {}).get("orphans"):
        problems.append(f"orphan image files: {report['orphans']['orphans'][:5]}")
    supplement = report["supplement"]
    if supplement.get("checked") and supplement.get("md_matches_source") is False:
        problems.append("supplement markdown differs from its build source")
    if supplement.get("checked") and supplement.get("actual_minus_declared"):
        problems.append(f"undeclared supplement files: {supplement['actual_minus_declared'][:5]}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--tex", default="paper.tex")
    parser.add_argument("--log", default=None)
    parser.add_argument("--figure-root", default="figures")
    parser.add_argument("--supplement-zip", default=None)
    parser.add_argument("--supplement-source", default=None)
    parser.add_argument("--supplement-text", nargs="*", default=None,
                        help="extra text sources (e.g. a supplement .tex) scanned for figure references")
    parser.add_argument("--json", default=None, help="write the full report to this path")
    parser.add_argument("--allow-warn", action="store_true", help="always exit 0")
    args = parser.parse_args()

    report = build_report(args)
    problems = failures(report)
    report["problems"] = problems

    floats = report["floats"]
    log = report["log"]
    last = report["last_page"]
    print(f"project      : {report['project']}")
    print(f"floats       : {floats['counts']['figure']} figures, {floats['counts']['table']} tables")
    if log.get("available"):
        print(f"compile      : {log.get('pages')} pages, {log['overfull']} overfull, "
              f"{log['errors']} errors, {log['undefined_references']} undefined refs")
    if last.get("available"):
        print(f"last page    : lowest baseline {last['last_page_lowest_baseline_pt']} pt "
              f"(headroom {last['headroom_pt']} pt{', page is full' if last['full_page'] else ''})")
    if report.get("orphans"):
        print(f"images       : {report['orphans']['image_files']} files, "
              f"{len(report['orphans']['orphans'])} orphaned")
    if report["supplement"].get("checked"):
        print(f"supplement   : md matches source = {report['supplement'].get('md_matches_source')}")
    print(f"identities   : {', '.join(sorted(report['identities']))}")
    print("problems     :", "none" if not problems else "")
    for problem in problems:
        print(f"  - {problem}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"report written: {args.json}")
    if problems and not args.allow_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
