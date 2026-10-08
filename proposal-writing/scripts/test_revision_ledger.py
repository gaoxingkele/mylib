"""Small synthetic tests for validate_revision_ledger.py."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_revision_ledger import validate


def _write_payload(payload: object) -> Path:
    temp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with temp:
        json.dump(payload, temp, ensure_ascii=False)
    return Path(temp.name)


def _write(records: list[object]) -> Path:
    return _write_payload({"records": records})


def _base(**updates: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "R01",
        "project_id": "P001",
        "location": "第2章 任务1",
        "quote": "指标缺少验证责任方",
        "basis": "S02:指南任务；S04:第2章模板",
        "issue_type": "defect",
        "severity": "major",
        "suggestion": "补充指标验证方法、地点和责任方。",
        "status": "resolved_text",
        "resolved_text": "在任务1中补充由项目组完成离线回放验证，输出验证记录。",
        "evidence": ["S02:任务要求"],
        "notes": "",
    }
    record.update(updates)
    return record


def test_conditional_scenario_and_baseline_denominator_record_passes() -> None:
    record = _base(
        id="R02",
        quote="场景和基线分母需要写清",
        suggestion="写明冻结测试集、条件场景和基线分母。",
        resolved_text="采用冻结测试集，以同一数据、同一任务、同一模型为基线，记录场景覆盖和分母口径。",
        evidence=["S03:考核指标表", "S04:第三章"],
    )
    errors, warnings = validate(_write([record]))
    assert not errors
    assert not warnings


def test_placeholder_cannot_be_cleared_as_resolved() -> None:
    record = _base(resolved_text="现场测试许可【待补】。")
    errors, _ = validate(_write([record]))
    assert any("placeholder" in item for item in errors)


def test_external_gap_needs_evidence_when_resolved() -> None:
    record = _base(
        issue_type="external_evidence_gap",
        quote="预算金额缺少依据",
        suggestion="补充经费测算依据。",
        evidence=[],
        resolved_text="已补充经费测算说明。",
    )
    errors, _ = validate(_write([record]))
    assert any("without evidence" in item for item in errors)


def test_rejected_record_requires_reason() -> None:
    record = _base(status="rejected", resolved_text="", notes="")
    errors, _ = validate(_write([record]))
    assert any("requires notes" in item for item in errors)


def test_needs_external_evidence_allows_unresolved_body() -> None:
    record = _base(
        status="needs_external_evidence",
        issue_type="external_evidence_gap",
        resolved_text="合作单位承诺【待补】。",
        evidence=[],
    )
    errors, warnings = validate(_write([record]))
    assert not errors
    assert any("placeholder" in item for item in warnings)


def test_empty_ledger_fails_instead_of_passing() -> None:
    errors, warnings = validate(_write([]))
    assert any("no_records" in item for item in errors)
    assert not warnings


def test_non_object_record_is_reported_without_attribute_error() -> None:
    errors, _ = validate(_write([1]))
    assert any("record must be an object" in item for item in errors)


def test_top_level_non_object_records_fails_schema_check() -> None:
    try:
        validate(_write_payload({"records": 1}))
    except ValueError as exc:
        assert "records list" in str(exc)
    else:
        raise AssertionError("expected schema failure for non-list records")


def test_duplicate_id_is_reported() -> None:
    errors, _ = validate(_write([_base(), _base()]))
    assert any("duplicate id" in item for item in errors)


def test_invalid_status_and_enums_are_reported() -> None:
    record = _base(status="closed", issue_type="guess", severity="blocker")
    errors, _ = validate(_write([record]))
    assert any("invalid status" in item for item in errors)
    assert any("invalid issue_type" in item for item in errors)
    assert any("invalid severity" in item for item in errors)


if __name__ == "__main__":
    tests = [
        test_conditional_scenario_and_baseline_denominator_record_passes,
        test_placeholder_cannot_be_cleared_as_resolved,
        test_external_gap_needs_evidence_when_resolved,
        test_rejected_record_requires_reason,
        test_needs_external_evidence_allows_unresolved_body,
        test_empty_ledger_fails_instead_of_passing,
        test_non_object_record_is_reported_without_attribute_error,
        test_top_level_non_object_records_fails_schema_check,
        test_duplicate_id_is_reported,
        test_invalid_status_and_enums_are_reported,
    ]
    for test in tests:
        test()
    print(f"PASS: {len(tests)} synthetic revision ledger tests")
