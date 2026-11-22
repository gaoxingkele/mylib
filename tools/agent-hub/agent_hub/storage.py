"""Project-scoped SQLite ledger for the Agent Hub. Each call owns one connection."""

from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import secrets
import sqlite3
import time


LEASE_SECONDS = 120
SCHEDULED_SOURCE = "__quota_monitor__"
EVENT_TEXT_FIELDS = {
    "event_id", "task_id", "attempt_id", "account", "tool", "summary", "status", "kind",
    "session_id", "window_id", "window", "host", "model", "tool_version", "turn_id", "step_id",
    "host_installation_id", "terminal_session_id", "journal_id",
    "role", "previous_attempt_id", "handoff_reason", "artifact", "artifact_digest", "verdict",
    "source_kind", "source_event_id", "observed_at",
}
REFERENCE_FIELDS = {
    "id", "kind", "event_id", "entry_id", "skill_id", "revision", "version", "path", "anchor",
    "sha256", "artifact", "title", "url",
}
ATTENTION_STATES = frozenset({
    "blocked", "failed", "needs_review", "baseline_unaligned", "needs_confirmation",
    "waiting", "limited", "waiting_user", "awaiting_user", "awaiting_confirmation",
    "awaiting_verification", "quota_limited", "rate_limited",
})


SCHEMA = """
CREATE TABLE IF NOT EXISTS hub_maintenance (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1), seal TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_receipts (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL, source TEXT NOT NULL,
    event_id TEXT NOT NULL, task_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
    digest TEXT NOT NULL, accepted_at REAL NOT NULL, UNIQUE(project, source, event_id)
);
CREATE TABLE IF NOT EXISTS task_current (
    project TEXT NOT NULL, task_id TEXT NOT NULL, primary_attempt_id TEXT NOT NULL,
    updated_at REAL NOT NULL, PRIMARY KEY(project, task_id)
);
CREATE TABLE IF NOT EXISTS task_events (
    seq INTEGER PRIMARY KEY REFERENCES event_receipts(seq), project TEXT NOT NULL,
    task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, source_order INTEGER,
    summary TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(project,task_id,attempt_id,source_order)
);
CREATE INDEX IF NOT EXISTS events_by_project ON task_events(project,seq DESC);
CREATE TABLE IF NOT EXISTS task_attempts (
    project TEXT NOT NULL, task_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
    source TEXT NOT NULL, role TEXT NOT NULL, identity TEXT NOT NULL,
    last_seq INTEGER NOT NULL REFERENCES event_receipts(seq), last_order INTEGER,
    status TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(project,task_id,attempt_id)
);
CREATE TABLE IF NOT EXISTS wiki_entry_versions (
    project TEXT NOT NULL, entry_id TEXT NOT NULL, version TEXT NOT NULL, parent_version TEXT,
    path TEXT NOT NULL, body TEXT NOT NULL, digest TEXT NOT NULL, anchor TEXT NOT NULL,
    seq INTEGER NOT NULL REFERENCES event_receipts(seq), PRIMARY KEY(project,entry_id,version)
);
CREATE INDEX IF NOT EXISTS wiki_parents ON wiki_entry_versions(project,entry_id,parent_version);
CREATE TABLE IF NOT EXISTS quota_refresh_jobs (
    job_id INTEGER PRIMARY KEY REFERENCES event_receipts(seq), project TEXT NOT NULL,
    account TEXT NOT NULL, tool TEXT NOT NULL, state TEXT NOT NULL, worker TEXT,
    lease_token TEXT, lease_until REAL, next_try REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS quota_pending ON quota_refresh_jobs(project,account,state,next_try,job_id);
CREATE TABLE IF NOT EXISTS quota_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL REFERENCES quota_refresh_jobs(job_id),
    project TEXT NOT NULL, account TEXT NOT NULL, pool TEXT NOT NULL, lease_token TEXT NOT NULL,
    digest TEXT NOT NULL, observed_at REAL NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL,
    UNIQUE(job_id,lease_token)
);
CREATE INDEX IF NOT EXISTS quota_latest ON quota_snapshots(project,account,pool,observed_at DESC,snapshot_id DESC);
"""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _text(value, name, maximum=256):
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > maximum or "\x00" in value:
        raise ValueError(f"invalid_{name}")
    return value


