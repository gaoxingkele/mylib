#!/usr/bin/env python3
"""
evaluator.py —— 自最小要素向上的聚合评估。

评估策略（机器可执行的聚合规则，语义判断由上游 agent 注入 verdict）：
  L0 要素层   : 外部评估 agent 对每个 element × 每篇对比文件给出
                disclosed / partially_disclosed / not_disclosed（ElementVerdict）
  L1 权项层   : 新颖性 = 全要素规则(all-elements rule)：存在单篇对比文件披露
                该权项(含父权项传递要素)全部要素 -> 被anticipate，否则新颖
  L2 创造性   : CNIPA 三步法脚手架 —— 最接近现有技术(披露率最高的对比文件)
                -> 区别特征(未披露要素集合，按类型加权) -> 实际解决的技术问题
                (映射 cognitive.technical_problems) -> 显而易见性留给 agent 填
  L3 案件层   : 独权权重1.0/从权0.4 加权聚合 -> overall score + grade
评分：claim_score = 0.45*novelty + 0.35*feature_strength + 0.20*support
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .model import PatentARA

ELEMENT_TYPE_WEIGHT = {"preamble": 0.3, "step": 1.0, "component": 1.0,
                       "limitation": 0.8, "feature": 0.9, "use_function": 0.7}
GRADE_BANDS = [(0.80, "strong"), (0.60, "moderate"), (0.40, "weak"), (0.0, "high_risk")]


@dataclass
class ElementVerdict:
    element_id: str
    reference_id: str                    # 对应 exploration_graph.citations 的 R id
    status: str                          # disclosed | partially_disclosed | not_disclosed
    confidence: float = 1.0
    rationale: str = ""
    evidence_excerpt: str = ""           # 在对比文件中披露该要素的原文位置


class Evaluator:
    def __init__(self, ara: PatentARA):
        self.ara = ara
        self._elem_by_id = {e.id: e for c in ara.claims for e in c.elements}

    # ---------- public ----------
    def evaluate(self, verdicts: list[ElementVerdict],
                 obviousness_notes: Optional[dict[int, str]] = None) -> dict[str, Any]:
        vmap = {(v.element_id, v.reference_id): v for v in verdicts}
        refs = sorted({v.reference_id for v in verdicts})
        notes = obviousness_notes or {}

        claim_results = [self._eval_claim(c.number, vmap, refs, notes.get(c.number, ""))
                         for c in self.ara.claims]
        overall = self._aggregate(claim_results)
        return {"schema_version": self.ara.schema_version,
                "application_number": self.ara.metadata.application_number,
                "title": self.ara.metadata.title,
                "references": refs,
                "claims": claim_results,
                "overall": overall}

    # ---------- L1/L2 per claim ----------
    def _eval_claim(self, number: int, vmap, refs: list[str],
                    obviousness_note: str) -> dict[str, Any]:
        claim = self.ara.claim(number)
        elems = self.ara.elements(number, transitive=True)   # 从权并入父权要素
        elem_ids = [e.id for e in elems]

        def disclosed(eid: str, ref: str) -> bool:
            v = vmap.get((eid, ref))
            return v is not None and v.status == "disclosed"

        def disclosure_level(eid: str, ref: str) -> float:
            v = vmap.get((eid, ref))
            if v is None:
                return 0.0
            return {"disclosed": 1.0, "partially_disclosed": 0.5}.get(v.status, 0.0)

        anticipated_by = [r for r in refs if elem_ids and all(disclosed(e, r) for e in elem_ids)]
        novel = not anticipated_by

        # 最接近现有技术 = 披露率最高者
        def ratio(r: str) -> float:
            return sum(disclosure_level(e, r) for e in elem_ids) / len(elem_ids) if elem_ids else 0.0
        closest = max(refs, key=ratio) if refs else None
        distinguishing = [e for e in elems if closest and not disclosed(e.id, closest)]

        # 为每条区别特征查找绑定的对比文件
        elem_to_citations = {}
        for cit in self.ara.citations:
            for eid in cit.mapped_element_ids:
                elem_to_citations.setdefault(eid, []).append(cit.id)
        distinguishing_with_bindings = []
        for e in distinguishing:
            distinguishing_with_bindings.append({
                "element_id": e.id,
                "element_type": e.element_type,
                "text": e.text,
                "bound_citations": elem_to_citations.get(e.id, []),
            })

        w_all = sum(ELEMENT_TYPE_WEIGHT.get(e.element_type, 0.9) for e in elems)
        w_dist = sum(
            ELEMENT_TYPE_WEIGHT.get(e.element_type, 0.9) * (1.0 - disclosure_level(e.id, closest))
            for e in distinguishing
        )
        feature_strength = round(w_dist / w_all, 3) if w_all else 0.0

        supports = [self.ara.support_weight(e.id) for e in elems]
        supports = [s for s in supports if s is not None]
        support = round(sum(supports) / len(supports), 3) if supports else 0.5

        score = round(0.45 * (1.0 if novel else 0.0)
                      + 0.35 * feature_strength + 0.20 * support, 3)
        return {
            "claim_id": claim.id, "number": number, "claim_type": claim.claim_type,
            "novel": novel, "anticipated_by": anticipated_by,
            "element_count": len(elem_ids),
            "three_step": {   # CNIPA 创造性三步法（第3步由评估 agent 填 obviousness_note）
                "step1_closest_prior_art": closest,
                "step2_distinguishing_features": distinguishing_with_bindings,
                "step2_technical_problem_actually_solved":
                    [asdict(p) for p in self.ara.technical_problems],
                "step3_obviousness": obviousness_note or None,
            },
            "support_score": support,
            "feature_strength": feature_strength,
            "claim_score": score,
        }

    # ---------- L3 aggregate ----------
    def _aggregate(self, claim_results: list[dict]) -> dict[str, Any]:
        if not claim_results:
            return {"score": 0.0, "grade": "high_risk", "note": "no claims"}
        num, den = 0.0, 0.0
        for r in claim_results:
            w = 1.0 if r["claim_type"] == "independent" else 0.4
            num += w * r["claim_score"]; den += w
        score = round(num / den, 3)
        grade = next(g for thr, g in GRADE_BANDS if score >= thr)
        return {"score": score, "grade": grade,
                "novel_claims": [r["number"] for r in claim_results if r["novel"]],
                "anticipated_claims": [r["number"] for r in claim_results if not r["novel"]],
                "weights": {"independent": 1.0, "dependent": 0.4}}
