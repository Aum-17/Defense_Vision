from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DetectionOut(BaseModel):
    id: int
    analysis_id: int
    change_id: str
    category: Optional[str]
    confidence: float
    confidence_source: str
    severity: Optional[str]
    area_pixels: int
    change_percentage: Optional[float]
    bbox_json: Optional[str]
    coordinates_json: Optional[str]
    centroid_json: Optional[str]
    mean_intensity: Optional[float]
    status: str
    model_version: Optional[str]
    evidence_json: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DetectionStatistics(BaseModel):
    total: int
    confirmed: int
    rejected: int
    needs_review: int
    pending_review: int
    high: int
    medium: int
    low: int
    avg_confidence: float
    categories: dict


class AnalysisStats(BaseModel):
    analysis_id: int
    status: str
    total_images: int
    image_height: Optional[int]
    image_width: Optional[int]
    registration_quality: Optional[float]
    processing_time: Optional[float]
    detection_statistics: DetectionStatistics
