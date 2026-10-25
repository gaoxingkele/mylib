#!/usr/bin/env python3
"""去 AI 痕迹统一动作：一个入口完成"识别 → 改写后门禁"。不是 AI 作者判定器。

用法：
  python deai.py check <file> --profile patent|paper [--claims 02_权利要求书.md] [--json out.json] [--top 30]
  python deai.py gate <original> <revised> --profile patent|paper [--json out.json]

check 合并三部分：
  1. 规则库 references/deai_rules.json（第三方 10 个清单 + 本机 authenticity_audit 与 check_ai_traces 词表，
     由 build_deai_rules.py 生成）按 profile 过滤后的命中，按段落定位；
  2. 结构指标：patent 用 paa/scripts/check_ai_traces.py（模板化分、只写做法不交代原因、先用后定义等）；
     英文 paper 用超额词密度（Kobak 等 2025 的 2024 年超额词）；
  3. 改写禁用手段（forbidden）的现存命中，供改写前知悉。
gate 检查改写是否越界：受保护片段（数字、单位、图号、权利要求号、引文号）不得增删；patent 段号集合不得变化；
  gate=True 的禁用手段数量不得增加；计分命中总数与结构分不得上升。任何一项不过即 FAIL。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MYLIB = HERE.parents[1]
RULES = HERE.parent / "references" / "deai_rules.json"
CT_PATH = MYLIB / "paa" / "scripts" / "check_ai_traces.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AA = _load(HERE / "authenticity_audit.py", "authenticity_audit")
CT = _load(CT_PATH, "check_ai_traces")
# 专利文体中的正当用法：同时（时间上同时）、此外（另列实施方式）不计为套话
PATENT_SAFE = {"同时"}


def is_english(s: str) -> bool:
    latin = len(re.findall(r"[A-Za-z]", s))
    han = len(re.findall(r"[一-鿿]", s))
    return latin > 2 * han


PATENT_MASK = re.compile(r"如图\s*\d+[（(]?[a-z]?[）)]?\s*所示|步骤\s*S\d+|\$[^$\n]+\$|(?:所要|进一步要)?解决的技术问题是|绝对(?:值|误差|偏差|尺寸)|系统性(?:偏差|误差|偏离)")


def units(path: Path, profile: str) -> list[tuple[str, str]]:
    """切成 (定位, 文本)。md 跳过标题、引用行；有 [00xx] 段号的按段号，否则按行号。"""
    text, _ = AA.read_text(path)
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("#", ">", "|---")):
            continue
        m = re.match(r"\[(\d{4})\]\s*(.*)", s)
        out.append((f"[{m.group(1)}]" if m else f"L{i}", m.group(2) if m else s))
    return out


def compiled_rules(profile: str):
    data = json.loads(RULES.read_text(encoding="utf-8"))
    rules = []
    for r in data["rules"]:
        if profile not in r["profiles"]:
            continue
        flags = re.IGNORECASE if r["ignore_case"] else 0
        rules.append((r, [re.compile(p, flags | re.MULTILINE) for p in r["patterns"]]))
    return rules, data.get("excess_vocab_en", [])


def scan(path: Path, profile: str) -> dict:
    rules, vocab = compiled_rules(profile)
    U = units(path, profile)
    hits = []
    for loc, raw in U:
        txt = AA.mask_quoted_and_code(raw)
        if profile == "patent":
            txt = PATENT_MASK.sub(lambda m: " " * len(m.group(0)), txt)
        eng = is_english(txt)
        for r, pats in rules:
            if (r["lang"] == "en") != eng and r["lang"] != "mixed":
                continue
            for rx in pats:
                for m in rx.finditer(txt):
                    if m.group(0).strip() and not (profile == "patent" and m.group(0) in PATENT_SAFE):
                        hits.append(dict(loc=loc, id=r["id"], role=r["role"], category=r["category"],
                                         weight=r["profiles"][profile], gate=r.get("gate", False), text=raw[m.start():m.end()][:40]))
    body = "".join(t for _, t in U)
    k = max(len(body), 1) / 1000
    scored = [h for h in hits if h["role"] == "flag" and h["weight"] == 1]
    res = dict(file=str(path), profile=profile, units=len(U), chars=len(body),
               flag_hits=len(scored), flag_per_1k=round(len(scored) / k, 2),
               by_category=dict(Counter(h["category"] for h in scored).most_common()),
               info_hits=sum(1 for h in hits if h["role"] == "flag" and h["weight"] == 0),
               forbidden_present=dict(Counter(h["id"] for h in hits if h["gate"])),
               hits=hits)
    words = re.findall(r"[A-Za-z]+", body.lower())
    if profile == "paper" and len(words) > 200:
        vs = set(vocab)
        c = Counter(w for w in words if w in vs)
        res["excess_vocab_per_1k_words"] = round(sum(c.values()) / len(words) * 1000, 2)
        res["excess_vocab_top"] = dict(c.most_common(15))
    return res


def structure(path: Path, profile: str, claims: Path | None) -> dict | None:
    if profile != "patent":
        return None
    text = path.read_text(encoding="utf-8")
    if not re.search(r"^\[\d{4}\]", text, re.M):
        return None
    r = CT.run(str(path), str(claims) if claims else None)
    return dict(score=r["score"], metrics=r["metrics"], flags=r["flags"])


def check(path: Path, profile: str, claims: Path | None) -> dict:
    res = scan(path, profile)
    res["structure"] = structure(path, profile, claims)
    res["disclaimer"] = "启发式写作质量审查，命中是审查线索，不是 AI 作者判定；改写只动表述，不动事实、数据与保护范围。"
    return res


def para_ids(path: Path) -> list[str]:
    return re.findall(r"^\[(\d{4})\]", path.read_text(encoding="utf-8"), re.M)


def gate(orig: Path, rev: Path, profile: str) -> dict:
    a, b = check(orig, profile, None), check(rev, profile, None)
    # 受保护片段只比对正文单元（与 check 同口径：md 的标题行、">" 备注行不随申请提交，不计入）
    ta = "\n".join(x for _, x in units(orig, profile))
    tb = "\n".join(x for _, x in units(rev, profile))
    pa, pb = AA.protected_tokens(ta), AA.protected_tokens(tb)
    removed, added = AA.counter_difference(pa, pb), AA.counter_difference(pb, pa)
    cmp = dict(protected_tokens_removed=removed, protected_tokens_added=added,
               manual_semantic_checks=["因果与强度措辞", "限定范围与不确定性", "术语与定义", "引文、公式与引用关系"])
    fails, warns = [], []
    if removed or added:
        fails.append(f"受保护片段变化：删 {removed}，增 {added}")
    if profile == "patent" and orig.suffix == ".md" and para_ids(orig) != para_ids(rev):
        fails.append("段号集合或顺序变化")
    fa, fb = Counter(a["forbidden_present"]), Counter(b["forbidden_present"])
    inc = {k: fb[k] - fa[k] for k in fb if fb[k] > fa[k]}
    if inc:
        fails.append(f"禁用手段新增：{inc}")
    if b["flag_hits"] > a["flag_hits"]:
        fails.append(f"计分命中上升 {a['flag_hits']}→{b['flag_hits']}")
    sa, sb = a["structure"], b["structure"]
    if sa and sb and sb["score"] > sa["score"]:
        fails.append(f"结构模板化分上升 {sa['score']}→{sb['score']}")
    ga = Counter(h["id"] for h in a["hits"] if h["role"] == "guard")
    gb = Counter(h["id"] for h in b["hits"] if h["role"] == "guard")
    if ga != gb:
        warns.append(f"保留项数量变化：{dict(ga)} → {dict(gb)}")
    return dict(result="PASS" if not fails else "FAIL", fails=fails, warns=warns,
                before=dict(flag_hits=a["flag_hits"], structure=sa and sa["score"]),
                after=dict(flag_hits=b["flag_hits"], structure=sb and sb["score"]), compare=cmp)


def print_check(r: dict, top: int) -> None:
    s = r["structure"]
    print(f"[{r['file']}] profile={r['profile']} 单元 {r['units']} 字符 {r['chars']}")
    print(f"  计分命中 {r['flag_hits']}（{r['flag_per_1k']}/千字）；提示命中 {r['info_hits']}；"
          f"现存禁用手段 {r['forbidden_present'] or '无'}" + (f"；结构模板化分 {s['score']}" if s else ""))
    print("  分类：", r["by_category"])
    if "excess_vocab_per_1k_words" in r:
        print(f"  英文超额词 {r['excess_vocab_per_1k_words']}/千词：{r['excess_vocab_top']}")
    by = defaultdict(list)
    for h in r["hits"]:
        if h["role"] == "flag" and h["weight"] == 1:
            by[h["loc"]].append(f"{h['id']}「{h['text']}」")
    for loc, v in list(by.items())[:top]:
        print("   -", loc, "；".join(v))
    if s:
        for f in s["flags"][:top]:
            print("   *", f[0], f[1], f[3])
    print("  ", r["disclaimer"])


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file", type=Path)
    c.add_argument("--claims", type=Path)
    c.add_argument("--top", type=int, default=30)
    g = sub.add_parser("gate")
    g.add_argument("original", type=Path)
    g.add_argument("revised", type=Path)
    for p in (c, g):
        p.add_argument("--profile", choices=("patent", "paper"), required=True)
        p.add_argument("--json", type=Path)
    a = ap.parse_args()
    if a.cmd == "check":
        r = check(a.file, a.profile, a.claims)
        print_check(r, a.top)
    else:
        r = gate(a.original, a.revised, a.profile)
        print(f"GATE {r['result']}  before {r['before']}  after {r['after']}")
        for f in r["fails"]:
            print("  FAIL", f)
        for w in r["warns"]:
            print("  WARN", w)
    if a.json:
        a.json.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if a.cmd == "check" or r["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
