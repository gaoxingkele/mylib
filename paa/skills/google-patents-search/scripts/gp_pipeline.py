#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""种子件扩检流水线：一次调用完成「多轴召回 → 去重排序 → 取原文 → 核验门禁」。

**为什么需要它**：只跑一条关键词腿时，措辞一变就漏在先技术；只跑语义腿时又要 GCP 凭据。
本脚本把四条互相独立的召回轴接成一条链，**任何一条轴不可用都如实记录**，不把「被拦」
或「缺凭据」写成「没有现有技术」。

| axis | 来源 | 前置条件 |
| --- | --- | --- |
| ``seed_citation`` | 种子件页面上的引证表（该件引用的在先公开） | 取得到种子件页面（直连或中继） |
| ``seed_similar`` | 种子件页面上的相似文献表 | 同上 |
| ``semantic`` | BigQuery ``embedding_v1`` 向量近邻（incoPat 语义检索的免费等价物） | GCP 凭据 |
| ``keyword`` | ``--query`` 显式检索式，或由种子件题名自动派生的检索式 | 免 key |

流程：召回 → 按公开号去重（保留 provenance：哪些轴发现了它）→ 启发式排序
（轴权重＋截止日资格＋题名词重合）→ 对前 N 件取原文（``google → tavily → bigquery``）
→ 生成可核验的引用骨架并跑核验门禁 → 落 ``screening.md`` / ``pipeline.json`` / ``verify.json``。

**排序只是「先看哪件」的顺序**，不是相关性结论；候选不构成本案与对比文件的异同判断，
任何 X/Y/A 判定必须由人按取回的原文作出。

用法：

  # 种子件扩检（引证轴 + 相似文献轴 + 题名派生关键词轴），并取前 6 件原文
  python gp_pipeline.py --seed CN103399241B --cutoff 2026-09-01 --out runs/p06 --audit runs/p06/audit.jsonl
  # 显式给检索式（推荐：题名派生受中文分词限制）
  python gp_pipeline.py --seed CN103399241B --query "配电变压器 温升 故障诊断" --country CN --fetch-top 8
  # 无种子也能跑（只有 keyword 轴）
  python gp_pipeline.py --query "石墨烯 眼罩" --out runs/x
  # 无中继、无语义轴的保守模式
  python gp_pipeline.py --seed CN103399241B --no-semantic --no-relay

退出码：0 有候选且至少一件取到原文（或已用 --fetch-top 0 明确跳过取件）；
4 有候选但一件原文都没取到；3 所有轴被拦/不可用；2 参数错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_backends as bk  # noqa: E402
import gp_fetch as gf  # noqa: E402
from gp_common import (  # noqa: E402
    append_audit, emit, ensure_utf8_stdio, hint, normalize_pub, note, now_iso,
    patent_url, sha256_text, split_pub, write_json,
)
from gp_verify import verify_one  # noqa: E402

EXIT_OK, EXIT_ARGS, EXIT_BLOCKED, EXIT_NO_FULLTEXT, EXIT_RUNTIME = 0, 2, 3, 4, 5

AXIS_WEIGHT = {"seed_citation": 3.0, "seed_similar": 2.0, "semantic": 2.0, "keyword": 1.0}
AXIS_ORDER = ("seed_citation", "seed_similar", "semantic", "keyword")

# 题名派生检索式时用来切分的结构性词（中英混排；切完取最长片段做检索词）
STRUCT_WORDS = (
    "一种", "一个", "基于", "用于", "及其", "以及", "包括", "涉及", "提供", "实现",
    "提高", "优化", "新型", "本实用", "本发明", "本实用新型", "的", "与", "和", "或",
    "及", "在", "中", "上", "下", "为", "是", "对其", "该", "其", "系统", "方法",
    "装置", "设备", "技术", "方案", "问题", "应用", "领域", "产品", "模块",
    "and", "of", "for", "the", "a", "an", "in", "on", "with", "to", "method",
    "system", "apparatus", "device", "based", "using", "comprising", "including",
    "present", "invention", "utility", "model", "related",
)


