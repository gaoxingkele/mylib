# -*- coding: utf-8 -*-
"""Save Windows clipboard to a utf-8 file. Usage: save_clipboard.py OUT.txt"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def read_clipboard() -> str:
    ps = [
        "powershell",
        "-NoProfile",
        "-Command",
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
    ]
    raw = subprocess.check_output(ps)
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    out = Path(sys.argv[1])
    text = read_clipboard()
    out.write_text(text, encoding="utf-8")
    print(out, len(text), text[:80].replace("\n", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
