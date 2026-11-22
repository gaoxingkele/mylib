"""Claim one account-scoped job and publish its provider usage observation."""

import argparse
import asyncio
import hashlib
import hmac
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


class UsageError(ValueError):
    """A safe, observable failure classification for the claimed job."""

    def __init__(self, status):
        super().__init__(status)
        self.status = status


def _utc(value):
    if not isinstance(value, str):
        raise UsageError("unavailable")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.utcoffset() is None:
            raise ValueError("missing timezone")
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise UsageError("unavailable") from None


def _iso(stamp):
    return stamp.isoformat().replace("+00:00", "Z")


def _json_file(path):
    with Path(path).open("rb") as stream:
        data = stream.read(256 * 1024 + 1)
    if len(data) > 256 * 1024:
        raise UsageError("unavailable")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise UsageError("unavailable")
    return value


def _remaining(value, unit):
    if value is None:
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise UsageError("unavailable")
    if unit == "percent" and value > 100:
        raise UsageError("unavailable")
    return value


def exported_snapshot(profile, job, now):
    """Read an operator-provided export of the bound account's official usage view."""
    value = _json_file(profile["snapshot_file"])
    if value.get("account") != job["account"] or value.get("provider") != profile["provider"]:
        raise UsageError("auth_required")
    if value.get("pool") != profile["pool"]:
        raise UsageError("unavailable")
    stamp = _utc(value.get("observed_at"))
    if stamp < _utc(job["accepted_at"]) or stamp > now:
        raise UsageError("unavailable")
    supplied = value.get("windows")
    if not isinstance(supplied, list) or not 1 <= len(supplied) <= 16:
        raise UsageError("unavailable")
    windows = []
    for row in supplied:
        if not isinstance(row, dict):
            raise UsageError("unavailable")
        period, unit = row.get("period"), row.get("unit")
        if period not in ("weekly", "short", "daily", "monthly", "balance", "other"):
            raise UsageError("unavailable")
        if unit not in ("percent", "tokens", "credits", "requests", "CNY", "USD"):
            raise UsageError("unsupported")
        reset = row.get("reset_at")
        windows.append({"period": period, "unit": unit, "remaining": _remaining(row.get("remaining"), unit),
                        "reset_at": _iso(_utc(reset)) if reset is not None else None})
    return {"provider": profile["provider"], "pool": profile["pool"], "source": "operator_usage_export",
            "status": "ok", "observed_at": _iso(stamp), "windows": windows}


def codex_windows(result, profile):
    """Normalize the current account's selected limit without inferring a weekly window."""
    if not isinstance(result, dict) or not profile.get("codex_account_id"):
        raise UsageError("auth_required")
    if result.get("accountId") != profile["codex_account_id"]:
        raise UsageError("auth_required")
    limit_id = profile.get("limit_id")
    if limit_id:
        mapping = result.get("rateLimitsByLimitId")
        rates = mapping.get(limit_id) if isinstance(mapping, dict) else None
    else:
        rates = result.get("rateLimits")
    if not isinstance(rates, dict):
        raise UsageError("unsupported")
    windows = []
    for field in ("primary", "secondary"):
        row = rates.get(field)
        if row is None:
            continue
        if not isinstance(row, dict):
            raise UsageError("unavailable")
        duration = row.get("windowDurationMins")
        if duration is not None and (type(duration) is not int or duration <= 0):
            raise UsageError("unavailable")
        period = {10080: "weekly", 1440: "daily"}.get(duration, "other")
        if duration is not None and duration < 1440:
            period = "short"
        used = _remaining(row.get("usedPercent"), "percent")
        reset = row.get("resetsAt")
        if reset is not None and type(reset) is not int:
            raise UsageError("unavailable")
        try:
            reset_at = _iso(datetime.fromtimestamp(reset, timezone.utc)) if reset is not None else None
        except (OverflowError, ValueError, OSError):
            raise UsageError("unavailable") from None
        windows.append({"period": period, "window_minutes": duration, "unit": "percent",
                        "remaining": 100 - used if used is not None else None, "reset_at": reset_at})
    if not windows:
        raise UsageError("unsupported")
    return windows


async def _read_codex(argv, environment, cwd, timeout=15):
    process = await asyncio.create_subprocess_exec(
        *argv, cwd=cwd, env=environment, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL, limit=256 * 1024,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )

    async def send(message):
        process.stdin.write(json.dumps(message).encode("utf-8") + b"\n")
        await process.stdin.drain()

    async def reply(request_id):
        for _ in range(128):
            line = await process.stdout.readline()
            if not line:
                break
            value = json.loads(line)
            if not isinstance(value, dict) or value.get("id") != request_id:
                continue
            if "error" in value:
                error = value["error"]
                code = error.get("code") if isinstance(error, dict) else None
                status = {401: "auth_required", 403: "auth_required", 429: "rate_limited",
                          -32601: "unsupported"}.get(code, "unavailable")
                raise UsageError(status)
            if not isinstance(value.get("result"), dict):
                raise UsageError("unavailable")
            return value["result"]
        raise UsageError("unavailable")

    async def exchange():
        await send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "mylib-quota", "version": "1"},
            "capabilities": {"experimentalApi": False}}})
        await reply(1)
        await send({"method": "initialized"})
        await send({"id": 2, "method": "account/rateLimits/read"})
        return await reply(2)

    try:
        return await asyncio.wait_for(exchange(), timeout)
    finally:
        process.stdin.close()
        try:
            await asyncio.wait_for(process.wait(), 1)
        except asyncio.TimeoutError:
            if process.returncode is None:
                process.kill()
            await process.wait()


