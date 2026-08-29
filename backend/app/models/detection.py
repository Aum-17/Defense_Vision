from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = (
        # change_id is scoped per analysis so each analysis can have its own CHG-001...
        UniqueConstraint("analysis_id", "change_id", name="uq_detection_analysis_change"),
    )

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    change_id = Column(String(16), nullable=False)
    category = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=False)
    confidence_source = Column(String(32), default="algorithmic")
    severity = Column(String(16), nullable=True)  # LOW | MEDIUM | HIGH
    area_pixels = Column(Integer, nullable=False, default=0)
    change_percentage = Column(Float, nullable=True)
    bbox_json = Column(String(500), nullable=True)  # [x,y,w,h] in pixels
    coordinates_json = Column(String(500), nullable=True)
    centroid_json = Column(String(200), nullable=True)
    mean_intensity = Column(Float, nullable=True)
    status = Column(String(32), default="PENDING_REVIEW", nullable=False, index=True)
    model_version = Column(String(120), nullable=True)
    evidence_json = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("Analysis", backref="detections")
    reviews = relationship(
        "AnalystReview",
        back_populates="detection",
        cascade="all, delete-orphan",
        uselist=True,
    )
