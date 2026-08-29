"""Database engine, session and declarative base."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call on every startup."""
    # Import models so they are registered on Base.metadata
    from ..models import ALL_MODELS  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised (%s)", "sqlite" if settings.sql_enabled else "postgresql")
