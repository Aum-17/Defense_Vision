from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from ..database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    area = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    analyst = Column(String(120), nullable=True)
    analysis_date = Column(DateTime, nullable=True)
    model_version = Column(String(120), nullable=True)
    status = Column(String(32), default="PENDING", nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    image_height = Column(Integer, nullable=True)
    image_width = Column(Integer, nullable=True)
    registration_quality = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
