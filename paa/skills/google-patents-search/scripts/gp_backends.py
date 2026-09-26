# -*- coding: utf-8 -*-
"""检索/取件的后端实现：**全部是 HTTP 客户端，不使用浏览器自动化**。

三个后端：

``google``       Google Patents 站点自身的 JSON/HTML 接口（最接近"Google Patents API"）。
                 用 curl_cffi 以 Chrome 指纹发请求。实测：普通 requests 与无头浏览器都会被
                 Google 的 "Sorry… automated queries" 页拦下；curl_cffi 在多数网络下可行，
                 但在被 Google 判定为可疑出口（本机即如此）时仍返回 503——这时如实上报
                 ``blocked_by_google``，不伪装成"0 命中"。
``patentscope``  WIPO PATENTSCOPE（官方库，免 key、免浏览器）。实测本机可用并覆盖 CN。
                 流程：result.jsf 检索 → 取结果行内部 ``data-rk`` 作 docId → detail.jsf 取详情。
``bigquery``     Google 官方专利数据集 ``patents-public-data``（真正的 Google 官方 API 通道），
                 需要 GCP 项目与凭据；未安装/未登录时给出明确前置条件。
"""
from __future__ import annotations

import re

from gp_common import (  # noqa: E402
    BASE, looks_blocked, normalize_pub, patent_url,
)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

GOOGLE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
}


def _session():
    """curl_cffi 会话（Chrome TLS / HTTP2 指纹）。未安装时给出可读错误。"""
    try:
        from curl_cffi import requests as cr
    except ImportError as exc:  # noqa: BLE001
        raise RuntimeError(
            "curl_cffi 未安装：pip install curl_cffi"
            "（本 skill 不依赖浏览器，但需要该库模拟 Chrome 指纹）") from exc
    return cr.Session(impersonate="chrome")


def _strip(html: str) -> str:
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    t = re.sub(r"<br\s*/?>", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
          .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- Google Patents 站点接口

def google_search(query: str, rows: int = 10, page: int = 1, lang: str | None = None,
                  timeout: int = 30) -> dict:
    """走 Google Patents 站点内部 JSON 接口。返回 {blocked, hits, url, ...}。"""
    from urllib.parse import quote_plus
    s = _session()
    try:
        s.get(f"{BASE}/", timeout=timeout)      # 先取一次页面，拿到必要 Cookie
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "hits": []}
    api = (f"{BASE}/xhr/query?url={quote_plus('q=' + quote_plus(query))}"
           + (f"&page={page}" if page and page > 1 else "") + "&exp=")
    try:
        r = s.get(api, timeout=timeout,
                  headers={**GOOGLE_HEADERS, "Referer": f"{BASE}/?q=" + quote_plus(query)})
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "hits": []}
    if looks_blocked(r.status_code, r.text):
        return {"blocked": True, "status": r.status_code, "url": api, "hits": []}
    if r.status_code != 200:
        return {"blocked": False, "error": f"http_{r.status_code}", "url": api, "hits": []}
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        return {"blocked": False, "error": "not_json", "url": api, "hits": []}
    hits = []
    for cluster in (data.get("results") or {}).get("cluster") or []:
        for item in cluster.get("result") or []:
            p = item.get("patent") or {}
            pn = normalize_pub(p.get("publication_number") or "")
            if not pn:
                continue
            hits.append({
                "pub_number": pn,
                "title": (p.get("title") or "").strip(),
                "assignee": (p.get("assignee") or "").strip(),
                "inventor": (p.get("inventor") or "").strip(),
                "priority_date": p.get("priority_date") or "",
                "filing_date": p.get("filing_date") or "",
                "publication_date": p.get("publication_date") or "",
                "snippet": (p.get("snippet") or "").strip()[:600],
                "pdf_url": p.get("pdf") or "",
                "url": patent_url(pn, lang),
                "source": "google_patents",
                "backend": "google",
                "evidence_level": "snippet-degraded",
            })
    return {"blocked": False, "hits": hits, "url": api, "status": r.status_code,
            "total_num_results": (data.get("results") or {}).get("total_num_results")}


