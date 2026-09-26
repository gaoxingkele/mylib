#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""按公开号取原文（核验腿：把命中项升级为可引用的原始文本）。**不使用浏览器自动化。**

**为什么必须有这一步**：检索结果只给标题/申请人/日期/摘要片段（``snippet-degraded``）。
本仓规则是"不得用检索片段当已核验的专利原文"，因此要写进检索报告的对比文件，
必须先经本脚本取到权利要求或说明书原文，并留下 URL、取回时间与 sha256。

**后端**

| backend | 输入 | 得到 | 证据级别 |
| --- | --- | --- | --- |
| ``google`` | 公开号 | 权利要求逐项 + 说明书 + 摘要 | ``original-text`` |
| ``patentscope`` | 内部 docId（见 gp_search 输出） | 著录项为主 | ``metadata-only`` |
| ``bigquery`` | 公开号 | 官方数据集的著录项/摘要/可得权利要求 | 视返回而定 |

**输出**：stdout 单行 ``GP_DOC_JSON:``；stderr 只写 ASCII 诊断；
``--out DIR`` 时落 ``<PN>.json``、``<PN>.md``、``manifest.json``。

用法：

  python gp_fetch.py CN210644322U --backend google --out evidence/gp --audit audit.jsonl
  python gp_fetch.py CN210644322U --from-hits hits.json --out evidence/gp   # 自动回填公开日
  python gp_fetch.py --doc-id CN241725947 --backend patentscope --out evidence/ps
  python gp_fetch.py CN210644322U --html saved_patent_page.html --out tmp/gp   # 离线复算

退出码：0 取到原文；3 被拦；4 只取到元数据；2 参数错误；5 运行时错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_backends as bk  # noqa: E402
from gp_common import (  # noqa: E402
    append_audit, blocked_payload, emit, ensure_utf8_stdio, hint, load_html,
    looks_blocked, normalize_pub, note, now_iso, parse_patent_doc, patent_url,
    sha256_text, write_json,
)

EXIT_OK, EXIT_ARGS, EXIT_BLOCKED, EXIT_METADATA_ONLY, EXIT_RUNTIME = 0, 2, 3, 4, 5
EXIT_EMPTY = 4          # 与 EXIT_METADATA_ONLY 同码：都是"没拿到可引用的原文"


def canonical_text(doc: dict) -> str:
    parts = [doc.get("title", ""), doc.get("abstract", "")]
    for c in doc.get("claims") or []:
        parts.append(f"{c.get('claim_no', '')}. {c.get('text', '')}")
    parts.append(doc.get("description", ""))
    return "\n".join(p for p in parts if p)


def render_md(doc: dict, url: str) -> str:
    lines = [f"# {doc.get('pub_number') or 'UNKNOWN'} — {doc.get('title') or ''}", "",
             f"- 后端：{doc.get('backend')}（{doc.get('source')}）",
             f"- URL：{url}",
             f"- 公开日：{doc.get('publication_date') or '未取到'}"
             f"（来源：{doc.get('publication_date_source') or 'n/a'}）",
             f"- 页面 DC.date：{doc.get('dc_date') or 'n/a'}"
             f"（Google 单件页实测为申请日，非公开日）",
             f"- 取回时间：{doc.get('retrieved_at')}",
             f"- 证据级别：{doc.get('evidence_level')}",
             f"- 规范文本 sha256：{doc.get('sha256')}",
             f"- 权利要求数：{doc.get('claim_count')}；说明书字符数：{doc.get('description_chars')}",
             "", "## 摘要", "", doc.get("abstract") or "（未取到）", "", "## 权利要求", ""]
    if doc.get("claims"):
        for c in doc["claims"]:
            lines += [f"**{c.get('claim_no')}. ** {c.get('text')}", ""]
    else:
        lines += [f"（未取到权利要求原文——不可作为对比文件引用）"
                  f"{doc.get('note') or ''}", ""]
    lines += ["## 说明书", "", doc.get("description") or "（未取到）", ""]
    return "\n".join(lines)


