"""Read opted-in provider usage surfaces without copying login state."""

import argparse
import asyncio
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile

from .quota import UsageError, _iso, _json_file, _remaining, _utc


_MAX_BYTES = 64 * 1024
_SOURCES = {"claude_statusline": "claude", "grok_cli": "grok"}
_CLAUDE_WINDOWS = (("seven_day", "weekly", 10080), ("five_hour", "short", 300))
_CLAUDE_OVERRIDES = {
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
}


def _json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _unique_keys(pairs):
    value = dict(pairs)
    if len(value) != len(pairs):
        raise UsageError("unsupported")
    return value


def _read_object(raw):
    if not isinstance(raw, bytes) or not 0 < len(raw) <= _MAX_BYTES:
        raise UsageError("unavailable")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_keys)
    except (UnicodeError, ValueError, RecursionError):
        raise UsageError("unsupported") from None
    if not isinstance(value, dict):
        raise UsageError("unsupported")
    return value


def _absolute(value):
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise UsageError("auth_required")
    return Path(value)


def _alias(value):
    if not isinstance(value, str) or not 0 < len(value) <= 180 or not value.isprintable():
        raise UsageError("auth_required")
    return value


def _binding(profile):
    source = profile.get("source")
    if not isinstance(source, str) or source not in _SOURCES or profile.get("native_enabled") is not True:
        raise UsageError("unsupported")
    if profile.get("provider") != _SOURCES[source]:
        raise UsageError("auth_required")
    return [_alias(profile.get(name)) for name in ("project", "account", "pool", "origin_source")]


def _verify_job(profile, job):
    project, account, _, origin = _binding(profile)
    if (job.get("project"), job.get("account"), job.get("worker")) != (project, account, profile.get("worker")):
        raise UsageError("auth_required")
    if job.get("trigger") == "scheduled" and job.get("event_id") is None:
        return
    if job.get("source") != origin or job.get("tool") != profile["provider"]:
        raise UsageError("auth_required")


def _stamp(value, form):
    if form == "utc_iso":
        return _utc(value)
    if form != "unix_seconds" or type(value) is not int or value <= 0:
        raise UsageError("unsupported")
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (OverflowError, ValueError, OSError):
        raise UsageError("unavailable") from None


def _window(period, minutes, used, reset):
    used = _remaining(used, "percent")
    if used is None:
        raise UsageError("unavailable")
    return {"period": period, "unit": "percent", "remaining": 100 - used,
            "window_minutes": minutes, "reset_at": _iso(reset)}


def _snapshot(profile, job, now, observed, windows):
    if not _utc(job["accepted_at"]) <= observed <= now or now - observed > timedelta(minutes=15):
        raise UsageError("unavailable")
    current = [window for window in windows if _utc(window["reset_at"]) > now]
    if not current:
        raise UsageError("unavailable")
    return {"provider": profile["provider"], "pool": profile["pool"], "source": profile["source"],
            "observed_at": _iso(observed), "status": "ok", "windows": current}


def _claude_binding(profile):
    binding = _binding(profile)
    if profile["source"] != "claude_statusline":
        raise UsageError("unsupported")
    config_dir = _absolute(profile.get("claude_config_dir")).resolve(strict=True)
    if not config_dir.is_dir():
        raise UsageError("auth_required")
    binding += [str(config_dir), _alias(profile.get("claude_session_id")), _alias(profile.get("claude_version"))]
    return hashlib.sha256(_json(binding).encode()).hexdigest(), config_dir


def _claude_windows(payload):
    limits = payload.get("rate_limits")
    if not isinstance(limits, dict):
        return []
    windows = []
    for key, period, duration in _CLAUDE_WINDOWS:
        limit = limits.get(key)
        if limit is None:
            continue
        if not isinstance(limit, dict) or not {"used_percentage", "resets_at"} <= limit.keys():
            raise UsageError("unsupported")
        reset = _stamp(limit["resets_at"], "unix_seconds")
        windows.append(_window(period, duration, limit["used_percentage"], reset))
    return windows


def _claude_changes(before, after, stamp):
    """Keep each window's observation time independent and reject regressions."""
    updated = dict(before)
    for current in after:
        period = current["period"]
        entry = before.get(period)
        if entry is None:
            updated[period] = {"window": current, "observed_at": None}
            continue
        previous = entry["window"]
        current_reset = _utc(current["reset_at"])
        previous_reset = _utc(previous["reset_at"])
        if current_reset < previous_reset:
            return before
        if current_reset == previous_reset and current["remaining"] > previous["remaining"]:
            return before
        if current != previous:
            updated[period] = {"window": current, "observed_at": stamp}
    return updated