def _utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp(value, name):
    try:
        dt = datetime.fromisoformat(_text(value, name).replace("Z", "+00:00"))
        if dt.utcoffset() is None:
            raise ValueError()
        return dt.timestamp()
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _bounded(value, limit):
    if not isinstance(value, dict):
        raise ValueError("invalid_object")
    try:
        payload = _json(value)
        if len(payload.encode("utf-8")) > limit:
            raise ValueError("payload_too_large")
    except (TypeError, RecursionError) as exc:
        raise ValueError("invalid_json") from exc
    return payload


def _validate_references(refs):
    if not isinstance(refs, list) or len(refs) > 32:
        raise ValueError("invalid_references")
    for ref in refs:
        if isinstance(ref, str):
            _text(ref, "reference", 2048)
        elif isinstance(ref, dict) and ref and set(ref) <= REFERENCE_FIELDS:
            for value in ref.values():
                _text(value, "reference_field", 2048)
        else:
            raise ValueError("invalid_reference")


def _receipt(row):
    return {
        "event_id": row["event_id"],
        "seq": row["seq"],
        "task_id": row["task_id"],
        "attempt_id": row["attempt_id"],
        "usage_job_id": row["seq"],
    }


def _record_wiki(db, project, seq, wiki):
    from .wiki_sync import validate_shared_wiki
    _bounded(wiki, 98304)
    entry = _text(wiki.get("entry_id"), "wiki_entry_id")
    validate_shared_wiki(db, project, entry, wiki)
    version = _text(wiki.get("version", wiki.get("revision")), "wiki_version")
    body = _text(wiki.get("body"), "wiki_body", 81920)
    path = _text(wiki.get("path"), "wiki_path", 1024)
    if "\\" in path or ":" in path or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
        raise ValueError("invalid_wiki_path")
    digest = _digest(body)
    if wiki.get("sha256", digest) != digest:
        raise ValueError("wiki_hash_mismatch")
    parent = wiki.get("parent_version")
    if parent is not None:
        _text(parent, "wiki_parent")
        if parent == version:
            raise ValueError("invalid_wiki_parent")
    anchor = wiki.get("anchor", "")
    if anchor != "":
        _text(anchor, "wiki_anchor", 512)
    expected = (parent, path, body, digest, anchor)
    old = db.execute("""SELECT parent_version,path,body,digest,anchor FROM wiki_entry_versions
                        WHERE project=? AND entry_id=? AND version=?""", (project, entry, version)).fetchone()
    if old is None:
        if parent is not None and db.execute(
            "SELECT 1 FROM wiki_entry_versions WHERE project=? AND entry_id=? AND version=?",
            (project, entry, parent)
        ).fetchone() is None:
            raise ValueError("wiki_parent_missing")
        db.execute("INSERT INTO wiki_entry_versions VALUES (?,?,?,?,?,?,?,?,?)",
                   (project, entry, version, *expected, seq))
    elif tuple(old) != expected:
        raise ValueError("wiki_version_conflict")
    return {"entry_id": entry, "version": version, "path": path, "anchor": anchor, "sha256": digest}


