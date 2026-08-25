#!/usr/bin/env python3
"""
claim_decomposer.py —— 权利要求 → 最小技术要素分解（CNIPA 两段式 + USPTO comprising/wherein）。

分解规则：
  CN: 权项号 -> 引用关系(根据/如权利要求N所述) -> 其特征在于 切前序/特征部分
      -> "；"分句 -> 去引导语(包括以下步骤：) -> 要素类型判定(步骤/部件/限定/功能)
  EN: claim number -> dependency(of claim N) -> ";"分句 -> wherein→limitation
最小要素 = 一个不可分割的技术特征（一个步骤 / 一个部件+功能 / 一条进一步限定）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .model import Claim, ClaimElement

# ---------- CN patterns ----------
CN_NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[.、．]\s*")
CN_DEP_RE = re.compile(
    r"(?:根据|如)\s*权利要求\s*([0-9\s、,，或和\-—~至]+?)"
    r"(?:\s*中\s*(?:任一项|任意一项))?\s*所述"
)
CN_RANGE_RE = re.compile(r"(\d+)\s*[-—~至]\s*(\d+)")
CN_CHAR_RE = re.compile(r"其特征在于\s*[:：,，]?")
CN_LEADIN_RE = re.compile(r"^\s*(?:包括|包含|具有|设有|为)\s*(?:以下|下列)?\s*(?:步骤|特征|部件)?\s*[:：,，]?\s*")
CN_STEP_LABEL_RE = re.compile(r"^\s*(?:步骤\s*)?S?\d+\s*[:：,，、]?\s*")
CN_FUNC_RE = re.compile(r"用于\s*([^，,；;。]+)")
CN_REFINE_RE = re.compile(r"所述\s*(步骤\s*S?\d+|[一二三四五六七八九十]+)")

# ---------- EN patterns ----------
EN_NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[.)]\s*")
EN_DEP_RE = re.compile(r"(?:of|according to)\s+claims?\s+([0-9\s,]+(?:or|and)?\s*[0-9]*)", re.I)
EN_LEADIN_RE = re.compile(r"^\s*(?:comprising|including|consisting of|having)\s*[:：]?\s*", re.I)
EN_FUNC_RE = re.compile(r"(?:configured to|operative to|adapted to)\s+([^,;.]+)", re.I)

_CATEGORY_CN = [("方法", "method"), ("系统", "system"), ("存储介质", "medium"), ("介质", "medium"),
                ("计算机程序产品", "computer_program_product"), ("装置", "apparatus"),
                ("设备", "apparatus"), ("终端", "apparatus")]
_COMPONENT_WORDS_CN = ("模块", "单元", "部件", "组件", "机构", "器件", "装置", "电路", "接口", "处理器")
_LIMIT_PREFIX_CN = ("其中", "所述", "优选", "可选")


def _parse_numbers(raw: str) -> list[int]:
    out: list[int] = []
    consumed = raw
    for a, b in CN_RANGE_RE.findall(raw):
        out.extend(range(int(a), int(b) + 1))
        consumed = consumed.replace(f"{a}-{b}", " ").replace(f"{a}至{b}", " ")
    out.extend(int(x) for x in re.findall(r"\d+", consumed))
    return sorted(set(out))


@dataclass
class ClaimDecomposer:
    """把权项文本分解为 Claim + ClaimElement 列表。lang: 'zh' | 'en'"""

    lang: str = "zh"

    # ---------- public ----------
    def decompose_block(self, claims_text: str) -> list[Claim]:
        """分解整段权利要求书文本（多条权项）。"""
        return [c for c in (self.decompose(t) for t in self._split_claims(claims_text)) if c]

    def decompose(self, text: str) -> Claim | None:
        text = " ".join(text.split())
        num_re = CN_NUM_RE if self.lang == "zh" else EN_NUM_RE
        m = num_re.match(text)
        if not m:
            return None
        number = int(m.group(1))
        body = text[m.end():]

        depends_on = self._extract_depends(body)
        preamble, characterizing, two_part = self._split_two_part(body)
        title, category = self._title_category(preamble)

        elements: list[ClaimElement] = []
        if two_part and preamble.strip():
            elements.append(self._mk_element(number, 1, "preamble", preamble.strip(),
                                             characterizing=False))
        for seg in self._segments(characterizing if two_part else body):
            elements.append(self._mk_element(number, len(elements) + 1,
                                             self._classify(seg, category), seg))

        return Claim(id=f"C{number}", number=number,
                     claim_type="dependent" if depends_on else "independent",
                     category=category, text=text, title=title,
                     depends_on=depends_on, two_part_form=two_part, elements=elements)

    # ---------- internals ----------
    def _split_claims(self, block: str) -> list[str]:
        num_re = CN_NUM_RE if self.lang == "zh" else EN_NUM_RE
        chunks, cur = [], []
        for line in block.splitlines():
            if num_re.match(line) and cur:
                chunks.append("\n".join(cur)); cur = [line]
            else:
                cur.append(line)
        if cur:
            chunks.append("\n".join(cur))
        return chunks

    def _extract_depends(self, body: str) -> list[int]:
        dep_re = CN_DEP_RE if self.lang == "zh" else EN_DEP_RE
        m = dep_re.search(body)
        return _parse_numbers(m.group(1)) if m else []

    def _split_two_part(self, body: str) -> tuple[str, str, bool]:
        """返回 (前序/preamble, 特征部分/body, 是否两段式)。"""
        if self.lang == "zh":
            parts = CN_CHAR_RE.split(body, maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1], True
            return "", body, False
        # EN: preamble 到 comprising/including 为止
        m = re.search(r"\b(comprising|including|consisting of)\b", body, re.I)
        if m and m.start() < 120:
            return body[:m.start()], body[m.start():], True
        return "", body, False

    def _title_category(self, preamble: str) -> tuple[str, str]:
        if self.lang == "zh":
            title = re.split(r"[，,：:]", preamble.strip())[0].strip()
            title = CN_DEP_RE.sub("", title).strip("，,。 ")
            for kw, cat in _CATEGORY_CN:
                if kw in title:
                    return title, cat
            return title, "other"
        title = re.split(r"[,;:]", preamble.strip())[0].strip() or "claim"
        low = title.lower()
        for kw, cat in [("method", "method"), ("process", "method"), ("system", "system"),
                        ("medium", "medium"), ("apparatus", "apparatus"), ("device", "apparatus")]:
            if kw in low:
                return title, cat
        return title, "other"

    def _segments(self, body: str) -> list[str]:
        seps = "；;" if self.lang == "zh" else ";"
        raw = re.split(f"[{re.escape(seps)}]", body)
        out = []
        for seg in raw:
            seg = seg.strip().rstrip("。. ").strip()
            if self.lang == "zh":
                seg = CN_LEADIN_RE.sub("", seg)
            else:
                seg = EN_LEADIN_RE.sub("", seg)
                seg = re.sub(r"^(and|wherein)\s+", "", seg, flags=re.I)
            if len(seg) >= 4:
                out.append(seg)
        return out

    def _classify(self, seg: str, category: str) -> str:
        if self.lang == "zh":
            if seg.startswith(_LIMIT_PREFIX_CN):
                return "limitation"
            if category == "method":
                return "step"
            if any(w in seg for w in _COMPONENT_WORDS_CN):
                return "component"
            return "feature"
        low = seg.lower()
        if low.startswith("wherein") or " wherein " in low:
            return "limitation"
        if category == "method" or low.startswith(("receiving", "generating", "determining", "outputting")):
            return "step"
        if any(w in low for w in ("module", "unit", "component", "circuit", "processor", "means for")):
            return "component"
        return "feature"

    def _mk_element(self, claim_no: int, idx: int, etype: str, text: str,
                    characterizing: bool = True) -> ClaimElement:
        func_re = CN_FUNC_RE if self.lang == "zh" else EN_FUNC_RE
        fm = func_re.search(text)
        refine = None
        if self.lang == "zh":
            rm = CN_REFINE_RE.search(text)   # 从权对父权步骤的细化，记录线索
            if rm and etype == "limitation":
                refine = rm.group(1)          # 由上层解析为具体 element_id（可选）
        return ClaimElement(id=f"C{claim_no}.E{idx}", claim_number=claim_no,
                            element_type=etype, text=text,
                            function=fm.group(1).strip() if fm else "",
                            order=idx, refines_element_id=refine,
                            characterizing=characterizing)