_CLAUDE_SCHEMA = """
CREATE TABLE IF NOT EXISTS observation (
    id INTEGER PRIMARY KEY CHECK(id=1),
    binding TEXT NOT NULL,
    sampled_at TEXT NOT NULL,
    windows TEXT NOT NULL
)
"""


def _observer_path(profile):
    path = _absolute(profile.get("observer_db"))
    if path.is_symlink() or not path.parent.is_dir():
        raise UsageError("auth_required")
    if os.name == "posix" and (path.parent.stat().st_mode & 0o077 or
                               (path.exists() and path.stat().st_mode & 0o077)):
        raise UsageError("auth_required")
    return path


def observe_claude_statusline(profile, raw, *, environ=None, now=None):
    """Observe statusLine stdin locally. First sample only seeds comparison."""
    environ = os.environ if environ is None else environ
    now = now or datetime.now(timezone.utc)
    recorded, config_dir = _claude_binding(profile)
    environment_dir = _absolute(environ.get("CLAUDE_CONFIG_DIR")).resolve(strict=True)
    if environment_dir != config_dir or any(environ.get(name) for name in _CLAUDE_OVERRIDES):
        raise UsageError("auth_required")
    payload = _read_object(raw)
    if payload.get("session_id") != profile["claude_session_id"] or payload.get("version") != profile["claude_version"]:
        raise UsageError("auth_required")
    windows = [window for window in _claude_windows(payload) if _utc(window["reset_at"]) > now]
    if not windows:
        return False
    path = _observer_path(profile)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        pass
    else:
        os.close(fd)
    with closing(sqlite3.connect(path, timeout=0.75)) as db, db:
        db.execute(_CLAUDE_SCHEMA)
        db.execute("BEGIN IMMEDIATE")
        previous = db.execute("SELECT binding,sampled_at,windows FROM observation").fetchone()
        stamp = _iso(now)
        if previous is None:
            baseline = _claude_changes({}, windows, stamp)
            db.execute("INSERT INTO observation VALUES(1,?,?,?)", (recorded, stamp, _json(baseline)))
            return False
        binding, sampled_at, document = previous
        if binding != recorded:
            raise UsageError("auth_required")
        if now <= _utc(sampled_at):
            return False
        before = json.loads(document)
        updated = _claude_changes(before, windows, stamp)
        if before == updated:
            return False
        db.execute("UPDATE observation SET sampled_at=?,windows=? WHERE id=1", (stamp, _json(updated)))
        return any(entry["observed_at"] == stamp for entry in updated.values())


def _fetch_claude(profile, job, now):
    expected, _ = _claude_binding(profile)
    path = _observer_path(profile)
    if not path.is_file():
        raise UsageError("unavailable")
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.75)) as db:
            row = db.execute("SELECT binding,windows FROM observation").fetchone()
    except sqlite3.Error:
        raise UsageError("unavailable") from None
    if row is None:
        raise UsageError("unavailable")
    if row[0] != expected:
        raise UsageError("auth_required")
    entries = json.loads(row[1])
    windows, observations = [], []
    for period in ("weekly", "short"):
        entry = entries.get(period)
        if entry is None or entry["observed_at"] is None:
            if period == "weekly":
                raise UsageError("unavailable")
            continue
        observed = _utc(entry["observed_at"])
        try:
            _snapshot(profile, job, now, observed, [entry["window"]])
        except UsageError:
            if period == "weekly":
                raise
            continue
        windows.append(entry["window"])
        observations.append(observed)
    return _snapshot(profile, job, now, min(observations), windows)


def _shape(node, level=0):
    if level > 12:
        raise UsageError("unsupported")
    if isinstance(node, dict):
        return {key: _shape(value, level + 1) for key, value in node.items()}
    if isinstance(node, list):
        return [_shape(value, level + 1) for value in node]
    if type(node) in (int, float):
        return "number"
    return type(node).__name__


def grok_shape_fingerprint(payload):
    """Hash the JSON shape only; does not read an account or include field values."""
    return hashlib.sha256(_json(_shape(payload)).encode()).hexdigest()


def _select(payload, keys):
    if (not isinstance(keys, list) or not 1 <= len(keys) <= 12 or
            any(not isinstance(key, str) or not 0 < len(key) <= 128 for key in keys)):
        raise UsageError("unsupported")
    for key in keys:
        if not isinstance(payload, dict) or key not in payload:
            raise UsageError("unsupported")
        payload = payload[key]
    return payload


def _grok_schema(profile):
    schema = profile.get("grok_schema")
    fields = {"shape_sha256", "account_path", "observed_at_path", "observed_at_format", "windows"}
    if not isinstance(schema, dict) or set(schema) != fields:
        raise UsageError("unsupported")
    fingerprint = schema["shape_sha256"]
    if not isinstance(fingerprint, str) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise UsageError("unsupported")
    return schema


