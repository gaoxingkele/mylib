#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Google Patents 免费检索（无需 API key）。

**输出约定（与仓库内 cnipa_epub_search.py 一致）**

- **stdout**：**仅一行** ``GP_HITS_JSON:`` + JSON 对象（UTF-8，含中文标题）。
- **stderr**：``GP_NOTE:`` / ``GP_HINT:`` / ``GP_BLOCKED:`` 等诊断行（ASCII 前缀）。

**取数路线**（2026-09-26 实测结论见 references/troubleshooting.md）

===================  ==========================================================
route                说明
===================  ==========================================================
``cdp``              挂到用户已开的 Chrome（``--remote-debugging-port=9222``）。**推荐**：
                     复用真实会话与 Cookie，能过 Google 的自动化拦截。
``headless``         Playwright 自带 chromium 无头。**本机实测会被 503 拦截**，
                     保留为探测手段：被拦时以退出码 3 + ``GP_BLOCKED`` 明确报告，
                     而不是返回「0 条命中」让人误判「没有现有技术」。
``headed``           同上但有头（仍可能被拦；被拦请换 ``cdp``）。
``html``             离线解析已保存的结果页 HTML，不联网（可复算、可回归测试）。
===================  ==========================================================

用法：

  # 1) 推荐：先按 --remote-debugging-port=9222 启动 Chrome，再
  python gp_search.py --query '(CN103399241B OR 变压器故障诊断) AND country=CN' --cdp 9222

  # 2) 无 key 的默认路线（自动优先 cdp，失败降级 headless 并如实报告被拦）
  python gp_search.py --query 'graphene eye mask' --route auto

  # 3) 离线复算：对已保存的结果页 HTML 解析
  python gp_search.py --html tmp/gp/result.html

  # 4) 检索式从文件读（长检索式避免命令行转义问题）
  python gp_search.py --query-file q.txt --cdp 9222 --out hits.json --audit audit.jsonl

退出码：0 成功有命中；3 被 Google 反爬拦截；4 无命中；2 参数/依赖错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gp_common import (  # noqa: E402
    SEL_RESULT_ITEM, append_audit, blocked_payload, emit, ensure_utf8_stdio,
    hint, load_html, looks_blocked, note, now_iso, parse_result_items, search_url,
    write_json,
)

EXIT_OK, EXIT_ARGS, EXIT_BLOCKED, EXIT_EMPTY, EXIT_RUNTIME = 0, 2, 3, 4, 5
DEFAULT_CDP = "http://127.0.0.1:9222"
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def _load_page(page, url: str, wait_ms: int) -> tuple[str, int | None]:
    resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait_ms)
    html = page.content()
    return html, (resp.status if resp else None)


