from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class ModelRun(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    model_name = Column(String(120), nullable=False)
    model_version = Column(String(120), nullable=True)
    execution_time = Column(Float, nullable=True)
    parameters_json = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", backref="model_runs")
