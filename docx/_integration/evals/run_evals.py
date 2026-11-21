#!/usr/bin/env python3
"""运行 zh_structure_lint 回归样例：python run_evals.py（全部通过返回 0）。"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import zh_structure_lint as lint  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
fails = 0
for c in json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]:
    r = lint.analyse(lint.read_paragraphs(HERE / c["file"]))
    flags = set(r["flags"])
    missing = [f for f in c["must_flag"] if f not in flags]
    extra = [f for f in c["must_not_flag"] if f in flags]
    ok = not missing and not extra
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {c['file']}  flags={sorted(flags)}"
          + (f"  missing={missing}" if missing else "") + (f"  unexpected={extra}" if extra else ""))
print(f"{'ALL PASS' if not fails else f'{fails} FAILED'}")
sys.exit(1 if fails else 0)
