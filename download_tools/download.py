"""Unified download API: prefer aria2c, fall back to curl/wget/urllib."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from .aria2 import DEFAULT_PROXY, download_with_aria2, find_aria2
from .fallback import fallback_download


def download(
    url: str,
    dest: str | Path,
    *,
    proxy: str | None = DEFAULT_PROXY,
    use_aria2: bool = True,
    fallback: bool = True,
    timeout: int = 60,
    aria2_extra_args: Iterable[str] | None = None,
    **aria2_kwargs,
) -> int:
    """Download ``url`` to ``dest``.

    Parameters
    ----------
    url:
        Remote URL to fetch.
    dest:
        Destination path. If it is an existing directory, the filename is
        inferred from the URL.
    proxy:
        Proxy URL. Pass ``None`` to disable. Defaults to the environment proxy
        used in this workspace.
    use_aria2:
        Try aria2c first when True.
    fallback:
        If aria2c fails or is unavailable, try curl/wget/urllib.
    timeout:
        Fallback timeout in seconds.
    aria2_extra_args:
        Extra arguments appended to the aria2c command.
    **aria2_kwargs:
        Passed to ``download_with_aria2`` (e.g. ``split=32``).

    Returns
    -------
    Exit code: 0 on success, non-zero on failure.
    """
    dest = _resolve_dest(url, dest)

    if use_aria2 and find_aria2() is not None:
        try:
            code = download_with_aria2(
                url,
                dest,
                proxy=proxy,
                extra_args=aria2_extra_args,
                **aria2_kwargs,
            )
            if code == 0:
                return 0
        except FileNotFoundError:
            pass  # aria2c disappeared between check and call

    if fallback:
        return fallback_download(url, dest, proxy=proxy, timeout=timeout)

    return 1


def _resolve_dest(url: str, dest: str | Path) -> Path:
    dest = Path(dest)
    if dest.is_dir():
        name = Path(url.split("?")[0]).name or "download"
        dest = dest / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def download_many(
    items: Iterable[tuple[str, str | Path]],
    *,
    proxy: str | None = DEFAULT_PROXY,
    use_aria2: bool = True,
    stop_on_error: bool = False,
    **kwargs,
) -> list[tuple[str, int]]:
    """Download multiple URLs.

    Returns a list of ``(url, exit_code)`` tuples.
    """
    results = []
    for url, dest in items:
        code = download(url, dest, proxy=proxy, use_aria2=use_aria2, **kwargs)
        results.append((url, code))
        if code != 0 and stop_on_error:
            break
    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for quick ad-hoc downloads."""
    import argparse

    parser = argparse.ArgumentParser(description="Download files, preferring aria2c.")
    parser.add_argument("url", help="URL to download")
    parser.add_argument("dest", help="Destination file or directory")
    parser.add_argument("--no-aria2", action="store_true", help="Disable aria2c")
    parser.add_argument("--no-fallback", action="store_true", help="Disable fallback downloaders")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help="Proxy URL (use 'none' to disable)")
    parser.add_argument("--split", type=int, default=16)
    parser.add_argument("--max-connection-per-server", type=int, default=16)
    args = parser.parse_args(argv)

    proxy = None if args.proxy == "none" else args.proxy
    return download(
        args.url,
        args.dest,
        proxy=proxy,
        use_aria2=not args.no_aria2,
        fallback=not args.no_fallback,
        split=args.split,
        max_connection_per_server=args.max_connection_per_server,
    )


if __name__ == "__main__":
    raise SystemExit(main())
