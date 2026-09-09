from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ahp_only_scorer as scorer  # noqa: E402
import ahp_sem_scorer as legacy  # noqa: E402


ROLES = ("examiner", "attorney", "invalidator", "analyst")


def raw_case(value: float = 5.0) -> dict:
    return {
        "case": "AHP-1",
        "title": "test",
        "review_context": {
            "claim_hash": "v1",
            "reviewed_claim_hash": "v1",
            "search_claim_hash": "v1",
            "evidence_hash": "e1",
            "search_status": "complete",
            "claim_text_verified": True,
            "engineering_evidence_status": "confirmed",
            "gates": {
                "subject_matter": "PASS",
                "novelty_inventive_evidence": "PASS",
                "disclosure_support": "PASS",
                "evidence_integrity": "PASS",
                "claim_formality": "PASS",
            },
        },
        "scores": {
            role: {code: value for code in legacy.ALL_INDICATORS}
            for role in ROLES
        },
    }


class AhpOnlyScorerTests(unittest.TestCase):
    def test_endpoint_scaling_is_affine_and_not_probability(self):
        weights = {"N": 0.25, "I": 0.25, "D": 0.25, "Q": 0.25}
        _, low = scorer.ahp_index({"N": 1, "I": 1, "D": 1, "Q": 1}, weights)
        _, high = scorer.ahp_index({"N": 9, "I": 9, "D": 9, "Q": 9}, weights)
        self.assertEqual(low, 0.0)
        self.assertEqual(high, 100.0)

    def test_raw_case_reports_ahp_index_without_grant_probability(self):
        result = scorer.score_case(raw_case())
        self.assertEqual(result["ahp_index"], 50.0)
        self.assertNotIn("grant_probability", result)
        self.assertIn("not grant probability", result["interpretation"])
        self.assertIn("action_queue", result)
        self.assertIn("round_transition", result)
        self.assertIn("patentara_structural_score", result["score_layers"])

    def test_hard_gate_remains_non_compensatory(self):
        case = raw_case(8.5)
        case["review_context"]["gates"]["subject_matter"] = "FAIL"
        result = scorer.score_case(case)
        self.assertEqual(result["decision"], "BLOCKED_BY_HARD_GATE")

    def test_existing_sem_result_is_not_used_as_input(self):
        record = {
            "case": "OLD-1",
            "grant_probability": 0.99,
            "latent": {"S": 7, "N": 5, "I": 5, "D": 5, "Q": 5},
            "group_weights": {"N": 0.2, "I": 0.45, "D": 0.2, "Q": 0.15},
        }
        result = scorer.score_case(record)
        self.assertEqual(result["ahp_index"], 50.0)
        self.assertFalse(result["legacy_sem_reference"]["used_in_ahp_index"])

    def test_cli_writes_cohort_percentiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "output.json"
            input_path.write_text(json.dumps([raw_case(4), raw_case(8)]), encoding="utf-8")
            self.assertEqual(scorer.main([str(input_path), "-o", str(output_path)]), 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertLess(
                payload[0]["relative_position"]["ahp_percentile"],
                payload[1]["relative_position"]["ahp_percentile"],
            )


if __name__ == "__main__":
    unittest.main()