def seed_title_chunks(title: str) -> list:
    """把题名按结构性词切成概念片段（保留 ≥2 字的片段，长的在前）。"""
    t = (title or "").strip()
    if not t:
        return []
    pat = "|".join(re.escape(w) for w in sorted(STRUCT_WORDS, key=len, reverse=True))
    chunks = [c.strip() for c in re.split(pat, t, flags=re.I)]
    chunks = [c for c in chunks if len(c) >= 2]
    chunks.sort(key=len, reverse=True)
    return chunks


def derive_queries(title: str, country: str) -> list:
    """由种子件题名派生免 key 检索式。

    实测（2026-09-26，PATENTSCOPE）：``EN_ALLTXT:(配电变压器故障诊断)`` 召回 10 条，
    而把四个词空格相连做 AND 会掉到 0 条——该库对中文查询会自行分词，**多词 AND 反而收死**。
    因此派生顺序是「最长片段单词查询 → 两片段 AND 查询」，由调用方逐个试、命中即停。
    """
    chunks = seed_title_chunks(title)
    if not chunks:
        return []
    suffix = f" AND CTR:({country})" if country else ""
    out = [f"EN_ALLTXT:({chunks[0]}){suffix}"]
    if len(chunks) >= 2:
        out.append(f"EN_ALLTXT:({chunks[0]} {chunks[1]}){suffix}")
    return out


def run_search(query: str, args) -> dict:
    """免 key 检索腿：``google`` 被拦则自动改走 ``patentscope``，如实记录每次尝试。"""
    attempts = []
    # auto：直连（免费）→ PATENTSCOPE（免费）→ 中继检索腿（耗 Tavily 额度，仅前两者无命中时才走）
    order = ([args.search_backend] if args.search_backend != "auto"
             else ["google", "patentscope", "tavily"])
    for backend in order:
        if backend == "google":
            res = bk.google_search(query, page=args.page, lang=args.lang, timeout=args.timeout)
        elif backend == "tavily":
            res = bk.tavily_search(query, limit=max(args.limit, 10),
                                   timeout=max(args.timeout, 60), country=args.country)
        else:
            res = bk.patentscope_search(query, timeout=max(args.timeout, 45),
                                        country=args.country)
        attempts.append({"backend": backend, "blocked": bool(res.get("blocked")),
                         "error": res.get("error"), "status": res.get("status"),
                         "hits": len(res.get("hits") or []),
                         "query_used": res.get("query_used")})
        if res.get("blocked"):
            sys.stderr.write(f"GP_BLOCKED: {backend}_anti_bot\n")
            continue
        if res.get("error"):
            continue
        hits = res.get("hits") or []
        if hits:
            return {"hits": hits, "backend": backend, "url": res.get("url", ""),
                    "attempts": attempts, "blocked": False,
                    "query_used": res.get("query_used") or query}
    blocked = bool(attempts) and all(a.get("blocked") for a in attempts)
    return {"hits": [], "backend": order[-1], "url": "", "attempts": attempts,
            "blocked": blocked,
            "error": None if blocked else (attempts[-1].get("error") if attempts else "no_hits")}


def key_terms(queries: list, seed_titles: list) -> set:
    """从显式检索式与种子题名里抽出用于排序加分的词。"""
    terms = set()
    for q in queries:
        for tok in re.split(r"[\s,，、;；:：()（）\"']+", q):
            tok = re.sub(r"^(EN_ALLTXT|CTR|TI|AB|CLAIMS):", "", tok, flags=re.I)
            if len(tok) >= 2 and tok.upper() not in {"AND", "OR", "CN", "NOT"}:
                terms.add(tok)
    for t in seed_titles:
        terms.update(seed_title_chunks(t))
    return terms


