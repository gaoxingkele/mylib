"""CLI entry point: python -m download_tools <url> <dest>"""
from __future__ import annotations

from .download import main

if __name__ == "__main__":
    raise SystemExit(main())
