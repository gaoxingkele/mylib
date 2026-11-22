"""Synthetic fixtures for the evaluation, publication and receipt protocols."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from agent_hub.evolution import (
    EvolutionError, EvolutionLedger, WAITING_BASELINE_VERSION, WAITING_CANDIDATE_VERSION,
    waiting_alert,
)


BASE = WAITING_BASELINE_VERSION
CANDIDATE = WAITING_CANDIDATE_VERSION
SCOPE = {"project_id": "fixture-project", "tool": "codex", "tool_version": "0.1"}
SKILL = "hub-alerts"
ACTOR = "fixture-operator"


def cohort(prefix, count):
    cases = []
    for label in ("blocked", "clear"):
        for index in range(count):
            key = f"{prefix}-{label}-{index}"
            cases.append({
                "evidence_id": key, "group_id": key, "label": label,
                "observable": True, "quiet_ms": 300_000,
                "signal": "blocked" if label == "blocked" else None,
                "signal_delay_ms": 1_000 if label == "blocked" else None,
                "trusted_current": label == "blocked",
            })
    return cases


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.file = Path(tmp.name) / "evolution.sqlite"
        self.now = 1_000
        self.store = EvolutionLedger(self.file, allow_fixture_promotion=True, clock=lambda: self.now)
        self.store.register_baseline(SCOPE, SKILL, BASE, ACTOR)

    def propose(self, scope=SCOPE, skill=SKILL, evidence_kind="fixture", candidate_id="rule"):
        self.store.propose(scope, skill, candidate_id, version=CANDIDATE, parent_version=BASE,
                           development_id="dev", heldout_id="hold", actor=ACTOR,
                           evidence_kind=evidence_kind)

    def assess(self, scope=SCOPE, skill=SKILL):
        self.propose(scope, skill)
        self.store.evaluate(scope, skill, "rule", "development", "dev", cohort("dev", 10), ACTOR)
        return self.store.evaluate(scope, skill, "rule", "heldout", "hold", cohort("hold", 60), ACTOR)

    def release(self, scope=SCOPE, skill=SKILL):
        proof = self.assess(scope, skill)
        self.store.promote(scope, skill, "rule", ACTOR, evaluation_digest=proof["evaluation_digest"])
        return proof

    def old_attempt(self):
        self.store.pin_attempt(SCOPE, SKILL, "attempt-a", 1, ACTOR)
        self.store.record_loading(SCOPE, SKILL, "attempt-a", 1, BASE, "fixture-host")

    def test_waiting_signal_distinguishes_observation_from_blocking(self):
        observation = dict(observable=True, quiet_ms=300_001, signal=None, trusted_current=False)
        self.assertEqual(waiting_alert(BASE, **observation), "blocked")
        self.assertEqual(waiting_alert(CANDIDATE, **observation), "observing")
        self.assertEqual(waiting_alert(CANDIDATE, **{**observation, "observable": False}), "unknown")
        for signal in ("blocked", "waiting", "limited"):
            trusted = {**observation, "signal": signal, "trusted_current": True}
            self.assertEqual(waiting_alert(CANDIDATE, **trusted), signal)
            self.assertEqual(waiting_alert(CANDIDATE, **{**trusted, "trusted_current": False}), "observing")

    def test_fixture_reports_are_labeled_and_cannot_produce_normal_release(self):
        sandbox = self.store
        self.store = EvolutionLedger(self.file.with_name("ordinary.sqlite"))
        self.store.register_baseline(SCOPE, SKILL, BASE, ACTOR)
        proof = self.assess()
        self.assertEqual(proof["evidence_kind"], "fixture")
        self.assertEqual(proof["splits"]["heldout"]["verdict"], "passed")
        self.assertEqual(proof["splits"]["heldout"]["fixed_false_alerts"], 60)
        self.assertEqual(proof["splits"]["heldout"]["false_alert_rate_reduction"], 1)
        with self.assertRaisesRegex(EvolutionError, "fixture"):
            self.store.promote(SCOPE, SKILL, "rule", ACTOR, evaluation_digest=proof["evaluation_digest"])
        self.assertEqual(self.store.get_status(SCOPE, SKILL)["published_version"], BASE)
        with self.assertRaisesRegex(EvolutionError, "separate databases"):
            EvolutionLedger(sandbox.path)

    def test_authorized_evidence_requires_independent_verifier(self):
        self.store = EvolutionLedger(self.file.with_name("ordinary.sqlite"))
        self.store.register_baseline(SCOPE, SKILL, BASE, ACTOR)
        self.propose(evidence_kind="authorized")
        samples = cohort("dev", 10)
        with self.assertRaisesRegex(EvolutionError, "could not be verified"):
            self.store.evaluate(SCOPE, SKILL, "rule", "development", "dev", samples, ACTOR)
        rejecting = EvolutionLedger(self.store.path, verify_evidence=lambda scope, case: case != samples[0])
        with self.assertRaisesRegex(EvolutionError, "could not be verified"):
            rejecting.evaluate(SCOPE, SKILL, "rule", "development", "dev", samples, ACTOR)

    def test_version_must_match_evaluated_policy(self):
        with self.assertRaisesRegex(EvolutionError, "fixed policy pair"):
            self.store.propose(SCOPE, SKILL, "wrong", version="a" * 64, parent_version=BASE,
                               development_id="dev", heldout_id="hold", actor=ACTOR)

    def test_holdout_is_once_only_and_disjoint_at_group_level(self):
        self.propose()
        cases = cohort("dev", 10)
        first = self.store.evaluate(SCOPE, SKILL, "rule", "development", "dev", cases, ACTOR)
        retry = self.store.evaluate(SCOPE, SKILL, "rule", "development", "dev", cases[::-1], ACTOR)
        self.assertEqual(retry, first)
        with self.assertRaisesRegex(EvolutionError, "differs"):
            self.store.evaluate(SCOPE, SKILL, "rule", "heldout", "other-window", cohort("hold", 60), ACTOR)
        holdout = cohort("hold", 60)
        holdout[0]["group_id"] = cases[0]["group_id"]
        with self.assertRaisesRegex(EvolutionError, "overlaps"):
            self.store.evaluate(SCOPE, SKILL, "rule", "heldout", "hold", holdout, ACTOR)
        holdout = cohort("hold", 60)
        result = self.store.evaluate(SCOPE, SKILL, "rule", "heldout", "hold", holdout, ACTOR)
        self.assertEqual(result["splits"]["heldout"]["verdict"], "passed")
        with self.assertRaisesRegex(EvolutionError, "different evidence"):
            self.store.evaluate(SCOPE, SKILL, "rule", "heldout", "hold", cohort("new", 60), ACTOR)

    def test_observed_safety_failure_and_small_sample_do_not_release(self):
        for case_count, expected in ((60, "rejected"), (59, "insufficient_evidence")):
            with self.subTest(expected=expected):
                scope = {**SCOPE, "tool_version": expected}
                self.store.register_baseline(scope, SKILL, BASE, ACTOR)
                self.propose(scope)
                self.store.evaluate(scope, SKILL, "rule", "development", "dev", cohort("dev", 10), ACTOR)
                holdout = cohort("hold", case_count)
                if expected == "rejected":
                    holdout[0]["signal"] = None
                    holdout[0]["trusted_current"] = False
                    holdout[0]["signal_delay_ms"] = None
                result = self.store.evaluate(scope, SKILL, "rule", "heldout", "hold", holdout, ACTOR)
                self.assertEqual(result["splits"]["heldout"]["verdict"], expected)
                with self.assertRaisesRegex(EvolutionError, "does not authorize"):
                    self.store.promote(scope, SKILL, "rule", ACTOR, evaluation_digest=result["evaluation_digest"])

    def test_revocation_invalidates_proof_and_rechecks_only_affected_scope(self):
        other = {**SCOPE, "tool": "claude"}
        self.store.register_baseline(other, SKILL, BASE, ACTOR)
        proof = self.release()
        self.release(other)
        revoked = "hold-blocked-0"
        result = self.store.revoke_evidence(SCOPE, revoked, ACTOR)
        self.assertEqual(result["rolled_back"], {SKILL: BASE})
        status = self.store.get_status(SCOPE, SKILL, candidate_id="rule")
        report = status["assessment"]
        self.assertTrue(report["splits"]["heldout"]["evidence_revoked"])
        self.assertNotIn(revoked, str(report))
        self.assertNotEqual(report["evaluation_digest"], proof["evaluation_digest"])
        self.assertEqual(self.store.get_status(other, SKILL)["published_version"], CANDIDATE)
        with self.assertRaisesRegex(EvolutionError, "does not authorize"):
            self.store.promote(SCOPE, SKILL, "rule", ACTOR, evaluation_digest=proof["evaluation_digest"])
        statuses = {row["tool"]: row for row in self.store.list_status(SCOPE["project_id"])["items"]}
        self.assertEqual(statuses["codex"]["state"], "insufficient_evidence")
        self.assertTrue(statuses["codex"]["evidence_revoked"])
        self.assertEqual(statuses["claude"]["state"], "published")
        self.assertNotIn(revoked, str(statuses))
        self.assertEqual(self.store.list_status("foreign-project"), {"items": []})

    def test_followup_uses_new_trial_and_never_reopens_old_holdout(self):
        self.release()
        self.store.rollback(SCOPE, SKILL, CANDIDATE, ACTOR)
        self.store.propose(SCOPE, SKILL, "followup", version=CANDIDATE, parent_version=BASE,
                           development_id="dev", heldout_id="future-hold", actor=ACTOR,
                           evidence_kind="fixture")
        self.store.evaluate(SCOPE, SKILL, "followup", "development", "dev", cohort("dev", 10), ACTOR)
        with self.assertRaisesRegex(EvolutionError, "overlaps"):
            self.store.evaluate(SCOPE, SKILL, "followup", "heldout", "future-hold", cohort("hold", 60), ACTOR)
        result = self.store.evaluate(SCOPE, SKILL, "followup", "heldout", "future-hold", cohort("new", 60), ACTOR)
        self.store.promote(SCOPE, SKILL, "followup", ACTOR, evaluation_digest=result["evaluation_digest"])
        self.assertEqual(self.store.get_status(SCOPE, SKILL)["published_candidate_id"], "followup")

    def test_publish_is_not_loading_and_only_host_receipt_changes_actual(self):
        self.old_attempt()
        self.release()
        args = (SCOPE, SKILL, "attempt-a", 1)
        status = self.store.get_status(SCOPE, SKILL, attempt_id="attempt-a", generation=1)
        self.assertTrue(status["has_update"])
        self.assertEqual(status["loaded_version"], BASE)
        self.store.confirm_loading(*args, CANDIDATE, "request", ACTOR)
        with self.assertRaisesRegex(EvolutionError, "conflicts"):
            self.store.record_loading(*args, CANDIDATE, "fixture-host", request_id="request")
        self.assertTrue(self.store.authorize_loading(*args, CANDIDATE, "request", ACTOR)["dispatch"])
        self.assertFalse(self.store.authorize_loading(*args, CANDIDATE, "request", ACTOR)["dispatch"])
        self.store.record_loading(*args, CANDIDATE, "fixture-host", request_id="request", result="pending_restart")
        status = self.store.get_status(SCOPE, SKILL, attempt_id="attempt-a", generation=1)
        self.assertEqual((status["loading_state"], status["loaded_version"]), ("pending_restart", BASE))
        self.store.record_loading(*args, CANDIDATE, "fixture-host", request_id="request")
        late = self.store.record_loading(*args, CANDIDATE, "fixture-host", request_id="request",
                                         result="pending_restart")
        self.assertTrue(late["replayed"])
        self.store.rollback(SCOPE, SKILL, CANDIDATE, ACTOR)
        status = self.store.get_status(SCOPE, SKILL, attempt_id="attempt-a", generation=1)
        self.assertEqual((status["published_version"], status["loaded_version"]), (BASE, CANDIDATE))

    def test_generation_and_expiration_prevent_old_requests_dispatch(self):
        self.old_attempt()
        self.release()
        old = (SCOPE, SKILL, "attempt-a", 1)
        self.store.confirm_loading(*old, CANDIDATE, "expires", ACTOR, ttl_seconds=1)
        self.now += 1
        self.assertFalse(self.store.authorize_loading(*old, CANDIDATE, "expires", ACTOR)["dispatch"])
        self.store.confirm_loading(*old, CANDIDATE, "old-generation", ACTOR)
        pinned = self.store.pin_attempt(SCOPE, SKILL, "attempt-a", 2, ACTOR)
        self.assertEqual(pinned["pinned_version"], BASE)
        with self.assertRaisesRegex(EvolutionError, "stale"):
            self.store.authorize_loading(*old, CANDIDATE, "old-generation", ACTOR)
        with self.assertRaisesRegex(EvolutionError, "target or version changed"):
            self.store.authorize_loading(SCOPE, SKILL, "attempt-a", 2, CANDIDATE, "old-generation", ACTOR)
        new = self.store.pin_attempt(SCOPE, SKILL, "attempt-b", 1, ACTOR)
        self.assertEqual(new["pinned_version"], CANDIDATE)
        status = self.store.get_status(SCOPE, SKILL, attempt_id="attempt-b", generation=1)
        self.assertIsNone(status["loaded_version"])

    def test_two_dispatched_retries_return_a_single_authorization(self):
        self.old_attempt()
        self.release()
        args = (SCOPE, SKILL, "attempt-a", 1, CANDIDATE, "request", ACTOR)
        self.store.confirm_loading(*args)
        with ThreadPoolExecutor(2) as executor:
            results = list(executor.map(lambda _: self.store.authorize_loading(*args)["dispatch"], range(2)))
        self.assertEqual(sorted(results), [False, True])

    def test_release_changes_invalidate_unspent_confirmation(self):
        self.old_attempt()
        release = self.release()
        args = (SCOPE, SKILL, "attempt-a", 1, CANDIDATE, "old", ACTOR)
        self.store.confirm_loading(*args)
        self.store.rollback(SCOPE, SKILL, CANDIDATE, ACTOR)
        self.store.promote(SCOPE, SKILL, "rule", ACTOR, evaluation_digest=release["evaluation_digest"])
        self.assertEqual(self.store.authorize_loading(*args), {"dispatch": False, "state": "expired"})

    def test_local_operator_cli_reports_labeled_scope(self):
        arguments = self.file.with_suffix(".json")
        arguments.write_text(json.dumps({"project_id": SCOPE["project_id"]}), encoding="utf-8")
        command = [sys.executable, "-B", "-m", "agent_hub.evolution", "--db", str(self.file)]
        refused = subprocess.run([*command, "list_status", str(arguments)], capture_output=True, text=True,
                                 check=False)
        self.assertEqual(refused.returncode, 2)
        result = subprocess.run([*command, "--fixture-sandbox", "list_status", str(arguments)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)["items"][0]["state"], "baseline")
