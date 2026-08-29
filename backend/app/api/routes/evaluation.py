"""Model evaluation + experiment comparison + demo endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...cv.evaluation import comparison_table, EvaluationResult
from ...database import get_db
from ...models import Analysis, Image
from ...schemas.analysis import AnalysisOut
from ...services.analysis_service import run_processing_task

router = APIRouter(tags=["evaluation", "demo"])


@router.get("/api/evaluation/compare")
def evaluate_compare() -> list[dict]:
    return comparison_table()


@router.get("/api/evaluation/baseline", response_model=dict)
def evaluate_baseline() -> dict:
    from ...services.evaluation_runner import run_baseline_evaluation

    try:
        result = run_baseline_evaluation()
    except Exception as exc:  # noqa: BLE001
        result = EvaluationResult(method="Classical Change Detection", evaluated=False, note=str(exc))
    return result.as_dict()


@router.post("/api/demo/load", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def load_demo(db: Session = Depends(get_db)) -> AnalysisOut:
    """Create a demo analysis from synthetic public demonstration data."""
    from ...core.config import settings
    from ...services.demo import save_demo_pair
    from ...utils.times import utcnow

    demo_dir = settings.demo_path
    before_p, after_p, _, meta = save_demo_pair(demo_dir)

    analysis = Analysis(
        name="Synthetic Demo Analysis",
        area="Synthetic Demonstration Area",
        description="PUBLIC / SYNTHETIC DEMONSTRATION DATA. "
                    f"{meta.get('label', '')} — not real imagery.",
        analyst="System (Demo)",
        analysis_date=utcnow(),
        latitude=None,
        longitude=None,
        status="PENDING",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    from ...services.storage import validate_image_file

    w_b, h_b = validate_image_file(before_p)
    w_a, h_a = validate_image_file(after_p)

    db.add(Image(analysis_id=analysis.id, type="before", filename=before_p.name, path=str(before_p.resolve()), width=w_b, height=h_b))
    db.add(Image(analysis_id=analysis.id, type="after", filename=after_p.name, path=str(after_p.resolve()), width=w_a, height=h_a))
    db.commit()
    db.refresh(analysis)

    # Trigger processing in the background.
    run_processing_task(analysis.id)

    out = AnalysisOut.model_validate(analysis)
    out.has_before = True
    out.has_after = True
    return out
