"""Transparent, algorithmic confidence scoring.

Confidence here reflects measurable signal qualities (change intensity,
region coverage, consistency, registration quality, mask stability). It is
explicitly *not* the probabilistic output of a neural network, so the source
is always labelled ``algorithmic``.
"""
from __future__ import annotations

import numpy as np


def calculate_confidence(
    mask: np.ndarray,
    diff_intensity: np.ndarray,
    region_mask: np.ndarray,
    registration_quality: float,
    stability: float = 1.0,
) -> float:
    """Compute a confidence score in [0, 1] for a detected region.

    Components:
      - intensity   : how distinct the region's change is from the background
      - coverage    : what fraction of the scene width/height the change spans
      - consistency : how uniformly the change fills its bounding box
      - alignment   : registration quality (0..1)
      - stability   : segmentation stability factor (default 1.0)
    """
    # Intensity separation between region and global background.
    fg = diff_intensity[region_mask > 0]
    bg = diff_intensity[region_mask == 0]
    fg_mean = float(fg.mean()) if fg.size else 0.0
    bg_mean = float(bg.mean()) if bg.size else 0.0
    sep = abs(fg_mean - bg_mean) / 255.0
    intensity = float(np.clip(sep, 0.0, 1.0))

    # Coverage relative to image.
    coverage = float(np.clip(mask.mean() / np.clip(mask.max(), 1e-6, 1.0), 0.0, 1.0))

    # Consistency: how fully the region fills its own bbox.
    ys, xs = np.where(region_mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        consistency = 0.0
    else:
        bbox_area = (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)
        consistency = float(np.clip(len(xs) / max(bbox_area, 1), 0.0, 1.0))

    weights = np.array([0.5, 0.15, 0.15, 0.15, 0.05])
    factors = np.array([intensity, coverage, consistency, registration_quality, stability])

    # Boost confidence when the change is both intense and consistent; penalise
    # when alignment is poor.
    score = float(np.dot(weights, factors))
    return float(np.clip(score * (0.6 + 0.4 * registration_quality), 0.0, 1.0))
