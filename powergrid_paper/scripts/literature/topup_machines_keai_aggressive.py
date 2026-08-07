# -*- coding: utf-8 -*-
"""Aggressive top-up for Machines/KeAi: aria2 with/without proxy + repo mirrors."""
from __future__ import annotations

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
PROXY = "http://127.0.0.1:17890"
ARIA2 = Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
    else:
        h.append(urllib.request.ProxyHandler({}))
    h.append(urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    return urllib.request.build_opener(*h)


def http_json(url, timeout=50, use_proxy=True):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with opener(use_proxy).open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def is_pdf(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > 15000 and b"%PDF" in path.read_bytes()[:8192]
    except Exception:
        return False


def slugify(t, n=55):
    return (re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_")[:n] or "paper").lower()


def title_key(t):
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:48]


def aria2_get(url: str, dest: Path, use_proxy: bool, referer: str = "") -> bool:
    if is_pdf(dest):
        return True
    if dest.exists():
        dest.unlink(missing_ok=True)
    cmd = [
        str(ARIA2),
        "-x", "8",
        "-s", "8",
        "--max-tries=2",
        "--timeout=35",
        "--connect-timeout=15",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--check-certificate=false",
        "-d", str(dest.parent),
        "-o", dest.name,
        f"--user-agent={UA}",
        "--header=Accept: application/pdf,*/*",
    ]
    if use_proxy:
        cmd.append(f"--all-proxy={PROXY}")
    if referer:
        cmd.append(f"--header=Referer: {referer}")
    cmd.append(url)
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except Exception:
        return False
    if is_pdf(dest):
        return True
    dest.unlink(missing_ok=True)
    return False


def s2_pdf(doi: str) -> list[str]:
    urls = []
    try:
        data = http_json(
            f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi)}"
            f"?fields=title,openAccessPdf,externalIds",
            timeout=30,
        )
        pdf = (data.get("openAccessPdf") or {}).get("url") or ""
        if pdf:
            urls.append(pdf)
    except Exception:
        pass
    return urls


def openalex_with_repos(issn: str, per=100):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "filter": f"primary_location.source.issn:{issn},is_oa:true,type:article",
            "per_page": per,
            "sort": "cited_by_count:desc",
            "mailto": MAILTO,
        }
    )
    payload = http_json(url)
    out = []
    for w in payload.get("results") or []:
        urls = []
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        for loc in [w.get("best_oa_location"), *(w.get("locations") or [])]:
            if not loc:
                continue
            host = ((loc.get("source") or {}).get("host_organization_name") or "")
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
                # keep repository / institutional
                ul = u.lower()
                if any(
                    x in ul
                    for x in (
                        "repository",
                        "handle.net",
                        "figshare",
                        "zenodo",
                        "researchgate",
                        ".edu/",
                        "ac.uk",
                        "hal.",
                        "osf.io",
                        "preprints",
                    )
                ):
                    urls.append(u)
                if ul.endswith(".pdf"):
                    urls.append(u)
                if "mdpi.com/" in ul:
                    urls.append(u if "/pdf" in ul else u.rstrip("/") + "/pdf")
                if "sciencedirect.com/science/article/pii/" in ul:
                    base = u.split("?")[0].rstrip("/")
                    urls.append(base if base.endswith("/pdf") else base + "/pdf")
        if doi:
            urls.extend(s2_pdf(doi))
            time.sleep(0.15)
            # unpaywall all locations
            try:
                up = http_json(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAILTO}", timeout=25)
                time.sleep(0.1)
                for loc in up.get("oa_locations") or []:
                    for key in ("url_for_pdf", "url"):
                        u = loc.get(key) or ""
                        if not u:
                            continue
                        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
                        if m:
                            urls.append(f"https://arxiv.org/pdf/{m.group(1)}.pdf")
                        if u.lower().endswith(".pdf") or "pdf" in u.lower() or "handle.net" in u.lower():
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
    print(f"\n=== {slug} have={len(have)} ===", flush=True)
    if len(have) >= TARGET:
        return len(have)
    have_t = set()
    for p in have:
        parts = p.stem.split("__")
        if len(parts) >= 3:
            have_t.add(title_key(parts[2]))
    print("  openalex+s2+unpaywall…", flush=True)
    cands = openalex_with_repos(issn, per=80)
    seen, uniq = set(), []
    for c in cands:
        k = title_key(c["title"])
        if k and k not in seen:
            seen.add(k)
            uniq.append(c)
    print(f"  uniq={len(uniq)}", flush=True)
    success = len(have)
    for c in uniq:
        if success >= TARGET:
            break
        tkey = title_key(c["title"])
        if tkey in have_t:
            continue
        h = hashlib.sha1((c.get("doi") or c["title"]).encode()).hexdigest()[:10]
        path = dest / f"{slug}__{c.get('year') or 'noyear'}__{slugify(c['title'])}__{h}.pdf"
        for u in (c.get("urls") or [])[:10]:
            if u.startswith("https://doi.org/"):
                continue
            ref = ""
            if "mdpi.com" in u:
                ref = "https://www.mdpi.com/"
            if "sciencedirect" in u:
                ref = "https://www.sciencedirect.com/"
            # try proxy then direct
            for use_proxy in (True, False):
                if aria2_get(u, path, use_proxy=use_proxy, referer=ref):
                    success += 1
                    have_t.add(tkey)
                    print(f"  [{success}/{TARGET}] {c['title'][:70]}", flush=True)
                    print(f"       {u[:100]} proxy={use_proxy}", flush=True)
                    break
            else:
                continue
            break
        time.sleep(0.05)
    print(f"  final={success}", flush=True)
    return success


def main():
    for slug, issn in NEED.items():
        topup(slug, issn)
    for slug in NEED:
        n = len(list((PDF_ROOT / slug).glob("*.pdf")))
        print(f"COUNT {slug}: {n}")


if __name__ == "__main__":
    main()
