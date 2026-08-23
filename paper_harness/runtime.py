"""Harness 状态：<paper_dir>/.paper_harness/ 下的 SQLite 状态机 + append-only timeline。"""

from __future__ import annotations

import json
import os
import sqlite3
import ctypes
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ_CN = timezone(timedelta(hours=8), name="Asia/Shanghai")

HARNESS_DIRNAME = ".paper_harness"

STAGE_STATUSES = ("PENDING", "RUNNING", "CANDIDATE", "ACCEPTED", "REJECTED", "BLOCKED", "FAILED")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS plans (
    version     INTEGER PRIMARY KEY,
    path        TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    status      TEXT NOT NULL,           -- AWAITING_APPROVAL | APPROVED
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stages (
    stage_id      TEXT NOT NULL,
    plan_version  INTEGER NOT NULL,
    title         TEXT,
    objective     TEXT,
    acceptance    TEXT,                  -- JSON list of check names
    status        TEXT NOT NULL,         -- PENDING/RUNNING/CANDIDATE/ACCEPTED/REJECTED/BLOCKED/FAILED
    branch        TEXT,
    worktree      TEXT,
    updated_at    TEXT NOT NULL,
    PRIMARY KEY (stage_id, plan_version)
);
"""


def now_iso() -> str:
    return datetime.now(TZ_CN).isoformat(timespec="seconds")


def today_cn() -> str:
    return datetime.now(TZ_CN).date().isoformat()


def ts_compact() -> str:
    return datetime.now(TZ_CN).strftime("%Y%m%d_%H%M%S")


class Runtime:
    """一个论文项目的 harness 状态。"""

    def __init__(self, paper_dir: str | Path):
        self.paper_dir = Path(paper_dir).resolve()
        self.root = self.paper_dir / HARNESS_DIRNAME
        if not self.root.is_dir():
            raise FileNotFoundError(
                f"{self.root} 不存在，请先运行: python -m paper_harness init <paper_dir> ..."
            )
        self.db_path = self.root / "runtime.sqlite3"
        self.timeline_path = self.root / "timeline.jsonl"
        self.db = sqlite3.connect(str(self.db_path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(_SCHEMA)
        self.db.commit()

    # ---------- 崩溃恢复 ----------

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if os.name == "nt":
            # ``os.kill(pid, 0)`` is not a portable existence probe on
            # Windows. Query a handle without delivering a signal.
            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError, ValueError):
            return False
        return True

    def recover_stale_running(self) -> list[str]:
        """Mark RUNNING stages without a live run lease as FAILED.

        Read-only status/review connections never mutate stage state. Recovery
        is invoked explicitly by ``run``.
        """
        rows = self.db.execute("SELECT stage_id, plan_version FROM stages WHERE status='RUNNING'").fetchall()
        recovered: list[str] = []
        for row in rows:
            run_dir = self.root / "runs" / f"v{row['plan_version']}_{row['stage_id']}"
            lease_path = run_dir / "lease.json"
            lease: dict = {}
            if lease_path.exists():
                try:
                    lease = json.loads(lease_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    lease = {}
            pid = lease.get("pid")
            if isinstance(pid, int) and self._pid_alive(pid):
                continue
            self.db.execute(
                "UPDATE stages SET status='FAILED', updated_at=? WHERE stage_id=? AND plan_version=?",
                (now_iso(), row["stage_id"], row["plan_version"]),
            )
            self.event(
                "stage_failed",
                stage_id=row["stage_id"],
                plan_version=row["plan_version"],
                reason="harness 检测到无存活 lease 的 RUNNING，无法证明其完成，标记 FAILED",
            )
            recovered.append(row["stage_id"])
        self.db.commit()
        return recovered

    # ---------- 事件 ----------

    def event(self, type_: str, **data) -> None:
        rec = {"ts": now_iso(), "type": type_, "data": data}
        with self.timeline_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def tail_events(self, n: int = 10) -> list[dict]:
        if not self.timeline_path.exists():
            return []
        lines = self.timeline_path.read_text(encoding="utf-8").splitlines()
        out = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return out

    # ---------- plan ----------

    def next_plan_version(self) -> int:
        row = self.db.execute("SELECT MAX(version) AS v FROM plans").fetchone()
        return (row["v"] or 0) + 1

    def add_plan(self, version: int, path: str, sha256: str) -> None:
        self.db.execute(
            "INSERT INTO plans(version, path, sha256, status, updated_at) VALUES(?,?,?,?,?)",
            (version, path, sha256, "AWAITING_APPROVAL", now_iso()),
        )
        self.db.commit()

    def set_plan_status(self, version: int, status: str) -> None:
        self.db.execute(
            "UPDATE plans SET status=?, updated_at=? WHERE version=?", (status, now_iso(), version)
        )
        self.db.commit()

    def latest_plan(self) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM plans ORDER BY version DESC LIMIT 1").fetchone()

    def get_plan(self, version: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM plans WHERE version=?", (version,)).fetchone()

    # ---------- stage ----------

    def add_stage(self, stage_id: str, plan_version: int, title: str, objective: str, acceptance: list[str]) -> None:
        self.db.execute(
            "INSERT INTO stages(stage_id, plan_version, title, objective, acceptance, status, updated_at)"
            " VALUES(?,?,?,?,?,'PENDING',?)",
            (stage_id, plan_version, title, objective, json.dumps(acceptance, ensure_ascii=False), now_iso()),
        )
        self.db.commit()

    def set_stage_status(
        self, stage_id: str, plan_version: int, status: str,
        branch: str | None = None, worktree: str | None = None,
    ) -> None:
        self.db.execute(
            "UPDATE stages SET status=?, branch=COALESCE(?, branch), worktree=COALESCE(?, worktree), updated_at=?"
            " WHERE stage_id=? AND plan_version=?",
            (status, branch, worktree, now_iso(), stage_id, plan_version),
        )
        self.db.commit()

    def reset_stage_for_retry(self, stage_id: str, plan_version: int) -> None:
        """Reset only a preserved BLOCKED/FAILED stage after an explicit retry command."""
        row = self.get_stage(stage_id, plan_version)
        if row is None or row["status"] not in ("BLOCKED", "FAILED"):
            raise ValueError("only BLOCKED or FAILED stages may be reset for retry")
        self.db.execute(
            "UPDATE stages SET status='PENDING', branch=NULL, worktree=NULL, updated_at=?"
            " WHERE stage_id=? AND plan_version=?",
            (now_iso(), stage_id, plan_version),
        )
        self.db.commit()

    def get_stage(self, stage_id: str, plan_version: int | None = None) -> sqlite3.Row | None:
        if plan_version is None:
            return self.db.execute(
                "SELECT * FROM stages WHERE stage_id=? ORDER BY plan_version DESC LIMIT 1", (stage_id,)
            ).fetchone()
        return self.db.execute(
            "SELECT * FROM stages WHERE stage_id=? AND plan_version=?", (stage_id, plan_version)
        ).fetchone()

    def stages_for_plan(self, plan_version: int) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM stages WHERE plan_version=? ORDER BY rowid", (plan_version,)
        ).fetchall()

    def all_stages(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM stages ORDER BY plan_version, rowid").fetchall()

    def close(self) -> None:
        self.db.close()