def google_fetch(pn: str, lang: str | None = None, timeout: int = 30) -> dict:
    from gp_common import parse_patent_doc
    url = patent_url(pn, lang)
    s = _session()
    try:
        r = s.get(url, timeout=timeout, headers={"Accept": "text/html,application/xhtml+xml"})
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "url": url}
    if looks_blocked(r.status_code, r.text):
        return {"blocked": True, "status": r.status_code, "url": url}
    doc = parse_patent_doc(r.text, pn)
    doc["url"] = url
    doc["backend"] = "google"
    return {"blocked": False, "doc": doc, "html": r.text}


# ---------------------------------------------------------------- WIPO PATENTSCOPE

PS = "https://patentscope.wipo.int/search/en"
PS_ROW = re.compile(r'<tr[^>]*data-ri="(\d+)"[^>]*data-rk="([^"]+)"[\s\S]*?</tr>')


def parse_patentscope_results(html: str) -> list[dict]:
    """解析 PATENTSCOPE 结果页。

    实测行结构（2026-09-26）：
        tr[data-ri][data-rk=<docId>]
          div.ps-patent-result[data-mt-ipc="A61F 9/04"]
            span.ps-patent-result--title--record-number      -> 序号
            a[href*="docId="]                                -> docId
            span.ps-patent-result--title--patent-number      -> 公开号数字部分
            span.ps-patent-result--title--title              -> 标题
            div.ps-patent-result--title--ctr-pubdate
               span.notranslate (1)                          -> 国家码
               span.notranslate (2)                          -> 种类码或 "-"
               span#...resultListTableColumnPubDate          -> 日期 dd.mm.yyyy
    """
    hits = []
    for m in PS_ROW.finditer(html):
        row = m.group(0)
        docid = m.group(2)
        md = re.search(r'docId=([A-Za-z0-9]+)', row)
        if md:
            docid = md.group(1)
        country = ""
        kind = ""
        mc = re.search(r'--title--ctr-pubdate">([\s\S]{0,200}?)</div>', row)
        if mc:
            spans = re.findall(r'<span[^>]*>([^<]{0,12})</span>', mc.group(1))
            if spans:
                country = spans[0].strip()
            if len(spans) > 1:
                kind = spans[1].strip()
        mnum = re.search(r'--title--patent-number"[^>]*>([^<]{4,20})<', row)
        number = mnum.group(1).strip() if mnum else ""
        mt = re.search(r'--title--title[^"]*"[^>]*>([\s\S]{5,400}?)</span>\s*</div>', row)
        title = _strip(mt.group(1)) if mt else ""
        mdate = re.search(r'id="[^"]*resultListTableColumnPubDate"[^>]*>([^<]{6,20})<', row)
        raw_date = mdate.group(1).strip() if mdate else ""
        dm = re.search(r"\d{2}\.\d{2}\.\d{4}", raw_date)
        iso = re.sub(r"(\d{2})\.(\d{2})\.(\d{4})", r"\3-\2-\1", dm.group(0)) if dm else ""
        mipc = re.search(r'data-mt-ipc="([^"]+)"', row)
        kc = kind if re.fullmatch(r"[A-Z]\d?", kind or "") else ""
        pn = normalize_pub(f"{country}{number}{kc}") if (country and number) else ""
        hits.append({
            "pub_number": pn,
            "title": title,
            "assignee": "",
            "inventor": "",
            "priority_date": "",
            "filing_date": "",
            "publication_date": iso,
            "snippet": _strip(row)[:600],
            "ipc": mipc.group(1).strip() if mipc else "",
            "pdf_url": "",
            "url": f"{PS}/detail.jsf?docId={docid}",
            "doc_id": docid,
            "source": "wipo_patentscope",
            "backend": "patentscope",
            "evidence_level": "snippet-degraded",
        })
    return hits


