# -*- coding: utf-8 -*-
"""Google Patents 免费检索 / 核验的共享工具。

本模块只放「与取数方式无关」的东西：公开号规范化、选择器常量、反爬判定、
审计记录、摘要与时间戳。检索/取件的三条路线（MCP 浏览器、CDP 挂载、无头）分别在
gp_search.py / gp_fetch.py 里实现，共享这里的选择器与判定。

选择器来源：2026-09-26 在真实 Chrome 会话中实测的 DOM（见 references/troubleshooting.md）。
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
        "remedy": "改用用户真实 Chrome 会话：MCP 浏览器工具（scripts/gp_browser_snippets.js）"
                  "或 gp_search.py --cdp http://127.0.0.1:9222（Chrome 需以 --remote-debugging-port=9222 启动）",
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
