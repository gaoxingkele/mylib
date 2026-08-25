"""Whether a path is spelled absolutely on any platform, not just the one this runs on."""

from __future__ import annotations

import ntpath
import os


def spelled(path: str) -> bool:
    """True for a rooted, drive-qualified or UNC path, whichever platform reads it."""
    return (
        os.path.isabs(path)
        or path.replace("\\", "/").startswith("/")
        or bool(ntpath.splitdrive(path)[0])
    )
