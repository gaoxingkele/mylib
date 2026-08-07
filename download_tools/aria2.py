"""aria2c wrapper with sane defaults for this environment."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

# Known aria2c locations in this Windows environment.
ARIA2_CANDIDATES = [
    Path(r"C:\Users\10175\AppData\Local\aria2\aria2-1.37.0-win-64bit-build1\aria2c.exe"),
    Path(r"C:\Users\10175\AppData\Local\aria2c.exe"),
    Path(r"C:\Program Files\Netease\GameViewer\bin\aria2c.exe"),
]

DEFAULT_PROXY = "http://127.0.0.1:17890"


def find_aria2() -> Path | None:
    """Return the path to aria2c, or None if not found."""
    exe = shutil.which("aria2c")
    if exe:
        return Path(exe)
    for candidate in ARIA2_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def aria2_command(
    url: str,
    dest: Path,
    *,
    proxy: str | None = DEFAULT_PROXY,
    split: int = 16,
    max_connection_per_server: int = 16,
    min_split_size: str = "1M",
    continue_download: bool = True,
    file_allocation: str = "none",
    max_tries: int = 0,
    retry_wait: int = 5,
    timeout: int = 60,
    connect_timeout: int = 30,
    auto_file_renaming: bool = False,
    allow_overwrite: bool = True,
    extra_args: Iterable[str] | None = None,
) -> list[str]:
    """Build an aria2c command list for the given URL and destination."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(find_aria2() or "aria2c"),
        f"--split={split}",
        f"--max-connection-per-server={max_connection_per_server}",
        f"--min-split-size={min_split_size}",
        f"--continue={'true' if continue_download else 'false'}",
        f"--file-allocation={file_allocation}",
        f"--max-tries={max_tries}",
        f"--retry-wait={retry_wait}",
        f"--timeout={timeout}",
        f"--connect-timeout={connect_timeout}",
        f"--auto-file-renaming={'true' if auto_file_renaming else 'false'}",
        f"--allow-overwrite={'true' if allow_overwrite else 'false'}",
        f"--dir={dest.parent}",
        f"--out={dest.name}",
    ]
    if proxy:
        cmd.append(f"--all-proxy={proxy}")
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)
    return cmd


def download_with_aria2(
    url: str,
    dest: Path,
    *,
    proxy: str | None = DEFAULT_PROXY,
    check: bool = True,
    **kwargs,
) -> int:
    """Download ``url`` to ``dest`` using aria2c.

    Returns the subprocess exit code. Raises ``FileNotFoundError`` if aria2c
    cannot be located.
    """
    aria2 = find_aria2()
    if aria2 is None:
        raise FileNotFoundError("aria2c not found on PATH or in known locations")

    cmd = aria2_command(url, Path(dest), proxy=proxy, **kwargs)
    print("RUN", " ".join(cmd), flush=True, file=sys.stderr)
    return subprocess.call(cmd)
