"""Search and optionally clone public GitHub code for literature ARA papers."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
COLLECTION_ROOT = ROOT / "ara_collections" / "dataset_benchmark_papers"
MANIFEST = COLLECTION_ROOT / "collection_manifest.csv"
CODE_MANIFEST = COLLECTION_ROOT / "code_harvest_manifest.csv"
USER_AGENT = "powergrid-benchmark-code-harvester/0.1"


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "based",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
    "via",
    "toward",
    "towards",
}


def slug_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def github_request(url: str, token: str | None = None, retries: int = 3) -> dict[str, Any]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {403, 429}:
                sleep_for = 70 + 10 * attempt
                print(f"GitHub rate/limit response {exc.code}; sleeping {sleep_for}s")
                time.sleep(sleep_for)
                continue
            if exc.code == 422:
                return {"items": []}
        except Exception as exc:
            last_error = exc
            time.sleep(3 * (attempt + 1))
    raise last_error or RuntimeError("unknown GitHub request failure")


def search_repos(title: str, dataset_id: str, token: str | None, per_page: int) -> list[dict[str, Any]]:
    tokens = slug_tokens(title)
    # Keep query compact for GitHub's search parser.
    title_terms = " ".join(tokens[:8])
    dataset_terms = dataset_id.replace(";", " ").replace("_", " ")
    queries = [
        f'"{title}" in:name,description,readme',
        f'{title_terms} in:name,description,readme',
        f'{title_terms} {dataset_terms} in:name,description,readme',
    ]
    seen: set[int] = set()
    results: list[dict[str, Any]] = []
    for query in queries:
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": str(per_page),
        }
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(params)
        print(f"  GitHub query: {query[:120]}")
        data = github_request(url, token=token)
        for item in data.get("items") or []:
            repo_id = item.get("id")
            if repo_id not in seen:
                seen.add(repo_id)
                results.append(item)
        if results:
            break
        time.sleep(1)
    return results


def score_repo(row: dict[str, str], repo: dict[str, Any]) -> tuple[float, str]:
    title_tokens = set(slug_tokens(row["title"]))
    if not title_tokens:
        return 0.0, "empty_title_tokens"
    repo_text = " ".join(
        [
            repo.get("full_name") or "",
            repo.get("name") or "",
            repo.get("description") or "",
            repo.get("html_url") or "",
        ]
    ).lower()
    repo_tokens = set(slug_tokens(repo_text))
    overlap = title_tokens & repo_tokens
    overlap_score = len(overlap) / max(len(title_tokens), 1)
    dataset_tokens = set(slug_tokens(row.get("dataset_id", "")))
    dataset_score = 0.1 if dataset_tokens & repo_tokens else 0.0
    star_score = min((repo.get("stargazers_count") or 0) / 100.0, 0.15)
    score = overlap_score + dataset_score + star_score
    reason = f"title_token_overlap={len(overlap)}/{len(title_tokens)}; stars={repo.get('stargazers_count') or 0}"
    return round(score, 3), reason


def clone_repo(repo: dict[str, Any], paper_dir: Path) -> tuple[str, str]:
    code_dir = paper_dir / "src" / "code"
    target = code_dir / "repo"
    if target.exists():
        return str(target.relative_to(ROOT)).replace("\\", "/"), "already_exists"
    code_dir.mkdir(parents=True, exist_ok=True)
    url = repo.get("clone_url") or repo.get("html_url")
    if not url:
        return "", "missing_clone_url"
    cmd = ["git", "clone", "--depth", "1", url, str(target)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=240)
    if proc.returncode != 0:
        return "", f"clone_failed: {proc.stderr.strip()[:300]}"
    return str(target.relative_to(ROOT)).replace("\\", "/"), "cloned"


def update_code_readme(row: dict[str, str], harvest: dict[str, str]) -> None:
    code_dir = ROOT / row["ara_path"] / "src" / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    readme = code_dir / "README.md"
    content = f"""# Code

## Harvest Status

- Status: `{harvest['code_status']}`
- Confidence: `{harvest['confidence']}`
- Repository: {harvest['repo_url'] or 'Not found'}
- Local path: `{harvest['code_path'] or 'Not cloned'}`
- Reason: {harvest['match_reason']}

## Policy

