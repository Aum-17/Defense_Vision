"""Application configuration loaded from environment variables.

All credentials and environment-dependent values are read here so that
secrets are never hardcoded in Python source files.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "DefenceVision"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database. Defaults are Docker-friendly (PostGIS service named "db").
    DATABASE_URL: str = (
        "postgresql://defence:defence@db:5432/defencevision"
    )

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Uploads
    MAX_UPLOAD_MB: int = 25
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png,.tif,.tiff"

    # Data root (mounted volume in Docker)
    DATA_ROOT: str = "./data"

    # Model registry
    DEFAULT_MODEL: str = "classical_change_detector_v1.0"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_extensions(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",") if e.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_ROOT).resolve()

    @property
    def uploads_path(self) -> Path:
        return self.data_path / "uploads"

    @property
    def processed_path(self) -> Path:
        return self.data_path / "processed"

    @property
    def output_path(self) -> Path:
        return self.data_path / "output"

    @property
    def demo_path(self) -> Path:
        return self.data_path / "demo"

    @property
    def annotations_path(self) -> Path:
        return self.data_path / "annotations"

    @property
    def sql_enabled(self) -> bool:
        """Whether the target DB is SQLite (fallback mode)."""
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
