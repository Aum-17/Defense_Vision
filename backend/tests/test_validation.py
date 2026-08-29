"""Tests for image upload validation and safe storage."""
from __future__ import annotations

import io

import pytest
from fastapi import UploadFile

from app.core.config import settings
from app.services.storage import (
    UploadValidationError,
    save_upload,
    validate_image_file,
    validate_upload,
)
from app.utils.files import sanitize_filename


def _upload(content: bytes, name: str) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(content))


def _png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), (0, 0, 0)).save(buf, "PNG")
    return buf.getvalue()


def test_sanitize_filename_prevents_traversal():
    # Path inputs are reduced to their basename, neutralising traversal.
    assert sanitize_filename("../../etc/passwd") == "passwd"
    # Result never contains a path separator.
    assert "/" not in sanitize_filename("a/b/c.png")
    assert "\\" not in sanitize_filename("a\\b\\c.png")
    # Joining the sanitised name with a base dir never escapes it.
    from pathlib import Path

    out = Path("/safe") / sanitize_filename("../../etc/passwd")
    assert out.parent == Path("/safe")


def test_validate_upload_rejects_bad_extension():
    with pytest.raises(UploadValidationError):
        validate_upload(_upload(b"x", "evil.exe"), allowed_extensions=[".png"])


def test_validate_upload_rejects_oversize():
    big = b"a" * (settings.max_upload_bytes + 1)
    with pytest.raises(UploadValidationError):
        validate_upload(_upload(big, "big.png"))


def test_validate_upload_accepts_valid():
    validate_upload(_upload(_png_bytes(), "ok.png"))


def test_validate_image_file_rejects_corrupt(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image at all")
    with pytest.raises(UploadValidationError):
        validate_image_file(bad)


def test_validate_image_file_accepts_valid(tmp_path):
    p = tmp_path / "good.png"
    p.write_bytes(_png_bytes())
    w, h = validate_image_file(p)
    assert (w, h) == (10, 10)
