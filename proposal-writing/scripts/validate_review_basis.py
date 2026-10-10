"""Validate proposal review source-basis records and competency profiles.

The checker verifies local JSON structure, source applicability declarations,
and traceability. It does not read cited source text or judge review content.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SOURCE_KINDS = {
    "call",
    "template",
    "enterprise_rule",
    "standard",
    "regulation",
    "method",
    "guide_case",
    "historical_case",
    "standard_plan",
}
SOURCE_STATUS = {"current", "historical", "superseded", "draft", "unknown"}
READ_LEVELS = {"full_text", "excerpt", "metadata"}
STAGES = {"application", "midterm", "acceptance", "follow_up"}
CLAIM_TYPES = {"requirement", "recommendation", "inference", "catalog_fact"}
APPLICABILITY = {"applicable", "conditional", "not_applicable", "unknown"}
ADOPTER_KINDS = {"call", "template", "enterprise_rule"}
FORBIDDEN_HARD_KINDS = {"standard_plan", "guide_case", "historical_case", "method"}
STANDARD_TYPES = {"mandatory", "recommended", "guidance"}
RECOMMENDED_STANDARD_CODE_RE = re.compile(r"\b(?:[A-Z]{1,8}\s*/\s*[TZ]|T\s*/)\b", re.IGNORECASE)
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|PLACEHOLDER|FIXME|待补|待定|占位)\b", re.IGNORECASE)


def _read_json(path: Path) -> Any:
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError("input contains NUL bytes")
    return json.loads(data.decode("utf-8-sig"))


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_date(value: Any) -> date | None:
    if not _is_text(value):
        return None
    if not ISO_DATE_RE.fullmatch(str(value)):
        return None
    try:
        parsed = date.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed


def _valid_enum(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _has_placeholder(value: Any) -> bool:
    return isinstance(value, str) and bool(PLACEHOLDER_RE.search(value))


def _standard_code_text(source: dict[str, Any]) -> str:
    raw = " ".join(str(source.get(key) or "") for key in ("code", "title"))
    return unicodedata.normalize("NFKC", raw).upper()


def _is_public_http_url(value: Any) -> bool:
    if not _is_text(value):
        return False
    parsed = urlparse(str(value))
    if parsed.scheme.lower() not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    if not host or host == "localhost" or host.startswith("127.") or host in {"::1", "0.0.0.0"}:
        return False
    return True


def _ids(items: list[Any], label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items, start=1):
        prefix = f"{label}-{index}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        item_id = item.get("id")
        if not _is_text(item_id):
            errors.append(f"{prefix}: missing required text field id")
            continue
        item_id = str(item_id)
        if item_id in seen:
            errors.append(f"{item_id}: duplicate id")
        seen[item_id] = item
    return seen


def _require_text(obj: dict[str, Any], keys: tuple[str, ...], prefix: str, errors: list[str]) -> None:
    for key in keys:
        if not _is_text(obj.get(key)):
            errors.append(f"{prefix}: missing required text field {key}")


def _validate_source_shape(source: dict[str, Any], prefix: str, errors: list[str]) -> None:
    _require_text(source, ("id", "title", "kind", "status", "read_level", "funder"), prefix, errors)
    if not _valid_enum(source.get("kind"), SOURCE_KINDS):
        errors.append(f"{prefix}: invalid kind {source.get('kind')!r}")
    if not _valid_enum(source.get("status"), SOURCE_STATUS):
        errors.append(f"{prefix}: invalid status {source.get('status')!r}")
    if not _valid_enum(source.get("read_level"), READ_LEVELS):
        errors.append(f"{prefix}: invalid read_level {source.get('read_level')!r}")
    if source.get("call_id") is not None and not _is_text(source.get("call_id")):
        errors.append(f"{prefix}: invalid call_id")
    if source.get("standard_type") is not None and not _valid_enum(source.get("standard_type"), STANDARD_TYPES):
        errors.append(f"{prefix}: invalid standard_type {source.get('standard_type')!r}")
    standard_code = _standard_code_text(source)
    if source.get("standard_type") == "mandatory" and RECOMMENDED_STANDARD_CODE_RE.search(standard_code):
        errors.append(f"{prefix}: standard_type mandatory conflicts with recommended or guidance standard code")
    for key in ("stages", "project_types"):
        values = source.get(key)
        if not isinstance(values, list) or not values or any(not _is_text(item) for item in values):
            errors.append(f"{prefix}: empty {key}")
        elif key == "stages":
            bad_stages = [item for item in values if item not in STAGES and item != "all"]
            if bad_stages:
                errors.append(f"{prefix}: invalid stages {bad_stages!r}")
    if not (_is_text(source.get("url")) or _is_text(source.get("source_path"))):
        errors.append(f"{prefix}: source requires url or source_path")
    if source.get("effective_date") is not None and _parse_date(source.get("effective_date")) is None:
        errors.append(f"{prefix}: invalid effective_date")


def _matches_scope(source: dict[str, Any], context: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not isinstance(context, dict):
        context = {}
    stages = source.get("stages") if isinstance(source.get("stages"), list) else []
    project_types = source.get("project_types") if isinstance(source.get("project_types"), list) else []
    if "all" not in stages and context.get("stage") not in stages:
        problems.append("stage")
    if "all" not in project_types and context.get("project_type") not in project_types:
        problems.append("project_type")
    funder = source.get("funder")
    if funder != "general" and funder != context.get("funder"):
        problems.append("funder")
    call_id = source.get("call_id")
    if _is_text(call_id) and call_id != "all" and call_id != context.get("call_id"):
        problems.append("call_id")
    return not problems, problems


def _is_effective(source: dict[str, Any], as_of: date | None) -> bool:
    effective = source.get("effective_date")
    if effective is None or as_of is None:
        return True
    parsed = _parse_date(effective)
    return parsed is not None and parsed <= as_of


def _adoption_map(
    record: dict[str, Any],
    source_ids: list[str],
    sources: dict[str, dict[str, Any]],
    errors: list[str],
    prefix: str,
) -> dict[str, dict[str, Any]]:
    adoptions = record.get("adoptions", [])
    if adoptions in (None, ""):
        return {}
    if not isinstance(adoptions, list):
        errors.append(f"{prefix}: adoptions must be a list")
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    cited = set(source_ids)
    seen_targets: set[str] = set()
    for index, adoption in enumerate(adoptions, start=1):
        aprefix = f"{prefix}: adoption-{index}"
        if not isinstance(adoption, dict):
            errors.append(f"{aprefix}: must be an object")
            continue
        entry_ok = True
        source_id = adoption.get("source_id")
        adopted_by = adoption.get("adopted_by")
        if not _is_text(source_id) or not _is_text(adopted_by):
            errors.append(f"{aprefix}: missing source_id or adopted_by")
            continue
        source_id = str(source_id)
        adopted_by = str(adopted_by)
        if source_id in seen_targets:
            errors.append(f"{aprefix}: duplicate adoption target {source_id}")
            entry_ok = False
        seen_targets.add(source_id)
        if source_id not in cited:
            errors.append(f"{aprefix}: adoption target {source_id} is not cited")
            entry_ok = False
        if source_id not in sources:
            errors.append(f"{aprefix}: adoption target {source_id} is unknown")
            entry_ok = False
        if adopted_by not in sources:
            errors.append(f"{aprefix}: unknown adopter source {adopted_by}")
            entry_ok = False
        if source_id == adopted_by:
            errors.append(f"{aprefix}: self-reference is not allowed")
            entry_ok = False
        if not _is_text(adoption.get("locus")) or not _is_text(adoption.get("explanation")):
            errors.append(f"{aprefix}: locus and explanation are required")
            entry_ok = False
        if entry_ok:
            mapped[source_id] = adoption
    return mapped


def _valid_adoption(
    source_id: str,
    adoption: dict[str, Any] | None,
    sources: dict[str, dict[str, Any]],
    context: dict[str, Any],
    as_of: date | None,
    prefix: str,
    errors: list[str],
    warnings: list[str],
) -> bool:
    if not adoption:
        return False
    adopted_by = str(adoption.get("adopted_by"))
    if source_id == adopted_by:
        return False
    adopter = sources.get(adopted_by)
    if adopter is None:
        errors.append(f"{prefix}: adoption for {source_id} uses unknown adopter source {adopted_by}")
        return False
    if not _valid_enum(adopter.get("kind"), ADOPTER_KINDS):
        errors.append(f"{prefix}: adoption adopter {adopted_by} must be call/template/enterprise_rule")
        return False
    if adopter.get("status") != "current" or adopter.get("read_level") == "metadata":
        errors.append(f"{prefix}: adoption adopter {adopted_by} must be current full_text or excerpt")
        return False
    if not _is_effective(adopter, as_of):
        errors.append(f"{prefix}: adoption adopter {adopted_by} is not yet effective")
        return False
    matches, problems = _matches_scope(adopter, context)
    if not matches:
        errors.append(f"{prefix}: adopter source does not match context ({', '.join(problems)})")
        return False
    if _valid_enum(adopter.get("kind"), {"call", "template"}) and adopter.get("call_id") != context.get("call_id"):
        errors.append(f"{prefix}: adoption adopter {adopted_by} must explicitly match current call_id")
        return False
    warnings.append(f"{prefix}: adoption declaration for {source_id} does not prove content truth")
    return True


def _validate_context(context: Any, errors: list[str]) -> date | None:
    if not isinstance(context, dict):
        errors.append("context: must be an object")
        return None
    _require_text(context, ("funder", "call_id", "stage", "project_type", "as_of"), "context", errors)
    if not _valid_enum(context.get("stage"), STAGES):
        errors.append(f"context: invalid stage {context.get('stage')!r}")
    as_of = _parse_date(context.get("as_of"))
    if as_of is None:
        errors.append("context: invalid context as_of")
    return as_of


def validate_basis(path: Path) -> tuple[list[str], list[str]]:
    payload = _read_json(path)
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return ["payload: must be an object"], warnings
    context = payload.get("context")
    sources_raw = payload.get("sources")
    records_raw = payload.get("records")
    as_of = _validate_context(context, errors)
    context_obj = context if isinstance(context, dict) else {}
    if not isinstance(sources_raw, list) or not sources_raw:
        errors.append("sources: must contain at least one source")
        sources_raw = []
    if not isinstance(records_raw, list) or not records_raw:
        errors.append("records: must contain at least one record")
        records_raw = []
    sources = _ids(sources_raw, "source", errors)
    for source_id, source in sources.items():
        _validate_source_shape(source, source_id, errors)
    seen_records: set[str] = set()
    for index, record in enumerate(records_raw, start=1):
        prefix = f"row-{index}"
        if not isinstance(record, dict):
            errors.append(f"{prefix}: record must be an object")
            continue
        record_id = str(record.get("id") or prefix)
        prefix = record_id
        if record_id in seen_records:
            errors.append(f"{prefix}: duplicate id")
        seen_records.add(record_id)
        _require_text(record, ("id", "project_id", "location", "quote", "basis", "suggestion"), prefix, errors)
        claim_type = record.get("claim_type")
        applicability = record.get("applicability")
        if not _valid_enum(claim_type, CLAIM_TYPES):
            errors.append(f"{prefix}: invalid claim_type {claim_type!r}")
        if not _valid_enum(applicability, APPLICABILITY):
            errors.append(f"{prefix}: invalid applicability {applicability!r}")
        source_ids = record.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids or any(not _is_text(item) for item in source_ids):
            errors.append(f"{prefix}: source_ids must be a list of non-empty strings")
            source_ids = []
        source_loci = record.get("source_loci")
        if not isinstance(source_loci, dict):
            source_loci = {}
        if claim_type != "catalog_fact":
            if not source_loci:
                errors.append(f"{prefix}: source_loci is required for cited non-catalog_fact claims")
            for source_id in source_ids:
                if not _is_text(source_loci.get(source_id)):
                    errors.append(f"{prefix}: source_loci missing locus for {source_id}")
        adoptions = _adoption_map(record, [str(item) for item in source_ids], sources, errors, prefix)
        if claim_type == "requirement" and applicability != "applicable":
            errors.append(f"{prefix}: hard requirement applicability must be applicable")
        for source_id in source_ids:
            source = sources.get(str(source_id))
            if source is None:
                errors.append(f"{prefix}: unknown source {source_id}")
                continue
            if _valid_enum(claim_type, {"recommendation", "inference"}):
                warnings.append(f"{prefix}: soft reference {source_id} is not validated as hard requirement source text")
                continue
            if claim_type != "requirement":
                continue
            adopted = _valid_adoption(str(source_id), adoptions.get(str(source_id)), sources, context_obj, as_of, prefix, errors, warnings)
            if source.get("read_level") == "metadata":
                errors.append(f"{prefix}: hard requirement source {source_id} cannot use metadata")
            if source.get("status") != "current":
                errors.append(f"{prefix}: hard requirement source {source_id} must be current")
            if not _is_effective(source, as_of):
                errors.append(f"{prefix}: hard requirement source {source_id} is not yet effective")
            kind = source.get("kind")
            if _valid_enum(kind, FORBIDDEN_HARD_KINDS):
                errors.append(f"{prefix}: hard requirement source {source_id} cannot use {kind}")
            standard_type = source.get("standard_type") or "recommended"
            if kind == "standard" and standard_type != "mandatory" and not adopted:
                errors.append(f"{prefix}: standard source {source_id} requires explicit current adoption basis")
            if _valid_enum(kind, {"call", "template"}) and source.get("call_id") != context_obj.get("call_id"):
                errors.append(f"{prefix}: hard requirement {kind} source {source_id} must explicitly match current call_id")
            matches, problems = _matches_scope(source, context_obj)
            if not matches and not adopted:
                errors.append(f"{prefix}: source {source_id} does not match context ({', '.join(problems)})")
    return errors, warnings


def _validate_profile_source(source: dict[str, Any], prefix: str, errors: list[str], warnings: list[str]) -> None:
    _validate_source_shape(source, prefix, errors)
    if source.get("source_path") is not None or not _is_public_http_url(source.get("url")):
        errors.append(f"{prefix}: profile source requires public http(s) url and must not use source_path")
    if _has_placeholder(source.get("title")):
        errors.append(f"{prefix}: placeholder text is not allowed")
    if source.get("status") != "current":
        warnings.append(f"{prefix}: profile source {prefix} is {source.get('status')}")
    if source.get("read_level") == "metadata":
        warnings.append(f"{prefix}: profile source {prefix} is metadata-only")


def validate_profile(path: Path) -> tuple[list[str], list[str]]:
    payload = _read_json(path)
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return ["profile: must be an object"], warnings
    if payload.get("schema_version") != "1.0":
        errors.append("profile: schema_version must be '1.0'")
    if payload.get("domain") != "power_grid":
        errors.append("profile: domain must be power_grid")
    if _parse_date(payload.get("verified_at")) is None:
        errors.append("profile: invalid verified_at")
    sources_raw = payload.get("sources")
    competencies = payload.get("competencies")
    if not isinstance(sources_raw, list) or not sources_raw:
        errors.append("profile: at least one source is required")
        sources_raw = []
    if not isinstance(competencies, list) or not competencies:
        errors.append("profile: at least one competency is required")
        competencies = []
    sources = _ids(sources_raw, "source", errors)
    for source_id, source in sources.items():
        _validate_profile_source(source, source_id, errors, warnings)
    seen_cards: set[str] = set()
    for index, card in enumerate(competencies, start=1):
        prefix = f"competency-{index}"
        if not isinstance(card, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        card_id = str(card.get("id") or prefix)
        prefix = card_id
        if card_id in seen_cards:
            errors.append(f"{prefix}: duplicate id")
        seen_cards.add(card_id)
        _require_text(card, ("id", "name", "failure_pattern", "transfer_limit"), prefix, errors)
        if card.get("type") != "inference":
            errors.append(f"{prefix}: type must be inference")
        roles = card.get("owner_roles")
        if not isinstance(roles, list) or not roles or any(
            isinstance(role, bool) or not isinstance(role, int) or role < 1 or role > 6 for role in roles
        ):
            errors.append(f"{prefix}: owner_roles must contain integers 1..6")
        for key in ("source_ids", "review_questions", "evidence_to_request"):
            values = card.get(key)
            if not isinstance(values, list) or not values or any(not _is_text(item) for item in values):
                errors.append(f"{prefix}: {key} must contain non-empty strings")
                values = []
            if key == "source_ids":
                for source_id in values:
                    if source_id not in sources:
                        errors.append(f"{prefix}: unknown source {source_id}")
        checked_values = [card.get("name"), card.get("failure_pattern"), card.get("transfer_limit")]
        checked_values += card.get("review_questions") if isinstance(card.get("review_questions"), list) else []
        checked_values += card.get("evidence_to_request") if isinstance(card.get("evidence_to_request"), list) else []
        if any(_has_placeholder(value) for value in checked_values):
            errors.append(f"{prefix}: placeholder text is not allowed")
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate proposal review-basis JSON.")
    parser.add_argument("input", nargs="?", type=Path, default=Path("input.json"))
    parser.add_argument("-o", "--output", type=Path, help="optional JSON report path")
    parser.add_argument("--profile", action="store_true", help="validate a domain competency profile")
    args = parser.parse_args(argv)
    try:
        errors, warnings = validate_profile(args.input) if args.profile else validate_basis(args.input)
    except Exception as exc:  # noqa: BLE001 - CLI reports parse/setup failures without traceback.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = {"status": "fail" if errors else "pass", "errors": errors, "warnings": warnings}
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status'].upper()}: {len(errors)} errors, {len(warnings)} warnings")
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