def patentscope_search(query: str, timeout: int = 45) -> dict:
    s = _session()
    try:
        r = s.get(f"{PS}/result.jsf", params={"query": query}, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "hits": []}
    if r.status_code != 200:
        return {"blocked": False, "error": f"http_{r.status_code}", "hits": [], "url": str(r.url)}
    hits = parse_patentscope_results(r.text)
    return {"blocked": False, "hits": hits, "url": str(r.url), "count": len(hits)}


def patentscope_fetch(doc_id: str, timeout: int = 45) -> dict:
    """按内部 docId 取详情页（著录项为主；PATENTSCOPE 详情页不保证给权利要求全文）。"""
    s = _session()
    try:
        r = s.get(f"{PS}/detail.jsf", params={"docId": doc_id}, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}"}
    if r.status_code != 200:
        return {"blocked": False, "error": f"http_{r.status_code}"}
    html = r.text
    text = _strip(html)
    title = ""
    mt = re.search(r'<h1[^>]*>([\s\S]{5,300}?)</h1>', html)
    if mt:
        title = _strip(mt.group(1))
    pns = re.findall(r"\b([A-Z]{2}\d{6,13}[A-Z]?\d?)\b", text)
    doc = {
        "pub_number": normalize_pub(pns[0]) if pns else "",
        "title": title,
        "abstract": "",
        "claims": [],
        "claim_count": 0,
        "description": "",
        "description_chars": 0,
        "raw_text_chars": len(text),
        "url": f"{PS}/detail.jsf?docId={doc_id}",
        "source": "wipo_patentscope",
        "backend": "patentscope",
        "evidence_level": "metadata-only",
        "note": "PATENTSCOPE 详情页以著录项为主；权利要求全文请用 google 后端或公共全文库",
    }
    return {"blocked": False, "doc": doc, "html": html}


# ---------------------------------------------------------------- Google BigQuery（官方通道）

def bigquery_probe() -> dict:
    """检查官方 Google Patents BigQuery 通道的前置条件（不发查询）。"""
    info = {"backend": "bigquery", "dataset": "patents-public-data.patents.publications"}
    try:
        import google.cloud.bigquery  # noqa: F401
        info["installed"] = True
    except ImportError:
        info["installed"] = False
        info["remedy"] = "pip install google-cloud-bigquery db-dtypes"
        return info
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        info["project"] = client.project
        info["credentials"] = "ok"
    except Exception as exc:  # noqa: BLE001
        info["credentials"] = f"missing:{type(exc).__name__}"
        info["remedy"] = ("需要 GCP 项目与凭据：gcloud auth application-default login，"
                          "或设置 GOOGLE_APPLICATION_CREDENTIALS 指向服务账号 JSON")
    return info


def bigquery_lookup(pn: str, timeout: int = 120) -> dict:
    """按公开号取官方数据集条目（著录项 + 摘要 + 可得权利要求）。"""
    try:
        from google.cloud import bigquery
    except ImportError:
        return {"error": "bigquery_sdk_missing",
                "remedy": "pip install google-cloud-bigquery db-dtypes"}
    try:
        client = bigquery.Client()
    except Exception as exc:  # noqa: BLE001
        return {"error": "bigquery_credentials_missing", "detail": type(exc).__name__,
                "remedy": "gcloud auth application-default login"}
    sql = ("SELECT publication_number, country_code, publication_date, title_localized, "
           "assignee, inventor, abstract_localized, claims_localized "
           "FROM `patents-public-data.patents.publications` "
           "WHERE publication_number = @pn LIMIT 1")
    job = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("pn", "STRING", pn)])
    rows = [dict(r) for r in client.query(sql, job_config=job, timeout=timeout).result()]
    return {"pub_number": pn, "rows": rows}
