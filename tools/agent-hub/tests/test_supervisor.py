import asyncio
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

from agent_hub.storage import Store
from agent_hub.supervisor import BODY_BYTES, EvidenceSupervisor, RemoteReadStore


@contextmanager
def model_response(reply, *, status=200):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            calls.append((self.path, self.headers.get("Authorization"), raw))
            body = json.dumps(reply).encode()
            self.send_response(status)
            if status == 307:
                self.send_header("Location", "/destination")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(3)


def completion(findings):
    return {"choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": json.dumps({"findings": findings})}}]}


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Store(Path(temp.name) / "hub.db")
        self.event = {"event_id": "e-1", "task_id": "review", "attempt_id": "a",
                      "account": "BILLING-ID-PRIVATE", "tool": "codex", "status": "running",
                      "summary": "review ready", "wiki": {"entry_id": "w1", "version": "1", "path": "review.md",
                                                          "body": "SYNTHETIC-WIKI-BODY"}}
        self.store.report_step("project-a", "machine-a", self.event)
        self.store.report_step("project-b", "machine-b", {**self.event, "summary": "FOREIGN-RECORD"})
        self.key = "synthetic-supervisor-key"

    def test_scoped_task_evidence_in_mcp_compatible_http_request(self):
        reply = completion([{"text": "The review is running.", "refs": ["R1"]}])
        with model_response(reply) as (url, calls), patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:1",
                                                                          "NO_PROXY": ""}):
            model = EvidenceSupervisor(self.store, url + "/v1", "test-model", self.key)
            answer = asyncio.run(model("project-a", {"question": "evidence for the task?", "task_id": "review"}))
        self.assertEqual(answer["mode"], "model")
        self.assertEqual(answer["evidence"], ["e-1"])
        self.assertIn("e-1", answer["answer"])
        path, bearer, raw = calls[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(bearer, "Bearer " + self.key)
        self.assertLessEqual(len(raw), BODY_BYTES)
        self.assertIn(b"SYNTHETIC-WIKI-BODY", raw)
        for secret in (b"BILLING-ID-PRIVATE", b"FOREIGN-RECORD", self.key.encode()):
            self.assertNotIn(secret, raw)
        self.assertNotIn("tools", json.loads(raw))

    def test_hallucinated_ids_and_redirects_return_only_real_records(self):
        reply = completion([{"text": "untrusted result", "refs": ["foreign-id"]}])
        for status in (200, 307, 429):
            with self.subTest(status=status), model_response(reply, status=status) as (url, calls):
                model = EvidenceSupervisor(self.store, url, "test", self.key)
                answer = asyncio.run(model("project-a", {"question": "recent events"}))
                self.assertEqual(answer["mode"], "recent_events")
                self.assertEqual(answer["evidence"], ["e-1"])
                self.assertNotIn("untrusted result", answer["answer"])
                self.assertEqual(len(calls), 1)

    def test_twenty_task_context_budget_and_empty_provider_scope(self):
        for n in range(20):
            self.store.report_step("project-a", "machine-a", {**self.event, "event_id": f"t{n}", "task_id": f"task-{n}",
                                 "summary": "输出" * 400})
        reply = completion([{"text": "bounded observation", "refs": ["R1"]}])
        with model_response(reply) as (url, calls):
            model = EvidenceSupervisor(self.store, url, "test", self.key)
            self.assertEqual(asyncio.run(model("project-a", {"question": "summary?"}))["mode"], "model")
            self.assertLessEqual(len(calls[0][2]), BODY_BYTES)
            data = json.loads(json.loads(calls[0][2])["messages"][-1]["content"])
            self.assertEqual(len({r["task_id"] for r in data["records"]}), 20)
            self.assertNotIn(b"SYNTHETIC-WIKI-BODY", calls[0][2])
            answer = asyncio.run(model("unknown-project", {"question": "summary?"}))
            self.assertEqual(answer["evidence"], [])
            self.assertEqual(len(calls), 1)
            answer = asyncio.run(model("project-a", {"question": "😀" * 2000}))
            self.assertEqual(answer["mode"], "recent_events")
            self.assertTrue(answer["evidence"])
            self.assertEqual(len(calls), 1)

    def test_remote_store_pins_project_identity_and_exposes_only_read_methods(self):
        calls = []
        def read(tool, args, **identity):
            calls.append((tool, args, identity))
            return {"events": []}
        remote = RemoteReadStore("https://test.invalid/hub/mcp", {"A": "token-a", "B": "token-b"}, call=read)
        self.assertEqual(remote.search_task_events("B", query="hello"), {"events": []})
        self.assertEqual(calls[-1], ("search_task_events", {"project": "B", "query": "hello", "limit": 50},
                                     {"endpoint": "https://test.invalid/hub/mcp", "token": "token-b"}))
        with self.assertRaises(PermissionError):
            remote.list_tasks("C")
        self.assertEqual(len(calls), 1)
        self.assertFalse(hasattr(remote, "report_step"))
        with self.assertRaises(ValueError):
            RemoteReadStore("https://test.invalid/hub/mcp", {"A": "token-a", "B": "token-a"})

    def test_remote_evidence_roundtrip_over_authenticated_mcp(self):
        try:
            from test_mcp_transport import pilot
            from agent_hub.client import call_tool_async
            from agent_hub.server import create_app, token_digest
            import uvicorn
        except ImportError:
            self.skipTest("Requires the pilot MCP test environment")

        async def scenario(tmp, url):
            async with pilot(tmp) as (authority, tokens, _):
                central = "http://" + authority + "/hub/mcp"
                step = {**self.event, "account": "fixture", "host": "host-A"}
                await call_tool_async("report_step", {"project": "demo", "event": step},
                                      endpoint=central, token=tokens["hook"])
                remote = RemoteReadStore(central, {"demo": tokens["reader"]})
                agent = EvidenceSupervisor(remote, url, "test", self.key)
                viewer_key = secrets.token_urlsafe(24)
                us_auth = tmp / "us-auth.json"
                us_auth.write_text(json.dumps({"grants": [{"project": "demo", "subject": "us-viewer",
                    "sha256": token_digest(viewer_key), "scopes": ["tasks:read", "chat:model"], "accounts": []}]}))
                us_auth.chmod(0o600)
                # An independently authorized MCP service owns no upstream task database.
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0))
                    us_host = f"127.0.0.1:{listener.getsockname()[1]}"
                    app = create_app(Store(tmp / "us.sqlite3"), us_auth, hosts=[us_host], supervisor=agent)
                    service = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False))
                    task = asyncio.create_task(service.serve(sockets=[listener]))
                    try:
                        for _ in range(200):
                            if service.started:
                                break
                            if task.done():
                                await task
                            await asyncio.sleep(.02)
                        self.assertTrue(service.started)
                        result = await call_tool_async("chat", {"project": "demo", "question": "wiki evidence?", "task_id": "review"},
                                                       endpoint=f"http://{us_host}/hub/mcp", token=viewer_key)
                    finally:
                        service.should_exit = True
                        await asyncio.wait_for(task, 10)
                self.assertEqual(result["evidence"], ["e-1"])
                self.assertEqual(result["mode"], "model")
                with self.assertRaises(PermissionError):
                    await agent("project-b", {"question": "other project's records?"})

        with tempfile.TemporaryDirectory() as tmp, model_response(
            completion([{"text": "evidence received", "refs": ["R1"]}])
        ) as (url, calls):
            asyncio.run(scenario(Path(tmp), url))
            self.assertEqual(len(calls), 1)

    def test_model_endpoint_and_credentials_fixed_by_operator(self):
        with self.assertRaises(ValueError):
            EvidenceSupervisor(self.store, "http://not-loopback.example", "test", self.key)
        with model_response({}) as (url, calls):
            model = EvidenceSupervisor(self.store, url, "test", self.key)
            with self.assertRaises(ValueError):
                asyncio.run(model("project-a", {"question": self.key}))
            with self.assertRaises(ValueError):
                asyncio.run(model("project-a", {"question": "hello", "endpoint": "https://evil.invalid"}))
            secret_event = {**self.event, "project": "project-a", "event_id": self.key}
            fallback = asyncio.run(model.summarize_authorized("hello", [secret_event]))
            self.assertEqual(fallback["evidence"], [])
            self.assertNotIn(self.key, json.dumps(fallback))
            self.assertEqual(calls, [])

    def test_single_global_call_keeps_matching_event_ids_project_scoped(self):
        rows = [{**self.event, "project": project, "source": "same-source",
                 "other_field": "PRIVATE-EXTRA", "summary": f"summary in {project}"}
                for project in ("A", "B")]
        for ref, mode in (("R2", "model"), ("UNKNOWN", "recent_events")):
            with self.subTest(mode=mode), model_response(completion([{
                "text": "A and B have distinct results", "refs": ["R1", ref]}])) as (url, calls):
                agent = EvidenceSupervisor(None, url, "test", self.key)
                result = asyncio.run(agent.summarize_authorized("compare tasks", rows))
                self.assertEqual(result["mode"], mode)
                self.assertEqual(result["evidence"], [{"project": p, "event_id": "e-1", "source": "same-source"}
                                                      for p in ("A", "B")])
                self.assertEqual(len(calls), 1)
                raw = calls[0][2]
                self.assertLessEqual(len(raw), BODY_BYTES)
                self.assertNotIn(self.event["account"].encode(), raw)
                self.assertNotIn(b"PRIVATE-EXTRA", raw)
                self.assertNotIn(b"SYNTHETIC-WIKI-BODY", raw)

    def test_remote_project_scope_disables_model_for_out_of_scope_global_rows(self):
        remote = RemoteReadStore("https://hub.invalid/hub/mcp", {"A": "central-token"})
        with model_response({}) as (url, calls):
            agent = EvidenceSupervisor(remote, url, "test", self.key)
            result = asyncio.run(agent.summarize_authorized("summary", [{**self.event, "project": "B"}]))
            self.assertEqual(result["mode"], "recent_events")
            self.assertEqual(result["evidence"][0]["project"], "B")
            self.assertEqual(calls, [])

    def test_remote_withdrawal_suppresses_model_and_held_fallback(self):
        for epochs, status, expected_calls in (([0, 1], 200, 0), ([0, 0, 1], 200, 1), ([0, 0, 1], 429, 1)):
            with self.subTest(epochs=epochs, status=status):
                versions = iter(epochs)
                def read(name, args, **identity):
                    if name == "get_evidence_epoch":
                        return {"epoch": next(versions)}
                    self.assertEqual(name, "get_task_status")
                    return {"task_id": "review", "primary_attempt_id": "a", "attempts": [self.event]}
                remote = RemoteReadStore("https://hub.invalid/hub/mcp", {"project-a": "secret"}, call=read)
                with model_response(completion([{"text": "internal", "refs": ["R1"]}]), status=status) as (url, calls):
                    agent = EvidenceSupervisor(remote, url, "test", self.key)
                    with self.assertRaisesRegex(PermissionError, "source_withdrawn"):
                        asyncio.run(agent("project-a", {"question": "status?", "task_id": "review"}))
                    self.assertEqual(len(calls), expected_calls)


if __name__ == "__main__":
    unittest.main()
