"""DefenceVision FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import analyses, dashboard, detections, evaluation, evidence, health
from .core.config import settings
from .core.logging import get_logger, setup_logging
from .database import init_db
from .utils.files import ensure_data_dirs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    ensure_data_dirs()
    init_db()
    logger.info("%s started (env=%s)", settings.APP_NAME, settings.APP_ENV)
    yield


app = FastAPI(
    title="DefenceVision API",
    description="AI-powered geospatial infrastructure change assessment platform "
                "(research/academic prototype).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/health",
    }


app.include_router(health.router)
app.include_router(analyses.router)
app.include_router(detections.router)
app.include_router(evidence.router)
app.include_router(evaluation.router)
app.include_router(dashboard.router)
