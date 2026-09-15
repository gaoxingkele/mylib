#!/usr/bin/env python3
"""Evidence-constrained AHP index for patent review.

This module intentionally does not estimate or report a grant probability.
It accepts either raw expert-score cases or prior scorer result records that
already contain latent S/N/I/D/Q values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import ahp_sem_scorer as core


PROTOCOL_VERSION = "2.1.0-ahp-only"
MODEL_KIND = "AHP_ONLY_INTERNAL_RISK_INDEX"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalise_weights(raw: Mapping[str, Any] | None = None) -> Dict[str, float]:
    if raw and all(code in raw for code in ("N", "I", "D", "Q")):
        values = {code: float(raw[code]) for code in ("N", "I", "D", "Q")}
    else:
        weights, _cr, _experts = core.group_weights()
        values = dict(zip(("N", "I", "D", "Q"), weights))
    total = sum(values.values())
    if total <= 0:
        raise ValueError("AHP weights must have a positive sum")
    return {code: value / total for code, value in values.items()}


def ahp_index(latent: Mapping[str, Any], weights: Mapping[str, float]) -> tuple[float, float]:
    """Return the 1-9 weighted composite and an affine 0-100 index.

    The affine transform maps the rubric endpoints 1 -> 0 and 9 -> 100. It is
    an internal readiness/risk index, not an observed grant frequency.
    """
    composite = sum(float(latent[code]) * weights[code] for code in ("N", "I", "D", "Q"))
    composite = _clamp(composite, 1.0, 9.0)
    index = (composite - 1.0) / 8.0 * 100.0
    return round(composite, 3), round(index, 1)


def band(index: float) -> str:
    if index >= 75:
        return "A_INTERNAL_STRONG"
    if index >= 65:
        return "B_PLUS_INTERNAL_RELATIVELY_STRONG"
    if index >= 55:
        return "B_INTERNAL_MEDIUM"
    if index >= 45:
        return "C_INTERNAL_WEAK"
    return "D_INTERNAL_HIGH_RISK"


def _decision(
    index: float,
    evidence_confidence: float | None,
    gates: Mapping[str, Any],
    version: Mapping[str, Any],
) -> str:
    if version.get("stale"):
        return "STALE_REVIEW_RESEARCH_REQUIRED"
    if gates.get("blocking"):
        return "BLOCKED_BY_HARD_GATE"
    if gates.get("conditional") or gates.get("unknown"):
        return "CONDITIONAL_EVIDENCE_OR_GATE_REVIEW"
    if evidence_confidence is not None and evidence_confidence < 65:
        return "CONDITIONAL_EVIDENCE_OR_GATE_REVIEW"
    if index >= 65:
        return "READY_FOR_PATENT_ATTORNEY_REVIEW"
    if index >= 50:
        return "REVISE_AND_REVIEW"
    return "REBUILD_INDEPENDENT_CLAIM_OR_RESELECT_POINT"


def _history_transition(
    case: Mapping[str, Any], current_binding: Mapping[str, Any], current_index: float
) -> Dict[str, Any]:
    """Compare state identity without converting an old SEM score into AHP."""
    history = case.get("history") or []
    if not history:
        return {
            "type": "baseline",
            "controlled_comparison": False,
            "ahp_index_delta": None,
            "reason": "no previous review state",
        }
    previous = history[-1].get("state") or history[-1]
    previous_claim_hash = previous.get("claim_hash") or previous.get("current_claim_hash")
    previous_evidence_hash = previous.get("evidence_hash") or previous.get("retrieval_hash")
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
    previous_index = previous.get("ahp_index")
    index_delta = (
        round(current_index - float(previous_index), 1)
        if previous_index is not None
        else None
    )
    return {
        "type": transition_type,
        "controlled_comparison": controlled,
        "claim_changed": claim_changed if claim_known else None,
        "evidence_changed": evidence_changed if evidence_known else None,
        "ahp_index_delta": index_delta,
        "legacy_sem_score_ignored": previous_index is None
        and previous.get("grant_probability") is not None,
        "warning": None
        if controlled
        else "score movement mixes retrieval/evidence drift with drafting change",
    }


def _score_raw_case(case: Mapping[str, Any], aggregation: str, root: Any = None) -> Dict[str, Any]:
    latent, indicators, consensus = core.latent_scores(
        case.get("scores") or {},
        case.get("expert_meta") or {},
        mode=aggregation,
    )
    weights_list, group_cr, expert_cr = core.group_weights()
    weights = dict(zip(("N", "I", "D", "Q"), weights_list))
    review_context = case.get("review_context") or {}
    gates = core._gate_diagnostics(review_context)
    version = core._version_binding(review_context, root=root)
    confidence, confidence_warnings = core._evidence_confidence(
        consensus, review_context, version
    )
    evidence_confidence = round(confidence * 100.0, 1)
    composite, index = ahp_index(latent, weights)
    result = {
        "protocol_version": PROTOCOL_VERSION,
        "model_kind": MODEL_KIND,
        "case": case.get("case", ""),
        "title": case.get("title", ""),
        "ahp_index": index,
        "ahp_band": band(index),
        "weighted_composite_1_to_9": composite,
        "interpretation": "internal ordinal risk/readiness index; not grant probability",
        "latent": latent,
        "indicators": indicators,
        "consensus": consensus,
        "group_weights": {code: round(value, 4) for code, value in weights.items()},
        "group_CR": round(group_cr, 4),
        "expert_CR": expert_cr,
        "hard_gates": gates,
        "version_binding": version,
        "score_layers": {
            "ahp_substantive_index": index,
            "structural_readiness": round(
                ((0.55 * float(latent["D"]) + 0.45 * float(latent["Q"]) - 1.0) / 8.0) * 100.0,
                1,
            ),
            "evidence_confidence": evidence_confidence,
            "patentara_structural_score": review_context.get("patentara_score"),
        },
        "confidence_warnings": confidence_warnings,
        "decision": _decision(index, evidence_confidence, gates, version),
    }
    result["round_transition"] = _history_transition(case, version, index)
    result["action_queue"] = core._action_queue(
        latent, consensus, review_context, gates, version
    )
    return result


def _score_existing_result(record: Mapping[str, Any]) -> Dict[str, Any]:
    latent = record.get("latent") or {}
    missing = [code for code in ("S", "N", "I", "D", "Q") if code not in latent]
    if missing:
        raise ValueError(f"existing result missing latent scores: {missing}")
    weights = normalise_weights(record.get("group_weights"))
    composite, index = ahp_index(latent, weights)
    gates = record.get("hard_gates") or {
        "statuses": {},
        "blocking": [],
        "conditional": [],
        "unknown": ["legacy_gate_metadata_missing"],
    }
    version = record.get("version_binding") or {
        "stale": False,
        "stale_reasons": [],
        "metadata_status": "legacy_version_metadata_missing",
    }
    evidence_confidence = (record.get("score_layers") or {}).get("evidence_confidence")
    warnings = list(record.get("confidence_warnings") or [])
    if evidence_confidence is None:
        warnings.append("legacy_evidence_confidence_missing")
    result = {
        "protocol_version": PROTOCOL_VERSION,
        "model_kind": MODEL_KIND,
        "case": record.get("case", ""),
        "title": record.get("title", ""),
        "ahp_index": index,
        "ahp_band": band(index),
        "weighted_composite_1_to_9": composite,
        "interpretation": "internal ordinal risk/readiness index; not grant probability",
        "latent": latent,
        "group_weights": {code: round(value, 4) for code, value in weights.items()},
        "group_CR": record.get("group_CR"),
        "hard_gates": gates,
        "version_binding": version,
        "score_layers": {
            "ahp_substantive_index": index,
            "structural_readiness": round(
                ((0.55 * float(latent["D"]) + 0.45 * float(latent["Q"]) - 1.0) / 8.0) * 100.0,
                1,
            ),
            "evidence_confidence": evidence_confidence,
            "patentara_structural_score": (record.get("score_layers") or {}).get(
                "patentara_structural_score"
            ),
        },
        "confidence_warnings": sorted(set(warnings)),
        "decision": _decision(index, evidence_confidence, gates, version),
        "legacy_sem_reference": {
            "value": record.get("grant_probability"),
            "used_in_ahp_index": False,
        },
    }
    result["round_transition"] = {
        "type": "legacy-result-conversion",
        "controlled_comparison": False,
        "ahp_index_delta": None,
        "reason": "raw cross-round history unavailable in converted result",
    }
    result["action_queue"] = record.get("action_queue") or core._action_queue(
        latent, record.get("consensus") or {}, {}, gates, version
    )
    return result


def score_case(case: Mapping[str, Any], aggregation: str = "robust", root: Any = None) -> Dict[str, Any]:
    if case.get("scores"):
        return _score_raw_case(case, aggregation, root=root)
    return _score_existing_result(case)


def add_relative_positions(results: Sequence[Dict[str, Any]], cohort_id: str = "") -> None:
    ordered = sorted(float(item["ahp_index"]) for item in results)
    count = len(ordered)
    for item in results:
        value = float(item["ahp_index"])
        below = sum(score < value for score in ordered)
        equal = sum(score == value for score in ordered)
        percentile = (below + 0.5 * equal) / count * 100.0 if count else 0.0
        item["relative_position"] = {
            "cohort_id": cohort_id,
            "ahp_percentile": round(percentile, 1),
            "cohort_size": count,
        }


def load_cases(path: Path) -> tuple[list[Mapping[str, Any]], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload, path.stem
    if isinstance(payload, Mapping) and isinstance(payload.get("cases"), list):
        cohort = payload.get("cohort") or {}
        return payload["cases"], str(cohort.get("id") or path.stem)
    if isinstance(payload, Mapping):
        return [payload], path.stem
    raise ValueError("input must be a case, case list, or {cases: [...]} object")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--aggregation", choices=("robust", "legacy-mean"), default="robust")
    parser.add_argument(
        "--root", default=None,
        help=(
            "base directory for resolving review_context.search_path; the scorer "
            "recomputes the search-input hash from that evidence file so binding "
            "equality cannot be asserted without evidence (default: cwd)"
        ),
    )
    args = parser.parse_args(argv)
    cases, cohort_id = load_cases(args.input)
    results = [score_case(case, aggregation=args.aggregation, root=args.root) for case in cases]
    add_relative_positions(results, cohort_id=cohort_id)
    text = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
