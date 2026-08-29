"""Dashboard aggregation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...models import Analysis, Detection
from ...schemas.analysis import AnalysisOut
from ..deps import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    total_analyses = db.query(Analysis).count()
    total_changes = db.query(Detection).count()
    high = db.query(Detection).filter(Detection.severity == "HIGH").count()
    medium = db.query(Detection).filter(Detection.severity == "MEDIUM").count()
    low = db.query(Detection).filter(Detection.severity == "LOW").count()
    avg_conf = db.query(func.avg(Detection.confidence)).scalar() or 0.0

    status_counts = {
        s: db.query(Analysis).filter(Analysis.status == s).count()
        for s in ["PENDING", "PROCESSING", "COMPLETED", "NEEDS_REVIEW", "FAILED"]
    }
    return {
        "total_analyses": total_analyses,
        "total_changes": total_changes,
        "high_severity": high,
        "medium_severity": medium,
        "low_severity": low,
        "average_confidence": round(float(avg_conf), 3),
        "analysis_status": status_counts,
    }


@router.get("/recent")
def recent(limit: int = 8, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "area": a.area,
            "created_at": a.created_at,
            "status": a.status,
            "model_version": a.model_version,
            "detection_count": len(a.detections),
        }
        for a in rows
    ]
