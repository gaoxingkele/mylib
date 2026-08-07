# -*- coding: utf-8 -*-
"""Download ~10 OA full-texts per journal via EuropePMC (+ OpenAlex arXiv).

Publisher PDFs (MDPI/IEEE/Elsevier/Wiley) 403 here; EuropePMC ?pdf=render works.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "papers/literature/target_journal_related"
PDF_ROOT = OUT / "fulltext_by_journal"
META = OUT / "metadata"
REGISTRY = META / "journal_fulltext_registry.csv"
SUMMARY = META / "journal_fulltext_summary.csv"
PROXY = "http://127.0.0.1:17890"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
TARGET = 10
MAILTO = "literature@powergrid-benchmark.local"

JOURNALS = [
    {"slug": "mdpi-machines", "issn": "2075-1702", "name": "Machines"},
    {"slug": "mdpi-information", "issn": "2078-2489", "name": "Information"},
    {"slug": "mdpi-symmetry", "issn": "2073-8994", "name": "Symmetry"},
    {"slug": "mdpi-remote-sensing", "issn": "2072-4292", "name": "Remote Sensing"},
    {"slug": "mdpi-algorithms", "issn": "1999-4893", "name": "Algorithms"},
    {"slug": "mdpi-future-internet", "issn": "1999-5903", "name": "Future Internet"},
    {"slug": "mdpi-atmosphere", "issn": "2073-4433", "name": "Atmosphere"},
    {"slug": "tsp-cmc", "issn": "1546-2226", "name": "Computers, Materials & Continua"},
    {"slug": "springer-discover-computing", "issn": "2948-2992", "name": "Discover Computing"},
    {"slug": "peerj-computer-science", "issn": "2376-5992", "name": "PeerJ Computer Science"},
    {"slug": "ieee-internet-of-things-journal", "issn": "2327-4662", "name": "IEEE Internet of Things Journal"},
    {"slug": "ijacsa", "issn": "2156-5570", "name": "IJACSA"},
    {"slug": "wiley-ccpe", "issn": "1532-0634", "name": "CCPE"},
    {"slug": "nature-scientific-reports", "issn": "2045-2322", "name": "Scientific Reports"},
    {"slug": "elsevier-journal-of-energy-storage", "issn": "2352-152X", "name": "Journal of Energy Storage"},
    {"slug": "keai-unconventional-resources", "issn": "2666-5190", "name": "Unconventional Resources"},
]

TOPIC_Q = (
    "(power OR energy OR electricity OR grid OR battery OR forecasting OR "
    "photovoltaic OR wind OR algorithm OR learning OR optimization OR IoT OR "
    "neural OR motor OR drive OR remote OR atmosphere OR storage OR network)"
)


def opener(use_proxy=True):
    h = []
    if use_proxy:
        h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_get(url, timeout=100, use_proxy=True):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with opener(use_proxy).open(req, timeout=timeout) as resp:
        return resp.read()


def http_json(url, timeout=60):
    for i in range(5):
        try:
            return json.loads(http_get(url, timeout=timeout).decode("utf-8", errors="replace"))
        except Exception as e:
            if i == 4:
                raise
            time.sleep(1.5 + i)
    return {}


def slugify(title, n=55):
    s = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_")
    return (s[:n] or "paper").lower()


def is_pdf(data: bytes) -> bool:
    return b"%PDF" in data[:8192]


def download_pdf(url: str, dest: Path) -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 20000 and is_pdf(dest.read_bytes()[:4096]):
        return True, "exists"
    last = "fail"
    for use_proxy in (True, False):
        try:
            data = http_get(url, timeout=120, use_proxy=use_proxy)
        except Exception as e:
            last = str(e)[:80]
            continue
        if not is_pdf(data):
            last = "not_pdf"
            continue
        dest.write_bytes(data)
        if dest.stat().st_size < 15000:
            dest.unlink(missing_ok=True)
            last = "small"
            continue
        return True, "ok"
    return False, last


def europepmc_candidates(issn: str, need: int) -> list[dict]:
    out = []
    seen = set()
    queries = [
        f"ISSN:{issn} AND OPEN_ACCESS:y AND {TOPIC_Q}",
        f"ISSN:{issn} AND OPEN_ACCESS:y",
    ]
    for q in queries:
        for page in range(1, 6):
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
                {
                    "query": q,
                    "format": "json",
                    "pageSize": 25,
                    "pageNumber": page,
                    "resultType": "core",
                    "sort": "CITED desc",
                }
            )
            try:
                payload = http_json(url, timeout=70)
            except Exception as e:
                print(f"  epmc error: {e}")
                break
            results = ((payload.get("resultList") or {}).get("result")) or []
            if not results:
                break
            for r in results:
                doi = (r.get("doi") or "").lower()
                key = doi or str(r.get("pmcid") or r.get("id"))
                if key in seen:
                    continue
                urls = []
                pmcid = r.get("pmcid")
                if pmcid:
                    urls.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
                    urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/")
                for ft in ((r.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
                    if (ft.get("documentStyle") or "").lower() != "pdf":
                        continue
                    u = ft.get("url") or ""
                    # skip publisher stampPDF
                    if any(x in u.lower() for x in ("mdpi.com", "ieeexplore", "sciencedirect", "wiley.com")):
                        continue
                    if "peerj.com/articles/" in u and not u.endswith(".pdf"):
                        m = re.search(r"/articles/(\d+)", u)
                        if m:
                            u = f"https://peerj.com/articles/{m.group(1)}.pdf"
                    if "arxiv.org" in u:
                        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                        if m:
                            u = f"https://arxiv.org/pdf/{m.group(1)}.pdf"
                    if u and u not in urls:
                        # allow europepmc/peerj/arxiv/nature/edu
                        if any(
                            k in u.lower()
                            for k in (
                                "europepmc",
                                "pmc.ncbi",
                                "arxiv.org",
                                "peerj.com",
                                "nature.com",
                                "zenodo",
                                "hal.",
                                ".edu",
                                "ac.uk",
                                "techscience",
                                "thesai.org",
                            )
                        ):
                            urls.append(u)
                if not urls:
                    continue
                seen.add(key)
                year = r.get("pubYear")
                out.append(
                    {
                        "title": re.sub(r"<[^>]+>", "", r.get("title") or "untitled"),
                        "year": int(year) if str(year).isdigit() else None,
                        "doi": doi,
                        "cited": int(r.get("citedByCount") or 0),
                        "pdf_urls": urls,
                        "src": "europepmc",
                    }
                )
            time.sleep(0.25)
            if len(out) >= need * 5:
                break
        if len(out) >= need * 4:
            break
    out.sort(key=lambda x: (-x["cited"], -(x["year"] or 0)))
    return out


def openalex_arxiv_for_issn(issn: str, need: int) -> list[dict]:
    """Supplement with works that have an arXiv location (same DOI/title family)."""
    out = []
    seen = set()
    cursor = "*"
    for _ in range(3):
        params = {
            "filter": f"primary_location.source.issn:{issn},type:article,is_oa:true",
            "search": "power OR energy OR algorithm OR learning OR IoT OR grid OR battery",
            "per_page": "50",
            "cursor": cursor,
            "mailto": MAILTO,
            "sort": "cited_by_count:desc",
        }
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
        try:
            payload = http_json(url, timeout=50)
        except Exception as e:
            print(f"  openalex skip: {e}")
            break
        for w in payload.get("results") or []:
            urls = []
            for loc in w.get("locations") or []:
                for key in ("pdf_url", "landing_page_url"):
                    u = loc.get(key) or ""
                    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                    if m:
                        urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
            urls = list(dict.fromkeys(urls))
            if not urls:
                continue
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            key = doi or w.get("id")
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "title": w.get("display_name") or "untitled",
                    "year": w.get("publication_year"),
                    "doi": doi,
                    "cited": w.get("cited_by_count") or 0,
                    "pdf_urls": urls,
                    "src": "openalex-arxiv",
                }
            )
        cursor = (payload.get("meta") or {}).get("next_cursor")
        time.sleep(0.4)
        if not cursor or len(out) >= need * 3:
            break
    return out


def migrate_cmc():
    old = OUT / "cmc_pdfs"
    dest = PDF_ROOT / "tsp-cmc"
    dest.mkdir(parents=True, exist_ok=True)
    if old.exists():
        for p in old.glob("*.pdf"):
            t = dest / p.name
            if not t.exists():
                t.write_bytes(p.read_bytes())


def existing(slug):
    d = PDF_ROOT / slug
    return sorted(d.glob("*.pdf")) if d.exists() else []


def process(j, target):
    slug = j["slug"]
    print(f"\n=== {slug} ({j['name']}) ===")
    if slug == "tsp-cmc":
        migrate_cmc()
    rows = []
    success = 0
    for p in existing(slug):
        rows.append(
            {
                "slug": slug,
                "journal": j["name"],
                "title": p.stem,
                "year": "",
                "doi": "",
                "pdf_path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "pdf_url": "",
                "status": "cached",
                "cited": "",
                "src": "cache",
            }
        )
        success += 1
    print(f"  existing: {success}")
    if success >= target:
        return {"slug": slug, "ok": success, "rows": rows[:target]}

    cands = europepmc_candidates(j["issn"], target)
    print(f"  europepmc: {len(cands)}")
    if len(cands) < target * 2:
        extra = openalex_arxiv_for_issn(j["issn"], target)
        print(f"  openalex-arxiv: {len(extra)}")
        seen = {(c.get("doi") or c["title"]).lower() for c in cands}
        for c in extra:
            k = (c.get("doi") or c["title"]).lower()
            if k not in seen:
                cands.append(c)
                seen.add(k)
        cands.sort(key=lambda x: (-x["cited"], -(x["year"] or 0)))

    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    seen_t = {re.sub(r"[^a-z0-9]+", "", r["title"].lower())[:48] for r in rows}
    for c in cands:
        if success >= target:
            break
        tkey = re.sub(r"[^a-z0-9]+", "", c["title"].lower())[:48]
        if tkey in seen_t:
            continue
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        ok = False
        used = ""
        err = ""
        for u in c["pdf_urls"]:
            ok, err = download_pdf(u, path)
            if ok:
                used = u
                break
            time.sleep(0.1)
        if ok:
            success += 1
            seen_t.add(tkey)
            rows.append(
                {
                    "slug": slug,
                    "journal": j["name"],
                    "title": c["title"],
                    "year": c.get("year") or "",
                    "doi": c.get("doi") or "",
                    "pdf_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "pdf_url": used,
                    "status": "downloaded",
                    "cited": c.get("cited") or "",
                    "src": c.get("src") or "",
                }
            )
            host = used.split("/")[2] if "://" in used else ""
            print(f"  [{success}/{target}] OK {host} | {c['title'][:70]}")
        else:
            print(f"  FAIL {c['title'][:60]} :: {err}")
        time.sleep(0.2)
    return {"slug": slug, "ok": success, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    META.mkdir(parents=True, exist_ok=True)
    PDF_ROOT.mkdir(parents=True, exist_ok=True)
    journals = JOURNALS
    if args.only:
        journals = [j for j in JOURNALS if j["slug"] in set(args.only)]
    all_rows, summary = [], []
    for j in journals:
        try:
            r = process(j, args.target)
        except Exception as e:
            print(f"  JOURNAL ERROR {j['slug']}: {e}")
            r = {"slug": j["slug"], "ok": 0, "rows": []}
        all_rows.extend(r.get("rows") or [])
        summary.append({"slug": r["slug"], "pdf_ok": r.get("ok", 0), "target": args.target})
    if all_rows:
        with REGISTRY.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "pdf_ok", "target"])
        w.writeheader()
        w.writerows(summary)
    print("\n=== SUMMARY ===")
    for s in summary:
        print(f"  [{'OK' if s['pdf_ok'] >= s['target'] else 'LOW'}] {s['slug']}: {s['pdf_ok']}/{s['target']}")


if __name__ == "__main__":
    main()
