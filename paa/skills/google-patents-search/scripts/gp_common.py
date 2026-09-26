# -*- coding: utf-8 -*-
"""Google Patents 免费检索 / 核验的共享工具。

本模块只放「与取数方式无关」的东西：公开号规范化、选择器常量、反爬判定、
审计记录、摘要与时间戳，以及**页面解析**（单件页 HTML 与中继取回的页面 Markdown 两种形态）。
检索/取件的各条路线在 gp_backends.py（HTTP 客户端）里实现，命令行入口在
gp_search.py / gp_fetch.py / gp_verify.py / gp_bigquery.py / gp_pipeline.py。

**本 skill 不使用浏览器自动化**；被反爬拦下时如实上报，并升级到中继（Tavily extract）
或 Google 官方 BigQuery 数据集，见 references/troubleshooting.md。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------- 常量

BASE = "https://patents.google.com"
SEARCH_PATH = "/"
PATENT_PATH = "/patent/"

# 按公开号国家码选语言路径：CN/TW 取中文全文，其余取英文
COUNTRY_LANG = {
    "CN": "zh", "TW": "zh", "HK": "zh", "US": "en", "EP": "en", "WO": "en",
    "JP": "ja", "KR": "ko", "DE": "de", "FR": "fr", "GB": "en", "RU": "ru",
    "IN": "en", "CA": "en", "AU": "en", "BR": "pt", "ES": "es", "IT": "it",
}

# 搜索结果页（结果项 = <search-result-item>，公开号在 <state-modifier data-result="patent/<PN>/<lang>">）
SEL_RESULT_ITEM = "search-result-item"
SEL_RESULT_CONTAINER = "#resultsContainer"
SEL_STATE_MODIFIER = "state-modifier"

# 单件说明书页
SEL_CLAIMS = "#claims"
SEL_CLAIM_ITEM = "#claims .claim, #claims [id^='CLM-']"
SEL_DESC = "#description"
SEL_ABSTRACT = "#abstract, .abstract, [itemprop='abstract']"
SEL_TITLE = "meta[name='DC.title']"
SEL_PUB_META = "meta[name='citation_patent_publication_number']"
SEL_DATE_META = "meta[name='DC.date']"

# Google 反爬页特征（2026-09-26 实测：直连与无头 chromium 均返回 503 + 此页）
ANTI_BOT_MARKERS = (
    "sorry...",
    "your computer or network may be sending automated queries",
    "unusual traffic",
    "to protect our users, we can't process your request",
)

# 公开号：国家码 + 数字 + 可选种类码（B/A1/A/U 等）
PUB_RE = re.compile(r"\b([A-Z]{2})[:\s]?(\d{6,13})[:\s]?([A-Z]\d?)?\b")


# ---------------------------------------------------------------- 输出约定

def ensure_utf8_stdio() -> None:
    """Windows 下把 stdout/stderr 设为 UTF-8：中文 JSON 只在 stdout 出现，
    stderr 只写 ASCII 说明，避免 PowerShell 把中文 stderr 当成 NativeCommandError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):
            pass


def note(msg: str) -> None:
    """stderr 诊断行（保持 ASCII 前缀，正文可含中文）。"""
    print(f"GP_NOTE: {msg}", file=sys.stderr, flush=True)


def hint(msg: str) -> None:
    print(f"GP_HINT: {msg}", file=sys.stderr, flush=True)


