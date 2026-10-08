import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_review_numbers.py"
FIXTURE = ROOT / "tests" / "fixtures" / "construction-cost-ledger.json"


def load_module():
    spec = importlib.util.spec_from_file_location("audit_review_numbers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditReviewNumbersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module()

    def audit_one(self, check):
        return self.audit.audit_ledger({"checks": [check]})["checks"][0]

    def test_fixture_cases_share_source_and_expected_statuses(self):
        result = self.audit.audit_ledger(json.loads(FIXTURE.read_text(encoding="utf-8")))
        by_id = {check["id"]: check for check in result["checks"]}

        self.assertEqual(by_id["MemoryOS-table4-construction-cost"]["status"], "mismatch")
        self.assertEqual(
            by_id["LightGMEM-table4-construction-cost"]["status"],
            "rounding_possible",
        )
        self.assertIn(
            by_id["Zep-table4-ratio"]["status"],
            {"consistent", "display_consistent"},
        )
        self.assertEqual(by_id["Zep-table4-ratio"]["reported"], "58.0")
        self.assertEqual(
            by_id["MemoryOS-table4-construction-cost"]["source"],
            "original manuscript table 4",
        )

    def test_unknown_rounding_does_not_apply_nearest_tolerance(self):
        checked = self.audit_one(
            {
                "id": "unknown-rounded-sum",
                "kind": "sum",
                "operands": ["2441", "36"],
                "reported": "2478",
                "resolution": "1",
                "rounding": "unknown",
            }
        )

        self.assertEqual(checked["status"], "needs_definition")

    def test_difference_allows_independent_nearest_rounding(self):
        checked = self.audit_one(
            {
                "id": "rounded-difference",
                "kind": "difference",
                "operands": ["2", "2"],
                "reported": "1",
                "resolution": "1",
                "rounding": "nearest",
            }
        )

        self.assertEqual(checked["status"], "rounding_possible")

    def test_difference_obvious_gap_is_mismatch(self):
        checked = self.audit_one(
            {
                "id": "mismatched-difference",
                "kind": "difference",
                "operands": ["2", "2"],
                "reported": "2",
                "resolution": "1",
                "rounding": "nearest",
            }
        )

        self.assertEqual(checked["status"], "mismatch")

    def test_rejects_zero_denominator_non_finite_numbers_and_bad_resolution(self):
        invalid_ledgers = [
            {
                "checks": [
                    {
                        "id": "zero-denominator",
                        "kind": "ratio",
                        "operands": ["1", "0"],
                        "reported": "1",
                        "resolution": "1",
                    }
                ]
            },
            {
                "checks": [
                    {
                        "id": "non-finite",
                        "kind": "sum",
                        "operands": ["1", "NaN"],
                        "reported": "1",
                        "resolution": "1",
                    }
                ]
            },
            {
                "checks": [
                    {
                        "id": "bad-resolution",
                        "kind": "difference",
                        "operands": ["2", "1"],
                        "reported": "1",
                        "resolution": "0",
                    }
                ]
            },
        ]

        for ledger in invalid_ledgers:
            with self.subTest(ledger=ledger["checks"][0]["id"]):
                with self.assertRaises(self.audit.InputError):
                    self.audit.audit_ledger(ledger)

    def test_rejects_missing_fields_and_duplicate_ids(self):
        with self.assertRaisesRegex(self.audit.InputError, "missing"):
            self.audit.audit_ledger({"checks": [{"id": "missing-kind"}]})

        with self.assertRaisesRegex(self.audit.InputError, "duplicate"):
            self.audit.audit_ledger(
                {
                    "checks": [
                        {
                            "id": "dup",
                            "kind": "sum",
                            "operands": ["1", "2"],
                            "reported": "3",
                            "resolution": "1",
                        },
                        {
                            "id": "dup",
                            "kind": "sum",
                            "operands": ["1", "2"],
                            "reported": "3",
                            "resolution": "1",
                        },
                    ]
                }
            )

    def test_cli_valid_mismatch_exits_zero_and_outputs_structured_json(self):
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), str(FIXTURE)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("checks", payload)
        self.assertIn("computed", payload["checks"][0])
        self.assertIn("discrepancy", payload["checks"][0])
        self.assertIn("status", payload["checks"][0])
        self.assertIn("source", payload["checks"][0])

    def test_cli_input_errors_exit_two(self):
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT)],
            input='{"checks":[{"id":"x","kind":"ratio","operands":["1","0"],"reported":"1","resolution":"1"}]}',
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "input_error")

        bad_json = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT)],
            input="{not-json",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(bad_json.returncode, 2)
        self.assertEqual(json.loads(bad_json.stdout)["status"], "input_error")

    def test_rejects_non_string_kind_and_rounding_without_type_error(self):
        invalid_ledgers = [
            {
                "checks": [
                    {
                        "id": "array-kind",
                        "kind": ["sum"],
                        "operands": ["1", "2"],
                        "reported": "3",
                        "resolution": "1",
                    }
                ]
            },
            {
                "checks": [
                    {
                        "id": "object-rounding",
                        "kind": "sum",
                        "operands": ["1", "2"],
                        "reported": "3",
                        "resolution": "1",
                        "rounding": {"mode": "nearest"},
                    }
                ]
            },
        ]

        for ledger in invalid_ledgers:
            with self.subTest(ledger=ledger["checks"][0]["id"]):
                with self.assertRaises(self.audit.InputError):
                    self.audit.audit_ledger(ledger)

    def test_large_integer_sum_preserves_precision_when_formatting(self):
        first = "1234567890123456789012345678901234567890"
        second = "9"
        reported = "1234567890123456789012345678901234567899"
        checked = self.audit_one(
            {
                "id": "large-integer-sum",
                "kind": "sum",
                "operands": [first, second],
                "reported": reported,
                "resolution": "1",
                "rounding": "nearest",
            }
        )

        self.assertEqual(checked["computed"], reported)
        self.assertEqual(checked["status"], "consistent")

    def test_high_precision_ratio_and_cli_decimal_errors_are_structured(self):
        checked = self.audit_one(
            {
                "id": "high-precision-ratio",
                "kind": "ratio",
                "operands": ["1", "7"],
                "reported": "0.1",
                "resolution": "0.1",
                "rounding": "nearest",
            }
        )

        self.assertTrue(checked["computed"].startswith("0.14285714285714285714"))
        self.assertIn(checked["status"], {"display_consistent", "mismatch"})

        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT)],
            input='{"checks":[{"id":"too-large","kind":"sum","operands":["1e10001","1"],"reported":"1","resolution":"1"}]}',
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "input_error")


if __name__ == "__main__":
    unittest.main()
