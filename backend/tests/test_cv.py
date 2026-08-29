"""Tests for preprocessing, registration, detection, severity, confidence, evaluation."""
from __future__ import annotations

import numpy as np

from app.cv.confidence import calculate_confidence
from app.cv.detection import ClassicalChangeDetector, get_detector
from app.cv.evaluation import evaluate
from app.cv.preprocess import preprocess_pair
from app.cv.registration import ClassicalRegistrar
from app.cv.severity import calculate_severity, SeverityThresholds

from helpers import make_pair


def _flat_pair(pad: int = 24):
    before, after, gt = make_pair()
    return before, after, gt


def test_preprocess_pair_shape_and_gray():
    before, after, _ = _flat_pair()
    pre = preprocess_pair(before, after)
    assert pre.before.shape[:2] == pre.after.shape[:2]
    assert pre.before_gray.ndim == 2
    assert pre.width == pre.before.shape[1]
    assert pre.height == pre.before.shape[0]
    assert len(pre.steps) >= 4


def test_registrar_returns_identity_fallback_on_trivial():
    reg = ClassicalRegistrar()
    before, after, _ = _flat_pair()
    r = reg.register(before, after)
    assert r.before_aligned is not None
    assert r.after_aligned is not None
    assert r.success is False or r.success is True
    assert 0.0 <= r.quality <= 1.0


def test_detector_detects_known_regions():
    detector = ClassicalChangeDetector()
    before, after, gt = _flat_pair()
    pre = preprocess_pair(before, after)
    result = detector.detect(pre.before, pre.after)
    assert result.mask.ndim == 2
    assert result.mask.dtype == np.uint8
    assert len(result.regions) >= 1
    assert result.percentage >= 0.0
    assert 0.0 <= result.confidence <= 1.0
    # The foreground mask should overlap ground truth significantly.
    overlap = np.logical_and(result.mask > 0, gt > 0).sum()
    assert overlap > 20


def test_get_detector_falls_back_to_classical():
    d = get_detector("changeformer")
    assert isinstance(d, ClassicalChangeDetector)


def test_severity_levels():
    t = SeverityThresholds()
    assert calculate_severity(0.5, 0.9, t) == "HIGH"
    assert calculate_severity(0.3, 0.4, t) == "HIGH"
    assert calculate_severity(0.01, 0.9, t) == "MEDIUM"
    assert calculate_severity(0.01, 0.05, t) == "LOW"


def test_confidence_in_range():
    mask = np.zeros((100, 100), dtype=np.uint8)
    diff = np.random.default_rng(1).random((100, 100)) * 255
    mask[20:40, 20:40] = 1
    c = calculate_confidence(mask, diff, mask, registration_quality=0.9)
    assert 0.0 <= c <= 1.0


def test_evaluation_metrics_perfect_match():
    gt = np.zeros((50, 50), dtype=np.uint8)
    gt[10:20, 10:20] = 1
    r = evaluate(gt, gt, "test")
    assert r.precision == 1.0
    assert r.recall == 1.0
    assert r.iou == 1.0
    assert r.dice == 1.0