def _grok_usage(profile, job, now, payload):
    schema = _grok_schema(profile)
    if grok_shape_fingerprint(payload) != schema["shape_sha256"]:
        raise UsageError("unsupported")
    if _select(payload, schema["account_path"]) != _alias(profile.get("grok_account_id")):
        raise UsageError("auth_required")
    observed = _stamp(_select(payload, schema["observed_at_path"]), schema["observed_at_format"])
    rules = schema["windows"]
    if not isinstance(rules, list) or not 1 <= len(rules) <= 2:
        raise UsageError("unsupported")
    windows = []
    for rule in rules:
        fields = {"period", "window_minutes", "used_percent_path", "reset_path", "reset_format"}
        if not isinstance(rule, dict) or set(rule) != fields:
            raise UsageError("unsupported")
        period, minutes = rule["period"], rule["window_minutes"]
        if type(minutes) is not int or not (
            (period == "weekly" and minutes == 10080) or (period == "short" and 0 < minutes < 1440)
        ):
            raise UsageError("unsupported")
        reset = _stamp(_select(payload, rule["reset_path"]), rule["reset_format"])
        windows.append(_window(period, minutes, _select(payload, rule["used_percent_path"]), reset))
    if len({row["period"] for row in windows}) != len(windows):
        raise UsageError("unsupported")
    return _snapshot(profile, job, now, observed, windows)


async def _bounded_cli(argv, cwd, environment, timeout=8):
    process = await asyncio.create_subprocess_exec(
        *argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )

    async def output():
        try:
            await process.stdout.readexactly(_MAX_BYTES + 1)
        except asyncio.IncompleteReadError as error:
            if await process.wait() == 0:
                return error.partial
        raise UsageError("unavailable")

    try:
        return await asyncio.wait_for(output(), timeout)
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            try:
                await asyncio.wait_for(process.communicate(), 1)
            except asyncio.TimeoutError:
                pass


def _grok_paths(profile):
    binary = _absolute(profile.get("grok_executable"))
    leader = _absolute(profile.get("grok_leader_socket"))
    named = leader.name
    if (not binary.is_file() or leader.is_symlink() or not
            (named.startswith("leader-") and named.endswith(".sock") and len(named) > len("leader-.sock"))):
        raise UsageError("auth_required")
    daemon = leader.with_name(named + ".daemon")
    if daemon.is_symlink() or not (leader.is_socket() or daemon.is_socket()):
        raise UsageError("unavailable")
    return binary, leader


def _fetch_grok(profile, job, now, *, runner=_bounded_cli, clock=None):
    _grok_schema(profile)
    _alias(profile.get("grok_account_id"))
    binary, leader = _grok_paths(profile)
    expected_build = _alias(profile.get("grok_version_line"))
    env_keys = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "TMPDIR")
    environment = {name: os.environ[name] for name in env_keys if name in os.environ}
    with tempfile.TemporaryDirectory(prefix="hub-grok-usage-") as cwd:
        async def query():
            version = await runner([str(binary), "--version"], cwd, environment)
            if version.decode("utf-8", errors="replace").strip() != expected_build:
                raise UsageError("unsupported")
            return await runner([str(binary), "usage", "--json", "--leader-socket", str(leader)], cwd, environment)

        data = asyncio.run(query())
    clock = clock or (lambda: datetime.now(timezone.utc))
    return _grok_usage(profile, job, max(now, clock()), _read_object(data))


def collect_native(profile, job, now):
    """Quota worker adapter for both native sources."""
    _verify_job(profile, job)
    _utc(job.get("accepted_at"))
    if profile["source"] == "claude_statusline":
        return _fetch_claude(profile, job, now)
    return _fetch_grok(profile, job, now)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Opt-in Agent Hub native usage helpers")
    commands = parser.add_subparsers(dest="operation", required=True)
    observer = commands.add_parser("claude-statusline", help="capture approved Claude Code statusLine stdin")
    observer.add_argument("--profile", required=True)
    fingerprint = commands.add_parser("grok-shape", help="print only a saved JSON shape digest")
    fingerprint.add_argument("--fixture", required=True)
    args = parser.parse_args(argv)
    if args.operation == "claude-statusline":
        try:
            profile = _json_file(args.profile)
            observe_claude_statusline(profile, sys.stdin.buffer.read(_MAX_BYTES + 1))
        except (OSError, TypeError, ValueError, sqlite3.Error):
            return 1
        return 0
    try:
        with open(args.fixture, "rb") as handle:
            print(grok_shape_fingerprint(_read_object(handle.read(_MAX_BYTES + 1))))
    except (OSError, ValueError):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
