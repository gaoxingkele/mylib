#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paper_ccf — tiny, dependency-free reader for the Paper_CCF venue export.

Lets ANY project consume the Paper_CCF skill's venue knowledge (15 journals + 155
CS conferences) programmatically. No third-party deps (stdlib json only).

Data resolution order (first hit wins):
  1) $PAPER_CCF_DATA            — full path to a venues.json
  2) $PAPER_CCF_HOME/data/venues.json
  3) venues.json next to this file (the global skill install)
  4) ~/.claude/skills/Paper_CCF/data/venues.json  (default global location)

Usage (import):
    import sys; sys.path.insert(0, r"C:\\Users\\10175\\.claude\\skills\\Paper_CCF\\data")
    import paper_ccf
    v = paper_ccf.find("IEEE Access")          # fuzzy by name/acronym/slug
    j = paper_ccf.get("mdpi-energies")         # exact by slug
    fast = paper_ccf.fastest(kind="journal", top=5)
    yml = paper_ccf.to_paper_reviews("ieee-access")   # dict shaped like config/journals/*.yaml

Usage (CLI):
    py paper_ccf.py "IEEE Access"
    py paper_ccf.py --list journals
    py paper_ccf.py --pr ieee-access          # print paper_reviews-shaped mapping
"""
from __future__ import annotations
import json, os, sys, functools

_ENV_DATA = "PAPER_CCF_DATA"
_ENV_HOME = "PAPER_CCF_HOME"
_DEFAULT_HOME = os.path.expanduser(os.path.join("~", ".claude", "skills", "Paper_CCF"))


def data_path() -> str:
    if os.environ.get(_ENV_DATA):
        return os.environ[_ENV_DATA]
    if os.environ.get(_ENV_HOME):
        return os.path.join(os.environ[_ENV_HOME], "data", "venues.json")
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venues.json")
    if os.path.exists(here):
        return here
    return os.path.join(_DEFAULT_HOME, "data", "venues.json")


@functools.lru_cache(maxsize=1)
def load() -> dict:
    p = data_path()
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"venues.json not found at {p}. Set {_ENV_DATA} or {_ENV_HOME}, "
            f"or run build_venues.py in the Paper_CCF/data dir."
        )
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def journals() -> list[dict]:
    return load()["journals"]


def conferences() -> list[dict]:
    return load()["conferences"]


def all_venues() -> list[dict]:
    return journals() + conferences()


def get(slug: str) -> dict | None:
    """Exact match by slug."""
    for v in all_venues():
        if v.get("slug") == slug:
            return v
    return None


def find(query: str) -> dict | None:
    """Fuzzy: exact slug, then acronym (case-insensitive), then substring in name/slug."""
    if not query:
        return None
    q = query.strip().lower()
    v = get(query)
    if v:
        return v
    for v in all_venues():
        if str(v.get("acronym", "")).lower() == q:
            return v
    for v in all_venues():
        if q in v.get("name", "").lower() or q in v.get("slug", "").lower():
            return v
    return None


def search(query: str, limit: int = 10) -> list[dict]:
    """All venues whose name/slug/acronym contains the query."""
    q = query.strip().lower()
    hits = []
    for v in all_venues():
        hay = " ".join(str(v.get(k, "")) for k in ("name", "slug", "acronym", "area")).lower()
        if q in hay:
            hits.append(v)
    return hits[:limit]


def _speed_days(v: dict):
    """Rough numeric review speed (days to first decision) for ranking; None -> +inf."""
    import re
    r = v.get("review") or {}
    s = str(r.get("first_decision") or "")
    m = re.search(r"(\d+)\s*(day|week|month)", s)
    if not m:
        # to_publication fallback
        s2 = str(r.get("to_publication") or "")
        m = re.search(r"(\d+)\s*(day|week|month)", s2)
        if not m:
            return float("inf")
    n = int(m.group(1)); unit = m.group(2)
    return n * {"day": 1, "week": 7, "month": 30}[unit]


def fastest(kind: str = "journal", top: int = 5, power_cs: str | None = None) -> list[dict]:
    """Journals ranked by review speed (fastest first). power_cs filters fit high/medium/low."""
    pool = journals() if kind == "journal" else all_venues()
    if power_cs:
        pool = [v for v in pool if v.get("power_cs_fit") == power_cs]
    return sorted(pool, key=_speed_days)[:top]


def to_paper_reviews(slug: str) -> dict | None:
    """Return the venue mapped to paper_reviews config/journals/<venue>.yaml top-level fields."""
    v = get(slug)
    if not v or v.get("type") != "journal":
        return None
    pr = dict(v.get("paper_reviews") or {})
    # attach author-facing extras paper_reviews' VenueMatch can surface
    pr["apc"] = v.get("apc")
    pr["free_to_publish"] = v.get("free_to_publish")
    pr["review_speed"] = v.get("review")
    pr["metrics"] = v.get("metrics")
    pr["power_cs_fit"] = v.get("power_cs_fit")
    pr["hard_gates"] = v.get("hard_gates")
    pr["desk_reject"] = v.get("desk_reject")
    pr["official_url"] = v.get("official_url")
    pr["_source_profile"] = v.get("profile_path")
    return pr


def _cli(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        kind = argv[1] if len(argv) > 1 else "journals"
        pool = journals() if kind.startswith("j") else conferences()
        for v in pool:
            print(f"{v['slug']:32} {v.get('acronym') or v.get('name')}")
        return 0
    if argv[0] == "--pr":
        d = to_paper_reviews(argv[1])
        print(json.dumps(d, ensure_ascii=False, indent=2) if d else "not a journal / not found")
        return 0 if d else 1
    v = find(" ".join(argv))
    if not v:
        print("not found")
        return 1
    print(json.dumps(v, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
