#!/usr/bin/env python3
"""Fetch the citation graph for a paper via OpenAlex.

OpenAlex (https://openalex.org) — free, no API key required.

Two views:
  - references: the papers THIS paper cites (what preceded it)
  - citations: the papers that cite THIS paper (what built on it)

Paper IDs accept: OpenAlex work ID (W...), DOI, arXiv ID (auto-converted to
arXiv's DOI), PMID (as pmid:<n>), or any OpenAlex/DOI URL.

Usage:
    python scholar_citations.py references <id> [--limit 100] [--min-year 2020]
    python scholar_citations.py citations  <id> [--limit 100] [--min-year 2020]
    python scholar_citations.py both       <id> [--limit 50]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.openalex.org"
USER_AGENT_BASE = "ai-skill-scholar-citations/1.0"
MIN_INTERVAL_SECONDS = 0.2
HTTP_TIMEOUT = 30

CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    / "ai-skill-scholar"
)
_LAST_CALL_FILE = CACHE_ROOT / ".last_call.timestamp"

DEFAULT_SELECT = [
    "id", "title", "publication_year", "publication_date", "cited_by_count",
    "authorships", "doi", "open_access", "primary_location",
    "abstract_inverted_index", "type",
]

_ARXIV_RE = re.compile(
    r"^(?:\d{4}\.\d{4,5}(v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(v\d+)?)$"
)
_ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.(\S+?)(?:v\d+)?$", re.IGNORECASE)
_ARXIV_URL_RE = re.compile(r"arxiv\.org/abs/([^\s?#/]+)")


def normalize_paper_id(raw: str) -> str:
    """Canonicalize the user-supplied id for an OpenAlex /works/<id> path."""
    s = raw.strip()
    # OpenAlex URL
    m = re.search(r"openalex\.org/(W[0-9A-Z]+)", s, re.IGNORECASE)
    if m:
        return m.group(1)
    # Full DOI URL
    m = re.search(r"doi\.org/(10\.[^\s]+)", s)
    if m:
        return f"doi:{m.group(1)}"
    # Raw "Wxxx" id
    if re.fullmatch(r"W\d+", s, re.IGNORECASE):
        return s.upper()
    # Already-prefixed
    for prefix in ("doi:", "pmid:", "pmcid:", "mag:", "arxiv:"):
        if s.lower().startswith(prefix):
            tail = s[len(prefix):]
            if prefix == "arxiv:":
                return f"doi:10.48550/arxiv.{tail}"
            return f"{prefix}{tail}"
    # Bare DOI (10.xxxx/...)
    if s.startswith("10.") and "/" in s:
        return f"doi:{s}"
    # Bare arxiv id → convert to arxiv's DOI
    if _ARXIV_RE.match(s):
        return f"doi:10.48550/arxiv.{s}"
    # Unknown — pass through and hope
    return s


def _throttle() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    now = time.time()
    try:
        last = float(_LAST_CALL_FILE.read_text().strip())
    except (OSError, ValueError):
        last = 0.0
    wait = MIN_INTERVAL_SECONDS - (now - last)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL_FILE.write_text(f"{time.time():.6f}")


def _user_agent() -> str:
    email = os.environ.get("OPENALEX_EMAIL")
    if email:
        return f"{USER_AGENT_BASE} (mailto:{email})"
    return USER_AGENT_BASE


def _http_get_json(url: str) -> tuple[int, dict | None]:
    _throttle()
    req = urllib.request.Request(
        url, headers={"User-Agent": _user_agent(), "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        print(f"[openalex] request failed: {e}", file=sys.stderr)
        return 0, None


def reconstruct_abstract(inv_idx: dict | None) -> str:
    if not inv_idx:
        return ""
    slots = []
    for word, positions in inv_idx.items():
        for p in positions:
            slots.append((p, word))
    slots.sort()
    return " ".join(w for _, w in slots)


def _extract_arxiv_id(work: dict) -> str | None:
    doi = (work.get("doi") or "").lower()
    m = _ARXIV_DOI_RE.search(doi) if doi else None
    if m:
        return m.group(1)
    pl = work.get("primary_location") or {}
    source = pl.get("source") or {}
    if (source.get("display_name") or "").lower() == "arxiv":
        m = _ARXIV_URL_RE.search(pl.get("landing_page_url") or "")
        if m:
            return m.group(1)
    return None


def _strip_prefix(s: str | None, prefix: str) -> str | None:
    if not s:
        return None
    return s.removeprefix(prefix) if s.startswith(prefix) else s


def normalize_work(raw: dict) -> dict:
    pl = raw.get("primary_location") or {}
    source = pl.get("source") or {}
    oa = raw.get("open_access") or {}
    return {
        "paper_id": _strip_prefix(raw.get("id"), "https://openalex.org/"),
        "title": raw.get("title") or "",
        "authors": [
            (a.get("author") or {}).get("display_name", "")
            for a in (raw.get("authorships") or [])
        ],
        "year": raw.get("publication_year"),
        "publication_date": raw.get("publication_date"),
        "venue": source.get("display_name") or "",
        "citation_count": raw.get("cited_by_count"),
        "abstract": reconstruct_abstract(raw.get("abstract_inverted_index")),
        "arxiv_id": _extract_arxiv_id(raw),
        "doi": _strip_prefix(raw.get("doi"), "https://doi.org/"),
        "open_access_pdf": oa.get("oa_url") or "",
        "openalex_url": raw.get("id"),
    }


def fetch_single(work_id: str) -> dict | None:
    """Fetch a single work (to get its referenced_works list or id)."""
    url = f"{API_BASE}/works/{urllib.parse.quote(work_id, safe=':/')}"
    status, payload = _http_get_json(url)
    if status != 200 or payload is None:
        print(f"error: work fetch failed (HTTP {status})", file=sys.stderr)
        return None
    return payload


def fetch_references(work_id: str, limit: int) -> list[dict]:
    """Fetch the papers THIS paper cites. referenced_works is a list of IDs;
    we batch-resolve them via the works-filter endpoint."""
    root = fetch_single(work_id)
    if root is None:
        return []
    ids = root.get("referenced_works") or []
    ids = ids[:limit]
    if not ids:
        return []

    # Batch-resolve in chunks of 50 ids (OpenAlex filter limit)
    resolved: list[dict] = []
    chunk_size = 50
    select = ",".join(DEFAULT_SELECT)
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        short_ids = [_strip_prefix(w, "https://openalex.org/") for w in chunk]
        filter_val = "openalex_id:" + "|".join(short_ids)
        url = (
            f"{API_BASE}/works?filter={urllib.parse.quote(filter_val)}"
            f"&per_page={len(chunk)}&select={select}"
        )
        status, payload = _http_get_json(url)
        if status == 200 and payload:
            resolved.extend(payload.get("results") or [])
    # Preserve the original reference order
    by_id = {r.get("id"): r for r in resolved}
    ordered = [by_id[w] for w in ids if w in by_id]
    return [normalize_work(r) for r in ordered]


def fetch_citations(work_id: str, limit: int) -> list[dict]:
    """Fetch papers that cite this one, via the cites filter."""
    root = fetch_single(work_id)
    if root is None:
        return []
    target_id = _strip_prefix(root.get("id"), "https://openalex.org/")
    if not target_id:
        return []

    results: list[dict] = []
    cursor: str | None = "*"
    select = ",".join(DEFAULT_SELECT)
    while cursor and len(results) < limit:
        per_page = min(200, limit - len(results))
        params = {
            "filter": f"cites:{target_id}",
            "per_page": str(per_page),
            "select": select,
            "cursor": cursor,
            "sort": "cited_by_count:desc",
        }
        url = f"{API_BASE}/works?{urllib.parse.urlencode(params)}"
        status, payload = _http_get_json(url)
        if status != 200 or not payload:
            break
        results.extend(payload.get("results") or [])
        meta = payload.get("meta") or {}
        cursor = meta.get("next_cursor")
        # Defensive: if no next_cursor we stop
        if not cursor:
            break
    return [normalize_work(r) for r in results[:limit]]


def _filter(papers: list[dict], min_year: int | None, min_citations: int | None) -> list[dict]:
    out = papers
    if min_year is not None:
        out = [p for p in out if (p.get("year") or 0) >= min_year]
    if min_citations is not None:
        out = [p for p in out if (p.get("citation_count") or 0) >= min_citations]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Citation graph via OpenAlex.")
    parser.add_argument("direction", choices=["references", "citations", "both"])
    parser.add_argument("paper_id", help="OpenAlex W-id, DOI, arxiv id, or URL")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--min-year", type=int)
    parser.add_argument("--min-citations", type=int)
    args = parser.parse_args()

    pid = normalize_paper_id(args.paper_id)

    out: dict = {"paper_id": pid}
    if args.direction in ("references", "both"):
        refs = fetch_references(pid, args.limit)
        out["references"] = _filter(refs, args.min_year, args.min_citations)
    if args.direction in ("citations", "both"):
        cits = fetch_citations(pid, args.limit)
        out["citations"] = _filter(cits, args.min_year, args.min_citations)

    if args.direction == "references":
        out["count"] = len(out["references"])
    elif args.direction == "citations":
        out["count"] = len(out["citations"])
    else:
        out["reference_count"] = len(out.get("references") or [])
        out["citation_count"] = len(out.get("citations") or [])

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
