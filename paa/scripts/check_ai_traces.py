# -*- coding: utf-8 -*-
"""专利说明书 AI 痕迹与叙事连贯性确定性检查（只读，不改文）。

用法：python check_ai_traces.py 03_说明书.md [--claims 02_权利要求书.md] [--json out.json] [--top 15]

六类检查（均为启发式信号，用于定位段落，不是判决）：
 A 套话与AI腔词：高频过渡/拔高/营销词、"首先…其次…最后"三段式、破折号与冒号堆叠
 B 术语堆砌：括号/引号内定义的新造术语密度；单段新造术语过多
 C 句式模板化：句首重复、句长离散度过低（节奏平）、连接词过密
 D 段落局部叙事：段内是否有 动机/问题(why)、做法(how)、落点(so)；只罗列做法不交代原因的段落
 E 首尾呼应：技术问题关键词在实施方式/效果中的回扣；权利要求步骤名在说明书中的覆盖
 F 递进：段间显式承接的密度；新术语先定义后使用
分数越高越像模板化文本；阈值在 THRESH 中调整。
"""
import re, sys, json, statistics, argparse, collections

THRESH = dict(filler_per_1k=1.2, dash_per_1k=3.0, define_per_1k=2.2, para_define_max=3,
              opener_dup=4, sent_cv_min=0.45, conn_per_1k=14.0, why_missing_min_len=160)

FILLER = ["值得注意的是", "需要指出的是", "需要说明的是", "不难看出", "由此可见", "综上所述", "总而言之", "毋庸置疑", "显而易见",
          "赋能", "打造", "闭环", "范式", "底层逻辑", "深度融合", "全方位", "多维度", "全链路", "一站式", "有力支撑", "极大地",
          "显著提升", "大幅", "领先", "革命性", "创新性地", "突破性", "无缝", "智能化升级", "核心竞争力"]
CONNECT = ["因此", "从而", "由此", "进而", "并且", "同时", "其中", "此外", "另外", "进一步地", "相应地", "具体地", "优选地", "换言之"]
WHY = ["为了", "由于", "因为", "针对", "以便", "使得", "避免", "防止", "原因", "否则", "若不", "不能", "无法", "需要", "以免", "因而", "故"]
SO = ["从而", "使得", "因此", "故", "用于", "以便", "由此", "得到", "即", "可", "能够", "保证"]
BACK = re.compile(r"\[\d{4}\]|如前所述|前述|上述步骤|在此基础上|承接|沿用|同一|仍按")
DEFINE = re.compile(r"[（(]“[^”]{2,20}”(?:指|是指|即|为)[^）)]{4,}[）)]|“[^”]{2,16}”(?:指|是指|即指)")
DEF1 = re.compile(r"“([^”]{2,14})”(?:指|是指|即指)")


def load(path):
    t = open(path, encoding="utf-8").read()
    t = re.sub(r"\$\$.*?\$\$", "", t, flags=re.S)
    t = re.sub(r"\\\[.*?\\\]|\\\(.*?\\\)", "", t, flags=re.S)
    t = re.sub(r"\$[^$\n]{1,200}\$", "", t)
    return t


def paragraphs(t):
    secs, paras = ["前言"], []
    for line in t.splitlines():
        if line.startswith("#"):
            secs.append(line.lstrip("# ").strip())
            continue
        m = re.match(r"\[(\d{4})\]\s*(.+)", line)
        if m:
            paras.append(dict(no=m.group(1), text=m.group(2), sec=secs[-1]))
    return paras


def sents(s):
    return [x for x in re.split(r"[。；;！？]", s) if len(x.strip()) > 3]


def count(text, words):
    return sum(text.count(w) for w in words)


