#!/usr/bin/env python3
"""Install / uninstall token-cockpit hooks and the quota-mcp server.

  install.py install     back up configs, append Stop hooks, register MCP
  install.py uninstall   remove only the entries this script added
  install.py status      show what is installed

Rules: existing hook entries (e.g. Orca's) are never modified or reordered; our
entry is appended as a separate group and recognised by the quota_hook.py path.
Backups go to ~/.agent-quota/backups/<file>.<timestamp>.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
PY = sys.executable.replace("\\", "/")
HOOK_CMD = f"{PY} -I -S {HERE}/quota_hook.py"
MARK = "token-cockpit/quota_hook.py"
HOME = os.path.expanduser("~")
BACKUP_DIR = os.path.join(HOME, ".agent-quota", "backups")
CLAUDE_SETTINGS = os.path.join(HOME, ".claude", "settings.json")
CODEX_HOOKS = os.path.join(HOME, ".codex", "hooks.json")
CODEX_CONFIG = os.path.join(HOME, ".codex", "config.toml")
GROK_HOOK = os.path.join(HOME, ".grok", "hooks", "agent-quota.json")
CLAUDE_JSON = os.path.join(HOME, ".claude.json")
MCP_NAME = "quota-mcp"
TOML_BEGIN = "# >>> token-cockpit quota-mcp >>>"
TOML_END = "# <<< token-cockpit quota-mcp <<<"


def backup(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"{os.path.basename(path).lstrip('.')}.{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(path, dst)
    return dst


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path: str, obj: dict) -> None:
    tmp = path + ".tmp-token-cockpit"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    json.loads(open(tmp, encoding="utf-8").read())  # validate before replacing
    os.replace(tmp, path)


def has_mark(group: dict) -> bool:
    return any(MARK in str(h.get("command", "")) for h in group.get("hooks", []))


def add_stop_hook(path: str, events=("Stop",)) -> str:
    if not os.path.exists(path):
        return f"skip {path} (not found)"
    data = load(path)
    hooks = data.setdefault("hooks", {})
    changed = False
    for ev in events:
        groups = hooks.setdefault(ev, [])
        if not any(has_mark(g) for g in groups):
            groups.append({"hooks": [{"type": "command", "command": HOOK_CMD, "timeout": 5}]})
            changed = True
    if not changed:
        return f"ok   {path} (already installed)"
    b = backup(path)
    save(path, data)
    return f"add  {path} (backup {b})"


def remove_stop_hook(path: str) -> str:
    if not os.path.exists(path):
        return f"skip {path}"
    data = load(path)
    changed = False
    for ev, groups in list((data.get("hooks") or {}).items()):
        keep = [g for g in groups if not has_mark(g)]
        if len(keep) != len(groups):
            data["hooks"][ev] = keep
            changed = True
    if not changed:
        return f"ok   {path} (nothing to remove)"
    b = backup(path)
    save(path, data)
    return f"del  {path} (backup {b})"


def grok_hook(install: bool) -> str:
    if not os.path.isdir(os.path.join(HOME, ".grok")):
        return "skip grok (not installed)"
    if install:
        os.makedirs(os.path.dirname(GROK_HOOK), exist_ok=True)
        save(GROK_HOOK, {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": HOOK_CMD, "timeout": 5}]}]}})
        return f"add  {GROK_HOOK}"
    if os.path.exists(GROK_HOOK):
        os.unlink(GROK_HOOK)
        return f"del  {GROK_HOOK}"
    return "ok   grok (nothing to remove)"


def claude_mcp(install: bool) -> str:
    exe = shutil.which("claude")
    if not exe:
        return "skip claude mcp (claude CLI not found)"
    if install:
        if os.path.exists(CLAUDE_JSON) and MCP_NAME in json.dumps(load(CLAUDE_JSON).get("mcpServers", {})):
            return "ok   claude mcp (already registered)"
        backup(CLAUDE_JSON)
        cmd = [exe, "mcp", "add", "--scope", "user", MCP_NAME, "--", PY, "-I", f"{HERE}/quota_mcp.py"]
    else:
        cmd = [exe, "mcp", "remove", "--scope", "user", MCP_NAME]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return f"{'add ' if install else 'del '} claude mcp: rc={r.returncode} {(r.stdout or r.stderr).strip()[:160]}"


def codex_mcp(install: bool) -> str:
    if not os.path.exists(CODEX_CONFIG):
        return "skip codex mcp (config.toml not found)"
    text = open(CODEX_CONFIG, encoding="utf-8").read()
    block_re = re.compile(re.escape(TOML_BEGIN) + r".*?" + re.escape(TOML_END) + r"\n?", re.S)
    present = bool(block_re.search(text))
    if install:
        if present:
            return "ok   codex mcp (already registered)"
        block = (f"\n{TOML_BEGIN}\n[mcp_servers.quota]\ncommand = \"{PY}\"\n"
                 f"args = [\"-I\", \"{HERE}/quota_mcp.py\"]\n{TOML_END}\n")
        new = text.rstrip("\n") + "\n" + block
    else:
        if not present:
            return "ok   codex mcp (nothing to remove)"
        new = block_re.sub("", text)
    b = backup(CODEX_CONFIG)
    with open(CODEX_CONFIG, "w", encoding="utf-8") as f:
        f.write(new)
    return f"{'add ' if install else 'del '} {CODEX_CONFIG} (backup {b})"


def status() -> None:
    for p in (CLAUDE_SETTINGS, CODEX_HOOKS):
        if os.path.exists(p):
            d = load(p)
            n = sum(has_mark(g) for gs in (d.get("hooks") or {}).values() for g in gs)
            print(f"{p}: our hook groups = {n}; JSON valid")
    print(f"{GROK_HOOK}: {'present' if os.path.exists(GROK_HOOK) else 'absent'}")
    if os.path.exists(CODEX_CONFIG):
        print(f"{CODEX_CONFIG}: quota block {'present' if TOML_BEGIN in open(CODEX_CONFIG, encoding='utf-8').read() else 'absent'}")
    if os.path.exists(CLAUDE_JSON):
        print(f"{CLAUDE_JSON}: {MCP_NAME} {'present' if MCP_NAME in load(CLAUDE_JSON).get('mcpServers', {}) else 'absent'}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "install":
        for line in (add_stop_hook(CLAUDE_SETTINGS), add_stop_hook(CODEX_HOOKS), grok_hook(True),
                     claude_mcp(True), codex_mcp(True)):
            print(line)
        print("NOTE: Codex asks you to trust new hooks (review via /hooks) before the Stop hook runs.")
    elif cmd == "uninstall":
        for line in (remove_stop_hook(CLAUDE_SETTINGS), remove_stop_hook(CODEX_HOOKS), grok_hook(False),
                     claude_mcp(False), codex_mcp(False)):
            print(line)
    status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
