# -*- coding: utf-8 -*-
"""Top-up journals still below 10 PDFs using Crossref + DOI resolution + EuropePMC broaden."""
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
REGISTRY = META / "journal_fulltext_registry.csv"
SUMMARY = META / "journal_fulltext_summary.csv"
PROXY = "http://127.0.0.1:17890"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
TARGET = 10
MAILTO = "powergrid.literature@gmail.com"

# journals still short after main pass (skip any already at TARGET at runtime)
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

ALLOW_SUBSTR = (
    "europepmc.org",
    "pmc.ncbi.nlm.nih.gov",
    "arxiv.org",
    "peerj.com",
    "nature.com",
    "zenodo.org",
    "hal.science",
    "hal.archives",
    ".edu",
    "ac.uk",
    "thesai.org",
    "techscience.com",
    "keaipublishing.com",
    "sciencedirect.com/science/article",  # try OA pdfft; may fail
    "figshare.com",
    "hdl.handle.net",
    "researchgate.net",
    "researchsquare.com",
    "ssrn.com",
    "frontiersin.org",
    "plos.org",
    "biomedcentral.com",
    "springer.com",
    "springeropen.com",
    "link.springer.com",
    "wiley.com/doi/pdf",
    "onlinelibrary.wiley.com/doi/pdf",
    "mdpi.com/",  # often 403; still try as last resort via unpaywall
    "sciopen.com",
    "doaj.org",
)


def opener(use_proxy=True):
    h = []
    if use_proxy:
        h.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_get(url, timeout=100, use_proxy=True, follow=True):
    headers = {
        "User-Agent": UA,
        "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if "sciencedirect.com" in url.lower():
        headers["Referer"] = "https://www.sciencedirect.com/"
    if "mdpi.com" in url.lower():
        headers["Referer"] = "https://www.mdpi.com/"
    if "wiley.com" in url.lower() or "onlinelibrary.wiley.com" in url.lower():
        headers["Referer"] = "https://onlinelibrary.wiley.com/"
    req = urllib.request.Request(url, headers=headers)
    with opener(use_proxy).open(req, timeout=timeout) as resp:
        return resp.read(), resp.geturl()


def http_json(url, timeout=60):
    data, _ = http_get(url, timeout=timeout)
    return json.loads(data.decode("utf-8", errors="replace"))


def is_pdf(b: bytes) -> bool:
    return b"%PDF" in b[:8192]


def download(url: str, dest: Path) -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 20000 and is_pdf(dest.read_bytes()[:4096]):
        return True, "exists"
    last = "fail"
    for use_proxy in (True, False):
        try:
            data, final = http_get(url, timeout=45, use_proxy=use_proxy)
        except Exception as e:
            last = str(e)[:100]
            continue
        if not is_pdf(data):
            last = f"not_pdf:{final[:60]}"
            continue
        dest.write_bytes(data)
        if dest.stat().st_size < 15000:
            dest.unlink(missing_ok=True)
            last = "small"
            continue
        return True, final
    return False, last


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def existing(slug):
    d = PDF_ROOT / slug
    return sorted(d.glob("*.pdf")) if d.exists() else []


def epmc(issn, pages=8):
    out = []
    seen = set()
    for page in range(1, pages + 1):
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
            {
                "query": f"ISSN:{issn} AND OPEN_ACCESS:y",
                "format": "json",
                "pageSize": 25,
                "pageNumber": page,
                "resultType": "core",
            }
        )
        try:
            payload = http_json(url)
        except Exception as e:
            print("  epmc", e)
            break
        results = ((payload.get("resultList") or {}).get("result")) or []
        if not results:
            break
        for r in results:
            pmcid = r.get("pmcid")
            if not pmcid:
                continue
            doi = (r.get("doi") or "").lower()
            key = doi or pmcid
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "title": re.sub(r"<[^>]+>", "", r.get("title") or "untitled"),
                    "year": r.get("pubYear"),
                    "doi": doi,
                    "urls": [
                        f"https://europepmc.org/articles/{pmcid}?pdf=render",
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",
                    ],
                }
            )
        time.sleep(0.2)
    return out


