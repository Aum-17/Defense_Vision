"""Helper to produce synthetic before/after images for tests."""
from __future__ import annotations

import cv2
import numpy as np


def make_pair(
    w: int = 256,
    h: int = 192,
    noise: int = 6,
    change_boxes: list[tuple[int, int, int, int]] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create a before/after pair with a known rectangular change.

    Returns (before, after, ground_truth_mask).
    """
    rng = np.random.default_rng(0)
    base = rng.integers(70, 130, size=(h, w, 3), dtype=np.uint8)
    base = cv2.GaussianBlur(base, (3, 3), 0)

    after = base.copy()
    after = np.clip(after.astype(np.int16) + rng.integers(-noise, noise, size=base.shape), 0, 255).astype(np.uint8)

    before = base.copy()
    gt = np.zeros((h, w), dtype=np.uint8)
    change_boxes = change_boxes or [(60, 50, 50, 40), (150, 100, 60, 30)]

    for (x, y, bw, bh) in change_boxes:
        color = (200, 90, 60)
        cv2.rectangle(after, (x, y), (x + bw, y + bh), color, -1)
        gt[y : y + bh, x : x + bw] = 1

    return before, after, gt
