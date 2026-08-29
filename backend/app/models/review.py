from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class AnalystReview(Base):
    __tablename__ = "analyst_reviews"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"), nullable=False, index=True)
    decision = Column(String(32), nullable=True)  # CONFIRMED | REJECTED | NEEDS_REVIEW
    comment = Column(Text, nullable=True)
    analyst = Column(String(120), nullable=True)
    original_prediction = Column(String(64), nullable=True)
    model_version = Column(String(120), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    detection = relationship("Detection", back_populates="reviews")
