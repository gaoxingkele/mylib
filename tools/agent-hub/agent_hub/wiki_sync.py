"""Synchronize explicitly shared wiki revisions and apply project-scoped withdrawals."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time

from .hooks import DAY, MAX_PENDING, canonical, safe_text


def _name(value, label):
    if not isinstance(value, str) or not value.strip() or "\0" in value or len(value.encode()) > 256:
        raise ValueError("invalid_" + label)
    return value


def _tables(db):
    db.execute("""CREATE TABLE IF NOT EXISTS wiki_withdrawals (
        project TEXT NOT NULL, entry_id TEXT NOT NULL, withdrawn_at REAL NOT NULL,
        PRIMARY KEY(project,entry_id))""")
    db.execute("""CREATE TABLE IF NOT EXISTS wiki_write_receipts (
        project TEXT NOT NULL, source TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
        receipt TEXT NOT NULL, PRIMARY KEY(project,source,request_id))""")


def ensure_wiki_visible(db, project, entry):
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='wiki_withdrawals'").fetchone():
        if db.execute("SELECT 1 FROM wiki_withdrawals WHERE project=? AND entry_id=?", (project, entry)).fetchone():
            raise ValueError("wiki_not_found")


def privacy_epoch(store, project):
    """Recheck before returning a long-lived read or external model response."""
    with store._db() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='wiki_withdrawals'").fetchone():
            return 0
        return db.execute("SELECT count(*) FROM wiki_withdrawals WHERE project=?", (project,)).fetchone()[0]


def _previous(db, project, source, request_id, digest):
    row = db.execute("""SELECT digest,receipt FROM wiki_write_receipts
        WHERE project=? AND source=? AND request_id=?""", (project, source, request_id)).fetchone()
    if row is None:
        return None
    if row[0] != digest:
        raise ValueError("wiki_request_conflict")
    return json.loads(row[1])


def _receipt(db, project, source, request_id, digest, result):
    db.execute("INSERT INTO wiki_write_receipts VALUES(?,?,?,?,?)",
               (project, source, request_id, digest, canonical(result)))
    return result


def _body(text):
    # Preserve the approved Markdown exactly. A secret requires a revised, explicitly
    # shared local file, so the two replicas never silently acquire different content.
    if safe_text(text, 81920) != text.strip():
        raise ValueError("wiki_requires_redaction")
    frontmatter = re.match(r"\A\ufeff?---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if frontmatter and re.search(
        r"(?im)^\s*(?:visibility\s*:\s*['\"]?private|private\s*:\s*['\"]?true|"
        r"share\s*:\s*['\"]?false)['\"]?\s*(?:#.*)?$", frontmatter[1]
    ):
        raise ValueError("private_wiki_entry")
    return text


def validate_shared_wiki(db, project, entry, wiki):
    ensure_wiki_visible(db, project, entry)
    if (wiki.get("private") is True or wiki.get("share") is False
            or wiki.get("visibility", "project") not in ("project", "shared")):
        raise ValueError("private_wiki_entry")
    _body(wiki.get("body"))


def sync_wiki(store, project, source, revision):
    from .storage import _record_wiki
    _name(project, "project")
    _name(source, "source")
    if not isinstance(revision, dict) or set(revision) - {
        "request_id", "task_id", "attempt_id", "entry_id", "version", "parent_version",
        "path", "anchor", "body", "sha256"
    }:
        raise ValueError("invalid_wiki_revision")
    for key in ("request_id", "task_id", "attempt_id", "entry_id", "version"):
        _name(revision.get(key), key)
    _body(revision.get("body"))
    request_id, task, attempt = (revision[key] for key in ("request_id", "task_id", "attempt_id"))
    digest = hashlib.sha256(canonical(["sync", revision]).encode()).hexdigest()
    with store._db(write=True) as db:
        _tables(db)
        entry = revision["entry_id"]
        ensure_wiki_visible(db, project, entry)
        prior = _previous(db, project, source, request_id, digest)
        if prior:
            return prior
        if not db.execute("SELECT 1 FROM task_attempts WHERE project=? AND source=? AND task_id=? "
                          "AND attempt_id=?", (project, source, task, attempt)).fetchone():
            raise ValueError("wiki_attempt_unavailable")
        exists = db.execute("SELECT 1 FROM wiki_entry_versions WHERE project=? AND entry_id=?",
                            (project, entry)).fetchone()
        if exists and not revision.get("parent_version"):
            raise ValueError("wiki_parent_required")
        # Pure revisions occupy the same global event sequence but create no quota job.
        # The internal NUL namespace cannot collide with report_step's validated source IDs.
        seq = db.execute("""INSERT INTO event_receipts (
            project,source,event_id,task_id,attempt_id,digest,accepted_at) VALUES(?,?,?,?,?,?,?)""",
            (project, "\0wiki:" + source, request_id, task, attempt, digest, time.time())).lastrowid
        wiki = {k: v for k, v in revision.items() if k not in ("request_id", "task_id", "attempt_id")}
        _record_wiki(db, project, seq, wiki)
        return _receipt(db, project, source, request_id, digest, {
            "entry_id": entry, "version": revision["version"], "request_id": request_id,
            "seq": seq, "status": "recorded"})


def _redact_entry(db, project, entry, timestamp):
    db.execute("INSERT OR IGNORE INTO wiki_withdrawals VALUES (?,?,?)", (project, entry, timestamp))
    for table in ("task_events", "task_attempts"):
        rows = db.execute(f"""SELECT rowid,payload FROM {table} WHERE project=?
            AND json_extract(payload,'$.wiki.entry_id')=?""", (project, entry)).fetchall()
        for rowid, raw in rows:
            old = json.loads(raw)
            clean = {k: old[k] for k in ("event_id", "task_id", "attempt_id", "tool", "account",
                                         "source_seq", "generation", "role") if k in old}
            clean.update(summary="Evidence withdrawn", status="evidence_withdrawn")
            column = "summary" if table == "task_events" else "status"
            db.execute(f"UPDATE {table} SET payload=?,{column}=? WHERE rowid=?",
                       (canonical(clean), clean[column], rowid))
    db.execute("DELETE FROM wiki_entry_versions WHERE project=? AND entry_id=?", (project, entry))


def withdraw_wiki(store, project, source, entry_id, request_id):
    for name, value in (("project", project), ("source", source), ("entry_id", entry_id), ("request_id", request_id)):
        _name(value, name)
    digest = hashlib.sha256(canonical(["withdraw", entry_id]).encode()).hexdigest()
    with store._db(write=True) as db:
        _tables(db)
        prior = _previous(db, project, source, request_id, digest)
        if prior:
            return prior
        _redact_entry(db, project, entry_id, time.time())
        return _receipt(db, project, source, request_id, digest,
                        {"entry_id": entry_id, "request_id": request_id, "status": "withdrawn"})


def replay_withdrawals(destination, authority):
    """Replay the latest trusted restriction state when restoring a historical copy."""
    _tables(destination)
    if authority.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='wiki_withdrawals'").fetchone():
        for project, entry, timestamp in authority.execute("SELECT project,entry_id,withdrawn_at FROM wiki_withdrawals"):
            _redact_entry(destination, project, entry, timestamp)


def _approved_file(project_root, wiki_directory, relative):
    root = Path(project_root).resolve(strict=True)
    allowed, name = Path(wiki_directory), Path(relative)
    if (not allowed.parts or not name.parts or allowed.is_absolute() or name.is_absolute()
            or ".." in (*allowed.parts, *name.parts) or not name.is_relative_to(allowed)
            or name.suffix.lower() != ".md"):
        raise ValueError("file_outside_wiki_directory")
    path = root
    for part in name.parts:
        if part.casefold() == ".git" or ":" in part:
            raise ValueError("invalid_wiki_file")
        path = path / part
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked_wiki_file")
    if not path.resolve(strict=True).is_relative_to(root) or not stat.S_ISREG(info.st_mode) or info.st_size > 81920:
        raise ValueError("invalid_wiki_file")
    with path.open("rb") as stream:
        raw = stream.read(81921)
    if len(raw) > 81920:
        raise ValueError("wiki_too_large")
    return _body(raw.decode("utf-8"))


class WikiOutbox:
    """Capture the approved revision even if an external wiki writer later edits its file."""

    def __init__(self, config):
        self.project = _name(config["project"], "project")
        self.task = _name(config["task_id"], "task_id")
        self.attempt = _name(config["attempt_id"], "attempt_id")
        if not all(Path(config[key]).is_absolute() for key in ("project_root","state_dir")):
            raise ValueError("absolute_binding_paths_required")
        self.root = Path(config["project_root"]).resolve(strict=True)
        self.wiki_dir = config.get("wiki_share_dir", config.get("wiki_dir", "omx_wiki"))
        state = Path(config["state_dir"]).resolve()
        if state.is_relative_to(self.root):
            raise ValueError("private_outbox_directory_required")
        state.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = state / "wiki-outbox.sqlite3"
        self.scope = hashlib.sha256(canonical([self.project, self.task, self.attempt, str(self.root),
                                               self.wiki_dir, config.get("endpoint")]).encode()).hexdigest()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS wiki_queue (
                seq INTEGER PRIMARY KEY, scope TEXT, project TEXT, entry_id TEXT, operation TEXT, request_id TEXT, payload TEXT,
                created REAL, delivered REAL, UNIQUE(scope,request_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS private_entries (
                project TEXT, entry_id TEXT, PRIMARY KEY(project,entry_id))""")

    def stage(self, relative, entry_id, version, expected_sha256, parent=None):
        _name(entry_id, "entry_id")
        _name(version, "version")
        if parent is not None:
            _name(parent, "parent_version")
        text = _approved_file(self.root, self.wiki_dir, relative)
        digest = hashlib.sha256(text.encode()).hexdigest()
        if digest != expected_sha256:
            raise ValueError("wiki_file_changed")
        request_id = hashlib.sha256(canonical([self.scope, entry_id, version]).encode()).hexdigest()
        revision = {"request_id": request_id, "task_id": self.task, "attempt_id": self.attempt,
                    "entry_id": entry_id, "version": version, "path": Path(relative).as_posix(),
                    "body": text, "sha256": digest, "parent_version": parent}
        payload = canonical(revision)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM private_entries WHERE project=? AND entry_id=?",
                          (self.project,entry_id)).fetchone():
                raise ValueError("private_wiki_entry")
            row = db.execute("SELECT payload FROM wiki_queue WHERE scope=? AND request_id=?",
                             (self.scope, request_id)).fetchone()
            if row and row[0] != payload:
                raise ValueError("wiki_request_conflict")
            if not row:
                if db.execute("SELECT count(*) FROM wiki_queue WHERE delivered IS NULL").fetchone()[0] >= MAX_PENDING:
                    raise ValueError("wiki_outbox_full")
                db.execute("INSERT INTO wiki_queue(scope,project,entry_id,operation,request_id,payload,created) "
                           "VALUES(?,?,?,'sync_wiki',?,?,?)",
                           (self.scope,self.project,entry_id,request_id,payload,time.time()))
        return request_id

    def stage_withdrawal(self, entry_id):
        _name(entry_id, "entry_id")
        request_id = hashlib.sha256(canonical([self.scope,"withdraw",entry_id]).encode()).hexdigest()
        payload = canonical({"entry_id":entry_id, "request_id":request_id})
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO private_entries VALUES(?,?)", (self.project,entry_id))
            db.execute("DELETE FROM wiki_queue WHERE project=? AND entry_id=? AND operation='sync_wiki'",
                       (self.project,entry_id))
            db.execute("INSERT OR IGNORE INTO wiki_queue(scope,project,entry_id,operation,request_id,payload,created) "
                       "VALUES(?,?,?,'withdraw_wiki',?,?,?)",
                       (self.scope,self.project,entry_id,request_id,payload,time.time()))
        return request_id

    def flush(self, send, limit=50):
        if type(limit) is not int or not 1 <= limit <= MAX_PENDING:
            raise ValueError("invalid_limit")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM wiki_queue WHERE delivered<?", (time.time() - 35 * DAY,))
            rows = db.execute("SELECT seq,operation,payload FROM wiki_queue WHERE scope=? AND delivered IS NULL "
                              "AND (operation='withdraw_wiki' OR created>=?) "
                              "ORDER BY operation='withdraw_wiki' DESC,seq LIMIT ?",
                              (self.scope,time.time()-14*DAY,limit)).fetchall()
        sent = 0
        for seq, operation, payload in rows:
            item = json.loads(payload)
            if operation == "sync_wiki":
                with closing(sqlite3.connect(self.path)) as db:
                    if db.execute("SELECT 1 FROM private_entries WHERE project=? AND entry_id=?",
                                  (self.project,item["entry_id"])).fetchone():
                        continue
                arguments, status, keys = {"revision":item}, "recorded", ("request_id","entry_id","version")
            else:
                arguments, status, keys = item, "withdrawn", ("entry_id","request_id")
            receipt = send(operation, {"project": self.project, **arguments})
            if not isinstance(receipt,dict) or receipt.get("status") != status or any(
                receipt.get(key) != item[key] for key in keys
            ):
                raise ValueError("wiki_receipt_mismatch")
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute("UPDATE wiki_queue SET delivered=? WHERE scope=? AND seq=?", (time.time(),self.scope,seq))
            sent += 1
        return sent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    share = commands.add_parser("share-file")
    for field in ("path", "entry", "version", "sha256"):
        share.add_argument("--" + field, required=True)
    share.add_argument("--parent")
    commands.add_parser("withdraw").add_argument("--entry", required=True)
    commands.add_parser("flush")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    box = WikiOutbox(config)
    if args.command == "share-file":
        print(json.dumps({"request_id":box.stage(args.path, args.entry, args.version, args.sha256, args.parent)}))
    elif args.command == "withdraw":
        print(json.dumps({"request_id":box.stage_withdrawal(args.entry)}))
    else:
        from .client import call_tool
        def send(name, arguments):
            return call_tool(name, arguments, endpoint=config["endpoint"], token=os.environ["AGENT_HUB_TOKEN"])
        print(json.dumps({"delivered":box.flush(send)}))


if __name__ == "__main__":
    main()
