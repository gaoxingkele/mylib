#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按公开号取 Google Patents 单件原文（核验腿：把命中项升级为可引用的原始文本）。

**为什么必须有这一步**：检索结果页只给标题/申请人/日期/摘要片段，属于降级证据。
本仓既有规则是「不得用检索片段当已核验专利原文」，因此任何要写进
``01_现有技术检索报告.md`` 的对比文件，都必须先经本脚本取到权利要求或说明书原文，
并留下 sha256、URL、取回时间，才能进入 gp_verify.py 的核验门禁。

**输出约定**

- **stdout**：**仅一行** ``GP_DOC_JSON:`` + JSON（含元数据、权利要求、说明书、sha256）。
- **stderr**：``GP_NOTE:`` / ``GP_BLOCKED:`` 等 ASCII 前缀诊断行。
- **落盘**（``--out DIR`` 时）：``<DIR>/<PN>.json``、``<DIR>/<PN>.md``、
  ``<DIR>/<PN>.html``（``--save-html`` 时），以及 ``<DIR>/manifest.json`` 追加索引。

用法：

  python gp_fetch.py CN103399241B --cdp 9222 --out evidence/gp
  python gp_fetch.py US20230013787A1 --html tmp/gp/US20230013787A1.html --out tmp/gp
  python gp_fetch.py CN103399241B CN101234567A --cdp 9222 --out evidence/gp   # 批量

退出码：0 取到原文；3 被反爬拦截；4 只取到元数据（无权利要求/说明书）；2 参数错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gp_common import (  # noqa: E402
    append_audit, blocked_payload, emit, ensure_utf8_stdio, hint, looks_blocked,
    load_html, normalize_pub, note, now_iso, parse_patent_doc, patent_url, sha256_text,
    write_json,
)

EXIT_OK, EXIT_ARGS, EXIT_BLOCKED, EXIT_METADATA_ONLY, EXIT_RUNTIME = 0, 2, 3, 4, 5


def canonical_text(doc: dict) -> str:
    """用于 sha256 的规范文本：标题 + 摘要 + 权利要求 + 说明书。"""
    parts = [doc.get("title", ""), doc.get("abstract", "")]
    for c in doc.get("claims") or []:
        parts.append(f"{c.get('claim_no', '')}. {c.get('text', '')}")
    parts.append(doc.get("description", ""))
    return "\n".join(p for p in parts if p)


def render_md(doc: dict, url: str) -> str:
    lines = [f"# {doc.get('pub_number') or 'UNKNOWN'} — {doc.get('title') or ''}", ""]
    lines += [f"- 来源：Google Patents（免费检索，非 API 授权数据源）",
              f"- URL：{url}",
              f"- 公开日（DC.date）：{doc.get('publication_date') or '未取到'}",
              f"- 取回时间：{doc.get('retrieved_at')}",
              f"- 证据级别：{doc.get('evidence_level')}",
              f"- 规范文本 sha256：{doc.get('sha256')}",
              f"- 权利要求数：{doc.get('claim_count')}；说明书字符数：{doc.get('description_chars')}",
              "", "## 摘要", "", doc.get("abstract") or "（未取到）", "", "## 权利要求", ""]
    if doc.get("claims"):
        for c in doc["claims"]:
            lines += [f"**{c.get('claim_no')}. ** {c.get('text')}", ""]
    else:
        lines += ["（未取到权利要求原文——不可作为对比文件引用）", ""]
    lines += ["## 说明书", "", doc.get("description") or "（未取到）", ""]
    return "\n".join(lines)


