#!/usr/bin/env python3
"""Deterministic formal checks for Chinese patent claim sets.

This checker deliberately limits itself to rules that can be evaluated without
an LLM: claim numbering, reference direction/existence, nested multiple
dependencies, and the one-sentence rule.  Antecedent basis and substantive
support remain reviewer tasks because regex-only judgments are too noisy.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


CLAIM_START = re.compile(r"^\s*(?:\*\*)?(\d+)(?:\.\*\*|[.、．])\s*", re.M)
REFERENCE_EXPR = re.compile(
    r"权利要求\s*([0-9０-９][0-9０-９\s、,，或和及至到~～\-—]*)"
)
RANGE = re.compile(r"(\d+)\s*(?:至|到|~|～|-|—)\s*(\d+)")


def _ascii_digits(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def parse_claims(text: str) -> list[dict[str, object]]:
    """Return numbered claim blocks, accepting plain and Markdown numbering."""
    matches = list(CLAIM_START.finditer(text))
    claims: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        claims.append({"number": int(match.group(1)), "text": text[match.start():end].strip()})
    return claims


def extract_references(claim_text: str) -> list[int]:
    """Extract and expand referenced claim numbers from Chinese expressions."""
    refs: set[int] = set()
    for match in REFERENCE_EXPR.finditer(_ascii_digits(claim_text)):
        expr = match.group(1)
        for left, right in RANGE.findall(expr):
            start, stop = int(left), int(right)
            if start <= stop:
                refs.update(range(start, stop + 1))
            else:
                refs.update((start, stop))
        expr_without_ranges = RANGE.sub(" ", expr)
        refs.update(int(value) for value in re.findall(r"\d+", expr_without_ranges))
    return sorted(refs)


def check_text(text: str) -> dict[str, object]:
    claims = parse_claims(text)
    findings: list[dict[str, object]] = []

    def add(code: str, severity: str, message: str, claim: int | None = None) -> None:
        findings.append({"code": code, "severity": severity, "claim": claim, "message": message})

    if not claims:
        add("no_claims", "error", "未识别到以1开始的编号权利要求")
        return {"severity": "fail", "score": 0.0, "claim_count": 0, "findings": findings}

    numbers = [int(claim["number"]) for claim in claims]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        add("numbering", "error", f"权利要求编号应连续为{expected}，实际为{numbers}")

    existing = set(numbers)
    refs_by_claim = {
        int(claim["number"]): extract_references(str(claim["text"])) for claim in claims
    }
    dependent_claims = {
        int(claim["number"])
        for claim in claims
        if re.match(
            r"^\s*(?:\*\*)?\d+(?:\.\*\*|[.、．])\s*(?:根据|如|按照|依照)权利要求",
            str(claim["text"]),
        )
    }
    multiple_dependent = {
        number for number, refs in refs_by_claim.items() if number in dependent_claims and len(refs) > 1
    }

    for claim in claims:
        number = int(claim["number"])
        block = str(claim["text"])
        refs = refs_by_claim[number]

        for ref in refs:
            if ref == number:
                add("self_reference", "error", f"权利要求{number}引用自身", number)
            elif ref > number:
                add("forward_reference", "error", f"权利要求{number}前向引用权利要求{ref}", number)
            elif ref not in existing:
                add("missing_reference", "error", f"权利要求{number}引用不存在的权利要求{ref}", number)

        if number in multiple_dependent:
            nested = sorted(set(refs) & multiple_dependent)
            if nested:
                add(
                    "nested_multiple_dependency",
                    "error",
                    f"多项从属权利要求{number}引用了多项从属权利要求{nested}",
                    number,
                )

        body = re.sub(r"^\s*(?:\*\*)?\d+(?:\.\*\*|[.、．])\s*", "", block).strip()
        body = re.sub(r"(?:\r?\n)\s*---+\s*$", "", body).strip()
        body = body.rstrip("*").strip()
        sentence_marks = body.count("。")
        if sentence_marks != 1 or not body.endswith("。"):
            add(
                "single_sentence",
                "error",
                f"权利要求{number}应仅在末尾使用一个句号，当前句号数为{sentence_marks}",
                number,
            )

        if not refs and "其特征在于" not in body:
            add("independent_transition", "review", f"独立权利要求{number}未出现“其特征在于”", number)

    errors = sum(1 for item in findings if item["severity"] == "error")
    reviews = sum(1 for item in findings if item["severity"] == "review")
    score = max(0.0, 1.0 - 0.15 * errors - 0.03 * reviews)
    severity = "fail" if errors else ("review" if reviews else "pass")
    return {
        "severity": severity,
        "score": round(score, 3),
        "claim_count": len(claims),
        "references": refs_by_claim,
        "multiple_dependent_claims": sorted(multiple_dependent),
        "findings": findings,
        "diagnostic_note": "术语先行基础与说明书支持需人工审查，未纳入确定性分数。",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="中国专利权利要求确定性形式检查")
    parser.add_argument("claims", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args()

    result = check_text(args.claims.read_text(encoding="utf-8"))
    result["path"] = str(args.claims)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"severity: {result['severity']} score: {result['score']:.3f} "
            f"claims: {result['claim_count']}"
        )
        for finding in result["findings"]:
            print(f"  - {finding['severity']} {finding['code']}: {finding['message']}")
        print(f"note: {result['diagnostic_note']}")

    if result["severity"] == "fail":
        return 2
    if args.fail_on_review and result["severity"] != "pass":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
