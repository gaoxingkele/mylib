"""Synthetic tests for validate_review_basis.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_review_basis import validate_basis, validate_profile


SCRIPT = Path(__file__).with_name("validate_review_basis.py")


def _write_payload(payload: object, *, bom: bool = False) -> Path:
    temp = tempfile.NamedTemporaryFile("w", encoding="utf-8-sig" if bom else "utf-8", suffix=".json", delete=False)
    with temp:
        json.dump(payload, temp, ensure_ascii=False)
    return Path(temp.name)


def _context(**updates: object) -> dict[str, object]:
    context: dict[str, object] = {
        "funder": "yn_power",
        "call_id": "2026-call",
        "stage": "application",
        "project_type": "grid_ai",
        "as_of": "2026-10-10",
    }
    context.update(updates)
    return context


def _source(source_id: str = "S1", **updates: object) -> dict[str, object]:
    source: dict[str, object] = {
        "id": source_id,
        "title": "Current call",
        "kind": "call",
        "status": "current",
        "read_level": "full_text",
        "funder": "yn_power",
        "call_id": "2026-call",
        "stages": ["application"],
        "project_types": ["grid_ai"],
        "url": "https://example.invalid/call",
        "effective_date": "2026-01-01",
    }
    source.update(updates)
    return source


def _record(record_id: str = "R1", **updates: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": record_id,
        "project_id": "P1",
        "location": "section 1",
        "quote": "short locator excerpt",
        "basis": "S1 section 2",
        "suggestion": "align requirement wording",
        "claim_type": "requirement",
        "source_ids": ["S1"],
        "source_loci": {"S1": "section 2"},
        "applicability": "applicable",
    }
    record.update(updates)
    return record


def _payload(
    *,
    context: dict[str, object] | None = None,
    sources: list[dict[str, object]] | None = None,
    records: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "context": context if context is not None else _context(),
        "sources": sources if sources is not None else [_source()],
        "records": records if records is not None else [_record()],
    }


class ReviewBasisTests(unittest.TestCase):
    def test_valid_requirement_passes_and_cli_writes_report(self) -> None:
        input_path = _write_payload(_payload(), bom=True)
        report_path = input_path.with_suffix(".report.json")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(input_path), "-o", str(report_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["errors"], [])

    def test_hard_requirement_rejects_metadata_historical_guide_wrong_stage_plan_future(self) -> None:
        sources = [
            _source("META", read_level="metadata"),
            _source("OLD", status="historical", kind="guide_case"),
            _source("STAGE", stages=["midterm"]),
            _source("PLAN", kind="standard_plan"),
            _source("FUTURE", effective_date="2026-12-01"),
        ]
        records = [
            _record("R_META", source_ids=["META"], source_loci={"META": "p1"}),
            _record("R_OLD", source_ids=["OLD"], source_loci={"OLD": "p1"}),
            _record("R_STAGE", source_ids=["STAGE"], source_loci={"STAGE": "p1"}),
            _record("R_PLAN", source_ids=["PLAN"], source_loci={"PLAN": "p1"}),
            _record("R_FUTURE", source_ids=["FUTURE"], source_loci={"FUTURE": "p1"}),
        ]
        errors, warnings = validate_basis(_write_payload(_payload(sources=sources, records=records)))
        joined = "\n".join(errors)
        self.assertIn("metadata", joined)
        self.assertIn("guide_case", joined)
        self.assertIn("stage", joined)
        self.assertIn("standard_plan", joined)
        self.assertIn("not yet effective", joined)
        self.assertFalse(any("quote" in item.lower() for item in errors + warnings))

    def test_adoption_allows_scope_mismatch_only_with_current_applicable_adopter(self) -> None:
        std = _source("STD", kind="standard", funder="general", call_id="other-call")
        call = _source("CALL", kind="call", read_level="excerpt")
        adopted = _record(
            source_ids=["STD", "CALL"],
            source_loci={"STD": "5.1", "CALL": "annex A"},
            adoptions=[
                {
                    "source_id": "STD",
                    "adopted_by": "CALL",
                    "locus": "annex A",
                    "explanation": "Current call adopts this standard for application projects.",
                }
            ],
        )
        errors, warnings = validate_basis(_write_payload(_payload(sources=[std, call], records=[adopted])))
        self.assertEqual(errors, [])
        self.assertTrue(any("does not prove content truth" in item for item in warnings))

    def test_bad_adoptions_are_reported_and_cannot_bypass_forbidden_sources(self) -> None:
        meta = _source("META", read_level="metadata", call_id="other-call")
        wrong_call = _source("WRONG", kind="call", call_id="other-call")
        self_ref = _record(
            "SELF",
            source_ids=["META"],
            source_loci={"META": "p1"},
            adoptions=[{"source_id": "META", "adopted_by": "META", "locus": "p1", "explanation": "self"}],
        )
        wrong_adopter = _record(
            "BAD",
            source_ids=["META", "WRONG"],
            source_loci={"META": "p1", "WRONG": "p2"},
            adoptions=[{"source_id": "META", "adopted_by": "WRONG", "locus": "p2", "explanation": "wrong call"}],
        )
        errors, _ = validate_basis(_write_payload(_payload(sources=[meta, wrong_call], records=[self_ref, wrong_adopter])))
        joined = "\n".join(errors)
        self.assertIn("self-reference", joined)
        self.assertIn("adopter source does not match context", joined)
        self.assertIn("metadata", joined)

    def test_stray_duplicate_and_incomplete_adoptions_fail(self) -> None:
        std = _source("STD", kind="standard", funder="general", call_id="other-call")
        call = _source("CALL", kind="call")
        record = _record(
            source_ids=["STD", "CALL"],
            source_loci={"STD": "5.1", "CALL": "annex A"},
            adoptions=[
                {"source_id": "STRAY", "adopted_by": "CALL", "locus": "annex A", "explanation": "stray target"},
                {"source_id": "STD", "adopted_by": "MISSING", "locus": "annex A", "explanation": "unknown adopter"},
                {"source_id": "STD", "adopted_by": "CALL", "locus": "annex A", "explanation": "first"},
                {"source_id": "STD", "adopted_by": "CALL", "locus": "", "explanation": "duplicate incomplete"},
            ],
        )
        errors, _ = validate_basis(_write_payload(_payload(sources=[std, call], records=[record])))
        joined = "\n".join(errors)
        self.assertIn("adoption target STRAY is not cited", joined)
        self.assertIn("unknown adopter source MISSING", joined)
        self.assertIn("duplicate adoption target STD", joined)
        self.assertIn("locus and explanation are required", joined)
        self.assertIn("standard source STD requires explicit current adoption basis", joined)

    def test_malformed_context_and_scope_values_report_without_crashing(self) -> None:
        source = _source(call_id=[], stages=["application"], project_types=["grid_ai"])
        payload = _payload(context=["bad"], sources=[source], records=[_record()])
        errors, _ = validate_basis(_write_payload(payload))  # type: ignore[arg-type]
        joined = "\n".join(errors)
        self.assertIn("context: must be an object", joined)
        self.assertIn("invalid call_id", joined)

    def test_hard_call_and_template_sources_must_name_current_batch(self) -> None:
        sources = [
            _source("CALL_ALL", kind="call", call_id="all"),
            _source("TPL_OLD", kind="template", call_id="old-call"),
        ]
        records = [
            _record("R_CALL", source_ids=["CALL_ALL"], source_loci={"CALL_ALL": "p1"}),
            _record("R_TPL", source_ids=["TPL_OLD"], source_loci={"TPL_OLD": "p2"}),
        ]
        errors, _ = validate_basis(_write_payload(_payload(sources=sources, records=records)))
        joined = "\n".join(errors)
        self.assertIn("hard requirement call source CALL_ALL must explicitly match current call_id", joined)
        self.assertIn("hard requirement template source TPL_OLD must explicitly match current call_id", joined)

    def test_mandatory_standard_can_support_requirement_without_adoption(self) -> None:
        standard = _source(
            "GB1",
            kind="standard",
            funder="general",
            call_id="all",
            stages=["all"],
            project_types=["all"],
            title="GB 50052 mandatory power standard",
            standard_type="mandatory",
        )
        errors, warnings = validate_basis(_write_payload(_payload(sources=[standard], records=[_record(source_ids=["GB1"], source_loci={"GB1": "4.1"})])))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_recommended_standard_still_requires_adoption_and_code_consistency(self) -> None:
        recommended = _source("GBT", kind="standard", funder="general", call_id="all", title="GB/T 123 recommended standard")
        contradictory = _source(
            "GBZ",
            kind="standard",
            funder="general",
            call_id="all",
            title="GB/Z 456 guidance standard",
            standard_type="mandatory",
        )
        records = [
            _record("R_GBT", source_ids=["GBT"], source_loci={"GBT": "5.1"}),
            _record("R_GBZ", source_ids=["GBZ"], source_loci={"GBZ": "6.1"}),
        ]
        errors, _ = validate_basis(_write_payload(_payload(sources=[recommended, contradictory], records=records)))
        joined = "\n".join(errors)
        self.assertIn("standard source GBT requires explicit current adoption basis", joined)
        self.assertIn("standard_type mandatory conflicts with recommended or guidance standard code", joined)

    def test_domestic_industry_recommended_codes_cannot_be_marked_mandatory(self) -> None:
        sources = [
            _source("DLT", kind="standard", funder="general", call_id="all", title="DL/T 2874-2024 smart grid guide", standard_type="mandatory"),
            _source("NBT", kind="standard", funder="general", call_id="all", title="NB／T 12345-2026 fullwidth slash", standard_type="mandatory"),
        ]
        records = [
            _record("R_DLT", source_ids=["DLT"], source_loci={"DLT": "5.1"}),
            _record("R_NBT", source_ids=["NBT"], source_loci={"NBT": "6.1"}),
        ]
        errors, _ = validate_basis(_write_payload(_payload(sources=sources, records=records)))
        joined = "\n".join(errors)
        self.assertIn("DLT: standard_type mandatory conflicts with recommended or guidance standard code", joined)
        self.assertIn("NBT: standard_type mandatory conflicts with recommended or guidance standard code", joined)

    def test_basis_mode_allows_private_source_path(self) -> None:
        source = _source(url="", source_path="C:/synthetic-private/current-call.pdf")
        errors, _ = validate_basis(_write_payload(_payload(sources=[source])))
        self.assertEqual(errors, [])

    def test_structure_errors_are_clear_for_unknown_refs_duplicates_bad_dates_and_empty_scope(self) -> None:
        source = _source(stages=[], effective_date="2026/10/10")
        records = [
            _record(source_ids=["UNKNOWN"], source_loci={}),
            _record(source_ids=["S1"], source_loci={"S1": "p2"}),
        ]
        errors, _ = validate_basis(_write_payload(_payload(context=_context(as_of="bad-date"), sources=[source], records=records)))
        joined = "\n".join(errors)
        self.assertIn("invalid context as_of", joined)
        self.assertIn("empty stages", joined)
        self.assertIn("invalid effective_date", joined)
        self.assertIn("unknown source", joined)
        self.assertIn("duplicate id", joined)

    def test_soft_reference_warns_but_passes_and_multiple_records_same_source_are_ok(self) -> None:
        soft_source = _source("M1", status="historical", read_level="metadata", stages=["midterm"], project_types=["other"])
        records = [
            _record("R1", claim_type="recommendation", applicability="conditional", source_ids=["M1"], source_loci={"M1": "meta"}),
            _record("R2", claim_type="inference", applicability="unknown", source_ids=["M1"], source_loci={"M1": "meta"}),
        ]
        errors, warnings = validate_basis(_write_payload(_payload(sources=[soft_source], records=records)))
        self.assertEqual(errors, [])
        self.assertTrue(any("soft reference" in item for item in warnings))

    def test_catalog_fact_may_omit_loci_but_other_claims_may_not(self) -> None:
        catalog = _record("CAT", claim_type="catalog_fact", source_loci={})
        inference = _record("INF", claim_type="inference", source_loci={})
        errors, _ = validate_basis(_write_payload(_payload(records=[catalog, inference])))
        self.assertTrue(any("INF" in item and "source_loci" in item for item in errors))
        self.assertFalse(any("CAT" in item and "source_loci" in item for item in errors))

    def test_nul_input_is_setup_error_exit_2(self) -> None:
        temp = tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False)
        with temp:
            temp.write(b'{"records": []}\x00')
        result = subprocess.run([sys.executable, str(SCRIPT), temp.name], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("NUL", result.stderr)

    def test_non_text_enum_values_are_validation_errors_not_type_errors(self) -> None:
        cases = [
            ("source.kind", _payload(sources=[_source(kind=[])])),
            ("source.status", _payload(sources=[_source(status={})])),
            ("source.read_level", _payload(sources=[_source(read_level=None)])),
            ("source.standard_type", _payload(sources=[_source(kind="standard", standard_type=[])])),
            ("context.stage", _payload(context=_context(stage=[]))),
            ("record.claim_type", _payload(records=[_record(claim_type={})])),
            ("record.applicability", _payload(records=[_record(applicability=None)])),
        ]
        for name, payload in cases:
            with self.subTest(name=name):
                path = _write_payload(payload)
                errors, _ = validate_basis(path)
                self.assertTrue(errors)
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_dates_are_strict_iso_calendar_dates(self) -> None:
        bad_contexts = ["20261010", "2026-W41-6"]
        for value in bad_contexts:
            with self.subTest(as_of=value):
                errors, _ = validate_basis(_write_payload(_payload(context=_context(as_of=value))))
                self.assertTrue(any("invalid context as_of" in item for item in errors))
        bad_sources = ["20261010", "2026-W41-6"]
        for value in bad_sources:
            with self.subTest(effective_date=value):
                errors, _ = validate_basis(_write_payload(_payload(sources=[_source(effective_date=value)])))
                self.assertTrue(any("invalid effective_date" in item for item in errors))
        leap_errors, _ = validate_basis(_write_payload(_payload(context=_context(as_of="2024-02-29"), sources=[_source(effective_date="2024-02-29")])))
        self.assertFalse(any("invalid context as_of" in item or "invalid effective_date" in item for item in leap_errors))


class ReviewProfileTests(unittest.TestCase):
    def _profile(self, **updates: object) -> dict[str, object]:
        profile: dict[str, object] = {
            "schema_version": "1.0",
            "domain": "power_grid",
            "verified_at": "2026-10-10",
            "sources": [_source("P1", funder="general", call_id="all", stages=["all"], project_types=["all"])],
            "competencies": [
                {
                    "id": "C1",
                    "name": "Grid application evidence check",
                    "type": "inference",
                    "owner_roles": [1, 3],
                    "source_ids": ["P1"],
                    "review_questions": ["Does the claim cite an applicable source?"],
                    "failure_pattern": "Uncited hard requirement.",
                    "evidence_to_request": ["Applicable call or template locus."],
                    "transfer_limit": "Use only for power grid proposal review.",
                }
            ],
        }
        profile.update(updates)
        return profile

    def test_valid_profile_passes_without_fixed_card_count(self) -> None:
        errors, warnings = validate_profile(_write_payload(self._profile()))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_empty_and_placeholder_profile_fail_clearly(self) -> None:
        bad = self._profile(
            verified_at="bad-date",
            sources=[],
            competencies=[
                {
                    "id": "C1",
                    "name": "TBD",
                    "type": "inference",
                    "owner_roles": [0, 7],
                    "source_ids": ["UNKNOWN"],
                    "review_questions": [""],
                    "failure_pattern": "TODO",
                    "evidence_to_request": [],
                    "transfer_limit": "",
                }
            ],
        )
        errors, _ = validate_profile(_write_payload(bad))
        joined = "\n".join(errors)
        self.assertIn("at least one source", joined)
        self.assertIn("placeholder", joined)
        self.assertIn("owner_roles", joined)
        self.assertIn("unknown source", joined)
        self.assertIn("verified_at", joined)

    def test_profile_allows_metadata_historical_unknown_sources_as_warnings(self) -> None:
        profile = self._profile(
            sources=[
                _source("META", status="historical", read_level="metadata", funder="general", call_id="all", stages=["all"], project_types=["all"]),
                _source("UNK", status="unknown", read_level="metadata", funder="general", call_id="all", stages=["all"], project_types=["all"]),
            ],
            competencies=[
                {
                    "id": "C1",
                    "name": "Historical reference awareness",
                    "type": "inference",
                    "owner_roles": [1, 6],
                    "source_ids": ["META", "UNK"],
                    "review_questions": ["Is this source only contextual?"],
                    "failure_pattern": "Treating a contextual source as a hard requirement.",
                    "evidence_to_request": ["Current call locus if making a hard requirement."],
                    "transfer_limit": "Context only; does not prove current requirements.",
                }
            ],
        )
        errors, warnings = validate_profile(_write_payload(profile))
        self.assertEqual(errors, [])
        self.assertTrue(any("profile source META is historical" in item for item in warnings))
        self.assertTrue(any("profile source UNK is unknown" in item for item in warnings))
        self.assertTrue(any("metadata-only" in item for item in warnings))

    def test_profile_rejects_bool_owner_roles(self) -> None:
        profile = self._profile(
            competencies=[
                {
                    "id": "CBOOL",
                    "name": "Role check",
                    "type": "inference",
                    "owner_roles": [True],
                    "source_ids": ["P1"],
                    "review_questions": ["Question?"],
                    "failure_pattern": "Pattern.",
                    "evidence_to_request": ["Evidence."],
                    "transfer_limit": "Limit.",
                }
            ]
        )
        errors, _ = validate_profile(_write_payload(profile))
        self.assertTrue(any("owner_roles" in item for item in errors))

    def test_profile_non_text_enum_values_are_validation_errors_not_type_errors(self) -> None:
        cases = [
            ("source.kind", self._profile(sources=[_source("P1", kind=[])])),
            ("source.status", self._profile(sources=[_source("P1", status={})])),
            ("source.read_level", self._profile(sources=[_source("P1", read_level=None)])),
            ("source.standard_type", self._profile(sources=[_source("P1", kind="standard", standard_type=[])])),
            (
                "card.type",
                self._profile(
                    competencies=[
                        {
                            "id": "C1",
                            "name": "Enum check",
                            "type": [],
                            "owner_roles": [1],
                            "source_ids": ["P1"],
                            "review_questions": ["Question?"],
                            "failure_pattern": "Pattern.",
                            "evidence_to_request": ["Evidence."],
                            "transfer_limit": "Limit.",
                        }
                    ]
                ),
            ),
        ]
        for name, profile in cases:
            with self.subTest(name=name):
                path = _write_payload(profile)
                errors, _ = validate_profile(path)
                self.assertTrue(errors)
                result = subprocess.run([sys.executable, str(SCRIPT), "--profile", str(path)], text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_profile_requires_public_http_url_and_rejects_source_path(self) -> None:
        cases = [
            ("source_path", _source("P1", url="", source_path="C:/synthetic-private/profile-source.pdf")),
            ("file_url", _source("P1", url="file:///C:/synthetic-private/profile-source.pdf")),
            ("localhost", _source("P1", url="http://localhost/profile")),
            ("loopback", _source("P1", url="https://127.0.0.1/profile")),
        ]
        for name, source in cases:
            with self.subTest(name=name):
                errors, _ = validate_profile(_write_payload(self._profile(sources=[source])))
                joined = "\n".join(errors)
                self.assertIn("profile source requires public http(s) url", joined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
