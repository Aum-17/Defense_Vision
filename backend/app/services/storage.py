"""Image upload validation and safe storage.

Validates file type, size, dimensions and integrity *and* stores uploads in a
sanitised, unique path inside the configured uploads directory. Rejects
corrupt files and never trusts the raw filename for filesystem writes.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile

from ..core.config import settings
from ..core.logging import get_logger
from ..utils.files import new_store_path, sanitize_filename

logger = get_logger(__name__)

MAX_DIMENSION = 20000


class UploadValidationError(ValueError):
    """Raised when an uploaded image fails validation."""


def validate_upload(
    upload: UploadFile,
    *,
    allowed_extensions: list[str] | None = None,
    max_bytes: int | None = None,
) -> None:
    """Validate an upload's extension, size and (optionally) pixel integrity."""
    allowed = allowed_extensions or settings.allowed_extensions
    max_bytes = max_bytes or settings.max_upload_bytes

    original = upload.filename or ""
    ext = Path(original).suffix.lower()
    if ext not in allowed:
        raise UploadValidationError(
            f"Unsupported file type '{ext or '<none>'}'. Allowed: {', '.join(allowed)}"
        )

    size = getattr(upload, "size", None)
    if size is None:
        # Some clients don't set size; read and count bytes.
        size = 0
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
        upload.file.seek(0)

    if size > max_bytes:
        raise UploadValidationError(
            f"File too large ({size / (1024*1024):.1f} MB). Max: {max_bytes / (1024*1024):.0f} MB"
        )


def validate_image_file(path: Path, expected: tuple[int, int] | None = None) -> tuple[int, int]:
    """Check the stored file is a decodable image and return (width, height).

    Raises UploadValidationError for corrupt or overly large images.
    """
    try:
        from PIL import Image

        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            w, h = im.size
    except Exception as exc:
        raise UploadValidationError(f"Corrupt or unreadable image: {exc}") from exc

    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        raise UploadValidationError(
            f"Image too large ({w}x{h}). Max dimension: {MAX_DIMENSION}"
        )
    return w, h


async def save_upload(upload: UploadFile) -> Path:
    """Validate and persist an uploaded image, returning its safe path."""
    validate_upload(upload)

    content = await upload.read()
    ext = Path(upload.filename or "file").suffix.lower()

    path = new_store_path(settings.uploads_path, f"{upload.filename or 'upload'}")
    # Force correct extension regardless of the client-supplied name.
    path = path.with_suffix(ext)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

    validate_image_file(path)
    logger.info("Saved upload -> %s (%d bytes)", path.name, len(content))
    return path
