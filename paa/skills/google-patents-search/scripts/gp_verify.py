#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比文件核验门禁：把「检索到的东西」变成「可引用的证据」，或明确判为不可用。

本仓既有红线：**不得用检索片段当已核验的专利原文，不得编造公开号**。
本脚本是该红线的执行器——对每条拟引用的对比文件，逐项检查：

1. 该公开号是否已由 ``gp_fetch.py`` 取到原文（``<docs>/<PN>.json``）；
2. 证据级别是否为 ``original-text``（``snippet-degraded`` / ``metadata-only`` 一律拒绝）；
3. 引用片段是否**逐字**出现在该件的权利要求或说明书中（空白归一化后比对）；
4. 若给了定位符（``claims/1``、``description``），片段是否真的落在该定位处；
5. 可选：公开日是否早于给定截止日（``--cutoff``，用于「申请日前公开」的资格判断）。

**输出约定**：stdout 单行 ``GP_VERIFY_JSON:`` + JSON；stderr 为 ASCII 诊断。

**退出码**：0 全部通过；1 存在未通过项（供流水线阻断）；2 参数/输入错误。

输入文件（``--citations``）格式：

```json
[
  {"pn": "CN103399241B", "role": "X", "quote": "……权利要求1原文片段……", "locator": "claims/1"},
  {"pn": "US20230013787A1", "role": "A", "quote": "……说明书片段……", "locator": "description"}
]
```

用法：

  python gp_verify.py --citations citations.json --docs evidence/gp --audit evidence/gp/audit.jsonl
  python gp_verify.py --citations citations.json --docs evidence/gp --cutoff 2026-09-26 --out verify.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gp_common import append_audit, emit, ensure_utf8_stdio, note, normalize_pub, now_iso, write_json  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_ARGS = 0, 1, 2


def norm_ws(s: str) -> str:
    """空白归一化：换行/多空格/全角空格都压成单空格，便于逐字比对。"""
    return re.sub(r"[\s\u3000]+", " ", (s or "")).strip()


def load_doc(docs_dir: str, pn: str) -> dict | None:
    path = os.path.join(docs_dir, f"{pn}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        note(f"doc parse failed {pn}: {type(exc).__name__}")
        return None


def locator_text(doc: dict, locator: str) -> str | None:
    """解析定位符：claims/N、claims、description、abstract。"""
    if not locator:
        return None
    loc = locator.strip().lower()
    if loc.startswith("claims/"):
        try:
            n = int(re.sub(r"[^0-9]", "", loc.split("/", 1)[1]) or 0)
        except ValueError:
            return None
        for c in doc.get("claims") or []:
            if c.get("claim_no") == n:
                return c.get("text") or ""
        return None
    if loc.startswith("claim"):
        return "\n".join((c.get("text") or "") for c in doc.get("claims") or []) or None
    if loc.startswith("description"):
        return doc.get("description") or None
    if loc.startswith("abstract"):
        return doc.get("abstract") or None
    return None


def verify_one(cit: dict, docs_dir: str, min_quote: int, cutoff: str | None,
               strict_locator: bool) -> dict:
    pn = normalize_pub(cit.get("pn") or "")
    quote = norm_ws(cit.get("quote") or "")
    locator = cit.get("locator") or ""
    rec = {"pub_number": pn, "role": cit.get("role") or "",
           "locator": locator, "quote_chars": len(quote), "status": "unverified",
           "reasons": []}
    if not pn:
        rec["reasons"].append("missing_pub_number")
        return rec
    doc = load_doc(docs_dir, pn)
    if doc is None:
        rec["reasons"].append("doc_missing:先跑 gp_fetch.py 取原文")
        return rec
    level = doc.get("evidence_level")
    if level != "original-text":
        rec["reasons"].append(f"evidence_level={level}:检索片段/仅元数据不可作为对比文件")
    if len(quote) < min_quote:
        rec["reasons"].append(f"quote_too_short:<{min_quote}字")
    hay = norm_ws("\n".join(
        [doc.get("title") or "", doc.get("abstract") or ""]
        + [(c.get("text") or "") for c in doc.get("claims") or []]
        + [doc.get("description") or ""]))
    if quote and quote not in hay:
        rec["reasons"].append("quote_not_found:引用片段未逐字出现在该件原文中")
    if locator:
        target = locator_text(doc, locator)
        if target is None:
            rec["reasons"].append(f"locator_invalid:{locator}")
        elif quote and quote not in norm_ws(target):
            rec["reasons"].append(f"locator_mismatch:片段不在 {locator}")
        else:
            rec["locator_ok"] = True
    elif strict_locator:
        rec["reasons"].append("locator_missing:--strict-locator 要求给出定位符")
    pub_date = doc.get("publication_date") or ""
    rec["publication_date"] = pub_date
    if cutoff:
        if not pub_date:
            rec["reasons"].append("publication_date_unknown")
        elif pub_date > cutoff:
            rec["reasons"].append(f"date_after_cutoff:公开日{pub_date}>截止{cutoff}")
    rec["sha256"] = doc.get("sha256")
    rec["doc_url"] = doc.get("url")
    rec["retrieved_at"] = doc.get("retrieved_at")
    if not rec["reasons"]:
        rec["status"] = "verified"
    return rec


def main(argv=None) -> int:
    ensure_utf8_stdio()
    ap = argparse.ArgumentParser(description="对比文件核验门禁（GP_VERIFY_JSON 单行输出）")
    ap.add_argument("--citations", required=True, help="拟引用列表 JSON")
    ap.add_argument("--docs", required=True, help="gp_fetch.py 的 --out 目录")
    ap.add_argument("--min-quote", type=int, default=20, help="引用片段最小字数（默认 20）")
    ap.add_argument("--cutoff", help="公开日截止（YYYY-MM-DD），用于申请日前公开资格判断")
    ap.add_argument("--strict-locator", action="store_true", help="强制要求定位符")
    ap.add_argument("--out", help="完整结果落盘")
    ap.add_argument("--audit", help="审计 JSONL 追加路径")
    args = ap.parse_args(argv)

    try:
        with open(args.citations, encoding="utf-8") as fh:
            cits = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        note(f"citations read failed: {type(exc).__name__}")
        return EXIT_ARGS
    if not isinstance(cits, list) or not cits:
        note("citations must be a non-empty JSON array")
        return EXIT_ARGS

    records = [verify_one(c, args.docs, args.min_quote, args.cutoff, args.strict_locator)
               for c in cits]
    ok = [r for r in records if r["status"] == "verified"]
    payload = {
        "checked_at": now_iso(), "docs_dir": os.path.abspath(args.docs),
        "total": len(records), "verified": len(ok), "failed": len(records) - len(ok),
        "all_verified": len(ok) == len(records), "records": records,
        "policy": "只有 status=verified 的条目才可写入现有技术检索报告并作为 X/Y/A 引用",
    }
    if args.out:
        write_json(args.out, payload)
    emit("GP_VERIFY_JSON", payload)
    append_audit(args.audit, {"ts": payload["checked_at"], "total": payload["total"],
                              "verified": payload["verified"], "failed": payload["failed"]})
    if payload["all_verified"]:
        return EXIT_OK
    note(f"unverified {payload['failed']}/{payload['total']} records: see records[].reasons")
    return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
