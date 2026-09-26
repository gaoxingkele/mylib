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


def patentscope_search(query: str, timeout: int = 45, retries: int = 2) -> dict:
    """PATENTSCOPE 检索。该站偶发 5xx（实测遇到 http_500），故对 5xx 做退避重试。"""
    import time as _t
    last = None
    for attempt in range(retries + 1):
        s = _session()
        try:
            r = s.get(f"{PS}/result.jsf", params={"query": query}, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            last = {"blocked": False, "error": f"network_error:{type(exc).__name__}", "hits": []}
        else:
            if r.status_code == 200:
                hits = parse_patentscope_results(r.text)
                res = {"blocked": False, "hits": hits, "url": str(r.url), "count": len(hits)}
                if attempt:
                    res["retried"] = attempt
                return res
            last = {"blocked": False, "error": f"http_{r.status_code}", "hits": [],
                    "url": str(r.url), "status": r.status_code}
            if r.status_code < 500:
                return last
        if attempt < retries:
            _t.sleep(3 * (attempt + 1))
    return last or {"blocked": False, "error": "unknown", "hits": []}


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


# ---------------------------------------------------------------- Google BigQuery（Google 官方通道）
#
# 表结构依据官方示例仓库 google/patents-public-data 核实（2026-09-26）：
#   patents-public-data.patents.publications
#     publication_number, country_code, priority_date(yyyymmdd), publication_date(yyyymmdd),
#     title_localized, abstract_localized, claims_localized（REPEATED RECORD: language/text）,
#     cpc（REPEATED RECORD: code）, assignee, inventor, citation …
#   patents-public-data.google_patents_research.publications
#     publication_number, country, top_terms, embedding_v1（向量，可做 cosine 相似检索）

PUBLIC_TABLE = "patents-public-data.patents.publications"
RESEARCH_TABLE = "patents-public-data.google_patents_research.publications"


def _bq_client():
    """返回 (client, error_dict)。"""
    try:
        from google.cloud import bigquery
    except ImportError:
        return None, {"error": "bigquery_sdk_missing",
                      "remedy": "pip install google-cloud-bigquery db-dtypes"}
    try:
        return bigquery.Client(), None
    except Exception as exc:  # noqa: BLE001
        return None, {"error": "bigquery_credentials_missing", "detail": type(exc).__name__,
                      "remedy": "gcloud auth application-default login，或设置 "
                                "GOOGLE_APPLICATION_CREDENTIALS 指向服务账号 JSON"}


def bigquery_probe() -> dict:
    """检查官方 Google Patents BigQuery 通道的前置条件（不发查询）。"""
    info = {"backend": "bigquery", "dataset": PUBLIC_TABLE,
            "research_dataset": RESEARCH_TABLE}
    client, err = _bq_client()
    if err:
        info.update(err)
        info["installed"] = err["error"] != "bigquery_sdk_missing"
        return info
    info.update({"installed": True, "credentials": "ok", "project": client.project})
    return info


def bigquery_dry_run(sql: str, params: list | None = None) -> dict:
    """干跑：只报预计扫描字节数，不计费。预算控制的第一步。"""
    client, err = _bq_client()
    if err:
        return err
    from google.cloud import bigquery
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False,
                                  query_parameters=params or [])
    job = client.query(sql, job_config=cfg)
    gb = (job.total_bytes_processed or 0) / 1e9
    return {"dry_run": True, "total_bytes_processed": job.total_bytes_processed,
            "estimate_gb": round(gb, 3),
            "free_tier_gb_per_month": 1000,
            "within_free_tier_single_query": gb <= 1000}


def bigquery_lookup(pn: str, lang: str | None = None, timeout: int = 120) -> dict:
    """按公开号从官方数据集取著录项 + 权利要求全文。"""
    client, err = _bq_client()
    if err:
        return err
    from google.cloud import bigquery
    sql = (
        "SELECT publication_number, country_code, publication_date, priority_date, "
        "title_localized, abstract_localized, claims_localized, cpc, assignee, inventor "
        f"FROM `{PUBLIC_TABLE}` WHERE publication_number = @pn LIMIT 1"
    )
    params = [bigquery.ScalarQueryParameter("pn", "STRING", pn)]
    est = bigquery_dry_run(sql, params)
    rows = [dict(r) for r in client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params),
        timeout=timeout).result()]
    return {"pub_number": pn, "rows": rows, "estimate": est}