def _upsert_attempt(db, project, source, seq, event, now):
    task, attempt = event["task_id"], event["attempt_id"]
    current = db.execute("SELECT primary_attempt_id FROM task_current WHERE project=? AND task_id=?",
                         (project, task)).fetchone()
    previous = db.execute("SELECT * FROM task_attempts WHERE project=? AND task_id=? AND attempt_id=?",
                          (project, task, attempt)).fetchone()
    role = event.get("role", previous["role"] if previous else "primary")
    if role not in ("primary", "verify"):
        raise ValueError("invalid_role")
    fields = ("account", "tool", "host", "window_id", "session_id", "generation",
              "host_installation_id", "terminal_session_id", "journal_id")
    identity = json.loads(previous["identity"]) if previous else {}
    for field in fields:
        if field not in event:
            continue
        if field in identity and identity[field] != event[field]:
            raise ValueError("attempt_identity_conflict")
        identity[field] = event[field]
    if previous is not None and (source != previous["source"] or role != previous["role"]):
        raise ValueError("attempt_owner_conflict")
    prior_payload = json.loads(previous["payload"]) if previous else {}
    if current is None:
        if role != "primary" or event.get("previous_attempt_id"):
            raise ValueError("unknown_task")
        db.execute("INSERT INTO task_current VALUES (?,?,?,?)", (project, task, attempt, now))
    elif not previous and role == "primary":
        if event.get("previous_attempt_id") != current["primary_attempt_id"]:
            raise ValueError("handoff_conflict")
        prior = db.execute("SELECT payload FROM task_attempts WHERE project=? AND task_id=? AND attempt_id=?",
                           (project, task, current["primary_attempt_id"])).fetchone()
        prior_payload = json.loads(prior["payload"])
        db.execute("UPDATE task_current SET primary_attempt_id=?,updated_at=? WHERE project=? AND task_id=?",
                   (attempt, now, project, task))
    order = event.get("source_seq")
    if previous and previous["last_order"] is not None:
        if order is None:
            raise ValueError("source_seq_required")
        if order < previous["last_order"]:
            return
        if order == previous["last_order"]:
            raise ValueError("source_sequence_conflict")
    snapshot = {**identity, **event}
    if "required_verifications" in prior_payload:
        snapshot.setdefault("required_verifications", prior_payload["required_verifications"])
    if previous:
        for key in ("artifact", "window", "previous_attempt_id"):
            if key in prior_payload:
                snapshot.setdefault(key, prior_payload[key])
    db.execute("""INSERT INTO task_attempts VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(project,task_id,attempt_id) DO UPDATE SET identity=excluded.identity,
        last_seq=excluded.last_seq,last_order=excluded.last_order,status=excluded.status,payload=excluded.payload""",
        (project, task, attempt, source, role, _json(identity), seq, order, event["status"], _json(snapshot)))
    db.execute("UPDATE task_current SET updated_at=? WHERE project=? AND task_id=?", (now, project, task))


def _verification_status(primary, attempts):
    required = set(primary.get("required_verifications", []))
    verifiers = [a for a in attempts if a["role"] == "verify"]
    if not required and not verifiers:
        return "none"
    if not verifiers:
        return "pending"
    baseline = primary.get("artifact")
    if not baseline or any(item.get("artifact") != baseline for item in verifiers):
        return "baseline_unaligned"
    verdicts = {item.get("verdict") for item in verifiers}
    if {"pass", "fail"} <= verdicts:
        return "conflict"
    if "fail" in verdicts:
        return "failed"
    accounted = {item["attempt_id"] for item in verifiers}
    if verdicts == {"pass"} and required <= accounted:
        return "passed"
    return "pending"


