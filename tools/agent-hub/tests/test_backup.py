from contextlib import closing
from datetime import datetime, timezone
import shutil
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from agent_hub.backup import backup, restore, rollback, rotate, verify
from agent_hub.storage import Store


def step(number, **extra):
    return {"event_id": f"step-{number}", "task_id": "task-a", "attempt_id": "run-1",
            "account": "fixture-account", "tool": "codex", "status": "running",
            "summary": f"synthetic step {number}", "source_seq": number, **extra}


class MaintenanceTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "source.sqlite3"
        self.store = Store(self.source)
        self.archive = self.root / "backup"
        self.generation = self.root / "generation"

    def report(self, event, store=None):
        return (store or self.store).report_step("p", "machine", event)

    def finish_job(self):
        job = self.store.claim_usage_job("p", "fixture-account", "worker")
        return self.store.record_usage_snapshot("p", "fixture-account", {
            "job_id": job["job_id"], "lease_token": job["lease_token"], "status": "ok",
            "observed_at": datetime.now(timezone.utc).isoformat(), "pool": "weekly",
            "windows": [{"period": "week", "unit": "percent", "remaining": 55}],
        })

    def test_backup_is_point_in_time_and_restore_requires_a_new_destination(self):
        receipt = self.report(step(1))
        metadata = backup(self.source, self.archive)
        self.report(step(2))
        self.assertEqual(verify(self.archive), metadata)
        self.assertEqual(metadata["sequence"], receipt["seq"])
        with self.assertRaises(FileExistsError):
            restore(self.archive, self.source)
        new = self.root / "restored.sqlite3"
        details = restore(self.archive, new)
        self.assertEqual(details["counts"]["task_events"], 1)
        self.assertEqual(self.report(step(1), Store(new)), receipt)
        self.assertEqual(self.report(step(2))["seq"], 2)

    def test_digest_failure_leaves_new_destination_absent(self):
        self.report(step(1))
        backup(self.source, self.archive)
        with (self.archive / "snapshot.sqlite3").open("ab") as f:
            f.write(b"tamper")
        dest = self.root / "restore.sqlite3"
        with self.assertRaisesRegex(ValueError, "snapshot_digest_mismatch"):
            restore(self.archive, dest)
        self.assertFalse(dest.exists())

    def test_online_snapshot_reads_committed_wal_and_ignores_uncommitted_transaction(self):
        with closing(sqlite3.connect(self.source)) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            self.report(step(1))
            writer.execute("BEGIN IMMEDIATE")
            writer.execute("UPDATE task_events SET summary='uncommitted'")
            metadata = backup(self.source, self.archive)
            writer.rollback()
        self.assertEqual(metadata["sequence"], 1)
        with closing(sqlite3.connect(self.archive / "snapshot.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT summary FROM task_events").fetchone()[0], "synthetic step 1")

    def test_missing_activated_database_requires_reconciliation(self):
        self.report(step(1))
        result = rotate(self.source, self.generation)
        self.report(step(2), Store(result["active"]))
        Path(result["active"]).rename(self.root / "simulated-lost.sqlite3")
        with self.assertRaisesRegex(ValueError, "missing_reconciliation_required"):
            rollback(self.source, self.generation)
        with self.assertRaisesRegex(ValueError, "database_sealed"):
            self.report(step(3))

    def test_rotation_preserves_idempotency_pending_status_quota_and_wiki_heads(self):
        old = time.time() - 10 * 86400
        def note(version, parent=None):
            return {"entry_id": "entry", "path": "wiki/task.md", "version": version,
                    "parent_version": parent, "body": "version " + version}
        with patch("agent_hub.storage.time.time", return_value=old):
            receipt = self.report(step(1, wiki=note("v1")))
            for n in range(2, 8):
                self.report(step(n))
        for _ in range(7):
            self.finish_job()
        self.report(step(8, wiki=note("v2", "v1")))
        self.report(step(9, wiki=note("fork", "v1")))
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute("UPDATE quota_snapshots SET observed_at=? WHERE snapshot_id<7", (old,))
        original_task = self.store.get_task_status("p", "task-a")
        original_usage = self.store.get_usage_overview("p")
        result = rotate(self.source, self.generation)
        self.assertEqual(verify(self.generation / "archive")["counts"]["task_events"], 9)
        self.assertLess(result["counts"]["task_events"], 9)
        with self.assertRaisesRegex(ValueError, "database_sealed"):
            self.report(step(10))
        new = Store(result["active"])
        self.assertEqual(new.get_task_status("p", "task-a"), original_task)
        self.assertEqual(new.get_usage_overview("p"), original_usage)
        self.assertEqual(new.get_wiki_entry("p", "entry", "v2")["body"], "version v2")
        self.assertEqual(new.get_wiki_entry("p", "entry", "fork")["body"], "version fork")
        self.assertEqual(self.report(step(1, wiki=note("v1")), new), receipt)
        self.assertEqual(new.claim_usage_job("p", "fixture-account", "new-worker")["event_id"], "step-8")
        self.assertEqual(self.report(step(10), new)["seq"], 10)
        with self.assertRaisesRegex(ValueError, "reconciliation_required"):
            rollback(self.source, self.generation)
        with self.assertRaisesRegex(ValueError, "database_sealed"):
            self.report(step(11))

    def test_rollback_without_new_writes_reopens_old_and_seals_new(self):
        self.report(step(1))
        result = rotate(self.source, self.generation)
        self.assertEqual(rollback(self.source, self.generation)["active"], str(self.source))
        self.assertEqual(self.report(step(2))["seq"], 2)
        with self.assertRaisesRegex(ValueError, "database_sealed"):
            self.report(step(2), Store(result["active"]))

    def test_failed_backup_leaves_original_recoverable(self):
        self.report(step(1))
        with patch("agent_hub.backup.backup", side_effect=OSError("simulated disk full")):
            with self.assertRaises(OSError):
                rotate(self.source, self.generation)
        with self.assertRaisesRegex(ValueError, "database_sealed"):
            self.report(step(2))
        self.assertFalse((self.generation / "active.sqlite3").exists())
        rollback(self.source, self.generation)
        self.assertEqual(self.report(step(2))["seq"], 2)

    def test_low_disk_preflight_keeps_source_writable(self):
        self.report(step(1))
        disk = shutil.disk_usage(self.root)._replace(free=0)
        with patch("agent_hub.backup.shutil.disk_usage", return_value=disk):
            with self.assertRaisesRegex(ValueError, "insufficient_rotation_space"):
                rotate(self.source, self.generation)
        self.assertEqual(self.report(step(2))["seq"], 2)

    def test_aged_wiki_forks_are_searchable_and_current_tasks_keep_latest_evidence(self):
        old = time.time() - 45 * 86400
        for seq, version, parent in ((1, "a", None), (2, "b", "a"), (3, "c", "a")):
            event = step(seq, wiki={"entry_id": "decision", "version": version,
                                   "parent_version": parent, "path": "wiki/decision.md", "body": version})
            self.report(event)
            self.finish_job()
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute("UPDATE event_receipts SET accepted_at=?", (old,))
            db.execute("UPDATE quota_snapshots SET observed_at=?", (old,))
        result = rotate(self.source, self.generation)
        new = Store(result["active"])
        self.assertEqual(verify(self.generation / "archive")["counts"]["wiki_entry_versions"], 3)
        self.assertEqual(result["counts"]["wiki_entry_versions"], 2)
        self.assertEqual(result["counts"]["event_receipts"], 2)
        self.assertEqual(new.get_task_status("p", "task-a")["primary_attempt_id"], "run-1")
        self.assertEqual(new.get_wiki_entry("p", "decision", "b")["body"], "b")
        self.assertEqual(new.get_wiki_entry("p", "decision", "c")["body"], "c")
        self.assertEqual(self.report(step(4), new)["seq"], 4)


if __name__ == "__main__":
    unittest.main()
