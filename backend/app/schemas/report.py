from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ReportInfo(BaseModel):
    analysis_id: int
    filename: str
    url: str
    generated_at: str