Only public GitHub repositories with sufficient title/dataset similarity are cloned.
Unconfirmed candidates remain in the collection-level `code_harvest_manifest.csv`.
"""
    readme.write_text(content, encoding="utf-8")


def update_collection_manifest(rows: list[dict[str, str]], harvest_rows: list[dict[str, str]]) -> None:
    by_paper = {r["paper_id"]: r for r in harvest_rows}
    fields = list(rows[0].keys()) if rows else []
    for row in rows:
        hit = by_paper.get(row["paper_id"])
        if not hit:
            continue
        row["code_status"] = hit["code_status"]
        row["code_path"] = hit["code_path"]
        row["code_url"] = hit["repo_url"]
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


HARVEST_FIELDS = [
    "paper_id",
    "title",
    "dataset_id",
    "code_status",
    "confidence",
    "score",
    "repo_full_name",
    "repo_url",
    "code_path",
    "clone_note",
    "match_reason",
]


def write_code_manifest(harvest_rows: list[dict[str, str]]) -> None:
    with CODE_MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HARVEST_FIELDS)
        writer.writeheader()
        writer.writerows(harvest_rows)


def safe_console(text: str, limit: int = 140) -> str:
    return text[:limit].encode("ascii", errors="replace").decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clone", action="store_true")
    parser.add_argument("--max-papers", type=int, default=0, help="0 means all papers")
    parser.add_argument("--per-page", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.55)
    parser.add_argument("--sleep", type=float, default=6.5, help="GitHub search API unauthenticated limit is low.")
    parser.add_argument("--refresh", action="store_true", help="Re-search papers already present in the code manifest.")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    existing: dict[str, dict[str, str]] = {}
    if CODE_MANIFEST.exists() and not args.refresh:
        with CODE_MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
            existing = {row["paper_id"]: row for row in csv.DictReader(handle)}

    todo = [row for row in rows if args.refresh or row["paper_id"] not in existing]
    selected = todo if args.max_papers <= 0 else todo[: args.max_papers]
    harvest_rows: list[dict[str, str]] = list(existing.values()) if not args.refresh else []
    for idx, row in enumerate(selected, start=1):
        print(f"[{idx}/{len(selected)}] {row['paper_id']}: {safe_console(row['title'], 100)}")
        best_repo: dict[str, Any] | None = None
        best_score = 0.0
        best_reason = "not_searched"
        try:
            repos = search_repos(row["title"], row["dataset_id"], token=token, per_page=args.per_page)
        except Exception as exc:
            repos = []
            best_reason = f"search_failed: {type(exc).__name__}: {exc}"
        for repo in repos:
            score, reason = score_repo(row, repo)
            if score > best_score:
                best_repo = repo
                best_score = score
                best_reason = reason

        code_status = "not_found"
        confidence = "none"
        repo_url = ""
        repo_full_name = ""
        code_path = ""
        clone_note = ""
        if best_repo:
            repo_url = best_repo.get("html_url") or ""
            repo_full_name = best_repo.get("full_name") or ""
            if best_score >= args.min_score:
                confidence = "high"
                code_status = "matched_not_cloned"
                if args.clone:
                    code_path, clone_note = clone_repo(best_repo, ROOT / row["ara_path"])
                    code_status = "cloned" if code_path else "clone_failed"
            elif best_score < 0.2:
                confidence = "none"
                code_status = "not_found"
                repo_url = ""
                repo_full_name = ""
            else:
                confidence = "low"
                code_status = "candidate_low_confidence"

        harvest = {
            "paper_id": row["paper_id"],
            "title": row["title"],
            "dataset_id": row["dataset_id"],
            "code_status": code_status,
            "confidence": confidence,
            "score": str(best_score),
            "repo_full_name": repo_full_name,
            "repo_url": repo_url,
            "code_path": code_path,
            "clone_note": clone_note,
            "match_reason": best_reason,
        }
        harvest_rows.append(harvest)
        update_code_readme(row, harvest)
        write_code_manifest(harvest_rows)
        update_collection_manifest(rows, harvest_rows)
        time.sleep(args.sleep)

    write_code_manifest(harvest_rows)
    update_collection_manifest(rows, harvest_rows)
    print(f"searched: {len(harvest_rows)}")
    print(f"high_confidence: {sum(1 for r in harvest_rows if r['confidence'] == 'high')}")
    print(f"cloned: {sum(1 for r in harvest_rows if r['code_status'] == 'cloned')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