def _candidates(page, rows: int, wait_ms: int) -> str:
    """结果列表是懒渲染的，滚动到底把条目带出来。"""
    for _ in range(max(1, rows // 10)):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(min(1200, wait_ms))
    return page.content()


def run_browser(args) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        note("playwright missing: pip install -r requirements.txt && python -m playwright install chromium")
        return EXIT_ARGS

    url = args.url or search_url(args.query, page=args.page, lang=args.lang)
    cdp = args.cdp
    if cdp and not cdp.startswith("http"):
        cdp = f"http://127.0.0.1:{cdp}"

    with sync_playwright() as pw:
        browser = None
        try:
            if args.route in ("auto", "cdp"):
                try:
                    browser = pw.chromium.connect_over_cdp(cdp or DEFAULT_CDP, timeout=8000)
                    note(f"route=cdp({cdp or DEFAULT_CDP})")
                except Exception as exc:  # noqa: BLE001
                    if args.route == "cdp":
                        note(f"CDP connect failed: {type(exc).__name__}")
                        return EXIT_ARGS
                    note("CDP unavailable: falling back to headless")
            if browser is None:
                headless = args.route != "headed"
                browser = pw.chromium.launch(headless=headless)
                note(f"route={'headless' if headless else 'headed'}")
            ctx = browser.contexts[0] if getattr(browser, "contexts", None) else browser.new_context(
                locale="zh-CN", user_agent=DEFAULT_UA)
            page = ctx.new_page()
            html, status = _load_page(page, url, args.wait)
            if looks_blocked(status, html):
                payload = blocked_payload(args.route, status, url)
                payload["retrieved_at"] = now_iso()
                sys.stderr.write("GP_BLOCKED: google_anti_bot\n")
                emit("GP_HITS_JSON", payload)
                append_audit(args.audit, {"ts": now_iso(), "query": args.query, "url": url,
                                          "route": args.route, "blocked": True, "hits": 0})
                return EXIT_BLOCKED
            html = _candidates(page, args.rows, args.wait)
            page.close()
        finally:
            try:
                if browser and args.route != "cdp":
                    browser.close()
            except Exception:  # noqa: BLE001
                pass

    hits = parse_result_items(html)
    return _finish(args, hits, url, status=None)


def _finish(args, hits: list[dict], url: str, status: int | None) -> int:
    if args.save_html:
        os.makedirs(os.path.dirname(os.path.abspath(args.save_html)), exist_ok=True)
        with open(args.save_html, "w", encoding="utf-8") as fh:
            fh.write(args._last_html or "")
    if args.limit and args.limit > 0:
        hits = hits[: args.limit]
    payload = {
        "ok": bool(hits), "blocked": False, "route": args.route, "url": url,
        "query": args.query, "retrieved_at": now_iso(), "count": len(hits),
        "hits": hits,
        "evidence_level": "snippet-degraded",
        "next_step": "对候选逐件执行 gp_fetch.py 取原文，再跑 gp_verify.py 才可作为对比文件引用",
    }
    if args.out:
        write_json(args.out, payload)
    emit("GP_HITS_JSON", payload)
    append_audit(args.audit, {"ts": payload["retrieved_at"], "query": args.query, "url": url,
                              "route": args.route, "blocked": False, "hits": len(hits)})
    if not hits:
        hint("zero hits: check query syntax (references/query_syntax.md), then widen CPC/assignee axes")
        return EXIT_EMPTY
    return EXIT_OK


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="Google Patents 免费检索（单行 GP_HITS_JSON 输出）")
    # 注意：位置参数不能与 --query 同名（argparse 会共用一个 dest 并互相覆盖）
    ap.add_argument("query_terms", nargs="*", help="检索式（位置参数）")
    ap.add_argument("--query", help="检索式（显式参数）")
    ap.add_argument("--query-file", help="从文件读检索式")
    ap.add_argument("--route", choices=["auto", "cdp", "headless", "headed", "html"], default="auto")
    ap.add_argument("--cdp", default=None, help="Chrome 调试端口或 URL（默认 http://127.0.0.1:9222）")
    ap.add_argument("--html", help="离线解析已保存的结果页 HTML")
    ap.add_argument("--url", help="直接给完整检索 URL（覆盖 --query 组装）")
    ap.add_argument("--page", type=int, default=1, help="结果页码（Google 每页 10 条）")
    ap.add_argument("--rows", type=int, default=10, help="期望条数（用于滚动加载，默认 10）")
    ap.add_argument("--limit", type=int, default=0, help="截断命中数（0=不截断）")
    ap.add_argument("--lang", help="界面语言 hl=zh-CN/en 等")
    ap.add_argument("--wait", type=int, default=3500, help="页面加载后等待毫秒数")
    ap.add_argument("--out", help="把完整 JSON 落盘")
    ap.add_argument("--save-html", help="把结果页 HTML 落盘（供 --html 复算）")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    ap.add_argument("--print-url", action="store_true",
                    help="只打印检索 URL（供 MCP 浏览器路线先 browser_navigate）")
    args = ap.parse_args(argv)

    args.query = args.query or " ".join(args.query_terms) or ""
    if args.query_file:
        with open(args.query_file, encoding="utf-8") as fh:
            args.query = fh.read().strip()
    if args.print_url:
        print(args.url or search_url(args.query, page=args.page, lang=args.lang))
        return EXIT_OK
    if args.html:
        args.route = "html"
        html = load_html(args.html)   # 兼容 MCP browser_evaluate 落盘的 JSON 转义形态
        args._last_html = html
        if looks_blocked(200, html):
            payload = blocked_payload("html", 200, args.html)
            emit("GP_HITS_JSON", payload)
            return EXIT_BLOCKED
        return _finish(args, parse_result_items(html), args.html, status=None)
    if not args.query and not args.url:
        ap.error("需要 query / --query / --query-file / --url / --html 之一")
    try:
        return run_browser(args)
    except Exception as exc:  # noqa: BLE001
        note(f"runtime error {type(exc).__name__}")
        emit("GP_HITS_JSON", {"ok": False, "blocked": False, "route": args.route,
                              "error": f"{type(exc).__name__}: {exc}", "query": args.query})
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
