"""Submission consistency audit: mechanical desk-reject risks in an MDPI-style LaTeX manuscript.

Distilled from the 2026-10 Information desk rejections of C2GES and MA-SQLGrid
(see ../digests/information-desk-reject-postmortem-2026-11.md). Both manuscripts carried
defects that an editorial office can see without reading the science:

  * main text cites supplementary tables that the supplement does not contain (C2GES: S27-S29)
  * the manuscript cites a supplement, dataset or archive directory that the package lacks (MA-SQLGrid)
  * back matter still says "pending" / "awaits confirmation" (C2GES)
  * no AI-use declaration, although MDPI requires one when generative AI was used
  * core evidence offered only "upon request"
  * an abstract crowded with numbers (an orientation indicator, not a threshold)

Validation (2026-11-02): on the two rejected sources it reports C2GES 2 FAIL (5 pending
markers; Tables S27-S29 undefined) and MA-SQLGrid 2 FAIL (9 cited paths absent; no
supplement in the package), plus the AI-declaration WARN for both. Cited external repo
names (e.g. bird-bench/mini_dev) can appear as absent paths; review the list by hand.

This script reports those items deterministically from the source. It does NOT judge
the science: cross-layer consistency, story coherence and claim support stay manual
(see the postmortem digest, gates D3-D8).

Usage:

    python -B submission_consistency_audit.py --tex paper.tex \
        [--supplement supplementary.tex] [--package Information_submission.zip | --package <dir>] \
        [--abstract-number-warn 10] [--json out.json]

Exit code: 1 if any FAIL, else 0 (use --allow-fail to always exit 0).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

BS = "\\"

BACK_MATTER = ["authorcontributions", "funding", "institutionalreview", "informedconsent",
               "dataavailability", "conflictsofinterest"]

PENDING_RE = re.compile(
    r"pending|await(?:s|ing)?\s+(?:author\s+)?confirmation|to be confirmed|\bTBD\b|\bTODO\b|"
    r"\bXXX\b|待确认|待补|待核实", re.I)
AI_DECL_RE = re.compile(
    r"During the preparation of this (?:manuscript|work)|generative (?:AI|artificial intelligence)|"
    r"(?:ChatGPT|GPT-\d|Claude|Gemini|Codex|Copilot|DeepSeek|large language model)[^.]{0,120}"
    r"(?:used|assist|edit|draft|polish|writ)", re.I)
UPON_REQUEST_RE = re.compile(r"(?:available|provided)\s+(?:from\s+the\s+\w+\s+author\s+)?(?:up)?on\s+(?:reasonable\s+)?request", re.I)
SUPP_REF_RE = re.compile(r"(Tables?|Figures?|Figs?\.)\s*(?:~|\s)*S(\d+)(?:\s*(?:--|-|–|to)\s*S?(\d+))?")
SUPP_SECTION_REF_RE = re.compile(r"Supplementary\s+(?:Sections?|Materials?|Tables?|Figures?|Information)|Minimal Dataset", re.I)
SUPP_DEF_RE = re.compile(r"(Table|Figure)\s+S(\d+)[.:\s]")
PATH_RE = re.compile(r"\\(?:nolinkurl|path|url)\{([^}]+)\}")


def read_tex(path: Path, seen: set[Path] | None = None) -> str:
    """Read a tex file and inline \\input/\\include targets that exist next to it."""
    seen = seen or set()
    path = path.resolve()
    if path in seen or not path.exists():
        return ""
    seen.add(path)
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    text = re.sub(r"(?<!\\)%.*", "", text)  # drop comments

    def repl(m: re.Match) -> str:
        name = m.group(1)
        cand = path.parent / (name if name.endswith(".tex") else name + ".tex")
        return read_tex(cand, seen) if cand.exists() else m.group(0)

    return re.sub(r"\\(?:input|include)\{([^}]+)\}", repl, text)


def macro_body(text: str, name: str) -> str | None:
    """Return the brace-balanced argument of \\name{...}, or None."""
    i = text.find(BS + name + "{")
    if i < 0:
        return None
    j = i + len(name) + 2
    depth, k = 1, j
    while k < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        k += 1
    return text[j:k - 1]


def words(s: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", re.sub(r"\\[a-zA-Z]+", " ", s)))


def package_names(pkg: Path) -> list[str]:
    if pkg.is_dir():
        return [p.relative_to(pkg).as_posix() for p in pkg.rglob("*")]
    with zipfile.ZipFile(pkg) as z:
        return z.namelist()


def audit(args) -> list[dict]:
    res: list[dict] = []

    def add(check, status, detail, evidence=None):
        res.append({"check": check, "status": status, "detail": detail, "evidence": evidence or []})

    tex_path = Path(args.tex)
    text = read_tex(tex_path)
    if not text:
        add("read", "FAIL", f"cannot read {tex_path}")
        return res
    doc = text[text.find(BS + "begin{document}"):] if BS + "begin{document}" in text else text

    # 1. back-matter completeness and pending markers
    missing = [m for m in BACK_MATTER if macro_body(text, m) is None]
    add("back_matter_present", "FAIL" if missing else "PASS",
        "missing: " + ", ".join(missing) if missing else "all MDPI back-matter statements present")
    pend = []
    for name in BACK_MATTER + ["Author", "address", "corres", "firstnote", "acknowledgments"]:
        body = macro_body(text, name) or ""
        for m in PENDING_RE.finditer(body):
            pend.append(f"\\{name}: ...{body[max(0, m.start()-60):m.end()+40].strip()}...")
    add("no_pending_markers", "FAIL" if pend else "PASS",
        f"{len(pend)} pending/unconfirmed marker(s) in front/back matter" if pend else "none", pend)

    # 2. AI-use declaration
    ai_hit = AI_DECL_RE.search(doc)
    add("ai_use_declaration", "PASS" if ai_hit else "WARN",
        "declaration-like sentence found" if ai_hit else
        "no AI-use declaration found; MDPI requires one if generative AI was used (author must decide)",
        [doc[max(0, ai_hit.start()-40):ai_hit.end()+60]] if ai_hit else [])

    # 3. data availability 'upon request'
    da = macro_body(text, "dataavailability") or ""
    ur = UPON_REQUEST_RE.search(da)
    add("data_not_only_on_request", "WARN" if ur else "PASS",
        "data availability offers material only on request; check that it is not the core evidence"
        if ur else "no 'upon request' wording", [da[max(0, ur.start()-120):ur.end()]] if ur else [])

    # 4. supplementary references resolve
    cited: set[str] = set()
    for m in SUPP_REF_RE.finditer(doc):
        kind = "Figure" if m.group(1).lower().startswith("fig") else "Table"
        a = int(m.group(2)); b = int(m.group(3)) if m.group(3) else a
        for n in range(a, min(b, a + 60) + 1):
            cited.add(f"{kind} S{n}")
    cites_supp = bool(cited) or bool(SUPP_SECTION_REF_RE.search(doc))
    if args.supplement:
        stext = read_tex(Path(args.supplement))
        defined = {f"{k} S{n}" for k, n in SUPP_DEF_RE.findall(stext)}
        dangling = sorted(cited - defined, key=lambda s: (s.split()[0], int(s.split("S")[-1])))
        add("supplement_refs_resolve", "FAIL" if dangling else "PASS",
            f"{len(dangling)} cited item(s) not defined in the supplement (defined: {len(defined)})"
            if dangling else f"all {len(cited)} cited supplementary items are defined", dangling)
    elif cites_supp:
        add("supplement_provided", "WARN",
            f"main text cites supplementary material ({len(cited)} numbered item(s)) but no --supplement "
            "was given; confirm the supplement is in the upload",
            sorted(cited, key=lambda s: (s.split()[0], int(s.split("S")[-1])))[:20])

    # 5. cited paths exist in the package
    paths = sorted({p for p in PATH_RE.findall(doc) if "/" in p and "@" not in p and "://" not in p})
    if args.package:
        names = package_names(Path(args.package))
        absent = [p for p in paths if not any(n.startswith(p.strip("/")) for n in names)]
        add("cited_paths_in_package", "FAIL" if absent else "PASS",
            f"{len(absent)} cited path(s) absent from the package" if absent else
            f"all {len(paths)} cited path(s) present", absent)
        if cites_supp and not any(re.search(r"supp|minimal|dataset|S\d", n, re.I) for n in names):
            add("supplement_in_package", "FAIL",
                "text cites supplementary material / datasets but the package contains no such file",
                names[:30])
    elif paths:
        add("cited_paths_in_package", "WARN", "paths cited; pass --package to verify they ship", paths)

    # 6. abstract indicators (orientation only)
    ab = macro_body(text, "abstract") or ""
    aw = words(ab)
    an = len(re.findall(r"(?<![A-Za-z])\d+(?:[.,]\d+)*", re.sub(r"\\[a-zA-Z]+", " ", ab)))
    add("abstract_numbers", "WARN" if an > args.abstract_number_warn else "PASS",
        f"{aw} words, {an} numbers ({(an / aw * 100) if aw else 0:.1f} per 100 words); "
        f"indicator only, warn above {args.abstract_number_warn}")

    # 7. hedge density (orientation only)
    body_words = words(doc)
    nots = len(re.findall(r"\bnot\b|\bcannot\b|n't\b", doc))
    add("hedge_density", "INFO",
        f"'not/cannot' {nots} times in ~{body_words} words ({nots / max(body_words, 1) * 1000:.1f} per 1000); "
        "high values flag defensive audit-style prose, not an error")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tex", required=True)
    ap.add_argument("--supplement")
    ap.add_argument("--package", help="submission zip or directory")
    ap.add_argument("--abstract-number-warn", type=int, default=10)
    ap.add_argument("--json")
    ap.add_argument("--allow-fail", action="store_true")
    args = ap.parse_args(argv)
    res = audit(args)
    for r in res:
        print(f"[{r['status']:4}] {r['check']}: {r['detail']}")
        for e in r["evidence"][:8]:
            print(f"         - {e}")
    if args.json:
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    fails = sum(r["status"] == "FAIL" for r in res)
    print(f"\n{fails} FAIL, {sum(r['status'] == 'WARN' for r in res)} WARN")
    return 0 if (args.allow_fail or not fails) else 1


if __name__ == "__main__":
    sys.exit(main())
