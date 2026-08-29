"""Runs the classical baseline against synthetic ground truth to produce
honest evaluation numbers for the Experiment Comparison table.
"""
from __future__ import annotations

import numpy as np

from ..core.config import settings
from ..cv.detection import get_detector
from ..cv.evaluation import evaluate, EvaluationResult
from ..cv.preprocess import preprocess_pair
from ..services.demo import generate_demo_pair


def run_baseline_evaluation() -> EvaluationResult:
    """Evaluate the classical change detector on the synthetic demo pair."""
    before, after, gt, _ = generate_demo_pair()

    pre = preprocess_pair(before, after)
    detector = get_detector(settings.DEFAULT_MODEL)
    result = detector.detect(pre.before, pre.after)

    mask = (result.mask > 0).astype(np.uint8)
    # Resize ground truth to the (possibly downscaled) processed dimensions.
    gt_resized = resize_gt(gt, mask.shape[1], mask.shape[0])

    return evaluate(mask, gt_resized, "Classical Change Detection")


def resize_gt(gt: np.ndarray, width: int, height: int) -> np.ndarray:
    import cv2

    if gt.shape[1] != width or gt.shape[0] != height:
        gt = cv2.resize(gt, (width, height), interpolation=cv2.INTER_NEAREST)
    return (gt > 0).astype(np.uint8)
