# -*- coding: utf-8 -*-
"""Write a gate eval markdown from a harvested reply."""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

# 结论段落提取规则（按优先级）
_CONCLUSION_PATTERNS = [
    r"(?:^|\n)(?:#{1,3}\s*)?(?:结论|总结|综合结论|总体评价|评估总结)[：:。]?\s*\n([\s\S]{30,800}?)(?=\n#{1,3}|\Z)",
    r"(?:^|\n)(?:#{1,3}\s*)?(?:主要风险|P0|0级|零级|高优先)[：:]?\s*\n([\s\S]{30,500}?)(?=\n#{1,3}|\n(?:P1|1级|一级|次要)|\Z)",
    r"(?:新颖性[结论评估]|创造性[结论评估])[：:]\s*([^\n]{20,200})",
    r"(?:授权概率|授权率)[：:]?\s*([^\n]{10,100})",
    r"(?:建议|修改建议)[：:]\s*\n([\s\S]{30,400}?)(?=\n#{1,3}|\Z)",
]


def extract_summary(raw: str, chars: int = 400) -> str:
    hits: list[str] = []
    for pat in _CONCLUSION_PATTERNS:
        for m in re.finditer(pat, raw, re.M):
            seg = (m.group(1) if m.lastindex else m.group(0)).strip()
            if seg and seg not in hits:
                hits.append(seg)
    if not hits:
        # 无结构标记时取末尾段落
        paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
        hits = paras[-3:] if len(paras) >= 3 else paras
    combined = "\n\n".join(hits)
    return combined[:chars]


def wrap_eval(
    case: str,
    gate: str,
    url: str,
    raw_text: str,
    note: str,
    out_dir: Path,
    version: str = "",
    day: str | None = None,
    summary_chars: int = 400,
) -> tuple[Path, Path]:
    when = day or date.today().isoformat()
    ver = version or "unspecified"
    head = (
        f"# {gate} 对 {case} 的新颖性/创造性评估\n\n"
        f"- 日期：{when}\n"
        f"- 模式：{note}\n"
        f"- 独立会话：{url}\n"
        f"- 输入：{ver} 申请文件全文 + 六节结构化提问\n"
        f"- 说明：网页模型评估，不是法律意见。未调用 incoPat。本会话只评 {case}。\n\n"
        "## 回复全文\n\n"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{gate}_新颖性创造性评估.md"
    out.write_text(head + raw_text.rstrip() + "\n", encoding="utf-8")

    summary = extract_summary(raw_text, summary_chars)
    sum_head = (
        f"# {gate} × {case} 结论摘要（{when}）\n\n"
        f"> 自动提取，全文见 `{out.name}`。网页模型意见，非法律结论。\n\n"
    )
    sum_out = out_dir / f"{gate}_摘要.md"
    sum_out.write_text(sum_head + summary + "\n", encoding="utf-8")
    return out, sum_out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--version", default="")
    ap.add_argument("--summary-chars", type=int, default=400)
    args = ap.parse_args()
    raw_text = Path(args.raw).read_text(encoding="utf-8")
    out, sum_out = wrap_eval(
        args.case,
        args.gate,
        args.url,
        raw_text,
        args.note,
        Path(args.out_dir),
        version=args.version,
        summary_chars=args.summary_chars,
    )
    print(out, out.stat().st_size)
    print("summary →", sum_out, sum_out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
