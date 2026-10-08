"""Validate proposal review/revision ledger records.

The checker is intentionally narrow: it verifies traceability and status
semantics for proposal-writing review loops without reading proposal text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUS = {"resolved_text", "needs_external_evidence", "partial", "rejected"}
ALLOWED_ISSUE_TYPES = {
    "defect",
    "optional_method_suggestion",
    "external_evidence_gap",
    "style_term",
    "template_compliance",
}
ALLOWED_SEVERITY = {"critical", "major", "minor"}
PLACEHOLDER_RE = re.compile(r"(【待补】|\bTBD\b|\bTODO\b|待核实|待提供|待确认)", re.IGNORECASE)
EXTERNAL_GAP_RE = re.compile(
    r"(预算|金额|经费|IP|知识产权|样本|授权|许可|合作|承诺|场景|测试|数据|证明|附件|单位|业主|现场)"
)


def _read_json(path: Path) -> Any:
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError("input contains NUL bytes")
    return json.loads(data.decode("utf-8"))


def _records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    raise ValueError("ledger must be a JSON list or an object with a records list")


def _nonempty_text(record: dict[str, Any], key: str) -> bool:
    return isinstance(record.get(key), str) and bool(record[key].strip())


def validate(path: Path) -> tuple[list[str], list[str]]:
    payload = _read_json(path)
    records = _records(payload)
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()

    if not records:
        errors.append("no_records: ledger must contain at least one review record")
        return errors, warnings

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            prefix = f"row-{index}"
            errors.append(f"{prefix}: record must be an object")
            continue
        prefix = str(record.get("id") or f"row-{index}")
        if prefix in seen_ids:
            errors.append(f"{prefix}: duplicate id")
        seen_ids.add(prefix)

        for key in ("id", "project_id", "location", "quote", "basis", "issue_type", "severity", "suggestion", "status"):
            if not _nonempty_text(record, key):
                errors.append(f"{prefix}: missing required text field {key}")

        status = record.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{prefix}: invalid status {status!r}")
        if record.get("issue_type") not in ALLOWED_ISSUE_TYPES:
            errors.append(f"{prefix}: invalid issue_type {record.get('issue_type')!r}")
        if record.get("severity") not in ALLOWED_SEVERITY:
            errors.append(f"{prefix}: invalid severity {record.get('severity')!r}")

        evidence = record.get("evidence", [])
        if evidence is None:
            evidence = []
        if not isinstance(evidence, list) or any(not isinstance(item, str) or not item.strip() for item in evidence):
            errors.append(f"{prefix}: evidence must be a list of non-empty strings")

        basis = str(record.get("basis", ""))
        if not re.search(r"\bS\d{2,}\b|材料\d+|指南|模板|附件|同文内", basis):
            errors.append(f"{prefix}: basis must cite material id, guide/template/appendix, or internal conflict")

        resolved_text = str(record.get("resolved_text", "") or "")
        notes = str(record.get("notes", "") or "")
        if status == "resolved_text":
            if not resolved_text.strip():
                errors.append(f"{prefix}: resolved_text status requires resolved_text")
            if PLACEHOLDER_RE.search(resolved_text):
                errors.append(f"{prefix}: resolved_text contains unresolved placeholder")
            if record.get("issue_type") == "external_evidence_gap" or EXTERNAL_GAP_RE.search(str(record.get("quote", "")) + str(record.get("suggestion", ""))):
                if not evidence:
                    errors.append(f"{prefix}: externally verifiable issue cannot be resolved without evidence")
        elif status in {"needs_external_evidence", "partial"}:
            if resolved_text.strip() and PLACEHOLDER_RE.search(resolved_text):
                warnings.append(f"{prefix}: unresolved placeholder remains in resolved_text")
        elif status == "rejected":
            if not notes.strip():
                errors.append(f"{prefix}: rejected status requires notes explaining source check or inapplicability")

        if len(str(record.get("quote", ""))) > 240:
            warnings.append(f"{prefix}: quote is long; keep only a locator-sized excerpt")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a proposal revision ledger JSON file.")
    parser.add_argument("ledger", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="optional JSON report path")
    args = parser.parse_args(argv)

    try:
        errors, warnings = validate(args.ledger)
    except Exception as exc:  # noqa: BLE001 - CLI should report parse and validation setup failures.
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