def emit(tag: str, payload) -> None:
    """stdout 单行契约：<TAG>: <JSON>。"""
    print(f"{tag}: " + json.dumps(payload, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- 公开号

def normalize_pub(raw: str) -> str:
    """把公开号规范为无分隔的大写形式：US:20230013787:A1 / us20230013787a1 -> US20230013787A1。"""
    if not raw:
        return ""
    s = raw.strip().upper().replace(" ", "")
    m = PUB_RE.search(s)
    if not m:
        return re.sub(r"[^A-Z0-9]", "", s)
    country, digits, kind = m.group(1), m.group(2), m.group(3) or ""
    return f"{country}{digits}{kind}"


def split_pub(pn: str) -> tuple[str, str, str]:
    """拆出 (国家码, 数字, 种类码)。"""
    m = PUB_RE.search(pn.upper())
    if not m:
        return "", "", ""
    return m.group(1), m.group(2), m.group(3) or ""


def lang_for(pn: str, override: str | None = None) -> str:
    if override:
        return override
    country, _, _ = split_pub(pn)
    return COUNTRY_LANG.get(country, "en")


def patent_url(pn: str, lang: str | None = None) -> str:
    return f"{BASE}{PATENT_PATH}{normalize_pub(pn)}/{lang_for(pn, lang)}"


def search_url(query: str, page: int | None = None, lang: str | None = None) -> str:
    from urllib.parse import quote
    q = quote(query, safe="")
    url = f"{BASE}{SEARCH_PATH}?q={q}&oq={q}"
    if page and page > 1:
        url += f"&page={page}"
    if lang:
        url += f"&hl={lang}"
    return url


# ---------------------------------------------------------------- 反爬判定

def looks_blocked(status: int | None, text: str) -> bool:
    """识别 Google 的 'Sorry...' 自动化拦截页。"""
    if status == 503:
        return True
    low = (text or "")[:4000].lower()
    return any(m in low for m in ANTI_BOT_MARKERS)


def blocked_payload(route: str, status: int | None, url: str) -> dict:
    return {
        "ok": False, "blocked": True, "route": route, "status": status, "url": url,
        "reason": "google_anti_bot",
        "remedy": "该出口被 Google 判定为可疑（非本 skill 问题）。二选一："
                  "① 配置 TAVILY_API_KEY 走中继取件/中继检索（免 GCP）；"
                  "② 开通 GCP 并用 BigQuery 官方数据集（见 references/gcp_bigquery_setup.md）。"
                  "本 skill 不回退到浏览器自动化。",
    }


# ---------------------------------------------------------------- 审计

def now_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)


def load_html(path: str) -> str:
    """读入页面 HTML，并兼容「被 JSON 转义后再落盘」的形态。

    实测坑：Playwright MCP 的 browser_evaluate(filename=...) 会把返回的字符串
    按 JSON 序列化写入文件，于是文件里是 ``"<html class=\\"x\\">"`` 这种转义文本。
    直接按 HTML 解析会匹配不到任何属性。这里先尝试 json.loads，成功且结果是字符串
    就用解码后的内容，否则按原始文本处理。
    """
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    s = raw.lstrip()
    if s.startswith('"'):
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, str):
                return decoded
        except Exception:  # noqa: BLE001
            pass
    return raw


