# -*- coding: utf-8 -*-
"""Supplement MDPI Applied Sciences power-grid papers (2023–2026).

Uses Crossref journal works + aria2c/proxy MDPI PDF URLs.
Writes into papers/literature/applied_sciences_power_grid_recent/.
"""
from __future__ import annotations

import csv
import json
import re
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "papers/literature/applied_sciences_power_grid_recent"
PDF_DIR = OUT / "pdf"
META_DIR = OUT / "metadata"
EXISTING_PDF_DIRS = [
    ROOT / "papers/literature/applied_sciences_power_ai_10/pdf",
    PDF_DIR,
]
PROXY = "http://127.0.0.1:17890"
ARIA2 = Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
MAILTO = "powergrid.literature@gmail.com"
ISSN = "2076-3417"
TARGET_NEW = 18  # additional downloads beyond already-local

QUERIES = [
    '"power system"',
    '"power grid"',
    '"smart grid"',
    '"distribution network"',
    "microgrid",
    '"load forecasting"',
    '"unit commitment"',
    '"economic dispatch"',
    '"optimal power flow"',
    '"active distribution"',
]

# Title must match at least one strong power-grid cue.
RELEVANT = re.compile(
    r"(?i)("
    r"power\s+system|power\s+grid|smart\s+grid|electric\s+grid|"
    r"distribution\s+network|transmission\s+network|active\s+distribution|"
    r"microgrid|unit\s+commitment|economic\s+dispatch|optimal\s+power\s+flow|"
    r"load\s+forecast|voltage\s+control|power\s+flow|feeder|"
    r"substation|demand\s+response|grid[- ]connected|"
    r"renewable.*(dispatch|grid|power\s+system)|"
    r"(photovoltaic|wind).*(grid|dispatch|forecast)|"
    r"energy\s+storage.*(dispatch|grid|power)|"
    r"virtual\s+power\s+plant|electricity\s+(load|market|theft)|"
    r"short[- ]circuit|harmonics?.*(grid|power)|"
    r"inertia\s+control|damping\s+control.*(grid|power)|"
    r"distribution\s+network\s+source|coordinated\s+restoration"
    r")"
)

# Drop obvious non-grid false positives even if a weak keyword matched.
EXCLUDE = re.compile(
    r"(?i)("
    r"exoskeleton|muscle|dental|pulp|hematoma|subglottic|mHealth|"
    r"brain[- ]machine|emotion\s+recognition|port.?s\s+collection|"
    r"quantum\s+key\s+distribution|key\s+distribution\s+network|"
    r"robotaxi|correction:|editorial|retraction"
    r")"
)


