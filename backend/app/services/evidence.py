"""Generates visual evidence crops for each detection.

The evidence (before crop, after crop, difference crop, change mask) is the
basis of the explainability feature and is embedded in the PDF report.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


def _pad_bbox(x, y, w, h, limit_w, limit_h, pad: int = 8) -> tuple[int, int, int, int]:
    x = max(0, x - pad)
    y = max(0, y - pad)
    x2 = min(limit_w, x + w + 2 * pad)
    y2 = min(limit_h, y + h + 2 * pad)
    return x, y, x2 - x, y2 - y


def build_evidence(
    detection_id: int,
    before: np.ndarray,
    after: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    out_dir: Path | None = None,
) -> dict:
    """Write evidence crops for a detection and return a paths dict.

    Returns dict with relative URLs/keys: before, after, difference, mask.
    """
    out_dir = out_dir or settings.output_path
    sub = out_dir / "evidence" / str(detection_id)
    sub.mkdir(parents=True, exist_ok=True)

    x, y, w, h = bbox
    px, py, pw, ph = _pad_bbox(x, y, w, h, before.shape[1], before.shape[0])

    before_crop = before[py : py + ph, px : px + pw]
    after_crop = after[py : py + ph, px : px + pw]
    diff = cv2.absdiff(before, after)
    diff_crop = diff[py : py + ph, px : px + pw]
    mask_crop = mask[py : py + ph, px : px + pw]

    names = {"before": "before.png", "after": "after.png", "difference": "difference.png", "mask": "mask.png"}
    result: dict[str, str] = {}
    fs: dict[str, str] = {}
    for key, fname in names.items():
        path = sub / fname
        try:
            if key == "before" or key == "after":
                cv2.imwrite(str(path), locals()[f"{key}_crop"])
            elif key == "difference":
                cv2.imwrite(str(path), diff_crop)
            else:
                cv2.imwrite(str(path), mask_crop * 255)
            result[key] = f"/api/evidence/{detection_id}/{fname}"
            fs[key + "_path"] = str(path)
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not write evidence %s for detection %s: %s", key, detection_id, exc)
            result[key] = ""
            fs[key + "_path"] = ""
    result["fs_dir"] = str(sub)
    result.update(fs)

    logger.info("Built evidence for detection %s", detection_id)
    return result


def resolve_evidence_dir(detection_id: int) -> Path:
    return (settings.output_path / "evidence" / str(detection_id))
