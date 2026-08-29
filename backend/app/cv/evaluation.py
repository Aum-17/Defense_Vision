"""Model evaluation metrics computed against ground-truth annotations.

Honest metrics only — if no ground truth is available for a method, the
caller must surface ``Not evaluated`` rather than inventing numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class EvaluationResult:
    method: str
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    iou: Optional[float] = None
    dice: Optional[float] = None
    accuracy: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    evaluated: bool = True
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "precision": round(self.precision, 4) if self.precision is not None else None,
            "recall": round(self.recall, 4) if self.recall is not None else None,
            "f1": round(self.f1, 4) if self.f1 is not None else None,
            "iou": round(self.iou, 4) if self.iou is not None else None,
            "dice": round(self.dice, 4) if self.dice is not None else None,
            "accuracy": round(self.accuracy, 4) if self.accuracy is not None else None,
            "false_positive_rate": round(self.false_positive_rate, 4) if self.false_positive_rate is not None else None,
            "false_negative_rate": round(self.false_negative_rate, 4) if self.false_negative_rate is not None else None,
            "evaluated": self.evaluated,
            "note": self.note,
        }


def evaluate(mask: np.ndarray, ground_truth: np.ndarray, method: str) -> EvaluationResult:
    """Compare a binary prediction mask against ground truth (pixel-level)."""
    pred = (mask > 0).astype(np.uint8)
    gt = (ground_truth > 0).astype(np.uint8)
    if pred.shape != gt.shape:
        raise ValueError("Prediction and ground-truth masks must have the same shape.")

    tp = float(np.logical_and(pred == 1, gt == 1).sum())
    fp = float(np.logical_and(pred == 1, gt == 0).sum())
    fn = float(np.logical_and(pred == 0, gt == 1).sum())
    tn = float(np.logical_and(pred == 0, gt == 0).sum())

    total = float(pred.size)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return EvaluationResult(
        method=method,
        precision=precision,
        recall=recall,
        f1=f1,
        iou=iou,
        dice=dice,
        accuracy=accuracy,
        false_positive_rate=fpr,
        false_negative_rate=fnr,
    )


def comparison_table() -> list[dict]:
    """Return the experiment comparison table.

    Only methods with real results are filled in; the rest are clearly
    marked 'Not evaluated'.
    """
    from ..services.evaluation_runner import run_baseline_evaluation

    try:
        baseline = run_baseline_evaluation()
    except Exception as exc:  # pragma: no cover - defensive
        baseline = EvaluationResult(
            method="Classical Change Detection", evaluated=False,
            note=f"Evaluation unavailable: {exc}",
        )

    rows = []
    for label in (
        "Classical Change Detection",
        "Siamese CNN (planned)",
        "U-Net (planned)",
        "ChangeFormer (planned)",
        "BIT Transformer (planned)",
    ):
        if label == baseline.method:
            rows.append(baseline.as_dict())
        else:
            rows.append(
                EvaluationResult(
                    method=label, evaluated=False, note="Not evaluated"
                ).as_dict()
            )
    return rows
