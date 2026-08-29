"""Image loading and preprocessing pipeline built on OpenCV/NumPy."""
from __future__ import annotations

import cv2
import numpy as np

from ..core.logging import get_logger
from .types import PreprocessResult

logger = get_logger(__name__)

TARGET_MAX_DIM = 1024  # resolution normalisation cap
MIN_DIM = 64


def load_image(path: str) -> np.ndarray:
    """Load an image from disk as an RGB float32 array.

    Returns the image in BGR order (OpenCV convention) as uint8.
    """
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Unable to read image at {path!r} (corrupt or unsupported)")
    return img


def _max_dim(img: np.ndarray) -> int:
    return max(img.shape[0], img.shape[1])


def normalize_resolution(img: np.ndarray) -> np.ndarray:
    """Resize so the longer edge is at most TARGET_MAX_DIM, preserving aspect."""
    scale = TARGET_MAX_DIM / _max_dim(img)
    if scale < 1.0:
        new_w = int(round(img.shape[1] * scale))
        new_h = int(round(img.shape[0] * scale))
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img


def reduce_noise(img: np.ndarray) -> np.ndarray:
    """Gaussian blur for mild noise reduction. Keep small kernel to preserve detail."""
    return cv2.GaussianBlur(img, (3, 3), 0)


def equalize_luminance(bgr: np.ndarray) -> np.ndarray:
    """CLAHE contrast normalisation on the L channel of LAB colour space."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, _ = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, _])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def normalize_color(bgr: np.ndarray) -> np.ndarray:
    """Global mean/std colour normalisation to reduce illumination variation."""
    mean = bgr.mean(axis=(0, 1), keepdims=True)
    std = bgr.std(axis=(0, 1), keepdims=True)
    std = np.where(std < 1e-4, 1.0, std)
    norm = (bgr - mean) / std
    norm = np.clip(norm * 64.0 + 128.0, 0, 255).astype(np.uint8)
    return norm


def preprocess_pair(before: np.ndarray, after: np.ndarray) -> PreprocessResult:
    """Run the full preprocessing pipeline on a before/after pair."""
    steps: list[str] = []

    before = normalize_resolution(before)
    after = normalize_resolution(after)
    steps.append("resolution_normalized")

    before = reduce_noise(before)
    after = reduce_noise(after)
    steps.append("noise_reduced")

    before = equalize_luminance(before)
    after = equalize_luminance(after)
    steps.append("contrast_normalized")

    before = normalize_color(before)
    after = normalize_color(after)
    steps.append("color_normalized")

    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    result = PreprocessResult(
        before=before,
        after=after,
        before_gray=before_gray,
        after_gray=after_gray,
        width=before.shape[1],
        height=before.shape[0],
        steps=steps,
    )
    logger.info("Preprocessing complete: %s", ", ".join(steps))
    return result
