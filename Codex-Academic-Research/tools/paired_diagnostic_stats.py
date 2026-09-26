#!/usr/bin/env python3
"""Paired-difference statistics for diagnostic / negative-result evaluations.

Distilled from the C2GES Information campaign (2026-09).  The failure mode this
tool exists to prevent: reporting a paired comparison whose differences are
*zero-inflated* and *heavy-tailed* with a mean-based test only, then reading
"p > 0.05" as "no effect".  The same data usually supports a much stronger
statement — a one-sided bound — which is why this tool reports both.

Reports, per contrast:
  * n, mean, median, sd, min, max, and the exact-zero mass
  * discordant split (negative / positive / tied) and the sign share
  * exact sign-flip p-value when n <= 20, otherwise a randomised sign flip
  * one-sided upper confidence limit on the mean (bootstrap percentile)
  * a leave-one-out envelope for both the mean and that upper limit
  * the power ceiling: the smallest attainable adjusted p-value for the family
  * sign-test sample size needed for 80% power at a given true sign share

Stdlib only, so it runs in any environment.

Input: long-format CSV or JSONL with one row per paired difference:
    doc_id, contrast, value
`contrast` groups the rows; `value` is the difference for that document.

Usage:
    python paired_diagnostic_stats.py pairs.csv --json report.json
    python paired_diagnostic_stats.py pairs.csv --alpha 0.05 --draws 200000
    python paired_diagnostic_stats.py --self-test
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return list(csv.DictReader(text.splitlines()))


def group(records: list[dict]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for row in records:
        out[str(row["contrast"])].append(float(row["value"]))
    return dict(out)


def boot_upper(values: list[float], *, draws: int, seed: int, alpha: float) -> float:
    rng = random.Random(seed)
    n = len(values)
    means = [statistics.fmean(rng.choices(values, k=n)) for _ in range(draws)]
    means.sort()
    return means[max(0, int(math.ceil((1 - alpha) * draws)) - 1)]


def exact_signflip(values: list[float]) -> float | None:
    n = len(values)
    if n > 18:
        return None
    observed = abs(statistics.fmean(values))
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=n):
        total += 1
        if abs(statistics.fmean(s * v for s, v in zip(signs, values))) >= observed - 1e-12:
            hits += 1
    return hits / total


def randomised_signflip(values: list[float], *, draws: int, seed: int) -> float:
    rng = random.Random(seed)
    observed = abs(statistics.fmean(values))
    hits = sum(
        1
        for _ in range(draws)
        if abs(statistics.fmean(v if rng.random() < 0.5 else -v for v in values)) >= observed - 1e-12
    )
    return (hits + 1) / (draws + 1)


def _upper_tail(n: int, p: float, k: int) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def sign_critical(n: int, alpha: float) -> int:
    """Smallest k with a two-sided exact sign test of alpha rejecting at k successes."""
    for k in range(0, n + 2):
        if 2 * _upper_tail(n, 0.5, k) <= alpha:
            return k
    return n + 1


def sign_power(n: int, p: float, alpha: float = 0.05) -> float:
    k = sign_critical(n, alpha)
    if k > n:
        return 0.0
    return _upper_tail(n, p, k) + sum(
        math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, n - k + 1)
    )


def sign_n_for_power(p: float, alpha: float = 0.05, target: float = 0.80, cap: int = 400) -> int | None:
    for n in range(4, cap + 1):
        if sign_power(n, p, alpha) >= target:
            return n
    return None


def power_ceiling(n: int, family_size: int) -> float:
    """Smallest Holm-adjusted exact sign-flip p-value attainable at this n."""
    return min(1.0, family_size * (2 / 2**n)) if n < 1024 else 0.0


def summarise(values: list[float], *, alpha: float, draws: int, seed: int, family_size: int) -> dict:
    n = len(values)
    negative = sum(1 for v in values if v < -1e-12)
    positive = sum(1 for v in values if v > 1e-12)
    tied = n - negative - positive
    discordant = negative + positive
    exact = exact_signflip(values)
    p = exact if exact is not None else randomised_signflip(values, draws=draws, seed=seed)
    loo_mean, loo_upper = [], []
    for index in range(n):
        rest = values[:index] + values[index + 1 :]
        loo_mean.append(statistics.fmean(rest))
        loo_upper.append(boot_upper(rest, draws=max(2000, draws // 20), seed=seed, alpha=alpha))
    sign_share = positive / discordant if discordant else None
    return {
        "n": n,
        "mean": round(statistics.fmean(values), 6),
        "median": round(statistics.median(values), 6),
        "sd": round(statistics.pstdev(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "negative": negative,
        "positive": positive,
        "tied": tied,
        "zero_mass": round(tied / n, 4),
        "positive_share_of_discordant": None if sign_share is None else round(sign_share, 4),
        "exact_sign_flip_p": None if exact is None else round(exact, 6),
        "randomised_sign_flip_p": None if exact is not None else round(p, 6),
        "p_value_used": round(p, 6),
        "one_sided_upper_limit": round(boot_upper(values, draws=draws, seed=seed, alpha=alpha), 6),
        "leave_one_out": {
            "mean_min": round(min(loo_mean), 6),
            "mean_max": round(max(loo_mean), 6),
            "mean_span": round(max(loo_mean) - min(loo_mean), 6),
            "upper_limit_max": round(max(loo_upper), 6),
        },
        "power_ceiling_min_adjusted_p": round(power_ceiling(n, family_size), 6),
        "sign_power_at_observed_share": None if sign_share is None else round(sign_power(int(discordant), max(sign_share, 1 - sign_share)), 6),
        "documents_for_80pct_power": {
            share: (
                None
                if sign_n_for_power(share) is None
                else math.ceil(sign_n_for_power(share) / (discordant / n)) if discordant else None
            )
            for share in (0.70, 0.75, 0.80)
        },
    }


SELF_TEST = {
    "path layer": [-0.15218, -0.01744, -0.0167, -0.01208, -0.00759, -0.00417, -0.00212, -0.00212,
                   -0.00085, -0.00057, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.05002],
}


def self_test() -> int:
    report = summarise(SELF_TEST["path layer"], alpha=0.05, draws=20000, seed=20260926, family_size=5)
    expected = {
        "n": 24,
        "negative": 10,
        "positive": 1,
        "tied": 13,
        "mean": -0.006908,
    }
    failures = []
    for key, want in expected.items():
        got = report[key]
        if isinstance(want, float):
            if abs(got - want) > 1e-5:
                failures.append(f"{key}: {got} != {want}")
        elif got != want:
            failures.append(f"{key}: {got} != {want}")
    if not (-0.001 <= report["one_sided_upper_limit"] <= 0.005):
        failures.append(f"upper limit out of the expected band: {report['one_sided_upper_limit']}")
    if failures:
        print("SELF-TEST FAILED")
        for item in failures:
            print("  -", item)
        return 1
    print("self-test OK:", json.dumps({k: report[k] for k in expected}, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pairs", nargs="?", help="long-format CSV/JSONL with doc_id, contrast, value")
    parser.add_argument("--json", type=Path, default=None, help="write the report here")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--draws", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=20260926)
    parser.add_argument("--family-size", type=int, default=1, help="contrasts sharing a Holm correction")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.pairs:
        parser.error("a pairs file is required (or use --self-test)")

    groups = group(load_records(Path(args.pairs)))
    report = {
        "schema": "paired-diagnostic-stats-v1",
        "alpha": args.alpha,
        "bootstrap_draws": args.draws,
        "seed": args.seed,
        "holm_family_size": args.family_size,
        "contrasts": {
            name: summarise(values, alpha=args.alpha, draws=args.draws, seed=args.seed,
                            family_size=args.family_size)
            for name, values in sorted(groups.items())
        },
    }
    for name, item in report["contrasts"].items():
        print(
            f"{name:28s} n={item['n']:3d} mean={item['mean']:+.5f} "
            f"neg/pos/tie={item['negative']}/{item['positive']}/{item['tied']} "
            f"UB{int((1 - args.alpha) * 100)}={item['one_sided_upper_limit']:+.5f} "
            f"p={item['p_value_used']:.4f}"
        )
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
