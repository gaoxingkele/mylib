# -*- coding: utf-8 -*-
"""Insert a gate+version line under a wiki heading instead of appending at EOF."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

DEFAULT_SECTION = "八案四端审核"


def format_line(case: str, gate: str, version: str, note: str = "", url: str = "", day: str | None = None) -> str:
    when = day or date.today().isoformat()
    return (
        f"- {when} `{gate}` `{case}` 版本 `{version}`"
        f"{' ' + note if note else ''}"
        f"{' ' + url if url else ''}\n"
    )


def insert_line(prev: str, line: str, section_mark: str = DEFAULT_SECTION) -> str:
    stripped = line.strip()
    if stripped and stripped in prev:
        return prev
    if not prev.endswith("\n"):
        prev += "\n"
    mark = prev.find(section_mark)
    if mark == -1:
        return prev + line
    after_heading = prev.find("\n", mark)
    if after_heading == -1:
        return prev + "\n" + line
    next_heading = prev.find("\n## ", after_heading)
    if next_heading == -1:
        return prev + line
    prefix = prev[:next_heading]
    if not prefix.endswith("\n"):
        prefix += "\n"
    return prefix + line + prev[next_heading:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--gate", required=True, help="GEMINI | GROK-EXPERT | GPT-ASTRA-HIGH | PPLX-COMMITTEE")
    ap.add_argument("--version", required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--log", required=True, help="path to wiki/log.md")
    ap.add_argument("--section", default=DEFAULT_SECTION)
    args = ap.parse_args()
    line = format_line(args.case, args.gate, args.version, args.note, args.url)
    log = Path(args.log)
    prev = log.read_text(encoding="utf-8") if log.exists() else "# Wiki 变更日志\n\n"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(insert_line(prev, line, args.section), encoding="utf-8")
    print(line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
