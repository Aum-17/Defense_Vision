"""Change Detection Engine: strategy interface + classical baseline.

The ``BaseChangeDetector`` abstract interface lets future deep-learning
detectors (Siamese CNN, U-Net, ChangeFormer, BIT) be dropped in without
changing the rest of the pipeline. A factory resolves the active model.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import cv2
import numpy as np

from .types import ChangeDetectionResult, ChangeRegion
from .regions import extract_regions

MODEL_INFO = {
    "classical": {
        "name": "Classical Change Detection",
        "version": "v1.0",
        "source": "algorithmic",
    },
}


class BaseChangeDetector(ABC):
    """Interface every change detector must implement."""

    name: str
    version: str
    confidence_source: str = "algorithmic"

    @abstractmethod
    def detect(self, before: np.ndarray, after: np.ndarray) -> ChangeDetectionResult:
        ...


class ClassicalChangeDetector(BaseChangeDetector):
    """Baseline: aligned-image difference + threshold + morphology + CC.

    Steps: absolute difference -> blur -> Otsu threshold -> morphological
    open/close -> connected components -> bounding boxes -> area stats.
    """

    name = "Classical Change Detection"
    version = "v1.0"
    confidence_source = "algorithmic"

    def __init__(self, blur_kernel: int = 5) -> None:
        self.blur_kernel = blur_kernel

    def detect(self, before: np.ndarray, after: np.ndarray) -> ChangeDetectionResult:
        if before.shape != after.shape:
            raise ValueError(
                f"Shape mismatch before={before.shape} after={after.shape}; "
                "images must be aligned to the same dimensions first."
            )

        before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(before_gray, after_gray)
        diff_blur = cv2.GaussianBlur(diff, (self.blur_kernel, self.blur_kernel), 0)

        _, mask = cv2.threshold(diff_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        mask = (mask > 0).astype(np.uint8)

        regions = extract_regions(mask, start_index=0)
        total_pixels = mask.size
        percentage = float(mask.sum() / max(total_pixels, 1) * 100.0)

        # Aggregate change confidence from the discriminating power of the
        # thresholded signal (see confidence.py for per-detection scoring).
        foreground = diff_blur[mask > 0]
        bg = diff_blur[mask == 0]
        fg_mean = float(foreground.mean()) if foreground.size else 0.0
        bg_mean = float(bg.mean()) if bg.size else 0.0
        separation = abs(fg_mean - bg_mean) / 255.0
        coverage = float(mask.mean())

        result = ChangeDetectionResult(
            mask=mask,
            regions=regions,
            percentage=percentage,
            method=f"{self.name} {self.version}",
            confidence=float(np.clip(0.5 * separation + 0.5 * coverage, 0.0, 1.0)),
            homography_success=True,
            registration_quality=1.0,
        )
        return result


def get_detector(model_name: str) -> BaseChangeDetector:
    """Factory resolving the active detector implementation.

    Unknown/inapplicable model names fall back to the classical baseline so
    the application never requires a heavyweight deep-learning checkpoint to
    run.
    """
    name = (model_name or "classical").lower()
    if "classical" in name:
        return ClassicalChangeDetector()
    # Future: Siamese / U-Net / ChangeFormer / BIT
    # if "changeformer" in name: return ChangeFormerDetector()
    return ClassicalChangeDetector()
