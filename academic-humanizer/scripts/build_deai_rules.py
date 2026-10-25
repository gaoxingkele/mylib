#!/usr/bin/env python3
"""把第三方去 AI 痕迹清单（deai-sources/_catalogue.json）与本机已有规则合并成 references/deai_rules.json。

用法：python build_deai_rules.py [--catalogue <path>]
规则角色：
  flag      识别用，命中即列为审查线索（不是判决）；
  forbidden 改写时禁止采用的手段（口语化噪声、事实改写、降检测形态操纵），只在 gate 中检查"是否新增"；
  guard     过度修正防护项，改写后数量变化只作提示；
gate=True 的条目在 gate 中"改后数量增加"即判失败。
weight：按 profile 取 1（适用）或 0（caution，只提示不计分）；不适用则不收入该 profile。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MYLIB = HERE.parents[1]
DEFAULT_CAT = MYLIB / "deai-sources" / "_catalogue.json"
OUT = HERE.parent / "references" / "deai_rules.json"

FORBIDDEN_CATS = ("口语化噪声注入", "事实改写风险手段", "降检测形态操纵")
GUARD_CATS = ("过度修正防护",)
WEIGHT = {"yes": 1, "caution": 0}
# 这些 forbidden 条目的模式是第三方技能"被替换的原词"而非其引入的噪声，不能用"改后是否增加"来判定
NO_GATE = {"HOU-07", "QSL-03", "YCC-04"}
# guard 中属于噪声本身的条目，改后新增即失败
GATE_GUARD = {"XFG-15"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def to_regex(item: str, kind: str) -> str:
    if kind == "regex":
        return item
    parts = [re.escape(p) for p in item.split("…")]
    return ".{1,30}?".join(parts)


def role_of(category: str) -> str:
    if any(category.startswith(c) for c in FORBIDDEN_CATS):
        return "forbidden"
    if any(category.startswith(c) for c in GUARD_CATS):
        return "guard"
    return "flag"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", type=Path, default=DEFAULT_CAT)
    a = ap.parse_args()
    cat = json.loads(a.catalogue.read_text(encoding="utf-8"))
    rules = []
    for p in cat["patterns"]:
        kind = p["detect"]["type"]
        if kind not in ("phrase", "regex"):
            continue
        pats = []
        for it in p["detect"]["items"]:
            rx = to_regex(it, kind)
            try:
                re.compile(rx)
            except re.error:
                continue
            pats.append(rx)
        if not pats:
            continue
        role = role_of(p["category"])
        profiles = {}
        for prof, key in (("patent", "patent_applicable"), ("paper", "paper_applicable")):
            v = p.get(key, "no")
            if role != "flag":
                profiles[prof] = 0  # forbidden/guard 对所有 profile 都检查，不计分
            elif v in WEIGHT:
                profiles[prof] = WEIGHT[v]
        rules.append(dict(id=p["id"], source=p["source"], lang=p["lang"], category=p["category"], name=p["name"],
                          role=role, profiles=profiles, meaning_risk=p.get("meaning_risk", "unknown"),
                          ignore_case=p["lang"] == "en", patterns=pats, fix_hint=p.get("example_fix", ""),
                          gate=(role == "forbidden" and p["id"] not in NO_GATE) or p["id"] in GATE_GUARD))
    # 本机已有规则
    aa = load_module(HERE / "authenticity_audit.py", "authenticity_audit")
    for i, (catg, exprs) in enumerate(aa.PATTERNS.items(), 1):
        rules.append(dict(id=f"LOC-AA-{i:02d}", source="academic-humanizer", lang="mixed", category=catg, name=catg,
                          role="flag", profiles={"patent": 1, "paper": 1}, meaning_risk="low", ignore_case=True,
                          patterns=list(exprs), fix_hint="", gate=False))
    ct = load_module(MYLIB / "paa" / "scripts" / "check_ai_traces.py", "check_ai_traces")
    rules.append(dict(id="LOC-CT-01", source="paa/check_ai_traces", lang="zh", category="套话与拔高词", name="专利说明书套话词表",
                      role="flag", profiles={"patent": 1, "paper": 1}, meaning_risk="low", ignore_case=False,
                      patterns=[re.escape(w) for w in ct.FILLER], fix_hint="删去或改为可核对的具体条件与数值", gate=False))
    out = dict(
        built_from=dict(catalogue=str(a.catalogue), sources=cat["sources"]),
        roles=dict(flag="审查线索，命中不等于 AI 所写", forbidden="改写时禁止新增", guard="改写后数量变化只作提示"),
        excess_vocab_en=[w["word"] for w in cat.get("excess_vocab_en", [])],
        rules=rules,
    )
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(OUT, len(rules), Counter(r["role"] for r in rules),
          {pf: sum(1 for r in rules if r["profiles"].get(pf) == 1) for pf in ("patent", "paper")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
