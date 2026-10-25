#!/usr/bin/env python3
"""Evidence-constrained AHP index for patent review.

This module intentionally does not estimate or report a grant probability.
It accepts either raw expert-score cases or prior scorer result records that
already contain latent S/N/I/D/Q values.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import ahp_sem_scorer as core


PROTOCOL_VERSION = "2.3.0-ahp-only"
MODEL_KIND = "AHP_ONLY_INTERNAL_RISK_INDEX"

# ---------------------------------------------------------------------------
# 2.3.0 additions. Every block below is driven by an *optional* input field.
# None of them changes the AHP formula, group weights, the 16 indicators or the
# band thresholds; when the fields are absent the output keeps the pre-2.3.0
# fields and values (only ``protocol_version`` differs, plus ``audit_warnings``
# when a history exists without a frozen anchor).
# ---------------------------------------------------------------------------

FEATURE_MARKS = {
    "●": "full", "◐": "partial", "○": "none",
    "full": "full", "partial": "partial", "none": "none",
}

#: retrieval items that each lift the graded cap for search_status=degraded.
DEGRADED_CAP_BASE = 45.0
DEGRADED_CAP_STEP = 5.0
DEGRADED_CAP_MAX = 65.0
FULLTEXT_FETCHED_THRESHOLD = 10

#: review_context / history fields that switch on the 2.3.0 transition logic.
EXTENDED_STATE_KEYS = (
    "independent_claim_hashes", "text_bundle_hash", "evidence_hash_facts", "argument_hash",
)

BACKGROUND_GATE = "background_prior_art_alignment"
BACKGROUND_GATE_ALIASES = (BACKGROUND_GATE, "background_alignment")

_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _norm(value: Any) -> Optional[str]:
    return core._norm_hash(value)


def _previous_state(case: Mapping[str, Any]) -> Mapping[str, Any]:
    history = case.get("history") or []
    if not history:
        return {}
    last = history[-1]
    return last.get("state") or last


def _dedupe(items: Sequence[str]) -> List[str]:
    seen: Dict[str, None] = {}
    for item in items:
        seen.setdefault(item, None)
    return list(seen)


def _residual_distinction(
    review_context: Mapping[str, Any], previous: Mapping[str, Any]
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Deterministic residual-distinction layer from a feature matrix.

    Not part of the AHP index. A feature counts as *disclosed* only when at
    least one document marks it ``●``; ``◐`` alone is *partial_only*.
    """
    matrix = review_context.get("feature_matrix")
    if not isinstance(matrix, Mapping):
        return None, []
    warnings: List[str] = []
    features = matrix.get("features") or {}
    independent = [str(f) for f in (matrix.get("independent_claim_features") or list(features))]
    docs = matrix.get("docs") or {}
    per_feature: Dict[str, Dict[str, Any]] = {}
    full_by_doc: Dict[str, List[str]] = {str(doc): [] for doc in docs}
    for feature in independent:
        if feature not in features:
            warnings.append(f"feature_matrix_undefined_feature:{feature}")
        full: List[str] = []
        partial: List[str] = []
        for doc, row in docs.items():
            if not isinstance(row, Mapping) or feature not in row:
                continue
            kind = FEATURE_MARKS.get(str(row[feature]).strip())
            if kind is None:
                warnings.append(f"feature_matrix_unknown_mark:{doc}:{feature}")
            elif kind == "full":
                full.append(str(doc))
                full_by_doc[str(doc)].append(feature)
            elif kind == "partial":
                partial.append(str(doc))
        status = "disclosed" if full else ("partial_only" if partial else "undisclosed")
        per_feature[feature] = {
            "status": status,
            "disclosed_by": full,
            "partially_by": partial,
        }
    count = len(independent)
    not_full = [f for f in independent if per_feature[f]["status"] != "disclosed"]
    untouched = [f for f in independent if per_feature[f]["status"] == "undisclosed"]
    best_doc = max(full_by_doc, key=lambda d: len(full_by_doc[d]), default=None)
    if best_doc is not None and not full_by_doc[best_doc]:
        best_doc = None
    if count == 0:
        warnings.append("feature_matrix_empty")
    elif len(not_full) <= 1:
        warnings.append("single_pivot_independent_claim")

    frozen_at = review_context.get("feature_matrix_frozen_at") or matrix.get("frozen_at")
    previous_frozen = previous.get("feature_matrix_frozen_at")
    previous_features = previous.get("independent_claim_features")
    if not frozen_at:
        warnings.append("feature_matrix_not_frozen")
    if previous_frozen and frozen_at and str(previous_frozen) != str(frozen_at):
        split_consistency = "changed"
        warnings.append("feature_matrix_split_changed")
    elif previous_features is not None and set(map(str, previous_features)) != set(independent):
        split_consistency = "changed"
        warnings.append("feature_matrix_split_changed")
    elif previous_frozen or previous_features is not None:
        split_consistency = "same"
    else:
        split_consistency = "no_previous_registration"

    layer = {
        "in_index": False,
        "feature_matrix_frozen_at": frozen_at,
        "split_consistency_vs_previous": split_consistency,
        "independent_claim_features": independent,
        "feature_count": count,
        "document_count": len(docs),
        "per_feature": per_feature,
        "not_fully_disclosed": not_full,
        "not_fully_disclosed_count": len(not_full),
        "untouched_by_any_document": untouched,
        "full_disclosure_coverage": round((count - len(not_full)) / count, 3) if count else None,
        "any_disclosure_coverage": round((count - len(untouched)) / count, 3) if count else None,
        "best_single_document": {
            "document": best_doc,
            "fully_disclosed_features": full_by_doc.get(best_doc, []) if best_doc else [],
        },
        "warnings": list(warnings),
    }
    return layer, warnings


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _retrieval_coverage(
    review_context: Mapping[str, Any], residual: Optional[Mapping[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Optional[float], List[str]]:
    """Retrieval-coverage layer (not in the index) and graded degraded cap."""
    retrieval = review_context.get("retrieval")
    if not isinstance(retrieval, Mapping):
        return None, None, []
    warnings: List[str] = []
    databases = sorted({str(db) for db in (retrieval.get("databases") or [])})
    fetched = _as_int(retrieval.get("fulltext_fetched_n"))
    cap_items = {
        "claim_fulltext_semantic": retrieval.get("claim_fulltext_semantic") is True,
        "fulltext_fetched_ge_10": fetched >= FULLTEXT_FETCHED_THRESHOLD,
        "incopat_done": retrieval.get("incopat_done") is True,
        "two_or_more_databases": len(databases) >= 2,
        "legal_status_verified": retrieval.get("legal_status_verified") is True,
    }
    other_items = {
        "npl_fulltext": retrieval.get("npl_fulltext") is True,
        "conflict_blindspot_closed": retrieval.get("conflict_blindspot") is False,
    }
    cap_met = sum(cap_items.values())
    graded_cap = min(DEGRADED_CAP_MAX, DEGRADED_CAP_BASE + DEGRADED_CAP_STEP * cap_met)
    degraded = review_context.get("search_status") == "degraded"

    independent = list((residual or {}).get("independent_claim_features") or [])
    raw_searched = retrieval.get("features_searched")
    not_searched: List[str] = []
    if raw_searched is None:
        if independent:
            warnings.append("retrieval_features_searched_not_declared")
    else:
        searched = {str(f) for f in raw_searched}
        not_searched = [f for f in independent if f not in searched]
        warnings.extend(f"feature_not_searched:{f}" for f in not_searched)

    items = {**cap_items, **other_items}
    layer = {
        "in_index": False,
        "databases": databases,
        "database_count": len(databases),
        "fulltext_fetched_n": fetched,
        "items": items,
        "items_met": sum(items.values()),
        "items_total": len(items),
        "coverage_ratio": round(sum(items.values()) / len(items), 3),
        "cap_items_met": cap_met,
        "graded_degraded_cap": graded_cap,
        "degraded_cap_applied": graded_cap if degraded else None,
        "features_searched": None if raw_searched is None else [str(f) for f in raw_searched],
        "independent_features_not_searched": not_searched,
        "warnings": list(warnings),
    }
    return layer, (graded_cap / 100.0 if degraded else None), warnings


def _apply_background_gate(
    gates: Mapping[str, Any], review_context: Mapping[str, Any]
) -> Dict[str, Any]:
    """Optional gate: only present in the output when supplied."""
    raw = review_context.get("gates") or {}
    value = next((raw[a] for a in BACKGROUND_GATE_ALIASES if a in raw), None)
    if value is None:
        return dict(gates)
    status = core._normalise_gate_status(value)
    statuses = dict(gates.get("statuses") or {})
    statuses[BACKGROUND_GATE] = status
    return {
        "statuses": statuses,
        "blocking": [n for n, s in statuses.items() if s == "FAIL"],
        "conditional": [n for n, s in statuses.items() if s == "CONDITIONAL"],
        "unknown": [n for n, s in statuses.items() if s == "UNKNOWN"],
    }


def _previous_indicator_scores(previous: Mapping[str, Any]) -> Dict[str, float]:
    flat = previous.get("indicator_scores")
    if isinstance(flat, Mapping):
        return {str(k): float(v) for k, v in flat.items() if isinstance(v, (int, float))}
    nested = previous.get("indicators")
    scores: Dict[str, float] = {}
    if isinstance(nested, Mapping):
        for group in nested.values():
            if isinstance(group, Mapping):
                for code, value in group.items():
                    if isinstance(value, (int, float)):
                        scores[str(code)] = float(value)
    return scores


def _evidence_paths(raw: Any) -> Optional[set]:
    """Accept {path: sha}, ["path"], ["sha  path"] or ["path\\tsha"]."""
    if raw is None:
        return None
    if isinstance(raw, Mapping):
        return {str(k) for k in raw}
    paths = set()
    for item in raw if isinstance(raw, list) else [raw]:
        if isinstance(item, Mapping):
            path = item.get("path")
            if path:
                paths.add(str(path))
            continue
        text = str(item).strip()
        head, _, tail = text.partition(" ")
        if _HEX64.match(head) and tail.strip():
            paths.add(tail.strip())
            continue
        left, sep, right = text.rpartition("\t")
        if sep and _HEX64.match(right.strip()):
            paths.add(left.strip())
            continue
        paths.add(text)
    return paths


def _audit_warnings(
    case: Mapping[str, Any],
    review_context: Mapping[str, Any],
    consensus: Mapping[str, Mapping[str, Any]],
) -> Tuple[List[str], Dict[str, Any]]:
    """Score-inflation guards. Warnings only; scores are never changed."""
    if not case.get("history"):
        return [], {}
    previous = _previous_state(case)
    warnings: List[str] = []
    details: Dict[str, Any] = {}

    anchor = review_context.get("anchor_sha256")
    if not anchor:
        warnings.append("anchor_not_frozen")
    elif previous.get("anchor_sha256") and _norm(previous["anchor_sha256"]) != _norm(anchor):
        warnings.append("anchor_changed_since_previous_round")

    previous_scores = _previous_indicator_scores(previous)
    current_data = review_context.get("data_artifact_hashes")
    previous_data = previous.get("data_artifact_hashes")
    for code in ("I4", "D3"):
        if code not in previous_scores or code not in consensus:
            continue
        if round(float(consensus[code]["score"]), 2) - previous_scores[code] > 0.005:
            unchanged = previous_data is not None and current_data == previous_data
            if not current_data or unchanged:
                warnings.append(f"effect_score_raised_without_new_data:{code}")

    previous_files = _evidence_paths(previous.get("evidence_files"))
    if previous_files is not None:
        current_files = _evidence_paths(review_context.get("evidence_files")) or set()
        removed = sorted(previous_files - current_files)
        if removed:
            details["evidence_removed"] = removed
            if review_context.get("evidence_removal_waiver"):
                details["evidence_removal_waiver"] = review_context["evidence_removal_waiver"]
            else:
                warnings.append("evidence_set_shrunk")
    return warnings, details


def _expert_independence(
    case: Mapping[str, Any], consensus: Mapping[str, Mapping[str, Any]]
) -> Optional[Dict[str, Any]]:
    meta = case.get("expert_meta") or {}
    roles = list((case.get("scores") or {}).keys())
    declared = {role: (meta.get(role) or {}).get("independent") for role in roles}
    if all(value is None for value in declared.values()):
        return None
    all_dependent = bool(roles) and all(value is False for value in declared.values())
    offsets: Dict[str, float] = {}
    abs_offsets: Dict[str, float] = {}
    for role in roles:
        diffs = [
            float(item["experts"][role]["score"]) - float(item["median"])
            for item in consensus.values()
            if role in item["experts"]
        ]
        offsets[role] = round(statistics.fmean(diffs), 3) if diffs else 0.0
        abs_offsets[role] = round(statistics.fmean(abs(d) for d in diffs), 3) if diffs else 0.0
    return {
        "declared_independent": declared,
        "all_roles_dependent": all_dependent,
        "flags": ["disagreement_not_informative"] if all_dependent else [],
        "role_mean_offset_from_median": offsets,
        "role_mean_abs_offset_from_median": abs_offsets,
        "note": "diagnostic only; scores and aggregation are unchanged",
    }


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


def _changed(current: Any, previous: Any) -> Optional[bool]:
    if not current or not previous:
        return None
    return _norm(current) != _norm(previous)


def _extended_transition(
    legacy: Dict[str, Any],
    review_context: Mapping[str, Any],
    previous: Mapping[str, Any],
    claim_known: bool,
    claim_changed: bool,
    combined_evidence_known: bool,
    combined_evidence_changed: bool,
) -> Dict[str, Any]:
    """2.3.0 transition: facts/argument evidence layers, other independent
    claims and the text bundle. Only used when such fields are supplied."""
    facts_changed = _changed(
        review_context.get("evidence_hash_facts"), previous.get("evidence_hash_facts")
    )
    argument_changed = _changed(review_context.get("argument_hash"), previous.get("argument_hash"))
    if facts_changed is not None:
        evidence_known, evidence_changed, evidence_basis = True, facts_changed, "facts_layer"
    else:
        evidence_known = combined_evidence_known
        evidence_changed = combined_evidence_changed
        evidence_basis = "combined_evidence_hash"

    current_claims = {str(k): v for k, v in (review_context.get("independent_claim_hashes") or {}).items()}
    previous_claims = {str(k): v for k, v in (previous.get("independent_claim_hashes") or {}).items()}
    if current_claims and previous_claims:
        other_changed: Optional[List[str]] = sorted(
            key for key in set(current_claims) | set(previous_claims)
            if key != "1" and _norm(current_claims.get(key)) != _norm(previous_claims.get(key))
        )
    else:
        other_changed = None
    bundle_current = review_context.get("text_bundle_hash")
    bundle_previous = previous.get("text_bundle_hash") or previous.get("text_bundle_sha256")
    bundle_changed = _changed(bundle_current, bundle_previous)
    text_changed = bool(other_changed) or bool(bundle_changed)

    reason = None
    if not claim_known or not evidence_known:
        transition_type, controlled = "unknown", False
        reason = "claim or evidence hash missing on one side"
    elif evidence_changed:
        controlled = False
        if claim_changed:
            transition_type = "mixed_claim_and_evidence_shift"
        elif text_changed:
            transition_type = "mixed_text_and_evidence_shift"
        else:
            transition_type = "retrieval_or_evidence_shift"
    elif claim_changed:
        transition_type, controlled = "claim_revision_fixed_evidence", True
    elif text_changed:
        transition_type, controlled = "non_claim1_text_revision_fixed_evidence", True
    elif bundle_changed is None:
        # same_state_recheck requires the text bundle to be verified equal.
        transition_type, controlled = "unknown", False
        reason = "text_bundle_hash missing on one side; same state cannot be confirmed"
    elif argument_changed:
        transition_type, controlled = "argument_revision_fixed_evidence", True
    else:
        transition_type, controlled = "same_state_recheck", True

    applicant_side = []
    if claim_changed:
        applicant_side.append("claim1")
    if other_changed:
        applicant_side.append("other_independent_claims")
    if bundle_changed:
        applicant_side.append("text_bundle")
    if argument_changed:
        applicant_side.append("argument")

    result = dict(legacy)
    result.update({
        "type": transition_type,
        "controlled_comparison": controlled,
        "evidence_changed": evidence_changed if evidence_known else None,
        "evidence_basis": evidence_basis,
        "combined_evidence_hash_changed": combined_evidence_changed if combined_evidence_known else None,
        "facts_changed": facts_changed,
        "argument_changed": argument_changed,
        "other_independent_claims_changed": other_changed,
        "text_bundle_changed": bundle_changed,
        "applicant_side_changes": applicant_side,
        "warning": None if controlled else "score movement mixes retrieval/evidence drift with drafting change",
    })
    if reason:
        result["reason"] = reason
    return result


def _history_transition(
    case: Mapping[str, Any],
    current_binding: Mapping[str, Any],
    current_index: float,
    review_context: Optional[Mapping[str, Any]] = None,
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
    legacy = {
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
    rc = review_context or {}
    if not any(key in rc or key in previous for key in EXTENDED_STATE_KEYS):
        return legacy
    return _extended_transition(
        legacy, rc, previous, claim_known, claim_changed, evidence_known, evidence_changed
    )


def _score_raw_case(case: Mapping[str, Any], aggregation: str, root: Any = None) -> Dict[str, Any]:
    latent, indicators, consensus = core.latent_scores(
        case.get("scores") or {},
        case.get("expert_meta") or {},
        mode=aggregation,
    )
    weights_list, group_cr, expert_cr = core.group_weights()
    weights = dict(zip(("N", "I", "D", "Q"), weights_list))
    review_context = case.get("review_context") or {}
    previous = _previous_state(case)
    gates = _apply_background_gate(core._gate_diagnostics(review_context), review_context)
    version = core._version_binding(review_context, root=root)
    residual, residual_warnings = _residual_distinction(review_context, previous)
    retrieval, graded_cap, retrieval_warnings = _retrieval_coverage(review_context, residual)
    confidence, confidence_warnings = core._evidence_confidence(
        consensus,
        review_context,
        version,
        degraded_cap=graded_cap if graded_cap is not None else 0.45,
    )
    if graded_cap is not None:
        confidence_warnings.append(f"degraded_cap_graded_to_{graded_cap * 100:.0f}")
    evidence_confidence = round(confidence * 100.0, 1)
    audit, audit_details = _audit_warnings(case, review_context, consensus)
    independence = _expert_independence(case, consensus)
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
    if residual is not None:
        result["score_layers"]["residual_distinction"] = residual
    if retrieval is not None:
        result["score_layers"]["retrieval_coverage"] = retrieval
    result["round_transition"] = _history_transition(case, version, index, review_context)
    result["action_queue"] = core._action_queue(
        latent, consensus, review_context, gates, version
    )
    if independence is not None:
        result["expert_independence"] = independence
    all_warnings = _dedupe(
        residual_warnings
        + retrieval_warnings
        + audit
        + (independence["flags"] if independence else [])
    )
    if all_warnings:
        result["audit_warnings"] = all_warnings
    if audit_details:
        result["audit_details"] = audit_details
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