def run(spec_path, claims_path=None):
    t = load(spec_path)
    P = paragraphs(t)
    out = dict(file=spec_path, paragraphs=len(P), flags=[], metrics={})
    body = "".join(p["text"] for p in P)
    k = max(len(body), 1) / 1000
    M = out["metrics"]
    # A
    fill = {w: body.count(w) for w in FILLER if body.count(w)}
    M["filler_per_1k"] = round(sum(fill.values()) / k, 2)
    M["filler_hits"] = fill
    M["dash_per_1k"] = round(body.count("——") / k, 2)
    M["colon_per_1k"] = round(body.count("：") / k, 2)
    M["first_second_last"] = len(re.findall(r"首先[^。]{0,200}其次[^。]{0,200}(?:最后|再次)", body))
    for p in P:
        h = [w for w in FILLER if w in p["text"]]
        if h:
            out["flags"].append(("A套话", p["no"], p["sec"], "、".join(h)))
    # B
    defs = [len(DEFINE.findall(p["text"])) for p in P]
    M["define_per_1k"] = round(sum(defs) / k, 2)
    for p, d in zip(P, defs):
        if d > THRESH["para_define_max"]:
            out["flags"].append(("B术语堆砌", p["no"], p["sec"], f"本段新造定义术语 {d} 个"))
    # C
    first = collections.Counter()
    lens = []
    for p in P:
        for s in sents(p["text"]):
            first[s.strip()[:6]] += 1
            lens.append(len(s))
    dup = {a: v for a, v in first.items() if v >= THRESH["opener_dup"] and len(a) == 6}
    M["opener_dups_top"] = dict(sorted(dup.items(), key=lambda x: -x[1])[:8])
    cv = statistics.pstdev(lens) / statistics.mean(lens) if lens else 0
    M["sent_len_cv"] = round(cv, 3)
    M["sent_mean_len"] = round(statistics.mean(lens), 1) if lens else 0
    M["long_sent_gt120_share"] = round(sum(1 for x in lens if x > 120) / max(len(lens), 1), 3)
    M["connective_per_1k"] = round(count(body, CONNECT) / k, 2)
    for p in P:
        c = count(p["text"], CONNECT)
        if len(p["text"]) > 0 and c / (len(p["text"]) / 1000) > 40 and c >= 5:
            out["flags"].append(("C连接词过密", p["no"], p["sec"], f"{c} 个"))
    # D
    nowhy, noso = [], []
    for p in P:
        tx = p["text"]
        if len(tx) >= THRESH["why_missing_min_len"] and count(tx, WHY) == 0 and p["sec"] in ("技术方案", "具体实施方式", "发明内容") and not tx.startswith(("为实现", "本发明提供")) and not re.match(r"^[一-龥]{2,12}步骤[：（]", tx):
            nowhy.append(p["no"])
            out["flags"].append(("D只写做法不交代原因", p["no"], p["sec"], tx[:40] + "…"))
        if len(tx) >= 160 and count(tx, SO) == 0 and p["sec"] == "具体实施方式":
            noso.append(p["no"])
            out["flags"].append(("D段末无落点", p["no"], p["sec"], tx[:40] + "…"))
    M["paras_no_why"] = len(nowhy)
    M["paras_no_closure"] = len(noso)
    # E
    prob = next((p["text"] for p in P if p["sec"] == "技术问题" or "要解决的技术问题" in p["text"]), "")
    pc = re.sub(r"[^一-龥]", "", prob)
    keys = sorted({pc[i:i + 4] for i in range(len(pc) - 3)})
    eff = re.sub(r"[^一-龥]", "", "".join(p["text"] for p in P if p["sec"] == "具体实施方式" or "效果" in p["sec"] or "计算例" in p["sec"]))
    cover = [w for w in keys if w in eff]
    M["problem_keys"] = len(keys)
    M["problem_keys_echoed"] = len(cover)
    if keys and len(cover) / len(keys) < 0.25:
        out["flags"].append(("E首尾呼应弱", "[0007]", "技术问题", f"技术问题用语在实施方式中回扣 {len(cover)}/{len(keys)}"))
    if claims_path:
        c = open(claims_path, encoding="utf-8").read()
        steps = sorted({re.sub(r"^(?:的|和|在|可由|并|及|与|或|按|由)+", "", x) for x in re.findall(r"所述([一-龥]{2,12}(?:步骤|模块|单元|阶段))", c)})
        miss = [s for s in steps if s not in body]
        M["claim_terms"] = len(steps)
        M["claim_terms_missing_in_spec"] = miss[:20]
        for s in miss[:20]:
            out["flags"].append(("E权利要求词未入说明书", "-", "-", s))
    # F
    M["back_ref_share"] = round(sum(1 for p in P if BACK.search(p["text"])) / max(len(P), 1), 3)
    defpos, firstuse = {}, {}
    for i, p in enumerate(P):
        for m in DEF1.finditer(p["text"]):
            defpos.setdefault(m.group(1), i)
    for i, p in enumerate(P):
        for w in defpos:
            if w in p["text"]:
                firstuse.setdefault(w, i)
    for w, di in defpos.items():
        if firstuse.get(w, di) < di:
            out["flags"].append(("F先用后定义", P[di]["no"], P[di]["sec"], f"“{w}”首次使用于第{P[firstuse[w]]['no']}段，定义在第{P[di]['no']}段"))
    # 评分
    sc = 0
    sc += min(M["filler_per_1k"] / THRESH["filler_per_1k"], 3) * 10
    sc += min(M["dash_per_1k"] / THRESH["dash_per_1k"], 3) * 5
    sc += min(M["define_per_1k"] / THRESH["define_per_1k"], 3) * 10
    sc += min(max(THRESH["sent_cv_min"] - M["sent_len_cv"], 0) / THRESH["sent_cv_min"], 1) * 15
    sc += min(M["connective_per_1k"] / THRESH["conn_per_1k"], 2) * 10
    sc += min(M["paras_no_why"] / max(len(P), 1) * 10, 1) * 15
    sc += min(len(dup), 5) * 2 + M["first_second_last"] * 3
    out["score"] = round(sc, 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--claims")
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    r = run(a.spec, a.claims)
    print(f"[{r['file']}] 段落 {r['paragraphs']}  模板化分 {r['score']}（越高越像模板文本）")
    for k, v in r["metrics"].items():
        print(f"  {k}: {v}")
    print("  标记:", dict(collections.Counter(f[0] for f in r["flags"])))
    for f in r["flags"][:a.top]:
        print("   -", f[0], f[1], f[2], f[3])
    if a.json:
        json.dump(r, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
