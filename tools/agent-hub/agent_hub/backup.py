"""Backup, rotate and verify the agent hub's local SQLite store."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import uuid


def _open(path, mode):
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=" + mode,
                                 uri=True, timeout=10, isolation_level=None)
    connection.execute("PRAGMA foreign_keys=ON")
    if mode == "ro":
        connection.execute("PRAGMA query_only=ON")
    else:
        connection.execute("PRAGMA synchronous=FULL")
    return connection


def _sync_directory(directory):
    if os.name == "posix":
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _write_json(path, value):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode="w",
                                     encoding="utf-8") as stream:
        temp_path = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            stream.close()
            temp_path.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp_path, path)
        _sync_directory(path.parent)
    finally:
        temp_path.unlink(missing_ok=True)


def _checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inspect(db):
    version = db.execute("PRAGMA user_version").fetchone()[0]
    if version != 1:
        raise ValueError("unsupported_hub_schema")
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("sqlite_integrity_failed")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("sqlite_foreign_key_failed")
    tables = ("event_receipts", "task_events", "task_attempts", "task_current",
              "wiki_entry_versions", "quota_refresh_jobs", "quota_snapshots")
    counts = {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
              for table in tables}
    high_water = db.execute("SELECT seq FROM sqlite_sequence WHERE name='event_receipts'").fetchone()
    return {"schema": version, "counts": counts, "sequence": high_water[0] if high_water else 0}


def _copy_db(source, destination):
    # Reserve the name exclusively; SQLite's default CREATE can overwrite an existing DB.
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    with closing(_open(source, "ro")) as src, closing(_open(destination, "rw")) as dst:
        src.backup(dst, pages=256)
        dst.execute("PRAGMA journal_mode=DELETE")
        return _inspect(dst)


def backup(source, directory):
    """Create an independent, self-contained snapshot and verification manifest."""
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    dest = directory / "snapshot.sqlite3"
    details = _copy_db(source, dest)
    details.update({"sha256": _checksum(dest), "bytes": dest.stat().st_size,
                    "created_at": datetime.now(timezone.utc).isoformat()})
    _write_json(directory / "snapshot.json", details)
    return verify(directory)


def verify(directory):
    directory = Path(directory)
    path = directory / "snapshot.sqlite3"
    metadata = json.loads((directory / "snapshot.json").read_text(encoding="utf-8"))
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-journal")):
        raise ValueError("unexpected_snapshot_sidecar")
    if path.stat().st_size != metadata["bytes"] or _checksum(path) != metadata["sha256"]:
        raise ValueError("snapshot_digest_mismatch")
    with closing(_open(path, "ro")) as db:
        details = _inspect(db)
    if any(value != metadata[key] for key, value in details.items()):
        raise ValueError("snapshot_manifest_mismatch")
    return metadata


def restore(directory, destination, revocations_from=None):
    """Restore a verified snapshot to a new path. Never replace the active file."""
    directory, destination = Path(directory), Path(destination)
    if os.path.lexists(destination):
        raise FileExistsError(destination)
    if any(os.path.lexists(str(destination) + suffix) for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("stale_restore_sidecar")
    expected = verify(directory)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        clone = Path(temp) / "restore.sqlite3"
        details = _copy_db(directory / "snapshot.sqlite3", clone)
        if any(value != expected[key] for key, value in details.items()):
            raise ValueError("restore_mismatch")
        with closing(_open(clone, "rw")) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM wiki_entry_versions LIMIT 1").fetchone() and revocations_from is None:
                raise ValueError("wiki_restore_requires_authoritative_revocations")
            if revocations_from is not None:
                from .wiki_sync import replay_withdrawals
                with closing(_open(revocations_from, "ro")) as authority:
                    authority.execute("BEGIN")
                    _inspect(authority)
                    replay_withdrawals(db, authority)
            db.execute("DELETE FROM hub_maintenance")
            db.commit()
            details = _inspect(db)
        os.link(clone, destination)
        _sync_directory(destination.parent)
    return details


def _prune(db, now):
    """Retain history, active evidence and idempotency across the generation boundary."""
    hot_cutoff = now - 7 * 86400
    receipts_cutoff = now - 35 * 86400
    db.execute("BEGIN IMMEDIATE")
    db.execute("CREATE TEMP TABLE feedback_pins(project TEXT, task_id TEXT, PRIMARY KEY(project,task_id))")
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='feedback_requests'").fetchone():
        db.execute("INSERT OR IGNORE INTO feedback_pins SELECT project,task_id FROM feedback_requests")
    # Keep reviewed/multi-attempt tasks until a future protocol explicitly records
    # resolution. Retire old, single-attempt completed tasks without pending work.
    db.execute("""
        CREATE TEMP TABLE archived_tasks AS
        SELECT t.project,t.task_id FROM task_current t
        JOIN task_attempts a ON a.project=t.project AND a.task_id=t.task_id
        WHERE t.updated_at < ? AND a.status IN ('completed','failed','cancelled')
          AND a.attempt_id=t.primary_attempt_id
          AND (t.project,t.task_id) NOT IN (SELECT project,task_id FROM feedback_pins)
          AND NOT EXISTS (SELECT 1 FROM task_attempts other WHERE other.project=t.project
              AND other.task_id=t.task_id AND other.attempt_id<>a.attempt_id)
          AND NOT EXISTS (SELECT 1 FROM quota_refresh_jobs j
              JOIN event_receipts r ON r.seq=j.job_id
              WHERE r.project=t.project AND r.task_id=t.task_id AND j.state<>'completed')
    """, (now - 30 * 86400,))
    for table in ("task_attempts", "task_current"):
        db.execute(f"DELETE FROM {table} WHERE (project,task_id) IN (SELECT * FROM archived_tasks)")
    db.execute("""
        CREATE TEMP TABLE kept_snapshots AS
        SELECT snapshot_id FROM quota_snapshots WHERE observed_at >= ?
        UNION
        SELECT snapshot_id FROM (
            SELECT snapshot_id, ROW_NUMBER() OVER (
                PARTITION BY project, account, pool ORDER BY observed_at DESC, snapshot_id DESC
            ) AS position FROM quota_snapshots
        ) WHERE position=1
        UNION
        SELECT snapshot_id FROM (
            SELECT snapshot_id, ROW_NUMBER() OVER (
                PARTITION BY project, account, pool ORDER BY observed_at DESC, snapshot_id DESC
            ) AS position FROM quota_snapshots WHERE status='ok'
        ) WHERE position=1
    """, (hot_cutoff,))
    db.execute("DELETE FROM quota_snapshots WHERE snapshot_id NOT IN (SELECT snapshot_id FROM kept_snapshots)")
    db.execute("""
        DELETE FROM quota_refresh_jobs
        WHERE state='completed'
          AND job_id IN (SELECT seq FROM event_receipts WHERE accepted_at < ?)
          AND job_id NOT IN (SELECT job_id FROM quota_snapshots)
    """, (hot_cutoff,))
    # Keep all heads (including forks), recent or operationally referenced versions
    # and their descendants. Removing a parent alone cannot create a false head;
    # retaining descendants of a pinned historical version prevents exactly that.
    db.execute("""
        WITH RECURSIVE kept(project,entry_id,version) AS (
          SELECT w.project,w.entry_id,w.version FROM wiki_entry_versions w
          JOIN event_receipts r ON r.seq=w.seq
          WHERE r.accepted_at >= ?
             OR w.seq IN (SELECT job_id FROM quota_refresh_jobs)
             OR w.seq IN (SELECT last_seq FROM task_attempts)
             OR (w.project,w.entry_id,w.version) IN (
                 SELECT project,json_extract(payload,'$.wiki.entry_id'),json_extract(payload,'$.wiki.version')
                 FROM task_attempts WHERE json_type(payload,'$.wiki')='object')
             OR (w.project,w.entry_id,w.version) IN (
                 SELECT e.project,json_extract(e.payload,'$.wiki.entry_id'),json_extract(e.payload,'$.wiki.version')
                 FROM task_events e JOIN event_receipts r ON r.seq=e.seq
                 WHERE json_type(e.payload,'$.wiki')='object'
                   AND (r.accepted_at>=? OR e.seq IN (SELECT job_id FROM quota_refresh_jobs)))
             OR NOT EXISTS (SELECT 1 FROM wiki_entry_versions child
                 WHERE child.project=w.project AND child.entry_id=w.entry_id AND child.parent_version=w.version)
          UNION
          SELECT c.project,c.entry_id,c.version FROM wiki_entry_versions c JOIN kept k
            ON c.project=k.project AND c.entry_id=k.entry_id AND c.parent_version=k.version)
        DELETE FROM wiki_entry_versions WHERE (project,entry_id,version) NOT IN (SELECT * FROM kept)
    """, (hot_cutoff, hot_cutoff))
    db.execute("""
        DELETE FROM task_events WHERE seq IN (SELECT seq FROM event_receipts WHERE accepted_at < ?)
          AND seq NOT IN (SELECT job_id FROM quota_refresh_jobs)
          AND seq NOT IN (SELECT last_seq FROM task_attempts WHERE last_seq IS NOT NULL)
          AND seq NOT IN (SELECT seq FROM wiki_entry_versions WHERE seq IS NOT NULL)
    """, (hot_cutoff,))
    db.execute("""
        DELETE FROM event_receipts WHERE accepted_at < ?
          AND seq NOT IN (SELECT seq FROM task_events)
          AND seq NOT IN (SELECT job_id FROM quota_refresh_jobs)
          AND seq NOT IN (SELECT last_seq FROM task_attempts WHERE last_seq IS NOT NULL)
          AND seq NOT IN (SELECT seq FROM wiki_entry_versions WHERE seq IS NOT NULL)
    """, (receipts_cutoff,))
    db.commit()
    db.execute("VACUUM")


def _seal(db, token):
    row = db.execute("SELECT seal FROM hub_maintenance WHERE singleton=1").fetchone()
    if row and row[0] != token:
        raise ValueError("another_rotation_owns_database")
    if not row:
        db.execute("INSERT INTO hub_maintenance(singleton,seal) VALUES (1,?)", (token,))


def _unseal(db, token):
    if db.execute("DELETE FROM hub_maintenance WHERE singleton=1 AND seal=?", (token,)).rowcount != 1:
        raise ValueError("rotation_seal_mismatch")


def _state_digest(db):
    # Logical digest is stable across checkpoints and catches updates to leases and wiki.
    # Exclude the single operational seal; it changes on activation and rollback.
    digest = hashlib.sha256()
    for statement in db.iterdump():
        if statement.startswith('INSERT INTO "hub_maintenance" VALUES('):
            continue
        digest.update(statement.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _verify_retention(db, archive, now):
    db.execute("ATTACH DATABASE ? AS original", (archive.resolve().as_uri() + "?mode=ro",))
    # Each expression selects the business rows that must survive rotation.
    required = {
        "event_receipts": ("accepted_at >= ?", (now - 35 * 86400,)),
        "task_events": ("seq IN (SELECT seq FROM original.event_receipts WHERE accepted_at >= ?)",
                        (now - 7 * 86400,)),
        "task_current": ("updated_at >= ? OR EXISTS (SELECT 1 FROM original.task_attempts a "
                         "WHERE a.project=t.project AND a.task_id=t.task_id "
                         "AND (a.status NOT IN ('completed','failed','cancelled') OR a.role='verify'))",
                         (now - 30 * 86400,)),
        "task_attempts": ("(project,task_id) IN (SELECT project,task_id FROM main.task_current)", ()),
        "quota_refresh_jobs": ("state <> 'completed'", ()),
        "wiki_entry_versions": ("NOT EXISTS (SELECT 1 FROM original.wiki_entry_versions c "
                                "WHERE c.project=t.project AND c.entry_id=t.entry_id AND c.parent_version=t.version)", ()),
    }
    for table, (condition, params) in required.items():
        missing = db.execute(f"SELECT * FROM original.{table} t WHERE {condition} "
                             f"EXCEPT SELECT * FROM main.{table} LIMIT 1", params).fetchone()
        if missing:
            raise ValueError(f"rotation_missing_{table}")
    for table in ("wiki_withdrawals", "wiki_write_receipts", "feedback_requests"):
        if db.execute("SELECT 1 FROM original.sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
            if db.execute(f"SELECT * FROM original.{table} EXCEPT SELECT * FROM main.{table} LIMIT 1").fetchone():
                raise ValueError(f"rotation_missing_{table}")
    # The UI displays latest observation and latest successful observation independently.
    for selection in ("", "WHERE status='ok'"):
        missing = db.execute(f"""
            SELECT snapshot_id FROM (
                SELECT snapshot_id, ROW_NUMBER() OVER (
                    PARTITION BY project,account,pool ORDER BY observed_at DESC,snapshot_id DESC
                ) AS position FROM original.quota_snapshots {selection}
            ) WHERE position=1 EXCEPT SELECT snapshot_id FROM main.quota_snapshots LIMIT 1
        """).fetchone()
        if missing:
            raise ValueError("rotation_missing_quota_current")
    db.execute("DETACH DATABASE original")


def rotate(source, directory):
    """Seal source, verify a full backup, publish a smaller active generation."""
    source, directory = Path(source).resolve(strict=True), Path(directory)
    directory.mkdir(mode=0o700, exist_ok=False)
    _sync_directory(directory.parent)
    with closing(_open(source, "ro")) as db:
        pages = db.execute("PRAGMA page_count").fetchone()[0]
        page_size = db.execute("PRAGMA page_size").fetchone()[0]
    # Allow room for the archive, its working clone, VACUUM and a rollback journal.
    if shutil.disk_usage(directory).free < pages * page_size * 4 + 1024 * 1024:
        raise ValueError("insufficient_rotation_space")
    token = uuid.uuid4().hex
    state = {"source": str(source), "seal": token, "phase": "preparing",
             "created_at": datetime.now(timezone.utc).isoformat()}
    metadata = directory / "rotation.json"
    _write_json(metadata, state)
    with closing(_open(source, "rw")) as db:
        db.execute("BEGIN IMMEDIATE")
        _seal(db, token)
        db.commit()
        # Serialize activation against a concurrent rollback. An interrupted
        # rotation releases the OS lock but preserves its recoverable source seal.
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT seal FROM hub_maintenance WHERE singleton=1").fetchone() != (token,):
            raise ValueError("rotation_seal_mismatch")
        return _build_generation(source, directory, token, metadata, state)


def _build_generation(source, directory, token, metadata, state):
    # Any error leaves the source sealed. The durable intent supports rollback even
    # after process loss. The new live name only appears after archive verification.
    archive = directory / "archive"
    snapshot = backup(source, archive)
    with tempfile.TemporaryDirectory(dir=directory) as temp:
        candidate = Path(temp) / "candidate.sqlite3"
        _copy_db(archive / "snapshot.sqlite3", candidate)
        with closing(_open(candidate, "rw")) as new:
            now = time.time()
            _prune(new, now)
            details = _inspect(new)
            _verify_retention(new, archive / "snapshot.sqlite3", now)
            if details["sequence"] != snapshot["sequence"]:
                raise ValueError("receipt_high_water_changed")
            state.update({"phase": "validated", "baseline": _state_digest(new),
                          "archive_sha256": snapshot["sha256"], "database": details})
        _write_json(metadata, state)
        destination = directory / "active.sqlite3"
        os.link(candidate, destination)
        _sync_directory(directory)
    # Publish intent before making this path writable: loss of a previously live
    # database must never be interpreted as a never-activated generation.
    state["phase"] = "activating"
    _write_json(metadata, state)
    with closing(_open(destination, "rw")) as new:
        new.execute("BEGIN IMMEDIATE")
        _unseal(new, token)
        new.commit()
    return {"active": str(destination), "archive": str(archive), **details}


def rollback(source, directory):
    """Reactivate original only if owned by this rotation and new has no changes."""
    directory = Path(directory)
    state = json.loads((directory / "rotation.json").read_text(encoding="utf-8"))
    source = Path(source).resolve(strict=True)
    if source != Path(state["source"]) or state["phase"] not in ("preparing", "validated", "activating"):
        raise ValueError("rotation_source_mismatch")
    token = state["seal"]
    with closing(_open(source, "rw")) as old:
        old.execute("BEGIN IMMEDIATE")
        if old.execute("SELECT seal FROM hub_maintenance WHERE singleton=1").fetchone() != (token,):
            raise ValueError("rotation_seal_mismatch")
        destination = directory / "active.sqlite3"
        if state["phase"] == "activating" and not destination.is_file():
            raise ValueError("new_generation_missing_reconciliation_required")
        if destination.exists():
            with closing(_open(destination, "rw")) as new:
                new.execute("BEGIN IMMEDIATE")
                if _state_digest(new) != state.get("baseline"):
                    raise ValueError("new_generation_changed_reconciliation_required")
                _seal(new, token)
                new.commit()
        _unseal(old, token)
        old.commit()
    return {"active": str(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("backup", "rotate", "rollback"):
        command = commands.add_parser(name)
        command.add_argument("source", type=Path)
        command.add_argument("directory", type=Path)
    commands.add_parser("verify").add_argument("directory", type=Path)
    command = commands.add_parser("restore")
    command.add_argument("directory", type=Path)
    command.add_argument("destination", type=Path)
    command.add_argument("--revocations-from", type=Path,
                         help="latest trusted hub database carrying wiki access withdrawals")
    args = vars(parser.parse_args())
    name = args.pop("command")
    operation = {"backup": backup, "rotate": rotate, "rollback": rollback,
                 "restore": restore, "verify": verify}[name]
    print(json.dumps(operation(**args), ensure_ascii=False))


if __name__ == "__main__":
    main()