def fetch_codex(profile, job, now):
    if profile["provider"] != "codex" or not profile.get("codex_account_id"):
        raise UsageError("auth_required")
    home = Path(profile["codex_home"])
    if not home.is_absolute() or not home.is_dir():
        raise UsageError("auth_required")
    binary = shutil.which(profile.get("codex_executable", "codex"))
    if not binary:
        raise UsageError("unsupported")
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(home)
    argv = [binary, "--no-daemon", "--disable", "hooks", "app-server", "--listen", "stdio://"]
    with tempfile.TemporaryDirectory(prefix="hub-quota-") as cwd:
        result = asyncio.run(_read_codex(argv, environment, cwd))
    return {"provider": "codex", "pool": profile["pool"], "source": "codex_app_server",
            "observed_at": _iso(datetime.now(timezone.utc)), "status": "ok", "windows": codex_windows(result, profile)}


def _fetch_native(profile, job, now):
    from .native_usage import collect_native
    return collect_native(profile, job, now)


def fetch_deepseek(profile, job, now, *, transport=None):
    """Read a pinned DeepSeek API account's currency balances via the official endpoint."""
    import httpx
    token = os.environ.get('MYLIB_HUB_DEEPSEEK_KEY', '')
    if (profile['provider'] != 'deepseek' or profile['account'] != job['account'] or not token
            or not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), profile.get('key_sha256', ''))):
        raise UsageError('auth_required')
    try:
        with httpx.Client(transport=transport, trust_env=False, follow_redirects=False, timeout=8) as client:
            with client.stream('GET', 'https://api.deepseek.com/user/balance', headers={
                'Authorization':'Bearer '+token, 'Accept-Encoding':'identity'}) as response:
                if response.status_code != 200:
                    raise UsageError({401:'auth_required',403:'auth_required',429:'rate_limited'}.get(response.status_code,'unavailable'))
                raw = bytearray()
                for block in response.iter_raw():
                    if len(raw) + len(block) > 16384:
                        raise UsageError('unavailable')
                    raw.extend(block)
    except httpx.HTTPError:
        raise UsageError('unavailable') from None
    value = json.loads(raw)
    rows = value.get('balance_infos') if isinstance(value, dict) else None
    if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
        raise UsageError('unavailable')
    windows = []
    for row in rows:
        if not isinstance(row, dict) or row.get('currency') not in {'USD','CNY'}:
            raise UsageError('unsupported')
        remaining = _remaining(float(row['total_balance']), row['currency'])
        windows.append({'period':'balance','unit':row['currency'],'remaining':remaining,'reset_at':None})
    return dict(provider='deepseek',pool=profile['pool'],source='deepseek_balance',status='ok',
                observed_at=_iso(now),windows=windows)


SOURCES = {
    'deepseek_balance': fetch_deepseek,
    "codex_app_server": fetch_codex,
    "operator_usage_export": exported_snapshot,
    "claude_statusline": _fetch_native,
    "grok_cli": _fetch_native,
}


def run_one(profile, call, *, sources=None, now=None):
    """Process one lease through an authenticated call_tool(name, arguments) client."""
    now = now or (lambda: datetime.now(timezone.utc))
    project, account, worker = (profile[key] for key in ("project", "account", "worker"))
    provider, pool, source = (profile[key] for key in ("provider", "pool", "source"))
    if not all(isinstance(s, str) and 0 < len(s) <= 160 for s in (project, account, worker, provider, pool, source)):
        raise ValueError("invalid quota profile")
    selector = {"project": project, "account": account}
    claim = {**selector, "worker": worker}
    if "idle_after_seconds" in profile:
        interval = profile["idle_after_seconds"]
        if type(interval) is not int or not 60 <= interval <= 7 * 86400:
            raise ValueError("invalid idle quota interval")
        claim["idle_after_seconds"] = interval
    job = call("claim_usage_job", claim)
    if job is None or job == {}:
        return {"status": "idle"}
    if (job.get("project"), job.get("account"), job.get("worker")) != (project, account, worker):
        raise ValueError("quota lease binding mismatch")
    fetch = (SOURCES if sources is None else sources).get(source)
    try:
        if not fetch:
            raise UsageError("unsupported")
        result = fetch(profile, job, now())
    except (UsageError, OSError, ValueError, KeyError, TypeError, OverflowError, asyncio.TimeoutError) as error:
        result = {"provider": provider, "pool": pool, "source": source,
                  "status": error.status if isinstance(error, UsageError) else "unavailable",
                  "observed_at": _iso(now()), "windows": []}
    snapshot = {**result, "job_id": job["job_id"], "lease_token": job["lease_token"]}
    return call("record_usage_snapshot", {**selector, "snapshot": snapshot})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Process one Agent Hub quota job for an authorized account")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--token-env", default="AGENT_HUB_QUOTA_TOKEN")
    parser.add_argument("--watch", action="store_true", help="keep polling for newly committed steps")
    parser.add_argument("--poll-seconds", type=int, default=10, choices=range(1, 301), metavar="1..300")
    args = parser.parse_args(argv)
    from .client import call_tool
    try:
        profile = _json_file(args.profile)
        token = os.environ[args.token_env]
        def call(name, values):
            return call_tool(name, values, endpoint=args.endpoint, token=token)
        while True:
            try:
                result = run_one(profile, call)
            except Exception:
                if not args.watch:
                    raise
                print("Quota worker could not process a job; retrying.", file=sys.stderr, flush=True)
                time.sleep(args.poll_seconds)
                continue
            if not args.watch or result["status"] != "idle":
                print(json.dumps({"job_id": result.get("job_id"), "status": result["status"]}), flush=True)
            if not args.watch:
                return 0
            if result["status"] == "idle":
                time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("Quota run failed; check the profile, endpoint and worker authorization.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
