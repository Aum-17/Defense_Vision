"""Analysis management endpoints: CRUD, upload, processing, stats, report."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...database import get_db
from ...models import Analysis, Image, ModelRun
from ...schemas.analysis import AnalysisCreate, AnalysisOut, AnalysisUpdate, ImageOut
from ...schemas.detection import AnalysisStats, DetectionOut, DetectionStatistics
from ...schemas.report import ReportInfo
from ...services.analysis_service import process_analysis, run_processing_task
from ...services.storage import save_upload, UploadValidationError
from ...utils.times import utcnow
from ..deps import get_analysis_or_404

router = APIRouter(prefix="/api/analyses", tags=["analyses"])


def _to_out(analysis: Analysis, db: Session) -> AnalysisOut:
    out = AnalysisOut.model_validate(analysis)
    out.has_before = any(i.type == "before" for i in analysis.images)
    out.has_after = any(i.type == "after" for i in analysis.images)
    out.detection_count = len(analysis.detections)
    return out


@router.post("", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def create_analysis(payload: AnalysisCreate, db: Session = Depends(get_db)) -> AnalysisOut:
    analysis = Analysis(
        name=payload.name,
        area=payload.area,
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        analyst=payload.analyst,
        analysis_date=payload.analysis_date or utcnow(),
        status="PENDING",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _to_out(analysis, db)


@router.get("", response_model=list[AnalysisOut])
def list_analyses(db: Session = Depends(get_db)) -> list[AnalysisOut]:
    rows = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    return [_to_out(a, db) for a in rows]


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisOut:
    analysis = get_analysis_or_404(db, analysis_id)
    return _to_out(analysis, db)


@router.patch("/{analysis_id}", response_model=AnalysisOut)
def update_analysis(
    analysis_id: int, payload: AnalysisUpdate, db: Session = Depends(get_db)
) -> AnalysisOut:
    analysis = get_analysis_or_404(db, analysis_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(analysis, key, value)
    db.commit()
    db.refresh(analysis)
    return _to_out(analysis, db)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    from fastapi import Response

    analysis = get_analysis_or_404(db, analysis_id)
    db.delete(analysis)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{analysis_id}/upload", response_model=AnalysisOut)
async def upload_image(
    analysis_id: int,
    file: UploadFile = File(...),
    type: str = Query(..., pattern="^(before|after)$"),
    db: Session = Depends(get_db),
) -> AnalysisOut:
    analysis = get_analysis_or_404(db, analysis_id)
    try:
        path = await save_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    from ...services.storage import validate_image_file

    width, height = validate_image_file(path)
    # Remove any existing image of this type (replace).
    for img in list(analysis.images):
        if img.type == type:
            db.delete(img)
    image = Image(
        analysis_id=analysis.id,
        type=type,
        filename=path.name,
        path=str(path.resolve()),
        width=width,
        height=height,
    )
    db.add(image)
    analysis.status = "PENDING"
    db.commit()
    db.refresh(analysis)
    return _to_out(analysis, db)


@router.post("/{analysis_id}/process", response_model=AnalysisOut)
def process(
    analysis_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalysisOut:
    analysis = get_analysis_or_404(db, analysis_id)
    has_before = any(i.type == "before" for i in analysis.images)
    has_after = any(i.type == "after" for i in analysis.images)
    if not (has_before and has_after):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both before and after images must be uploaded before processing.",
        )
    analysis.status = "PROCESSING"
    analysis.error_message = None
    db.commit()
    db.refresh(analysis)
    analysis_id_capture = analysis.id
    # Background task uses its own session (the request session closes after).
    background.add_task(run_processing_task, analysis_id_capture)
    return _to_out(analysis, db)


@router.get("/{analysis_id}/detections", response_model=list[DetectionOut])
def get_detections(analysis_id: int, db: Session = Depends(get_db)) -> list:
    analysis = get_analysis_or_404(db, analysis_id)
    dets = sorted(analysis.detections, key=lambda d: d.id)
    return [DetectionOut.model_validate(d) for d in dets]


@router.get("/{analysis_id}/statistics", response_model=AnalysisStats)
def get_statistics(analysis_id: int, db: Session = Depends(get_db)) -> AnalysisStats:
    analysis = get_analysis_or_404(db, analysis_id)
    dets = analysis.detections
    stats = DetectionStatistics(
        total=len(dets),
        confirmed=sum(1 for d in dets if d.status == "CONFIRMED"),
        rejected=sum(1 for d in dets if d.status == "REJECTED"),
        needs_review=sum(1 for d in dets if d.status == "NEEDS_REVIEW"),
        pending_review=sum(1 for d in dets if d.status == "PENDING_REVIEW"),
        high=sum(1 for d in dets if (d.severity or "").upper() == "HIGH"),
        medium=sum(1 for d in dets if (d.severity or "").upper() == "MEDIUM"),
        low=sum(1 for d in dets if (d.severity or "").upper() == "LOW"),
        avg_confidence=round(sum(d.confidence for d in dets) / len(dets), 3) if dets else 0.0,
        categories=_category_counts(dets),
    )
    return AnalysisStats(
        analysis_id=analysis.id,
        status=analysis.status,
        total_images=len(analysis.images),
        image_height=analysis.image_height,
        image_width=analysis.image_width,
        registration_quality=analysis.registration_quality,
        processing_time=analysis.processing_time,
        detection_statistics=stats,
    )


def _category_counts(dets) -> dict:
    counts: dict[str, int] = {}
    for d in dets:
        counts[d.category or "Other Change"] = counts.get(d.category or "Other Change", 0) + 1
    return counts


@router.post("/{analysis_id}/report", response_model=ReportInfo)
def generate_report(
    analysis_id: int, db: Session = Depends(get_db)
) -> ReportInfo:
    analysis = get_analysis_or_404(db, analysis_id)
    if analysis.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must be completed before a report can be generated.",
        )
    from ...reports.pdf_report import generate_report as build_report

    out_dir = settings.output_path / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"analysis_{analysis.id}.pdf"
    dets = sorted(analysis.detections, key=lambda d: d.id)
    build_report(analysis, dets, out_path)
    from ...utils.times import utcnow

    return ReportInfo(
        analysis_id=analysis.id,
        filename=out_path.name,
        url=f"/api/analyses/{analysis.id}/report",
        generated_at=utcnow().isoformat(),
    )


@router.get("/{analysis_id}/report")
def download_report(analysis_id: int, db: Session = Depends(get_db)):
    analysis = get_analysis_or_404(db, analysis_id)
    out_dir = settings.output_path / "reports"
    out_path = out_dir / f"analysis_{analysis.id}.pdf"
    if not out_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not generated yet.")
    from fastapi.responses import FileResponse

    return FileResponse(str(out_path), media_type="application/pdf", filename=f"DefenceVision_{analysis.name}.pdf")


@router.get("/{analysis_id}/image/{image_type}")
def get_image(analysis_id: int, image_type: str, db: Session = Depends(get_db)):
    """Serve the original uploaded image for a given type (before/after)."""
    from fastapi.responses import FileResponse

    if image_type not in ("before", "after"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="image_type must be before or after")
    analysis = get_analysis_or_404(db, analysis_id)
    target = next((i for i in analysis.images if i.type == image_type), None)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No {image_type} image uploaded")
    path = Path(target.path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file missing")
    media = "image/png" if path.suffix.lower() in (".png",) else "image/jpeg"
    return FileResponse(str(path), media_type=media)


@router.get("/{analysis_id}/mask")
def get_mask(analysis_id: int, db: Session = Depends(get_db)):
    """Serve the full change-mask PNG for overlay mode."""
    from fastapi.responses import FileResponse

    analysis = get_analysis_or_404(db, analysis_id)
    path = settings.output_path / f"analysis_{analysis.id}_mask.png"
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mask not available")
    return FileResponse(str(path), media_type="image/png")
