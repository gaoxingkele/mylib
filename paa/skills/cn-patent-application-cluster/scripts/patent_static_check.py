#!/usr/bin/env python3
"""Lightweight static checks for Chinese patent Markdown drafts."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


REQUIRED_TERM_GROUPS = [
    ("权利要求", ["权利要求"]),
    ("技术领域", ["技术领域"]),
    ("背景技术", ["背景技术"]),
    ("发明内容", ["发明内容", "发明目的", "技术方案"]),
    ("具体实施方式", ["具体实施方式", "实施例"]),
    ("摘要", ["说明书摘要", "摘要"]),
]

RISK_PATTERNS = {
    "todo_or_placeholder": re.compile(r"TODO|待填写|待补充|占位|xxx|XXXX", re.I),
    "ai_meta": re.compile(r"AI|ChatGPT|Codex|Claude|本次修改|根据你的要求|作为智能体", re.I),
    "unsupported_certainty": re.compile(r"必然授权|保证授权|完全新颖|绝对不会"),
    "abstract_figure_meta": re.compile(r"摘要附图建议|摘要附图为"),
}


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？!?;\n]+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 18]


def jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[\w\u4e00-\u9fff]+", a.lower()))
    tb = set(re.findall(r"[\w\u4e00-\u9fff]+", b.lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def repetition_pairs(sentences: list[str], threshold: float) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for i, left in enumerate(sentences):
        for j in range(i + 1, len(sentences)):
            score = jaccard(left, sentences[j])
            if score >= threshold:
                pairs.append({"i": i, "j": j, "score": round(score, 3), "left": left[:80], "right": sentences[j][:80]})
    return pairs


def check(path: Path, threshold: float) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    compact_text = re.sub(r"\s+", "", text)
    headings = re.findall(r"^#{1,6}\s+(.+)$", text, flags=re.M)
    missing_terms = [
        label
        for label, options in REQUIRED_TERM_GROUPS
        if not any(re.sub(r"\s+", "", option) in compact_text for option in options)
    ]
    risks = {name: len(pattern.findall(text)) for name, pattern in RISK_PATTERNS.items()}
    sentences = split_sentences(text)
    repeated = repetition_pairs(sentences, threshold)
    claim_count = len(re.findall(r"^\s*\d+[\.、]\s*", text, flags=re.M))
    formula_count = text.count("\\[") + text.count("$$")
    top_headings = Counter(h.split()[0] for h in headings).most_common(10)
    severity = "pass"
    if missing_terms or any(risks.values()):
        severity = "review"
    if len(repeated) > 20:
        severity = "review"
    return {
        "path": str(path),
        "severity": severity,
        "chars": len(text),
        "headings": len(headings),
        "top_headings": top_headings,
        "claim_like_numbered_items": claim_count,
        "formula_blocks": formula_count,
        "missing_required_terms": missing_terms,
        "risk_counts": risks,
        "sentence_count": len(sentences),
        "repetition_threshold": threshold,
        "repetition_pair_count": len(repeated),
        "repetition_examples": repeated[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static quality checks for Chinese patent Markdown drafts.")
    parser.add_argument("draft", type=Path)
    parser.add_argument("--threshold", type=float, default=0.82)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-review", action="store_true")
    args = parser.parse_args()
    result = check(args.draft, args.threshold)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"severity: {result['severity']}")
        print(f"chars: {result['chars']} headings: {result['headings']} numbered-items: {result['claim_like_numbered_items']}")
        if result["missing_required_terms"]:
            print("missing:", ", ".join(result["missing_required_terms"]))
        for key, value in result["risk_counts"].items():
            if value:
                print(f"{key}: {value}")
        print(f"repetition-pairs: {result['repetition_pair_count']}")
    if args.fail_on_review and result["severity"] != "pass":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