def save_doc(args, doc: dict, html: str, url: str) -> None:
    if not args.out:
        return
    os.makedirs(args.out, exist_ok=True)
    pn = doc.get("pub_number") or "UNKNOWN"
    write_json(os.path.join(args.out, f"{pn}.json"), doc)
    with open(os.path.join(args.out, f"{pn}.md"), "w", encoding="utf-8") as fh:
        fh.write(render_md(doc, url))
    if args.save_html:
        with open(os.path.join(args.out, f"{pn}.html"), "w", encoding="utf-8") as fh:
            fh.write(html)
    man_path = os.path.join(args.out, "manifest.json")
    man = []
    if os.path.exists(man_path):
        import json
        try:
            man = json.load(open(man_path, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            man = []
    man.append({"pub_number": pn, "title": doc.get("title"), "url": url,
                "retrieved_at": doc.get("retrieved_at"), "sha256": doc.get("sha256"),
                "evidence_level": doc.get("evidence_level"),
                "claim_count": doc.get("claim_count")})
    write_json(man_path, man)


def finish(args, doc: dict, html: str, url: str, route: str) -> int:
    doc["url"] = url
    doc["retrieved_at"] = now_iso()
    doc["route"] = route
    # 公开日回填：优先 --pub-date，其次 --from-hits（gp_search.py 的输出），
    # 最后才是单件页静态 HTML 里能解析到的 Published 行。取不到就留空，
    # 由 gp_verify.py 报 publication_date_unknown，绝不用申请日冒充公开日。
    if args.pub_date:
        doc["publication_date"] = args.pub_date
        doc["publication_date_source"] = "cli"
    elif args.from_hits:
        try:
            with open(args.from_hits, encoding="utf-8") as fh:
                hits = json.load(fh)
            for h in hits.get("hits", []):
                if normalize_pub(h.get("pub_number", "")) == normalize_pub(doc.get("pub_number", "")):
                    doc["publication_date"] = h.get("publication_date") or doc.get("publication_date", "")
                    doc["publication_date_source"] = "search_hits"
                    doc.setdefault("assignee", h.get("assignee") or "")
                    break
        except Exception as exc:  # noqa: BLE001
            note(f"--from-hits read failed: {type(exc).__name__}")
    elif doc.get("publication_date"):
        doc["publication_date_source"] = "page"
    doc["sha256"] = sha256_text(canonical_text(doc))
    save_doc(args, doc, html, url)
    emit("GP_DOC_JSON", doc)
    append_audit(args.audit, {"ts": doc["retrieved_at"], "pub_number": doc.get("pub_number"),
                              "url": url, "route": route, "claim_count": doc.get("claim_count"),
                              "description_chars": doc.get("description_chars"),
                              "sha256": doc["sha256"], "blocked": False})
    if doc.get("evidence_level") == "metadata-only":
        hint("metadata only: no electronic full text; try family members or another source")
        return EXIT_METADATA_ONLY
    return EXIT_OK


def run_live(args, pn: str) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        note("playwright missing: pip install -r requirements.txt && python -m playwright install chromium")
        return EXIT_ARGS
    url = args.url or patent_url(pn, args.lang)
    cdp = args.cdp
    if cdp and not cdp.startswith("http"):
        cdp = f"http://127.0.0.1:{cdp}"
    with sync_playwright() as pw:
        browser = None
        try:
            if args.route in ("auto", "cdp"):
                try:
                    browser = pw.chromium.connect_over_cdp(cdp or "http://127.0.0.1:9222", timeout=8000)
                    note(f"route=cdp({cdp or 'http://127.0.0.1:9222'})")
                    route = "cdp"
                except Exception as exc:  # noqa: BLE001
                    if args.route == "cdp":
                        note(f"CDP connect failed: {type(exc).__name__}")
                        return EXIT_ARGS
                    note("CDP unavailable: falling back to headless")
            if browser is None:
                headless = args.route != "headed"
                browser = pw.chromium.launch(headless=headless)
                route = "headless" if headless else "headed"
            ctx = browser.contexts[0] if getattr(browser, "contexts", None) else browser.new_context(locale="zh-CN")
            page = ctx.new_page()
            resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(args.wait)
            html = page.content()
            status = resp.status if resp else None
            page.close()
        finally:
            try:
                if browser and args.route != "cdp":
                    browser.close()
            except Exception:  # noqa: BLE001
                pass
    if looks_blocked(status, html):
        payload = blocked_payload(route, status, url)
        sys.stderr.write("GP_BLOCKED: google_anti_bot\n")
        emit("GP_DOC_JSON", payload)
        append_audit(args.audit, {"ts": now_iso(), "pub_number": pn, "url": url,
                                  "route": route, "blocked": True})
        return EXIT_BLOCKED
    doc = parse_patent_doc(html, pn)
    return finish(args, doc, html, url, route)


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="按公开号取 Google Patents 原文（GP_DOC_JSON 单行输出）")
    ap.add_argument("pub_numbers", nargs="*", help="公开号，可多个")
    ap.add_argument("--route", choices=["auto", "cdp", "headless", "headed", "html"], default="auto")
    ap.add_argument("--cdp", default=None, help="Chrome 调试端口或 URL")
    ap.add_argument("--html", help="离线解析已保存的单件说明书页 HTML")
    ap.add_argument("--url", help="直接给完整说明书页 URL")
    ap.add_argument("--lang", help="语言路径 zh/en/ja…（默认按国家码推断）")
    ap.add_argument("--wait", type=int, default=3500, help="加载后等待毫秒数")
    ap.add_argument("--out", help="落盘目录（PN.json / PN.md / manifest.json）")
    ap.add_argument("--save-html", action="store_true", help="同时保存原始 HTML")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    ap.add_argument("--pub-date", help="显式指定公开日 YYYY-MM-DD（覆盖页面解析结果）")
    ap.add_argument("--from-hits", help="从 gp_search.py 的 --out 文件回填公开日/申请人")
    args = ap.parse_args(argv)

    if args.html:
        html = load_html(args.html)   # 兼容 MCP browser_evaluate 落盘的 JSON 转义形态
        if looks_blocked(200, html):
            emit("GP_DOC_JSON", blocked_payload("html", 200, args.html))
            return EXIT_BLOCKED
        doc = parse_patent_doc(html, args.pub_numbers[0] if args.pub_numbers else "")
        return finish(args, doc, html, args.html, "html")

    if not args.pub_numbers:
        ap.error("需要至少一个公开号（或 --html）")
    rc = EXIT_OK
    for raw in args.pub_numbers:
        pn = normalize_pub(raw)
        note(f"fetch {pn}")
        try:
            code = run_live(args, pn)
        except Exception as exc:  # noqa: BLE001
            note(f"runtime error {type(exc).__name__}")
            emit("GP_DOC_JSON", {"ok": False, "pub_number": pn,
                                 "error": f"{type(exc).__name__}: {exc}"})
            code = EXIT_RUNTIME
        rc = code if code not in (EXIT_OK,) else rc
        if code == EXIT_BLOCKED:
            break
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
