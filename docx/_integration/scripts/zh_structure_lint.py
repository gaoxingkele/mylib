#!/usr/bin/env python3
"""中文申报书/论文的“AI 腔”结构指标检查（不是 AI 作者判定器）。

与 academic-humanizer 分工：
  - academic-humanizer/scripts/deai.py、authenticity_audit.py 负责词句级命中
    （套话、空泛归因、模板开头等）和改写越界门禁；
  - 本脚本只看**结构**：并列堆叠、顿号密度、长段、自造框架数量、条件限定语密度、
    行话密度、长句比例。这些是“读着像 AI”最常见、又最容易量化的成因。

用法：
  python zh_structure_lint.py check FILE [--from-para N] [--json OUT] [--top 8]
  python zh_structure_lint.py compare BEFORE AFTER [--json OUT]

FILE 支持 .docx / .md / .txt。阈值为暂定值（见 THRESHOLDS），来源与校准记录见
docx/_integration/evals/README.md。指标命中只是“该处值得人看一眼”的线索，
修复必须靠删减并列、补机制句、绑定证据，不能靠同义替换或故意加噪。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

# 暂定阈值：超过即 flag。每千字口径按去空白后的字符数计算。
THRESHOLDS = {
    "dunhao_per_k": 30.0,        # 顿号/千字
    "long_para_ratio": 0.20,     # ≥250 字段落占正文段落比例
    "frame_kinds": 4,            # 自造“数字+框架词”的不同种类数
    "enum_chain_per_k": 1.0,     # “一是/二是”“其一/其二”式链/千字
    "stack_per_k": 2.0,          # ≥4 项顿号并列/千字
    "jargon_per_k": 6.0,         # 行话词/千字
    "long_sentence_ratio": 0.25, # >80 字句子比例
    "qualifier_per_k": 1.5,      # “在取得授权/经审核后”式条件限定语/千字
}

JARGON = [
    "赋能", "闭环", "抓手", "全链条", "全链路", "全方位", "多维度", "深度融合", "体系化",
    "一体化", "底座", "生态", "矩阵", "范式", "打通", "落地", "沉淀", "颗粒度", "赛道",
    "双轮驱动", "引擎", "链路", "全栈", "飞轮", "护城河", "抓手", "顶层设计", "提质增效",
    "降本增效", "数智", "智能化升级", "全生命周期", "多源异构", "协同联动",
]
FRAME_RE = re.compile(
    r"(?<![0-9０-９第])([二三四五六七八九十两]|[2-9])"
    r"(?:大|个|项|类|层|重|条|级|位)?"
    r"(环节|步走|步|维度|维|层次|模块|支柱|引擎|闭环|体系|机制|能力|路径|抓手|中心|平台|方向|挑战|难题|目标|任务|原则|阶段)"
)
ENUM_RE = re.compile(r"(一是|其一|第一[，,、])[^。；]{0,200}?(二是|其二|第二[，,、])")
STACK_RE = re.compile(r"(?:[^、，。；：\s]{1,12}、){3,}[^、，。；：\s]{1,12}")
NOT_BUT_RE = re.compile(r"不是[^。；]{1,40}而是")
PLACEHOLDER_RE = re.compile(r"【[^】]*】")
QUALIFIER_RE = re.compile(
    r"(?:在|经|按|依|待|取得|获得|通过|满足|具备)[^，。；]{0,24}?"
    r"(?:授权|审核|复核|许可|同意|条件)(?:后|下|前|的前提|范围内|时)?"
)


def read_paragraphs(path: Path) -> list[str]:
    if path.suffix.lower() == ".docx":
        xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
        paras = []
        for p in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
            t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).strip()
            if t:
                paras.append(t)
        return paras
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = re.sub(r"^#+\s*|^[-*>]\s+|\|", "", block.strip(), flags=re.M)
        block = " ".join(x.strip() for x in block.splitlines()).strip()
        if block:
            out.append(block)
    return out


def nchar(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def repeated_phrases(paras: list[str], n: int = 6, min_count: int = 4) -> list[tuple[str, int]]:
    cnt: Counter[str] = Counter()
    for p in paras:
        s = PLACEHOLDER_RE.sub("", re.sub(r"\s", "", p))
        seen = set()
        for i in range(len(s) - n + 1):
            g = s[i:i + n]
            if re.search(r"[0-9A-Za-z%．.]", g) or re.search(r"[，。；：、（）“”]", g):
                continue
            if g not in seen:
                seen.add(g)
                cnt[g] += 1
    hits = [(g, c) for g, c in cnt.items() if c >= min_count]
    hits.sort(key=lambda x: (-x[1], x[0]))
    kept: list[tuple[str, int]] = []
    for g, c in hits:  # 去掉被已保留短语覆盖的重叠片段
        if any(g[1:] in k or g[:-1] in k for k, _ in kept):
            continue
        kept.append((g, c))
    return kept


def analyse(paras: list[str], top: int = 8) -> dict:
    body = [p for p in paras if nchar(p) >= 30]  # 去掉标题、表格短格
    text = "\n".join(body)
    n = max(nchar(text), 1)
    k = n / 1000
    sentences = [s for s in re.split(r"[。！？；]", text) if nchar(s) >= 4]
    long_s = [s for s in sentences if nchar(s) > 80]
    long_p = [p for p in body if nchar(p) >= 250]
    frames = Counter(m.group(0) for m in FRAME_RE.finditer(text))
    jargon = Counter()
    for w in set(JARGON):
        c = text.count(w)
        if c:
            jargon[w] = c
    stacks = [m.group(0) for m in STACK_RE.finditer(text)]
    enums = ENUM_RE.findall(text)
    reps = repeated_phrases(body)
    m = {
        "chars": n,
        "body_paragraphs": len(body),
        "dunhao_per_k": round(text.count("、") / k, 1),
        "long_para_ratio": round(len(long_p) / max(len(body), 1), 2),
        "long_paras": len(long_p),
        "frame_kinds": len(frames),
        "enum_chain_per_k": round(len(enums) / k, 2),
        "stack_per_k": round(len(stacks) / k, 2),
        "jargon_per_k": round(sum(jargon.values()) / k, 1),
        "long_sentence_ratio": round(len(long_s) / max(len(sentences), 1), 2),
        "qualifier_per_k": round(len(QUALIFIER_RE.findall(text)) / k, 2),
        "repeat_phrases": len(reps),
        "not_but": len(NOT_BUT_RE.findall(text)),
        "placeholders": len(PLACEHOLDER_RE.findall(text)),
    }
    flags = [key for key, th in THRESHOLDS.items() if m[key] > th]
    evidence = {
        "frames": frames.most_common(top),
        "jargon": jargon.most_common(top),
        "stacks": [s[:60] for s in stacks[:top]],
        "repeat_phrases": reps[:top],
        "qualifiers": Counter(QUALIFIER_RE.findall(text)).most_common(top),
        "long_paras": [p[:40] + f"…({nchar(p)}字)" for p in sorted(long_p, key=nchar, reverse=True)[:top]],
    }
    return {"metrics": m, "thresholds": THRESHOLDS, "flags": flags, "evidence": evidence}


FIX_HINT = {
    "dunhao_per_k": "把 4 项以上的顿号并列拆成句子，或只保留与本段主张直接相关的 1–2 项",
    "long_para_ratio": "一段只推进一个主张；按“主张—证据—限定”拆段",
    "frame_kinds": "全文只保留一套分解框架，其余改写成对它的引用",
    "enum_chain_per_k": "“一是二是三是”改为有因果或递进关系的句子",
    "stack_per_k": "并列名词串换成“做什么—为什么—怎么验”",
    "jargon_per_k": "行话换成具体对象和动作（谁、对什么、做了什么）",
    "long_sentence_ratio": "超过 80 字的句子拆开，先说结论再说条件",
    "qualifier_per_k": "授权/审核类限定语集中写在一处（如数据治理段），其他位置删除",
}


def print_report(path: Path, r: dict) -> None:
    m = r["metrics"]
    print(f"# {path.name}")
    print(f"正文 {m['chars']} 字 / {m['body_paragraphs']} 段；占位符 {m['placeholders']}")
    for key, th in THRESHOLDS.items():
        mark = "FLAG" if key in r["flags"] else "ok  "
        print(f"  {mark} {key:20s} {m[key]!s:>6} (阈值 {th})")
    print(f"  info not_but={m['not_but']} long_paras={m['long_paras']} repeat_phrases={m['repeat_phrases']}")
    ev = r["evidence"]
    if ev["frames"]:
        print("  框架:", "、".join(f"{a}×{b}" for a, b in ev["frames"]))
    if ev["jargon"]:
        print("  行话:", "、".join(f"{a}×{b}" for a, b in ev["jargon"]))
    if ev["qualifiers"]:
        print("  限定语:", "；".join(f"{a}×{b}" for a, b in ev["qualifiers"][:5]))
    if ev["repeat_phrases"]:
        print("  重复短语:", "；".join(f"{a}×{b}" for a, b in ev["repeat_phrases"]))
    if ev["long_paras"]:
        print("  最长段:", "；".join(ev["long_paras"][:3]))
    for f in r["flags"]:
        print(f"  修法[{f}]: {FIX_HINT[f]}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file", type=Path)
    c.add_argument("--from-para", type=int, default=1, help="从第 N 个非空段落起算（跳过封面/表格）")
    c.add_argument("--top", type=int, default=8)
    c.add_argument("--json", type=Path)
    g = sub.add_parser("compare")
    g.add_argument("before", type=Path)
    g.add_argument("after", type=Path)
    g.add_argument("--from-para", type=int, default=1)
    g.add_argument("--json", type=Path)
    a = ap.parse_args()

    if a.cmd == "check":
        r = analyse(read_paragraphs(a.file)[a.from_para - 1:], a.top)
        print_report(a.file, r)
        out = r
        code = 1 if r["flags"] else 0
    else:
        rb = analyse(read_paragraphs(a.before)[a.from_para - 1:])
        ra = analyse(read_paragraphs(a.after)[a.from_para - 1:])
        print(f"{'指标':22s}{'前':>8}{'后':>8}")
        worse = []
        for key in ["chars", "placeholders", *THRESHOLDS]:
            b, f = rb["metrics"][key], ra["metrics"][key]
            tag = ""
            if key in THRESHOLDS and f > b and f > THRESHOLDS[key]:
                tag = "  ↑超阈"
                worse.append(key)
            print(f"{key:22s}{b!s:>8}{f!s:>8}{tag}")
        out = {"before": rb, "after": ra, "worse": worse}
        code = 1 if worse else 0
    if a.json:
        a.json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
