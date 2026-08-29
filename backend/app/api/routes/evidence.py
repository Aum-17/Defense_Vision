"""Serving generated evidence images (before/after/diff/mask crops)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from ...core.config import settings

router = APIRouter(prefix="/api/evidence", tags=["evidence"])

_SAFE_FILES = {"before.png", "after.png", "difference.png", "mask.png"}


@router.get("/{detection_id}/{filename}")
def get_evidence(detection_id: int, filename: str) -> FileResponse:
    if filename not in _SAFE_FILES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid evidence file")
    path = settings.output_path / "evidence" / str(detection_id) / filename
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return FileResponse(str(path), media_type="image/png")
