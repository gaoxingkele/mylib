# -*- coding: utf-8 -*-
"""Fill short journals by matching OpenAlex titles to arXiv PDFs (preprint mirrors)."""
from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
SUMMARY = META / "journal_fulltext_summary.csv"
PROXY = "http://127.0.0.1:17890"
ARIA2 = Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe")
UA = "Mozilla/5.0"
MAILTO = "powergrid.literature@gmail.com"
TARGET = 10

NEED = {
    "mdpi-machines": "2075-1702",
    "keai-unconventional-resources": "2666-5190",
}


def opener(use_proxy=True):
    h = []
    if use_proxy:
        h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_bytes(url, timeout=40, use_proxy=True):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with opener(use_proxy).open(req, timeout=timeout) as resp:
        return resp.read()


def http_json(url, timeout=50):
    return json.loads(http_bytes(url, timeout=timeout).decode("utf-8", errors="replace"))


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def title_key(t):
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:48]


def is_pdf(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 20000 and b"%PDF" in path.read_bytes()[:8192]


def aria2_get(url: str, dest: Path) -> bool:
    import subprocess

    if is_pdf(dest):
        return True
    dest.unlink(missing_ok=True)
    cmd = [
        str(ARIA2),
        "-x", "8",
        "-s", "8",
        "--max-tries=3",
        "--timeout=40",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        f"--all-proxy={PROXY}",
        f"--user-agent={UA}",
        "-d", str(dest.parent),
        "-o", dest.name,
        url,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=100)
    except Exception:
        return False
    if is_pdf(dest):
        return True
    dest.unlink(missing_ok=True)
    return False


def openalex_titles(issn: str, per=80):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "filter": f"primary_location.source.issn:{issn},type:article",
            "per_page": per,
            "sort": "cited_by_count:desc",
            "mailto": MAILTO,
        }
    )
    payload = http_json(url)
    out = []
    for w in payload.get("results") or []:
        out.append(
            {
                "title": w.get("display_name") or "untitled",
                "year": w.get("publication_year"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            }
        )
    return out


def arxiv_search(title: str, max_results: int = 5):
    # quote title words
    q = "ti:\"" + title[:120].replace('"', "") + "\""
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "start": 0, "max_results": max_results}
    )
    try:
        xml = http_bytes(url, timeout=40).decode("utf-8", errors="replace")
    except Exception:
        # looser search
        words = re.findall(r"[A-Za-z0-9]{4,}", title)[:8]
        if not words:
            return []
        q2 = " AND ".join(f"all:{w}" for w in words)
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"search_query": q2, "start": 0, "max_results": max_results}
        )
        try:
            xml = http_bytes(url, timeout=40).decode("utf-8", errors="replace")
        except Exception:
            return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(xml)
    except Exception:
        return []
    hits = []
    for entry in root.findall("a:entry", ns):
        etitle = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        etitle = re.sub(r"\s+", " ", etitle)
        pdf = ""
        for link in entry.findall("a:link", ns):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf = link.attrib.get("href") or ""
        if not pdf:
            id_url = entry.findtext("a:id", default="", namespaces=ns) or ""
            m = re.search(r"arxiv\.org/abs/([0-9.]+)", id_url)
            if m:
                pdf = f"https://arxiv.org/pdf/{m.group(1)}.pdf"
        if pdf and not pdf.endswith(".pdf"):
            pdf = pdf + ".pdf"
        hits.append({"title": etitle, "pdf": pdf})
    return hits


def similar(a: str, b: str) -> float:
    ka = set(re.findall(r"[a-z0-9]{4,}", a.lower()))
    kb = set(re.findall(r"[a-z0-9]{4,}", b.lower()))
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


def topup(slug, issn):
    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    have = list(dest.glob("*.pdf"))
    print(f"\n=== ARXIV-MATCH {slug} have={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have)
    have_t = set()
    for p in have:
        parts = p.stem.split("__")
        if len(parts) >= 3:
            have_t.add(title_key(parts[2]))
    works = openalex_titles(issn)
    print(f"  openalex works={len(works)}", flush=True)
    success = len(have)
    tried = 0
    for w in works:
        if success >= TARGET:
            break
        tkey = title_key(w["title"])
        if tkey in have_t:
            continue
        tried += 1
        hits = arxiv_search(w["title"])
        time.sleep(0.3)
        best = None
        best_s = 0.0
        for h in hits:
            s = similar(w["title"], h["title"])
            if s > best_s:
                best_s, best = s, h
        if not best or best_s < 0.55 or not best.get("pdf"):
            if tried % 10 == 0:
                print(f"  …tried {tried} no arxiv match, still {success}/{TARGET}", flush=True)
            continue
        hsh = hashlib.sha1((w.get("doi") or w["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{w.get('year') or 'noyear'}__{slugify(w['title'])}__{hsh}.pdf"
        # note in filename stem already; mark as arxiv mirror via sidecar? skip
        if aria2_get(best["pdf"], path):
            success += 1
            have_t.add(tkey)
            print(
                f"  [{success}/{TARGET}] sim={best_s:.2f} {w['title'][:60]}",
                flush=True,
            )
            print(f"       arxiv: {best['title'][:60]}", flush=True)
        time.sleep(0.15)
    print(f"  final={success} tried={tried}", flush=True)
    return success


def rewrite_summary():
    import csv

    rows = []
    for d in sorted(PDF_ROOT.glob("*")):
        if d.is_dir() and not d.name.startswith("_"):
            rows.append({"slug": d.name, "pdf_ok": len(list(d.glob("*.pdf"))), "target": TARGET})
    META.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "pdf_ok", "target"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        if r["pdf_ok"] < TARGET:
            print(f"  [LOW] {r['slug']}: {r['pdf_ok']}/{TARGET}")
        else:
            print(f"  [OK] {r['slug']}: {r['pdf_ok']}/{TARGET}")


def main():
    for slug, issn in NEED.items():
        topup(slug, issn)
    print("\n=== SUMMARY ===")
    rewrite_summary()


if __name__ == "__main__":
    main()
