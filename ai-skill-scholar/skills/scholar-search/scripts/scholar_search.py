#!/usr/bin/env python3
"""Search scholarly works via OpenAlex and return structured JSON.

OpenAlex (https://openalex.org) is a free, open catalog of 250M+ scholarly
works with citation counts, references, authors, venues, DOIs, and open-access
PDF links. No API key required. Set OPENALEX_EMAIL to join the "polite pool"
(higher rate limits + priority routing).

Usage:
    python scholar_search.py "query terms" [--limit 25] [--year 2024-2026] \\
        [--venue "ICLR"] [--concepts "Machine learning"] \\
        [--min-citations 10] [--open-access]

Output: JSON on stdout with {query, count, results: [...]}.
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
USER_AGENT_BASE = "ai-skill-scholar-search/1.0"
MIN_INTERVAL_SECONDS = 0.2  # polite-pool limit is 10 req/s; 5 req/s is safe
HTTP_TIMEOUT = 30

CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    / "ai-skill-scholar"
)
_LAST_CALL_FILE = CACHE_ROOT / ".last_call.timestamp"

# Fields we want — keeping this list narrow keeps payloads small.
DEFAULT_SELECT = [
    "id", "title", "publication_year", "publication_date", "cited_by_count",
    "authorships", "ids", "doi", "open_access", "primary_location",
    "abstract_inverted_index", "referenced_works", "type", "concepts",
]


# --------------------------------------------------------------------------- #
# Rate limit cooperation (file-based, cross-process)
# --------------------------------------------------------------------------- #

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
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        print(f"[openalex] request failed: {e}", file=sys.stderr)
        return 0, None


# --------------------------------------------------------------------------- #
# Response shaping
# --------------------------------------------------------------------------- #

def reconstruct_abstract(inv_idx: dict | None) -> str:
    """OpenAlex stores abstracts as {word: [positions,...]}. Rebuild word order."""
    if not inv_idx:
        return ""
    slots: list[tuple[int, str]] = []
    for word, positions in inv_idx.items():
        for p in positions:
            slots.append((p, word))
    slots.sort()
    return " ".join(w for _, w in slots)


_ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.(\S+?)(?:v\d+)?$", re.IGNORECASE)
_ARXIV_URL_RE = re.compile(r"arxiv\.org/abs/([^\s?#/]+)")


def _extract_arxiv_id(work: dict) -> str | None:
    """Detect arXiv submissions across several OpenAlex fields."""
    # Primary: arXiv's DOI convention
    doi = (work.get("doi") or "").lower()
    m = _ARXIV_DOI_RE.search(doi) if doi else None
    if m:
        return m.group(1)
    # Fallback: primary_location source identifies arXiv
    pl = work.get("primary_location") or {}
    source = pl.get("source") or {}
    if (source.get("display_name") or "").lower() == "arxiv":
        landing = pl.get("landing_page_url") or ""
        m = _ARXIV_URL_RE.search(landing)
        if m:
            return m.group(1)
    return None


def _strip_prefix(url: str | None, prefix: str) -> str | None:
    if not url:
        return None
    return url.removeprefix(prefix) if url.startswith(prefix) else url


def normalize_work(raw: dict) -> dict:
    ids = raw.get("ids") or {}
    pl = raw.get("primary_location") or {}
    source = pl.get("source") or {}
    oa = raw.get("open_access") or {}
    concepts = raw.get("concepts") or []
    # OpenAlex concepts are level-ranked; keep first two levels worth of topics
    top_concepts = [c.get("display_name") for c in concepts[:5] if c.get("display_name")]
    return {
        "paper_id": _strip_prefix(raw.get("id"), "https://openalex.org/"),
        "openalex_id": raw.get("id"),
        "title": raw.get("title") or "",
        "authors": [
            (a.get("author") or {}).get("display_name", "")
            for a in (raw.get("authorships") or [])
        ],
        "author_ids": [
            _strip_prefix((a.get("author") or {}).get("id"), "https://openalex.org/")
            for a in (raw.get("authorships") or [])
        ],
        "year": raw.get("publication_year"),
        "publication_date": raw.get("publication_date"),
        "venue": source.get("display_name") or "",
        "work_type": raw.get("type"),
        "citation_count": raw.get("cited_by_count"),
        "reference_count": len(raw.get("referenced_works") or []),
        "abstract": reconstruct_abstract(raw.get("abstract_inverted_index")),
        # OpenAlex has no TLDR field; 'concepts' are the closest "topic" signal
        "concepts": top_concepts,
        "arxiv_id": _extract_arxiv_id(raw),
        "doi": _strip_prefix(raw.get("doi"), "https://doi.org/") or None,
        "pmid": _strip_prefix(ids.get("pmid"), "https://pubmed.ncbi.nlm.nih.gov/"),
        "mag": ids.get("mag"),
        "is_open_access": oa.get("is_oa"),
        "open_access_pdf": oa.get("oa_url") or "",
        "landing_url": pl.get("landing_page_url") or "",
        "openalex_url": raw.get("id"),
    }


# --------------------------------------------------------------------------- #
# Query construction
# --------------------------------------------------------------------------- #

def build_filters(
    year: str | None,
    venue: str | None,
    concepts: str | None,
    min_citations: int | None,
    open_access_only: bool,
) -> str:
    filters: list[str] = []
    if year:
        if "-" in year:
            lo, hi = year.split("-", 1)
            filters.append(f"from_publication_date:{lo}-01-01")
            filters.append(f"to_publication_date:{hi}-12-31")
        else:
            filters.append(f"from_publication_date:{year}-01-01")
            filters.append(f"to_publication_date:{year}-12-31")
    if venue:
        # display_name.search does case-insensitive partial match
        filters.append(
            f"primary_location.source.display_name.search:{venue}"
        )
    if concepts:
        filters.append(f"concepts.display_name.search:{concepts}")
    if min_citations is not None:
        filters.append(f"cited_by_count:>{max(0, min_citations - 1)}")
    if open_access_only:
        filters.append("is_oa:true")
    return ",".join(filters)


def build_search_url(
    query: str,
    limit: int,
    filters: str,
    select: list[str],
) -> str:
    params = {
        "search": query,
        "per_page": str(min(200, max(1, limit))),
        "select": ",".join(select),
        "sort": "relevance_score:desc",
    }
    if filters:
        params["filter"] = filters
    return f"{API_BASE}/works?{urllib.parse.urlencode(params)}"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search scholarly works via OpenAlex."
    )
    parser.add_argument("query", help="Free-text search query")
    parser.add_argument("--limit", type=int, default=25,
                        help="Max results (1-200; default 25)")
    parser.add_argument("--year", help="Year range, e.g. 2022-2026 or 2024")
    parser.add_argument("--venue",
                        help="Venue name (partial/case-insensitive match), e.g. 'ICLR'")
    parser.add_argument("--concepts",
                        help="OpenAlex concept name, e.g. 'Machine learning'")
    parser.add_argument("--min-citations", type=int)
    parser.add_argument("--open-access", action="store_true")
    args = parser.parse_args()

    filters = build_filters(
        args.year, args.venue, args.concepts, args.min_citations, args.open_access
    )
    url = build_search_url(args.query, args.limit, filters, DEFAULT_SELECT)

    status, payload = _http_get_json(url)
    if status != 200 or payload is None:
        print(f"error: search failed (HTTP {status})", file=sys.stderr)
        return 4

    meta = payload.get("meta") or {}
    raw_results = payload.get("results") or []
    results = [normalize_work(r) for r in raw_results]

    print(json.dumps({
        "query": args.query,
        "total_count": meta.get("count"),
        "page": meta.get("page"),
        "per_page": meta.get("per_page"),
        "count": len(results),
        "results": results,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
