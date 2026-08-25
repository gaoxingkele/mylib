#!/usr/bin/env python3
"""
scorer_integration.py —— 接入 patent-grant-scorer（AHP-SEM 评分）。

如果项目中有 patent-grant-scorer skill，调用它生成评分数据；
否则提供基于规则的简化评分。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

from .model import PatentARA


class PatentGrantScorer:
    """专利授权评分器。"""

    def __init__(self, scorer_path: Optional[str] = None):
        self.scorer_path = scorer_path
        self._has_external_scorer = scorer_path and os.path.exists(scorer_path)

    def score(self, ara: PatentARA, eval_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成评分数据。

        如果有外部 scorer，调用它；
        否则基于 eval_report 和规则生成简化评分。
        """
        if self._has_external_scorer:
            return self._score_external(ara, eval_report)
        return self._score_internal(ara, eval_report)

    def _score_external(self, ara: PatentARA, eval_report: Dict[str, Any]) -> Dict[str, Any]:
        """调用外部 patent-grant-scorer。"""
        # TODO: 根据实际 patent-grant-scorer 的接口实现
        # 目前先返回内部评分
        return self._score_internal(ara, eval_report)

    def _score_internal(self, ara: PatentARA, eval_report: Dict[str, Any]) -> Dict[str, Any]:
        """基于规则的内部评分。"""
        overall = eval_report.get("overall", {})
        claims = eval_report.get("claims", [])

        # AHP 权重（简化版）
        weights = {
            "novelty": 0.35,
            "inventiveness": 0.35,
            "clarity": 0.15,
            "support": 0.15,
        }

        # 从 eval_report 提取指标
        novel_claims = overall.get("novel_claims", [])
        anticipated_claims = overall.get("anticipated_claims", [])
        total_claims = len(claims)

        novelty_score = len(novel_claims) / total_claims if total_claims else 0.5
        inventiveness_score = overall.get("score", 0.5)

        # 清晰度：基于权利要求长度和要素数量
        clarity_scores = []
        for claim in ara.claims:
            # 要素越多、文本越短，通常越清晰
            elem_count = len(claim.elements)
            text_len = len(claim.text)
            clarity = min(1.0, elem_count / 10.0) * 0.5 + min(1.0, 500 / max(text_len, 1)) * 0.5
            clarity_scores.append(clarity)
        clarity_score = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.5

        # 支持度：基于 supported_by 边
        support_weights = []
        for claim in ara.claims:
            for elem in claim.elements:
                w = ara.support_weight(elem.id)
                if w is not None:
                    support_weights.append(w)
        support_score = sum(support_weights) / len(support_weights) if support_weights else 0.5

        # 综合评分
        final_score = (
            weights["novelty"] * novelty_score +
            weights["inventiveness"] * inventiveness_score +
            weights["clarity"] * clarity_score +
            weights["support"] * support_score
        )

        # SEM 指标（简化版）
        sem_indicators = {
            "I1_technical_contribution": round(inventiveness_score * 10, 2),
            "I2_novelty_degree": round(novelty_score * 10, 2),
            "I3_claim_clarity": round(clarity_score * 10, 2),
            "I4_spec_support": round(support_score * 10, 2),
            "I5_overall_patentability": round(final_score * 10, 2),
        }

        return {
            "ahp_weights": weights,
            "sem_indicators": sem_indicators,
            "scores": {
                "novelty": round(novelty_score, 3),
                "inventiveness": round(inventiveness_score, 3),
                "clarity": round(clarity_score, 3),
                "support": round(support_score, 3),
                "overall": round(final_score, 3),
            },
            "grade": overall.get("grade", "unknown"),
            "recommendation": self._get_recommendation(final_score),
        }

    def _get_recommendation(self, score: float) -> str:
        if score >= 0.8:
            return "strongly_recommend_filing"
        elif score >= 0.6:
            return "recommend_filing"
        elif score >= 0.4:
            return "revise_and_refiling"
        else:
            return "do_not_file"


def integrate_scoring(ara: PatentARA, eval_report: Dict[str, Any],
                      scorer_path: Optional[str] = None) -> Dict[str, Any]:
    """便捷函数：为 PatentARA 生成评分。"""
    scorer = PatentGrantScorer(scorer_path)
    return scorer.score(ara, eval_report)
