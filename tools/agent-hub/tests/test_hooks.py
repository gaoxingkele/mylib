import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from agent_hub.hooks import HookQueue, adapt, binding


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "project"
        self.root.mkdir()
        self.config = dict(project_root=str(self.root), state_dir=str(base / "state"),
                           project="sample", attempt_id="a", task_id="t", account="owner",
                           tool="codex", host="machine-a", window="window-a", generation="1")
        self.stop = dict(hook_event_name="Stop", session_id="session-a", turn_id="turn-a",
                         cwd=str(self.root), last_assistant_message="Private introduction.\nHUB-REPORT: verified fixture")
        self.queue = HookQueue(self.config)

    @staticmethod
    def receipt(_name, arguments):
        event = arguments["event"]
        return {**{k: event[k] for k in ("event_id", "task_id", "attempt_id")}, "seq": 7}

    def test_native_content_minimization_and_stable_turn(self):
        event = adapt(self.queue.config, self.stop)
        self.assertEqual("verified fixture", event["summary"])
        self.assertNotIn("Private introduction", json.dumps(event))
        self.assertEqual(event["event_id"], adapt(self.queue.config, self.stop)["event_id"])
        for tool in ("codex", "claude"):
            config = binding({**self.config, "tool": tool})
            plain_stop = {**self.stop, "last_assistant_message": "private transcript"}
            self.assertNotIn("private transcript", json.dumps(adapt(config, plain_stop)))
            secret = {**self.stop, "last_assistant_message": "HUB-REPORT: token=SYNTHETIC_TEST_SECRET"}
            self.assertNotIn("SYNTHETIC_TEST_SECRET", json.dumps(adapt(config, secret)))
            secret["last_assistant_message"] = "HUB-REPORT: Authorization: Bearer SYNTHETIC_TEST_SECRET"
            self.assertNotIn("SYNTHETIC_TEST_SECRET", json.dumps(adapt(config, secret)))
        report = self.queue.enqueue(self.stop)
        self.assertEqual(report, self.queue.enqueue(self.stop))
        with self.assertRaises(ValueError):
            self.queue.enqueue({**self.stop, "last_assistant_message": "HUB-REPORT: different result"})
        self.assertEqual(1, self.queue.status()["pending"])

    def test_grok_native_protocol_and_other_tools_manual_fallback(self):
        grok = HookQueue({**self.config, "tool": "grok"})
        actual = dict(hookEventName="StopFailure", sessionId="grok-s", cwd=str(self.root))
        self.assertEqual("blocked", adapt(grok.config, actual)["status"])
        self.assertIsNone(adapt(grok.config, self.stop))
        custom = HookQueue({**self.config, "tool": "other-cli"})
        with self.assertRaises(ValueError):
            custom.enqueue(self.stop)
        self.assertTrue(custom.enqueue(dict(step_id="s1", summary="manual result", evidence=["commit/fixture"]), manual=True))

    def test_nonproject_events_and_mcp_calls_are_ignored(self):
        self.assertIsNone(self.queue.enqueue({**self.stop, "cwd": str(self.root.parent)}))
        self.assertIsNone(self.queue.enqueue({**self.stop, "hook_event_name":"PostToolUse",
                                              "tool_name":"mcp__agenthub__report_step", "tool_input":{"token":"secret"}}))
        with self.assertRaises(ValueError):
            binding({**self.config, "wiki_dir": "../outside"})
        with self.assertRaises(ValueError):
            binding({**self.config, "state_dir": str(self.root / "state")})
        self.assertIsNone(adapt(binding({**self.config, "session_id": "another"}), self.stop))

    def test_wiki_precedes_network_and_duplicate_retry_uses_same_event(self):
        event_id = self.queue.enqueue(self.stop)
        wiki = self.root / "omx_wiki" / "agent-results" / (event_id + ".md")
        captured = []

        def lost_ack(name, args):
            captured.append(args)
            self.assertEqual("report_step", name)
            self.assertEqual(wiki.read_bytes(), args["event"]["wiki"]["body"].encode())
            raise TimeoutError

        with self.assertRaises(TimeoutError):
            self.queue.flush(lost_ack)
        recovered = HookQueue(self.config)
        def success(name, args):
            self.assertEqual(captured[0], args)
            return self.receipt(name, args)
        self.assertEqual(1, recovered.flush(success))
        self.assertEqual(0, recovered.flush(success))
        self.assertEqual(1, recovered.status()["delivered"])

    def test_recovery_after_failed_wiki_write_and_bad_receipt(self):
        with patch.object(self.queue, "write_wiki", side_effect=OSError):
            with self.assertRaises(OSError):
                self.queue.enqueue(self.stop)
        queue = HookQueue(self.config)
        self.assertEqual(1, queue.status()["pending"])
        with self.assertRaises(ValueError):
            queue.flush(lambda name, args: {"seq": 4, "event_id": "another"})
        self.assertEqual(1, queue.flush(self.receipt))
        pages = list(self.root.rglob("*.md"))
        self.assertEqual(1, len(pages))
        pages[0].write_text("operator edit", encoding="utf-8")
        with self.assertRaises(ValueError):
            queue.enqueue(self.stop)
        self.assertEqual("operator edit", pages[0].read_text())

    def test_parallel_capture_and_account_separation(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(lambda _: self.queue.enqueue(self.stop), range(8)))
        self.assertEqual(1, len(set(ids)))
        self.assertEqual(1, self.queue.status()["pending"])
        other = HookQueue({**self.config, "account":"other"})
        self.assertEqual(0, other.flush(self.receipt))

    def test_old_event_is_retained_for_review_and_new_events_can_flush(self):
        old = self.queue.enqueue(self.stop)
        with closing(self.queue.connect()) as db, db:
            db.execute("UPDATE outbox SET created=0 WHERE event_id=?", (old,))
        self.queue.enqueue({**self.stop, "turn_id":"new-turn"})
        self.assertEqual(1, self.queue.flush(self.receipt))
        self.assertEqual(1, self.queue.status()["needs_reconciliation"])
        self.assertEqual(1, self.queue.status()["pending"])

    def test_fail_open_native_command_with_invalid_input(self):
        cfg = Path(self.temp.name) / "binding.json"
        cfg.write_text(json.dumps(self.config), encoding="utf-8")
        cwd = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-m", "agent_hub.hooks", "capture", "--config", str(cfg)],
                                cwd=cwd, input="not json SYNTHETIC_TEST_SECRET", text=True, capture_output=True)
        self.assertEqual(0, result.returncode)
        self.assertEqual({}, json.loads(result.stdout))
        self.assertNotIn("SYNTHETIC_TEST_SECRET", result.stderr)

    def test_real_store_keeps_wiki_copy_and_starts_usage_after_acceptance(self):
        from agent_hub.storage import Store
        store = Store(Path(self.temp.name) / "hub.sqlite3")
        eid = self.queue.enqueue(self.stop)
        def submit(_name, args):
            return store.report_step(args["project"], "hook-device", args["event"])
        self.assertEqual(self.queue.flush(submit), 1)
        actual = store.get_wiki_entry("sample", eid, "1")
        expected = self.root / "omx_wiki" / "agent-results" / (eid + ".md")
        self.assertEqual(actual["body"], expected.read_text(encoding="utf-8"))
        self.assertEqual(store.claim_usage_job("sample", "owner", "quota-worker")["event_id"], eid)


if __name__ == "__main__":
    unittest.main()
