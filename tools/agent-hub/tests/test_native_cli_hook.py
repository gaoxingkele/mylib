"""Prove native Stop hooks with isolated CLI profiles and loopback model responses."""

from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid

import pytest


MARKER = "HUB-REPORT: isolated native Codex Stop"


class ResponsesFixture(BaseHTTPRequestHandler):
    """One synthetic Responses turn; external proxy destinations get rejected."""
    def log_message(self, *_):
        pass

    def do_CONNECT(self):
        self.send_error(403)

    def do_GET(self):
        self.send_error(404)

    def do_POST(self):
        if self.path.partition("?")[0] == "/v1/messages":
            self.rfile.read(int(self.headers["Content-Length"]))
            self.server.completed_requests += 1
            message = {"id": "msg_owned", "type": "message", "role": "assistant", "model": "claude-sonnet-4-5",
                       "content": [], "stop_reason": None, "stop_sequence": None,
                       "usage": {"input_tokens": 1, "output_tokens": 1}}
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for event in (
                {"type": "message_start", "message": message},
                {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
                {"type": "content_block_delta", "index": 0,
                 "delta": {"type": "text_delta", "text": "HUB-REPORT: isolated native Claude Stop"}},
                {"type": "content_block_stop", "index": 0},
                {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                 "usage": {"output_tokens": 8}},
                {"type": "message_stop"},
            ):
                self.wfile.write(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode())
            return
        if self.path != "/v1/responses":
            self.send_error(404)
            return
        self.rfile.read(int(self.headers["Content-Length"]))
        self.server.completed_requests += 1
        response = {"id": "fixture", "object": "response", "created_at": 1800000000, "model": "pilot-fixture",
                    "parallel_tool_calls": False, "tools": [], "tool_choice": "auto", "error": None}
        marker = self.server.marker
        message = {"id": "fixture-message", "type": "message", "role": "assistant", "status": "completed",
                   "phase": "final_answer", "content": [{"type": "output_text", "text": marker, "annotations": []}]}
        events = [
            {"type": "response.created", "response": {**response, "status": "in_progress", "output": []}},
            {"type": "response.output_item.added", "output_index": 0, "item": {**message, "content": []}},
            {"type": "response.content_part.added", "output_index": 0, "item_id": message["id"], "content_index": 0,
             "part": {"type": "output_text", "text": "", "annotations": []}},
            {"type": "response.output_text.delta", "output_index": 0, "item_id": message["id"],
             "content_index": 0, "delta": marker},
            {"type": "response.output_item.done", "output_index": 0, "item": message},
            {"type": "response.completed", "response": {**response, "status": "completed", "output": [message],
             "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2,
                       "input_tokens_details": {"cached_tokens": 0, "text_tokens": 1, "audio_tokens": 0, "image_tokens": 0},
                       "output_tokens_details": {"reasoning_tokens": 0}}}},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for sequence, event in enumerate(events):
            event["sequence_number"] = sequence
            self.wfile.write(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode())


@pytest.mark.skipif(os.environ.get("AGENT_HUB_RUN_NATIVE_HOOKS") != "1", reason="Opt-in installed CLI smoke")
def test_installed_codex_stop_captures_shareable_wiki_and_outbox(tmp_path):
    binary = shutil.which("codex")
    if binary is None or Path(binary).suffix.lower() in {".bat", ".cmd", ".ps1"}:
        pytest.skip("A native Codex CLI is required")
    runner = Path(__file__).resolve().parents[1] / "hooks" / "run.py"
    work, state, home = tmp_path / "repo", tmp_path / "state", tmp_path / "codex"
    work.mkdir()
    home.mkdir()
    (work / ".codex").mkdir()
    binding = tmp_path / "binding.json"
    binding.write_text(json.dumps(dict(project="native-smoke", project_root=str(work), state_dir=str(state),
        task_id="synthetic-task", attempt_id="native-codex", account="fake-seat", tool="codex",
        host="fixture", window="temporary", generation="1")), encoding="utf-8")
    command = [sys.executable, "-I", str(runner), "capture", "--config", str(binding)]
    shell_command = subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)
    (work / ".codex/hooks.json").write_text(json.dumps({"hooks": {
        "Stop": [{"hooks": [{"type": "command", "command": shell_command}]}]}}), encoding="utf-8")
    keep = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "SYSTEMDRIVE", "PROGRAMFILES", "PROGRAMFILES(X86)"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    for variable in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "XDG_CONFIG_HOME",
                     "XDG_CACHE_HOME", "XDG_DATA_HOME"):
        dest = tmp_path / ("profile" if variable in ("HOME", "USERPROFILE") else variable.lower())
        dest.mkdir(exist_ok=True)
        env[variable] = str(dest)
    with ResponsesFixtureServer() as mock:
        endpoint = f"http://127.0.0.1:{mock.server_port}"
        env.update(CODEX_HOME=str(home), HTTP_PROXY=endpoint, HTTPS_PROXY=endpoint,
                   ALL_PROXY=endpoint, NO_PROXY="localhost,127.0.0.1", AGENT_HUB_BINDING=str(binding))
        (home / "config.toml").write_text("\n".join([
            'model="gpt-5.4"', 'model_provider="fixture"', 'check_for_update_on_startup=false',
            'cli_auth_credentials_store="file"', 'notify=[]', '[features]', 'hooks=true', 'apps=false',
            '[model_providers.fixture]', 'name="Local fixture"', 'wire_api="responses"',
            'base_url=' + json.dumps(endpoint + "/v1"), 'requires_openai_auth=false',
            '[projects.' + json.dumps(str(work)) + ']', 'trust_level="trusted"',
        ]) + "\n", encoding="utf-8")
        flags = {"cwd": work, "env": env, "capture_output": True, "text": True, "encoding": "utf-8",
                 "errors": "replace", "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0}
        version = subprocess.run([binary, "--version"], **flags, timeout=10).stdout.strip()
        if version != "codex-cli 0.166.0":
            pytest.skip("Installed hook smoke validated with codex-cli 0.166.0")
        proc = subprocess.run([binary, "--no-daemon", "exec", "--skip-git-repo-check",
            "--dangerously-bypass-hook-trust", "--sandbox", "read-only", "Return the fixture marker."],
            **flags, stdin=subprocess.DEVNULL, timeout=60)
        assert proc.returncode == 0, proc.stderr[-2500:]
        assert mock.completed_requests == 1
    deadline = time.monotonic() + 4
    files = []
    while not files and time.monotonic() < deadline:
        files = list((work / "omx_wiki/agent-results").glob("*.md"))
        if not files:
            time.sleep(.05)
    assert len(files) == 1, f"wiki pages={len(files)}, CLI diagnostics={proc.stderr[-1600:]}"
    body = files[0].read_text(encoding="utf-8")
    with closing(sqlite3.connect(state / "hook-outbox.sqlite3")) as db:
        rows = db.execute("SELECT payload, delivered FROM outbox").fetchall()
    assert len(rows) == 1 and rows[0][1] is None
    event = json.loads(rows[0][0])
    assert event["tool"] == "codex" and event["kind"] == "Stop" and event["session_id"]
    assert event["summary"] == "isolated native Codex Stop"
    assert event["wiki"]["body"] == body and event["event_id"] == files[0].stem


class ResponsesFixtureServer(ThreadingHTTPServer):
    def __init__(self, marker=MARKER):
        super().__init__(("127.0.0.1", 0), ResponsesFixture)
        self.marker = marker
        self.completed_requests = 0

    def __enter__(self):
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.shutdown()
        self.server_close()
        self.thread.join(3)


def isolated_windows_environment(root, endpoint):
    keep = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "SYSTEMDRIVE", "PROGRAMFILES", "PROGRAMFILES(X86)"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "XDG_CONFIG_HOME",
                "XDG_CACHE_HOME", "XDG_DATA_HOME", "GROK_HOME", "CLAUDE_CONFIG_DIR"):
        dest = root / ("profile" if key in ("HOME", "USERPROFILE") else key.lower())
        dest.mkdir(exist_ok=True)
        env[key] = str(dest)
    env.update(HTTP_PROXY=endpoint, HTTPS_PROXY=endpoint, ALL_PROXY=endpoint, NO_PROXY="127.0.0.1,localhost",
               DISABLE_TELEMETRY="1", OTEL_SDK_DISABLED="true", CI="1", NO_COLOR="1")
    return env


