# -*- coding: utf-8 -*-
"""Top-up journals still below 10 PDFs using aria2c + proxy."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import ssl
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_ROOT = ROOT / "papers/literature/target_journal_related/fulltext_by_journal"
META = ROOT / "papers/literature/target_journal_related/metadata"
SUMMARY = META / "journal_fulltext_summary.csv"
PROXY = "http://127.0.0.1:17890"
ARIA2 = Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
TARGET = 10
MAILTO = "powergrid.literature@gmail.com"

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


def http_json(url, timeout=50):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with opener(True).open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def is_pdf(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > 20000 and b"%PDF" in path.read_bytes()[:8192]
    except Exception:
        return False


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def title_key(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:48]


def aria2_download(url: str, dest: Path, referer: str = "") -> tuple[bool, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if is_pdf(dest):
        return True, "exists"
    tmp = dest.with_suffix(".part.pdf")
    if tmp.exists():
        tmp.unlink(missing_ok=True)
    headers = [f"User-Agent: {UA}", "Accept: application/pdf,*/*"]
    if referer:
        headers.append(f"Referer: {referer}")
    cmd = [
        str(ARIA2),
        "-x", "4",
        "-s", "4",
        "-k", "1M",
        "--max-tries=3",
        "--retry-wait=2",
        "--timeout=40",
        "--connect-timeout=20",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        f"--all-proxy={PROXY}",
        "-d", str(dest.parent),
        "-o", dest.name,
    ]
    for h in headers:
        cmd.extend(["--header", h])
    cmd.append(url)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return False, str(e)[:120]
    if is_pdf(dest):
        return True, url
    # cleanup non-pdf
    if dest.exists():
        head = dest.read_bytes()[:200]
        dest.unlink(missing_ok=True)
        return False, f"not_pdf:{head[:40]!r}"
    err = (p.stderr or p.stdout or "")[-200:]
    return False, err.replace("\n", " ")[:160]


def epmc(issn: str, pages: int = 20):
    out, seen = [], set()
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
            print("  epmc", e, flush=True)
            break
        results = ((payload.get("resultList") or {}).get("result")) or []
        if not results:
            break
        for r in results:
            pmcid = r.get("pmcid")
            if not pmcid:
                continue
            doi = (r.get("doi") or "").lower()
            title = re.sub(r"<[^>]+>", "", r.get("title") or "untitled")
            key = doi or pmcid
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "title": title,
                    "year": r.get("pubYear"),
                    "doi": doi,
                    "urls": [
                        f"https://europepmc.org/articles/{pmcid}?pdf=render",
                        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",
                    ],
                }
            )
        time.sleep(0.12)
    return out


def openalex(issn: str, per: int = 100):
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
        print("  openalex", e, flush=True)
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
                if "sciencedirect.com/science/article/pii/" in u.lower():
                    # try both /pdf and /pdfft
                    base = u.split("?")[0].rstrip("/")
                    if base.endswith("/pdf"):
                        urls.append(base)
                        urls.append(base + "ft?isDTMRedir=true&download=true")
                    else:
                        urls.append(base + "/pdf")
                        urls.append(base + "/pdfft?isDTMRedir=true&download=true")
                if "mdpi.com/" in u.lower():
                    if "/pdf" not in u.lower():
                        urls.append(u.rstrip("/") + "/pdf")
                    else:
                        urls.append(u)
                if u.lower().endswith(".pdf") or "pdf" in u.lower():
                    urls.append(u)
                if any(x in u.lower() for x in ("zenodo.org", "figshare.com", "peerj.com")):
                    urls.append(u)
        # unpaywall
        if doi:
            try:
                up = http_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}", timeout=30)
                time.sleep(0.12)
                for loc in [up.get("best_oa_location"), *(up.get("oa_locations") or [])]:
                    if not loc:
                        continue
                    for key in ("url_for_pdf", "url"):
                        u = loc.get(key) or ""
                        if not u:
                            continue
                        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                        if m:
                            urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
                        if "sciencedirect.com" in u.lower() and "/pdf" not in u.lower():
                            urls.append(u.rstrip("/") + "/pdf")
                        elif u.lower().endswith(".pdf") or "pdf" in u.lower():
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


def referer_for(url: str) -> str:
    ul = url.lower()
    if "sciencedirect.com" in ul:
        return "https://www.sciencedirect.com/"
    if "mdpi.com" in ul:
        return "https://www.mdpi.com/"
    if "europepmc.org" in ul:
        return "https://europepmc.org/"
    if "arxiv.org" in ul:
        return "https://arxiv.org/"
    return ""


def existing_keys(slug: str) -> set[str]:
    d = PDF_ROOT / slug
    keys = set()
    if not d.exists():
        return keys
    for p in d.glob("*.pdf"):
        parts = p.stem.split("__")
        if len(parts) >= 3:
            keys.add(title_key(parts[2]))
    return keys


def topup(slug: str, issn: str) -> int:
    dest = PDF_ROOT / slug
    dest.mkdir(parents=True, exist_ok=True)
    have = list(dest.glob("*.pdf"))
    print(f"\n=== ARIA2 TOPUP {slug} existing={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have)
    print("  fetching candidates…", flush=True)
    cands = epmc(issn) + openalex(issn)
    seen, uniq = set(), []
    for c in cands:
        k = title_key(c["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    # prefer non-publisher hosts first
    def score(c):
        s = 0
        for u in c.get("urls") or []:
            ul = u.lower()
            if any(x in ul for x in ("arxiv", "europepmc", "pmc.ncbi", "zenodo", "figshare", "peerj")):
                s += 5
            elif "sciencedirect" in ul or "mdpi.com" in ul:
                s += 1
        return -s

    uniq.sort(key=score)
    print(f"  candidates={len(uniq)}", flush=True)
    have_t = existing_keys(slug)
    success = len(have)
    tried = 0
    for c in uniq:
        if success >= TARGET:
            break
        tkey = title_key(c["title"])
        if tkey in have_t:
            continue
        urls = c.get("urls") or []
        if not urls:
            continue
        tried += 1
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        ok = False
        for u in urls[:8]:
            # skip pure landing pages without pdf hint
            if u.startswith("https://doi.org/"):
                continue
            ref = referer_for(u)
            ok, info = aria2_download(u, path, referer=ref)
            if ok and info != "exists":
                success += 1
                have_t.add(tkey)
                print(f"  [{success}/{TARGET}] OK {c['title'][:70]}", flush=True)
                print(f"       via {u[:90]}", flush=True)
                break
            if ok and info == "exists":
                have_t.add(tkey)
                break
            time.sleep(0.05)
        if tried % 10 == 0 and success < TARGET:
            print(f"  …tried {tried} still {success}/{TARGET}", flush=True)
        time.sleep(0.1)
    print(f"  done tried={tried} final={success}", flush=True)
    return success


def rewrite_summary():
    rows = []
    for d in sorted(PDF_ROOT.glob("*")):
        if d.is_dir():
            rows.append({"slug": d.name, "pdf_ok": len(list(d.glob("*.pdf"))), "target": TARGET})
    META.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "pdf_ok", "target"])
        w.writeheader()
        w.writerows(rows)
    print("\n=== SUMMARY ===", flush=True)
    for r in rows:
        flag = "OK" if r["pdf_ok"] >= TARGET else "LOW"
        print(f"  [{flag}] {r['slug']}: {r['pdf_ok']}/{TARGET}", flush=True)


def main():
    if not ARIA2.exists():
        raise SystemExit(f"aria2c not found: {ARIA2}")
    for slug, issn in NEED.items():
        topup(slug, issn)
    rewrite_summary()


if __name__ == "__main__":
    main()
