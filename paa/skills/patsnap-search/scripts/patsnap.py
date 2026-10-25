#!/usr/bin/env python3
"""智慧芽（PatSnap）开放平台检索与取件客户端——方案一：只用检索与数据接口，不外发技术方案。

子命令（每次调用都把请求与原始响应存为证据 JSON，含取回时间与 sha256）：
  count     --query Q                       P001 检索式命中数
  search    --query Q [--limit N]           P002 检索式检索（TACD/TTL/ABST/CLMS/IPC 等字段语法）
  semantic  --text T  [--limit N]           P008 语义检索；T 限 80 字，只放公开层级的主题词
  similar   --pn PN   [--limit N]           P007 以已公开专利为种子找相似专利
  paper     --keywords K1 K2 ... [--semantic T] [--limit N]   P081 论文检索（source=paper）
  fetch     --pn PN [--parts biblio,claims,desc,legal]        P012/P018/P019/P041 取原文
  indicators --pns PN1:92% PN2:88% ...      P050 技术创新 + P051 可专利性（相似专利群统计；相似度取自 semantic/similar）

密钥：环境变量 PATSNAP_API_KEY / ZHIHUIYA_API_KEY，否则从当前目录向上找 .env
（识别 PATSNAP_API_KEY=、ZHIHUIYA_API_KEY=，以及"智慧芽 KEY="写法）。密钥不回显、不写入证据。

红线：本客户端不提供 AI 查新（AI35/M002/AI29/AI30）、Pat GPT、撰写类接口——它们要提交技术方案全文，
与"未公开技术仅本机处理"冲突；如确需使用，须用户针对具体内容明确授权后改用 patsnap_ai.py。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://connect.zhihuiya.com"
SEMANTIC_MAX = 80
KEY_RE = re.compile(r"^\s*(?:PATSNAP_API_KEY|ZHIHUIYA_API_KEY|智慧芽\s*KEY)\s*=\s*(\S+)", re.M)


def api_key() -> tuple[str, str]:
    for name in ("PATSNAP_API_KEY", "ZHIHUIYA_API_KEY"):
        if os.environ.get(name):
            return os.environ[name], f"env:{name}"
    for d in [Path.cwd(), *Path.cwd().parents]:
        f = d / ".env"
        if f.is_file():
            m = KEY_RE.search(f.read_text(encoding="utf-8", errors="ignore"))
            if m:
                return m.group(1), f"dotenv:{f}"
    raise SystemExit("未找到智慧芽密钥：设置 PATSNAP_API_KEY 或在 .env 中写 PATSNAP_API_KEY=sk-...")


def call(method: str, path: str, body: dict | None = None, query: dict | None = None) -> dict:
    key, _ = api_key()
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode("utf-8") if body is not None else None,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, raw = r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"_raw": raw[:2000]}
    ok = status == 200 and (data.get("status") in (True, "success"))
    return dict(endpoint=f"{method} {path}", request=body or query, http=status, ok=ok,
                retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(), response=data)


def save(rec: dict, out: Path | None, stem: str) -> None:
    if not out:
        return
    out.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]+", "_", stem)[:80]
    p = out / f"{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}.json"
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[evidence] {p}", file=sys.stderr)


def strip_tags(s: str) -> str:
    s = re.sub(r"<sup>(.*?)</sup>", r"^\1", s or "")
    s = re.sub(r"</div>|<br\s*/?>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def hits(rec: dict) -> list[dict]:
    d = rec["response"].get("data") or {}
    rows = d.get("results") if isinstance(d, dict) else None
    out = []
    for r in rows or []:
        out.append({k: r.get(k) for k in ("pn", "patent_id", "title", "original_assignee", "apdt", "pbdt", "relevancy") if r.get(k) is not None})
    return out


def paper_hits(rec: dict) -> list[dict]:
    d = rec["response"].get("data") or {}
    return [{k: x.get(k) for k in ("id", "title", "publication_date", "doi", "venue", "cited_count", "url") if x.get(k) is not None}
            for x in d.get("docs") or []]


def total(rec: dict):
    d = rec["response"].get("data") or {}
    return d.get("total_search_result_count") or d.get("total_hits") if isinstance(d, dict) else None


def cmd_fetch(pn: str, parts: list[str]) -> dict:
    ep = {"biblio": "/basic-patent-data/bibliography", "claims": "/basic-patent-data/claim-data",
          "desc": "/basic-patent-data/description-data", "legal": "/basic-patent-data/simple-legal-status"}
    res = {"pn": pn, "parts": {}}
    for p in parts:
        rec = call("GET", ep[p], query={"patent_number": pn})
        res["parts"][p] = rec
    text = {}
    for p, rec in res["parts"].items():
        d = rec["response"].get("data") or []
        d0 = d[0] if isinstance(d, list) and d else {}
        if p == "claims":
            text[p] = "\n".join(strip_tags(c.get("claim_text", "")) for c in d0.get("claims", []) if c.get("lang") in ("CN", "ZH", None)) \
                or "\n".join(strip_tags(c.get("claim_text", "")) for c in d0.get("claims", []))
        elif p == "desc":
            descs = d0.get("description", []) if isinstance(d0, dict) else []
            text[p] = "\n".join(strip_tags(x.get("text", "")) for x in descs)
        elif p == "legal":
            text[p] = d0.get("simple_legal_status")
        elif p == "biblio":
            b = d0.get("bibliographic_data", d0) if isinstance(d0, dict) else {}
            text[p] = {k: b.get(k) for k in ("invention_title", "abstracts", "application_reference", "publication_reference",
                                               "priority_claims", "classification_ipcr", "parties") if k in b}
    res["text"] = text
    return res


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = {n: sub.add_parser(n) for n in ("count", "search", "semantic", "similar", "paper", "fetch", "indicators")}
    for n in ("count", "search"):
        s[n].add_argument("--query", required=True)
    s["semantic"].add_argument("--text", required=True)
    for n in ("similar", "fetch"):
        s[n].add_argument("--pn", required=True)
    s["paper"].add_argument("--keywords", nargs="+", required=True)
    s["paper"].add_argument("--semantic", default="")
    s["fetch"].add_argument("--parts", default="biblio,claims,legal")
    s["indicators"].add_argument("--pns", nargs="+", required=True)
    for n, p in s.items():
        if n in ("search", "semantic", "similar", "paper"):
            p.add_argument("--limit", type=int, default=50)
            p.add_argument("--country", nargs="*", help="如 CN US，留空为全部")
        p.add_argument("--out", type=Path, help="证据 JSON 目录")
        p.add_argument("--json", action="store_true", help="stdout 输出精简 JSON")
    a = ap.parse_args()

    if a.cmd == "count":
        rec = call("POST", "/search/patent/query-search-count/v2", {"query_text": a.query})
        summary = {"query": a.query, "total": total(rec), "ok": rec["ok"]}
    elif a.cmd == "search":
        rec = call("POST", "/search/patent/query-search-patent/v2",
                   {"query_text": a.query, "limit": a.limit, "collapse_type": "APNO", "collapse_by": "PBD", "collapse_order": "LATEST"})
        summary = {"query": a.query, "total": total(rec), "hits": hits(rec)}
    elif a.cmd == "semantic":
        if len(a.text) > SEMANTIC_MAX:
            raise SystemExit(f"语义文本 {len(a.text)} 字，超过 {SEMANTIC_MAX} 字上限：只放公开层级主题词，不放技术方案。")
        body = {"text": a.text, "limit": a.limit}
        if a.country:
            body["country"] = a.country
        rec = call("POST", "/search/patent/semantic-search-patent/v2", body)
        summary = {"text": a.text, "total": total(rec), "hits": hits(rec)}
    elif a.cmd == "similar":
        body = {"patent_number": a.pn, "limit": a.limit}
        if a.country:
            body["country"] = a.country
        rec = call("POST", "/search/patent/similar-search-patent/v2", body)
        summary = {"seed": a.pn, "total": total(rec), "hits": hits(rec)}
    elif a.cmd == "paper":
        if len(a.semantic) > SEMANTIC_MAX:
            raise SystemExit(f"--semantic 超过 {SEMANTIC_MAX} 字上限")
        strat = ["keyword"] + (["semantic"] if a.semantic else [])
        body = {"source": "paper", "search_strategy": strat, "keywords": a.keywords, "limit": min(a.limit, 100)}
        if a.semantic:
            body["semantic_query"] = a.semantic
        rec = call("POST", "/search-agent/rag/v4/search", body)
        summary = {"keywords": a.keywords, "total": total(rec), "hits": paper_hits(rec)}
    elif a.cmd == "fetch":
        res = cmd_fetch(a.pn, a.parts.split(","))
        rec = res
        summary = {"pn": a.pn, "ok": {k: v["ok"] for k, v in res["parts"].items()}, "text": res["text"]}
    else:
        # P050 需要每件的相似度：写成 PN:92%（取自 semantic/similar 结果），缺省按 0% 计
        pi = []
        for p in a.pns[:100]:
            pn, _, rel = p.partition(":")
            pi.append({"pn": pn, "relevancy": rel or "0%"})
        rec = {"tech_innovation": call("POST", "/patent-valuation-data/tech_innovation", {"patent_info": pi}),
               "patent_ability": call("POST", "/patent-valuation-data/patent_ability", {"patent_info": pi})}
        summary = {k: {kk: vv for kk, vv in (v["response"].get("data") or {}).items() if kk != "patent_info"} for k, v in rec.items()}
        summary["note"] = "相似专利群的统计指标，不是本申请的授权概率"
    save(rec, a.out, f"{a.cmd}_{getattr(a, 'pn', '') or getattr(a, 'query', '') or getattr(a, 'text', '') or 'x'}")
    if a.json or a.cmd in ("fetch", "indicators"):
        print(json.dumps(summary, ensure_ascii=False, indent=1))
    else:
        print(f"{a.cmd} total={summary.get('total')}")
        for h in summary.get("hits", []):
            print("  ", h.get("pn") or h.get("id"), h.get("relevancy", ""), h.get("apdt") or h.get("publication_date", ""),
                  h.get("title", ""), "|", h.get("original_assignee", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
