"""Tests for the 2.3.0 optional layers, gates and warnings of ahp_only_scorer.

Every 2.3.0 feature is driven by an optional input field. The regression test
pins that legacy inputs reproduce the pre-2.3.0 outputs recorded in
``fixtures/legacy_golden_pre230.json`` (generated with the unmodified 2.2.x
scorer before the upgrade).
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ahp_only_scorer as scorer  # noqa: E402
import ahp_sem_scorer as core  # noqa: E402


ROLES = ("examiner", "attorney", "invalidator", "analyst")
OFFSETS = {"examiner": 0.0, "attorney": 0.5, "invalidator": -1.0, "analyst": 0.0}


def rich_case(search_status: str = "complete") -> dict:
    entry = {"confidence": 0.9, "evidence_quality": 0.9, "status": "confirmed", "evidence_refs": ["x"]}
    return {
        "case": "T230",
        "title": "t",
        "review_context": {
            "claim_hash": "sha256:c1",
            "reviewed_claim_hash": "sha256:c1",
            "search_claim_hash": "sha256:c1",
            "evidence_hash": "sha256:e1",
            "search_status": search_status,
            "claim_text_verified": True,
            "engineering_evidence_status": "confirmed",
            "gates": {name: "PASS" for name in core.GATE_ALIASES},
        },
        "scores": {
            role: {code: dict(entry, score=5.0 + OFFSETS[role]) for code in core.ALL_INDICATORS}
            for role in ROLES
        },
    }


def matrix(docs: dict, frozen_at: str = "v1-split") -> dict:
    return {
        "features": {f"F{i}": f"feature {i}" for i in range(1, 5)},
        "independent_claim_features": ["F1", "F2", "F3", "F4"],
        "docs": docs,
        "frozen_at": frozen_at,
    }


def strip_ws_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256("".join(c for c in text if not c.isspace()).encode()).hexdigest()


class LegacyRegressionTests(unittest.TestCase):
    def test_legacy_inputs_reproduce_pre230_outputs_field_by_field(self):
        golden = json.loads((TESTS_DIR / "fixtures" / "legacy_golden_pre230.json").read_text(encoding="utf-8"))
        for case, old in zip(golden["inputs"], golden["outputs"]):
            with self.subTest(case=case.get("case")):
                new = scorer.score_case(copy.deepcopy(case))
                self.assertEqual(new["protocol_version"], "2.3.0-ahp-only")
                for key, value in old.items():
                    if key == "protocol_version":
                        continue
                    self.assertEqual(new.get(key), value, key)
                extra = set(new) - set(old)
                if case.get("history"):
                    # the only addition for a legacy case with history
                    self.assertEqual(extra, {"audit_warnings"})
                    self.assertEqual(new["audit_warnings"], ["anchor_not_frozen"])
                else:
                    self.assertEqual(extra, set())

    def test_new_fields_never_move_the_ahp_index(self):
        base = scorer.score_case(rich_case("degraded"))
        case = rich_case("degraded")
        rc = case["review_context"]
        rc["feature_matrix"] = matrix({"D1": {"F1": "●", "F2": "●", "F3": "●"}})
        rc["retrieval"] = {"databases": ["a", "b"], "claim_fulltext_semantic": True, "fulltext_fetched_n": 30}
        rc["gates"]["background_prior_art_alignment"] = "PASS"
        case["expert_meta"] = {role: {"independent": False} for role in ROLES}
        new = scorer.score_case(case)
        self.assertEqual(new["ahp_index"], base["ahp_index"])
        self.assertEqual(new["latent"], base["latent"])
        self.assertEqual(new["ahp_band"], base["ahp_band"])


class ResidualDistinctionTests(unittest.TestCase):
    def test_single_pivot_and_coverage(self):
        case = rich_case()
        case["review_context"]["feature_matrix"] = matrix({
            "D1": {"F1": "●", "F2": "◐", "F3": "○", "F4": "○"},
            "D2": {"F2": "●", "F3": "●", "F4": "○"},
        })
        layer = scorer.score_case(case)["score_layers"]["residual_distinction"]
        self.assertFalse(layer["in_index"])
        self.assertEqual(layer["not_fully_disclosed"], ["F4"])
        self.assertEqual(layer["untouched_by_any_document"], ["F4"])
        self.assertEqual(layer["full_disclosure_coverage"], 0.75)
        self.assertEqual(layer["per_feature"]["F2"]["disclosed_by"], ["D2"])
        self.assertEqual(layer["best_single_document"]["document"], "D2")
        self.assertIn("single_pivot_independent_claim", layer["warnings"])

    def test_partial_only_is_not_disclosed_and_split_change_is_flagged(self):
        case = rich_case()
        case["review_context"]["feature_matrix"] = matrix(
            {"D1": {"F1": "◐", "F2": "◐", "F3": "●"}}, frozen_at="v2-split"
        )
        case["history"] = [{"claim_hash": "sha256:c1", "evidence_hash": "sha256:e1",
                            "feature_matrix_frozen_at": "v1-split", "anchor_sha256": "a"}]
        case["review_context"]["anchor_sha256"] = "a"
        result = scorer.score_case(case)
        layer = result["score_layers"]["residual_distinction"]
        self.assertEqual(layer["per_feature"]["F1"]["status"], "partial_only")
        self.assertEqual(layer["not_fully_disclosed_count"], 3)
        self.assertNotIn("single_pivot_independent_claim", layer["warnings"])
        self.assertEqual(layer["split_consistency_vs_previous"], "changed")
        self.assertIn("feature_matrix_split_changed", result["audit_warnings"])


class RetrievalCoverageTests(unittest.TestCase):
    def test_graded_cap_replaces_binary_45(self):
        legacy = scorer.score_case(rich_case("degraded"))
        self.assertEqual(legacy["score_layers"]["evidence_confidence"], 45.0)
        case = rich_case("degraded")
        case["review_context"]["retrieval"] = {
            "databases": ["patsnap", "google_patents"],
            "claim_fulltext_semantic": True,
            "fulltext_fetched_n": 38,
            "incopat_done": False,
            "legal_status_verified": False,
            "npl_fulltext": False,
            "conflict_blindspot": True,
        }
        result = scorer.score_case(case)
        layer = result["score_layers"]["retrieval_coverage"]
        self.assertEqual(layer["cap_items_met"], 3)
        self.assertEqual(layer["degraded_cap_applied"], 60.0)
        self.assertEqual(result["score_layers"]["evidence_confidence"], 60.0)
        self.assertIn("degraded_cap_graded_to_60", result["confidence_warnings"])

    def test_cap_is_bounded_at_65_and_ignored_when_not_degraded(self):
        full = {"databases": ["a", "b"], "claim_fulltext_semantic": True, "fulltext_fetched_n": 10,
                "incopat_done": True, "legal_status_verified": True}
        case = rich_case("degraded")
        case["review_context"]["retrieval"] = dict(full)
        self.assertEqual(scorer.score_case(case)["score_layers"]["evidence_confidence"], 65.0)
        complete = rich_case("complete")
        complete["review_context"]["retrieval"] = dict(full)
        result = scorer.score_case(complete)
        self.assertIsNone(result["score_layers"]["retrieval_coverage"]["degraded_cap_applied"])
        self.assertEqual(result["score_layers"]["evidence_confidence"],
                         scorer.score_case(rich_case("complete"))["score_layers"]["evidence_confidence"])

    def test_feature_not_searched_warning(self):
        case = rich_case()
        case["review_context"]["feature_matrix"] = matrix({"D1": {"F1": "●"}})
        case["review_context"]["retrieval"] = {"databases": ["a"], "features_searched": ["F1", "F2", "F4"]}
        result = scorer.score_case(case)
        self.assertEqual(result["score_layers"]["retrieval_coverage"]["independent_features_not_searched"], ["F3"])
        self.assertIn("feature_not_searched:F3", result["audit_warnings"])


class SearchBindingTests(unittest.TestCase):
    def _evidence(self, tmp: str, query: str) -> str:
        (Path(tmp) / "mcp.json").write_text(
            json.dumps({"request": {"semantic_query": query}}, ensure_ascii=False), encoding="utf-8"
        )
        return "mcp.json"

    def test_jsonpath_and_strip_ws_normalisation_verify_binding(self):
        claim_text = "一种方法，包括：步骤A；步骤B。"
        with tempfile.TemporaryDirectory() as tmp:
            case = rich_case()
            rc = case["review_context"]
            rc["claim_hash"] = rc["reviewed_claim_hash"] = strip_ws_hash(claim_text)
            rc.pop("search_claim_hash")
            rc["search_binding"] = {
                "relation": "same_claim_text",
                "search_path": self._evidence(tmp, "一种方法，\n包括：步骤A； 步骤B。　"),
                "input_jsonpath": "request.semantic_query",
                "normalization": "strip_ws_sha256",
            }
            binding = scorer.score_case(case, root=tmp)["version_binding"]
        self.assertEqual(binding["search_binding_basis"], "verified_from_evidence")
        self.assertFalse(binding["stale"])
        self.assertEqual(binding["search_input_jsonpath"], "request.semantic_query")

    def test_jsonpath_detects_different_searched_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = rich_case()
            rc = case["review_context"]
            rc["claim_hash"] = rc["reviewed_claim_hash"] = strip_ws_hash("新权利要求")
            rc["search_binding"] = {
                "search_path": self._evidence(tmp, "旧权利要求"),
                "input_jsonpath": "request.semantic_query",
                "normalization": "strip_ws_sha256",
            }
            result = scorer.score_case(case, root=tmp)
        self.assertTrue(result["version_binding"]["stale"])
        self.assertEqual(result["decision"], "STALE_REVIEW_RESEARCH_REQUIRED")

    def test_missing_jsonpath_field_is_a_visible_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = rich_case()
            case["review_context"]["search_binding"] = {
                "search_path": self._evidence(tmp, "x"), "input_jsonpath": "request.nope",
            }
            result = scorer.score_case(case, root=tmp)
        self.assertIn("search_evidence_missing_jsonpath_field", result["confidence_warnings"])

    def _narrowed(self, searched: bool) -> dict:
        case = rich_case()
        rc = case["review_context"]
        rc["claim_hash"] = rc["reviewed_claim_hash"] = "sha256:narrowed"
        rc["search_binding"] = {
            "relation": "narrowed_from_searched_claim",
            "search_input_hash": "sha256:c1",
            "searched_claim_text_hash": "sha256:c1",
            "new_features_searched": searched,
        }
        return scorer.score_case(case)

    def test_narrowed_with_new_features_searched_is_not_stale(self):
        result = self._narrowed(True)
        binding = result["version_binding"]
        self.assertFalse(binding["stale"])
        self.assertEqual(binding["narrowed_status"], "narrowed_rechecked")
        self.assertNotEqual(result["decision"], "STALE_REVIEW_RESEARCH_REQUIRED")

    def test_narrowed_without_new_feature_search_stays_stale(self):
        result = self._narrowed(False)
        binding = result["version_binding"]
        self.assertTrue(binding["stale"])
        self.assertIn("narrowed_new_features_not_searched", binding["stale_reasons"])
        self.assertEqual(result["decision"], "STALE_REVIEW_RESEARCH_REQUIRED")


class TransitionTests(unittest.TestCase):
    def _case(self, current: dict, previous: dict) -> dict:
        case = rich_case()
        case["review_context"].update(current)
        case["review_context"]["anchor_sha256"] = "anchor"
        case["history"] = [dict({"claim_hash": "sha256:c1", "evidence_hash": "sha256:e1",
                                 "ahp_index": 50.0, "anchor_sha256": "anchor"}, **previous)]
        return case

    def test_non_claim1_text_revision_is_not_same_state(self):
        case = self._case(
            {"independent_claim_hashes": {"1": "c1", "22": "new22"}, "text_bundle_hash": "b2"},
            {"independent_claim_hashes": {"1": "c1", "22": "old22"}, "text_bundle_hash": "b1"},
        )
        transition = scorer.score_case(case)["round_transition"]
        self.assertEqual(transition["type"], "non_claim1_text_revision_fixed_evidence")
        self.assertTrue(transition["controlled_comparison"])
        self.assertEqual(transition["other_independent_claims_changed"], ["22"])
        self.assertTrue(transition["text_bundle_changed"])

    def test_same_state_requires_text_bundle_equality(self):
        same = scorer.score_case(self._case({"text_bundle_hash": "b1"}, {"text_bundle_hash": "b1"}))
        self.assertEqual(same["round_transition"]["type"], "same_state_recheck")
        missing = scorer.score_case(self._case({"text_bundle_hash": "b1"}, {}))
        self.assertEqual(missing["round_transition"]["type"], "unknown")

    def test_argument_only_change_is_applicant_side_not_evidence_shift(self):
        case = self._case(
            {"evidence_hash": "sha256:e2", "evidence_hash_facts": "f1", "argument_hash": "a2",
             "text_bundle_hash": "b1"},
            {"evidence_hash_facts": "f1", "argument_hash": "a1", "text_bundle_hash": "b1"},
        )
        transition = scorer.score_case(case)["round_transition"]
        self.assertEqual(transition["type"], "argument_revision_fixed_evidence")
        self.assertEqual(transition["evidence_basis"], "facts_layer")
        self.assertFalse(transition["evidence_changed"])
        self.assertTrue(transition["combined_evidence_hash_changed"])
        self.assertEqual(transition["applicant_side_changes"], ["argument"])

    def test_facts_change_with_text_change_is_mixed(self):
        case = self._case(
            {"evidence_hash_facts": "f2", "text_bundle_hash": "b2"},
            {"evidence_hash_facts": "f1", "text_bundle_hash": "b1"},
        )
        transition = scorer.score_case(case)["round_transition"]
        self.assertEqual(transition["type"], "mixed_text_and_evidence_shift")
        self.assertFalse(transition["controlled_comparison"])


class AuditWarningTests(unittest.TestCase):
    def _case(self) -> dict:
        case = rich_case()
        case["review_context"]["anchor_sha256"] = "anchor"
        case["history"] = [{
            "claim_hash": "sha256:c1", "evidence_hash": "sha256:e1", "anchor_sha256": "anchor",
            "indicator_scores": {"I4": 4.95, "D3": 6.0},  # current consensus is 4.95
            "evidence_files": ["aa" * 32 + "  01.md", "bb" * 32 + "  mcp.md"],
        }]
        case["review_context"]["evidence_files"] = {"01.md": "x", "mcp.md": "y"}
        return case

    def test_anchor_not_frozen(self):
        case = self._case()
        del case["review_context"]["anchor_sha256"]
        self.assertIn("anchor_not_frozen", scorer.score_case(case)["audit_warnings"])

    def test_clean_round_has_no_audit_warnings(self):
        self.assertNotIn("audit_warnings", scorer.score_case(self._case()))

    def test_effect_score_raised_without_new_data(self):
        case = self._case()
        case["history"][0]["indicator_scores"]["I4"] = 4.0  # consensus 4.95 > 4.0
        self.assertIn("effect_score_raised_without_new_data:I4", scorer.score_case(case)["audit_warnings"])
        case["review_context"]["data_artifact_hashes"] = {"sim.csv": "new"}
        case["history"][0]["data_artifact_hashes"] = {"sim.csv": "new"}
        self.assertIn("effect_score_raised_without_new_data:I4", scorer.score_case(case)["audit_warnings"])
        case["history"][0]["data_artifact_hashes"] = {"sim.csv": "old"}
        self.assertNotIn("audit_warnings", scorer.score_case(case))

    def test_evidence_set_shrunk_and_waiver(self):
        case = self._case()
        case["review_context"]["evidence_files"] = {"01.md": "x"}
        result = scorer.score_case(case)
        self.assertIn("evidence_set_shrunk", result["audit_warnings"])
        self.assertEqual(result["audit_details"]["evidence_removed"], ["mcp.md"])
        case["review_context"]["evidence_removal_waiver"] = "mcp.md 重复取件，见说明"
        waived = scorer.score_case(case)
        self.assertNotIn("audit_warnings", waived)
        self.assertEqual(waived["audit_details"]["evidence_removed"], ["mcp.md"])


class IndependenceAndGateTests(unittest.TestCase):
    def test_all_dependent_roles_flag_disagreement_not_informative(self):
        case = rich_case()
        case["expert_meta"] = {role: {"independent": False} for role in ROLES}
        result = scorer.score_case(case)
        independence = result["expert_independence"]
        self.assertTrue(independence["all_roles_dependent"])
        self.assertIn("disagreement_not_informative", result["audit_warnings"])
        self.assertEqual(independence["role_mean_offset_from_median"]["invalidator"], -1.0)
        self.assertEqual(independence["role_mean_offset_from_median"]["attorney"], 0.5)
        case["expert_meta"]["analyst"]["independent"] = True
        mixed = scorer.score_case(case)
        self.assertEqual(mixed["expert_independence"]["flags"], [])
        self.assertNotIn("audit_warnings", mixed)

    def test_background_gate_warn_and_fail(self):
        absent = scorer.score_case(rich_case())
        self.assertNotIn("background_prior_art_alignment", absent["hard_gates"]["statuses"])
        case = rich_case()
        case["review_context"]["gates"]["background_prior_art_alignment"] = "WARN"
        warn = scorer.score_case(case)
        self.assertIn("background_prior_art_alignment", warn["hard_gates"]["conditional"])
        self.assertEqual(warn["decision"], "CONDITIONAL_EVIDENCE_OR_GATE_REVIEW")
        case["review_context"]["gates"]["background_prior_art_alignment"] = "FAIL"
        fail = scorer.score_case(case)
        self.assertIn("background_prior_art_alignment", fail["hard_gates"]["blocking"])
        self.assertEqual(fail["decision"], "BLOCKED_BY_HARD_GATE")


if __name__ == "__main__":
    unittest.main()
