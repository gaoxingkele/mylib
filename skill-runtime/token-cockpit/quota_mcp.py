#!/usr/bin/env python3
"""quota-mcp: stdio MCP server exposing the agent quota snapshot.

Tools:     list_quotas, get_quota(agent), pick_model(min_remaining=20), refresh(agent?)
Resource:  quota://snapshot
Stdlib only (newline-delimited JSON-RPC 2.0). Reads ~/.agent-quota/state.json,
written by quota_probe.py. pick_model is advisory and read-only.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quota_probe as qp  # noqa: E402

SERVER_INFO = {"name": "quota-mcp", "version": "0.1.0"}
DEFAULT_PROTOCOL = "2025-06-18"

TOOLS = [
    {"name": "list_quotas",
     "description": "All local AI CLIs' quota snapshot (plan, used/remaining %, reset time, freshness), "
                    "sorted by remaining percent. Stale entries must be shown as outdated.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "get_quota",
     "description": "Quota snapshot for one agent: claude, codex, grok, kimi, gemini or opencode.",
     "inputSchema": {"type": "object", "properties": {"agent": {"type": "string", "enum": qp.AGENTS}},
                     "required": ["agent"]}},
    {"name": "pick_model",
     "description": "Advisory, read-only: agents whose tightest window has at least min_remaining % left "
                    "and non-stale data, ordered by earliest weekly reset (use-it-or-lose-it).",
     "inputSchema": {"type": "object", "properties": {
         "min_remaining": {"type": "number", "default": 20},
         "include_stale": {"type": "boolean", "default": False}}}},
    {"name": "refresh",
     "description": "Re-run the probe now (network fallback still limited to once per TTL per agent).",
     "inputSchema": {"type": "object", "properties": {"agent": {"type": "string", "enum": ["all"] + qp.AGENTS}}}},
]


def load_state() -> dict:
    state = qp.read_json(qp.STATE_PATH, {"agents": {}})
    now = qp.now_utc()
    for snap in (state.get("agents") or {}).values():
        if snap.get("source") != "unsupported":
            snap["stale"] = qp.is_stale(snap, now)  # recompute at read time
        for w in snap.get("windows") or []:
            t = qp.parse_time(w.get("resets_at"))
            if t and t < now:  # window rolled over since the probe ran
                w.update(used_percent=0.0, remaining_percent=100.0, resets_at=None,
                         estimated=True, note="observed window has already reset")
    return state


def tightest(snap: dict) -> float | None:
    vals = [w["remaining_percent"] for w in snap.get("windows") or [] if w.get("remaining_percent") is not None]
    return min(vals) if vals else None


def list_quotas() -> dict:
    state = load_state()
    rows = []
    for name, snap in (state.get("agents") or {}).items():
        rows.append({"agent": name, "remaining_min_percent": tightest(snap), **snap})
    rows.sort(key=lambda r: (r["remaining_min_percent"] is None, -(r["remaining_min_percent"] or 0)))
    return {"updated_at": state.get("updated_at"), "ttl_seconds": state.get("ttl_seconds"), "agents": rows}


def get_quota(agent: str) -> dict:
    snap = (load_state().get("agents") or {}).get(agent)
    return {"agent": agent, **snap} if snap else {"agent": agent, "error": "no data yet; call refresh"}


def pick_model(min_remaining: float = 20, include_stale: bool = False) -> dict:
    cands = []
    for name, snap in (load_state().get("agents") or {}).items():
        rem = tightest(snap)
        if rem is None or rem < min_remaining or (snap.get("stale") and not include_stale):
            continue
        resets = [w.get("resets_at") for w in snap["windows"] if w.get("name", "").startswith("weekly") and w.get("resets_at")]
        cands.append({"agent": name, "remaining_min_percent": rem, "weekly_resets_at": min(resets) if resets else None,
                      "stale": snap.get("stale"), "plan": snap.get("plan")})
    cands.sort(key=lambda c: (c["weekly_resets_at"] is None, c["weekly_resets_at"] or "", -c["remaining_min_percent"]))
    return {"min_remaining": min_remaining, "pick": cands[0]["agent"] if cands else None, "candidates": cands,
            "note": "advisory only; the caller decides which model to use"}


def refresh(agent: str = "all") -> dict:
    agents = qp.AGENTS if agent == "all" else [agent]
    qp.run(agents, force=False)
    return list_quotas() if agent == "all" else get_quota(agent)


def call_tool(name: str, args: dict) -> dict:
    if name == "list_quotas":
        return list_quotas()
    if name == "get_quota":
        return get_quota(str(args.get("agent", "")))
    if name == "pick_model":
        return pick_model(float(args.get("min_remaining", 20)), bool(args.get("include_stale", False)))
    if name == "refresh":
        return refresh(str(args.get("agent") or "all"))
    raise KeyError(name)


def handle(msg: dict) -> dict | None:
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if mid is None:  # notification
        return None
    try:
        if method == "initialize":
            res = {"protocolVersion": params.get("protocolVersion") or DEFAULT_PROTOCOL,
                   "capabilities": {"tools": {}, "resources": {}}, "serverInfo": SERVER_INFO}
        elif method == "ping":
            res = {}
        elif method == "tools/list":
            res = {"tools": TOOLS}
        elif method == "tools/call":
            try:
                out = call_tool(params.get("name"), params.get("arguments") or {})
                res = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, indent=2)}],
                       "structuredContent": out, "isError": False}
            except KeyError:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {params.get('name')}"}}
            except Exception as e:
                res = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
        elif method == "resources/list":
            res = {"resources": [{"uri": "quota://snapshot", "name": "agent quota snapshot",
                                  "mimeType": "application/json"}]}
        elif method == "resources/read":
            if params.get("uri") != "quota://snapshot":
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "unknown resource"}}
            res = {"contents": [{"uri": "quota://snapshot", "mimeType": "application/json",
                                 "text": json.dumps(load_state(), ensure_ascii=False, indent=2)}]}
        elif method in ("prompts/list",):
            res = {"prompts": []}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": res}
    except Exception as e:  # never crash the server
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": f"{type(e).__name__}: {e}"}}


def main() -> None:
    stdin = open(sys.stdin.fileno(), encoding="utf-8", errors="replace", closefd=False)
    out = open(sys.stdout.fileno(), "w", encoding="utf-8", newline="\n", closefd=False)
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            out.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}) + "\n")
            out.flush()
            continue
        batch = msg if isinstance(msg, list) else [msg]
        replies = [r for r in (handle(m) for m in batch if isinstance(m, dict)) if r is not None]
        for r in replies:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