def crossref(issn, rows=40):
    url = (
        f"https://api.crossref.org/journals/{urllib.parse.quote(issn)}/works?"
        + urllib.parse.urlencode(
            {
                "rows": rows,
                "select": "DOI,title,issued,link,URL,published-print,published-online",
                "mailto": MAILTO,
            }
        )
    )
    try:
        payload = http_json(url, timeout=70)
    except Exception as e:
        print("  crossref", e)
        return []
    out = []
    for it in ((payload.get("message") or {}).get("items") or []):
        doi = (it.get("DOI") or "").lower()
        title = " ".join(it.get("title") or ["untitled"])
        year = None
        for k in ("published-print", "published-online", "issued"):
            parts = ((it.get(k) or {}).get("date-parts") or [[None]])[0]
            if parts and parts[0]:
                year = parts[0]
                break
        urls = []
        for link in it.get("link") or []:
            u = link.get("URL") or ""
            ct = (link.get("content-type") or "").lower()
            if "pdf" in ct or u.lower().endswith(".pdf") or "pdf" in u.lower():
                if any(a in u.lower() for a in ALLOW_SUBSTR) or "unpaywall" in u.lower() or "repository" in u.lower():
                    urls.append(u)
        # unpaywall
        if doi:
            urls.append(f"UNPAYWALL:{doi}")
        out.append({"title": title, "year": year, "doi": doi, "urls": urls})
    return out


def unpaywall_pdf(doi: str) -> list[str]:
    url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}"
    try:
        payload = http_json(url, timeout=40)
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
            ul = u.lower()
            # Prefer non-stampPDF hosts first; keep publisher URLs as fallback.
            if "ieeexplore" in ul:
                continue
            if u.endswith(".pdf") or "pdf" in ul or any(
                x in ul for x in ("arxiv", "pmc", "peerj", "thesai", "figshare", "zenodo", "handle.net", "springer")
            ):
                urls.append(u)
            if "arxiv.org/abs/" in u:
                m = re.search(r"arxiv\.org/abs/([0-9.]+)", u)
                if m:
                    urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
            if "sciencedirect.com/science/article/pii/" in ul and "/pdfft" not in ul:
                urls.append(u.rstrip("/") + "/pdfft?isDTMRedir=true&download=true")
            if "mdpi.com/" in ul and "/pdf" not in ul:
                urls.append(u.rstrip("/") + "/pdf")
    # rank: repositories before publisher stampPDF
    def rank(u: str) -> int:
        ul = u.lower()
        if any(x in ul for x in ("arxiv", "europepmc", "pmc.ncbi", "zenodo", "figshare", "handle.net", "peerj", "thesai")):
            return 0
        if "sciencedirect" in ul or "springer" in ul:
            return 1
        if "mdpi.com" in ul or "wiley.com" in ul:
            return 2
        return 3

    return list(dict.fromkeys(sorted(urls, key=rank)))


def openalex_by_issn(issn, per=100):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "filter": f"primary_location.source.issn:{issn},is_oa:true,type:article",
            "per_page": per,
            "sort": "cited_by_count:desc",
            "mailto": MAILTO,
        }
    )
    try:
        payload = http_json(url, timeout=50)
    except Exception as e:
        print("  openalex", e)
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
                if "europepmc.org/articles/" in u or "pmc.ncbi.nlm.nih.gov" in u:
                    m2 = re.search(r"(PMC\d+)", u, re.I)
                    if m2:
                        pmc = m2.group(1).upper()
                        urls.append(f"https://europepmc.org/articles/{pmc}?pdf=render")
                        urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/")
                if "peerj.com/articles/" in u:
                    m3 = re.search(r"/articles/(\d+)", u)
                    if m3:
                        urls.append(f"https://peerj.com/articles/{m3.group(1)}.pdf")
                if "thesai.org" in u and u.lower().endswith(".pdf"):
                    urls.append(u)
                if any(x in u.lower() for x in ("zenodo.org", "figshare.com", "hdl.handle.net")):
                    urls.append(u)
                if u.lower().endswith(".pdf"):
                    urls.append(u)
                if "sciencedirect.com/science/article/pii/" in u.lower():
                    urls.append(u.rstrip("/") + "/pdfft?isDTMRedir=true&download=true")
                if "mdpi.com/" in u.lower() and "/pdf" not in u.lower():
                    urls.append(u.rstrip("/") + "/pdf")
        # Unpaywall resolved lazily in topup() — avoid N API calls up-front.
        urls = list(dict.fromkeys(urls))
        if not urls and not doi:
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


