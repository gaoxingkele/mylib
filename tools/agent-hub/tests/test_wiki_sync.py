import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from agent_hub.backup import backup, restore, rotate
from agent_hub.storage import Store
from agent_hub.wiki_sync import WikiOutbox, privacy_epoch, sync_wiki, withdraw_wiki


PROJECT, SOURCE = "project-a", "host-a"


def report(body=None):
    event = dict(event_id="e1", task_id="task", attempt_id="run", account="account",
                 tool="codex", summary="shared-sensitive-summary" if body else "ready", status="running")
    if body:
        event["wiki"] = dict(entry_id="result", version="v1", path="wiki/result.md", body=body)
        event["evidence"] = ["shared-sensitive-reference"]
    return event


def revision(version="v1", parent=None):
    return dict(request_id="req-" + version, task_id="task", attempt_id="run", entry_id="result",
                version=version, parent_version=parent, path="wiki/result.md", body="approved-" + version)


class WikiLifecycleTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.db = self.root / "hub.sqlite3"
        self.store = Store(self.db)
        self.project_root = self.root / "project"
        self.project_root.mkdir()
        self.external = self.project_root / ".metarsi" / "wiki" / "log.md"
        self.external.parent.mkdir(parents=True)
        self.config = dict(project=PROJECT, task_id="task", attempt_id="run",
                           wiki_share_dir=".metarsi/wiki", project_root=str(self.project_root),
                           state_dir=str(self.root / "private"), endpoint="https://fixture.invalid/mcp")

    def send(self, name, args):
        func = {"sync_wiki":sync_wiki, "withdraw_wiki":withdraw_wiki}[name]
        return func(self.store, source=SOURCE, **args)

    def test_external_file_immutable_and_retries_use_captured_bytes(self):
        self.store.report_step(PROJECT, SOURCE, report())
        data = b"# Approved\r\n\r\nold revision\r\n"
        self.external.write_bytes(data)
        box = WikiOutbox(self.config)
        request = box.stage(".metarsi/wiki/log.md", "result", "v1", hashlib.sha256(data).hexdigest())
        self.assertEqual(self.external.read_bytes(), data)
        self.external.write_bytes(b"# Newer external revision\n")
        def lost_ack(name, args):
            self.send(name, args)
            raise ConnectionError("dropped")
        with self.assertRaises(ConnectionError):
            box.flush(lost_ack)
        self.assertEqual(WikiOutbox(self.config).flush(self.send), 1)
        self.assertEqual(self.store.get_wiki_entry(PROJECT, "result", "v1")["body"], data.decode())
        self.assertTrue(request)
        self.assertEqual(self.external.read_bytes(), b"# Newer external revision\n")
        with self.store._db() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM quota_refresh_jobs").fetchone()[0], 1)

    def test_forks_conflict_binding_and_outdated_parent(self):
        self.store.report_step(PROJECT, SOURCE, report())
        initial = sync_wiki(self.store, PROJECT, SOURCE, revision())
        self.assertEqual(sync_wiki(self.store, PROJECT, SOURCE, revision()), initial)
        with self.assertRaisesRegex(ValueError,"wiki_request_conflict"):
            sync_wiki(self.store, PROJECT, SOURCE, {**revision(), "body":"changed"})
        with self.assertRaisesRegex(ValueError,"wiki_attempt_unavailable"):
            sync_wiki(self.store, PROJECT, "other", revision("v2","v1"))
        with self.assertRaisesRegex(ValueError,"wiki_parent_missing"):
            sync_wiki(self.store, PROJECT, SOURCE, revision("v2","missing"))
        sync_wiki(self.store, PROJECT, SOURCE, revision("v2","v1"))
        sync_wiki(self.store, PROJECT, SOURCE, revision("branch","v1"))
        self.assertCountEqual(self.store.get_wiki_entry(PROJECT,"result")["heads"], ["v2","branch"])

    def test_private_and_wrong_digest_and_escaping_files_are_excluded(self):
        box = WikiOutbox(self.config)
        for sample in (b"---\nvisibility: private\n---\nprivate", b"token = syntheticValueSecret"):
            self.external.write_bytes(sample)
            with self.assertRaises(ValueError):
                box.stage(".metarsi/wiki/log.md", "r", "v1", hashlib.sha256(sample).hexdigest())
        self.external.write_bytes(b"safe")
        with self.assertRaisesRegex(ValueError, "wiki_file_changed"):
            box.stage(".metarsi/wiki/log.md","r","v1","a"*64)
        with self.assertRaisesRegex(ValueError,"outside_wiki_directory"):
            box.stage(".metarsi/wiki/../../hidden.md","r","v1","a"*64)
        self.assertEqual(box.flush(self.send), 0)
        private = report("private rationale")
        private["wiki"]["visibility"] = "private"
        with self.assertRaisesRegex(ValueError,"private_wiki_entry"):
            self.store.report_step(PROJECT,SOURCE,private)
        self.assertEqual(self.store.search_task_events(PROJECT)["events"],[])

    def test_withdrawal_scrubs_projections_and_prevents_stale_republication(self):
        self.store.report_step(PROJECT, SOURCE, report("shared-sensitive-body"))
        self.store.report_step("project-b", SOURCE, report("shared-sensitive-body"))
        old_epoch = privacy_epoch(self.store,PROJECT)
        ack = withdraw_wiki(self.store,PROJECT,"owner","result","w1")
        self.assertEqual(withdraw_wiki(self.store,PROJECT,"owner","result","w1"),ack)
        self.assertEqual(privacy_epoch(self.store,PROJECT),old_epoch+1)
        self.assertEqual(privacy_epoch(self.store,"project-b"),0)
        for version in (None,"v1"):
            with self.assertRaisesRegex(ValueError,"wiki_not_found"):
                self.store.get_wiki_entry(PROJECT,"result",version)
        with self.assertRaisesRegex(ValueError,"wiki_not_found"):
            self.store.report_step(PROJECT,SOURCE,{**report("shared-sensitive-body"),"event_id":"late"})
        with self.assertRaisesRegex(ValueError,"wiki_not_found"):
            sync_wiki(self.store,PROJECT,SOURCE,revision("late","v1"))
        for result in (self.store.search_task_events(PROJECT),self.store.get_task_status(PROJECT,"task"),
                       self.store.list_tasks(PROJECT)):
            self.assertNotIn("shared-sensitive", json.dumps(result))
        self.assertEqual(self.store.search_task_events(PROJECT,"shared-sensitive")["events"],[])
        self.assertEqual(self.store.get_wiki_entry("project-b","result","v1")["body"],"shared-sensitive-body")

    def test_queued_withdrawal_drops_unsent_text_and_is_repeatable(self):
        self.external.write_text("approved",encoding="utf-8")
        box=WikiOutbox(self.config)
        box.stage(".metarsi/wiki/log.md","result","v1",hashlib.sha256(b"approved").hexdigest())
        box.stage_withdrawal("result")
        sent = []
        def deliver(name,args):
            sent.append((name,args))
            return self.send(name,args)
        self.assertEqual(box.flush(deliver),1)
        self.assertEqual(sent[0][0],"withdraw_wiki")
        self.assertNotIn("approved",json.dumps(sent))
        with self.assertRaisesRegex(ValueError,"private_wiki_entry"):
            box.stage(".metarsi/wiki/log.md","result","v2",hashlib.sha256(b"approved").hexdigest())

    def test_old_snapshot_restored_with_current_tombstones_and_rotation_preserves_denial(self):
        self.store.report_step(PROJECT, SOURCE, report("shared-sensitive-body"))
        backup(self.db, self.root/"archive")
        withdraw_wiki(self.store,PROJECT,"owner","result","w1")
        with self.assertRaisesRegex(ValueError,"requires_authoritative_revocations"):
            restore(self.root/"archive",self.root/"unsafe.sqlite3")
        self.assertFalse((self.root/"unsafe.sqlite3").exists())
        restore(self.root/"archive",self.root/"restored.sqlite3",self.db)
        restored=Store(self.root/"restored.sqlite3")
        with self.assertRaisesRegex(ValueError,"wiki_not_found"):
            restored.get_wiki_entry(PROJECT,"result","v1")
        self.assertNotIn("shared-sensitive",json.dumps(restored.get_task_status(PROJECT,"task")))
        new=Store(rotate(self.db,self.root/"generation")["active"])
        with self.assertRaisesRegex(ValueError,"wiki_not_found"):
            sync_wiki(new,PROJECT,SOURCE,revision("again","v1"))

    @unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("mcp", "pytest", "uvicorn")),
                         "requires the pilot MCP transport test environment")
    def test_real_mcp_revision_withdrawal_and_scope_authorization(self):
        from agent_hub.client import call_tool_async
        from test_mcp_transport import pilot

        async def scenario():
            async with pilot(self.root) as (host, tokens, auth):
                grants = json.loads(auth.read_text())
                for grant in grants["grants"]:
                    if grant["project"]=="demo" and grant["subject"]=="hook":
                        grant["scopes"].extend(["wiki:write","wiki:withdraw"])
                auth.write_text(json.dumps(grants))
                async def call(tool, subject, **arguments):
                    return await call_tool_async(tool, {"project":"demo", **arguments},
                                                 endpoint=f"http://{host}/hub/mcp", token=tokens[subject])
                event = {**report(), "host":"host-A","account":"fixture"}
                await call("report_step","hook",event=event)
                with self.assertRaises(Exception):
                    await call("sync_wiki","reader",revision=revision())
                ack = await call("sync_wiki","hook",revision=revision())
                self.assertEqual(ack["status"], "recorded")
                self.assertEqual((await call("get_wiki_entry","reader",entry_id="result",version="v1"))["body"],
                                 "approved-v1")
                with self.assertRaises(Exception):
                    await call("withdraw_wiki","reader",entry_id="result",request_id="remove")
                await call("withdraw_wiki","hook",entry_id="result",request_id="remove")
                with self.assertRaises(Exception):
                    await call("get_wiki_entry","reader",entry_id="result",version="v1")
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
