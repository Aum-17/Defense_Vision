"""Shared API dependencies."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Analysis


def get_analysis_or_404(db: Session, analysis_id: int) -> Analysis:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


__all__ = ["get_db", "get_analysis_or_404"]
