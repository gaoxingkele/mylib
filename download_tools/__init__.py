"""Global download tools: prefer aria2c, fall back to curl/wget/urllib."""
from __future__ import annotations

from .aria2 import (
    ARIA2_CANDIDATES,
    DEFAULT_PROXY,
    aria2_command,
    download_with_aria2,
    find_aria2,
)
from .download import download, download_many, main
from .fallback import (
    download_with_curl,
    download_with_urllib,
    download_with_wget,
    fallback_download,
)

__all__ = [
    "ARIA2_CANDIDATES",
    "DEFAULT_PROXY",
    "aria2_command",
    "download",
    "download_many",
    "download_with_aria2",
    "download_with_curl",
    "download_with_urllib",
    "download_with_wget",
    "fallback_download",
    "find_aria2",
    "main",
]
