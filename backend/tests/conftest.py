"""Shared pytest fixtures.

For tests we use an in-memory SQLite database so no external DB is required.
Environment variables are set *before* importing the application so that the
cached Settings object points at SQLite.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure tests run against SQLite regardless of environment.
os.environ["DATABASE_URL"] = "sqlite:///./data/test_defencevision.db"
os.environ["DATA_ROOT"] = "./data"
os.environ["LOG_LEVEL"] = "ERROR"

# Make the backend package importable.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / "app"))
sys.path.insert(0, str(TESTS_DIR))


@pytest.fixture(scope="session", autouse=True)
def _app_setup():
    from app.core.config import settings
    from app.database import Base, engine, SessionLocal
    from app.utils.files import ensure_data_dirs

    ensure_data_dirs()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    from app.database import SessionLocal

    session = SessionLocal()
    from app.database import Base

    Base.metadata.create_all(bind=session.get_bind())
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
