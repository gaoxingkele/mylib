#!/usr/bin/env python3
"""Orchestrate a two-pass literature review across multiple paper sources.

Workflow (the agent drives the LLM-judgment steps; this script drives the
mechanical state tracking):

  1. init      — create a session folder with the research question
  2. search    — cast a wide net via scholar-search (and optionally arxiv-search)
  3. screen    — agent reads titles/abstracts/tldrs, marks keepers
  4. fetch     — the script lists each keeper's best full-text URL; the agent
                 uses arxiv-analyze (or another reader) to load each one
  5. synthesize — agent writes the final review

Sessions live in ./literature-reviews/<slug>/ by default (overridable). Each
session is a self-contained JSON state machine: state.json, candidates.json,
shortlist.json, final.md.

Usage:
    literature_review.py init "research question" [--out-dir PATH]
    literature_review.py search  <session-dir> [--limit 50] [--year 2022-2026] \\
                                  [--venue ICLR,NeurIPS] [--min-citations 5]
    literature_review.py screen  <session-dir> --include ID1,ID2,...  \\
                                  [--reasons-file path.json]
    literature_review.py fetch   <session-dir>
    literature_review.py status  <session-dir>
    literature_review.py list-sessions [--out-dir PATH]

Full-text resolution priority per paper:
  1. arxiv_id present -> suggest arxiv-analyze (tiered fallback)
  2. open_access_pdf URL present -> suggest the PDF URL
  3. neither -> flag as abstract-only; the agent decides whether to skip
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ---- Locating sibling scripts --------------------------------------------- #

_HERE = Path(__file__).resolve().parent
# sibling skill under skills/
_SCHOLAR_SEARCH = _HERE.parent.parent / "scholar-search" / "scripts" / "scholar_search.py"
# optional: an installed arxiv-search skill (same install root)
_ARXIV_SEARCH_CANDIDATES = [
    _HERE.parent.parent / "arxiv-search" / "scripts" / "arxiv_search.py",
    # common install roots
    Path.home() / ".claude" / "skills" / "arxiv-search" / "scripts" / "arxiv_search.py",
]

DEFAULT_OUT_DIR = Path.cwd() / "literature-reviews"


# ---- Session state -------------------------------------------------------- #

def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or f"review-{int(time.time())}"


def _session_dir(out_dir: Path, slug: str) -> Path:
    return out_dir / slug


def _load_state(session: Path) -> dict:
    state_path = session / "state.json"
    if not state_path.exists():
        print(f"error: no state.json in {session}", file=sys.stderr)
        sys.exit(3)
    return json.loads(state_path.read_text())


def _save_state(session: Path, state: dict) -> None:
    (session / "state.json").write_text(json.dumps(state, indent=2))


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ---- Subcommands ---------------------------------------------------------- #

def cmd_init(args) -> int:
    out_dir = args.out_dir or DEFAULT_OUT_DIR
    slug = _slugify(args.question)
    session = _session_dir(out_dir, slug)
    if session.exists():
        print(f"error: session already exists: {session}", file=sys.stderr)
        return 1
    session.mkdir(parents=True)
    state = {
        "question": args.question,
        "slug": slug,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "initialized",
        "sources_searched": [],
    }
    _save_state(session, state)
    print(json.dumps({"session": str(session), "slug": slug}, indent=2))
    return 0


def _run_json(cmd: list[str]) -> dict | None:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[lit-review] {cmd[1] if len(cmd) > 1 else 'command'} failed: {e}", file=sys.stderr)
        return None
    if res.returncode != 0:
        print(f"[lit-review] command failed (exit {res.returncode}): {res.stderr.strip()}", file=sys.stderr)
        return None
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        print(f"[lit-review] invalid JSON from {cmd[1] if len(cmd) > 1 else 'command'}: {e}", file=sys.stderr)
        return None


def _find_arxiv_search() -> Path | None:
    for p in _ARXIV_SEARCH_CANDIDATES:
        if p.is_file():
            return p
    return None


def _dedup(papers: list[dict]) -> list[dict]:
    """Dedup across sources by (arxiv_id, doi, title-lower)."""
    seen = set()
    out = []
    for p in papers:
        keys = {
            ("arxiv", (p.get("arxiv_id") or "").lower().lstrip("arxiv:")),
            ("doi", (p.get("doi") or "").lower()),
            ("title", re.sub(r"\s+", " ", (p.get("title") or "").lower()).strip()),
        }
        if any(k in seen for k in keys if k[1]):
            continue
        for k in keys:
            if k[1]:
                seen.add(k)
        out.append(p)
    return out


def cmd_search(args) -> int:
    session = Path(args.session_dir).resolve()
    state = _load_state(session)

    all_candidates: list[dict] = []

    # Scholar search (primary)
    if _SCHOLAR_SEARCH.exists():
        cmd = [sys.executable, str(_SCHOLAR_SEARCH), state["question"], "--limit", str(args.limit)]
        if args.year:
            cmd += ["--year", args.year]
        if args.venue:
            cmd += ["--venue", args.venue]
        if args.min_citations is not None:
            cmd += ["--min-citations", str(args.min_citations)]
        payload = _run_json(cmd)
        if payload:
            for r in payload.get("results", []):
                r["_source"] = "scholar"
                all_candidates.append(r)
            state["sources_searched"].append("scholar")
    else:
        print("[lit-review] scholar-search script not found; skipping", file=sys.stderr)

    # arxiv search (optional)
    arxiv_path = _find_arxiv_search()
    if arxiv_path and args.include_arxiv:
        cmd = [sys.executable, str(arxiv_path), state["question"], "--max", str(args.limit)]
        if args.year:
            # arxiv_search expects --from/--to
            if "-" in args.year:
                lo, hi = args.year.split("-", 1)
                cmd += ["--from", f"{lo}-01-01", "--to", f"{hi}-12-31"]
            else:
                cmd += ["--from", f"{args.year}-01-01", "--to", f"{args.year}-12-31"]
        payload = _run_json(cmd)
        if payload:
            # arxiv results have different shape; map to scholar-like
            for r in payload.get("results", []):
                all_candidates.append({
                    "_source": "arxiv",
                    "paper_id": None,
                    "title": r.get("title", ""),
                    "authors": r.get("authors", []),
                    "year": (r.get("published") or "")[:4],
                    "abstract": r.get("abstract", ""),
                    "tldr": "",
                    "arxiv_id": r.get("id"),
                    "doi": r.get("doi"),
                    "open_access_pdf": r.get("pdf_url"),
                    "citation_count": None,
                    "venue": "",
                })
            state["sources_searched"].append("arxiv")

    deduped = _dedup(all_candidates)
    _write_json(session / "candidates.json", {
        "question": state["question"],
        "count": len(deduped),
        "deduped_from": len(all_candidates),
        "results": deduped,
    })
    state["phase"] = "searched"
    state["candidate_count"] = len(deduped)
    _save_state(session, state)

    print(json.dumps({
        "session": str(session),
        "candidates": len(deduped),
        "deduped_from": len(all_candidates),
        "sources": state["sources_searched"],
        "next_step": "screen",
    }, indent=2))
    return 0


def cmd_screen(args) -> int:
    session = Path(args.session_dir).resolve()
    state = _load_state(session)
    candidates_path = session / "candidates.json"
    if not candidates_path.exists():
        print("error: run 'search' first", file=sys.stderr)
        return 1
    candidates = json.loads(candidates_path.read_text())["results"]
    include_ids = set((args.include or "").split(","))
    include_ids.discard("")

    # Accept either S2 paperId, arxiv_id, or DOI as the selector
    def matches(p: dict) -> bool:
        return bool(
            (p.get("paper_id") and p["paper_id"] in include_ids)
            or (p.get("arxiv_id") and p["arxiv_id"] in include_ids)
            or (p.get("doi") and p["doi"] in include_ids)
        )

    reasons: dict = {}
    if args.reasons_file:
        try:
            reasons = json.loads(Path(args.reasons_file).read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(f"warn: couldn't read reasons file: {e}", file=sys.stderr)

    shortlist = []
    for p in candidates:
        if matches(p):
            key = p.get("paper_id") or p.get("arxiv_id") or p.get("doi") or p.get("title")
            p2 = dict(p)
            p2["_include_reason"] = reasons.get(key, "")
            shortlist.append(p2)

    _write_json(session / "shortlist.json", {
        "question": state["question"],
        "count": len(shortlist),
        "results": shortlist,
    })
    state["phase"] = "screened"
    state["shortlist_count"] = len(shortlist)
    _save_state(session, state)

    print(json.dumps({
        "session": str(session),
        "shortlist_count": len(shortlist),
        "dropped": len(candidates) - len(shortlist),
        "next_step": "fetch",
    }, indent=2))
    return 0


def cmd_fetch(args) -> int:
    session = Path(args.session_dir).resolve()
    state = _load_state(session)
    shortlist_path = session / "shortlist.json"
    if not shortlist_path.exists():
        print("error: run 'screen' first", file=sys.stderr)
        return 1
    shortlist = json.loads(shortlist_path.read_text())["results"]

    plan = []
    for p in shortlist:
        entry = {
            "title": p.get("title"),
            "authors": p.get("authors"),
            "year": p.get("year"),
            "paper_id": p.get("paper_id"),
            "arxiv_id": p.get("arxiv_id"),
            "doi": p.get("doi"),
        }
        if p.get("arxiv_id"):
            entry["strategy"] = "arxiv-analyze"
            entry["fetch_hint"] = (
                f"python3 arxiv_fetch.py {p['arxiv_id']}"
            )
        elif p.get("open_access_pdf"):
            entry["strategy"] = "open-access-pdf"
            entry["fetch_hint"] = p["open_access_pdf"]
        else:
            entry["strategy"] = "abstract-only"
            entry["fetch_hint"] = None
        plan.append(entry)

    _write_json(session / "fetch_plan.json", {
        "question": state["question"],
        "count": len(plan),
        "plan": plan,
    })
    state["phase"] = "fetch-planned"
    _save_state(session, state)

    summary = {
        "arxiv": sum(1 for e in plan if e["strategy"] == "arxiv-analyze"),
        "open_access_pdf": sum(1 for e in plan if e["strategy"] == "open-access-pdf"),
        "abstract_only": sum(1 for e in plan if e["strategy"] == "abstract-only"),
    }
    print(json.dumps({
        "session": str(session),
        "total": len(plan),
        "by_strategy": summary,
        "next_step": "read each paper with the indicated strategy, then synthesize",
    }, indent=2))
    return 0


def cmd_status(args) -> int:
    session = Path(args.session_dir).resolve()
    state = _load_state(session)
    print(json.dumps({
        "session": str(session),
        "question": state["question"],
        "phase": state.get("phase"),
        "created": state.get("created"),
        "sources_searched": state.get("sources_searched", []),
        "candidate_count": state.get("candidate_count"),
        "shortlist_count": state.get("shortlist_count"),
    }, indent=2))
    return 0


def cmd_list_sessions(args) -> int:
    out_dir = args.out_dir or DEFAULT_OUT_DIR
    if not out_dir.is_dir():
        print(json.dumps({"sessions": []}, indent=2))
        return 0
    sessions = []
    for d in sorted(out_dir.iterdir()):
        state_path = d / "state.json"
        if state_path.is_file():
            try:
                s = json.loads(state_path.read_text())
                sessions.append({
                    "slug": s.get("slug"),
                    "phase": s.get("phase"),
                    "question": s.get("question"),
                    "created": s.get("created"),
                    "path": str(d),
                })
            except (OSError, json.JSONDecodeError):
                pass
    print(json.dumps({"sessions": sessions}, indent=2))
    return 0


# ---- CLI ------------------------------------------------------------------ #

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("question")
    p_init.add_argument("--out-dir", type=Path)

    p_search = sub.add_parser("search")
    p_search.add_argument("session_dir")
    p_search.add_argument("--limit", type=int, default=50)
    p_search.add_argument("--year")
    p_search.add_argument("--venue")
    p_search.add_argument("--min-citations", type=int)
    p_search.add_argument("--include-arxiv", action="store_true",
                          help="Also query arxiv-search if that skill is installed")

    p_screen = sub.add_parser("screen")
    p_screen.add_argument("session_dir")
    p_screen.add_argument("--include", required=True,
                          help="Comma-separated IDs (S2 paperId, arxiv_id, or DOI) to keep")
    p_screen.add_argument("--reasons-file",
                          help="Optional JSON mapping id -> reason for inclusion")

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("session_dir")

    p_status = sub.add_parser("status")
    p_status.add_argument("session_dir")

    p_ls = sub.add_parser("list-sessions")
    p_ls.add_argument("--out-dir", type=Path)

    args = parser.parse_args()
    handlers = {
        "init": cmd_init,
        "search": cmd_search,
        "screen": cmd_screen,
        "fetch": cmd_fetch,
        "status": cmd_status,
        "list-sessions": cmd_list_sessions,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