def ijacsa_seed():
    """Try recent IJACSA volume PDF index pages via Crossref DOIs 10.14569/IJACSA.*"""
    out = []
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {
            "filter": "issn:2156-5570,from-pub-date:2022",
            "rows": 30,
            "mailto": MAILTO,
            "select": "DOI,title,issued,link",
        }
    )
    try:
        payload = http_json(url, timeout=60)
    except Exception as e:
        print("  ijacsa crossref", e)
        return []
    for it in ((payload.get("message") or {}).get("items") or []):
        doi = (it.get("DOI") or "").lower()
        title = " ".join(it.get("title") or ["untitled"])
        urls = []
        # common SAI pattern guesses from DOI
        # e.g. 10.14569/IJACSA.2024.0150101
        m = re.search(r"ijacsa\.(\d{4})\.(\d+)\.(\d+)", doi, re.I)
        if m:
            year, vol, art = m.group(1), m.group(2), m.group(3)
            # Papers often at:
            urls.append(f"https://thesai.org/Downloads/Volume{int(vol)}/Paper_{int(art[-2:]) if False else ''}")
        for link in it.get("link") or []:
            u = link.get("URL") or ""
            if "thesai.org" in u:
                urls.append(u)
        urls.append(f"UNPAYWALL:{doi}")
        # DOI content negotiation for PDF
        urls.append(f"DOIPDF:{doi}")
        out.append({"title": title, "year": None, "doi": doi, "urls": urls})
    return out


def expand_urls(item, resolve_unpaywall: bool = False):
    urls = []
    for u in item.get("urls") or []:
        if u.startswith("UNPAYWALL:"):
            if resolve_unpaywall:
                urls.extend(unpaywall_pdf(u.split(":", 1)[1]))
                time.sleep(0.15)
        elif u.startswith("DOIPDF:"):
            continue
        else:
            urls.append(u)
    if resolve_unpaywall and item.get("doi"):
        extra = unpaywall_pdf(item["doi"])
        urls.extend(extra)
        if extra:
            time.sleep(0.15)
    good = []
    for u in urls:
        ul = u.lower()
        if "ieeexplore.ieee.org" in ul:
            continue
        good.append(u)
    return list(dict.fromkeys(good))


def title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())[:48]


def stem_title_key(stem: str) -> str:
    parts = stem.split("__")
    if len(parts) >= 3:
        return title_key(parts[2])
    return title_key(stem)


def existing_keys(slug: str) -> tuple[set[str], set[str]]:
    titles: set[str] = set()
    hashes: set[str] = set()
    for p in existing(slug):
        titles.add(stem_title_key(p.stem))
        parts = p.stem.split("__")
        if parts:
            hashes.add(parts[-1].lower())
    return titles, hashes


def try_download_urls(urls: list[str], path: Path, max_try: int = 6) -> tuple[bool, str, str]:
    for u in urls[:max_try]:
        if u.startswith("https://doi.org/"):
            continue
        ok, info = download(u, path)
        if ok:
            used = u if isinstance(info, str) and str(info).startswith("http") else u
            return True, info, used
        time.sleep(0.05)
    return False, "fail", ""


