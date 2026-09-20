# -*- coding: utf-8 -*-
"""Write a gate eval markdown from a harvested reply."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


def wrap_eval(
    case: str,
    gate: str,
    url: str,
    raw_text: str,
    note: str,
    out_dir: Path,
    version: str = "",
    day: str | None = None,
) -> Path:
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
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--version", default="")
    args = ap.parse_args()
    raw_text = Path(args.raw).read_text(encoding="utf-8")
    out = wrap_eval(
        args.case,
        args.gate,
        args.url,
        raw_text,
        args.note,
        Path(args.out_dir),
        version=args.version,
    )
    print(out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
