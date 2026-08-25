#!/usr/bin/env python3
"""
parser.py —— 专利全文 → PatentARA（章节切分 / 附图 / 标号 / 探索图自动构建）。

用法：
    from patent_ara import PatentParser
    ara = PatentParser(lang="zh").parse(full_text)
    ara.save("case.patentara.json")
"""
from __future__ import annotations

import re
from typing import Optional

from .claim_decomposer import ClaimDecomposer
from .model import (Example, Figure, GraphEdge, GraphNode, Metadata, PatentARA,
                    ReferenceNumeral, SpecSection)

CN_HEADINGS = {
    "技术领域": "field", "背景技术": "background", "发明内容": "summary",
    "附图说明": "drawings_brief", "具体实施方式": "embodiments",
    "权利要求书": "claims", "说明书摘要": "abstract", "摘要": "abstract",
}
EN_HEADINGS = {
    "FIELD": "field", "BACKGROUND": "background", "SUMMARY": "summary",
    "BRIEF DESCRIPTION OF THE DRAWINGS": "drawings_brief",
    "DETAILED DESCRIPTION": "embodiments", "CLAIMS": "claims", "ABSTRACT": "abstract",
}
CN_FIG_RE = re.compile(r"图\s*(\d+)\s*[是为：:，,]\s*(.+)")
EN_FIG_RE = re.compile(r"FIG(?:URE)?\.?\s*(\d+)\s*(?:is|shows|illustrates|:)\s*(.+)", re.I)
CN_NUMERAL_RE = re.compile(r"([一-龥A-Za-z]{1,10}?)[（(](\d{1,3})[)）]")
CN_IPC_RE = re.compile(r"[A-H]\d{2}[A-Z]\s*\d+[^\s,，;；]*")
CN_APPL_RE = re.compile(r"CN\s*\d{9,13}\s*[A-Z]?")
US_APPL_RE = re.compile(r"(?:US\s*)?\d{2}/\d{3},?\d{3}")


