# -*- coding: utf-8 -*-
"""post_copy.py — 合并 save_clipboard + wrap_eval + wiki_log 为单次 Bash 调用。

用法：
  python post_copy.py \\
    --case P01-1 --gate PPLX-PATENTS --version 20260927 \\
    --url https://www.perplexity.ai/search/... \\
    --out-dir output/闽投申报10篇/P01-1/当前版本_20260927/paa/evidence/browser_review \\
    --log wiki/log.md \\
    [--note "Max委员会"] [--summary-chars 400] [--section 八案四端审核]

stdout 返回单行 JSON（约 300 字），包含：
  out_md    全文 md 路径
  sum_md    摘要 md 路径（供 Claude 直接阅读，不读全文）
  wiki      写入 wiki/log.md 的那行文字
  summary   摘要正文（最多 summary_chars 字符）
  raw_len   原始剪贴板字符数（用于核验是否复制完整）

token 节省：三次 Bash 工具调用 → 一次；Claude 只读 summary 字段，不读全文 md。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 同目录脚本引用
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from wiki_log import format_line, insert_line  # noqa: E402
from wrap_eval import wrap_eval  # noqa: E402


def read_clipboard() -> str:
    ps = [
        "powershell",
        "-NoProfile",
        "-Command",
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
    ]
    raw = subprocess.check_output(ps)
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--gate", required=True,
                    help="GEMINI | GROK-EXPERT | GPT-6-PRO | PPLX-PATENTS | KIMI-K3-ACADEMIC")
    ap.add_argument("--version", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--log", required=True, help="path to wiki/log.md")
    ap.add_argument("--note", default="")
    ap.add_argument("--summary-chars", type=int, default=400)
    ap.add_argument("--section", default="八案四端审核")
    args = ap.parse_args()

    # 1. 读剪贴板
    raw_text = read_clipboard()

    # 2. wrap_eval（写全文 md + 摘要 md）
    out_md, sum_md = wrap_eval(
        case=args.case,
        gate=args.gate,
        url=args.url,
        raw_text=raw_text,
        note=args.note,
        out_dir=Path(args.out_dir),
        version=args.version,
        summary_chars=args.summary_chars,
    )

    # 3. wiki_log（在 wiki/log.md 的指定 section 下插入一行）
    log = Path(args.log)
    wiki_line = format_line(args.case, args.gate, args.version, args.note, args.url)
    prev = log.read_text(encoding="utf-8") if log.exists() else "# Wiki 变更日志\n\n"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(insert_line(prev, wiki_line, args.section), encoding="utf-8")

    # 4. 读摘要内容（仅此字段进 Claude 上下文）
    summary_text = sum_md.read_text(encoding="utf-8")
    # 去掉 header 行（以 # / > 开头的前几行），只保留正文
    lines = summary_text.splitlines()
    body_lines = [l for l in lines if not l.startswith("#") and not l.startswith(">")]
    summary_body = "\n".join(body_lines).strip()[:args.summary_chars]

    result = {
        "out_md": str(out_md),
        "sum_md": str(sum_md),
        "wiki": wiki_line.strip(),
        "summary": summary_body,
        "raw_len": len(raw_text),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
