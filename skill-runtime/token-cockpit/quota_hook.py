"""Minimal hook entry: drain stdin, start quota_probe.py detached, exit 0 at once.

Kept separate from quota_probe.py so a hook pays only for os/sys/subprocess
imports (target < 200 ms total on Windows). Prints nothing.
"""
import os
import subprocess
import sys


def main():
    try:
        if not sys.stdin.isatty():
            sys.stdin.read()
    except Exception:
        pass
    probe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quota_probe.py")
    args = [sys.executable, "-I", probe, "--agent", "all"]
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    try:
        if os.name == "nt":
            base = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            try:
                subprocess.Popen(args, creationflags=base | 0x01000000, **kw)  # + BREAKAWAY_FROM_JOB
            except OSError:
                subprocess.Popen(args, creationflags=base, **kw)
        else:
            subprocess.Popen(args, start_new_session=True, **kw)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