def append_audit(audit_path: str | None, record: dict) -> None:
    """检索审计一行一条 JSONL：查询式 / URL / 路线 / 时间 / 命中数 / 是否被拦。"""
    if not audit_path:
        return
    os.makedirs(os.path.dirname(os.path.abspath(audit_path)), exist_ok=True)
    with open(audit_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- HTML 解析

SNIPPET_KEYS = ("Priority", "Filed", "Published", "优先权", "申请日", "公开日")


def parse_result_items(html: str) -> list[dict]:
    """从检索结果页 HTML 解析命中项。

    优先用 data-result（结构化、稳定）取公开号；标题取 h3；其余字段从条目文本行里抽取。
    本函数只做正则/文本解析，不依赖浏览器，便于 --html 离线复算。
    """
    items: list[dict] = []
    for block in re.findall(r"<search-result-item[\s\S]*?</search-result-item>", html):
        pn = ""
        m = re.search(r'data-result="patent/([^/"]+)/([a-z]{2})"', block)
        if m:
            pn = normalize_pub(m.group(1))
        if not pn:
            m2 = re.search(r'href="(/patent/[^/"]+/)', block)
            if m2:
                pn = normalize_pub(m2.group(1).split("/")[2])
        title = ""
        for pat in (r'<h3[^>]*>[\s\S]*?<span[^>]*>([\s\S]*?)</span>',
                    r'<h3[^>]*>([\s\S]*?)</h3>'):
            mt = re.search(pat, block)
            if mt:
                title = _strip_tags(mt.group(1))
                break
        text = _strip_tags(block)
        if not pn:  # 退路：条目文本里出现形如 CN110475396B 的公开号
            mp2 = re.search(r"\b([A-Z]{2}\d{6,13}[A-Z]?\d?)\b", text)
            if mp2:
                pn = normalize_pub(mp2.group(1))
        inventor, assignee = _entities(text, pn)
        pdf = ""
        mp = re.search(r'href="(https://patentimages\.storage\.googleapis\.com/[^"]+\.pdf)"', block)
        if mp:
            pdf = mp.group(1)
        thumb = ""
        mth = re.search(r'<img[^>]+class="thumbnail"[^>]+src="([^"]+)"', block)
        if mth:
            thumb = mth.group(1)
        items.append({
            "pub_number": pn,
            "title": title,
            "assignee": assignee,
            "inventor": inventor,
            "priority_date": _find_date(text, ("Priority", "优先权")),
            "filing_date": _find_date(text, ("Filed", "申请日")),
            "publication_date": _find_date(text, ("Published", "公开日")),
            "snippet": _snippet(text),
            "pdf_url": pdf,
            "thumbnail": thumb,
            "url": patent_url(pn) if pn else "",
            "source": "google_patents",
            "evidence_level": "snippet-degraded",   # 命中项只能算降级证据，须 gp_fetch 取原文后升级
        })
    # 去重（同一公开号只留首条）
    seen, out = set(), []
    for it in items:
        key = it["pub_number"] or it["title"]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _strip_tags(html: str) -> str:
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
          .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'"))
    t = re.sub(r"[ \t\u00a0]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()


DATES_RE = re.compile(r"(Priority|Filed|Granted|Published|优先权|申请日|公开日)", re.I)


def _entities(text: str, pn: str) -> tuple[str, str]:
    """从结果项文本里取发明人与申请人。

    实测版式（按行）：
        <标题> / <国家码若干行> / <公开号> / <发明人> / <申请人> / Priority … • Filed … • Published …
    即公开号之后、日期行之前的相邻两行。取不到就返回空串（宁可为空，不可猜错）。
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    idx = -1
    for i, l in enumerate(lines):
        if pn and pn in l.replace(" ", ""):
            idx = i
            break
    if idx < 0:
        return "", ""
    cand = []
    for l in lines[idx + 1:]:
        if DATES_RE.search(l):
            break
        if re.fullmatch(r"[A-Z]{2}", l):      # 国家码行，跳过
            continue
        cand.append(l)
        if len(cand) == 2:
            break
    inventor = cand[0] if cand else ""
    assignee = cand[1] if len(cand) > 1 else ""
    return inventor, assignee


def _find_line(text: str, keys: tuple[str, ...]) -> str:
    for line in text.splitlines():
        for k in keys:
            if line.strip().lower().startswith(k.lower()):
                return line.strip()[len(k):].strip(" :：") or line.strip()
    return ""


def _find_date(text: str, keys: tuple[str, ...]) -> str:
    for k in keys:
        m = re.search(k + r"[^0-9]{0,12}(\d{4}-\d{2}-\d{2})", text, re.I)
        if m:
            return m.group(1)
    return ""


def _snippet(text: str) -> str:
    """取摘要片段：日期行之后的正文段落（结果页摘要）。"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        if DATES_RE.search(l) and ("•" in l or "-" in l or "：" in l):
            tail = " ".join(lines[i + 1:i + 4]).strip()
            if len(tail) > 30:
                return tail[:600]
    cand = [l for l in lines if len(l) > 60 and not l.startswith(("Priority", "Filed", "Published"))]
    return (cand[0] if cand else "")[:600]


def parse_patent_doc(html: str, pn: str = "") -> dict:
    """从单件说明书页 HTML 抽取结构化全文（离线可复算）。"""
    def meta(name: str) -> str:
        m = re.search(rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]*)"', html)
        return _strip_tags(m.group(1)) if m else ""

    claims = []
    for m in re.finditer(
        r'<(?:div|li|section)[^>]*class="[^"]*\bclaim\b[^"]*"[^>]*>([\s\S]*?)</(?:div|li|section)>',
        html, re.I):
        txt = _strip_tags(m.group(1))
        if len(txt) < 40:
            continue
        num = 0
        mn = re.match(r"(\d+)\s*[.、]", txt)
        if mn:
            num = int(mn.group(1))
        claims.append({"claim_no": num, "text": txt})
    if not claims:  # 退路：直接用 #claims 段整体裁剪
        mc = re.search(r'<section[^>]+id="claims"[\s\S]*?</section>', html, re.I)
        if mc:
            body = _strip_tags(mc.group(0))
            parts = re.split(r"(?m)^\s*(\d{1,3})\s*[.、]\s*", body)
            for i in range(1, len(parts) - 1, 2):
                claims.append({"claim_no": int(parts[i]), "text": parts[i + 1].strip()})

    desc = ""
    md = re.search(r'<section[^>]+id="description"[^>]*>([\s\S]*?)</section>', html, re.I)
    if md:
        desc = _strip_tags(md.group(1))

    abstract = ""
    ma = re.search(r'<section[^>]+id="abstract"[^>]*>([\s\S]*?)</section>', html, re.I)
    if ma:
        abstract = _strip_tags(ma.group(1))
    if not abstract:
        abstract = meta("DC.description") or ""

    def count(sec_id: str) -> int:
        ms = re.search(rf'<section[^>]+id="{sec_id}"[\s\S]*?</section>', html, re.I)
        return len(re.findall(r'<tr[^>]*class="[^"]*tr[^"]*"', ms.group(0))) if ms else 0

    # 多段权利要求：无编号的续行并回前一项（否则会被当成独立权利要求，虚增权项数）
    merged: list[dict] = []
    for c in claims:
        if c["claim_no"] == 0 and merged:
            merged[-1]["text"] = merged[-1]["text"] + "\n" + c["text"]
        else:
            merged.append(dict(c))
    claims = merged

    # 公开日：Google 单件页的 DC.date 实测是**申请日**（与检索结果里的 Filed 一致，
    # 不等于 Published），因此不能当公开日用于"申请日前公开"的资格判断。
    # 静态 HTML 里若没有公开日，就留空，由 gp_fetch.py 用 --pub-date / --from-hits 回填。
    pub = ""
    for pat in (r"Published[^0-9]{0,20}(\d{4}-\d{2}-\d{2})",
                r"公开日[^0-9]{0,20}(\d{4}-\d{2}-\d{2})"):
        mp = re.search(pat, html, re.I)
        if mp:
            pub = mp.group(1)
            break

    return {
        "pub_number": normalize_pub(meta("citation_patent_publication_number").replace(":", "") or pn),
        "title": meta("DC.title"),
        "publication_date": pub,
        "dc_date": meta("DC.date"),
        "dc_date_note": "Google 单件页 DC.date 实测为申请日，不等于公开日",
        "contributors": meta("DC.contributor"),
        "abstract": abstract,
        "claims": claims,
        "claim_count": len(claims),
        "description": desc,
        "description_chars": len(desc),
        "patent_citations": count("patentCitations"),
        "cited_by": count("citedBy"),
        "similar_documents": count("similarDocuments"),
        "source": "google_patents",
        "evidence_level": "original-text" if (claims or desc) else "metadata-only",
    }


# ---------------------------------------------------------------- 中继取件：Google Patents 页面 Markdown
#
# 背景（2026-09-26 实测）：本机出口 IP 直连 patents.google.com 一律 503，Google Patents
# 页面本身又是客户端渲染，普通抽取器只能拿到空的章节标题。改用 Tavily 官方 extract API
# （extract_depth=advanced）时，该服务返回的 Markdown **带完整正文**：摘要、说明书、
# 权利要求逐项，以及引证表（Citations）、相似文献表（Similar Documents）、PDF 直链。
# 因此把这些解析函数放在共享层，供 gp_backends.tavily_extract 与离线复算共用。

MD_HEADING_RE = re.compile(r"^\s{0,3}(#{1,3})\s+(.*\S)\s*$")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MD_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
MD_PUB_IN_URL_RE = re.compile(r"patents\.google\.com/patent/([A-Za-z0-9]+)")
MD_PDF_RE = re.compile(r"\((https://patentimages\.storage\.googleapis\.com/[^)\s]+\.pdf)\)")


def strip_md(text: str) -> str:
    """把 Markdown 片段还原成纯文本：去链接外壳、去引用记号、压空白。"""
    t = MD_LINK_RE.sub(r"\1", text or "")
    t = t.replace("**", "").replace("`", "").replace("*", "").replace("†", "")
    t = re.sub(r"^[\s>#-]+", "", t)
    return re.sub(r"[ \t\u00a0]+", " ", t).strip()


def md_sections(md: str) -> dict:
    """按 ``## 标题`` 切分页面 Markdown：{标题: 正文}。重名标题取正文较长的一份。"""
    out: dict[str, str] = {}
    cur, buf = "", []
    for line in (md or "").splitlines():
        m = MD_HEADING_RE.match(line)
        if m:
            if cur:
                body = "\n".join(buf).strip()
                if len(body) > len(out.get(cur, "")):
                    out[cur] = body
            cur, buf = m.group(2).strip(), []
        else:
            buf.append(line)
    if cur:
        body = "\n".join(buf).strip()
        if len(body) > len(out.get(cur, "")):
            out[cur] = body
    return out


def md_find_section(sections: dict, name: str) -> str:
    """按标题前缀取章节正文（标题常带计数，如 ``Claims (6)``、``Citations (5)``）。"""
    n = (name or "").lower()
    best = ""
    for k, v in (sections or {}).items():
        kl = k.lower()
        if (kl == n or kl.startswith(n + " ") or kl.startswith(n + "(")) and len(v) > len(best):
            best = v
    return best


def md_table_rows(text: str) -> list:
    """解析 Markdown 表格 → 行列表（跳过表头分隔行）。"""
    rows = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c != ""):
            continue
        rows.append([strip_md(c) for c in cells] + ["\u0000"])  # 末尾哨兵，防下标越界
    return rows


