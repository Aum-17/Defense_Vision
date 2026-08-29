"""Health and system information endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ...database import init_db
from ...schemas.health import Health

router = APIRouter(prefix="/api")


@router.get("/health", response_model=Health, tags=["system"])
def health() -> Health:
    from ...core.config import settings

    init_db()  # ensure schema exists (idempotent)
    db_name = "sqlite" if settings.sql_enabled else "postgresql"
    return Health(status="ok", database=db_name, api_version="1.0.0")
