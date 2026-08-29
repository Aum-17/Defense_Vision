"""Extraction of discrete change regions from a binary change mask."""
from __future__ import annotations

import numpy as np
import cv2

from .types import ChangeRegion

MIN_REGION_PIXELS = 40  # ignore tiny speckles below this area


def connected_components(mask: np.ndarray) -> tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    """Run connected-component labelling with statistics.

    Returns (n_labels, labels, stats, centroids) exactly as OpenCV's
    ``connectedComponentsWithStats``.
    """
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    return num, labels, stats, centroids


def extract_regions(
    mask: np.ndarray,
    prefix: str = "CHG",
    start_index: int = 0,
    min_region_pixels: int = MIN_REGION_PIXELS,
) -> list[ChangeRegion]:
    """Turn a binary change mask into a list of discrete ``ChangeRegion``.

    Each region corresponds to one connected component and carries its
    bounding box, area and centroid.
    """
    num, labels, stats, centroids = connected_components(mask)
    regions: list[ChangeRegion] = []

    for i in range(1, num):  # skip background label 0
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_region_pixels:
            continue
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        region_mask = (labels == i).astype(np.uint8)

        cy, cx = int(centroids[i][1]), int(centroids[i][0])
        regions.append(
            ChangeRegion(
                change_id=f"{prefix}-{start_index + len(regions) + 1:03d}",
                bbox=(x, y, w, h),
                area_pixels=area,
                mean_intensity=float(region_mask.mean()),
                mask=region_mask,
                centroid=(cx, cy),
            )
        )
    return regions
