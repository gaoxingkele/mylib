#!/usr/bin/env python3
"""quota_probe: refresh weekly-quota snapshots for local AI CLIs.

Writes ~/.agent-quota/state.json (override with AGENT_QUOTA_HOME). The snapshot
holds only plan names, usage percentages, window sizes, reset times and
freshness metadata: never tokens, prompts, or credit balances.

Usage:
  quota_probe.py [--agent all|claude|codex|grok|kimi|gemini|opencode] [--force] [--print]
  quota_probe.py --hook            # for CLI hooks: drain stdin, spawn a detached
                                   # refresh of all agents, exit 0 immediately
  quota_probe.py --detach ...      # same as above without reading stdin

Sources (offline first; network only when offline data is stale, at most once
per TTL per agent, 3 s timeout):
  codex  ~/.codex/sessions/**/rollout-*.jsonl rate_limits -> chatgpt.com wham/usage
  claude ~/.agent-quota/claude-statusline.json (if a statusline tee exists)
         -> api.anthropic.com/api/oauth/usage
  grok   ~/.grok/logs/unified.jsonl "billing: fetched credits config" (offline only)
  kimi / gemini / opencode: unsupported (no local quota source found)
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

TTL = int(os.environ.get("AGENT_QUOTA_TTL", "300"))
NET_TIMEOUT = 3.0
HOME = os.path.expanduser("~")
STATE_DIR = os.environ.get("AGENT_QUOTA_HOME") or os.path.join(HOME, ".agent-quota")
STATE_PATH = os.path.join(STATE_DIR, "state.json")
META_PATH = os.path.join(STATE_DIR, "meta.json")
LOCK_PATH = os.path.join(STATE_DIR, "probe.lock")
LOG_PATH = os.path.join(STATE_DIR, "probe.log")
AGENTS = ["claude", "codex", "grok", "kimi", "gemini", "opencode"]
THROTTLED = "throttled"
EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
UNSUPPORTED = {
    "kimi": "Kimi Code 本地日志与会话中没有额度字段，也未找到公开的用量接口",
    "gemini": "本机未安装 Gemini CLI",
    "opencode": "OpenCode 按 API key 计费，没有周额度概念",
}


# ---------------------------------------------------------------- utilities
def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(t: dt.datetime | None) -> str | None:
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def parse_time(v) -> dt.datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        if x > 1e12:  # milliseconds
            x /= 1000.0
        return dt.datetime.fromtimestamp(x, dt.timezone.utc)
    s = str(v).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # trim fractional seconds beyond microseconds (e.g. .315237+00:00 is fine)
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def log(msg: str) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 256_000:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{iso(now_utc())} {msg}\n")
    except OSError:
        pass


def read_json(path: str, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def atomic_write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class FileLock:
    """Exclusive create-based lock; a lock older than 60 s is considered dead."""

    def __init__(self, path: str, wait: float = 5.0):
        self.path, self.wait, self.held = path, wait, False

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        deadline = time.time() + self.wait
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > 60:
                        os.unlink(self.path)
                        continue
                except OSError:
                    continue
                if time.time() > deadline:
                    return self  # not held: caller skips
                time.sleep(0.1)

    def __exit__(self, *exc):
        if self.held:
            try:
                os.unlink(self.path)
            except OSError:
                pass


def window(name: str, minutes: int | None, used: float | None, resets_at,
           estimated: bool = False) -> dict:
    t = parse_time(resets_at)
    w = {"name": name, "minutes": minutes}
    if used is None:
        w.update(used_percent=None, remaining_percent=None)
    else:
        used = max(0.0, min(100.0, float(used)))
        w.update(used_percent=round(used, 2), remaining_percent=round(100.0 - used, 2))
    w["resets_at"] = iso(t)
    if t and t < now_utc():
        # the window rolled over after we last observed it: usage restarted
        w.update(used_percent=0.0, remaining_percent=100.0, resets_at=None,
                 estimated=True, note="observed window has already reset")
    elif estimated:
        w["estimated"] = True
    return w


def window_name(minutes: int | None) -> str:
    return {300: "5h", 10080: "weekly"}.get(minutes or 0, f"{minutes}m" if minutes else "window")


def http_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=NET_TIMEOUT) as r:  # noqa: S310 (fixed vendor URLs)
        return json.loads(r.read().decode("utf-8"))


# ----------------------------------------------------------------- adapters
def codex_offline() -> dict | None:
    files = glob.glob(os.path.join(HOME, ".codex", "sessions", "**", "rollout-*.jsonl"), recursive=True)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    for path in files[:8]:
        last = None
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if '"rate_limits"' in line:
                        last = line
        except OSError:
            continue
        if not last:
            continue
        try:
            ev = json.loads(last)
        except ValueError:
            continue
        rl = (ev.get("payload") or {}).get("rate_limits") or {}
        wins = []
        for key in ("primary", "secondary"):
            w = rl.get(key)
            if isinstance(w, dict) and w.get("used_percent") is not None:
                m = w.get("window_minutes")
                wins.append(window(window_name(m), m, w.get("used_percent"), w.get("resets_at")))
        if not wins:
            continue
        return {"plan": rl.get("plan_type"), "windows": wins, "source": "codex-rollout",
                "observed_at": iso(parse_time(ev.get("timestamp")))}
    return None


def codex_network() -> dict:
    auth = read_json(os.path.join(HOME, ".codex", "auth.json"), {})
    tok = (auth.get("tokens") or {})
    if not tok.get("access_token"):
        raise RuntimeError("no ChatGPT login in ~/.codex/auth.json")
    headers = {"Authorization": "Bearer " + tok["access_token"], "User-Agent": "codex-cli",
               "OpenAI-Beta": "codex-1", "originator": "Codex Desktop"}
    if tok.get("account_id"):
        headers["ChatGPT-Account-Id"] = tok["account_id"]
    data = http_json("https://chatgpt.com/backend-api/wham/usage", headers)
    rl = data.get("rate_limit") or {}
    wins = []
    for key in ("primary_window", "secondary_window"):
        w = rl.get(key)
        if isinstance(w, dict) and w.get("used_percent") is not None:
            secs = w.get("limit_window_seconds")
            m = int((secs + 59) // 60) if isinstance(secs, (int, float)) and secs > 0 else None
            wins.append(window(window_name(m), m, w.get("used_percent"), w.get("reset_at")))
    return {"plan": data.get("plan_type"), "windows": wins, "source": "wham-usage",
            "observed_at": iso(now_utc())}


def claude_offline() -> dict | None:
    """Reads a statusline payload copy if some statusline wrapper saved one."""
    p = os.path.join(STATE_DIR, "claude-statusline.json")
    data = read_json(p, None)
    if not isinstance(data, dict):
        return None
    rl = data.get("rate_limits") or {}
    wins = []
    for key, name, m in (("five_hour", "5h", 300), ("seven_day", "weekly", 10080)):
        w = rl.get(key)
        if isinstance(w, dict):
            used = w.get("used_percentage", w.get("utilization"))
            if used is not None:
                wins.append(window(name, m, used, w.get("resets_at")))
    if not wins:
        return None
    return {"plan": None, "windows": wins, "source": "claude-statusline",
            "observed_at": iso(dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc))}


def claude_network() -> dict:
    cred = read_json(os.path.join(HOME, ".claude", ".credentials.json"), {})
    oa = cred.get("claudeAiOauth") or {}
    tok = oa.get("accessToken")
    if not tok:
        raise RuntimeError("no Claude.ai OAuth login in ~/.claude/.credentials.json")
    exp = parse_time(oa.get("expiresAt"))
    if exp and exp < now_utc():
        raise RuntimeError("Claude OAuth access token expired; it refreshes when Claude Code next runs")
    data = http_json("https://api.anthropic.com/api/oauth/usage",
                     {"Authorization": "Bearer " + tok, "anthropic-beta": "oauth-2025-04-20",
                      "User-Agent": "claude-code/2.1.0"})
    wins = []

    def add(name, m, w):
        if isinstance(w, dict):
            used = w.get("utilization", w.get("used_percentage", w.get("percent")))
            if isinstance(used, (int, float)):
                wins.append(window(name, m, used, w.get("resets_at")))

    add("5h", 300, data.get("five_hour"))
    add("weekly", 10080, data.get("seven_day"))
    for lim in data.get("limits") or []:
        if isinstance(lim, dict) and lim.get("kind") == "weekly_scoped":
            model = ((lim.get("scope") or {}).get("model") or {}).get("display_name") or "scoped"
            add(f"weekly-{str(model).strip().lower()}", 10080, lim)
    for key, val in data.items():  # seven_day_opus, seven_day_fable, ...
        if key.startswith("seven_day_") and not any(w["name"] == "weekly-" + key[10:] for w in wins):
            add("weekly-" + key[10:], 10080, val)
    return {"plan": oa.get("subscriptionType"), "windows": wins, "source": "oauth-usage",
            "observed_at": iso(now_utc())}


def tail_lines(path: str, needle: str, max_bytes: int = 16 << 20) -> str | None:
    """Return the last line containing needle, scanning backwards in chunks."""
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            pos, buf, chunk = size, b"", 1 << 20
            nb = needle.encode()
            while pos > 0 and size - pos < max_bytes:
                step = min(chunk, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + buf
                lines = buf.split(b"\n")
                head, lines = lines[0], lines[1:]
                for ln in reversed(lines):
                    if nb in ln:
                        return ln.decode("utf-8", "replace")
                buf = head
            if nb in buf:
                return buf.decode("utf-8", "replace")
    except OSError:
        return None
    return None


def grok_offline() -> dict | None:
    line = tail_lines(os.path.join(HOME, ".grok", "logs", "unified.jsonl"), "billing: fetched credits config")
    if not line:
        return None
    try:
        ev = json.loads(line)
    except ValueError:
        return None
    ctx = ev.get("ctx") or {}
    cfg = ctx.get("config") or {}
    period = cfg.get("currentPeriod") or {}
    start, end = parse_time(period.get("start")), parse_time(period.get("end"))
    minutes = int((end - start).total_seconds() // 60) if start and end else None
    ptype = str(period.get("type") or "")
    name = "weekly" if "WEEKLY" in ptype else window_name(minutes)
    # protobuf JSON omits zero values: a missing creditUsagePercent means 0 %
    used = cfg.get("creditUsagePercent", 0.0)
    w = window(name, minutes, used, period.get("end"))
    if "creditUsagePercent" not in cfg and not w.get("estimated"):
        w["note"] = "creditUsagePercent omitted by server (protobuf zero value)"
    return {"plan": ctx.get("subscriptionTier"), "windows": [w], "source": "grok-log",
            "observed_at": iso(parse_time(ev.get("ts")))}


ADAPTERS = {
    "codex": (codex_offline, codex_network),
    "claude": (claude_offline, claude_network),
    "grok": (grok_offline, None),
}


# ------------------------------------------------------------------- engine
def is_stale(snap: dict, now: dt.datetime | None = None) -> bool:
    now = now or now_utc()
    t = parse_time(snap.get("observed_at"))
    return t is None or (now - t).total_seconds() > 2 * TTL


def probe_agent(agent: str, meta: dict, force: bool) -> dict:
    now = now_utc()
    if agent in UNSUPPORTED:
        return {"plan": None, "windows": [], "source": "unsupported", "note": UNSUPPORTED[agent],
                "observed_at": None, "fetched_at": iso(now), "stale": True}
    offline, network = ADAPTERS[agent]
    snap, err = None, None
    try:
        snap = offline()
    except Exception as e:  # adapter failures never reach the hook
        err = f"offline: {type(e).__name__}"
    if (snap is None or is_stale(snap, now)) and network:
        last = (meta.get(agent) or {}).get("last_network_at", 0)
        if force or time.time() - last >= TTL:
            meta.setdefault(agent, {})["last_network_at"] = time.time()
            log(f"{agent}: network fetch")
            try:
                snap = network()
                err = None
            except urllib.error.HTTPError as e:
                err = f"network: HTTP {e.code}"
            except Exception as e:
                err = f"network: {type(e).__name__}: {str(e)[:120]}"
        elif snap is None:
            err = THROTTLED
    if snap is None:
        snap = {"plan": None, "windows": [], "source": "none", "observed_at": None}
    now = now_utc()
    snap["fetched_at"] = iso(now)
    snap["stale"] = is_stale(snap, now)
    if err and err != THROTTLED:
        snap["error"] = err
        log(f"{agent}: {err}")
    elif err:
        snap["throttled"] = True
    return snap


def run(agents: list[str], force: bool) -> dict | None:
    with FileLock(LOCK_PATH) as lk:
        if not lk.held:
            log("another probe holds the lock; skipped")
            return None
        state = read_json(STATE_PATH, {"agents": {}})
        state.setdefault("agents", {})
        meta = read_json(META_PATH, {})
        for a in agents:
            prev = state["agents"].get(a)
            new = probe_agent(a, meta, force)
            # keep the previous reading when this run produced nothing or older data
            older = (prev and prev.get("windows") and new["windows"]
                     and (parse_time(prev.get("observed_at")) or EPOCH)
                     > (parse_time(new.get("observed_at")) or EPOCH))
            if (older or (not new["windows"] and prev and prev.get("windows"))) and new["source"] != "unsupported":
                prev = dict(prev)
                prev["stale"] = is_stale(prev)
                prev.pop("error", None)
                if new.get("error"):
                    prev["error"] = new["error"]
                prev["fetched_at"] = new["fetched_at"]
                new = prev
            state["agents"][a] = new
        state["updated_at"] = iso(now_utc())
        state["ttl_seconds"] = TTL
        atomic_write_json(STATE_PATH, state)
        atomic_write_json(META_PATH, meta)
        return state


def spawn_detached(agent: str) -> None:
    args = [sys.executable, "-I", os.path.abspath(__file__), "--agent", agent]
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              close_fds=True)
    if os.name == "nt":
        base = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        try:
            subprocess.Popen(args, creationflags=base | 0x01000000, **kw)  # + BREAKAWAY_FROM_JOB
            return
        except OSError:
            subprocess.Popen(args, creationflags=base, **kw)
    else:
        subprocess.Popen(args, start_new_session=True, **kw)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent", default="all", choices=["all"] + AGENTS)
    ap.add_argument("--detach", action="store_true", help="spawn a background probe and return")
    ap.add_argument("--hook", action="store_true", help="hook mode: drain stdin, detach, no output")
    ap.add_argument("--force", action="store_true", help="ignore the network TTL")
    ap.add_argument("--print", action="store_true", help="print the resulting snapshot")
    a = ap.parse_args(argv)
    if a.hook or a.detach:
        if a.hook:
            try:
                if not sys.stdin.isatty():
                    sys.stdin.read()
            except Exception:
                pass
        try:
            spawn_detached(a.agent)
        except Exception as e:
            log(f"spawn failed: {type(e).__name__}")
        return 0
    agents = AGENTS if a.agent == "all" else [a.agent]
    state = run(agents, a.force)
    if a.print:
        print(json.dumps(state if state is not None else read_json(STATE_PATH, {}),
                         ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
