"""Fallback downloaders used when aria2c is unavailable."""
from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def _which(name: str) -> str | None:
    return shutil.which(name)


def download_with_urllib(url: str, dest: Path, *, timeout: int = 60) -> int:
    """Download using Python's stdlib urllib.request.urlretrieve."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"fallback urllib: {url} -> {dest}", flush=True, file=sys.stderr)
    try:
        urllib.request.urlretrieve(url, dest)  # noqa: S310
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"urllib failed: {exc}", flush=True, file=sys.stderr)
        return 1


def download_with_curl(url: str, dest: Path, *, proxy: str | None = None, timeout: int = 60) -> int:
    """Download using curl."""
    curl = _which("curl")
    if curl is None:
        return 127
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        curl,
        "-L",  # follow redirects
        "-f",  # fail on HTTP error
        "-C", "-",  # resume
        "--max-time", str(timeout),
        "-o", str(dest),
    ]
    if proxy:
        cmd.extend(["-x", proxy, "--proxytunnel"])
    cmd.append(url)
    print(f"fallback curl: {url} -> {dest}", flush=True, file=sys.stderr)
    return subprocess.call(cmd)


def download_with_wget(url: str, dest: Path, *, proxy: str | None = None, timeout: int = 60) -> int:
    """Download using wget."""
    wget = _which("wget")
    if wget is None:
        return 127
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        wget,
        "--continue",
        "--tries=0",
        "--timeout", str(timeout),
        "-O", str(dest),
    ]
    if proxy:
        cmd.append(f"--proxy=on")
        # wget uses environment variables; set them in subprocess if needed.
    cmd.append(url)
    print(f"fallback wget: {url} -> {dest}", flush=True, file=sys.stderr)
    return subprocess.call(cmd)


def fallback_download(
    url: str,
    dest: Path,
    *,
    proxy: str | None = None,
    timeout: int = 60,
    prefer: list[str] | None = None,
) -> int:
    """Try a series of fallback downloaders until one succeeds.

    The default order is curl -> wget -> urllib.
    """
    dest = Path(dest)
    order = prefer or ["curl", "wget", "urllib"]
    for name in order:
        if name == "curl":
            code = download_with_curl(url, dest, proxy=proxy, timeout=timeout)
        elif name == "wget":
            code = download_with_wget(url, dest, proxy=proxy, timeout=timeout)
        elif name == "urllib":
            code = download_with_urllib(url, dest, timeout=timeout)
        else:
            raise ValueError(f"unknown fallback downloader: {name}")
        if code == 0:
            return 0
    return 1