class PatentParser:
    def __init__(self, lang: str = "zh"):
        self.lang = lang
        self.decomposer = ClaimDecomposer(lang=lang)

    # ---------- main ----------
    def parse(self, text: str, meta_overrides: Optional[dict] = None) -> PatentARA:
        sections = self._split_sections(text)
        ara = PatentARA(metadata=self._metadata(text, sections, meta_overrides))
        ara.spec_sections = [SpecSection(id=f"S{i+1}", kind=k, title=t, text=b)
                             for i, (k, t, b) in enumerate(sections)]

        claims_body = next((b for k, _, b in sections if k == "claims"), "")
        ara.claims = self.decomposer.decompose_block(claims_body) if claims_body else []

        brief = next((b for k, _, b in sections if k == "drawings_brief"), "")
        ara.figures = self._figures(brief)
        ara.reference_numerals = self._numerals(
            next((b for k, _, b in sections if k == "embodiments"), ""))

        self._build_graph(ara)
        return ara

    # ---------- sections ----------
    def _split_sections(self, text: str) -> list[tuple[str, str, str]]:
        """按章节标题切分，返回 [(kind, title, body)]。"""
        headings = CN_HEADINGS if self.lang == "zh" else EN_HEADINGS
        marks: list[tuple[int, str, str]] = []   # (line_idx, kind, title)
        lines = text.splitlines()
        for i, ln in enumerate(lines):
            key = ln.strip().strip("【】[] ").rstrip("：:").strip()
            if self.lang == "en":
                key = re.sub(r"^\d+\.?\s*", "", key).upper()
                hit = next((v for h, v in headings.items() if key.startswith(h)), None)
            else:
                key = re.sub(r"^(?:[一二三四五六七八九十百]+|\d+)\s*[、.．]\s*", "", key)
                key = re.sub(r"^第(?:[一二三四五六七八九十百]+|\d+)[章节部分]\s*", "", key)
                hit = headings.get(key)
            if hit and len(key) < 30:
                marks.append((i, hit, ln.strip()))
        out = []
        for j, (i, kind, title) in enumerate(marks):
            end = marks[j + 1][0] if j + 1 < len(marks) else len(lines)
            out.append((kind, title, "\n".join(lines[i + 1:end]).strip()))
        if not out:   # 无标题：整体作为 other
            out.append(("other", "", text.strip()))
        return out

    # ---------- metadata ----------
    def _metadata(self, text: str, sections, overrides: Optional[dict]) -> Metadata:
        md = Metadata(language=self.lang,
                      jurisdiction="CNIPA" if self.lang == "zh" else "USPTO")
        head = text[:2000]
        if self.lang == "zh":
            m = re.search(r"发明名称\s*[:：]?\s*(.+)", head)
            md.title = m.group(1).strip() if m else (sections[0][2].splitlines() or [""])[0][:60]
            m = CN_APPL_RE.search(head)
            if m:
                md.application_number = m.group(0).replace(" ", "")
            md.ipc_classifications = CN_IPC_RE.findall(head)
        else:
            m = re.search(r"Title\s*[:：]\s*(.+)", head, re.I)
            md.title = m.group(1).strip() if m else (text.splitlines() or [""])[0][:120]
            m = US_APPL_RE.search(head)
            if m:
                md.application_number = m.group(0)
        for k, v in (overrides or {}).items():
            if hasattr(md, k):
                setattr(md, k, v)
        return md

    # ---------- figures & numerals ----------
    def _figures(self, brief: str) -> list[Figure]:
        fig_re = CN_FIG_RE if self.lang == "zh" else EN_FIG_RE
        figs = []
        for ln in brief.splitlines():
            m = fig_re.search(ln)
            if m:
                figs.append(Figure(id=f"F{len(figs)+1}", number=int(m.group(1)),
                                   caption=m.group(2).strip().rstrip("。;；")))
        return figs

    def _numerals(self, embodiments: str) -> list[ReferenceNumeral]:
        if self.lang != "zh":
            return []
        seen: dict[int, str] = {}
        for name, num in CN_NUMERAL_RE.findall(embodiments):
            name = re.sub(r"^[，,。；;：:、\s]*(?:所述|该|此|上述)", "", name).strip()
            n = int(num)
            if 2 <= len(name) <= 10 and n not in seen:
                seen[n] = name
        return [ReferenceNumeral(numeral=n, name=v) for n, v in sorted(seen.items())]

    # ---------- exploration graph ----------
    def _build_graph(self, ara: PatentARA) -> None:
        n, e = ara.nodes, ara.edges
        for s in ara.spec_sections:
            n.append(GraphNode(id=s.id, node_type="section", label=s.title or s.kind))
        for f in ara.figures:
            n.append(GraphNode(id=f.id, node_type="figure", label=f"图{f.number}"))
        for c in ara.claims:
            n.append(GraphNode(id=c.id, node_type="claim", label=c.title))
            for p in c.depends_on:
                e.append(GraphEdge(source=c.id, target=f"C{p}", relation="depends_on"))
            for el in c.elements:
                n.append(GraphNode(id=el.id, node_type="element",
                                   label=el.text[:40]))
                e.append(GraphEdge(source=c.id, target=el.id, relation="has_element"))
                self._support_edges(ara, el)
        # figure --illustrates--> element（经附图标号名称匹配）
        name2num = {r.name: r.numeral for r in ara.reference_numerals}
        for f in ara.figures:
            for c in ara.claims:
                for el in c.elements:
                    if any(nm in el.text for nm in name2num):
                        e.append(GraphEdge(source=f.id, target=el.id,
                                           relation="illustrates", weight=0.5))

    def _support_edges(self, ara: PatentARA, el) -> None:
        """要素→说明书支持边：取要素的关键片段在说明书各节中的覆盖率作为 weight。"""
        def normalize_support_text(text: str) -> str:
            return re.sub(r"所述|一种|用于", "", text)

        frags = [f for f in re.split(r"[，,、；;：:（）()\s]+",
                                     normalize_support_text(el.text)) if len(f) >= 4]
        if not frags:
            return
        best, best_w = None, 0.0
        for s in ara.spec_sections:
            if s.kind in ("claims", "abstract"):
                continue
            normalized_section = normalize_support_text(s.text)
            w = sum(1 for f in frags if f in normalized_section) / len(frags)
            if w > best_w:
                best, best_w = s, w
        if best and best_w > 0:
            ara.edges.append(GraphEdge(source=el.id, target=best.id,
                                       relation="supported_by",
                                       weight=round(best_w, 3)))
            el.support_section_ids = [best.id]
