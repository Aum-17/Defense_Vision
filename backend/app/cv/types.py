"""Shared data structures used across the Computer Vision pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from numpy import ndarray


@dataclass
class PreprocessResult:
    before: ndarray
    after: ndarray
    before_gray: ndarray
    after_gray: ndarray
    width: int
    height: int
    steps: list[str] = field(default_factory=list)


@dataclass
class RegistrationResult:
    before_aligned: ndarray
    after_aligned: ndarray
    success: bool
    method: str
    quality: float = 0.0  # 0..1 alignment quality proxy
    homography: Optional[ndarray] = None
    message: str = ""


@dataclass
class ChangeRegion:
    change_id: str
    bbox: tuple[int, int, int, int]  # x, y, w, h
    area_pixels: int
    mean_intensity: float
    mask: ndarray
    centroid: tuple[int, int]


@dataclass
class Classification:
    category: str
    confidence: float
    rationale: str


@dataclass
class Detection:
    change_id: str
    bbox: tuple[int, int, int, int]
    area_pixels: int
    change_percentage: float
    mean_intensity: float
    confidence: float
    confidence_source: str
    severity: str
    category: str
    category_confidence: float
    rationale: str
    centroid: tuple[int, int]
    mask: Optional[ndarray] = None


@dataclass
class ChangeDetectionResult:
    mask: ndarray
    regions: list[ChangeRegion]
    percentage: float
    method: str
    confidence: float
    homography_success: bool
    registration_quality: float
