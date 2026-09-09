#!/usr/bin/env python3
"""Evidence-led prose audit; deliberately not an AI-authorship detector."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


PATTERNS = {
    "generic_transition": [
        r"\b(?:moreover|furthermore|additionally|notably|in conclusion)\b",
        r"(?:此外|同时|值得注意的是|需要强调的是|综上所述|总而言之)",
    ],
    "inflation": [
        r"\b(?:groundbreaking|revolutionary|transformative|pivotal|unprecedented|seamless|intricate)\b",
        r"(?:颠覆性|革命性|开创性|前所未有|至关重要|无缝|全方位赋能)",
    ],
    "vague_attribution": [
        r"\b(?:experts|researchers|observers|many studies)\s+(?:say|argue|believe|suggest|show)\b",
        r"(?:研究表明|有研究认为|业内人士认为|专家指出|普遍认为)",
    ],
    "formulaic_opening": [
        r"\b(?:in recent years|with the rapid development of|in today's rapidly evolving)\b",
        r"(?:近年来，?随着|随着.+?的快速发展|在当今快速发展的)",
    ],
    "empty_effect": [
        r"\b(?:significantly improves|greatly enhances|effectively solves|plays a crucial role)\b",
        r"(?:显著提高|大幅提升|有效解决|发挥(?:着)?重要作用|实现智能化|形成闭环)",
    ],
    "placeholder": [
        r"\[(?:citation needed|to be confirmed|tbd|todo)\]",
        r"(?:待补充|待确认|此处填写|XXX+|【[^】]*(?:待|补充)[^】]*】)",
    ],
}

PATENT_EVIDENCE_TERMS = (
    "字段", "类型", "取值", "时间戳", "版本", "事务", "状态", "异常", "阈值",
    "计算", "实施例", "附图", "日志", "代码", "接口", "数据源", "回滚",
)

PROTECTED_RE = re.compile(
    r"(?:\\cite\w*\{[^}]+\}|\\(?:ref|eqref)\{[^}]+\}|"
    r"\[[0-9]{1,3}(?:\s*[-,，]\s*[0-9]{1,3})*\]|"
    r"(?:图|表|权利要求)\s*[0-9一二三四五六七八九十]+|"
    r"\b(?:Fig(?:ure)?|Table|Claim|Section)\.?\s*\d+(?:\.\d+)*|"
    r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:\s*%|\s*(?:ms|s|kg|g|mm|cm|m|kV|V|A|Hz|MHz|GHz|℃|°C|元|万元))?)",
    re.IGNORECASE,
)

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CORE_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}


def read_text(path: Path) -> tuple[str, dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
            paragraphs = []
            for paragraph in root.iter(WORD_NS + "p"):
                text = "".join(node.text or "" for node in paragraph.iter(WORD_NS + "t"))
                if text.strip():
                    paragraphs.append(text)
            metadata: dict[str, str] = {}
            if "docProps/core.xml" in archive.namelist():
                core = ET.fromstring(archive.read("docProps/core.xml"))
                for key, query in {
                    "creator": "dc:creator",
                    "last_modified_by": "cp:lastModifiedBy",
                    "created": "dcterms:created",
                    "modified": "dcterms:modified",
                }.items():
                    node = core.find(query, CORE_NS)
                    if node is not None and node.text:
                        metadata[key] = node.text
            if "docProps/app.xml" in archive.namelist():
                app = ET.fromstring(archive.read("docProps/app.xml"))
                for node in app:
                    if node.tag.rsplit("}", 1)[-1] == "Application" and node.text:
                        metadata["application"] = node.text
            return "\n".join(paragraphs), metadata
    if suffix not in {".txt", ".md", ".markdown", ".tex"}:
        raise ValueError(f"unsupported input type: {suffix}; use txt, md, tex, or docx")
    return path.read_text(encoding="utf-8-sig"), {}


def sentence_lengths(text: str) -> list[int]:
    sentences = [part.strip() for part in re.split(r"(?<=[。！？!?;；.])\s*", text) if part.strip()]
    return [len(re.findall(r"[\w\u3400-\u9fff]+", sentence)) for sentence in sentences]


def mask_quoted_and_code(text: str) -> str:
    """Preserve offsets/newlines while excluding quoted examples and code."""
    masked = text
    expressions = (
        r"```.*?```",
        r"`[^`\n]+`",
        r"\\begin\{verbatim\}.*?\\end\{verbatim\}",
        r"“[^”\n]*”",
        r"‘[^’\n]*’",
        r'"[^"\n]*"',
    )
    for expression in expressions:
        masked = re.sub(
            expression,
            lambda match: "".join("\n" if char == "\n" else " " for char in match.group(0)),
            masked,
            flags=re.DOTALL,
        )
    return masked


def find_patterns(text: str) -> list[dict[str, object]]:
    searchable = mask_quoted_and_code(text)
    findings = []
    for category, expressions in PATTERNS.items():
        for expression in expressions:
            for match in re.finditer(expression, searchable, re.IGNORECASE):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {"category": category, "line_or_paragraph": line, "text": text[match.start():match.end()]}
                )
    return findings


def repeated_openers(text: str) -> list[dict[str, object]]:
    openers = []
    for index, sentence in enumerate(re.split(r"(?<=[。！？!?;；.])\s*", text), start=1):
        tokens = re.findall(r"[A-Za-z]+|[\u3400-\u9fff]", sentence.strip().lower())
        if tokens:
            opener = " ".join(tokens[:3]) if re.match(r"[a-z]", tokens[0]) else "".join(tokens[:4])
            openers.append((opener, index))
    counts = Counter(opener for opener, _ in openers if opener)
    return [
        {"opener": opener, "count": count, "sentences": [i for value, i in openers if value == opener]}
        for opener, count in counts.most_common()
        if count >= 3
    ]


def audit(path: Path, profile: str) -> dict[str, object]:
    text, metadata = read_text(path)
    lengths = sentence_lengths(text)
    mean = statistics.fmean(lengths) if lengths else 0.0
    stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    coefficient = stdev / mean if mean else 0.0
    findings = find_patterns(text)
    categories = Counter(item["category"] for item in findings)
    result: dict[str, object] = {
        "disclaimer": "Heuristic writing-quality audit only; not an AI-authorship detector.",
        "file": str(path.resolve()),
        "profile": profile,
        "characters": len(text),
        "sentences": len(lengths),
        "sentence_length_mean_tokens": round(mean, 2),
        "sentence_length_cv": round(coefficient, 3),
        "pattern_counts": dict(categories),
        "findings": findings,
        "repeated_openers": repeated_openers(text),
        "metadata_for_manual_review": metadata,
    }
    if profile == "patent":
        evidence_counts = {term: text.count(term) for term in PATENT_EVIDENCE_TERMS}
        result["patent_evidence_anchors"] = evidence_counts
        result["patent_manual_gates"] = [
            "problem-mechanism-effect-support chain",
            "independent-claim feature/support chart",
            "antecedent basis and terminology consistency",
            "inventor confirmation for every added implementation detail",
        ]
    return result


def protected_tokens(text: str) -> Counter[str]:
    normalized = (re.sub(r"\s+", "", match.group(0)).lower() for match in PROTECTED_RE.finditer(text))
    return Counter(normalized)


def counter_difference(left: Counter[str], right: Counter[str]) -> dict[str, int]:
    return dict(sorted((key, value) for key, value in (left - right).items()))


def compare(original: Path, revised: Path, profile: str) -> dict[str, object]:
    original_text, _ = read_text(original)
    revised_text, _ = read_text(revised)
    before = protected_tokens(original_text)
    after = protected_tokens(revised_text)
    removed = counter_difference(before, after)
    added = counter_difference(after, before)
    return {
        "disclaimer": "Token drift is a verification lead; inspect context before deciding an edit is wrong.",
        "profile": profile,
        "original": str(original.resolve()),
        "revised": str(revised.resolve()),
        "protected_tokens_removed": removed,
        "protected_tokens_added": added,
        "manual_semantic_checks": [
            "claim strength and causal language",
            "scope qualifiers and uncertainty",
            "technical terminology and definitions",
            "citation meaning, equations, quotations, and legal dependencies",
        ],
        "status": "review_required" if removed or added else "token_check_passed",
    }


def markdown(data: dict[str, object]) -> str:
    lines = ["# Authorial authenticity audit", "", f"> {data['disclaimer']}", ""]
    for key in ("file", "original", "revised", "profile", "status", "characters", "sentences",
                "sentence_length_mean_tokens", "sentence_length_cv"):
        if key in data:
            lines.append(f"- **{key}:** {data[key]}")
    for heading, key in (
        ("Pattern counts", "pattern_counts"),
        ("Findings", "findings"),
        ("Repeated openers", "repeated_openers"),
        ("Protected tokens removed", "protected_tokens_removed"),
        ("Protected tokens added", "protected_tokens_added"),
        ("Metadata for manual review", "metadata_for_manual_review"),
        ("Patent evidence anchors", "patent_evidence_anchors"),
        ("Manual semantic checks", "manual_semantic_checks"),
        ("Patent manual gates", "patent_manual_gates"),
    ):
        value = data.get(key)
        if value:
            lines.extend(["", f"## {heading}", "", "```json", json.dumps(value, ensure_ascii=False, indent=2), "```"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("file", type=Path)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("original", type=Path)
    compare_parser.add_argument("revised", type=Path)
    for child in (audit_parser, compare_parser):
        child.add_argument("--profile", choices=("paper", "proposal", "article", "patent"), required=True)
        child.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        data = audit(args.file, args.profile) if args.command == "audit" else compare(
            args.original, args.revised, args.profile
        )
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.format == "json" else markdown(data), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