def save_doc(args, doc: dict, html: str, url: str) -> None:
    if not args.out:
        return
    os.makedirs(args.out, exist_ok=True)
    pn = doc.get("pub_number") or args.doc_id or "UNKNOWN"
    write_json(os.path.join(args.out, f"{pn}.json"), doc)
    with open(os.path.join(args.out, f"{pn}.md"), "w", encoding="utf-8") as fh:
        fh.write(render_md(doc, url))
    if args.save_html and html:
        with open(os.path.join(args.out, f"{pn}.html"), "w", encoding="utf-8") as fh:
            fh.write(html)
    man_path = os.path.join(args.out, "manifest.json")
    man = []
    if os.path.exists(man_path):
        try:
            man = json.load(open(man_path, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            man = []
    man.append({"pub_number": pn, "title": doc.get("title"), "url": url,
                "backend": doc.get("backend"), "retrieved_at": doc.get("retrieved_at"),
                "sha256": doc.get("sha256"), "evidence_level": doc.get("evidence_level"),
                "claim_count": doc.get("claim_count")})
    write_json(man_path, man)


def finish(args, doc: dict, html: str, url: str, backend: str) -> int:
    doc["url"] = url
    doc["retrieved_at"] = now_iso()
    doc["backend"] = doc.get("backend") or backend
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
                    doc["assignee"] = h.get("assignee") or doc.get("assignee", "")
                    break
        except Exception as exc:  # noqa: BLE001
            note(f"--from-hits read failed: {type(exc).__name__}")
    doc["sha256"] = sha256_text(canonical_text(doc))
    save_doc(args, doc, html, url)
    emit("GP_DOC_JSON", doc)
    append_audit(args.audit, {"ts": doc["retrieved_at"], "pub_number": doc.get("pub_number"),
                              "backend": doc.get("backend"), "url": url,
                              "claim_count": doc.get("claim_count"), "sha256": doc["sha256"],
                              "blocked": False})
    if doc.get("evidence_level") != "original-text":
        hint("not original-text: cannot be quoted as prior art; try backend=google or a full-text source")
        return EXIT_METADATA_ONLY
    return EXIT_OK


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="按公开号取专利原文（GP_DOC_JSON 单行输出，无浏览器）")
    ap.add_argument("pub_numbers", nargs="*", help="公开号（google/bigquery 后端）")
    ap.add_argument("--backend", choices=["auto", "google", "patentscope", "bigquery"], default="auto")
    ap.add_argument("--doc-id", help="patentscope 内部 docId（来自 gp_search 输出的 doc_id）")
    ap.add_argument("--html", help="离线解析已保存的单件页 HTML")
    ap.add_argument("--lang", help="google 语言路径 zh/en（默认按国家码推断）")
    ap.add_argument("--from-hits", help="从 gp_search 的 --out 文件回填公开日/申请人（含 doc_id 时也可解析 patentscope）")
    ap.add_argument("--pub-date", help="显式指定公开日 YYYY-MM-DD")
    ap.add_argument("--timeout", type=int, default=40, help="单次请求超时秒数")
    ap.add_argument("--out", help="落盘目录")
    ap.add_argument("--save-html", action="store_true", help="同时保存原始 HTML")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    args = ap.parse_args(argv)

    if args.html:
        html = load_html(args.html)
        if looks_blocked(200, html):
            emit("GP_DOC_JSON", blocked_payload("html", 200, args.html))
            return EXIT_BLOCKED
        doc = parse_patent_doc(html, args.pub_numbers[0] if args.pub_numbers else "")
        return finish(args, doc, html, args.html, "offline")

    # patentscope 分支：需要内部 docId
    doc_id = args.doc_id
    pn = normalize_pub(args.pub_numbers[0]) if args.pub_numbers else ""
    if not doc_id and args.from_hits:
        try:
            hits = json.load(open(args.from_hits, encoding="utf-8"))
            for h in hits.get("hits", []):
                if pn and normalize_pub(h.get("pub_number", "")) == pn and h.get("doc_id"):
                    doc_id = h["doc_id"]
                    break
        except Exception:  # noqa: BLE001
            pass

    backend = args.backend
    if backend == "auto":
        backend = "patentscope" if (doc_id and not pn) else "google"

    try:
        if backend == "patentscope":
            if not doc_id:
                ap.error("patentscope 后端需要 --doc-id（或 --from-hits 中带 doc_id 的条目）")
            res = bk.patentscope_fetch(doc_id, timeout=args.timeout)
            if res.get("error"):
                note(f"patentscope error={res['error']}")
                emit("GP_DOC_JSON", {"ok": False, "error": res["error"]})
                return EXIT_RUNTIME
            url = res["doc"].get("url", "")
            return finish(args, res["doc"], res.get("html", ""), url, "patentscope")

        if backend == "bigquery":
            if not pn:
                ap.error("bigquery 后端需要公开号")
            res = bk.bigquery_lookup(pn, timeout=max(args.timeout, 120))
            if res.get("error"):
                note(f"bigquery error={res['error']}")
                emit("GP_DOC_JSON", {"ok": False, "backend": "bigquery", "pub_number": pn,
                                     **res})
                return EXIT_RUNTIME
            rows = res.get("rows") or []
            if not rows:
                emit("GP_DOC_JSON", {"ok": False, "backend": "bigquery", "pub_number": pn,
                                     "error": "not_found"})
                return EXIT_EMPTY
            doc = bk.bigquery_normalize_row(rows[0], lang=args.lang)
            doc["estimate"] = res.get("estimate")
            return finish(args, doc, "", f"bigquery://patents-public-data/{pn}", "bigquery")

        if not pn:
            ap.error("需要至少一个公开号（或 --doc-id / --html）")
        rc = EXIT_OK
        for raw in args.pub_numbers:
            p = normalize_pub(raw)
            note(f"fetch {p}")
            res = bk.google_fetch(p, lang=args.lang, timeout=args.timeout)
            if res.get("blocked"):
                sys.stderr.write("GP_BLOCKED: google_anti_bot\n")
                emit("GP_DOC_JSON", blocked_payload("google", res.get("status"), res.get("url", "")))
                return EXIT_BLOCKED
            if res.get("error"):
                note(f"google error={res['error']}")
                emit("GP_DOC_JSON", {"ok": False, "pub_number": p, "error": res["error"]})
                return EXIT_RUNTIME
            code = finish(args, res["doc"], res.get("html", ""), res["doc"]["url"], "google")
            rc = code if code != EXIT_OK else rc
        return rc
    except Exception as exc:  # noqa: BLE001
        note(f"runtime error {type(exc).__name__}")
        emit("GP_DOC_JSON", {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return EXIT_RUNTIME
if __name__ == "__main__":
    raise SystemExit(main())
