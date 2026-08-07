# -*- coding: utf-8 -*-
"""Focused top-up: only hosts that usually return real PDFs in this env."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
SUMMARY = META / "journal_fulltext_summary.csv"
PROXY = "http://127.0.0.1:17890"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
TARGET = 10
MAILTO = "powergrid.literature@gmail.com"

NEED = {
    "mdpi-machines": "2075-1702",
    "mdpi-symmetry": "2073-8994",
    "mdpi-algorithms": "1999-4893",
    "mdpi-future-internet": "1999-5903",
    "springer-discover-computing": "2948-2992",
    "wiley-ccpe": "1532-0634",
    "elsevier-journal-of-energy-storage": "2352-152X",
    "keai-unconventional-resources": "2666-5190",
}

GOOD_HOST = (
    "europepmc.org",
    "pmc.ncbi.nlm.nih.gov",
    "arxiv.org",
    "peerj.com",
    "nature.com",
    "zenodo.org",
    "figshare.com",
    "hal.science",
    "thesai.org",
    "techscience.com",
    "springer.com",
    "springeropen.com",
    "link.springer.com",
    ".edu/",
    "ac.uk/",
)


def opener(use_proxy=True):
    h = []
    if use_proxy:
        h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_get(url, timeout=40, use_proxy=True):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/pdf,*/*;q=0.8"},
    )
    with opener(use_proxy).open(req, timeout=timeout) as resp:
        return resp.read(), resp.geturl()


def http_json(url, timeout=50):
    data, _ = http_get(url, timeout=timeout)
    return json.loads(data.decode("utf-8", errors="replace"))


def is_pdf(b: bytes) -> bool:
    return b"%PDF" in b[:8192]


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())[:48]


def download(url: str, dest: Path) -> tuple[bool, str]:
    if dest.exists() and dest.stat().st_size > 20000 and is_pdf(dest.read_bytes()[:4096]):
        return True, "exists"
    last = "fail"
    for use_proxy in (True, False):
        try:
            data, final = http_get(url, timeout=40, use_proxy=use_proxy)
        except Exception as e:
            last = str(e)[:100]
            continue
        if not is_pdf(data):
            last = f"not_pdf:{final[:70]}"
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        if dest.stat().st_size < 15000:
            dest.unlink(missing_ok=True)
            last = "small"
            continue
        return True, final
    return False, last


def good_url(u: str) -> bool:
    ul = u.lower()
    if any(x in ul for x in ("mdpi.com/", "ieeexplore", "sciencedirect.com", "wiley.com/doi/pdf", "onlinelibrary.wiley")):
        return False
    return any(x in ul for x in GOOD_HOST) or ul.endswith(".pdf")


def epmc_candidates(issn: str, pages: int = 15):
    out = []
    seen = set()
    for page in range(1, pages + 1):
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
            {
                "query": f"ISSN:{issn} AND (OPEN_ACCESS:y OR HAS_PDF:y)",
                "format": "json",
                "pageSize": 25,
                "pageNumber": page,
                "resultType": "core",
            }
        )
        try:
            payload = http_json(url)
        except Exception as e:
            print("  epmc err", e, flush=True)
            break
        results = ((payload.get("resultList") or {}).get("result")) or []
        if not results:
            break
        for r in results:
            pmcid = r.get("pmcid")
            doi = (r.get("doi") or "").lower()
            title = re.sub(r"<[^>]+>", "", r.get("title") or "untitled")
            key = doi or pmcid or title_key(title)
            if key in seen:
                continue
            seen.add(key)
            urls = []
            if pmcid:
                urls += [
                    f"https://europepmc.org/articles/{pmcid}?pdf=render",
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",
                ]
            out.append({"title": title, "year": r.get("pubYear"), "doi": doi, "urls": urls})
        time.sleep(0.15)
    return out


def openalex_candidates(issn: str, per: int = 100):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "filter": f"primary_location.source.issn:{issn},is_oa:true,type:article",
            "per_page": per,
            "sort": "cited_by_count:desc",
            "mailto": MAILTO,
        }
    )
    try:
        payload = http_json(url)
    except Exception as e:
        print("  openalex err", e, flush=True)
        return []
    out = []
    for w in payload.get("results") or []:
        urls = []
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        for loc in [w.get("best_oa_location"), *(w.get("locations") or [])]:
            if not loc:
                continue
            for k in ("pdf_url", "landing_page_url"):
                u = loc.get(k) or ""
                if not u:
                    continue
                m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                if m:
                    urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
                m2 = re.search(r"(PMC\d+)", u, re.I)
                if m2:
                    pmc = m2.group(1).upper()
                    urls.append(f"https://europepmc.org/articles/{pmc}?pdf=render")
                    urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/")
                if "peerj.com/articles/" in u:
                    m3 = re.search(r"/articles/(\d+)", u)
                    if m3:
                        urls.append(f"https://peerj.com/articles/{m3.group(1)}.pdf")
                if any(x in u.lower() for x in ("zenodo.org", "figshare.com")):
                    urls.append(u)
                if "springer.com" in u.lower() and u.lower().endswith(".pdf"):
                    urls.append(u)
                if good_url(u) and (u.lower().endswith(".pdf") or "pdf" in u.lower()):
                    urls.append(u)
        urls = [u for u in dict.fromkeys(urls) if good_url(u)]
        if not urls:
            continue
        out.append(
            {
                "title": w.get("display_name") or "untitled",
                "year": w.get("publication_year"),
                "doi": doi,
                "urls": urls,
            }
        )
    return out


def unpaywall_good(doi: str) -> list[str]:
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}"
    try:
        payload = http_json(url, timeout=30)
    except Exception:
        return []
    urls = []
    for loc in [payload.get("best_oa_location"), *(payload.get("oa_locations") or [])]:
        if not loc:
            continue
        for key in ("url_for_pdf", "url"):
            u = loc.get(key) or ""
            if not u:
                continue
            m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
            if m:
                urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
            m2 = re.search(r"(PMC\d+)", u, re.I)
            if m2:
                pmc = m2.group(1).upper()
                urls.append(f"https://europepmc.org/articles/{pmc}?pdf=render")
            if good_url(u):
                urls.append(u)
    return list(dict.fromkeys(urls))


def existing_title_keys(slug: str) -> set[str]:
    d = PDF_ROOT / slug
    keys = set()
    if not d.exists():
        return keys
    for p in d.glob("*.pdf"):
        parts = p.stem.split("__")
        if len(parts) >= 3:
            keys.add(title_key(parts[2]))
        keys.add(title_key(p.stem))
    return keys


def topup(slug: str, issn: str) -> int:
    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    have = list(dest.glob("*.pdf"))
    print(f"\n=== TOPUP {slug} existing={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have)

    print("  epmc…", flush=True)
    cands = epmc_candidates(issn)
    print(f"  epmc n={len(cands)}", flush=True)
    print("  openalex…", flush=True)
    cands.extend(openalex_candidates(issn))
    seen = set()
    uniq = []
    for c in cands:
        k = title_key(c["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    print(f"  uniq={len(uniq)}", flush=True)

    have_t = existing_title_keys(slug)
    success = len(have)
    tried = 0
    for c in uniq:
        if success >= TARGET:
            break
        tkey = title_key(c["title"])
        if tkey in have_t:
            continue
        urls = list(c.get("urls") or [])
        if not urls and c.get("doi"):
            urls = unpaywall_good(c["doi"])
            time.sleep(0.12)
        urls = [u for u in urls if good_url(u)]
        if not urls:
            continue
        tried += 1
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        ok = False
        for u in urls[:5]:
            ok, info = download(u, path)
            if ok and info != "exists":
                success += 1
                have_t.add(tkey)
                print(f"  [{success}/{TARGET}] OK {c['title'][:70]}", flush=True)
                break
            if ok and info == "exists":
                have_t.add(tkey)
                break
            time.sleep(0.05)
        if tried % 10 == 0 and success < TARGET:
            print(f"  …tried {tried} still {success}/{TARGET}", flush=True)
        time.sleep(0.08)
    print(f"  done tried={tried} final={success}", flush=True)
    return success


def main():
    # ensure dirs for empty journals
    for slug in NEED:
        (PDF_ROOT / slug).mkdir(parents=True, exist_ok=True)

    by = {}
    for d in sorted(PDF_ROOT.glob("*")):
        if not d.is_dir():
            continue
        if d.name in NEED:
            n = topup(d.name, NEED[d.name])
        else:
            n = len(list(d.glob("*.pdf")))
        by[d.name] = {"slug": d.name, "pdf_ok": n, "target": TARGET}

    # recount from disk
    for d in sorted(PDF_ROOT.glob("*")):
        if d.is_dir():
            by[d.name] = {
                "slug": d.name,
                "pdf_ok": len(list(d.glob("*.pdf"))),
                "target": TARGET,
            }

    META.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "pdf_ok", "target"])
        w.writeheader()
        w.writerows(by.values())

    print("\n=== SUMMARY ===", flush=True)
    for s in sorted(by.values(), key=lambda x: x["slug"]):
        flag = "OK" if s["pdf_ok"] >= TARGET else "LOW"
        print(f"  [{flag}] {s['slug']}: {s['pdf_ok']}/{TARGET}", flush=True)


if __name__ == "__main__":
    main()
