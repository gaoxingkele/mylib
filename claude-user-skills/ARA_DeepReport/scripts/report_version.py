"""autodeepreport — 版本管理与变更日志

把"文档版本升级"语义化：根据证据账本(ledger)的跨版本 diff，自动生成 CHANGELOG，
并管理语义化版本号与带版本号的文件名。对应持续学习里的"何时更新/更新了什么"。

版本号语义（映射持续学习三场景）：
  major  新增国别/全新对象            (Class-IL)
  minor  新增维度/章节、结构性扩展     (Task-IL，参数隔离式挂载)
  patch  事实更新/勘误/时效刷新        (Domain-IL，时效复检)

用法：
  python report_version.py bump <current> <major|minor|patch>
  python report_version.py changelog <old_ledger.json> <new_ledger.json> \
         --version 2.0.0 --date 2026-06-10 [--out CHANGELOG.md] [--append]
  python report_version.py stamp <basename> <version>   # 输出带版本名: basename_v2.0.0
"""
import argparse
import json
import sys
import io
import os
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def bump(current, kind):
    parts = (current or "0.0.0").split(".")
    while len(parts) < 3:
        parts.append("0")
    major, minor, patch = (int(x) for x in parts[:3])
    if kind == "major":
        major, minor, patch = major + 1, 0, 0
    elif kind == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return {c["id"]: c for c in json.load(f).get("claims", [])}


def changelog(old_path, new_path, version, on, out, append):
    old = _load(old_path) if os.path.exists(old_path) else {}
    new = _load(new_path)
    added, revised, flipped, preserved, removed = [], [], [], [], []
    for cid, n in new.items():
        if cid not in old:
            added.append(n)
        else:
            o = old[cid]
            if o.get("status") != n.get("status"):
                flipped.append((o, n))
            elif o.get("value") != n.get("value"):
                revised.append((o, n))
            else:
                preserved.append(n)
    removed = [o for cid, o in old.items() if cid not in new]

    lines = [f"## v{version} — {on}", ""]
    lines.append(f"> 变更统计：新增 {len(added)} · 修订 {len(revised)} · 翻案 {len(flipped)} · "
                 f"保留(不遗忘) {len(preserved)} · 移除 {len(removed)}")
    lines.append("")
    if added:
        lines.append("### 新增断言")
        for c in added:
            src = f"（{len(c.get('sources', []))} 源）" if c.get("sources") else "（⚠无源）"
            lines.append(f"- **[{c['dimension']}]** {c['text']} = {c.get('value','')} {src}")
        lines.append("")
    if revised:
        lines.append("### 修订（数值/结论更新）")
        for o, n in revised:
            lines.append(f"- **[{n['dimension']}]** {n['text']}：~~{o.get('value','')}~~ → "
                         f"**{n.get('value','')}**" + (f"　_{n.get('note','')}_" if n.get('note') else ""))
        lines.append("")
    if flipped:
        lines.append("### 翻案（结论状态变化）")
        for o, n in flipped:
            lines.append(f"- **[{n['dimension']}]** {n['text']}：`{o.get('status')}` → "
                         f"`{n.get('status')}`" + (f"　_{n.get('note','')}_" if n.get('note') else ""))
        lines.append("")
    if removed:
        lines.append("### 移除")
        for o in removed:
            lines.append(f"- **[{o['dimension']}]** {o['text']}")
        lines.append("")
    block = "\n".join(lines)

    if out:
        mode = "a" if append and os.path.exists(out) else "w"
        header = "" if (append and os.path.exists(out)) else "# 变更日志（CHANGELOG）\n\n"
        with open(out, mode, encoding="utf-8") as f:
            f.write(header + block + "\n")
        print(f"CHANGELOG 已{'追加' if mode=='a' else '写入'}: {out}")
    print(block)


def main():
    p = argparse.ArgumentParser(description="autodeepreport 版本管理")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("bump"); s.add_argument("current"); s.add_argument("kind", choices=["major", "minor", "patch"])
    s.set_defaults(fn=lambda a: print(bump(a.current, a.kind)))

    s = sub.add_parser("changelog")
    s.add_argument("old"); s.add_argument("new")
    s.add_argument("--version", required=True)
    s.add_argument("--date", dest="on", default=str(date.today()))
    s.add_argument("--out", default=None)
    s.add_argument("--append", action="store_true")
    s.set_defaults(fn=lambda a: changelog(a.old, a.new, a.version, a.on, a.out, a.append))

    s = sub.add_parser("stamp"); s.add_argument("basename"); s.add_argument("version")
    s.set_defaults(fn=lambda a: print(f"{a.basename}_v{a.version}"))

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
