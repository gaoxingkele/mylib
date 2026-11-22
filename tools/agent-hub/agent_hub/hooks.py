"""Opt-in, per-execution lifecycle capture and durable project wiki delivery."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
import uuid
from contextlib import closing
from pathlib import Path


MAX_INPUT = 256 * 1024
MAX_PENDING = 1000
DAY = 86400
NATIVE = {"codex", "claude", "grok"}
IDENTITY = ("project", "task_id", "attempt_id", "tool", "account", "host", "window", "generation")
SECRET = re.compile(
    r"(?i)(\bbearer\s+)[^\s,\"']+|"
    r"(\b(?:api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[\"']?(?:(?:bearer|basic)\s+)?)[^\s,\"']+|"
    r"\b(?:sk-|xai-|gh[pousr]_)[A-Za-z0-9_-]{12,}"
)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def safe_text(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > limit:
        raise ValueError("invalid text field")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        raise ValueError("unexpected control character")
    if "-----BEGIN " in value and "PRIVATE KEY-----" in value:
        raise ValueError("private key material")
    return SECRET.sub(lambda m: (m[1] or m[2] or "") + "[redacted]", value.strip())


def wiki_file(root, relative):
    if Path(relative).is_absolute() or ".." in Path(relative).parts or not Path(relative).parts:
        raise ValueError("wiki path must be project relative")
    destination = root / relative
    current = root
    for part in Path(relative).parts:
        if part.casefold() in {".git", ".metarsi"} or ":" in part:
            raise ValueError("unsupported wiki destination")
        current /= part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("linked wiki destination")
    if not destination.resolve().is_relative_to(root):
        raise ValueError("wiki destination outside project")
    return destination


def binding(config):
    result = {name: safe_text(config[name], 180) for name in IDENTITY}
    for name in ("project_root", "state_dir"):
        path = Path(config[name])
        if not path.is_absolute():
            raise ValueError("absolute path required")
        result[name] = str(path.resolve())
    root = Path(result["project_root"])
    if not root.is_dir() or Path(result["state_dir"]).is_relative_to(root):
        raise ValueError("store hook state outside the project")
    result["wiki_dir"] = config.get("wiki_dir", "omx_wiki/agent-results")
    wiki_file(root, result["wiki_dir"])
    result["window_id"] = safe_text(config.get("window_id", result["window"]), 180)
    for name in ("endpoint", "session_id", "tool_version", "previous_attempt_id", "role", "artifact",
                 "host_installation_id", "terminal_session_id", "journal_id"):
        if config.get(name):
            result[name] = safe_text(config[name], 1024)
    return result


def adapt(config, payload, manual=False):
    """Return only coarse lifecycle metadata and explicitly marked shareable text."""
    if not isinstance(payload, dict):
        raise ValueError("expected an object")
    tool = config["tool"]
    if manual:
        kind = "ManualReport"
        session = config.get("session_id", config["attempt_id"])
        key = safe_text(payload["step_id"], 180)
        status = safe_text(payload.get("status", "reported"), 48)
        summary = safe_text(payload["summary"], 4096)
    else:
        if tool not in NATIVE:
            raise ValueError("tool requires manual reporting")
        grok = tool == "grok"
        kind = payload.get("hookEventName" if grok else "hook_event_name")
        if grok:
            kind = {"stop": "Stop", "stop_failure": "StopFailure", "post_tool_use": "PostToolUse",
                    "post_tool_use_failure": "PostToolUseFailure"}.get(kind, kind)
            # Grok also fires an observe-only Stop when the session closes.
            if kind == "Stop" and payload.get("reason") not in (None, "end_turn"):
                return None
        if kind not in {"Stop", "StopFailure", "PostToolUseFailure", "PostToolUse"}:
            return None
        session = safe_text(payload.get("sessionId" if grok else "session_id"), 180)
        cwd = Path(payload["cwd"])
        if not cwd.is_absolute() or not cwd.resolve().is_relative_to(Path(config["project_root"])):
            return None
        if config.get("session_id") and session != config["session_id"]:
            return None
        key = payload.get("toolUseId" if grok else "tool_use_id") if kind.startswith("Post") else None
        key = key or (payload.get("promptId") or payload.get("turnId") if grok else payload.get("turn_id"))
        # Some runtimes omit turn IDs. Preserve separate occurrences; transport
        # retries always reuse the ID assigned before this process returns.
        key = safe_text(key, 180) if key else uuid.uuid4().hex
        status = "reported"
        if kind.startswith("PostToolUse"):
            name = safe_text(payload.get("toolName" if grok else "tool_name"), 128)
            if name not in {"Edit", "Write", "apply_patch", "ApplyPatch"}:
                return None
            status = "blocked" if kind == "PostToolUseFailure" else "reported"
            summary = f"{name}: " + ("tool failure reported" if status == "blocked" else "change reported")
        elif kind == "StopFailure":
            status = "blocked"
            summary = "Provider reported a turn failure."
        else:
            summary = "Provider reported the end of a turn."
            final = payload.get("lastAssistantMessage" if grok else "last_assistant_message")
            if isinstance(final, str):
                for line in final.splitlines():
                    if line.startswith("HUB-REPORT:") and line[11:].strip():
                        summary = safe_text(line[11:], 4096)
                        break
    event_id = digest(canonical([config["project"], config["attempt_id"], tool, session, kind, key]))
    event = {k: config[k] for k in IDENTITY if k != "project"}
    for field in ("window_id", "previous_attempt_id", "role", "tool_version", "artifact",
                  "host_installation_id", "terminal_session_id", "journal_id"):
        if field in config:
            event[field] = config[field]
    event.update(event_id=event_id, session_id=session, status=status, summary=summary, kind=kind)
    if manual:
        if "verdict" in payload:
            if payload["verdict"] not in ("pass", "fail", "unknown"):
                raise ValueError("invalid verification verdict")
            event["verdict"] = payload["verdict"]
        for field in ("evidence", "skills"):
            if field in payload:
                values = payload[field]
                if not isinstance(values, list) or len(values) > 16:
                    raise ValueError("invalid manual references")
                event[field] = [safe_text(v, 512) for v in values]
    path = (Path(config["wiki_dir"]) / f"{event_id}.md").as_posix()
    lines = [f"# {event['task_id']}", "", summary, "", f"- Tool: {tool}", f"- Status: {status}",
             f"- Attempt: {event['attempt_id']}", f"- Event: {event_id}"]
    for field in ("evidence", "skills"):
        lines.extend(f"- {field}: {item}" for item in event.get(field, []))
    body = "\n".join(lines) + "\n"
    event["wiki"] = dict(entry_id=event_id, version="1", body=body, path=path, sha256=digest(body))
    return event


class HookQueue:
    def __init__(self, config):
        self.config = binding(config)
        self.root = Path(self.config["project_root"])
        state = Path(self.config["state_dir"])
        state.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.database = state / "hook-outbox.sqlite3"
        self.scope = digest(canonical(self.config))
        with closing(self.connect()) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS outbox(
                seq INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL,
                source_seq INTEGER NOT NULL, event_id TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL,
                delivered REAL, receipt_seq INTEGER, UNIQUE(scope,event_id))""")
            db.execute("CREATE INDEX IF NOT EXISTS pending ON outbox(scope,delivered,seq)")
            db.execute("CREATE TABLE IF NOT EXISTS counters(scope TEXT PRIMARY KEY, last_seq INTEGER NOT NULL)")

    def connect(self):
        db = sqlite3.connect(self.database, timeout=3)
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, payload, manual=False):
        event = adapt(self.config, payload, manual)
        if event is None:
            return None
        encoded = canonical(event)
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            now = time.time()
            db.execute("DELETE FROM outbox WHERE delivered < ?", (now - 35 * DAY,))
            row = db.execute("SELECT payload FROM outbox WHERE scope=? AND event_id=?",
                             (self.scope, event["event_id"])).fetchone()
            if row and row["payload"] != encoded:
                raise ValueError("native event identity conflict")
            if not row:
                count = db.execute("SELECT COUNT(*) FROM outbox WHERE delivered IS NULL").fetchone()[0]
                if count >= MAX_PENDING:
                    raise RuntimeError("hook backlog full")
                db.execute("""INSERT INTO counters VALUES(?,1)
                    ON CONFLICT(scope) DO UPDATE SET last_seq=last_seq+1""", (self.scope,))
                seq = db.execute("SELECT last_seq FROM counters WHERE scope=?", (self.scope,)).fetchone()[0]
                db.execute("INSERT INTO outbox(scope,source_seq,event_id,payload,created) VALUES(?,?,?,?,?)",
                           (self.scope, seq, event["event_id"], encoded, now))
        self.write_wiki(event["wiki"])
        return event["event_id"]

    def write_wiki(self, wiki):
        dest = wiki_file(self.root, wiki["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = wiki["body"].encode("utf-8")
        if dest.exists():
            if dest.stat().st_size != len(data) or dest.read_bytes() != data:
                raise ValueError("existing wiki entry differs")
            return
        with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=".hub-", delete=False) as tmp:
            tmp_name = Path(tmp.name)
            try:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            except BaseException:
                tmp.close()
                tmp_name.unlink(missing_ok=True)
                raise
        try:
            try:
                os.link(tmp_name, dest)
            except FileExistsError:
                if dest.stat().st_size != len(data) or dest.read_bytes() != data:
                    raise ValueError("concurrent wiki entry differs") from None
        finally:
            tmp_name.unlink(missing_ok=True)

    def flush(self, send, limit=50):
        if not 1 <= limit <= MAX_PENDING:
            raise ValueError("invalid flush limit")
        with closing(self.connect()) as db:
            rows = db.execute("""SELECT * FROM outbox WHERE scope=? AND delivered IS NULL AND created>=?
                ORDER BY seq LIMIT ?""", (self.scope, time.time() - 14 * DAY, limit)).fetchall()
        delivered = 0
        for row in rows:
            event = json.loads(row["payload"])
            self.write_wiki(event["wiki"])
            event["source_seq"] = row["source_seq"]
            receipt = send("report_step", {"project": self.config["project"], "event": event})
            if not isinstance(receipt, dict) or any(receipt.get(k) != event[k]
                    for k in ("event_id", "task_id", "attempt_id")) or type(receipt.get("seq")) is not int or receipt["seq"] <= 0:
                raise ValueError("unmatched MCP receipt")
            with closing(self.connect()) as db, db:
                db.execute("UPDATE outbox SET delivered=?,receipt_seq=? WHERE seq=? AND delivered IS NULL",
                           (time.time(), receipt["seq"], row["seq"]))
            delivered += 1
        return delivered

    def status(self):
        with closing(self.connect()) as db:
            row = db.execute("""SELECT COUNT(*) AS total, COUNT(delivered) AS delivered,
                COUNT(CASE WHEN delivered IS NULL AND created<? THEN 1 END) AS review,
                MIN(CASE WHEN delivered IS NULL THEN created END) AS oldest_pending
                FROM outbox WHERE scope=?""", (time.time() - 14 * DAY, self.scope)).fetchone()
        return {"pending": row["total"] - row["delivered"], "delivered": row["delivered"],
                "needs_reconciliation": row["review"], "oldest_pending": row["oldest_pending"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("capture", "report", "flush", "watch", "status"))
    parser.add_argument("--config", default=os.environ.get("AGENT_HUB_BINDING"))
    parser.add_argument("--interval", type=int, default=5, help="worker poll interval in seconds")
    args = parser.parse_args(argv)
    try:
        if not args.config and args.action == "capture":
            print("{}")
            return 0
        if not args.config:
            raise ValueError("configuration required")
        queue = HookQueue(json.loads(Path(args.config).read_text(encoding="utf-8-sig")))
        if args.action in {"capture", "report"}:
            raw = sys.stdin.buffer.read(MAX_INPUT + 1)
            if len(raw) > MAX_INPUT:
                raise ValueError("input exceeds limit")
            event_id = queue.enqueue(json.loads(raw), manual=args.action == "report")
            result = {} if args.action == "capture" else {"event_id": event_id}
        elif args.action in {"flush", "watch"}:
            from .client import call_tool
            endpoint, token = queue.config["endpoint"], os.environ["AGENT_HUB_TOKEN"]
            def send(name, arguments):
                return call_tool(name, arguments, endpoint=endpoint, token=token)
            if args.action == "watch":
                if not 1 <= args.interval <= 3600:
                    raise ValueError("invalid interval")
                delay = args.interval
                while True:
                    try:
                        queue.flush(send)
                        delay = args.interval
                    except Exception as exc:
                        print("Agent Hub worker: " + type(exc).__name__, file=sys.stderr)
                        delay = min(max(args.interval, 300), delay * 2)
                    time.sleep(delay)
            result = {"delivered": queue.flush(send)}
        else:
            result = queue.status()
        print(json.dumps(result))
        return 0
    except Exception as exc:
        print("Agent Hub hook: " + type(exc).__name__, file=sys.stderr)
        if args.action == "capture":
            print("{}")
            return 0
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
