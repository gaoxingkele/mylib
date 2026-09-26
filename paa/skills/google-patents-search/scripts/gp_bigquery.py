#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google 官方专利数据集（BigQuery）深度用法 CLI。**不使用浏览器。**

这是"更深入使用 Google Patents"的正路：Google 把整套专利数据放在 BigQuery 公共数据集里，
可以用 SQL 直接查——包括权利要求全文、CPC 分类、申请/公开日期，以及**向量嵌入**
（`google_patents_research.publications.embedding_v1`）做语义近邻检索。

**成本**：BigQuery 每月前 1 TiB 扫描量免费；未开账单也能用 **BigQuery 沙盒**
（免信用卡、1 TiB/月、不支持 DML/流式写入）。本 CLI 对每条查询**先干跑估算**，
超过 `--max-gb` 直接拒绝执行，避免误烧额度。

子命令：

  probe                     检查 SDK 与凭据前置条件
  lookup   <公开号>          取著录项 + 权利要求全文（扫描量极小）
  search   --keyword 石墨烯 --country CN --cpc A61F --after 2015-01-01
                            关键词/CPC/国别/日期条件检索
  similar  <种子公开号>       以该件向量做**语义近邻**检索（incoPat 语义检索的免费等价物）

**输出**：stdout 单行 ``GP_BIGQUERY_JSON:`` + JSON；stderr 只写 ASCII 诊断。
退出码：0 成功；3 被预算守卫拒绝；2 参数/前置条件错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_backends as bk  # noqa: E402
from gp_common import emit, ensure_utf8_stdio, note, now_iso, write_json  # noqa: E402

EXIT_OK, EXIT_ARGS, EXIT_BUDGET, EXIT_RUNTIME = 0, 2, 3, 5


def _out(args, payload: dict) -> int:
    payload.setdefault("checked_at", now_iso())
    if args.out:
        write_json(args.out, payload)
    emit("GP_BIGQUERY_JSON", payload)
    if payload.get("error") == "estimate_over_budget":
        note("rejected by budget guard (see estimate)")
        return EXIT_BUDGET
    if payload.get("error"):
        note(f"error={payload['error']}")
        return EXIT_ARGS if payload["error"].endswith(("missing", "sdk_missing")) else EXIT_RUNTIME
    return EXIT_OK


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="Google Patents 官方 BigQuery 数据集（GP_BIGQUERY_JSON 单行输出）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("probe", help="检查前置条件")
    p1.add_argument("--out")

    p2 = sub.add_parser("lookup", help="按公开号取著录项+权利要求")
    p2.add_argument("pn")
    p2.add_argument("--lang", help="权利要求语言 zh/en（默认按国家码推断）")
    p2.add_argument("--out")

    p3 = sub.add_parser("search", help="关键词/CPC/国别/日期检索")
    p3.add_argument("--keyword", action="append", default=[], help="可重复；命中标题或摘要即可")
    p3.add_argument("--country", help="如 CN / US")
    p3.add_argument("--cpc", help="CPC 前缀，如 A61F")
    p3.add_argument("--after", help="优先权日下限 YYYY-MM-DD")
    p3.add_argument("--before", help="优先权日上限 YYYY-MM-DD")
    p3.add_argument("--limit", type=int, default=20)
    p3.add_argument("--max-gb", type=float, default=50.0, help="预计扫描量上限（GB），超过即拒绝")
    p3.add_argument("--out")

    p4 = sub.add_parser("similar", help="语义近邻检索（需 research 子集）")
    p4.add_argument("pn", help="种子公开号")
    p4.add_argument("--country", help="限定 country 字段，如 China / United States")
    p4.add_argument("--limit", type=int, default=20)
    p4.add_argument("--max-gb", type=float, default=20.0)
    p4.add_argument("--out")

    args = ap.parse_args(argv)

    if args.cmd == "probe":
        return _out(args, bk.bigquery_probe())
    if args.cmd == "lookup":
        res = bk.bigquery_lookup(args.pn, lang=args.lang)
        if res.get("error"):
            return _out(args, res)
        rows = res.get("rows") or []
        if not rows:
            return _out(args, {"error": "not_found", "pub_number": args.pn})
        doc = bk.bigquery_normalize_row(rows[0], lang=args.lang)
        doc["estimate"] = res.get("estimate")
        return _out(args, doc)
    if args.cmd == "search":
        if not args.keyword and not args.cpc:
            ap.error("search 至少要给 --keyword 或 --cpc")
        res = bk.bigquery_search(args.keyword, country=args.country, cpc_prefix=args.cpc,
                                 after_priority=args.after, before_priority=args.before,
                                 limit=args.limit)
        if res.get("error"):
            return _out(args, res)
        est_gb = (res.get("estimate") or {}).get("estimate_gb", 0)
        if est_gb > args.max_gb:
            return _out(args, {"error": "estimate_over_budget", "estimate": res.get("estimate"),
                               "remedy": f"预计 {est_gb} GB > --max-gb {args.max_gb}；"
                                         "请加 --country/--cpc/--after 收窄"})
        return _out(args, {"hits": res["hits"], "count": res["count"],
                           "estimate": res.get("estimate")})
    res = bk.bigquery_similar(args.pn, country=args.country, limit=args.limit,
                              max_gb=args.max_gb)
    return _out(args, res)


if __name__ == "__main__":
    raise SystemExit(main())