def topup(slug, issn):
    have = existing(slug)
    print(f"\n=== TOPUP {slug} existing={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have), []
    cands = []
    print("  fetching europepmc...", flush=True)
    cands.extend(epmc(issn, pages=8))
    time.sleep(0.3)
    print("  fetching openalex...", flush=True)
    cands.extend(openalex_by_issn(issn, per=80))
    time.sleep(0.5)
    print("  fetching crossref...", flush=True)
    if slug == "ijacsa":
        cands.extend(ijacsa_seed())
    else:
        cands.extend(crossref(issn, rows=60))
    seen = set()
    uniq = []
    for c in cands:
        k = title_key(c["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(c)

    def score(c):
        urls = c.get("urls") or []
        direct = sum(
            1
            for u in urls
            if (not u.startswith("UNPAYWALL:"))
            and any(
                x in u.lower()
                for x in ("arxiv", "europepmc", "pmc.ncbi", "peerj", "zenodo", "figshare", ".pdf")
            )
        )
        return -direct

    uniq.sort(key=score)
    print(f"  candidates: {len(uniq)}", flush=True)
    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    have_t, have_h = existing_keys(slug)
    rows = []
    success = len(have)
    tried = 0
    for c in uniq:
        if success >= TARGET:
            break
        tkey = title_key(c["title"])
        if tkey in have_t:
            continue
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        if h in have_h:
            have_t.add(tkey)
            continue
        urls = expand_urls(c, resolve_unpaywall=False)
        if not urls:
            urls = expand_urls(c, resolve_unpaywall=True)
        if not urls:
            continue
        tried += 1
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        ok, info, used = try_download_urls(urls, path)
        if not ok and c.get("doi"):
            more = expand_urls(c, resolve_unpaywall=True)
            more = [u for u in more if u not in urls]
            if more:
                ok, info, used = try_download_urls(more, path, max_try=4)
        if ok and info == "exists":
            have_t.add(tkey)
            have_h.add(h)
            continue
        if ok:
            success += 1
            have_t.add(tkey)
            have_h.add(h)
            rows.append(
                {
                    "slug": slug,
                    "title": c["title"],
                    "doi": c.get("doi") or "",
                    "pdf_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "pdf_url": used,
                    "status": "topup",
                }
            )
            print(f"  [{success}/{TARGET}] OK {c['title'][:70]}", flush=True)
        elif tried % 8 == 0:
            print(f"  ...tried {tried}, still {success}/{TARGET}", flush=True)
        time.sleep(0.08)
    print(f"  tried_new={tried} final={success}", flush=True)
    return success, rows


def main():
    all_rows = []
    summary = []
    # also recount OK journals
    for d in sorted(PDF_ROOT.glob("*")):
        if not d.is_dir():
            continue
        n = len(list(d.glob("*.pdf")))
        if d.name in NEED:
            n2, rows = topup(d.name, NEED[d.name])
            all_rows.extend(rows)
            summary.append({"slug": d.name, "pdf_ok": n2, "target": TARGET})
        else:
            summary.append({"slug": d.name, "pdf_ok": n, "target": TARGET})
    # journals in NEED with empty folder
    for slug, issn in NEED.items():
        if not (PDF_ROOT / slug).exists() or slug not in {s["slug"] for s in summary}:
            n2, rows = topup(slug, issn)
            all_rows.extend(rows)
            summary.append({"slug": slug, "pdf_ok": n2, "target": TARGET})

    # rewrite summary
    # unique by slug last
    by = {}
    for s in summary:
        by[s["slug"]] = s
    # recount all dirs accurately
    for d in sorted(PDF_ROOT.glob("*")):
        if d.is_dir():
            by[d.name] = {"slug": d.name, "pdf_ok": len(list(d.glob("*.pdf"))), "target": TARGET}
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "pdf_ok", "target"])
        w.writeheader()
        w.writerows(by.values())
    print("\n=== TOPUP SUMMARY ===")
    for s in sorted(by.values(), key=lambda x: x["slug"]):
        print(f"  [{'OK' if s['pdf_ok'] >= TARGET else 'LOW'}] {s['slug']}: {s['pdf_ok']}/{TARGET}")


if __name__ == "__main__":
    main()
