from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    decision: str = Field(..., pattern="^(CONFIRMED|REJECTED|NEEDS_REVIEW)$")
    comment: Optional[str] = None
    analyst: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    detection_id: int
    decision: Optional[str]
    comment: Optional[str]
    analyst: Optional[str]
    original_prediction: Optional[str]
    model_version: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}
