# -*- coding: utf-8 -*-
"""Evidence-grounded AHP/SEM patent review scorer.

The scorer keeps the original 1-9, four-role input compatible, but no longer
silently treats an arithmetic mean as consensus. It adds evidence-weighted
Byzantine-resilient aggregation, disagreement diagnostics, hard gates,
claim/search-version binding, Markov-style round comparison, and cohort-relative
percentiles. A high score means ready for patent-attorney review, never a grant
guarantee or permission to file directly.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple


PROTOCOL_VERSION = "2.0.0"

INDICATORS = {
    "S": {
        "S1": ("技术问题-技术手段-技术效果链完整度", 0.45),
        "S2": ("技术特征占比(vs 纯商业规则/智力活动)", 0.35),
        "S3": ("算法与具体应用场景/内部结构结合度", 0.20),
    },
    "N": {
        "N1": ("最接近现有技术语义相似度反向分", 0.40),
        "N2": ("无单篇X文件的证据置信度", 0.35),
        "N3": ("独权全部必要技术特征组合未命中度", 0.25),
    },
    "I": {
        "I1": ("区别特征的非显而易见性", 0.35),
        "I2": ("特征间因果协同而非并列拼接", 0.30),
        "I3": ("最接近文件与第二文件缺少组合启示", 0.20),
        "I4": ("有益效果的可信增益与可复现性", 0.15),
    },
    "D": {
        "D1": ("关键参数/公式/阈值/状态转换具体化", 0.40),
        "D2": ("正常、边界和异常实施路径完整度", 0.35),
        "D3": ("效果数据与工程事实可验证性", 0.25),
    },
    "Q": {
        "Q1": ("独权保护范围与说明书支持的平衡", 0.40),
        "Q2": ("从权A/B/C退守梯与商业价值保持", 0.35),
        "Q3": ("术语、对象、状态和版本引用一致性", 0.25),
    },
}

ALL_INDICATORS = tuple(
    code for latent_indicators in INDICATORS.values() for code in latent_indicators
)

EXPERT_MATRICES = {
    "examiner": [
        [1, 1 / 3, 1, 2], [3, 1, 3, 4], [1, 1 / 3, 1, 2], [1 / 2, 1 / 4, 1 / 2, 1]
    ],
    "attorney": [
        [1, 1 / 2, 1, 1], [2, 1, 2, 2], [1, 1 / 2, 1, 1], [1, 1 / 2, 1, 1]
    ],
    "invalidator": [
        [1, 1, 2, 3], [1, 1, 2, 3], [1 / 2, 1 / 2, 1, 2], [1 / 3, 1 / 3, 1 / 2, 1]
    ],
    "analyst": [
        [1, 1 / 4, 1 / 2, 1], [4, 1, 3, 4], [2, 1 / 3, 1, 2], [1, 1 / 4, 1 / 2, 1]
    ],
}

RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12}

STATUS_FACTORS = {
    "confirmed": 1.00,
    "supported": 0.90,
    "inferred": 0.72,
    "needs-confirmation": 0.55,
    "unverified": 0.42,
    "contradicted": 0.20,
}

GATE_ALIASES = {
    "subject_matter": ("subject_matter", "gate_1_subject_matter", "subject"),
    "novelty_inventive_evidence": (
        "novelty_inventive_evidence", "gate_2_novelty_inventive", "prior_art_evidence"
    ),
    "disclosure_support": (
        "disclosure_support", "gate_3_sufficient_disclosure", "disclosure", "support"
    ),
    "evidence_integrity": (
        "evidence_integrity", "gate_4_no_fabrication", "no_fabrication"
    ),
    "claim_formality": ("claim_formality", "formal_check", "formality"),
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalise_probability(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1:
        number /= 100.0
    return _clamp(number, 0.0, 1.0)


def ahp_weights(matrix: Sequence[Sequence[float]]) -> Tuple[List[float], float]:
    """Geometric-mean eigenvector approximation plus CR check."""
    n = len(matrix)
    gm = []
    for row in matrix:
        product = 1.0
        for value in row:
            product *= value
        gm.append(product ** (1.0 / n))
    total = sum(gm)
    weights = [value / total for value in gm]
    lambda_max = 0.0
    for i in range(n):
        row_value = sum(matrix[i][j] * weights[j] for j in range(n))
        lambda_max += row_value / weights[i]
    lambda_max /= n
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    cr = ci / RI[n] if RI[n] else 0.0
    return weights, cr


def group_weights() -> Tuple[List[float], float, Dict[str, Dict[str, Any]]]:
    """Aggregate four role-specific AHP matrices using geometric means."""
    names = list(EXPERT_MATRICES)
    n = 4
    aggregate = [[1.0] * n for _ in range(n)]
    per_expert: Dict[str, Dict[str, Any]] = {}
    for name in names:
        weights, cr = ahp_weights(EXPERT_MATRICES[name])
        if cr >= 0.1:
            raise ValueError(f"{name} 判断矩阵 CR={cr:.3f} >= 0.1")
        per_expert[name] = {"weights": weights, "CR": round(cr, 4)}
    for i in range(n):
        for j in range(n):
            product = 1.0
            for name in names:
                product *= EXPERT_MATRICES[name][i][j]
            aggregate[i][j] = product ** (1.0 / len(names))
    weights, cr = ahp_weights(aggregate)
    return weights, cr, per_expert


def _score_entry(raw: Any) -> Dict[str, Any]:
    """Normalise a legacy number or an evidence-rich score entry."""
    numeric_only = not isinstance(raw, Mapping)
    if numeric_only:
        score = raw
        confidence = 0.65
        evidence_quality = 0.55
        status = "unverified"
        evidence_refs: List[str] = []
    else:
        score = raw.get("score", raw.get("value"))
        confidence = raw.get("confidence", 0.70)
        evidence_quality = raw.get("evidence_quality", raw.get("evidence_confidence", 0.60))
        status = str(raw.get("status", "inferred")).strip().lower()
        evidence_refs = [str(x) for x in (raw.get("evidence_refs") or [])]
    try:
        score_number = float(score)
        confidence_number = float(confidence)
        evidence_number = float(evidence_quality)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid score entry: {raw!r}") from exc
    if not math.isfinite(score_number) or not 1 <= score_number <= 9:
        raise ValueError(f"indicator score must be in [1, 9], got {score_number!r}")
    status_factor = STATUS_FACTORS.get(status, STATUS_FACTORS["unverified"])
    reliability = (
        _clamp(confidence_number, 0.0, 1.0)
        * _clamp(evidence_number, 0.0, 1.0)
        * status_factor
    )
    return {
        "score": score_number,
        "status": status,
        "evidence_refs": evidence_refs,
        "reliability": reliability,
        "numeric_only": numeric_only,
    }


def _weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    total = sum(weights)
    if total <= 0:
        return statistics.fmean(values)
    return sum(value * weight for value, weight in zip(values, weights)) / total


def _aggregate_indicator(
    case_scores: Mapping[str, Mapping[str, Any]],
    code: str,
    expert_meta: Mapping[str, Mapping[str, Any]],
    mode: str = "robust",
) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for expert, indicators in case_scores.items():
        if code not in indicators:
            raise ValueError(f"expert {expert!r} is missing indicator {code}")
        entry = _score_entry(indicators[code])
        meta = expert_meta.get(expert, {})
        calibration = _clamp(float(meta.get("calibration", 1.0)), 0.2, 1.5)
        domain_fit = _clamp(float(meta.get("domain_fit", 1.0)), 0.2, 1.5)
        entry["expert"] = expert
        entry["reliability"] *= calibration * domain_fit
        entries.append(entry)

    values = [entry["score"] for entry in entries]
    median = statistics.median(values)
    deviations = [abs(value - median) for value in values]
    mad = statistics.median(deviations)
    value_range = max(values) - min(values)
    threshold = max(2.0, 2.5 * mad)
    byzantine_tolerance = max(0, (len(entries) - 1) // 3)

    suspicious = [
        entry
        for entry in entries
        if abs(entry["score"] - median) > threshold
        and entry["reliability"] < 0.55
        and not entry["numeric_only"]
    ]
    suspicious.sort(
        key=lambda entry: abs(entry["score"] - median) * (1.0 - min(entry["reliability"], 1.0)),
        reverse=True,
    )
    suppressed_experts = {entry["expert"] for entry in suspicious[:byzantine_tolerance]}
    effective_weights = []
    for entry in entries:
        weight = max(entry["reliability"], 0.05)
        if entry["expert"] in suppressed_experts:
            weight *= 0.25
        effective_weights.append(weight)

    evidence_weighted_mean = _weighted_mean(values, effective_weights)
    arithmetic_mean = statistics.fmean(values)
    aggregate = arithmetic_mean if mode == "legacy-mean" else 0.60 * median + 0.40 * evidence_weighted_mean
    high_quality_dissent = [
        entry["expert"]
        for entry in entries
        if abs(entry["score"] - median) > threshold and entry["reliability"] >= 0.75
    ]
    review_required = bool(
        value_range >= 2.5
        or mad >= 1.0
        or high_quality_dissent
        or len(suspicious) > byzantine_tolerance
    )
    return {
        "score": round(aggregate, 3),
        "median": round(median, 3),
        "arithmetic_mean": round(arithmetic_mean, 3),
        "evidence_weighted_mean": round(evidence_weighted_mean, 3),
        "mad": round(mad, 3),
        "range": round(value_range, 3),
        "byzantine_tolerance": byzantine_tolerance,
        "suppressed_experts": sorted(suppressed_experts),
        "high_quality_dissent": sorted(high_quality_dissent),
        "review_required": review_required,
        "legacy_numeric_only": all(entry["numeric_only"] for entry in entries),
        "experts": {
            entry["expert"]: {
                "score": round(entry["score"], 3),
                "reliability": round(entry["reliability"], 3),
                "status": entry["status"],
                "evidence_refs": entry["evidence_refs"],
            }
            for entry in entries
        },
    }


def latent_scores(
    case_scores: Mapping[str, Mapping[str, Any]],
    expert_meta: Mapping[str, Mapping[str, Any]] | None = None,
    mode: str = "robust",
) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]], Dict[str, Dict[str, Any]]]:
    """Aggregate experts per indicator, then apply the measurement model."""
    if not case_scores:
        raise ValueError("scores must contain at least one expert")
    expert_meta = expert_meta or {}
    latent: Dict[str, float] = {}
    detail: Dict[str, Dict[str, float]] = {}
    consensus: Dict[str, Dict[str, Any]] = {}
    for latent_code, indicators in INDICATORS.items():
        latent_value = 0.0
        detail[latent_code] = {}
        for code, (_name, loading) in indicators.items():
            result = _aggregate_indicator(case_scores, code, expert_meta, mode=mode)
            consensus[code] = result
            detail[latent_code][code] = round(result["score"], 2)
            latent_value += loading * result["score"]
        latent[latent_code] = round(latent_value, 2)
    return latent, detail, consensus


def sem_probability(latent: Mapping[str, float], weights: Sequence[float]) -> Tuple[float, float, float]:
    """Map latent scores to a risk baseline, then apply the subject gate."""
    n_score, i_score, d_score, q_score = latent["N"], latent["I"], latent["D"], latent["Q"]
    w_n, w_i, w_d, w_q = weights
    composite = w_n * n_score + w_i * i_score + w_d * d_score + w_q * q_score
    p_core = 1.0 / (1.0 + math.exp(-0.65 * (composite - 5.6)))
    subject_score = latent["S"]
    if subject_score >= 6:
        gate_factor = 1.0
    elif subject_score > 3:
        gate_factor = 0.55 + 0.15 * (subject_score - 3)
    else:
        gate_factor = min(0.15 / max(p_core, 1e-6), 0.35)
    return round(p_core * gate_factor, 3), round(composite, 2), round(p_core, 3)


def grade(probability: float) -> str:
    if probability >= 0.70:
        return "A(内部高位,进入代理师复核)"
    if probability >= 0.55:
        return "B+(较高,小修并补证据后复核)"
    if probability >= 0.40:
        return "B(中等,需实质性强化)"
    if probability >= 0.25:
        return "C(偏低,建议重构独权)"
    return "D(高危,建议重选创造点或保护路径)"


def _normalise_gate_status(value: Any) -> str:
    if isinstance(value, Mapping):
        value = value.get("status")
    text = str(value or "UNKNOWN").strip().upper().replace("_", "-")
    if text in {"PASS", "CONFIRMED", "SUPPORTED"}:
        return "PASS"
    if text in {"FAIL", "FAILED", "BLOCK", "BLOCKED", "REJECT"}:
        return "FAIL"
    if text in {"WARN", "WARNING", "CONDITIONAL", "NEEDS-CONFIRMATION", "PENDING"}:
        return "CONDITIONAL"
    if text == "WAIVED":
        return "WAIVED"
    return "UNKNOWN"


def _gate_diagnostics(review_context: Mapping[str, Any]) -> Dict[str, Any]:
    raw_gates = review_context.get("gates") or {}
    gates: Dict[str, str] = {}
    for canonical, aliases in GATE_ALIASES.items():
        value = next((raw_gates[a] for a in aliases if a in raw_gates), None)
        gates[canonical] = _normalise_gate_status(value)
    return {
        "statuses": gates,
        "blocking": [name for name, status in gates.items() if status == "FAIL"],
        "conditional": [name for name, status in gates.items() if status == "CONDITIONAL"],
        "unknown": [name for name, status in gates.items() if status == "UNKNOWN"],
    }


def _version_binding(review_context: Mapping[str, Any]) -> Dict[str, Any]:
    current_claim_hash = review_context.get("claim_hash") or review_context.get("current_claim_hash")
    reviewed_claim_hash = review_context.get("reviewed_claim_hash") or current_claim_hash
    search_claim_hash = review_context.get("search_claim_hash")
    evidence_hash = review_context.get("evidence_hash") or review_context.get("retrieval_hash")
    stale_reasons = []
    if current_claim_hash and reviewed_claim_hash and current_claim_hash != reviewed_claim_hash:
        stale_reasons.append("reviewed_claim_hash_mismatch")
    if current_claim_hash and search_claim_hash and current_claim_hash != search_claim_hash:
        stale_reasons.append("search_bound_to_different_claim_hash")
    return {
        "current_claim_hash": current_claim_hash,
        "reviewed_claim_hash": reviewed_claim_hash,
        "search_claim_hash": search_claim_hash,
        "evidence_hash": evidence_hash,
        "stale": bool(stale_reasons),
        "stale_reasons": stale_reasons,
    }


def _evidence_confidence(
    consensus: Mapping[str, Mapping[str, Any]],
    review_context: Mapping[str, Any],
    version_binding: Mapping[str, Any],
) -> Tuple[float, List[str]]:
    warnings: List[str] = []
    legacy_only = all(item["legacy_numeric_only"] for item in consensus.values())
    reliabilities = [
        expert["reliability"]
        for item in consensus.values()
        for expert in item["experts"].values()
    ]
    if legacy_only:
        confidence = 0.55
        warnings.append("legacy_numeric_scores_without_evidence_metadata")
    else:
        confidence = _clamp(statistics.fmean(reliabilities) / 0.80, 0.30, 0.95)
    if not review_context:
        warnings.append("missing_review_context")
        confidence = min(confidence, 0.55)
    if not version_binding.get("current_claim_hash"):
        warnings.append("missing_claim_hash")
        confidence = min(confidence, 0.70)
    if not version_binding.get("search_claim_hash"):
        warnings.append("missing_search_claim_hash")
        confidence = min(confidence, 0.70)
    if version_binding.get("stale"):
        warnings.append("stale_review_or_search_binding")
        confidence = min(confidence, 0.20)
    if review_context.get("claim_text_verified") is not True:
        warnings.append("closest_prior_art_claim_text_not_confirmed")
        confidence = min(confidence, 0.65)
    if review_context.get("search_status") in {"failed", "empty", "quota-exhausted", "degraded"}:
        warnings.append("search_failure_is_missing_evidence_not_negative_evidence")
        confidence = min(confidence, 0.45)
    if any(item["review_required"] for item in consensus.values()):
        warnings.append("material_expert_disagreement")
        confidence = min(confidence, 0.68)
    return round(_clamp(confidence, 0.0, 1.0), 3), warnings


def _history_transition(case: Mapping[str, Any], current: Mapping[str, Any]) -> Dict[str, Any]:
    history = case.get("history") or []
    if not history:
        return {"type": "baseline", "controlled_comparison": False, "reason": "no previous review state"}
    previous_state = history[-1].get("state") or history[-1]
    current_binding = current["version_binding"]
    previous_claim_hash = previous_state.get("claim_hash") or previous_state.get("current_claim_hash")
    previous_evidence_hash = previous_state.get("evidence_hash") or previous_state.get("retrieval_hash")
    claim_hash = current_binding.get("current_claim_hash")
    evidence_hash = current_binding.get("evidence_hash")
    claim_known = bool(previous_claim_hash and claim_hash)
    evidence_known = bool(previous_evidence_hash and evidence_hash)
    claim_changed = claim_known and previous_claim_hash != claim_hash
    evidence_changed = evidence_known and previous_evidence_hash != evidence_hash
    if not claim_known or not evidence_known:
        transition_type, controlled = "unknown", False
    elif claim_changed and not evidence_changed:
        transition_type, controlled = "claim_revision_fixed_evidence", True
    elif not claim_changed and evidence_changed:
        transition_type, controlled = "retrieval_or_evidence_shift", False
    elif claim_changed and evidence_changed:
        transition_type, controlled = "mixed_claim_and_evidence_shift", False
    else:
        transition_type, controlled = "same_state_recheck", True
    previous_probability = _normalise_probability(previous_state.get("grant_probability"))
    probability_delta = (
        round(current["grant_probability"] - previous_probability, 3)
        if previous_probability is not None else None
    )
    previous_latent = previous_state.get("latent") or {}
    latent_delta = {
        code: round(current["latent"][code] - float(previous_latent[code]), 2)
        for code in current["latent"] if code in previous_latent
    }
    return {
        "type": transition_type,
        "controlled_comparison": controlled,
        "claim_changed": claim_changed if claim_known else None,
        "evidence_changed": evidence_changed if evidence_known else None,
        "grant_probability_delta": probability_delta,
        "latent_delta": latent_delta,
        "warning": None if controlled else "score movement mixes retrieval/evidence drift with drafting change",
    }


def _action_queue(
    latent: Mapping[str, float],
    consensus: Mapping[str, Mapping[str, Any]],
    review_context: Mapping[str, Any],
    gates: Mapping[str, Any],
    version_binding: Mapping[str, Any],
) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    if version_binding.get("stale"):
        actions.append({"priority": "P0", "dimension": "version-binding", "action": "以当前最终独权重新检索与评审，旧分数不得沿用。"})
    for gate in gates.get("blocking", []):
        actions.append({"priority": "P0", "dimension": gate, "action": "先关闭硬门禁；不得用综合平均分覆盖FAIL。"})
    if latent["S"] < 6:
        actions.append({"priority": "P0", "dimension": "subject-matter", "action": "证明具体计算机内部对象、状态、信号或控制效果；若真实方案不支持则重选客体。"})
    if latent["I"] < 5.5:
        actions.append({"priority": "P1", "dimension": "inventiveness", "action": "完成最接近文件+D2组合启示攻击；把创造点收敛为前一机制改变后一机制输入、状态或允许动作的最小因果闭环。"})
    if latent["N"] < 5.5:
        actions.append({"priority": "P1", "dimension": "novelty-search", "action": "用最终独权执行语义、布尔检索及2—4件高相关文献claim/spec原文核验。"})
    if latent["D"] < 6.5 or review_context.get("engineering_evidence_status") in {"needs-confirmation", "missing"}:
        actions.append({"priority": "P1", "dimension": "disclosure-evidence", "action": "取得申请日前代码、字段表、日志、异常路径和真实对照数据；不能为提分新增未实现机制。"})
    disputed = [code for code, item in consensus.items() if item["review_required"]]
    if disputed:
        actions.append({"priority": "P1", "dimension": "expert-arbitration", "action": "对分歧指标补定向证据并重评，不以简单多数或平均值消除异议：" + ", ".join(disputed)})
    if not review_context.get("application_date") and not review_context.get("priority_date"):
        actions.append({"priority": "P1", "dimension": "date-eligibility", "action": "确认申请日/优先权日后再判定新近文献是否具备现有技术资格。"})
    if latent["Q"] < 6.5:
        actions.append({"priority": "P2", "dimension": "claim-strategy", "action": "形成唯一主叙事及A/B/C退守梯；删除不改变后续状态或允许动作的功能旁支。"})
    return actions[:10]


def _decision(probability: float, confidence: float, gates: Mapping[str, Any], version_binding: Mapping[str, Any]) -> str:
    if version_binding.get("stale"):
        return "STALE_REVIEW_RESEARCH_REQUIRED"
    if gates.get("blocking"):
        return "BLOCKED_BY_HARD_GATE"
    if gates.get("conditional") or gates.get("unknown") or confidence < 0.65:
        return "CONDITIONAL_EVIDENCE_OR_GATE_REVIEW"
    if probability >= 0.55:
        return "READY_FOR_PATENT_ATTORNEY_REVIEW"
    if probability >= 0.40:
        return "REVISE_AND_REVIEW"
    return "REBUILD_INDEPENDENT_CLAIM_OR_RESELECT_POINT"


def score_case(case: Mapping[str, Any], mode: str = "robust") -> Dict[str, Any]:
    weights, group_cr, per_expert = group_weights()
    latent, indicator_detail, consensus = latent_scores(
        case["scores"], case.get("expert_meta") or {}, mode=mode
    )
    probability, composite, probability_before_subject = sem_probability(latent, weights)
    review_context = case.get("review_context") or {}
    gates = _gate_diagnostics(review_context)
    version_binding = _version_binding(review_context)
    confidence, confidence_warnings = _evidence_confidence(consensus, review_context, version_binding)
    uncertainty_margin = 0.05 + (1.0 - confidence) * 0.25
    result: Dict[str, Any] = {
        "protocol_version": PROTOCOL_VERSION,
        "case": case.get("case", ""),
        "title": case.get("title", ""),
        "grant_probability": probability,
        "grade": grade(probability),
        "decision": _decision(probability, confidence, gates, version_binding),
        "score_layers": {
            "structural_readiness": round((0.55 * latent["D"] + 0.45 * latent["Q"]) / 9 * 100, 1),
            "risk_adjusted_patentability": round(probability * 100, 1),
            "evidence_confidence": round(confidence * 100, 1),
            "patentara_structural_score": review_context.get("patentara_score"),
        },
        "uncertainty_interval": {
            "low": round(_clamp(probability - uncertainty_margin, 0.0, 1.0), 3),
            "high": round(_clamp(probability + uncertainty_margin, 0.0, 1.0), 3),
            "reason": "evidence confidence and expert disagreement; not a statistical confidence interval",
        },
        "composite_x": composite,
        "p_before_subject_gate": probability_before_subject,
        "latent": latent,
        "indicators": indicator_detail,
        "consensus": consensus,
        "hard_gates": gates,
        "version_binding": version_binding,
        "confidence_warnings": confidence_warnings,
        "group_weights": {"N": round(weights[0], 3), "I": round(weights[1], 3), "D": round(weights[2], 3), "Q": round(weights[3], 3)},
        "group_CR": round(group_cr, 4),
        "expert_CR": {name: value["CR"] for name, value in per_expert.items()},
    }
    result["round_transition"] = _history_transition(case, result)
    result["action_queue"] = _action_queue(latent, consensus, review_context, gates, version_binding)
    return result


def _percentile(values: Sequence[float], value: float) -> float:
    if not values:
        return 50.0
    less = sum(item < value for item in values)
    equal = sum(item == value for item in values)
    return round(100.0 * (less + 0.5 * equal) / len(values), 1)


def add_relative_positions(results: List[MutableMapping[str, Any]], cohort_id: str | None = None) -> None:
    probabilities = [float(result["grant_probability"]) for result in results]
    structural = [float(result["score_layers"]["structural_readiness"]) for result in results]
    for result in results:
        result["relative_position"] = {
            "cohort_id": cohort_id or "current-input-cohort",
            "cohort_size": len(results),
            "risk_percentile": _percentile(probabilities, float(result["grant_probability"])),
            "structural_percentile": _percentile(structural, float(result["score_layers"]["structural_readiness"])),
            "warning": "percentiles support relative prioritisation; they are not fixed grant standards",
        }


def _load_cases(path: str) -> Tuple[List[Mapping[str, Any]], str | None]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    cohort_id = None
    if isinstance(data, Mapping) and "cases" in data:
        cases = data["cases"]
        cohort = data.get("cohort") or {}
        cohort_id = cohort.get("id") if isinstance(cohort, Mapping) else None
    else:
        cases = data if isinstance(data, list) else [data]
    if not isinstance(cases, list):
        raise ValueError("input must be a case object, a list of cases, or {cases:[...]}")
    return cases, cohort_id


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON input file")
    parser.add_argument("--output", "-o", help="write JSON result to this path")
    parser.add_argument(
        "--aggregation", choices=("robust", "legacy-mean"), default="robust",
        help="robust is the default; legacy-mean reproduces arithmetic aggregation",
    )
    args = parser.parse_args(argv)
    if not args.input:
        weights, group_cr, per_expert = group_weights()
        payload: Any = {
            "protocol_version": PROTOCOL_VERSION,
            "group_weights_NIDQ": [round(weight, 3) for weight in weights],
            "group_CR": round(group_cr, 4),
            "per_expert": per_expert,
            "note": "supply an input JSON to run evidence-grounded review",
        }
    else:
        cases, cohort_id = _load_cases(args.input)
        payload = [score_case(case, mode=args.aggregation) for case in cases]
        add_relative_positions(payload, cohort_id=cohort_id)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
