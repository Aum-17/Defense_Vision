"""High-level processing pipeline tying the CV modules together.

Runs the full computer-vision workflow for a before/after pair and returns
structured detections ready to be persisted to the database.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from numpy import ndarray

from ..core.config import settings
from ..core.logging import get_logger
from .classification import get_classifier
from .confidence import calculate_confidence
from .detection import get_detector
from .preprocess import preprocess_pair, load_image
from .registration import get_registrar
from .severity import calculate_severity, DEFAULT_THRESHOLDS
from .types import Detection

logger = get_logger(__name__)


@dataclass
class PipelineOutcome:
    detections: list[Detection] = field(default_factory=list)
    change_percentage: float = 0.0
    method: str = ""
    registration_quality: float = 1.0
    homography_success: bool = True
    registration_message: str = ""
    width: int = 0
    height: int = 0
    mask: ndarray | None = None
    spent: float = 0.0


def run_pipeline(before_path: str, after_path: str) -> PipelineOutcome:
    """Execute the full change-detection pipeline for two image paths."""
    t0 = time.time()
    logger.info("Pipeline start: before=%s after=%s", before_path, after_path)

    before = load_image(before_path)
    after = load_image(after_path)

    pre = preprocess_pair(before, after)

    registrar = get_registrar()
    reg = registrar.register(pre.before, pre.after)

    detector = get_detector(settings.DEFAULT_MODEL)
    result = detector.detect(reg.before_aligned, reg.after_aligned)

    # override registration linkage
    result.homography_success = reg.success
    result.registration_quality = reg.quality
    result.confidence = float(
        np.clip(result.confidence * (0.6 + 0.4 * reg.quality), 0.0, 1.0)
    )

    classifier = get_classifier()
    total_pixels = reg.before_aligned.shape[0] * reg.before_aligned.shape[1]

    diff_gray = np.abs(
        np.asarray(reg.before_aligned, dtype=np.int16)
        - np.asarray(reg.after_aligned, dtype=np.int16)
    ).mean(axis=2).astype(np.float64)

    detections: list[Detection] = []
    for region in result.regions:
        x, y, w, h = region.bbox
        area_ratio = region.area_pixels / max(total_pixels, 1)
        mean_intensity = region.mean_intensity * 255.0

        expression = np.zeros_like(result.mask, dtype=np.uint8)
        expression[y : y + h, x : x + w] = region.mask[y : y + h, x : x + w]

        confidence = calculate_confidence(
            mask=result.mask,
            diff_intensity=diff_gray,
            region_mask=expression,
            registration_quality=reg.quality,
        )
        severity = calculate_severity(area_ratio, mean_intensity / 255.0, DEFAULT_THRESHOLDS)

        category, cat_confidence, rationale = classifier.classify(
            region, reg.before_aligned.shape[:2]
        )

        detections.append(
            Detection(
                change_id=region.change_id,
                bbox=region.bbox,
                area_pixels=region.area_pixels,
                change_percentage=float(region.area_pixels / max(total_pixels, 1) * 100.0),
                mean_intensity=round(mean_intensity, 2),
                confidence=confidence,
                confidence_source=detector.confidence_source,
                severity=severity,
                category=category,
                category_confidence=cat_confidence,
                rationale=rationale,
                centroid=region.centroid,
                mask=region.mask,
            )
        )

    # Keep only regions the severity/confidence engine deems noteworthy enough.
    significant = []
    for d in detections:
        if d.area_pixels >= 40 and d.confidence >= 0.25:
            significant.append(d)
    detections = significant

    elapsed = time.time() - t0
    logger.info("Pipeline complete: %d detections in %.2fs", len(detections), elapsed)

    return PipelineOutcome(
        detections=detections,
        change_percentage=result.percentage,
        method=result.method,
        registration_quality=reg.quality,
        homography_success=reg.success,
        registration_message=reg.message,
        width=reg.before_aligned.shape[1],
        height=reg.before_aligned.shape[0],
        mask=result.mask,
        spent=elapsed,
    )