def opener(use_proxy=True):
    h = []
    if use_proxy:
        h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_json(url: str, timeout: int = 70) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with opener(True).open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def is_pdf(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > 20000 and b"%PDF" in path.read_bytes()[:8192]
    except Exception:
        return False


def parse_app_doi(doi: str) -> tuple[str, str, str] | None:
    """MDPI Appl. Sci. DOI: 10.3390/app{VV}{II}{article}.

    Example: 10.3390/app15084498 → vol=15, issue=08, article=4498
    → filename applsci-15-04498.
    """
    bare = doi.lower().replace("https://doi.org/", "").strip()
    m = re.search(r"10\.3390/app(\d{2})(\d{2})(\d+)$", bare)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def doi_to_applsci_id(doi: str) -> str | None:
    parsed = parse_app_doi(doi)
    if not parsed:
        return None
    vol, _issue, art = parsed
    return f"applsci-{vol}-{art.zfill(5)}"


def parse_existing_ids() -> set[str]:
    ids: set[str] = set()
    for d in EXISTING_PDF_DIRS:
        if not d.exists():
            continue
        for p in d.glob("*.pdf"):
            m = re.search(r"applsci-(\d{2})-(\d+)", p.name, re.I)
            if m:
                ids.add(f"applsci-{m.group(1)}-{m.group(2).zfill(5)}")
            # also bare doi-style names
            m2 = re.search(r"app(\d{2})(\d+)", p.name, re.I)
            if m2:
                ids.add(f"applsci-{m2.group(1)}-{m2.group(2).zfill(5)}")
    # mintou / other mapped copies referenced in lit_table
    lit = (
        ROOT
        / "papers/literature/target_journal_related/metadata"
        / "ideaspark_fullcorpus_lit_tables/mdpi-applied-sciences_lit_table.md"
    )
    if lit.exists():
        for m in re.finditer(r"applsci-(\d{2})-(\d+)", lit.read_text(encoding="utf-8", errors="replace")):
            ids.add(f"applsci-{m.group(1)}-{m.group(2).zfill(5)}")
    return ids


def crossref_collect(rows_per_query: int = 40) -> list[dict]:
    by_doi: dict[str, dict] = {}
    for q in QUERIES:
        url = (
            f"https://api.crossref.org/journals/{ISSN}/works?"
            + urllib.parse.urlencode(
                {
                    "filter": "from-pub-date:2023-01-01,until-pub-date:2026-12-31",
                    "query": q,
                    "rows": rows_per_query,
                    "mailto": MAILTO,
                    "sort": "relevance",
                    "order": "desc",
                }
            )
        )
        try:
            payload = http_json(url)
        except Exception as e:
            print(f"  crossref fail [{q}]: {e}", flush=True)
            continue
        items = payload.get("message", {}).get("items", []) or []
        print(f"  query={q!r} n={len(items)} total={payload.get('message', {}).get('total-results')}", flush=True)
        for it in items:
            doi = (it.get("DOI") or "").lower()
            if not doi.startswith("10.3390/app"):
                continue
            title = ""
            if it.get("title"):
                title = it["title"][0]
            if EXCLUDE.search(title or ""):
                continue
            if not RELEVANT.search(title or ""):
                continue
            year = None
            for key in ("published-print", "published-online", "created"):
                parts = (it.get(key) or {}).get("date-parts") or []
                if parts and parts[0]:
                    year = parts[0][0]
                    break
            if year is not None and (year < 2023 or year > 2026):
                continue
            aid = doi_to_applsci_id(doi)
            if not aid:
                continue
            by_doi[doi] = {
                "doi": doi,
                "title": title,
                "year": year,
                "applsci_id": aid,
                "query": q,
            }
        time.sleep(0.35)
    return list(by_doi.values())


def mdpi_pdf_urls(doi: str, applsci_id: str) -> list[str]:
    parsed = parse_app_doi(doi)
    if not parsed:
        return []
    vol, issue, art = parsed
    art_int = str(int(art))
    art_pad = art.zfill(5)
    bare = doi.lower().replace("https://doi.org/", "")
    # mdpi-res CDN is the most reliable path in this environment
    return [
        f"https://mdpi-res.com/d_attachment/applsci/{applsci_id}/article_deploy/{applsci_id}.pdf",
        f"https://mdpi-res.com/d_attachment/applsci/{applsci_id}/article_deploy/{applsci_id}.pdf?version=0",
        f"https://www.mdpi.com/{ISSN}/{int(vol)}/{int(issue)}/{art_int}/pdf",
        f"https://www.mdpi.com/{ISSN}/{int(vol)}/{int(issue)}/{art_pad}/pdf",
        f"https://www.mdpi.com/pdf/{bare}",
    ]


def aria2_download(url: str, dest: Path, referer: str = "") -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if is_pdf(dest):
        return True, "exists"
    if dest.exists():
        dest.unlink(missing_ok=True)
    headers = [f"User-Agent: {UA}", "Accept: application/pdf,*/*"]
    if referer:
        headers.append(f"Referer: {referer}")
    cmd = [
        str(ARIA2),
        "-x",
        "4",
        "-s",
        "4",
        "-k",
        "1M",
        "--max-tries=3",
        "--retry-wait=2",
        "--timeout=45",
        "--connect-timeout=20",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        f"--all-proxy={PROXY}",
        "-d",
        str(dest.parent),
        "-o",
        dest.name,
    ]
    for h in headers:
        cmd.extend(["--header", h])
    cmd.append(url)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    except Exception as e:
        return False, str(e)[:120]
    if is_pdf(dest):
        return True, url
    if dest.exists():
        head = dest.read_bytes()[:80]
        dest.unlink(missing_ok=True)
        return False, f"not_pdf:{head[:40]!r}"
    err = (p.stderr or p.stdout or "")[-180:]
    return False, err.replace("\n", " ")[:160]


def balance_pick(cands: list[dict], existing: set[str], n: int) -> list[dict]:
    """Prefer year diversity + skip existing."""
    fresh = [c for c in cands if c["applsci_id"] not in existing]
    # score: prefer clearer grid terms
    strong = re.compile(
        r"(?i)(power\s+system|power\s+grid|smart\s+grid|microgrid|"
        r"distribution\s+network|unit\s+commitment|economic\s+dispatch|"
        r"load\s+forecast|optimal\s+power\s+flow|active\s+distribution)"
    )

    def score(c: dict) -> tuple:
        t = c["title"] or ""
        y = c["year"] or 0
        return (0 if strong.search(t) else 1, -int(y), t)

    fresh.sort(key=score)
    # round-robin by year for diversity
    by_year: dict[int, list] = {}
    for c in fresh:
        by_year.setdefault(c["year"] or 0, []).append(c)
    years = sorted([y for y in by_year if y], reverse=True)
    picked: list[dict] = []
    seen = set()
    while len(picked) < n and any(by_year.values()):
        for y in years:
            if len(picked) >= n:
                break
            bucket = by_year.get(y) or []
            while bucket:
                c = bucket.pop(0)
                if c["doi"] in seen:
                    continue
                seen.add(c["doi"])
                picked.append(c)
                break
        if not any(by_year.values()):
            break
    return picked


def main():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)
    existing = parse_existing_ids()
    print(f"already-local applsci ids: {len(existing)}", flush=True)

    print("collecting Crossref candidates…", flush=True)
    cands = crossref_collect()
    print(f"relevant unique DOIs: {len(cands)}", flush=True)
    picked = balance_pick(cands, existing, TARGET_NEW)
    print(f"selected for download: {len(picked)}", flush=True)

    rows = []
    ok = 0
    for i, c in enumerate(picked, 1):
        dest = PDF_DIR / f"{c['applsci_id']}.pdf"
        print(f"[{i}/{len(picked)}] {c['year']} {c['applsci_id']} | {c['title'][:70]}", flush=True)
        success, note = False, "no_url"
        if is_pdf(dest):
            success, note = True, "exists"
        else:
            parsed = parse_app_doi(c["doi"])
            if parsed:
                vol, issue, art = parsed
                referer = f"https://www.mdpi.com/{ISSN}/{int(vol)}/{int(issue)}/{int(art)}"
            else:
                referer = f"https://www.mdpi.com/journal/applsci"
            for url in mdpi_pdf_urls(c["doi"], c["applsci_id"]):
                success, note = aria2_download(url, dest, referer=referer)
                if success:
                    break
                time.sleep(0.35)
        if success:
            ok += 1
            existing.add(c["applsci_id"])
        rows.append(
            {
                **c,
                "pdf": str(dest.relative_to(ROOT)).replace("\\", "/") if success else "",
                "status": "ok" if success else "fail",
                "note": note,
                "bytes": dest.stat().st_size if success and dest.exists() else 0,
            }
        )
        time.sleep(0.5)

    reg = META_DIR / "download_registry.csv"
    with reg.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["doi", "year", "applsci_id", "title", "query", "status", "note", "pdf", "bytes"],
        )
        w.writeheader()
        w.writerows(rows)

    summary = {
        "target_new": TARGET_NEW,
        "downloaded_ok": ok,
        "failed": len(rows) - ok,
        "already_local_before": len(parse_existing_ids()) - ok,  # approximate
        "pdf_dir": str(PDF_DIR.relative_to(ROOT)).replace("\\", "/"),
        "years": sorted({r["year"] for r in rows if r["status"] == "ok"}),
        "ok_ids": [r["applsci_id"] for r in rows if r["status"] == "ok"],
    }
    (META_DIR / "download_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    readme = META_DIR / "README.md"
    lines = [
        "# Applied Sciences — power-grid supplement (2023–2026)",
        "",
        f"- Downloaded OK: **{ok}** / {len(rows)} attempted (target {TARGET_NEW}).",
        f"- PDF dir: `{summary['pdf_dir']}`",
        f"- Years: {summary['years']}",
        "",
        "| Year | ID | Title | Status |",
        "|---:|---|---|---|",
    ]
    for r in rows:
        t = (r["title"] or "").replace("|", "/")[:90]
        lines.append(f"| {r['year']} | `{r['applsci_id']}` | {t} | {r['status']} |")
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
