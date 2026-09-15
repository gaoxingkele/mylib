from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ahp_sem_scorer as scorer  # noqa: E402


ROLES = ("examiner", "attorney", "invalidator", "analyst")


def numeric_case(value: float = 6.0) -> dict:
    return {
        "case": "T-1",
        "title": "test",
        "scores": {
            role: {code: value for code in scorer.ALL_INDICATORS}
            for role in ROLES
        },
    }


def rich_case(value: float = 7.0) -> dict:
    entry = {
        "score": value,
        "confidence": 0.9,
        "evidence_quality": 0.9,
        "status": "confirmed",
        "evidence_refs": ["claim:CN100000001A:1"],
    }
    return {
        "case": "T-2",
        "title": "rich",
        "review_context": {
            "claim_hash": "claim-v2",
            "reviewed_claim_hash": "claim-v2",
            "search_claim_hash": "claim-v2",
            "evidence_hash": "evidence-v1",
            "application_date": "2026-01-01",
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
            role: {code: dict(entry) for code in scorer.ALL_INDICATORS}
            for role in ROLES
        },
    }


class PatentGrantScorerTests(unittest.TestCase):
    def test_legacy_numeric_input_remains_compatible(self):
        result = scorer.score_case(numeric_case())
        self.assertEqual(result["protocol_version"], "2.0.0")
        self.assertEqual(set(result["latent"]), {"S", "N", "I", "D", "Q"})
        self.assertIn("legacy_numeric_scores_without_evidence_metadata", result["confidence_warnings"])
        self.assertEqual(len(result["consensus"]), 16)
        self.assertNotIn("DIRECT", result["decision"])

    def test_hard_gate_cannot_be_averaged_away(self):
        case = rich_case(8.5)
        case["review_context"]["gates"]["subject_matter"] = "FAIL"
        result = scorer.score_case(case)
        self.assertEqual(result["decision"], "BLOCKED_BY_HARD_GATE")
        self.assertIn("subject_matter", result["hard_gates"]["blocking"])

    def test_stale_claim_search_binding_blocks_reuse(self):
        case = rich_case()
        case["review_context"]["search_claim_hash"] = "claim-v1"
        result = scorer.score_case(case)
        self.assertTrue(result["version_binding"]["stale"])
        self.assertEqual(result["decision"], "STALE_REVIEW_RESEARCH_REQUIRED")

    # --- binding-identity regressions (2026-09-15) -------------------------
    # A bare `current_claim_hash != search_claim_hash` test assumes both hashes
    # name the same artifact. Populated from different files it yields a
    # guaranteed false positive; written equal by hand it yields a guaranteed
    # false negative. These four cases pin both failure modes.

    def test_derived_claim_text_binding_is_not_a_false_stale(self):
        """Search bound to claim 1 extracted from the reviewed claims document
        describes a different artifact than the document — that is not drift."""
        case = rich_case()
        case["review_context"]["search_claim_hash"] = "sha256:claim1-hash"
        case["review_context"]["search_binding"] = {
            "searched_artifact": "claims/claim1.txt",
            "document_artifact": "02_权利要求书.md",
            "relation": "verbatim_substring",
            "searched_claim_text_hash": "sha256:claim1-hash",
        }
        result = scorer.score_case(case)
        binding = result["version_binding"]
        self.assertFalse(binding["stale"])
        self.assertNotIn("search_bound_to_different_claim_hash", binding["stale_reasons"])
        self.assertEqual(binding["search_binding_relation"], "verbatim_substring")

    def test_undeclared_binding_identity_is_visible_not_silent(self):
        """Equal hashes with no declared identity is an assertion, not evidence."""
        result = scorer.score_case(rich_case())  # claim_hash == search_claim_hash
        binding = result["version_binding"]
        self.assertFalse(binding["stale"])
        self.assertEqual(binding["search_binding_basis"], "legacy_assumed_same_artifact")
        self.assertIn("search_binding_identity_undeclared", binding["binding_warnings"])
        self.assertIn("search_binding_identity_undeclared", result["confidence_warnings"])

    def test_binding_equality_cannot_be_asserted_without_evidence(self):
        """With search_path present the hash is recomputed from the evidence, so
        declaring matching hashes does not make the check pass."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "semantic.json").write_text(
                json.dumps({"input": "the OLD claim text"}), encoding="utf-8"
            )
            case = rich_case()
            case["review_context"]["search_path"] = "semantic.json"
            case["review_context"]["search_binding"] = {
                "relation": "same_document",
                "search_input_hash": "claim-v2",  # caller claims it matches
            }
            result = scorer.score_case(case, root=tmp)
        binding = result["version_binding"]
        self.assertEqual(binding["search_binding_basis"], "verified_from_evidence")
        self.assertTrue(binding["stale"])
        self.assertIn("search_bound_to_different_claim_hash", binding["stale_reasons"])
        self.assertEqual(result["decision"], "STALE_REVIEW_RESEARCH_REQUIRED")

    def test_unreadable_evidence_degrades_to_a_warning(self):
        """A missing evidence file must be visible, never a silent pass."""
        case = rich_case()
        case["review_context"]["search_path"] = "does/not/exist.json"
        result = scorer.score_case(case, root=".")
        binding = result["version_binding"]
        self.assertIn("search_evidence_unreadable", binding["binding_warnings"])
        self.assertIn("search_evidence_unreadable", result["confidence_warnings"])

    def test_low_evidence_byzantine_outlier_is_downweighted(self):
        case = rich_case()
        case["scores"]["analyst"]["I1"] = {
            "score": 1,
            "confidence": 0.2,
            "evidence_quality": 0.2,
            "status": "unverified",
            "evidence_refs": [],
        }
        result = scorer.score_case(case)
        consensus = result["consensus"]["I1"]
        self.assertEqual(consensus["suppressed_experts"], ["analyst"])
        self.assertGreater(consensus["score"], 6.5)
        self.assertTrue(consensus["review_required"])

    def test_high_quality_minority_is_preserved_for_arbitration(self):
        case = rich_case()
        case["scores"]["analyst"]["I1"] = {
            "score": 1,
            "confidence": 1.0,
            "evidence_quality": 1.0,
            "status": "confirmed",
            "evidence_refs": ["claim:CN200000001A:1"],
        }
        result = scorer.score_case(case)
        consensus = result["consensus"]["I1"]
        self.assertEqual(consensus["suppressed_experts"], [])
        self.assertEqual(consensus["high_quality_dissent"], ["analyst"])
        self.assertTrue(consensus["review_required"])

    def test_markov_transition_separates_claim_change_from_retrieval_shift(self):
        case = rich_case()
        case["history"] = [{
            "claim_hash": "claim-v1",
            "evidence_hash": "evidence-v1",
            "grant_probability": 0.50,
            "latent": {"S": 6, "N": 6, "I": 6, "D": 6, "Q": 6},
        }]
        result = scorer.score_case(case)
        self.assertEqual(result["round_transition"]["type"], "claim_revision_fixed_evidence")
        self.assertTrue(result["round_transition"]["controlled_comparison"])

        case["review_context"]["evidence_hash"] = "evidence-v2"
        shifted = scorer.score_case(case)
        self.assertEqual(shifted["round_transition"]["type"], "mixed_claim_and_evidence_shift")
        self.assertFalse(shifted["round_transition"]["controlled_comparison"])

    def test_cohort_percentiles_are_relative(self):
        low = scorer.score_case(rich_case(5.0))
        high = scorer.score_case(rich_case(8.0))
        results = [low, high]
        scorer.add_relative_positions(results, cohort_id="test-cohort")
        self.assertLess(low["relative_position"]["risk_percentile"], high["relative_position"]["risk_percentile"])
        self.assertEqual(high["relative_position"]["cohort_id"], "test-cohort")

    def test_cli_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            output_path = Path(tmp) / "output.json"
            input_path.write_text(json.dumps([numeric_case()]), encoding="utf-8")
            exit_code = scorer.main([str(input_path), "-o", str(output_path)])
            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 1)
            self.assertIn("relative_position", payload[0])


if __name__ == "__main__":
    unittest.main()
