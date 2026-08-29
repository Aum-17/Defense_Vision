"""Synthetic public demonstration data generator.

Produces clearly-labelled, non-classified synthetic before/after imagery with
obvious, known infrastructure-like changes (buildings, roads) plus a matching
ground-truth annotation mask. Used for Demo Mode and for honest evaluation of
the classical baseline. Nothing here could be mistaken for real intelligence.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from ..core.logging import get_logger

logger = get_logger(__name__)

W, H = 768, 576
SEED = 7


def _solid(shape, rng: np.random.Generator) -> np.ndarray:
    """A textured 'terrain' background image (ground/cloud palette)."""
    base = rng.integers(60, 110, size=shape, dtype=np.uint8)
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    ramp = ((xx / shape[1] * 40 + yy / shape[0] * 30) % 60).astype(np.uint8)
    img = cv2.add(base, ramp)
    noise = rng.integers(-12, 12, size=shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    return cv2.merge([img, img, img])


def _draw_building(img, x, y, w, h, color) -> None:
    cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (20, 20, 20), 1)


def _draw_road(img, pts, color) -> None:
    cv2.line(img, pts[0], pts[1], color, 6)
    cv2.line(img, pts[1], pts[2], color, 6)


def generate_demo_pair() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Generate (before, after, ground_truth_mask, metadata)."""
    rng = np.random.default_rng(SEED)

    before = _solid((H, W), rng)

    # Static buildings (present in both images) to provide visual texture.
    for _ in range(5):
        x = int(rng.integers(20, W - 120))
        y = int(rng.integers(20, H - 90))
        bw = int(rng.integers(55, 110))
        bh = int(rng.integers(40, 80))
        v = int(rng.integers(0, 60))
        _draw_building(before, x, y, bw, bh, (90 + v, 90 + v, 90 + v))

    after = before.copy()

    metadata = {"label": "PUBLIC / SYNTHETIC DEMONSTRATION DATA", "changes": []}
    gt = np.zeros((H, W), dtype=np.uint8)

    def add_change(cid, typ, desc):
        metadata["changes"].append({"id": cid, "type": typ, "description": desc})

    # 1) A new building-like structure appears (after only).
    b1 = {"x": 300, "y": 180, "w": 90, "h": 70}
    _draw_building(after, b1["x"], b1["y"], b1["w"], b1["h"], (200, 160, 140))
    gt[b1["y"] : b1["y"] + b1["h"], b1["x"] : b1["x"] + b1["w"]] = 1
    add_change("CHG-001", "new_structure", "New building-like structure")

    # 2) A structure is removed (before only).
    b2 = {"x": 500, "y": 380, "w": 80, "h": 60}
    _draw_building(before, b2["x"], b2["y"], b2["w"], b2["h"], (180, 150, 130))
    gt[b2["y"] : b2["y"] + b2["h"], b2["x"] : b2["x"] + b2["w"]] = 1
    add_change("CHG-002", "removed_structure", "Structure removed")

    # 3) A road segment appears (after only).
    road = [(80, 500), (360, 500), (430, 440)]
    _draw_road(before, road, (0, 0, 0))
    _draw_road(after, road, (160, 160, 150))
    rm = np.zeros((H, W), dtype=np.uint8)
    cv2.line(rm, road[0], road[1], 1, 7)
    cv2.line(rm, road[1], road[2], 1, 7)
    gt[rm > 0] = 1
    add_change("CHG-003", "road", "New road segment")

    # 4) Surface / possible-damage patch over an open area.
    _draw_building(after, 180, 90, 100, 45, (120, 120, 110))
    gt[90:135, 180:280] = 1
    add_change("CHG-004", "surface_change", "Surface / possible-damage patch")

    return before, after, gt, metadata


def save_demo_pair(dest: Path) -> tuple[Path, Path, Path, dict]:
    """Persist demo imagery + ground truth and return file paths."""
    dest.mkdir(parents=True, exist_ok=True)
    before, after, gt, meta = generate_demo_pair()

    before_path = dest / "demo_before.png"
    after_path = dest / "demo_after.png"
    gt_path = dest / "demo_gt.png"

    cv2.imwrite(str(before_path), before)
    cv2.imwrite(str(after_path), after)
    cv2.imwrite(str(gt_path), gt * 255)

    meta_path = dest / "demo_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    logger.info("Saved demo pair to %s", dest)
    return before_path, after_path, gt_path, meta
