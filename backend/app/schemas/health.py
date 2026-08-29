from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Health(BaseModel):
    status: str
    database: str
    api_version: str
