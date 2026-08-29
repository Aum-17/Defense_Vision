"""Detection detail + analyst review endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models import AnalystReview, Detection
from ...schemas.detection import DetectionOut
from ...schemas.review import ReviewCreate, ReviewOut
from ...utils.times import utcnow
from ..deps import get_db

router = APIRouter(prefix="/api/detections", tags=["detections"])


def _get_det(db: Session, det_id: int) -> Detection:
    det = db.get(Detection, det_id)
    if det is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detection not found")
    return det


@router.get("/{detection_id}", response_model=DetectionOut)
def get_detection(detection_id: int, db: Session = Depends(get_db)) -> DetectionOut:
    return DetectionOut.model_validate(_get_det(db, detection_id))


@router.get("/{detection_id}/reviews", response_model=list[ReviewOut])
def get_reviews(detection_id: int, db: Session = Depends(get_db)) -> list[ReviewOut]:
    det = _get_det(db, detection_id)
    return [ReviewOut.model_validate(r) for r in det.reviews]


@router.post("/{detection_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def review_detection(
    detection_id: int, payload: ReviewCreate, db: Session = Depends(get_db)
) -> ReviewOut:
    det = _get_det(db, detection_id)

    review = AnalystReview(
        detection_id=det.id,
        decision=payload.decision,
        comment=payload.comment,
        analyst=payload.analyst,
        original_prediction=det.category,
        model_version=det.model_version,
        timestamp=utcnow(),
    )
    db.add(review)

    # Update detection status based on analyst decision.
    det.status = payload.decision  # CONFIRMED | REJECTED | NEEDS_REVIEW
    db.commit()
    db.refresh(review)
    return ReviewOut.model_validate(review)
