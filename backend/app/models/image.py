from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    type = Column(String(16), nullable=False, index=True)  # before | after
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    metadata_json = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", backref="images")
