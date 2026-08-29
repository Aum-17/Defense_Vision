"""Filesystem utilities for safe storage.

Guards against path traversal and ensures data directories exist.
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)

# Strip characters that could be used for traversal or are problematic on
# common filesystems.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str) -> str:
    """Sanitize a user-supplied filename into a safe basename."""
    name = Path(filename or "file").name
    name = _UNSAFE.sub("_", name).strip("._")
    if not name:
        name = "file"
    return name


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def new_store_path(base: Path, original_filename: str | None = None) -> Path:
    """Build a unique, safe storage path inside `base`.

    Only the basename of the original filename is ever used and it is
    sanitised, so a crafted value like ``../../etc/passwd`` cannot leave
    the intended directory.
    """
    ensure_dir(base)
    safe = sanitize_filename(original_filename or "file")
    stem = Path(safe).stem
    ext = Path(safe).suffix.lower()
    unique = uuid.uuid4().hex[:12]
    return base / f"{stem}_{unique}{ext}"


def ensure_data_dirs() -> None:
    """Create all configured data directories on startup."""
    from ..core.config import settings

    for path in (
        settings.data_path,
        settings.uploads_path,
        settings.processed_path,
        settings.output_path,
        settings.demo_path,
        settings.annotations_path,
    ):
        ensure_dir(path)
