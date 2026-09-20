# -*- coding: utf-8 -*-
"""Build per-case prompt + fulltext for a browser review session."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = SKILL / "prompts" / "six_section_review.zh.txt"
PARTS = (
    "05_说明书摘要.md",
    "02_权利要求书.md",
    "04_附图清单与描述.md",
    "03_说明书.md",
)


def load_meta(args: argparse.Namespace) -> dict:
    if args.cases_json:
        data = json.loads(Path(args.cases_json).read_text(encoding="utf-8"))
        meta = next(c for c in data["queue"] if c["id"] == args.case)
        return {
            "id": meta["id"],
            "short": meta["short"],
            "title": meta["title"],
            "source_version": args.version or meta["source_version"],
        }
    if not (args.case and args.title and args.short and args.version):
        raise SystemExit("need --cases-json+--case, or --case --title --short --version")
    return {
        "id": args.case,
        "short": args.short,
        "title": args.title,
        "source_version": args.version,
    }


def find_src(src: Path, case_id: str, version: str) -> Path:
    if (src / "02_权利要求书.md").is_file():
        return src
    for cand in (
        src / f"当前版本_{version}" / "申请源稿",
        src / case_id / f"当前版本_{version}" / "申请源稿",
        src / case_id,
    ):
        if (cand / "02_权利要求书.md").is_file():
            return cand
    raise FileNotFoundError(f"no 02_权利要求书.md under {src}")


def build_texts(meta: dict, src: Path, prompt: str) -> tuple[str, str, str]:
    parts: list[str] = []
    for name in PARTS:
        p = src / name
        if p.is_file():
            parts.append(f"\n\n===== {name} =====\n\n")
            parts.append(p.read_text(encoding="utf-8"))
    header = (
        f"【案件标识】仅评本案：{meta['id']}。简写名称：{meta['short']}。"
        f"发明名称：{meta['title']}。版本：{meta['source_version']}。\n\n"
    )
    ask = header + "请先完整阅读本会话上传的专利申请书全文。若附件未能解析，请明确说明。\n\n" + prompt
    full = header + prompt + "\n以下为申请文件全文。\n" + "".join(parts)
    title = f"{meta['id']} {meta['short']}"
    return ask, full, title


def write_batch(out: Path, case_id: str, ask: str, full: str, title: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{case_id}_ask_with_file.txt").write_text(ask, encoding="utf-8")
    (out / f"{case_id}_fulltext.txt").write_text(full, encoding="utf-8")
    (out / f"{case_id}_thread_title.txt").write_text(title, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--short", default="")
    ap.add_argument("--version", default="")
    ap.add_argument("--src", required=True, help="directory that contains 02/03/04/05 md, or a parent")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cases-json", default="")
    ap.add_argument("--prompt", default=str(DEFAULT_PROMPT))
    args = ap.parse_args()
    meta = load_meta(args)
    src = find_src(Path(args.src), meta["id"], meta["source_version"])
    prompt = Path(args.prompt).read_text(encoding="utf-8")
    ask, full, title = build_texts(meta, src, prompt)
    write_batch(Path(args.out), meta["id"], ask, full, title)
    print(Path(args.out).resolve())
    print("full_chars", len(full))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
