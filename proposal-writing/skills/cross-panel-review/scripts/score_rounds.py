"""Summarize complete cross-panel review rounds from a UTF-8 JSON file."""

import argparse
import json
from collections import Counter
from itertools import combinations
from pathlib import Path


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def require_keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"{where}: expected keys {sorted(expected)}")


def summarize(data):
    require_keys(data, ["roles", "rounds"], "input")
    roles = data["roles"]
    if not isinstance(roles, dict) or len(roles) < 2:
        raise ValueError("roles: supply at least two seats")
    if not all(k.strip() and isinstance(v, str) and v.strip() for k, v in roles.items()):
        raise ValueError("roles: supply nonempty seat IDs and labels")
    if not isinstance(data["rounds"], list) or not data["rounds"]:
        raise ValueError("rounds: supply a baseline or more rounds")

    results = []
    seen = set()
    for entry in data["rounds"]:
        require_keys(entry, ["version", "reviews"], "round")
        version = entry["version"]
        if not isinstance(version, str) or not version.strip() or version in seen:
            raise ValueError(f"invalid or duplicate version: {version!r}")
        seen.add(version)
        reviews = entry["reviews"]
        require_keys(reviews, roles, version)
        totals = {}
        counts = Counter({"Y": 0, "C": 0, "N": 0})
        for seat, review in reviews.items():
            where = f"{version}/{seat}"
            require_keys(review, ["scores", "votes"], where)
            scores = review["scores"]
            if (not isinstance(scores, list) or len(scores) != 4
                    or not all(type(s) is int and 0 <= s <= 25 for s in scores)):
                raise ValueError(f"{where}: expected four integer scores in [0, 25]")
            votes = review["votes"]
            require_keys(votes, set(roles) - {seat}, f"{where}/votes")
            if any(v not in ("Y", "C", "N") for v in votes.values()):
                raise ValueError(f"{where}: expected Y, C or N")
            totals[seat] = sum(scores)
            counts.update(votes.values())
        mutual = sum(
            reviews[a]["votes"][b] == reviews[b]["votes"][a] == "Y"
            for a, b in combinations(roles, 2)
        )
        n = len(roles)
        results.append({
            "version": version,
            "totals": totals,
            "mean": round(sum(totals.values()) / n, 1),
            "directed_votes": dict(counts),
            "mutual_pairs": mutual,
            "possible_pairs": n * (n - 1) // 2,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"),
                          object_pairs_hook=unique_keys)
        results = summarize(data)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
