"""A combined status answer travels from central MCP to an independently authorized US MCP."""

import asyncio
from contextlib import asynccontextmanager
import json
import secrets
import socket

import pytest
import uvicorn

from agent_hub.client import call_tool_async
from agent_hub.remote_supervisor import RemoteSupervisor, project_token_env
from agent_hub.server import create_app, token_digest
from agent_hub.storage import Store
from agent_hub.supervisor import EvidenceSupervisor, RemoteReadStore
from test_supervisor import completion, model_response


@asynccontextmanager
async def running(app, listener):
    service = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False, lifespan="on"))
    task = asyncio.create_task(service.serve(sockets=[listener]))
    try:
        for _ in range(200):
            if service.started:
                break
            if task.done():
                await task
            await asyncio.sleep(.02)
        assert service.started
        yield
    finally:
        service.should_exit = True
        await asyncio.wait_for(task, 8)


class ControlledAnswer(EvidenceSupervisor):
    """Hold a completed fixture response until the test changes an upstream permission."""
    async def _ask(self, raw):
        reply = await super()._ask(raw)
        if self.hold:
            self.responded.set()
            await self.release.wait()
        return reply


def grant(token, project, scopes):
    return {"sha256": token_digest(token), "subject": "fixture", "project": project, "scopes": scopes}


def test_global_chat_two_mcp_instances_scope_epoch_and_duplicates(tmp_path):
    async def scenario(fake_model, model_calls):
        ports = {}
        with socket.socket() as central_socket, socket.socket() as us_socket:
            for label, sock in (("central", central_socket), ("us", us_socket)):
                sock.bind(("127.0.0.1", 0))
                ports[label] = f"127.0.0.1:{sock.getsockname()[1]}"
            central, usa = ("http://" + ports[name] + "/hub/mcp" for name in ("central", "us"))
            keys = {name: secrets.token_urlsafe(24) for name in ("viewer", "viewer_a", "delegate", "us_reader",
                                                                  "up_a", "up_b", "withdraw")}
            view = ["tasks:read", "chat:model"]
            central_grants = [grant(keys["viewer"], p, view) for p in ("A", "B")]
            central_grants += [grant(keys["viewer_a"], "A", view), grant(keys["withdraw"], "B", ["wiki:withdraw"]),
                               grant(keys["up_a"], "A", ["tasks:read"]), grant(keys["up_b"], "B", ["tasks:read"])]
            us_grants = [grant(keys["delegate"], p, [*view, "chat:delegate"]) for p in ("A", "B")]
            us_grants += [grant(keys["us_reader"], p, view) for p in ("A", "B")]
            central_auth, us_auth = tmp_path / "central.json", tmp_path / "us.json"
            for dest, grants in ((central_auth, central_grants), (us_auth, us_grants)):
                dest.write_text(json.dumps({"grants": grants}), encoding="utf-8")
                dest.chmod(0o600)
            db = Store(tmp_path / "central.sqlite3")
            for p in ("A", "B", "unrelated"):
                db.report_step(p, "same-source", dict(event_id="same-event", task_id="same-task", attempt_id="run",
                    tool="codex", account="private-billing", status="completed", summary="only-in-" + p,
                    wiki=dict(entry_id="private-note", version="1", path="notes.md", body="unpublished body")))
            upstream = RemoteReadStore(central, {"A": keys["up_a"], "B": keys["up_b"]})
            engine = ControlledAnswer(upstream, fake_model, "test", "model-only-test-token")
            engine.hold = False
            engine.release, engine.responded = asyncio.Event(), asyncio.Event()
            delegate = RemoteSupervisor(usa, ["A", "B"], keys["delegate"])
            primary_app = create_app(db, central_auth, hosts=[ports["central"]], supervisor=delegate)
            us_app = create_app(Store(tmp_path / "us-empty.sqlite3"), us_auth, hosts=[ports["us"]], supervisor=engine)
            async with running(primary_app, central_socket), running(us_app, us_socket):
                async def ask(token, project="*"):
                    return await call_tool_async("chat", {"project": project, "question": "compare work"},
                                                 endpoint=central, token=keys[token])
                answer = await ask("viewer")
                assert answer["mode"] == "model"
                assert {(r["project"], r["event_id"], r["source"]) for r in answer["evidence_refs"]} == {
                    ("A", "same-event", "same-source"), ("B", "same-event", "same-source")}
                assert set(answer["evidence"]) == {"A/same-event", "B/same-event"}
                assert len(model_calls) == 1
                payload = model_calls[0][2]
                assert b"only-in-A" in payload and b"only-in-B" in payload
                assert b"only-in-unrelated" not in payload and b"private-billing" not in payload
                assert b"unpublished body" not in payload and keys["viewer"].encode() not in payload
                await ask("viewer_a")
                assert b"only-in-A" in model_calls[-1][2] and b"only-in-B" not in model_calls[-1][2]
                before = len(model_calls)
                with pytest.raises(Exception):
                    await ask("viewer_a", "B")
                request = {"projects": ["A", "B"], "epochs": {"A": 0, "B": 0}, "question": "compare work"}
                with pytest.raises(Exception):
                    await call_tool_async("infer_projects", request, endpoint=usa, token=keys["us_reader"])
                with pytest.raises(Exception):
                    await call_tool_async("infer_projects", {**request, "projects": ["A", "unrelated"],
                                          "epochs": {"A": 0, "unrelated": 0}}, endpoint=usa, token=keys["delegate"])
                assert len(model_calls) == before
                engine.hold = True
                pending = asyncio.create_task(ask("viewer"))
                try:
                    await asyncio.wait_for(engine.responded.wait(), 12)
                    await call_tool_async("withdraw_wiki", {"project": "B", "entry_id": "private-note", "request_id": "withdraw"},
                                          endpoint=central, token=keys["withdraw"])
                finally:
                    engine.release.set()
                with pytest.raises(Exception):
                    await pending
                before = len(model_calls)
                with pytest.raises(Exception):
                    await call_tool_async("infer_projects", request, endpoint=usa, token=keys["delegate"])
                assert len(model_calls) == before

    with model_response(completion([{"text": "Grounded status.", "refs": ["R1", "R2"]}])) as (endpoint, calls):
        asyncio.run(scenario(endpoint, calls))


def test_binding_map_and_remote_citation_validation():
    assert project_token_env(["A=KEY_A", "B=KEY_B"], {"KEY_A": "a", "KEY_B": "b"}) == {"A": "a", "B": "b"}
    for values in (["A=KEY_A", "A=KEY_B"], ["*=KEY_A"], ["A=MISSING"]):
        with pytest.raises(ValueError):
            project_token_env(values, {"KEY_A": "a", "KEY_B": "b"})

    async def bad_reply(name, args, *, endpoint, token):
        return {"mode": "model", "answer": "unsupported", "evidence": [
            {"project": "B", "event_id": "same-event", "source": "same-source"}]}
    supervisor = RemoteSupervisor("https://hub.invalid/hub/mcp", ["A"], "private-demo-service-key", call=bad_reply)
    with pytest.raises(ValueError, match="unbound_evidence"):
        asyncio.run(supervisor.summarize_projects("question", ["A"], {"A": 2}, [
            {"project": "A", "event_id": "same-event", "source": "same-source"}]))
    with pytest.raises(ValueError, match="credential_in_request"):
        asyncio.run(supervisor.summarize_projects("private-demo-service-key", ["A"], {"A": 2}, []))
