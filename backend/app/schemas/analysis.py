from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    area: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = None
    analyst: Optional[str] = Field(None, max_length=120)
    analysis_date: Optional[datetime] = None


class AnalysisUpdate(BaseModel):
    name: Optional[str] = None
    area: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    analyst: Optional[str] = None
    analysis_date: Optional[datetime] = None


class AnalysisOut(BaseModel):
    id: int
    name: str
    area: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    analyst: Optional[str]
    analysis_date: Optional[datetime]
    model_version: Optional[str]
    status: str
    error_message: Optional[str]
    processing_time: Optional[float]
    image_height: Optional[int]
    image_width: Optional[int]
    registration_quality: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    has_before: bool = False
    has_after: bool = False
    detection_count: int = 0

    model_config = {"from_attributes": True}


class ImageOut(BaseModel):
    id: int
    analysis_id: int
    type: str
    filename: str
    width: Optional[int]
    height: Optional[int]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
