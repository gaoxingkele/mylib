"""State transitions and recovery using only temporary files and synthetic accounts."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_hub.storage import Store


class StoreTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "hub.sqlite3"
        self.store = Store(self.path)

    @staticmethod
    def event(event_id, **fields):
        return {"event_id": event_id, "task_id": "task", "attempt_id": "a", "account": "account",
                "tool": "codex", "summary": "Synthetic step", "status": "running", **fields}

    def counts(self, *tables):
        with closing(sqlite3.connect(self.path)) as db:
            return tuple(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables)

    def test_concurrent_retry_returns_one_durable_receipt(self):
        event = self.event("same", wiki={"entry_id": "decision", "version": "1", "path": "wiki/page.md", "body": "test"})
        with ThreadPoolExecutor(max_workers=8) as workers:
            receipts = list(workers.map(lambda _: self.store.report_step("p", "hook", event), range(12)))
        self.assertTrue(all(receipt == receipts[0] for receipt in receipts))
        self.assertEqual(self.counts("task_events", "event_receipts", "wiki_entry_versions", "quota_refresh_jobs"), (1, 1, 1, 1))
        with self.assertRaisesRegex(ValueError, "event_id_conflict"):
            self.store.report_step("p", "hook", {**event, "summary": "different"})
        self.assertEqual(Store(self.path).report_step("p", "hook", event), receipts[0])

    def test_wiki_branch_content_conflict_rolls_back_every_write(self):
        def add(event_id, version, parent=None, body="data"):
            wiki = {"entry_id": "decision", "version": version, "parent_version": parent,
                  "path": "wiki/decision.md", "body": body}
            return self.store.report_step("p", "source", self.event(event_id, wiki=wiki))
        add("1", "base")
        add("2", "left", "base")
        add("3", "right", "base")
        self.assertEqual(set(self.store.get_wiki_entry("p", "decision")["heads"]), {"left", "right"})
        self.assertEqual(self.store.get_wiki_entry("p", "decision", "base")["body"], "data")
        with self.assertRaisesRegex(ValueError, "wiki_version_conflict"):
            add("4", "left", "base", body="tampered")
        self.assertEqual(self.counts("event_receipts", "task_events", "quota_refresh_jobs"), (3, 3, 3))
        with self.assertRaisesRegex(ValueError, "wiki_not_found"):
            self.store.get_wiki_entry("other", "decision", "left")

    def test_handoff_compare_and_swap_late_source_and_parallel_verdicts(self):
        def add(source, event_id, **fields):
            return self.store.report_step("p", source, self.event(event_id, **fields))
        add("old", "1", source_seq=2)
        with self.assertRaisesRegex(ValueError, "attempt_owner_conflict"):
            add("intruder", "bad")
        add("new", "2", attempt_id="b", previous_attempt_id="a", source_seq=1, artifact="sha", status="completed")
        with self.assertRaisesRegex(ValueError, "handoff_conflict"):
            add("racer", "3", attempt_id="c", previous_attempt_id="a")
        add("old", "late", source_seq=1, status="blocked")
        for attempt, verdict in (("v1", "pass"), ("v2", "fail")):
            add(attempt, attempt, attempt_id=attempt, role="verify", artifact="sha", verdict=verdict)
        task = self.store.get_task_status("p", "task")
        self.assertEqual((task["primary_attempt_id"], task["status"], task["verification_status"]), ("b", "needs_review", "conflict"))
        self.assertEqual(task["primary_status"], "completed")
        self.assertEqual(next(a["status"] for a in task["attempts"] if a["attempt_id"] == "a"), "running")
        add("v3", "v3", attempt_id="v3", role="verify", artifact="wrong", verdict="pass")
        self.assertEqual(self.store.list_tasks("p", "attention")["tasks"][0]["verification_status"], "baseline_unaligned")
        self.assertEqual(self.store.list_tasks("p", "blocked")["tasks"], [])

    def test_required_verifications_hold_completion_across_handoff(self):
        self.store.report_step("p", "hook", self.event("1", required_verifications=["v1", "v2"]))
        self.store.report_step("p", "hook-2", self.event("2", attempt_id="a2", status="completed",
                              previous_attempt_id="a", artifact="code-sha"))
        for verifier in ("v1", "v2"):
            current = self.store.list_tasks("p", "attention")["tasks"][0]
            self.assertEqual(current["status"], "awaiting_verification")
            self.assertEqual((current["event_id"], current["source"]), ("2", "hook-2"))
            self.store.report_step("p", verifier, self.event(verifier, attempt_id=verifier, role="verify",
                                   artifact="code-sha", verdict="pass"))
        completed = self.store.list_tasks("p", "completed")["tasks"][0]
        self.assertEqual(completed["verification_status"], "passed")
        self.assertEqual(self.store.list_tasks("p", "attention")["tasks"], [])

    def test_project_isolation_and_limit_cursor(self):
        for i in range(5):
            self.store.report_step("p", "source", self.event(str(i), task_id=f"t{i}"))
        self.store.report_step("other", "source", self.event("1", task_id="secret"))
        one = self.store.list_tasks("p", limit=3)
        two = self.store.list_tasks("p", limit=3, before=one["next_before"])
        self.assertEqual([t["task_id"] for t in one["tasks"]+two["tasks"]], ["t4", "t3", "t2", "t1", "t0"])
        self.assertIsNone(two["next_before"])
        self.assertEqual(self.store.search_task_events("other")["events"][0]["task_id"], "secret")
        self.assertFalse(self.store.search_task_events("other", query="t1")["events"])

    def test_only_normalized_metadata_is_persisted(self):
        for extra in ({"raw_transcript":"synthetic test payload"}, {"skills":[{"access_key":"synthetic"}]},
                      {"generation":{"unsafe":"raw"}}, {"source":"some-other-machine"}):
            with self.assertRaises(ValueError):
                self.store.report_step("p", "source", self.event("tested", **extra))
        self.assertEqual(self.counts("task_events", "event_receipts", "quota_refresh_jobs"), (0, 0, 0))
        event = self.event("tested", skills=[{"skill_id":"test-skill", "revision":"abc"}],
                           evidence=["fixture"], generation="local-1")
        self.store.report_step("p", "source", event)
        self.assertEqual(self.store.search_task_events("p")["events"][0]["skills"], event["skills"])

    def test_hook_to_store_preserves_and_freezes_host_feedback_binding(self):
        from agent_hub.hooks import HookQueue

        project = self.path.parent / "project"
        project.mkdir()
        target = {"host_installation_id": "sma-install-a", "terminal_session_id": "terminal-a",
                  "journal_id": "journal-a", "window_id": "window-a", "generation": "3"}
        queue = HookQueue(dict(project_root=str(project), state_dir=str(self.path.parent / "queue"),
                               project="p", attempt_id="a", task_id="task", account="account",
                               tool="codex", host="host-alias", window="Visible title", **target))
        queue.enqueue(dict(hook_event_name="Stop", turn_id="one", session_id="provider-session",
                           cwd=str(project), last_assistant_message="HUB-REPORT: Verified binding"))

        def report(name, args):
            self.assertEqual(name, "report_step")
            return self.store.report_step(args["project"], "hook", args["event"])

        self.assertEqual(queue.flush(report), 1)
        attempt = self.store.get_task_status("p", "task")["attempts"][0]
        self.assertEqual({key: attempt[key] for key in target}, target)
        self.assertEqual(attempt["session_id"], "provider-session")
        for field in ("host_installation_id", "terminal_session_id", "journal_id"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "attempt_identity_conflict"):
                self.store.report_step("p", "hook", self.event("forged", source_seq=2, **{field:"another"}))
        self.assertEqual(self.counts("task_events", "quota_refresh_jobs"), (1, 1))

    def test_scoped_lease_idempotent_snapshot_and_no_refresh_recursion(self):
        a = self.store.report_step("p", "hook", self.event("e"))
        job = self.store.claim_usage_job("p", "account", "collector")
        self.assertEqual(a["usage_job_id"], job["job_id"])
        self.assertIsNone(self.store.claim_usage_job("p", "account", "second"))
        snap = {"job_id": job["job_id"], "lease_token": job["lease_token"], "status": "ok",
              "observed_at": job["claimed_at"], "windows": [{"period": "weekly", "unit": "percent", "remaining": 73, "reset_at": None}]}
        with self.assertRaisesRegex(ValueError, "invalid_or_expired_lease"):
            self.store.record_usage_snapshot("p", "other", snap)
        with self.assertRaisesRegex(ValueError, "invalid_or_expired_lease"):
            self.store.record_usage_snapshot("other", "account", snap)
        with self.assertRaisesRegex(ValueError, "snapshot_binding_mismatch"):
            self.store.record_usage_snapshot("p", "account", {**snap, "account": "foreign"})
        with self.assertRaisesRegex(ValueError, "invalid_sample_time"):
            self.store.record_usage_snapshot("p", "account", {**snap, "observed_at": "2020-01-01T00:00:00Z"})
        result = self.store.record_usage_snapshot("p", "account", snap)
        self.assertEqual(self.store.record_usage_snapshot("p", "account", snap), result)
        with self.assertRaisesRegex(ValueError, "snapshot_conflict"):
            self.store.record_usage_snapshot("p", "account", {**snap, "source": "another"})
        self.assertEqual(self.counts("quota_refresh_jobs", "quota_snapshots"), (1, 1))
        self.assertIsNone(self.store.claim_usage_job("p", "account", "worker"))
        current = self.store.get_usage_overview("p")["accounts"][0]
        self.assertEqual(current["latest"]["windows"][0]["remaining"], 73)
        self.assertNotIn("lease_token", current["latest"])

    def test_lease_expiry_and_failure_retains_last_success(self):
        def step(i):
            self.store.report_step("p", "source", self.event(i))
            return self.store.claim_usage_job("p", "account", "collector")
        first = step("a")
        snap = {"job_id": first["job_id"], "lease_token": first["lease_token"], "status": "ok",
              "observed_at": first["claimed_at"], "windows": [{"period": "weekly", "unit": "percent", "remaining": 98}]}
        self.store.record_usage_snapshot("p", "account", snap)
        failed = step("b")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE quota_refresh_jobs SET lease_until=0 WHERE job_id=?", (failed["job_id"],))
        replacement = self.store.claim_usage_job("p", "account", "other-worker")
        blocked = {"job_id": failed["job_id"], "lease_token": failed["lease_token"], "status": "rate_limited",
                 "observed_at": replacement["claimed_at"], "windows": [], "retry_after_seconds": 90}
        with self.assertRaisesRegex(ValueError, "invalid_or_expired_lease"):
            self.store.record_usage_snapshot("p", "account", blocked)
        self.store.record_usage_snapshot("p", "account", {**blocked, "lease_token": replacement["lease_token"]})
        self.assertIsNone(self.store.claim_usage_job("p", "account", "collector"))
        current = self.store.get_usage_overview("p")["accounts"][0]
        self.assertEqual(current["latest"]["status"], "rate_limited")
        self.assertEqual(current["last_success"]["windows"][0]["remaining"], 98)

    def test_seal_refuses_all_writes_allows_existing_reads(self):
        self.store.report_step("p", "source", self.event("a"))
        job = self.store.claim_usage_job("p", "account", "q")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO hub_maintenance VALUES(1,'test seal')")
        stamp = datetime.now(timezone.utc).isoformat()
        for operation in (lambda: self.store.report_step("p", "source", self.event("b")),
                          lambda: self.store.claim_usage_job("p", "account", "q"),
                          lambda: self.store.record_usage_snapshot("p", "account",
                              {"job_id": job["job_id"], "lease_token": job["lease_token"], "status": "unavailable", "observed_at": stamp})):
            with self.assertRaisesRegex(ValueError, "database_sealed"):
                operation()
        self.assertEqual(Store(self.path).get_task_status("p", "task")["status"], "running")

    def test_idle_poll_is_atomic_throttled_and_creates_no_task_events(self):
        def claim():
            return self.store.claim_usage_job("p", "account", "q", idle_after_seconds=300)

        for interval in (True, -1, 0, 59, 604801):
            with self.assertRaisesRegex(ValueError, "invalid_idle_interval"):
                self.store.claim_usage_job("p", "account", "q", interval)
        with self.assertRaisesRegex(ValueError, "reserved_source"):
            self.store.report_step("p", "__quota_monitor__", self.event("forged"))
        with patch("agent_hub.storage.time.time", return_value=1700000000):
            with ThreadPoolExecutor(max_workers=4) as workers:
                claims = [r for r in workers.map(lambda _: claim(), range(4)) if r]
            self.assertEqual(len(claims), 1)
            job = claims[0]
            self.assertEqual((job["trigger"], job["event_id"]), ("scheduled", None))
            self.store.record_usage_snapshot("p", "account", {
                "job_id":job["job_id"], "lease_token":job["lease_token"], "status":"ok",
                "observed_at":job["claimed_at"], "windows":[{"period":"weekly","unit":"percent","remaining":67}],
            })
        with patch("agent_hub.storage.time.time", return_value=1700000299):
            self.assertIsNone(claim())
        with patch("agent_hub.storage.time.time", return_value=1700000300):
            self.assertEqual(claim()["trigger"], "scheduled")
        self.assertEqual(self.store.get_usage_overview("p")["accounts"][0]["last_success"]["windows"][0]["remaining"],67)
        self.assertEqual(self.store.list_tasks("p")["tasks"],[])
        self.assertEqual(self.store.search_task_events("p")["events"],[])
        self.assertEqual(self.counts("task_attempts","task_current","task_events"), (0,0,0))

    def test_old_snapshot_cannot_replace_newer_after_late_worker_return(self):
        first = self.store.report_step("p", "source", self.event("1"))
        old = self.store.claim_usage_job("p", "account", "slow")
        self.store.report_step("p", "source", self.event("2"))
        new = self.store.claim_usage_job("p", "account", "fast", idle_after_seconds=900)
        self.assertEqual((new["trigger"], new["event_id"]), ("step", "2"))
        for job, remaining in ((new,98),(old,2)):
            self.store.record_usage_snapshot("p","account", {
                "job_id":job["job_id"], "lease_token":job["lease_token"], "status":"ok",
                "observed_at":job["claimed_at"], "windows":[{"period":"weekly","unit":"percent","remaining":remaining}],
            })
        current = self.store.get_usage_overview("p")["accounts"][0]["latest"]
        self.assertEqual(current["job_id"],new["job_id"])
        self.assertNotEqual(current["job_id"],first["seq"])


if __name__ == "__main__":
    unittest.main()
