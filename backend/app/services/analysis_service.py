"""Orchestration service that runs the CV pipeline for an analysis and
persists results. Designed to be invoked from a FastAPI BackgroundTask so the
API does not block while expensive operations run.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.logging import get_logger
from ..cv.pipeline import run_pipeline
from ..cv.preprocess import load_image
from ..database import SessionLocal
from ..models import Analysis, Detection, ModelRun
from .evidence import build_evidence
from .storage import validate_image_file

logger = get_logger(__name__)

CLASSIFICATION_CATEGORIES = [
    "New Structure", "Removed Structure", "Structural Change",
    "Road Change", "Surface Change", "Possible Damage", "Other Change",
]


def resolve_upload_path(db: Session, analysis: Analysis, image_type: str) -> Path | None:
    for img in analysis.images:
        if img.type == image_type:
            return Path(img.path)
    return None


def _map_category(heuristic_category: str) -> str:
    """Translate heuristic category into a change-classification label."""
    base = {
        "Building": "Structural Change",
        "Large Structure": "Structural Change",
        "Road": "Road Change",
        "Open Area": "Surface Change",
        "Other": "Other Change",
    }
    # Refine by direction heuristics is not possible with a single diff mask;
    # we keep neutral potential-based labels.
    return base.get(heuristic_category, "Other Change")


def process_analysis(db: Session, analysis_id: int) -> None:
    """Run the pipeline and persist detections. Sets status on completion."""
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        logger.error("Analysis %s not found for processing", analysis_id)
        return

    before_path = resolve_upload_path(db, analysis, "before")
    after_path = resolve_upload_path(db, analysis, "after")

    if before_path is None or after_path is None:
        analysis.status = "FAILED"
        analysis.error_message = "Both before and after images are required."
        analysis.completed_at = datetime.utcnow()
        db.commit()
        return

    try:
        # Re-validate stored files decodable before running.
        validate_image_file(before_path)
        validate_image_file(after_path)

        outcome = run_pipeline(str(before_path), str(after_path))

        # Regenerate in-memory masks for evidence crop generation.
        before_proc = load_image(str(before_path))

        analysis.model_version = settings.DEFAULT_MODEL
        analysis.status = "COMPLETED"
        analysis.processing_time = outcome.spent
        analysis.image_width = outcome.width
        analysis.image_height = outcome.height
        analysis.registration_quality = outcome.registration_quality
        analysis.completed_at = datetime.utcnow()
        db.flush()

        model_run = ModelRun(
            analysis_id=analysis.id,
            model_name="Classical Change Detection",
            model_version=settings.DEFAULT_MODEL,
            execution_time=outcome.spent,
            parameters_json=json.dumps(
                {
                    "method": outcome.method,
                    "registration": {
                        "success": outcome.homography_success,
                        "quality": outcome.registration_quality,
                        "message": outcome.registration_message,
                    },
                }
            ),
        )
        db.add(model_run)
        db.flush()

        mask_full = outcome.mask
        after_proc = load_image(str(after_path))

        # Persist full change-mask PNG for overlay mode.
        import cv2

        mask_path = settings.output_path / f"analysis_{analysis.id}_mask.png"
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(mask_path), (mask_full > 0).astype("uint8") * 255)

        det_ids: list[int] = []
        for i, det in enumerate(outcome.detections):
            change_id = f"CHG-{i + 1:03d}"
            category = _map_category(det.category)

            record = Detection(
                analysis_id=analysis.id,
                change_id=change_id,
                category=category,
                confidence=round(det.confidence, 3),
                confidence_source=det.confidence_source,
                severity=det.severity,
                area_pixels=det.area_pixels,
                change_percentage=round(det.change_percentage, 3),
                bbox_json=json.dumps(list(det.bbox)),
                centroid_json=json.dumps(list(det.centroid)),
                mean_intensity=det.mean_intensity,
                status="PENDING_REVIEW",
                model_version=settings.DEFAULT_MODEL,
            )
            db.add(record)
            db.flush()

            # Now generate evidence with the real id.
            ev = build_evidence(
                detection_id=record.id,
                before=before_proc,
                after=after_proc,
                mask=mask_full,
                bbox=det.bbox,
            )
            record.evidence_json = json.dumps(ev)
            det_ids.append(record.id)

        db.commit()
        logger.info(
            "Analysis %s completed: %d detections in %.2fs",
            analysis_id, len(det_ids), outcome.spent,
        )
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        analysis = db.get(Analysis, analysis_id)
        if analysis is not None:
            analysis.status = "FAILED"
            analysis.error_message = str(exc)
            analysis.completed_at = datetime.utcnow()
            db.commit()
        logger.exception("Processing failed for analysis %s", analysis_id)


def run_processing_task(analysis_id: int) -> None:
    """Spin up a dedicated DB session and run the pipeline.

    Intended to be scheduled from a FastAPI BackgroundTask so the API
    returns immediately while CV processing happens in the background.
    """
    db = SessionLocal()
    try:
        process_analysis(db, analysis_id)
    finally:
        db.close()