class Store:
    """Authorization of project/account/source is performed by the calling service."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            sqlite_version = sqlite3.sqlite_version_info
            patched = (sqlite_version >= (3, 51, 3)
                       or (3, 50, 7) <= sqlite_version < (3, 51, 0)
                       or (3, 44, 6) <= sqlite_version < (3, 45, 0))
            if not patched and db.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
                raise ValueError("unsafe_wal_runtime")
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version == 1:
                if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='hub_maintenance'").fetchone():
                    raise ValueError("unrecognized_database")
                return
            if version != 0:
                raise ValueError("unsupported_schema")
            if db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
                raise ValueError("unrecognized_database")
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    db.execute(statement)
            db.execute("PRAGMA user_version=1")
            db.commit()
            if patched:
                db.execute("PRAGMA journal_mode=WAL")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextmanager
    def _db(self, *, write=False):
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            if write and db.execute("SELECT seal FROM hub_maintenance WHERE singleton=1").fetchone():
                raise ValueError("database_sealed")
            yield db

    def report_step(self, project, source, event):
        _text(project, "project")
        _text(source, "source")
        if source == SCHEDULED_SOURCE:
            raise ValueError("reserved_source")
        digest = _digest(_bounded(event, 131072))
        event = dict(event)
        if set(event) - EVENT_TEXT_FIELDS - {"generation", "source_seq", "wiki", "evidence", "skills", "required_verifications"}:
            raise ValueError("invalid_step_fields")
        for key in ("event_id", "task_id", "attempt_id", "account", "tool", "status"):
            _text(event.get(key), key)
        _text(event.get("summary"), "summary", 8192)
        if "artifact_digest" in event:
            if event.setdefault("artifact", event["artifact_digest"]) != event["artifact_digest"]:
                raise ValueError("artifact_conflict")
        for name in EVENT_TEXT_FIELDS.intersection(event) - {"summary"}:
            _text(event[name], name, 1024)
        if "generation" in event:
            generation = event["generation"]
            if type(generation) is int:
                if not 0 <= generation < 2**63:
                    raise ValueError("invalid_generation")
            else:
                _text(generation, "generation")
        for name in ("evidence", "skills"):
            if name in event:
                _validate_references(event[name])
        if event.get("verdict") is not None and event["verdict"] not in ("pass", "fail", "unknown"):
            raise ValueError("invalid_verdict")
        required = event.get("required_verifications", [])
        if not isinstance(required, list) or len(required) > 32:
            raise ValueError("invalid_required_verifications")
        for verifier in required:
            _text(verifier, "verifier_id")
        if len(set(required)) != len(required) or event["attempt_id"] in required:
            raise ValueError("invalid_required_verifications")
        order = event.get("source_seq")
        if order is not None and (type(order) != int or not 1 <= order < 2**63):
            raise ValueError("invalid_source_seq")
        now = time.time()
        with self._db(write=True) as db:
            ids = (project, source, event["event_id"])
            row = db.execute("SELECT * FROM event_receipts WHERE project=? AND source=? AND event_id=?", ids).fetchone()
            if row:
                if row["digest"] != digest:
                    raise ValueError("event_id_conflict")
                return _receipt(row)
            seq = db.execute("""INSERT INTO event_receipts(project,source,event_id,task_id,attempt_id,digest,accepted_at)
                               VALUES(?,?,?,?,?,?,?)""", (*ids, event["task_id"], event["attempt_id"], digest, now)).lastrowid
            if "wiki" in event:
                event["wiki"] = _record_wiki(db, project, seq, event["wiki"])
            try:
                db.execute("INSERT INTO task_events VALUES (?,?,?,?,?,?,?)",
                    (seq, project, event["task_id"], event["attempt_id"], order, event["summary"], _json(event)))
            except sqlite3.IntegrityError as exc:
                raise ValueError("source_sequence_conflict") from exc
            _upsert_attempt(db, project, source, seq, event, now)
            db.execute("""INSERT INTO quota_refresh_jobs(job_id,project,account,tool,state,next_try)
                          VALUES(?,?,?,?,'pending',?)""", (seq, project, event["account"], event["tool"], now))
            return _receipt({"seq": seq, **{k: event[k] for k in ("event_id", "attempt_id", "task_id")}})

    def search_task_events(self, project, query="", limit=50):
        if type(limit) != int or not 1 <= limit <= 100 or not isinstance(query, str) or len(query) > 512:
            raise ValueError("invalid_search")
        with self._db() as db:
            rows = db.execute("""SELECT e.seq,e.payload,r.accepted_at,r.source FROM task_events e
                JOIN event_receipts r ON e.seq=r.seq WHERE e.project=?
                AND (?='' OR instr(e.summary,?)>0 OR instr(e.task_id,?)>0)
                ORDER BY e.seq DESC LIMIT ?""", (_text(project, "project"), query, query, query, limit))
            return {"events": [{**json.loads(r["payload"]), "seq": r["seq"], "source": r["source"],
                               "accepted_at": _utc(r["accepted_at"])} for r in rows]}

    def get_wiki_entry(self, project, entry_id, version=None):
        from .wiki_sync import ensure_wiki_visible
        args = (_text(project, "project"), _text(entry_id, "entry_id"))
        with self._db() as db:
            ensure_wiki_visible(db, project, entry_id)
            if version is None:
                rows = db.execute("""SELECT version FROM wiki_entry_versions w WHERE project=? AND entry_id=?
                    AND NOT EXISTS(SELECT 1 FROM wiki_entry_versions c WHERE c.project=w.project
                    AND c.entry_id=w.entry_id AND c.parent_version=w.version) ORDER BY seq DESC""", args)
                return {"entry_id": entry_id, "heads": [r["version"] for r in rows]}
            row = db.execute("""SELECT entry_id,version,parent_version,path,anchor,body,digest AS sha256,seq
                FROM wiki_entry_versions WHERE project=? AND entry_id=? AND version=?""", (*args, _text(version, "version"))).fetchone()
            if row is None:
                raise ValueError("wiki_not_found")
            return dict(row)

    def list_tasks(self, project, status=None, limit=50, before=None):
        project = _text(project, "project")
        if type(limit) != int or not 1 <= limit <= 100:
            raise ValueError("invalid_limit")
        if status is not None:
            _text(status, "status")
        if before is not None and (type(before) != int or not 0 < before < 2**63):
            raise ValueError("invalid_cursor")
        with self._db() as db:
            rows = db.execute("""SELECT c.*, MAX(a.last_seq) AS seq FROM task_current c
                JOIN task_attempts a ON a.project=c.project AND a.task_id=c.task_id
                WHERE c.project=?
                GROUP BY c.project,c.task_id HAVING (? IS NULL OR MAX(a.last_seq)<?)
                ORDER BY seq DESC""", (project, before, before))
            tasks = []
            next_before = None
            for row in rows:
                task = self._task_status(db, row)
                if (status == "attention" and task["status"] not in ATTENTION_STATES
                    and task["verification_status"] not in {"failed", "conflict", "baseline_unaligned"}):
                    continue
                if status not in (None, "attention") and task["status"] != status:
                    continue
                if len(tasks) == limit:
                    next_before = tasks[-1]["seq"]
                    break
                task.pop("attempts")
                task["seq"] = row["seq"]
                tasks.append(task)
            return {"tasks": tasks, "next_before": next_before}

    def get_task_status(self, project, task_id):
        args = (_text(project, "project"), _text(task_id, "task_id"))
        with self._db() as db:
            current = db.execute("SELECT * FROM task_current WHERE project=? AND task_id=?", args).fetchone()
            if current is None:
                raise ValueError("task_not_found")
            return self._task_status(db, current)

    @staticmethod
    def _task_status(db, current):
        args = (current["project"], current["task_id"])
        rows = db.execute("SELECT * FROM task_attempts WHERE project=? AND task_id=? ORDER BY last_seq", args)
        attempts = [{**json.loads(r["payload"]), "role": r["role"], "source": r["source"], "seq": r["last_seq"]} for r in rows]
        primary = next(a for a in attempts if a["attempt_id"] == current["primary_attempt_id"])
        verification = _verification_status(primary, attempts)
        status = primary["status"]
        if status in ("done", "completed", "succeeded"):
            status = {"pending": "awaiting_verification", "conflict": "needs_review",
                      "failed": "needs_review", "baseline_unaligned": "baseline_unaligned"}.get(verification, status)
        return {
            "task_id": current["task_id"], "primary_attempt_id": primary["attempt_id"],
            "status": status, "primary_status": primary["status"], "summary": primary["summary"],
            "event_id": primary["event_id"], "source": primary["source"],
            "attempts": attempts, "verification_status": verification,
            "required_verifications": primary.get("required_verifications", []),
            "updated_at": _utc(current["updated_at"]),
        }

    def claim_usage_job(self, project, account, worker, idle_after_seconds=None):
        args = (_text(project, "project"), _text(account, "account"))
        _text(worker, "worker")
        if idle_after_seconds is not None and (
            type(idle_after_seconds) != int or not 60 <= idle_after_seconds <= 7 * 86400
        ):
            raise ValueError("invalid_idle_interval")
        with self._db(write=True) as db:
            now = time.time()
            row = db.execute("""SELECT j.job_id,j.project,j.account,j.tool,r.source,r.event_id,r.accepted_at
                FROM quota_refresh_jobs j JOIN event_receipts r ON r.seq=j.job_id
                WHERE j.project=? AND j.account=? AND ((j.state='pending' AND j.next_try<=?)
                  OR (j.state='leased' AND j.lease_until<=?))
                ORDER BY (r.source=?),j.job_id LIMIT 1""", (*args, now, now, SCHEDULED_SOURCE)).fetchone()
            if row is None and idle_after_seconds is not None:
                row = self._schedule_idle_job(db, project, account, now, idle_after_seconds)
            if row is None:
                return None
            scheduled = row["source"] == SCHEDULED_SOURCE
            token = secrets.token_urlsafe(24)
            db.execute("""UPDATE quota_refresh_jobs SET state='leased',worker=?,lease_token=?,lease_until=?
                          WHERE job_id=?""", (worker, token, now + LEASE_SECONDS, row["job_id"]))
            return {
                **dict(row), "accepted_at": _utc(row["accepted_at"]), "claimed_at": _utc(now),
                "worker": worker, "lease_token": token, "lease_until": _utc(now + LEASE_SECONDS),
                "trigger": "scheduled" if scheduled else "step",
                "event_id": None if scheduled else row["event_id"],
            }

    @staticmethod
    def _schedule_idle_job(db, project, account, now, interval):
        # The caller holds the write transaction. A delayed retry or another
        # worker's live lease already accounts for this account's next query.
        pending = db.execute("""SELECT 1 FROM quota_refresh_jobs WHERE project=? AND account=?
                             AND state IN ('pending','leased') LIMIT 1""", (project, account)).fetchone()
        if pending:
            return None
        recent = db.execute("""SELECT 1 FROM quota_snapshots WHERE project=? AND account=?
                               AND observed_at>? LIMIT 1""", (project, account, now - interval)).fetchone()
        if recent:
            return None
        poll_id = secrets.token_hex(16)
        seq = db.execute("""INSERT INTO event_receipts
            (project,source,event_id,task_id,attempt_id,digest,accepted_at)
            VALUES (?,?,?,'','',?,?)""",
            (project, SCHEDULED_SOURCE, poll_id, _digest(_json([project, account, poll_id])), now)).lastrowid
        db.execute("""INSERT INTO quota_refresh_jobs(job_id,project,account,tool,state,next_try)
                      VALUES(?,?,?,'quota','pending',?)""", (seq, project, account, now))
        return {"job_id":seq, "project":project, "account":account, "tool":"quota",
                "source":SCHEDULED_SOURCE, "event_id":None, "accepted_at":now}

    def record_usage_snapshot(self, project, account, snapshot):
        _text(project, "project")
        _text(account, "account")
        digest = _digest(_bounded(snapshot, 32768))
        snap = dict(snapshot)
        allowed = {"job_id", "lease_token", "project", "account", "provider", "source", "pool",
                   "status", "observed_at", "windows", "retry_after_seconds"}
        if set(snap) - allowed:
            raise ValueError("invalid_snapshot_fields")
        if snap.get("account", account) != account or snap.get("project", project) != project:
            raise ValueError("snapshot_binding_mismatch")
        for name in ("provider", "source"):
            if name in snap:
                _text(snap[name], name, 160)
        token = _text(snap.pop("lease_token", None), "lease_token")
        job_id = snap.get("job_id")
        if type(job_id) != int or not 0 < job_id < 2**63:
            raise ValueError("invalid_job_id")
        status = snap.get("status")
        if status not in ("ok", "rate_limited", "unavailable", "auth_required", "unsupported"):
            raise ValueError("invalid_usage_status")
        pool = _text(snap.get("pool", account), "pool")
        observed = _timestamp(snap.get("observed_at"), "observed_at")
        windows = snap.get("windows", [])
        if not isinstance(windows, list) or len(windows) > 32 or (status == "ok" and not windows):
            raise ValueError("invalid_windows")
        for window in windows:
            if not isinstance(window, dict):
                raise ValueError("invalid_window")
            if set(window) - {"period", "unit", "remaining", "reset_at", "window_minutes"}:
                raise ValueError("invalid_window_fields")
            _text(window.get("period"), "period", 64)
            _text(window.get("unit"), "unit", 32)
            remaining = window.get("remaining")
            if remaining is not None:
                if type(remaining) not in (int, float) or not 0 <= remaining <= 2**63 - 1:
                    raise ValueError("invalid_remaining")
                if window["unit"] == "percent" and remaining > 100:
                    raise ValueError("invalid_remaining")
            if window.get("window_minutes") is not None:
                minutes = window["window_minutes"]
                if type(minutes) != int or minutes <= 0:
                    raise ValueError("invalid_window_minutes")
            if window.get("reset_at") is not None:
                _timestamp(window["reset_at"], "reset_at")
        retry = snap.get("retry_after_seconds", 60)
        if type(retry) != int or not 1 <= retry <= 7*86400:
            raise ValueError("invalid_retry_delay")
        with self._db(write=True) as db:
            old = db.execute("""SELECT snapshot_id,digest FROM quota_snapshots WHERE project=? AND account=?
                                AND job_id=? AND lease_token=?""", (project, account, job_id, token)).fetchone()
            if old:
                if old["digest"] != digest:
                    raise ValueError("snapshot_conflict")
                return {"snapshot_id": old["snapshot_id"], "job_id": job_id, "status": status}
            row = db.execute("""SELECT j.*,r.accepted_at FROM quota_refresh_jobs j JOIN event_receipts r
                ON r.seq=j.job_id WHERE job_id=? AND j.project=? AND j.account=?""", (job_id, project, account)).fetchone()
            now = time.time()
            if not row or row["state"] != "leased" or row["lease_until"] <= now or not secrets.compare_digest(row["lease_token"], token):
                raise ValueError("invalid_or_expired_lease")
            # A provider export may be observed after the step but before a worker
            # claims its refresh. Both the observation and this query follow the step.
            if observed + 0.000001 < row["accepted_at"] or observed > now + 60:
                raise ValueError("invalid_sample_time")
            snapshot_id = db.execute("""INSERT INTO quota_snapshots(job_id,project,account,pool,lease_token,digest,
                observed_at,status,payload) VALUES(?,?,?,?,?,?,?,?,?)""",
                (job_id, project, account, pool, token, digest, observed, status, _json(snap))).lastrowid
            state = "pending" if status in {"rate_limited", "unavailable"} else "completed"
            db.execute("""UPDATE quota_refresh_jobs SET state=?,next_try=?,lease_token=NULL,worker=NULL,lease_until=NULL
                          WHERE job_id=?""", (state, now+retry, job_id))
            return {"snapshot_id": snapshot_id, "job_id": job_id, "status": status}

    def get_usage_overview(self, project):
        with self._db() as db:
            args = (_text(project, "project"),)
            rows = db.execute("""SELECT DISTINCT account,pool FROM quota_snapshots WHERE project=?
                UNION SELECT DISTINCT j.account,j.account FROM quota_refresh_jobs j WHERE j.project=?
                AND NOT EXISTS(SELECT 1 FROM quota_snapshots s WHERE s.project=j.project AND s.account=j.account)
                ORDER BY account,pool""", args+args).fetchall()
            result = []
            for account, pool in rows:
                item = {"account": account, "pool": pool}
                for name, condition in (("latest", ""), ("last_success", " AND status='ok'")):
                    row = db.execute("SELECT snapshot_id,payload FROM quota_snapshots WHERE project=? AND account=? AND pool=?"
                        +condition+" ORDER BY observed_at DESC,snapshot_id DESC LIMIT 1", (*args, account, pool)).fetchone()
                    item[name] = {**json.loads(row["payload"]), "snapshot_id": row["snapshot_id"]} if row else None
                item["pending_jobs"] = db.execute(
                    "SELECT count(*) FROM quota_refresh_jobs WHERE project=? AND account=? AND state!='completed'",
                    (project, account),
                ).fetchone()[0]
                result.append(item)
            return {"accounts": result}