def md_pub_in_cell(cell: str) -> str:
    """从表格单元里取公开号（优先 Google 链接，其次裸公开号文本）。"""
    m = MD_PUB_IN_URL_RE.search(cell or "")
    if m:
        return normalize_pub(m.group(1))
    m2 = PUB_RE.search((cell or "").upper())
    return normalize_pub(m2.group(0)) if m2 else ""


def parse_related_table(text: str) -> list:
    """解析相似文献表 / 引证表 → [{pub_number, publication_date, title, assignee, url, source}]。

    实测列序：相似文献 ``Publication | Publication Date | Title``；
    引证表 ``Publication number | Priority date | Publication date | Assignee | Title``。
    因此标题取末列，申请人取倒数第二列（仅当列数≥5）。
    """
    out = []
    for cells in md_table_rows(text):
        pn = md_pub_in_cell(cells[0])
        if not pn:
            continue
        dates = [c for c in cells if MD_DATE_RE.fullmatch(c or "")]
        raw = cells[:-1]
        title = raw[-1] if raw else ""
        assignee = raw[-2] if len(raw) >= 5 else ""
        out.append({
            "pub_number": pn,
            "title": "" if MD_DATE_RE.fullmatch(title or "") else title,
            "assignee": "" if MD_DATE_RE.fullmatch(assignee or "") else assignee,
            "priority_date": dates[0] if dates else "",
            "publication_date": dates[-1] if len(dates) > 1 else (dates[0] if dates else ""),
            "url": patent_url(pn),
            "source": "google_patents_page_table",
            "evidence_level": "snippet-degraded",
        })
    # 同一公开号只留首条
    seen, uniq = set(), []
    for it in out:
        if it["pub_number"] in seen:
            continue
        seen.add(it["pub_number"])
        uniq.append(it)
    return uniq


