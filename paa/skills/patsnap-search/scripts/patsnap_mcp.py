#!/usr/bin/env python3
"""智慧芽"专利&文献融合检索" MCP 客户端（streamable HTTP，stdlib only）。

服务端：https://connect.zhihuiya.com/2b0355/logic-mcp（工具：search_patent、search_literature、fetch_patent、
fetch_patent_lifecycle、fetch_literature、build_patent_boolean_query 等）。与 REST 开放平台分开计费/授权：
REST 报 67200004/67200005 时 MCP 可能仍可用，反之亦然。

密钥：环境变量 PATSNAP_MCP_KEY，否则 PATSNAP_API_KEY / ZHIHUIYA_API_KEY / .env（同 patsnap.py）。不回显、不入证据。

子命令（证据 JSON 存 --out：工具名、参数、取回时间、sha256、原始返回）：
  tools                                   列出工具与参数
  call  --tool NAME --args JSON|@file     任意工具
  search --semantic-file F | --semantic T [--keywords K ...] [--limit N] [--offset N] [--family]
  fetch  --pn PN [--md]                   fetch_patent 全文（著录+权利要求+说明书）
  life   --pn PN                          fetch_patent_lifecycle 法律事件
  lit    --semantic T [--keywords K ...]  search_literature

红线：semantic_query 若含未公开技术方案全文，须用户对该内容明确授权（同 patsnap_ai.py）。
检索结果是候选，入 01 前须 fetch 原文；结论不等于授权概率。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from patsnap import api_key, save  # noqa: E402

URL = "https://connect.zhihuiya.com/2b0355/logic-mcp"


class MCP:
    def __init__(self, url: str = URL, key: str | None = None):
        self.url, self.sid, self.i = url, None, 0
        self.key = key or os.environ.get("PATSNAP_MCP_KEY") or api_key()[0]
        self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                "clientInfo": {"name": "patsnap_mcp", "version": "1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _post(self, body: dict) -> tuple[list[dict], str]:
        h = {"Authorization": "Bearer " + self.key, "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"), headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                self.sid = r.headers.get("Mcp-Session-Id") or self.sid
                raw = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
        msgs = [json.loads(m) for m in re.findall(r"^data:\s*(.+)$", raw, re.M)]
        if not msgs and raw.strip().startswith("{"):
            msgs = [json.loads(raw)]
        return msgs, raw

    def rpc(self, method: str, params: dict) -> dict:
        self.i += 1
        msgs, raw = self._post({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params})
        for m in msgs:
            if m.get("id") == self.i:
                return m.get("result") or {"error": m.get("error")}
        return {"error": raw[:500]}

    def call(self, tool: str, args: dict) -> dict:
        r = self.rpc("tools/call", {"name": tool, "arguments": args})
        text = "\n".join(c.get("text", "") for c in r.get("content", []))
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            data = {"_text": text}
        ok = not r.get("isError") and not r.get("error") and (not isinstance(data, dict) or data.get("status") != "error")
        return dict(endpoint=f"MCP {tool}", request=args, http=200, ok=ok,
                    retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), response=data)


def _docs(rec: dict) -> list[dict]:
    d = rec["response"].get("data") if isinstance(rec["response"], dict) else None
    out = []
    for x in (d or {}).get("docs", []) if isinstance(d, dict) else []:
        out.append({k: x.get(k) for k in ("pn", "id", "title", "assignee", "application_date", "publication_date",
                                          "score", "relevance") if x.get(k) is not None}
                   or {"title": x.get("title"), "id": x.get("id")})
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tools")
    p = sub.add_parser("call"); p.add_argument("--tool", required=True); p.add_argument("--args", required=True)
    for name in ("search", "lit"):
        p = sub.add_parser(name)
        p.add_argument("--semantic"); p.add_argument("--semantic-file", type=Path)
        p.add_argument("--keywords", nargs="*"); p.add_argument("--limit", type=int, default=20)
        p.add_argument("--offset", type=int, default=0)
        if name == "search":
            p.add_argument("--family", action="store_true", help="collapse_family")
    for name in ("fetch", "life"):
        p = sub.add_parser(name); p.add_argument("--pn", required=True)
        p.add_argument("--md", action="store_true", help="markdown 格式")
    for p in sub.choices.values():
        p.add_argument("--out", type=Path, help="证据 JSON 目录")
        p.add_argument("--full", action="store_true", help="stdout 打印完整返回")
    a = ap.parse_args()
    m = MCP()
    if a.cmd == "tools":
        for t in m.rpc("tools/list", {}).get("tools", []):
            print("##", t["name"], "-", (t.get("description") or "")[:200].replace("\n", " "))
            print("  ", list(t.get("inputSchema", {}).get("properties", {})))
        return
    if a.cmd == "call":
        args = json.loads(Path(a.args[1:]).read_text(encoding="utf-8") if a.args.startswith("@") else a.args)
        tool, stem = a.tool, a.tool
    elif a.cmd in ("search", "lit"):
        sem = a.semantic_file.read_text(encoding="utf-8").strip() if a.semantic_file else a.semantic
        strat = (["semantic"] if sem else []) + (["keyword"] if a.keywords else [])
        args = {"search_strategy": strat, "limit": a.limit, "offset": a.offset}
        if sem:
            args["semantic_query"] = sem
        if a.keywords:
            args["keywords"] = a.keywords
        if a.cmd == "search" and a.family:
            args["collapse_family"] = True
        tool = "search_patent" if a.cmd == "search" else "search_literature"
        stem = f"{a.cmd}_{(a.keywords or [sem or ''])[0][:30]}"
    else:
        tool = "fetch_patent" if a.cmd == "fetch" else "fetch_patent_lifecycle"
        args = {"patent_id": a.pn, "language": "zh-CN"}
        if a.md:
            args["format"] = "markdown"
        stem = f"{a.cmd}_{a.pn}"
    rec = m.call(tool, args)
    save(rec, a.out, "mcp_" + stem)
    if a.full or a.cmd in ("fetch", "life", "call"):
        print(json.dumps(rec["response"], ensure_ascii=False, indent=1)[:200000])
    else:
        d = rec["response"].get("data", {}) if isinstance(rec["response"], dict) else {}
        print(json.dumps({"ok": rec["ok"], "total_hits": d.get("total_hits") if isinstance(d, dict) else None,
                          "docs": _docs(rec), "error": None if rec["ok"] else str(rec["response"])[:300]},
                         ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