def score_candidate(c: dict, cutoff: str | None, terms: set, seed_country: str) -> tuple:
    """启发式排序分：轴权重 + 截止日资格 + 题名词重合 + 同国别。只用于排序。"""
    parts = {"axis": sum(AXIS_WEIGHT.get(a, 1.0) for a in c.get("axes") or [])}
    pub = c.get("publication_date") or ""
    if cutoff:
        parts["cutoff"] = 1.0 if (pub and pub <= cutoff) else (-1.0 if pub else 0.0)
    else:
        parts["cutoff"] = 0.0
    title = c.get("title") or ""
    hit = [t for t in terms if t and t in title]
    parts["term_overlap"] = round(2.0 * (len(hit) / max(len(terms), 1)), 3)
    country = split_pub(c["pub_number"])[0]
    parts["same_country"] = 0.5 if (seed_country and country == seed_country) else 0.0
    if not pub:
        parts["unknown_date"] = -0.25      # 公开日未知则无法做「申请日前公开」资格判断
    return round(sum(parts.values()), 3), parts


def render_screening_md(ctx: dict) -> str:
    L = ["# 现有技术候选筛查报告（种子件扩检流水线）", "",
         f"- 种子件：{', '.join(ctx['seeds']) or '（无）'}",
         f"- 显式检索式：{'; '.join(ctx['queries']) or '（无）'}",
         f"- 派生检索式：{'; '.join(ctx['derived_queries']) or '（无）'}",
         f"- 国别/截止日：{ctx['country'] or '不限'} / {ctx['cutoff'] or '不限'}",
         f"- 生成时间：{ctx['generated_at']}",
         "- 性质：本文件是**候选筛查**，不是检索结论；排序分只决定先看哪件。", "",
         "## 一、召回轴覆盖（任一轴不可用都如实列出）", "",
         "| axis | 状态 | 候选数 | 说明 |", "| --- | --- | --- | --- |"]
    for axis in AXIS_ORDER:
        d = ctx["axes"].get(axis) or {"status": "not_requested", "count": 0, "detail": ""}
        L.append("| {} | {} | {} | {} |".format(
            axis, d.get("status"), d.get("count", 0),
            (d.get("detail") or "—").replace("|", "/")))
    L += ["", "## 二、候选池（去重后按启发式分排序）", "",
          "| # | 公开号 | 公开日 | 标题 | 来源轴 | 分 | 原文级别 | 截止日资格 |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    cutoff = ctx.get("cutoff")
    for i, c in enumerate(ctx["candidates"], 1):
        pub = c.get("publication_date") or ""
        if cutoff:
            elig = "早于截止" if (pub and pub <= cutoff) else ("晚于截止" if pub else "未知")
        else:
            elig = "未设截止"
        L.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
            i, c["pub_number"], pub or "—",
            (c.get("title") or "—").replace("|", "/")[:60],
            "/".join(c.get("axes") or []), c.get("score"),
            c.get("evidence_level") or "snippet-degraded", elig))
    L += ["", "## 三、已取原文（证据级别与留痕）", ""]
    if ctx["fetched"]:
        L += ["| 公开号 | 证据级别 | 权项数 | 说明书字数 | 取件后端 | 中继 | sha256(前12) |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
        for d in ctx["fetched"]:
            L.append("| {} | {} | {} | {} | {} | {} | {} |".format(
                d.get("pub_number"), d.get("evidence_level"), d.get("claim_count"),
                d.get("description_chars"), d.get("backend"), d.get("relay") or "—",
                (d.get("sha256") or "")[:12]))
    else:
        L.append("（未取到原文——见第五节限制；此时不得作为对比文件引用）")
    L += ["", "## 四、核验门禁", ""]
    v = ctx.get("verify")
    if v:
        L += [f"- 条目：{v['verified']}/{v['total']} 通过（all_verified={v['all_verified']}）",
              f"- 引用骨架：{ctx['artifacts'].get('citations_draft') or '—'}",
              "- 骨架里 quote=权利要求1原文，只证明「已取到原文且可逐字定位」；",
              "  真正的 X/Y/A 引用片段与角色判定须人工替换后重跑 gp_verify.py。"]
        for r in [x for x in v["records"] if x["status"] != "verified"][:10]:
            L.append(f"- 未通过 {r['pub_number']}：{', '.join(r['reasons'])}")
    else:
        L.append("（本轮未生成引用骨架：没有取到 original-text 证据）")
    L += ["", "## 五、限制与未完成项", ""]
    if ctx["limitations"]:
        for lim in ctx["limitations"]:
            L.append(f"- [{lim.get('axis') or 'pipeline'}] {lim.get('reason')}"
                     + (f"｜处置：{lim['remedy']}" if lim.get("remedy") else ""))
    else:
        L.append("- （本轮登记的轴与取件均正常，无额外限制）")
    L += ["", "## 六、使用边界", "",
          "- 本报告**不是法定检索**；所有「未发现」只能表述为「本轮检索未发现」。",
          "- relay 中继取回的文本与直连取回在 provenance 上不同；写入检索报告的引用"
          "建议同步保存同页 PDF（gp_fetch.py --save-pdf）做字节留痕。",
          "- 候选是否构成 X/Y/A 对比文件、是否影响新颖性/创造性，须由人按原文逐特征比对后作出。",
          ""]
    return "\n".join(L)


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(
        description="种子件扩检流水线（GP_PIPELINE_JSON 单行输出，无浏览器）")
    ap.add_argument("--seed", action="append", default=[], help="种子公开号，可重复")
    ap.add_argument("--query", action="append", default=[], help="显式检索式，可重复")
    ap.add_argument("--query-file", help="检索式文件（每行一条）")
    ap.add_argument("--country", help="国别（用于派生检索式与排序加分，非硬过滤）")
    ap.add_argument("--cutoff", help="公开日截止 YYYY-MM-DD（申请日前公开资格判断）")
    ap.add_argument("--limit", type=int, default=30, help="候选池上限（默认 30）")
    ap.add_argument("--per-axis", type=int, default=3,
                    help="截断时每条轴先保留的名额（默认 3，避免整条轴被挤空）")
    ap.add_argument("--fetch-top", type=int, default=6, help="对前 N 件取原文（0=只筛查）")
    ap.add_argument("--max-gb", type=float, default=20.0, help="语义轴扫描量上限（GB）")
    ap.add_argument("--no-semantic", action="store_true", help="关闭语义轴（BigQuery）")
    ap.add_argument("--no-relay", action="store_true", help="禁用第三方中继取件")
    ap.add_argument("--search-backend",
                    choices=["auto", "google", "patentscope", "tavily"], default="auto",
                    help="auto=直连→PATENTSCOPE→中继检索腿")
    ap.add_argument("--tavily-key", help="中继取件凭据（缺省读 TAVILY_API_KEY 或 .env）")
    ap.add_argument("--lang", help="取件语言路径 zh/en（默认按国家码推断）")
    ap.add_argument("--page", type=int, default=1, help="检索结果页码")
    ap.add_argument("--timeout", type=int, default=45, help="单次请求超时秒数")
    ap.add_argument("--no-citations-draft", action="store_true",
                    help="不生成引用骨架（默认生成，供 gp_verify 留痕）")
    ap.add_argument("--save-pdf", action="store_true",
                    help="对取到原文的候选同步下载同页 PDF 做字节留痕（记 pdf_sha256）")
    ap.add_argument("--out", help="输出目录（screening.md / pipeline.json / docs/ …）")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    args = ap.parse_args(argv)

    queries = list(args.query)
    if args.query_file:
        with open(args.query_file, encoding="utf-8") as fh:
            queries += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    seeds = [normalize_pub(s) for s in args.seed if s.strip()]
    if not seeds and not queries:
        ap.error("至少要给 --seed 或 --query")

    out_dir = os.path.abspath(args.out) if args.out else ""
    docs_dir = os.path.join(out_dir, "docs") if out_dir else ""
    if docs_dir:
        os.makedirs(docs_dir, exist_ok=True)

    ctx = {"seeds": seeds, "queries": queries, "derived_queries": [], "country": args.country,
           "cutoff": args.cutoff, "generated_at": now_iso(), "axes": {}, "limitations": [],
           "candidates": [], "fetched": [], "verify": None,
           "artifacts": {"dir": out_dir, "screening_md": "", "pipeline_json": "",
                         "docs_dir": docs_dir, "citations_draft": "", "verify_json": ""}}
    if not out_dir:
        ctx["limitations"].append({
            "axis": "artifacts",
            "reason": "未指定 --out：取回的原文不落盘，也不生成引用骨架与核验记录",
            "remedy": "加 --out <目录> 以保留证据留痕（docs/<PN>.json|.md|.relay.md、verify.json）"})
    candidates: dict = {}

    def add(item: dict, axis: str) -> None:
        pn = normalize_pub(item.get("pub_number") or "")
        if not pn:
            return
        c = candidates.setdefault(pn, {
            "pub_number": pn, "axes": [], "title": "", "assignee": "",
            "publication_date": "", "url": item.get("url") or "",
            "doc_id": item.get("doc_id") or "",
            "evidence_level": "snippet-degraded",
            "links": {"google_patents": patent_url(pn)}})
        if axis not in c["axes"]:
            c["axes"].append(axis)
        for k in ("title", "assignee", "publication_date", "priority_date", "url", "doc_id"):
            if not c.get(k) and item.get(k):
                c[k] = item[k]
        if item.get("doc_id") and item.get("backend") == "patentscope":
            c["links"]["patentscope"] = item.get("url") or ""

    # ------------------------------------------------------------ 种子轴：引证 + 相似文献
    seed_docs, seed_titles, seed_country = {}, [], ""
    ctx["blocked_seen"] = False
    for seed in seeds:
        res = bk.fetch_document(seed, lang=args.lang, timeout=args.timeout,
                                tavily_key=args.tavily_key, allow_relay=not args.no_relay)
        if not res.get("ok"):
            ctx["blocked_seen"] = ctx["blocked_seen"] or bool(res.get("blocked"))
            ctx["limitations"].append({
                "axis": "seed", "reason": f"种子件 {seed} 页面未取到（{res.get('reason')}）",
                "remedy": res.get("remedy"), "attempts": res.get("attempts")})
            for axis, label in (("seed_citation", "引证表"), ("seed_similar", "相似文献表")):
                ctx["axes"].setdefault(axis, {
                    "status": "unavailable", "count": 0,
                    "detail": "种子件页面未取到（{}），{}不可用".format(res.get("reason"), label)})
            continue
        doc = res["doc"]
        seed_docs[seed] = doc
        if doc.get("title"):
            seed_titles.append(doc["title"])
        seed_country = seed_country or split_pub(seed)[0]
        note("seed {} via {}: cited={} similar={}".format(
            seed, res["backend"], len(doc.get("cited_patents") or []),
            len(doc.get("similar_patents") or [])))
        for axis, key, label in (("seed_citation", "cited_patents", "引证表"),
                                 ("seed_similar", "similar_patents", "相似文献表")):
            items = doc.get(key) or []
            for it in items:
                add(it, axis)
            prev = ctx["axes"].get(axis) or {"count": 0, "seeds": []}
            seeds_used = list(prev.get("seeds") or []) + [seed]
            ctx["axes"][axis] = {
                "status": "ok" if (prev["count"] + len(items)) else "empty",
                "count": prev["count"] + len(items),
                "seeds": seeds_used,
                "detail": "{} 页面{}，本次 {} 条（后端 {}）".format(
                    "、".join(seeds_used), label, len(items), res["backend"])}

    # ------------------------------------------------------------ 关键词轴
    derived = []
    for t in seed_titles:
        derived += derive_queries(t, args.country or seed_country)
    ctx["derived_queries"] = derived
    all_queries = queries + [q for q in derived if q not in queries]
    if all_queries:
        hit_q, miss_q, blocked_q = [], [], []
        for q in all_queries:
            r = run_search(q, args)
            for h in r["hits"]:
                add(h, "keyword")
            if r["hits"]:
                hit_q.append(q)
            elif r.get("blocked"):
                blocked_q.append(q)
            else:
                miss_q.append(q)
            append_audit(args.audit, {"ts": now_iso(), "kind": "pipeline_search", "query": q,
                                      "backend": r["backend"], "blocked": bool(r.get("blocked")),
                                      "query_used": r.get("query_used"),
                                      "hits": len(r["hits"]), "attempts": r["attempts"]})
        n_kw = len([c for c in candidates.values() if "keyword" in c["axes"]])
        status = ("ok" if hit_q else ("blocked" if blocked_q and not miss_q else "empty"))
        ctx["axes"]["keyword"] = {
            "status": status, "count": n_kw,
            "detail": "命中 {}/{} 条检索式".format(len(hit_q), len(all_queries))}
        if not hit_q:
            ctx["limitations"].append({
                "axis": "keyword",
                "reason": "检索式全部无命中" + ("（部分被反爬拦截）" if blocked_q else ""),
                "remedy": "改用 --query 给更短的概念词（该库对中文长词会自行分词，多词 AND 易收死）"})
    else:
        ctx["axes"]["keyword"] = {"status": "not_requested", "count": 0,
                                  "detail": "未给 --query，且种子件题名不可用"}
        ctx["limitations"].append({
            "axis": "keyword", "reason": "没有可用的检索式：题名派生需要先取到种子件页面",
            "remedy": "用 --query 显式给检索式"})

    # ------------------------------------------------------------ 语义轴（BigQuery 向量近邻）
    if args.no_semantic or not seeds:
        ctx["axes"]["semantic"] = {"status": "not_requested", "count": 0,
                                   "detail": "--no-semantic 或未给种子件"}
    else:
        probe = bk.bigquery_probe()
        if probe.get("error"):
            ctx["axes"]["semantic"] = {"status": "unavailable", "count": 0,
                                       "detail": probe.get("error")}
            ctx["limitations"].append({"axis": "semantic",
                                       "reason": "语义轴不可用：{}".format(probe["error"]),
                                       "remedy": probe.get("remedy")})
        else:
            cnt = 0
            for seed in seeds:
                res = bk.bigquery_similar(seed, country=args.country, limit=args.limit,
                                          max_gb=args.max_gb)
                if res.get("error"):
                    ctx["limitations"].append({"axis": "semantic",
                                               "reason": "{}: {}".format(seed, res["error"]),
                                               "remedy": res.get("remedy")})
                    continue
                for row in res.get("hits") or []:
                    add({"pub_number": row.get("publication_number"), "url": "",
                         "title": " ".join((row.get("top_terms") or [])[:8])}, "semantic")
                    cnt += 1
                append_audit(args.audit, {"ts": now_iso(), "kind": "pipeline_semantic",
                                          "seed": seed, "hits": len(res.get("hits") or []),
                                          "estimate": res.get("estimate")})
            ctx["axes"]["semantic"] = {"status": "ok" if cnt else "empty", "count": cnt,
                                       "detail": "BigQuery embedding_v1 近邻，种子 {} 件".format(
                                           len(seeds))}

    # ------------------------------------------------------------ 去重 → 排序 → 截断
    seed_set = set(seeds)
    pool = [c for c in candidates.values() if c["pub_number"] not in seed_set]
    terms = key_terms(all_queries, seed_titles)
    for c in pool:
        c["score"], c["score_parts"] = score_candidate(c, args.cutoff, terms, seed_country)
    pool.sort(key=lambda c: (-c["score"], c["pub_number"]))
    if args.limit > 0 and len(pool) > args.limit:
        # 先给每条轴保留 quota 个名额，再按总分补足：否则低权重的整条轴会被高分轴挤空，
        # 多轴召回就失去了意义（实测 12 条关键词轴候选曾全部被挤出前 30）。
        keep, taken = [], set()
        for axis in AXIS_ORDER:
            n = 0
            for c in pool:
                if axis in c["axes"] and c["pub_number"] not in taken:
                    keep.append(c)
                    taken.add(c["pub_number"])
                    n += 1
                    if n >= max(args.per_axis, 0):
                        break
        for c in pool:
            if len(keep) >= args.limit:
                break
            if c["pub_number"] not in taken:
                keep.append(c)
                taken.add(c["pub_number"])
        ranked = sorted(keep, key=lambda c: (-c["score"], c["pub_number"]))
        ctx["limitations"].append({
            "axis": "ranking",
            "reason": "候选池 {} 条超过 --limit {}，已按轴各留 {} 个名额再按总分补足".format(
                len(pool), args.limit, args.per_axis),
            "remedy": "提高 --limit 可看到完整候选池（candidates.json 里只落截断后的榜）"})
    else:
        ranked = pool
    ctx["candidates"] = ranked

    # ------------------------------------------------------------ 取原文（前 N 件）
    chain = ["google"] + ([] if args.no_relay else ["tavily"]) + ["bigquery"]
    fetched_ok = 0
    for c in ranked[: max(args.fetch_top, 0)]:
        pn = c["pub_number"]
        res = bk.fetch_document(pn, backends=chain, lang=args.lang, timeout=args.timeout,
                                tavily_key=args.tavily_key, allow_relay=not args.no_relay)
        if not res.get("ok"):
            ctx["blocked_seen"] = ctx["blocked_seen"] or bool(res.get("blocked"))
            c["fetch"] = {"ok": False, "reason": res.get("reason"),
                          "attempts": res.get("attempts")}
            ctx["limitations"].append({"axis": "fetch",
                                       "reason": "{} 未取到原文：{}".format(pn, res.get("reason")),
                                       "remedy": res.get("remedy")})
            note("fetch {} failed: {}".format(pn, res.get("reason")))
            continue
        doc = res["doc"]
        doc["url"] = res["url"] or doc.get("url", "")
        doc["retrieved_at"] = now_iso()
        doc["backend"] = res["backend"]
        doc["fetch_attempts"] = res["attempts"]
        doc["sha256"] = sha256_text(gf.canonical_text(doc))
        if args.save_pdf and doc.get("pdf_url"):
            pdf = bk.fetch_binary(doc["pdf_url"], timeout=max(args.timeout, 120))
            doc["pdf_bytes"] = pdf.get("bytes")
            doc["pdf_sha256"] = pdf.get("sha256")
            doc["pdf_retrieved_at"] = now_iso()
            if pdf.get("ok") and docs_dir:
                with open(os.path.join(docs_dir, "{}.pdf".format(pn)), "wb") as fh:
                    fh.write(pdf["data"])
            elif not pdf.get("ok"):
                doc["pdf_error"] = pdf.get("error")
                ctx["limitations"].append({
                    "axis": "pdf", "reason": "{} PDF 未下载成功：{}".format(pn, pdf.get("error")),
                    "remedy": "PDF 直链为 Google 存储；失败不影响已取回的文本证据"})
        c["fetch"] = {"ok": True, "backend": res["backend"],
                      "evidence_level": doc.get("evidence_level"),
                      "relay": doc.get("relay"), "attempts": res["attempts"]}
        c["evidence_level"] = doc.get("evidence_level")
        c["title"] = c.get("title") or doc.get("title") or ""
        c["publication_date"] = c["publication_date"] or doc.get("publication_date") or ""
        if docs_dir:
            write_json(os.path.join(docs_dir, "{}.json".format(pn)), doc)
            with open(os.path.join(docs_dir, "{}.md".format(pn)), "w", encoding="utf-8") as fh:
                fh.write(gf.render_md(doc, doc["url"]))
            if doc.get("relay") and res.get("html"):
                with open(os.path.join(docs_dir, "{}.relay.md".format(pn)), "w",
                          encoding="utf-8") as fh:
                    fh.write(res["html"])
        ctx["fetched"].append(doc)
        if doc.get("evidence_level") == "original-text":
            fetched_ok += 1
        append_audit(args.audit, {"ts": doc["retrieved_at"], "kind": "pipeline_fetch",
                                  "pub_number": pn, "backend": res["backend"],
                                  "evidence_level": doc.get("evidence_level"),
                                  "relay": doc.get("relay"), "sha256": doc["sha256"],
                                  "blocked": False})

    # ------------------------------------------------------------ 引用骨架 + 核验门禁
    if docs_dir and not args.no_citations_draft and ctx["fetched"]:
        cits = []
        for doc in ctx["fetched"]:
            claims = doc.get("claims") or []
            if not claims:
                continue
            cits.append({"pn": doc["pub_number"], "role": "",
                         "quote": claims[0]["text"], "locator": "claims/1", "auto": True,
                         "note": "自动骨架：quote=权利要求1原文，仅用于核验留痕；"
                                 "真正的 X/Y/A 引用片段与角色须人工替换"})
        if cits:
            draft_path = os.path.join(out_dir, "citations.draft.json")
            write_json(draft_path, cits)
            ctx["artifacts"]["citations_draft"] = draft_path
            records = [verify_one(c, docs_dir, 20, args.cutoff, False) for c in cits]
            okn = len([r for r in records if r["status"] == "verified"])
            v = {"checked_at": now_iso(), "docs_dir": docs_dir, "total": len(records),
                 "verified": okn, "failed": len(records) - okn, "all_verified": okn == len(records),
                 "records": records,
                 "policy": "只有 status=verified 的条目才可写入检索报告并作为 X/Y/A 引用"}
            vpath = os.path.join(out_dir, "verify.json")
            write_json(vpath, v)
            ctx["artifacts"]["verify_json"] = vpath
            ctx["verify"] = v
            append_audit(args.audit, {"ts": v["checked_at"], "kind": "pipeline_verify",
                                      "total": v["total"], "verified": v["verified"]})

    # ------------------------------------------------------------ 落盘 + 输出
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        md_path = os.path.join(out_dir, "screening.md")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(render_screening_md(ctx))
        ctx["artifacts"]["screening_md"] = md_path
        write_json(os.path.join(out_dir, "candidates.json"), ranked)
        ctx["artifacts"]["pipeline_json"] = os.path.join(out_dir, "pipeline.json")

    payload = {
        "ok": bool(ranked) and (fetched_ok > 0 or args.fetch_top <= 0),
        "seeds": seeds, "queries": queries, "derived_queries": ctx["derived_queries"],
        "cutoff": args.cutoff, "country": args.country, "axes": ctx["axes"],
        "candidates": ranked,
        "fetched": [{k: d.get(k) for k in
                     ("pub_number", "title", "publication_date", "evidence_level",
                      "claim_count", "description_chars", "backend", "relay", "sha256",
                      "url", "pdf_url")} for d in ctx["fetched"]],
        "counts": {
            "candidates": len(ranked), "candidates_in_pool": len(pool),
            "fetched": len(ctx["fetched"]), "original_text": fetched_ok,
            "by_axis_in_pool": {a: len([c for c in pool if a in c["axes"]]) for a in AXIS_ORDER},
            "by_axis_in_list": {a: len([c for c in ranked if a in c["axes"]]) for a in AXIS_ORDER}},
        "verify": ({k: ctx["verify"].get(k) for k in
                    ("total", "verified", "failed", "all_verified")}
                   if ctx.get("verify") else None),
        "limitations": ctx["limitations"], "artifacts": ctx["artifacts"],
        "retrieved_at": now_iso(),
        "next_step": "人工按 artifacts.docs_dir 里的原文逐特征比对，替换 citations.draft.json 的 "
                     "quote/role，再跑 gp_verify.py；排序分不构成相关性结论",
    }
    if ctx["artifacts"]["pipeline_json"]:
        write_json(ctx["artifacts"]["pipeline_json"], payload)
    append_audit(args.audit, {"ts": payload["retrieved_at"], "kind": "pipeline_summary",
                              "candidates": len(ranked), "original_text": fetched_ok})
    emit("GP_PIPELINE_JSON", payload)

    if not ranked:
        hint("no candidates: see axes[] and limitations[]")
        blocked = ctx.get("blocked_seen") or any(
            v.get("status") in ("blocked", "unavailable") for v in ctx["axes"].values())
        return EXIT_BLOCKED if blocked else EXIT_NO_FULLTEXT
    if fetched_ok == 0 and args.fetch_top > 0:
        hint("candidates found but no original text: see limitations[]")
        return EXIT_BLOCKED if ctx.get("blocked_seen") else EXIT_NO_FULLTEXT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
