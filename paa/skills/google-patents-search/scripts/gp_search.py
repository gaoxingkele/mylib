#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""专利检索（免费、**不使用浏览器自动化**）。

**输出约定**（沿用仓内 cnipa_epub_search.py 的做法）

- **stdout 仅一行**：``GP_HITS_JSON:`` + JSON（UTF-8，含中文标题）。
- **stderr 只写 ASCII 诊断**：``GP_NOTE:`` / ``GP_HINT:`` / ``GP_BLOCKED:``。

**后端**（见 gp_backends.py）

| backend | 说明 | 是否需要 key |
| --- | --- | --- |
| ``google`` | Google Patents 站点内部 JSON 接口（最接近 Google Patents API） | 否 |
| ``patentscope`` | WIPO PATENTSCOPE 官方库（覆盖 CN，实测本机可用） | 否 |

``--backend auto``（默认）先试 google；若被 Google 反爬拦下，自动改走 patentscope，
并在输出的 ``attempts`` 里如实记录两次尝试，绝不把"被拦"写成"0 命中"。

用法：

  python gp_search.py --query 'graphene eye mask country=CN' --out hits.json --audit audit.jsonl
  python gp_search.py --query 'EN_ALLTXT:(石墨烯 眼罩) AND CTR:(CN)' --backend patentscope
  python gp_search.py --html saved_result.html      # 离线复算（可回归测试）

退出码：0 有命中；3 后端被拦；4 无命中；2 参数/依赖错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_backends as bk  # noqa: E402
from gp_common import (  # noqa: E402
    append_audit, emit, ensure_utf8_stdio, hint, load_html, looks_blocked, note,
    now_iso, parse_result_items, search_url, write_json,
)

EXIT_OK, EXIT_ARGS, EXIT_BLOCKED, EXIT_EMPTY, EXIT_RUNTIME = 0, 2, 3, 4, 5


def _finish(args, hits, backend, attempts, url) -> int:
    if args.limit and args.limit > 0:
        hits = hits[: args.limit]
    blocked = bool(attempts) and all(a.get("blocked") for a in attempts)
    payload = {
        "ok": bool(hits), "blocked": blocked, "backend": backend,
        "attempts": attempts, "url": url, "query": args.query,
        "retrieved_at": now_iso(), "count": len(hits), "hits": hits,
        "evidence_level": "snippet-degraded",
        "next_step": "对候选逐件 gp_fetch.py 取原文，再 gp_verify.py 核验后才可引用",
    }
    if args.out:
        write_json(args.out, payload)
    emit("GP_HITS_JSON", payload)
    append_audit(args.audit, {"ts": payload["retrieved_at"], "query": args.query,
                              "backend": backend, "blocked": blocked,
                              "hits": len(hits), "url": url})
    if hits:
        return EXIT_OK
    if blocked:
        return EXIT_BLOCKED
    hint("zero hits: check query syntax (references/query_syntax.md), then widen axes")
    return EXIT_EMPTY


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="免费专利检索（GP_HITS_JSON 单行输出，无浏览器）")
    ap.add_argument("query_terms", nargs="*", help="检索式（位置参数）")
    ap.add_argument("--query", help="检索式（显式参数）")
    ap.add_argument("--query-file", help="从文件读检索式")
    ap.add_argument("--backend", choices=["auto", "google", "patentscope"], default="auto")
    ap.add_argument("--html", help="离线解析已保存的结果页 HTML")
    ap.add_argument("--page", type=int, default=1, help="页码（google 每页 10 条）")
    ap.add_argument("--limit", type=int, default=0, help="截断命中数（0=不截断）")
    ap.add_argument("--lang", help="google 界面语言 hl=zh-CN/en")
    ap.add_argument("--timeout", type=int, default=40, help="单次请求超时秒数")
    ap.add_argument("--out", help="完整 JSON 落盘")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    ap.add_argument("--print-url", action="store_true", help="只打印 google 检索 URL")
    args = ap.parse_args(argv)

    args.query = args.query or " ".join(args.query_terms) or ""
    if args.query_file:
        with open(args.query_file, encoding="utf-8") as fh:
            args.query = fh.read().strip()
    if args.print_url:
        print(search_url(args.query, page=args.page, lang=args.lang))
        return EXIT_OK

    if args.html:
        html = load_html(args.html)
        if looks_blocked(200, html):
            emit("GP_HITS_JSON", {"ok": False, "blocked": True, "backend": "offline",
                                  "url": args.html, "reason": "google_anti_bot", "hits": []})
            return EXIT_BLOCKED
        hits = parse_result_items(html)
        backend = "offline-google"
        if not hits:
            hits = bk.parse_patentscope_results(html)
            backend = "offline-patentscope"
        return _finish(args, hits, backend, [{"backend": backend, "blocked": False}], args.html)

    if not args.query:
        ap.error("需要 query / --query / --query-file / --html 之一")

    attempts = []
    order = ["google", "patentscope"] if args.backend == "auto" else [args.backend]
    try:
        for backend in order:
            note(f"backend={backend}")
            if backend == "google":
                res = bk.google_search(args.query, page=args.page, lang=args.lang,
                                       timeout=args.timeout)
            else:
                res = bk.patentscope_search(args.query, timeout=args.timeout)
            attempts.append({"backend": backend, "blocked": bool(res.get("blocked")),
                             "error": res.get("error"), "status": res.get("status"),
                             "hits": len(res.get("hits") or []), "url": res.get("url")})
            if res.get("blocked"):
                sys.stderr.write(f"GP_BLOCKED: {backend}_anti_bot\n")
                continue
            if res.get("error"):
                note(f"{backend} error={res['error']}")
                continue
            hits = res.get("hits") or []
            if hits:
                return _finish(args, hits, backend, attempts, res.get("url", ""))
        return _finish(args, [], order[-1], attempts, "")
    except Exception as exc:  # noqa: BLE001
        note(f"runtime error {type(exc).__name__}")
        emit("GP_HITS_JSON", {"ok": False, "blocked": False, "backend": args.backend,
                              "error": f"{type(exc).__name__}: {exc}", "query": args.query})
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