def run_in_private_job(command, cwd, env):
    # Enroll the wrapper before telling it to start the CLI. Any leader or hook
    # it launches inherits this test-owned job; closing the job releases them.
    win32job = pytest.importorskip("win32job")
    job = win32job.CreateJobObject(None, "mylib-hook-fixture-" + uuid.uuid4().hex)
    info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    info["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, info)
    wrapper = ("import subprocess,sys; assert sys.stdin.readline()=='START\\n';"
               "sys.exit(subprocess.run(sys.argv[1:],stdin=subprocess.DEVNULL).returncode)")
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen([sys.executable, "-I", "-c", wrapper, *command], cwd=cwd, env=env,
                                stdin=subprocess.PIPE, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            win32job.AssignProcessToJobObject(job, int(proc._handle))
            proc.stdin.write(b"START\n")
            proc.stdin.close()
            proc.wait(timeout=40)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                stats = win32job.QueryInformationJobObject(job, win32job.JobObjectBasicAccountingInformation)
                if not stats["ActiveProcesses"]:
                    break
                time.sleep(.05)
        finally:
            job.Close()
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
        log.seek(0)
        return proc.returncode, log.read(32768).decode(errors="replace")


def new_native_binding(root, tool):
    work = root / "project"
    work.mkdir()
    binding = root / "binding.json"
    binding.write_text(json.dumps(dict(project="native-smoke", project_root=str(work), state_dir=str(root / "state"),
        task_id="synthetic-task", attempt_id=f"native-{tool}", account="fake-seat", tool=tool,
        host="fixture", window="temporary", generation="1")), encoding="utf-8")
    runner = Path(__file__).resolve().parents[1] / "hooks/run.py"
    command = subprocess.list2cmdline([Path(sys.executable).as_posix(), "-I", runner.as_posix(),
                                        "capture", "--config", binding.as_posix()])
    return work, binding, {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": command}]}]}}


def verify_native_result(root, work, tool, summary):
    files = list((work / "omx_wiki/agent-results").glob("*.md"))
    assert len(files) == 1, f"{tool} Stop did not produce exactly one project wiki page"
    with closing(sqlite3.connect(root / "state/hook-outbox.sqlite3")) as db:
        rows = db.execute("SELECT payload, delivered FROM outbox").fetchall()
    assert len(rows) == 1 and rows[0][1] is None
    event = json.loads(rows[0][0])
    assert event["tool"] == tool and event["kind"] == "Stop" and event["session_id"]
    assert event["summary"] == summary
    assert event["wiki"]["body"] == files[0].read_text(encoding="utf-8")
    assert event["event_id"] == files[0].stem


@pytest.mark.skipif(os.name != "nt" or os.environ.get("AGENT_HUB_RUN_NATIVE_HOOKS") != "1",
                    reason="Opt-in Windows native hook smoke")
def test_installed_claude_stop_captures_shareable_wiki_and_outbox(tmp_path):
    cli = shutil.which("claude")
    if not cli or Path(cli).suffix.lower() != ".exe":
        pytest.skip("A native Claude executable is required")
    work, binding, hooks = new_native_binding(tmp_path, "claude")
    settings = tmp_path / "synthetic-settings.json"
    settings.write_text(json.dumps(hooks), encoding="utf-8")
    with ResponsesFixtureServer() as mock:
        endpoint = f"http://127.0.0.1:{mock.server_port}"
        env = isolated_windows_environment(tmp_path, endpoint)
        env.update(ANTHROPIC_BASE_URL=endpoint, ANTHROPIC_API_KEY="synthetic-local-only-key",
                   AGENT_HUB_BINDING=str(binding), DISABLE_AUTOUPDATER="1", DISABLE_ERROR_REPORTING="1",
                   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1", CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")
        rc, version = run_in_private_job([cli, "--version"], work, env)
        if rc or version.strip() != "2.1.310 (Claude Code)":
            pytest.skip("Installed hook smoke validated with Claude Code 2.1.310")
        rc, output = run_in_private_job([cli, "--setting-sources", "", "--settings", str(settings),
            "--strict-mcp-config", "--disable-slash-commands", "--tools", "", "--model", "claude-sonnet-4-5",
            "--no-session-persistence", "--system-prompt", "Return the fixture marker.", "-p", "fixture"],
            work, env)
        assert rc == 0, output[-1400:]
        assert mock.completed_requests >= 1
    verify_native_result(tmp_path, work, "claude", "isolated native Claude Stop")


@pytest.mark.skipif(os.name != "nt" or os.environ.get("AGENT_HUB_RUN_NATIVE_HOOKS") != "1",
                    reason="Opt-in Windows native hook smoke")
def test_installed_grok_stop_captures_wiki_and_outbox():
    cli = shutil.which("grok")
    if not cli or Path(cli).suffix.lower() != ".exe":
        pytest.skip("A native Grok executable is required")
    # A short path also fits the platform's Unix socket path limit.
    with tempfile.TemporaryDirectory(prefix="grok-hub-") as temp, ResponsesFixtureServer("HUB-REPORT: isolated native Grok Stop") as mock:
        root = Path(temp)
        work, binding, hooks = new_native_binding(root, "grok")
        endpoint = f"http://127.0.0.1:{mock.server_port}"
        env = isolated_windows_environment(root, endpoint)
        home = Path(env["GROK_HOME"])
        leader = home / "leader-pilot.sock"
        hook_path = home / "hooks/pilot.json"
        hook_path.parent.mkdir(parents=True)
        hook_path.write_text(json.dumps(hooks), encoding="utf-8")
        env.update(XAI_API_KEY="synthetic-local-only", AGENT_HUB_BINDING=str(binding),
                   GROK_EXTERNAL_OTEL="0", OTEL_LOGS_EXPORTER="none", OTEL_METRICS_EXPORTER="none")
        (home / "config.toml").write_text("\n".join([
            '[models]', 'default="pilot-fixture"', '[model.pilot-fixture]',
            'model="pilot-fixture"', 'name="Test fixture"', 'base_url=' + json.dumps(endpoint + '/v1'),
            'api_base_url=' + json.dumps(endpoint + '/v1'), 'api_backend="responses"',
            'env_key="XAI_API_KEY"', 'supports_backend_search=false', '[cli]', 'auto_update=false',
            '[telemetry]', 'otel_enabled=false',
        ]) + "\n", encoding="utf-8")
        rc, version = run_in_private_job([cli, "--version"], work, env)
        if rc or version.strip() not in {"grok 1.0.92 (b06756fd6256)", "grok 1.0.92 (b06756fd6256) [stable]"}:
            pytest.skip("Installed hook smoke validated with Grok 1.0.92 b06756fd6256")
        rc, out = run_in_private_job([cli, "--leader-socket", str(leader), "--cwd", str(work),
            "--disable-web-search", "--no-subagents", "--no-memory", "--no-plan", "--tools", "",
            "--max-turns", "1", "-m", "pilot-fixture", "-p", "fixture"], work, env)
        assert rc == 0, out[-1400:]
        assert mock.completed_requests >= 1
        verify_native_result(root, work, "grok", "isolated native Grok Stop")
