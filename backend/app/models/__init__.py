"""SQLAlchemy ORM models for DefenceVision."""
from .analysis import Analysis  # noqa: F401
from .image import Image  # noqa: F401
from .detection import Detection  # noqa: F401
from .review import AnalystReview  # noqa: F401
from .model_run import ModelRun  # noqa: F401

ALL_MODELS = [Analysis, Image, Detection, AnalystReview, ModelRun]
