# -*- coding: utf-8 -*-
"""Fill Machines/KeAi to 10 using cloudscraper (+aria2 fallback) via OpenAlex OA URLs."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import ssl
from pathlib import Path

import cloudscraper

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
PROXY = "http://127.0.0.1:17890"
MAILTO = "powergrid.literature@gmail.com"
TARGET = 10
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

NEED = {
    "mdpi-machines": "2075-1702",
    "keai-unconventional-resources": "2666-5190",
}


def api_json(url: str):
    ctx = ssl.create_default_context()
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    op = urllib.request.build_opener(proxy, urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with op.open(req, timeout=50) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def title_key(t):
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:48]


def is_pdf_bytes(b: bytes) -> bool:
    return b"%PDF" in b[:8192]


def is_pdf_file(p: Path) -> bool:
    return p.exists() and p.stat().st_size > 20000 and is_pdf_bytes(p.read_bytes()[:8192])


def scraper(use_proxy=True):
    s = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    if use_proxy:
        s.proxies = {"http": PROXY, "https": PROXY}
    return s


def download_cf(url: str, dest: Path) -> tuple[bool, str]:
    if is_pdf_file(dest):
        return True, "exists"
    last = "fail"
    headers = {"User-Agent": UA, "Accept": "application/pdf,*/*"}
    if "mdpi.com" in url:
        headers["Referer"] = "https://www.mdpi.com/"
    if "sciencedirect.com" in url:
        headers["Referer"] = "https://www.sciencedirect.com/"
    for use_proxy in (True, False):
        try:
            s = scraper(use_proxy=use_proxy)
            r = s.get(url, headers=headers, timeout=60, allow_redirects=True)
            data = r.content
            if r.status_code >= 400:
                last = f"http{r.status_code}"
                continue
            if not is_pdf_bytes(data):
                last = f"not_pdf:{r.url[:60]}"
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            if dest.stat().st_size < 15000:
                dest.unlink(missing_ok=True)
                last = "small"
                continue
            return True, r.url
        except Exception as e:
            last = str(e)[:120]
    return False, last


def candidates(issn: str):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "filter": f"primary_location.source.issn:{issn},is_oa:true,type:article",
            "per_page": 50,
            "sort": "cited_by_count:desc",
            "mailto": MAILTO,
        }
    )
    payload = api_json(url)
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
                ul = u.lower()
                if "mdpi.com/" in ul:
                    urls.append(u if "/pdf" in ul else u.rstrip("/") + "/pdf")
                if "sciencedirect.com/science/article/pii/" in ul:
                    base = u.split("?")[0].rstrip("/")
                    urls.append(base if base.endswith("/pdf") else base + "/pdf")
                m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                if m:
                    urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
                m2 = re.search(r"(PMC\d+)", u, re.I)
                if m2:
                    pmc = m2.group(1).upper()
                    urls.append(f"https://europepmc.org/articles/{pmc}?pdf=render")
                if ul.endswith(".pdf"):
                    urls.append(u)
        if doi:
            try:
                up = api_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}")
                time.sleep(0.1)
                for loc in [up.get("best_oa_location"), *(up.get("oa_locations") or [])]:
                    if not loc:
                        continue
                    for key in ("url_for_pdf", "url"):
                        u = loc.get(key) or ""
                        if not u:
                            continue
                        ul = u.lower()
                        if "mdpi.com/" in ul:
                            urls.append(u if "/pdf" in ul else u.rstrip("/") + "/pdf")
                        if "sciencedirect.com" in ul and "/pdf" not in ul:
                            urls.append(u.rstrip("/") + "/pdf")
                        elif "pdf" in ul or ul.endswith(".pdf"):
                            urls.append(u)
            except Exception:
                pass
        urls = list(dict.fromkeys(urls))
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


def topup(slug, issn):
    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    have = list(dest.glob("*.pdf"))
    print(f"\n=== CF TOPUP {slug} have={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have)
    have_t = set()
    for p in have:
        parts = p.stem.split("__")
        if len(parts) >= 3:
            have_t.add(title_key(parts[2]))
    cands = candidates(issn)
    print(f"  cands={len(cands)}", flush=True)
    success = len(have)
    tried = 0
    for c in cands:
        if success >= TARGET:
            break
        tkey = title_key(c["title"])
        if tkey in have_t:
            continue
        tried += 1
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        for u in c["urls"][:6]:
            ok, info = download_cf(u, path)
            if ok and info != "exists":
                success += 1
                have_t.add(tkey)
                print(f"  [{success}/{TARGET}] {c['title'][:70]}", flush=True)
                print(f"       {u[:100]}", flush=True)
                break
            if ok and info == "exists":
                have_t.add(tkey)
                break
        if tried % 5 == 0 and success < TARGET:
            print(f"  …tried {tried} still {success}/{TARGET}", flush=True)
        time.sleep(0.2)
    print(f"  final={success} tried={tried}", flush=True)
    return success


def main():
    # quick probe
    print("probe mdpi…", flush=True)
    probe = PDF_ROOT / "_probe" / "cf_mdpi.pdf"
    probe.parent.mkdir(parents=True, exist_ok=True)
    ok, info = download_cf("https://www.mdpi.com/2075-1702/11/7/677/pdf", probe)
    print("  mdpi", ok, info, "size", probe.stat().st_size if probe.exists() else 0, flush=True)
    if probe.exists() and not ok:
        probe.unlink(missing_ok=True)

    print("probe sciencedirect…", flush=True)
    probe2 = PDF_ROOT / "_probe" / "cf_keai.pdf"
    ok2, info2 = download_cf(
        "https://www.sciencedirect.com/science/article/pii/S2666519022000024/pdf", probe2
    )
    print("  sd", ok2, info2, "size", probe2.stat().st_size if probe2.exists() else 0, flush=True)
    if probe2.exists() and not ok2:
        probe2.unlink(missing_ok=True)

    for slug, issn in NEED.items():
        topup(slug, issn)
    for slug in NEED:
        print("COUNT", slug, len(list((PDF_ROOT / slug).glob("*.pdf"))), flush=True)


if __name__ == "__main__":
    main()
