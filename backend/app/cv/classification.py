"""Infrastructure / object category assignment for detected change regions.

This is a lightweight rule-based classifier used by the classical baseline.
The ``BaseObjectClassifier`` interface means a real object-detection model
(YOLO, RT-DETR, Faster R-CNN, Mask R-CNN) can be plugged in later.

We deliberately classify only broad *infrastructure* categories and never
weapon/personnel categories, keeping the system a civilian infrastructure
assessment tool.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from numpy import ndarray

from .types import ChangeRegion

CATEGORIES = ["Building", "Road", "Open Area", "Large Structure", "Other"]


class BaseObjectClassifier(ABC):
    @abstractmethod
    def classify(self, region: ChangeRegion, image_shape: tuple[int, int]) -> tuple[str, float, str]:
        """Return (category, confidence, rationale)."""
        ...


class RuleBasedClassifier(BaseObjectClassifier):
    """Classify regions by geometry/aspect ratio and position heuristic.

    Note: this is a *heuristic* categorisation, not a learned model. It is
    clearly labelled as such in the UI/report.
    """

    def classify(self, region: ChangeRegion, image_shape: tuple[int, int]) -> tuple[str, float, str]:
        x, y, w, h = region.bbox
        img_h, img_w = image_shape

        aspect = (w + 1) / (h + 1)
        area_ratio = region.area_pixels / max(img_h * img_w, 1)
        fill_ratio = region.area_pixels / max(w * h, 1)

        category = "Other"
        confidence = 0.5
        rationale = "No confident category assigned by heuristic."

        if area_ratio > 0.30:
            category, confidence, rationale = "Large Structure", 0.7, (
                "Region covers a substantial fraction of the scene."
            )
        elif fill_ratio > 0.85 and 0.4 < aspect < 2.5:
            category, confidence, rationale = "Building", 0.6, (
                "Compact high-fill region, consistent with a building-like footprint."
            )
        elif aspect > 3.5 or (aspect > 2.5 and h <= img_h * 0.15):
            category, confidence, rationale = "Road", 0.6, (
                "Elongated aspect ratio, consistent with a road or linear feature."
            )
        elif area_ratio < 0.01:
            category, confidence, rationale = "Open Area", 0.5, (
                "Small dispersed region consistent with an open-area surface change."
            )

        return category, min(confidence, 0.95), rationale


def get_classifier() -> BaseObjectClassifier:
    """Factory returning the active object classifier."""
    return RuleBasedClassifier()
