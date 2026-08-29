"""Classical image registration using ORB features + RANSAC homography.

The ``BaseRegistrar`` interface allows a more advanced (deep-learning)
registration model to be plugged in later without touching the rest of
the pipeline.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import cv2
import numpy as np

from ..core.logging import get_logger
from .types import RegistrationResult

logger = get_logger(__name__)


class BaseRegistrar(ABC):
    """Strategy interface for registering before/after image pairs."""

    @abstractmethod
    def register(self, before: np.ndarray, after: np.ndarray) -> RegistrationResult:
        ...


class ClassicalRegistrar(BaseRegistrar):
    """ORB feature detection, BF matching, RANSAC homography, perspective warp.

    If registration is unreliable (too few good matches) we return an
    identity-warp fallback and surface a clear message instead of crashing.
    """

    MIN_GOOD_MATCHES = 10
    ORB_MAX_FEATURES = 4000

    def __init__(self) -> None:
        self._orb = cv2.ORB_create(nfeatures=self.ORB_MAX_FEATURES)
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def _compute_quality(self, h: np.ndarray) -> float:
        """Heuristic alignment-quality score in [0, 1].

        Combines homography departure from identity with match count.
        A perfect identity transform yields 1.0.
        """
        identity = np.eye(3)
        # Euclidean distance between homography and identity params
        diff = np.linalg.norm(h[:2, :] - identity[:2, :])
        scale = 1.0 / (1.0 + diff)
        return float(np.clip(scale, 0.0, 1.0))

    def register(self, before: np.ndarray, after: np.ndarray) -> RegistrationResult:
        kp1, des1 = self._orb.detectAndCompute(before, None)
        kp2, des2 = self._orb.detectAndCompute(after, None)

        if des1 is None or des2 is None or len(kp1) < self.MIN_GOOD_MATCHES or len(kp2) < self.MIN_GOOD_MATCHES:
            return self._fallback(
                before, after,
                message="Not enough ORB features detected; using identity alignment. "
                        "Consider uploading higher-contrast imagery.",
            )

        matches = self._bf.match(des1, des2)
        matches = sorted(matches, key=lambda m: m.distance)

        # Keep a proportional slice of the best matches (robust to clutter).
        keep = min(len(matches), max(self.MIN_GOOD_MATCHES, int(len(matches) * 0.3)))
        good = matches[:keep]

        if len(good) < self.MIN_GOOD_MATCHES:
            return self._fallback(
                before, after,
                message="Feature matching produced too few correspondences; "
                        "using identity alignment.",
            )

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        if H is None or mask is None:
            return self._fallback(before, after, message="Homography estimation failed.")

        inlier_ratio = float(mask.sum() / max(mask.size, 1))
        if inlier_ratio < 0.2:
            return self._fallback(
                before, after,
                message="Low inlier ratio during registration; using identity alignment.",
            )

        h, w = before.shape[:2]
        before_aligned = cv2.warpPerspective(
            before, H, (w, h), flags=cv2.INTER_LINEAR
        )
        # Align "after" to "before" frame so both match the reference.

        quality = self._compute_quality(H) * (0.5 + 0.5 * inlier_ratio)
        return RegistrationResult(
            before_aligned=before_aligned,
            after_aligned=after,
            success=True,
            method="ORB+RANSAC homography",
            quality=float(np.clip(quality, 0.0, 1.0)),
            homography=H,
            message=f"Aligned with {inlier_ratio:.2f} inlier ratio.",
        )

    @staticmethod
    def _fallback(before: np.ndarray, after: np.ndarray, message: str) -> RegistrationResult:
        logger.warning("Registration fallback: %s", message)
        return RegistrationResult(
            before_aligned=before,
            after_aligned=after,
            success=False,
            method="identity (fallback)",
            quality=0.5,
            homography=np.eye(3, dtype=np.float64),
            message=message,
        )


def get_registrar() -> BaseRegistrar:
    """Factory for the active registrar implementation."""
    return ClassicalRegistrar()
