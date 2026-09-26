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
``tavily``       中继取件：本机出口被 Google 判定为可疑（patents.google.com 一律 503）时，
                 用 Tavily 官方 extract API 取同一公开页面，**能拿到摘要/说明书/权利要求全文**，
                 并附带引证表与相似文献表。它是"取件中继"，不是检索源；provenance 如实记 relay。
"""
from __future__ import annotations

import hashlib
import os
import re

from gp_common import (  # noqa: E402
    BASE, looks_blocked, normalize_pub, patent_url, split_pub,
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


_NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")


def patentscope_query_variants(query: str, country: str | None = None) -> tuple:
    """把检索式归一化成 PATENTSCOPE 可用的形式，返回 (候选检索式列表, 国别)。

    实测（2026-09-26，两轮）：

    第一轮误判：``EN_ALLTXT:(配电变压器 故障诊断)`` 表面看"10 命中"，曾被当作中文可用的证据；
    第二轮用真实案件的中文查询词复测发现，``EN_ALLTXT`` 是**英文机器翻译全文字段**，塞中文进去
    命中与否、相关与否都不稳定——同一天另外两组中文查询（``大模型 评测 缓存``、``题目版本 依赖
    失效 重算``）用 ``EN_ALLTXT`` 返回的候选与检索词毫无关系（私域直播间热点预测、堰塞湖灾害
    防治……）。对照测试 ``FP:(大模型 评测 缓存)``（Front Page：标题/摘要/申请人等前页字段，
    覆盖各文献原始语言，非机翻）——同一组中文词直接命中"大模型集群分流""KV缓存管理""大语言
    模型键值缓存安全检测"等真正相关的title；再用 ``FP:(物化视图 增量刷新)`` 复测同样精准命中
    多篇物化视图增量刷新专利。结论：**中文查询式必须用 FP，不能用 EN_ALLTXT**；纯英文查询式
    两者都可，仍用 EN_ALLTXT（已验证对英文词精确）。

    * 裸检索式（无字段算子）直接提交 → 0 命中，必须带字段算子；
    * 用户常按 Google 语法写 ``graphene eye mask country=CN``，该库不认 ``country=``。

    因此：抽掉 ``country=``/``ctr=`` 作为国别；已带字段算子的原样放行；否则按查询式是否含
    非 ASCII 字符选字段（含中文/日文/韩文等 → ``FP``，纯英文/数字 → ``EN_ALLTXT``），
    并在词数 >2 时追加"仅留最长两词""仅留最长一词"两个收窄候选，由调用方逐个试、命中即停。
    """
    q = (query or "").strip()
    m = re.search(r"\b(?:country|ctr|pn)\s*=\s*([A-Za-z]{2})\b", q)
    if m:
        country = country or m.group(1).upper()
        q = (q[:m.start()] + " " + q[m.end():]).strip()
    suffix = f" AND CTR:({country.upper()})" if country else ""
    if re.search(r"\b[A-Za-z_]{2,}\s*:", q):        # 已带字段算子，原样放行
        return ([q] if q else []), country
    toks = [t for t in re.split(r"[\s,，、;；]+", q) if t]
    if not toks:
        return [], country
    field = "FP" if _NON_ASCII_RE.search(q) else "EN_ALLTXT"
    out = [f"{field}:({' '.join(toks)}){suffix}"]
    if len(toks) > 2:
        srt = sorted(toks, key=len, reverse=True)
        out.append(f"{field}:({' '.join(srt[:2])}){suffix}")
        out.append(f"{field}:({srt[0]}){suffix}")
    return out, country


def patentscope_search(query: str, timeout: int = 45, retries: int = 2,
                       country: str | None = None) -> dict:
    """PATENTSCOPE 检索。该站偶发 5xx（实测遇到 http_500），故对 5xx 做退避重试。

    检索式先经 :func:`patentscope_query_variants` 归一化；多个候选按顺序试，命中即返回，
    并在结果里记 ``query_used`` / ``variants``，便于回溯到底哪条检索式起了作用。
    """
    import time as _t
    variants, country = patentscope_query_variants(query, country)
    if not variants:
        return {"blocked": False, "error": "empty_query", "hits": []}
    last = None
    for vq in variants:
        for attempt in range(retries + 1):
            s = _session()
            try:
                r = s.get(f"{PS}/result.jsf", params={"query": vq}, timeout=timeout)
            except Exception as exc:  # noqa: BLE001
                last = {"blocked": False, "error": f"network_error:{type(exc).__name__}",
                        "hits": [], "query_used": vq, "variants": variants}
            else:
                if r.status_code == 200:
                    hits = parse_patentscope_results(r.text)
                    res = {"blocked": False, "hits": hits, "url": str(r.url),
                           "count": len(hits), "query_used": vq, "variants": variants,
                           "country": country}
                    if attempt:
                        res["retried"] = attempt
                    if hits:
                        return res
                    last = res          # 0 命中：试下一个收窄候选
                    break
                last = {"blocked": False, "error": f"http_{r.status_code}", "hits": [],
                        "url": str(r.url), "status": r.status_code, "query_used": vq,
                        "variants": variants}
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


def _bq_pub_number(pn: str) -> str:
    """把规范化公开号转成 patents-public-data 实际存储的带分隔符形式。

    该数据集的 ``publication_number`` 一律是 ``{国家}-{数字}-{种类码}``
    （如 ``CN-117291184-A``），而本 skill 其余通道统一用无分隔符形式
    （``CN117291184A``）。不做这层转换会导致 ``lookup``/``similar`` 对任何
    真实存在的公开号都返回 not_found（2026-09-26 实测发现，含官方示例号）。
    """
    country, digits, kind = split_pub(pn)
    if not country or not digits:
        return pn
    return f"{country}-{digits}-{kind}" if kind else f"{country}-{digits}"


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
    params = [bigquery.ScalarQueryParameter("pn", "STRING", _bq_pub_number(pn))]
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
        "pub_number": normalize_pub(row.get("publication_number") or ""),
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
    where = ("gpr.publication_number != @pn AND gpr.embedding_v1 IS NOT NULL "
              "AND ARRAY_LENGTH(gpr.embedding_v1) = ARRAY_LENGTH(seed.embedding_v1)")
    if country:
        where += " AND gpr.country = @cc"
    sql = (
        "WITH seed AS (SELECT embedding_v1 FROM `" + RESEARCH_TABLE + "` "
        "WHERE publication_number = @pn AND embedding_v1 IS NOT NULL LIMIT 1) "
        "SELECT gpr.publication_number, gpr.country, gpr.top_terms, "
        "cosine_distance(gpr.embedding_v1, seed.embedding_v1) AS distance "
        f"FROM `{RESEARCH_TABLE}` gpr, seed WHERE {where} "
        "ORDER BY distance LIMIT @lim"
    )
    params = [bigquery.ScalarQueryParameter("pn", "STRING", _bq_pub_number(pn)),
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
    for r in rows:
        r["publication_number"] = normalize_pub(r.get("publication_number") or "")
    return {"seed": pn, "hits": rows, "estimate": est, "count": len(rows)}


# ---------------------------------------------------------------- Tavily 中继取件
#
# 用途：出口 IP 被 Google 反爬判定为可疑时（patents.google.com 恒 503，curl_cffi 指纹无效），
# 仍需要"该公开号到底公开了什么"的**原文**。做法是把同一公开页面交给 Tavily 官方 extract API，
# 由它取回并转成 Markdown —— 实测该 Markdown 含摘要、说明书、权利要求逐项，以及引证表、
# 相似文献表、PDF 直链。这不是绕 WAF 的破解：用的是有授权凭据的公开 API，取的是公开页面。
#
# 证据纪律：结果里始终带 relay / relay_key_source / url / retrieved_at，且 sha256 只覆盖文本。
# 中继文本可能有个别字符与页面渲染差异，故 gp_verify 会标记 relay provenance；
# 需要更强证据时用同一页的 PDF 直链（--save-pdf）做字节级留痕。

TAVILY_EXTRACT = "https://api.tavily.com/extract"
TAVILY_SEARCH = "https://api.tavily.com/search"
TAVILY_KEY_NAMES = ("TAVILY_API_KEY", "TAVILYAPI", "TAVILY_KEY", "TAVILY_TOKEN")
DOTENV_NAMES = (".env", ".env.local", ".env.cloubic")


def _dotenv_lookup(names: set) -> tuple:
    """从当前目录起向上最多 4 层找 .env，按键名（大小写不敏感）取第一个命中值。"""
    d = os.path.abspath(os.getcwd())
    for _ in range(5):
        for fn in DOTENV_NAMES:
            p = os.path.join(d, fn)
            if not os.path.exists(p):
                continue
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip().upper() in names:
                            return v.strip().strip('"').strip("'"), f"dotenv:{fn}"
            except OSError:
                continue
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return "", ""


def resolve_tavily_key(explicit: str | None = None) -> tuple:
    """返回 (key, 来源)。来源只报位置（env:名字 / dotenv:文件名 / cli），绝不回显 key。"""
    if explicit:
        return explicit.strip(), "cli"
    for n in TAVILY_KEY_NAMES + ("tavilyapi", "TavilyApi"):
        v = os.environ.get(n)
        if v:
            return v.strip(), f"env:{n}"
    return _dotenv_lookup({n.upper() for n in TAVILY_KEY_NAMES})


def tavily_extract(pn: str, lang: str | None = None, timeout: int = 90,
                   key: str | None = None) -> dict:
    """用 Tavily extract 中继取回某公开号的 Google Patents 页面，并解析成统一 doc 结构。"""
    from gp_common import parse_google_patents_markdown

    k, src = resolve_tavily_key(key)
    url = patent_url(pn, lang)
    if not k:
        return {"blocked": False, "error": "tavily_key_missing", "url": url, "hits": [],
                "remedy": "设置环境变量 TAVILY_API_KEY=<key>，或在当前目录（或其上层）的 .env "
                          "里写 TAVILY_API_KEY=…；本 skill 只把它当取件中继，不当检索源"}
    s = _session()
    body = {"urls": [url], "include_raw_content": True, "extract_depth": "advanced"}
    try:
        r = s.post(TAVILY_EXTRACT, timeout=timeout, json=body,
                   headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "url": url}
    if r.status_code in (401, 402, 403):
        return {"blocked": False, "error": "tavily_auth_failed", "status": r.status_code,
                "url": url, "key_source": src,
                "remedy": "检查凭据/额度（401=key 无效；402/403=额度或权限不足）"}
    if r.status_code == 429:
        return {"blocked": False, "error": "tavily_rate_limited", "status": 429, "url": url,
                "key_source": src}
    if r.status_code != 200:
        return {"blocked": False, "error": f"http_{r.status_code}", "status": r.status_code,
                "url": url, "key_source": src}
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        return {"blocked": False, "error": "not_json", "url": url, "key_source": src}
    results = data.get("results") or []
    if not results:
        failed = [f for f in (data.get("failed_results") or []) if isinstance(f, dict)]
        msg = str((failed[0].get("error") if failed else "") or "")
        # 与"被拦""缺凭据"区分开：404 表示该公开号在 Google Patents 确实没有页面
        # （实测常见于只收录在 PATENTSCOPE/CNIPA 的 CN 文献），不是本机网络问题。
        code = "doc_not_on_google_patents" if "404" in msg else "relay_extract_failed"
        remedy = ("该公开号在 Google Patents 无对应页面（常见于只收录在 PATENTSCOPE/CNIPA 的 "
                  "CN 文献）：请改用 incoPat/CNIPA 原文库，或按 PATENTSCOPE docId 直接查看"
                  ) if code == "doc_not_on_google_patents" else "稍后重试，或换 --backend google/bigquery"
        return {"blocked": False, "error": code, "message": msg, "url": url, "remedy": remedy,
                "failed_results": failed[:3], "key_source": src}
    res = results[0]
    md = res.get("raw_content") or res.get("content") or ""
    doc = parse_google_patents_markdown(md, pn)
    doc.update({
        "url": url,
        "backend": "tavily",
        "relay": "tavily_extract",
        "relay_key_source": src,
        "relay_depth": "advanced",
        "note": "文本由第三方中继取回公开页面后转 Markdown；引用前建议用 pdf_url 复核原文",
    })
    return {"blocked": False, "doc": doc, "html": md, "url": url,
            "relay": "tavily", "key_source": src, "status": r.status_code}


def fetch_binary(url: str, timeout: int = 120) -> dict:
    """下载二进制（用于 PDF 直链留痕）。返回 {ok, data, sha256, status, bytes}。"""
    s = _session()
    try:
        r = s.get(url, timeout=timeout, headers={"Accept": "application/pdf,*/*"})
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"network_error:{type(exc).__name__}"}
    if r.status_code != 200:
        return {"ok": False, "error": f"http_{r.status_code}", "status": r.status_code}
    data = r.content
    return {"ok": True, "data": data, "status": 200, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "url": url}


# ---------------------------------------------------------------- Tavily 中继检索

TAVILY_PATENT_URL_RE = re.compile(
    r"(?:patents\.google\.[a-z.]+|google\.[a-z.]+)/patents?/?(?:patent/)?"
    r"([A-Z]{2}\d{6,13}[A-Z]?\d?)", re.I)


def tavily_search(query: str, limit: int = 10, timeout: int = 60, key: str | None = None,
                  country: str | None = None) -> dict:
    """中继检索腿：用 Tavily 官方 search API 在 ``patents.google.com`` 域内检索。

    为什么需要：本机出口被 Google 判为可疑时，``google_search`` 恒 503，检索腿就只剩
    PATENTSCOPE 一个索引。实测（2026-09-26）Tavily 的 search 走它自己的出口，中文查询
    也能返回 Google Patents 的条目（``include_domains=["patents.google.com"]``），
    因此它是"Google 检索腿"的中继替代。**它是检索来源的中继，不是新证据源**：
    返回项一律 ``evidence_level=snippet-degraded``，必须再经 gp_fetch 取原文才能引用。

    只保留能解析出公开号的 Google Patents 链接，避免把普通网页混进对比文件池。
    """
    k, src = resolve_tavily_key(key)
    if not k:
        return {"blocked": False, "error": "tavily_key_missing", "hits": [],
                "remedy": "设置 TAVILY_API_KEY 后可用中继检索腿"}
    q = (query or "").strip()
    body = {"query": q, "max_results": max(1, min(limit * 2, 20)),
            "search_depth": "advanced", "include_domains": ["patents.google.com"]}
    s = _session()
    try:
        r = s.post(TAVILY_SEARCH, timeout=timeout, json=body,
                   headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    except Exception as exc:  # noqa: BLE001
        return {"blocked": False, "error": f"network_error:{type(exc).__name__}", "hits": []}
    if r.status_code in (401, 402, 403):
        return {"blocked": False, "error": "tavily_auth_failed", "status": r.status_code,
                "hits": [], "key_source": src,
                "remedy": "检查凭据/额度（401=key 无效；402/403=额度或权限不足）"}
    if r.status_code == 429:
        return {"blocked": False, "error": "tavily_rate_limited", "status": 429, "hits": [],
                "key_source": src}
    if r.status_code != 200:
        return {"blocked": False, "error": f"http_{r.status_code}", "status": r.status_code,
                "hits": [], "key_source": src}
    try:
        data = r.json()
    except Exception:  # noqa: BLE001
        return {"blocked": False, "error": "not_json", "hits": [], "key_source": src}
    hits, skipped = [], 0
    for it in data.get("results") or []:
        url = it.get("url") or ""
        m = TAVILY_PATENT_URL_RE.search(url)
        if not m:
            skipped += 1
            continue
        pn = normalize_pub(m.group(1))
        title = re.sub(r"\s*[-–—|]\s*Google Patents\s*$", "",
                       (it.get("title") or "").strip(), flags=re.I)
        title = re.sub(r"^[A-Z]{2}\d{6,13}[A-Z]?\d?\s*[-–—]\s*", "", title)
        hits.append({
            "pub_number": pn,
            "title": title,
            "assignee": "",
            "inventor": "",
            "priority_date": "",
            "filing_date": "",
            "publication_date": "",
            "snippet": (it.get("content") or "")[:600],
            "pdf_url": "",
            "url": url or patent_url(pn),
            "source": "google_patents_via_relay",
            "backend": "tavily",
            "relay": "tavily_search",
            "evidence_level": "snippet-degraded",
        })
    seen, uniq = set(), []
    for h in hits:
        if h["pub_number"] in seen:
            continue
        seen.add(h["pub_number"])
        uniq.append(h)
    return {"blocked": False, "hits": uniq[:limit], "count": len(uniq[:limit]),
            "raw_results": len(data.get("results") or []), "non_patent_skipped": skipped,
            "key_source": src, "relay": "tavily", "url": TAVILY_SEARCH}


# ---------------------------------------------------------------- 统一的"取件链"

DEFAULT_FETCH_CHAIN = ("google", "tavily", "bigquery")
CONFIG_ERRORS = frozenset({
    "tavily_key_missing", "bigquery_credentials_missing", "bigquery_sdk_missing",
})


def fetch_document(pn: str, backends=DEFAULT_FETCH_CHAIN, lang: str | None = None,
                   timeout: int = 40, tavily_key: str | None = None,
                   allow_relay: bool = True) -> dict:
    """按顺序尝试多个后端取同一公开号的原文，返回首个成功结果。

    ``gp_fetch.py`` 与 ``gp_pipeline.py`` 共用本函数，保证两条入口的降级顺序、
    退出判定与 ``attempts[]`` 记录一致。返回值：

    * 成功：``{ok: True, backend, doc, html, url, attempts}``
    * 失败：``{ok: False, blocked, reason, remedy, attempts}``
      （``reason`` ∈ all_backends_blocked / no_usable_channel / all_backends_failed）

    **绝不**把"被拦"或"缺凭据"降级成"没找到"：``attempts[]`` 会逐条保留原因。
    """
    attempts: list = []
    for b in backends:
        if b == "tavily" and not allow_relay:
            continue
        if b == "google":
            res = google_fetch(pn, lang=lang, timeout=timeout)
            if res.get("blocked"):
                attempts.append({"backend": b, "blocked": True, "status": res.get("status")})
                continue
            if res.get("error"):
                attempts.append({"backend": b, "error": res["error"],
                                 **({"detail": res["message"]} if res.get("message") else {})})
                continue
            doc, html, url = res["doc"], res.get("html", ""), res["doc"].get("url", "")
        elif b == "tavily":
            res = tavily_extract(pn, lang=lang, timeout=max(timeout, 90), key=tavily_key)
            if res.get("error"):
                attempts.append({"backend": b, "error": res["error"],
                                 **({"detail": res["message"]} if res.get("message") else {})})
                continue
            doc, html, url = res["doc"], res.get("html", ""), res["url"]
        elif b == "bigquery":
            res = bigquery_lookup(pn, timeout=max(timeout, 120))
            if res.get("error"):
                attempts.append({"backend": b, "error": res["error"]})
                continue
            rows = res.get("rows") or []
            if not rows:
                attempts.append({"backend": b, "error": "not_found"})
                continue
            doc = bigquery_normalize_row(rows[0], lang=lang)
            doc["estimate"] = res.get("estimate")
            html, url = "", f"bigquery://patents-public-data/{pn}"
        else:
            attempts.append({"backend": b, "error": "unsupported_backend"})
            continue
        attempts.append({"backend": b, "blocked": False})
        return {"ok": True, "backend": b, "doc": doc, "html": html,
                "url": url or doc.get("url", ""), "attempts": attempts}

    blocked = bool(attempts) and all(a.get("blocked") for a in attempts)
    all_cfg = bool(attempts) and all(a.get("error") in CONFIG_ERRORS for a in attempts)
    any_block = any(a.get("blocked") for a in attempts)
    block_or_cfg = bool(attempts) and all(
        a.get("blocked") or a.get("error") in CONFIG_ERRORS for a in attempts)
    codes = {a.get("error") for a in attempts if a.get("error")}
    if blocked:
        reason = "all_backends_blocked"
        remedy = ("该出口被 Google 拦截：配置 TAVILY_API_KEY 走中继取件（免 GCP），"
                  "或开通 GCP 用 BigQuery 官方通道")
    elif all_cfg:
        reason = "no_usable_channel"
        remedy = ("缺少取件凭据：export TAVILY_API_KEY=…（中继，免 GCP）"
                  " 或 gcloud auth application-default login（BigQuery）")
    elif any_block and block_or_cfg:
        # 直连被拦 + 其余通道缺凭据：本质是"当前没有任何可用取件通道"，按被拦处理并给两条出路
        reason, blocked = "all_backends_blocked_or_unconfigured", True
        remedy = ("直连被 Google 拦截、其余通道又缺凭据：二选一即可——"
                  "① export TAVILY_API_KEY=…（中继取件，免 GCP）；"
                  "② 开通 GCP 并 gcloud auth application-default login（BigQuery 官方通道）")
    elif codes == {"doc_not_on_google_patents"}:
        reason = "doc_not_on_google_patents"
        remedy = ("该公开号在 Google Patents 无页面（不是网络问题）；改用 incoPat/CNIPA 原文库，"
                  "或按 PATENTSCOPE docId 查看该件")
    else:
        reason, remedy = "all_backends_failed", None
    return {"ok": False, "blocked": blocked, "reason": reason, "remedy": remedy,
            "attempts": attempts}