def bigquery_normalize_row(row: dict, lang: str | None = None) -> dict:
    """把 BigQuery 行转成本 skill 统一的 doc 结构（含公开日 ISO 化与权利要求切分）。"""
    def pick(localized, want):
        """localized 是 [{language, text}, …]；按期望语言优先取，其次 en，最后第一个。"""
        if isinstance(localized, str):
            return localized
        if not localized:
            return ""
        want = want or ""
        for item in localized:
            if (item.get("language") or "") == want and item.get("text"):
                return item["text"]
        for item in localized:
            if (item.get("language") or "") == "en" and item.get("text"):
                return item["text"]
        return (localized[0].get("text") or "")

    country = (row.get("country_code") or "").upper()
    want = lang or ("zh" if country == "CN" else "en")
    pub = row.get("publication_date")
    iso = ""
    if isinstance(pub, int) and pub > 10000000:
        s = str(pub)
        iso = f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    claim_text = pick(row.get("claims_localized"), want)
    claims = []
    if claim_text:
        parts = re.split(r"(?m)^\s*(\d{1,3})\s*[.、]\s*", claim_text)
        if len(parts) > 2:
            for i in range(1, len(parts) - 1, 2):
                claims.append({"claim_no": int(parts[i]), "text": parts[i + 1].strip()})
        else:
            for i, line in enumerate([l for l in claim_text.split("\n") if l.strip()], 1):
                claims.append({"claim_no": i, "text": line.strip()})
    cpc = row.get("cpc") or []
    codes = [c.get("code", "") for c in cpc] if isinstance(cpc, list) else []
    return {
        "pub_number": row.get("publication_number") or "",
        "country": country,
        "title": (pick(row.get("title_localized"), want) or "")[:300],
        "publication_date": iso,
        "priority_date": str(row.get("priority_date") or ""),
        "abstract": pick(row.get("abstract_localized"), want),
        "claims": claims,
        "claim_count": len(claims),
        "description": "",
        "description_chars": 0,
        "cpc": codes[:12],
        "assignee": row.get("assignee") or "",
        "inventor": row.get("inventor") or "",
        "source": "google_patents_bigquery",
        "backend": "bigquery",
        "evidence_level": "original-text" if claims else "metadata-only",
    }


def bigquery_search(keywords: list[str], country: str | None = None,
                    cpc_prefix: str | None = None, after_priority: str | None = None,
                    before_priority: str | None = None, limit: int = 20,
                    timeout: int = 180) -> dict:
    """关键词/CPC/国别/日期条件检索官方数据集（廉价路径：只用可过滤字段）。

    ``after_priority``/``before_priority`` 形如 ``2015-01-01``（转成 yyyymmdd 整数比较）。
    """
    client, err = _bq_client()
    if err:
        return err
    from google.cloud import bigquery
    where, params = [], []
    for i, kw in enumerate(keywords or []):
        p = f"kw{i}"
        where.append(f"(EXISTS (SELECT 1 FROM UNNEST(title_localized) t WHERE LOWER(t.text) LIKE @{p}) "
                     f"OR EXISTS (SELECT 1 FROM UNNEST(abstract_localized) a WHERE LOWER(a.text) LIKE @{p}))")
        params.append(bigquery.ScalarQueryParameter(p, "STRING", f"%{kw.lower()}%"))
    if country:
        where.append("country_code = @cc")
        params.append(bigquery.ScalarQueryParameter("cc", "STRING", country.upper()))
    if cpc_prefix:
        where.append("EXISTS (SELECT 1 FROM UNNEST(cpc) c WHERE STARTS_WITH(c.code, @cpc))")
        params.append(bigquery.ScalarQueryParameter("cpc", "STRING", cpc_prefix.upper()))
    if after_priority:
        where.append("priority_date >= @ap")
        params.append(bigquery.ScalarQueryParameter(
            "ap", "INT64", int(after_priority.replace("-", "")) * 10000))
    if before_priority:
        where.append("priority_date <= @bp")
        params.append(bigquery.ScalarQueryParameter(
            "bp", "INT64", int(before_priority.replace("-", "")) * 10000))
    sql = ("SELECT publication_number, country_code, publication_date, priority_date, "
           "title_localized, assignee "
           f"FROM `{PUBLIC_TABLE}` "
           + ("WHERE " + " AND ".join(where) if where else "")
           + " ORDER BY priority_date DESC LIMIT @lim")
    params.append(bigquery.ScalarQueryParameter("lim", "INT64", int(limit)))
    est = bigquery_dry_run(sql, params)
    rows = [bigquery_normalize_row(dict(r)) for r in client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params),
        timeout=timeout).result()]
    return {"hits": rows, "estimate": est, "count": len(rows)}


def bigquery_similar(pn: str, country: str | None = None, limit: int = 20,
                     max_gb: float = 20.0, timeout: int = 300) -> dict:
    """**语义近邻检索**：以某件专利的向量为种子，在官方研究子集里找最相似的公开。

    这是 incoPat 语义检索的免费等价物（用 Google 官方数据集的 ``embedding_v1``）。
    整表扫描代价高，故先干跑估算，超过 ``max_gb`` 直接拒绝执行。
    """
    client, err = _bq_client()
    if err:
        return err
    from google.cloud import bigquery
    where = "gpr.publication_number != @pn"
    if country:
        where += " AND gpr.country = @cc"
    sql = (
        "WITH seed AS (SELECT embedding_v1 FROM `" + RESEARCH_TABLE + "` "
        "WHERE publication_number = @pn LIMIT 1) "
        "SELECT gpr.publication_number, gpr.country, gpr.top_terms, "
        "cosine_distance(gpr.embedding_v1, seed.embedding_v1) AS distance "
        f"FROM `{RESEARCH_TABLE}` gpr, seed WHERE {where} "
        "ORDER BY distance LIMIT @lim"
    )
    params = [bigquery.ScalarQueryParameter("pn", "STRING", pn),
              bigquery.ScalarQueryParameter("lim", "INT64", int(limit))]
    if country:
        params.append(bigquery.ScalarQueryParameter("cc", "STRING", country))
    est = bigquery_dry_run(sql, params)
    if est.get("estimate_gb", 0) > max_gb:
        return {"error": "estimate_over_budget", "estimate": est,
                "remedy": f"预计扫描 {est.get('estimate_gb')} GB > --max-gb {max_gb}；"
                          "请加 country 过滤或提高预算上限"}
    rows = [dict(r) for r in client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params),
        timeout=timeout).result()]
    return {"seed": pn, "hits": rows, "estimate": est, "count": len(rows)}