def parse_claims_md(text: str) -> list:
    """从 Claims 章节 Markdown 切出逐项权利要求。"""
    # 中继 Markdown 里权利要求段之后可能紧跟家族/引证表的裸行（无标题分隔），
    # 实测末项会把 "CN202022751283.7U 2020-11-25 … Expired - Fee Related[CN…](…)" 粘进正文。
    # 故先切掉表行与含 Google 链接的行，避免污染引用片段。
    keep = []
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("|") or "patents.google.com/patent/" in s or s.startswith("#"):
            break
        keep.append(line)
    body = "\n".join(keep).strip()
    if not body:
        return []
    claims = []
    parts = re.split(r"(?m)^\s*(\d{1,3})\s*[.、]\s*", body)
    if len(parts) > 2:
        for i in range(1, len(parts) - 1, 2):
            chunk = strip_md(parts[i + 1])
            if chunk:
                claims.append({"claim_no": int(parts[i]), "text": chunk})
    if not claims:
        chunk = strip_md(body)
        if chunk:
            claims.append({"claim_no": 1, "text": chunk})
    return claims


def parse_google_patents_markdown(md: str, pn: str = "") -> dict:
    """把中继取回的 Google Patents 页面 Markdown 解析成与 parse_patent_doc 同构的 doc。

    与 HTML 路径的差别（都要如实写进报告）：

    * 公开日取自 ``Publications`` 表，是**真实公开日**（HTML 路径的 ``DC.date`` 是申请日）；
    * 附带回引证表 ``cited_patents`` 与相似文献表 ``similar_patents``（可作扩检轴）；
    * 文本经第三方中继转成 Markdown，provenance 记 ``relay``，引用前建议核对 PDF。
    """
    md = md or ""
    sections = md_sections(md)
    lines = [l.strip() for l in md.splitlines()]
    head = lines[0] if lines else ""
    m = re.match(r"^#\s*([A-Z]{2}\d{6,13}[A-Z]?\d?)\s*[-–—]?\s*(.*)$", head)
    if m:
        pn = pn or normalize_pub(m.group(1))
        title = m.group(2)
    else:
        mt = re.match(r"^#\s*(.+)$", head)
        title = mt.group(1) if mt else ""
    # 页面标题形如 "# CN214180783U - 标题 - Google Patents"；去掉站点后缀与链接外壳
    title = re.sub(r"\s*[-–—|]\s*Google Patents\s*$", "", title, flags=re.I).strip()
    title = re.sub(r"\s*\[[^\]]*\]\([^)]*\)\s*$", "", title).strip()
    if not title or re.fullmatch(r"[A-Z]{2}\d{6,13}[A-Z]?\d?", title):
        for l in lines[1:6]:
            if not l or l.startswith("#"):
                continue
            cand = re.split(r"\s{2,}|\[", l)[0].strip()
            if cand and not re.fullmatch(r"[A-Z]{2}\d{6,13}[A-Z]?\d?", cand):
                title = cand
                break

    claims = parse_claims_md(md_find_section(sections, "Claims"))
    desc = strip_md(md_find_section(sections, "Description"))
    abstract = strip_md(md_find_section(sections, "Abstract"))
    if desc.startswith(title) and title:      # 说明书首行常重复标题
        desc = desc[len(title):].lstrip()

    pub, priority, filing = "", "", ""
    for cells in md_table_rows(md_find_section(sections, "Publications")):
        if pn and pn.replace(" ", "") in (cells[0] or "").replace(" ", ""):
            dates = [c for c in cells if MD_DATE_RE.fullmatch(c or "")]
            if dates:
                pub = dates[-1]
    for cells in md_table_rows(md_find_section(sections, "Priority Applications")):
        dates = [c for c in cells if MD_DATE_RE.fullmatch(c or "")]
        if len(dates) >= 2:
            priority, filing = dates[0], dates[1]
            break
    if not pub:   # 退路：正文里紧跟公开号出现的日期
        mp = re.search(re.escape(pn) + r"[^\n]{0,80}?(\d{4}-\d{2}-\d{2})", md)
        pub = mp.group(1) if mp else ""

    pdf = ""
    mpdf = MD_PDF_RE.search(md)
    if mpdf:
        pdf = mpdf.group(1)

    cited = parse_related_table(md_find_section(sections, "Citations"))
    similar = parse_related_table(md_find_section(sections, "Similar Documents"))

    return {
        "pub_number": normalize_pub(pn),
        "title": title,
        "publication_date": pub,
        "publication_date_source": "google_patents_publications_table" if pub else "",
        "priority_date": priority,
        "filing_date": filing,
        "abstract": abstract,
        "claims": claims,
        "claim_count": len(claims),
        "description": desc,
        "description_chars": len(desc),
        "cited_patents": cited,
        "similar_patents": similar,
        "pdf_url": pdf,
        "raw_markdown_chars": len(md),
        "source": "google_patents_via_relay",
        "evidence_level": "original-text" if (claims or desc) else "metadata-only",
    }
