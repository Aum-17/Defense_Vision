"""Generates the PDF assessment report with ReportLab.

The report is built entirely from real, stored analysis data — detections,
statistics, evidence crops and the model version actually used. It never
fabricates intelligence claims and includes explicit limitations.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..core.config import settings
from ..core.logging import get_logger
from ..models import Analysis, Detection

logger = get_logger(__name__)

DARK = colors.HexColor("#0f172a")
ACCENT = colors.HexColor("#3b82f6")
LIGHT = colors.HexColor("#e2e8f0")


def _styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "TitleX", parent=ss["Title"], fontSize=22, textColor=colors.white,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleX", parent=ss["Normal"], fontSize=10, textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER, spaceAfter=18,
        ),
        "h1": ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, textColor=DARK, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, textColor=DARK, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=ss["Normal"], fontSize=9.5, leading=13),
        "small": ParagraphStyle("Small", parent=ss["Normal"], fontSize=8, textColor=colors.HexColor("#475569")),
        "mono": ParagraphStyle("Mono", parent=ss["Code"], fontSize=8),
    }
    return styles


def _info_table(rows: list[tuple[str, str]], styles) -> Table:
    data = [[Paragraph(k, styles["small"]), Paragraph(v or "-", styles["body"])] for k, v in rows]
    t = Table(data, colWidths=[4.2 * cm, 11 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _severity_color(sev: str):
    return {
        "HIGH": colors.HexColor("#ef4444"),
        "MEDIUM": colors.HexColor("#f59e0b"),
        "LOW": colors.HexColor("#22c55e"),
        "NONE": colors.grey,
    }.get((sev or "NONE").upper(), colors.grey)


def _fmt_dt(d: dt.datetime | None) -> str:
    return d.strftime("%Y-%m-%d %H:%M") if d else ""


def generate_report(analysis: Analysis, detections: list[Detection], out_path: Path) -> Path:
    """Write a PDF report for an analysis and return its path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    s = _styles()

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    elems: list = []

    # --- Header ---
    header_data = [[Paragraph("DEFENCEVISION", s["title"]), Paragraph("RESEARCH / ACADEMIC PROTOTYPE", s["small"])]]
    header_tbl = Table(header_data, colWidths=[14 * cm, 1.2 * cm])
    header_tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    elems.append(header_tbl)
    elems.append(Paragraph("Geospatial Infrastructure Change Assessment", s["subtitle"]))
    elems.append(Spacer(1, 4 * mm))

    # --- 1. Analysis Information ---
    elems.append(Paragraph("1. Analysis Information", s["h1"]))
    north = 90 if (analysis.latitude or 0) >= 0 else -90
    east = 90 if (analysis.longitude or 0) >= 0 else -90
    coord = ""
    if analysis.latitude is not None and analysis.longitude is not None:
        coord = f"{abs(analysis.latitude):.5f}°{'N' if north == 90 else 'S'}, {abs(analysis.longitude):.5f}°{'E' if east == 90 else 'W'}"
    elems.append(
        _info_table(
            [
                ("Analysis ID", f"#{analysis.id}"),
                ("Analysis Name", analysis.name),
                ("Area", analysis.area),
                ("Latitude / Longitude", coord or "Not provided"),
                ("Analysis Date", _fmt_dt(analysis.analysis_date)),
                ("Analyst", analysis.analyst),
                ("Model Used", f"{analysis.model_version} ({'algorithmic' if analysis.model_version else 'unknown'})"),
                ("Processing Time", f"{analysis.processing_time:.2f}s" if analysis.processing_time else "-"),
                ("Registration Quality", f"{analysis.registration_quality:.2f}" if analysis.registration_quality is not None else "-"),
            ],
            s,
        )
    )

    # --- 2. Executive Summary ---
    elems.append(Paragraph("2. Executive Summary", s["h1"]))
    total = len(detections)
    high = sum(1 for d in detections if (d.severity or "").upper() == "HIGH")
    medium = sum(1 for d in detections if (d.severity or "").upper() == "MEDIUM")
    low = sum(1 for d in detections if (d.severity or "").upper() == "LOW")
    confirmed = sum(1 for d in detections if d.status == "CONFIRMED")
    avg_conf = round(sum(d.confidence for d in detections) / total, 3) if total else 0.0

    cats: dict[str, int] = {}
    for d in detections:
        cats[d.category or "Other Change"] = cats.get(d.category or "Other Change", 0) + 1
    cat_str = ", ".join(f"{k} ({v})" for k, v in cats.items()) or "None"

    summary_rows = [
        ("Detected Changes", str(total)),
        ("Categories", cat_str),
        ("Severity distribution", f"High: {high}, Medium: {medium}, Low: {low}"),
        ("Average confidence", f"{avg_conf:.3f} (algorithmic)"),
        ("Analyst verified", f"{confirmed} of {total} confirmed"),
    ]
    elems.append(_info_table(summary_rows, s))

    # --- 3. Methodology ---
    elems.append(Paragraph("3. Methodology", s["h1"]))
    elems.append(
        Paragraph(
            "Images were preprocessed (resolution normalisation, noise reduction, "
            "CLAHE contrast normalisation, colour normalisation), then registered using "
            "ORB feature detection with RANSAC homography estimation (identity-warp "
            "fallback when unreliable). Change detection used an aligned-image difference, "
            "Otsu thresholding, morphological filtering and connected-component analysis. "
            "Detected regions were categorised by heuristic geometry rules in broad "
            "infrastructure categories, and severity/confidence were computed from "
            "transparent algorithmic measures. ",
            s["body"],
        )
    )

    # --- 4. Change Findings ---
    elems.append(Paragraph("4. Change Findings", s["h1"]))
    for i, d in enumerate(detections):
        sev = (d.severity or "NONE").upper()
        elems.append(
            Paragraph(
                f"{d.change_id} — {d.category} &nbsp; "
                f'<font color="#ef4444">Severity: {sev}</font> &nbsp; '
                f"Confidence: {d.confidence * 100:.0f}% &nbsp; "
                f"Area: {d.area_pixels:,} px &nbsp; Status: {d.status}",
                s["h2"],
            )
        )
        ev = {}
        try:
            ev = json.loads(d.evidence_json or "{}")
        except Exception:
            ev = {}
        img_cols = []
        for label, key in (("Before", "before"), ("After", "after"), ("Difference", "difference"), ("Mask", "mask")):
            fs_path = ev.get(key + "_path", "")
            if not fs_path:
                continue
            fpath = Path(fs_path)
            if fpath.exists():
                try:
                    im = Image(str(fpath), width=5 * cm, height=4 * cm)
                    img_cols.append([Paragraph(label, s["small"]), im])
                except Exception:
                    pass
        if img_cols:
            table = Table(img_cols, colWidths=[2.5 * cm, 5.5 * cm])
            table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            elems.append(table)
        elems.append(Spacer(1, 3 * mm))

    # --- 5. Spatial Summary ---
    elems.append(Paragraph("5. Spatial Summary", s["h1"]))
    if analysis.latitude is not None and analysis.longitude is not None:
        geos = "\n".join(
            f"{d.change_id}: image centroid near ({d.centroid_json or '-'})" for d in detections
        )
        elems.append(Paragraph(f"Geographic reference: {coord}. Change regions are reported in image-relative coordinates; no geographic projection was applied.", s["body"]))
    else:
        elems.append(
            Paragraph(
                "No geospatial coordinates were provided for this analysis. Change "
                "locations are reported in image-relative coordinates only and labelled "
                "as such. Geographic coordinates were not fabricated.",
                s["body"],
            )
        )

    # --- 6. Limitations ---
    elems.append(Paragraph("6. Limitations", s["h1"]))
    limitations = [
        "This is a research/academic prototype, not operational military software.",
        "Analysis relies on available (potentially public/low-resolution) imagery; "
        "fine detail may be lost.",
        "Registration errors can produce false positives/negatives.",
        "Illumination, weather and seasonal difference can resemble ground change.",
        "The baseline change detector is algorithmic; it does not infer real-world "
        "causes. Terms are presented as 'potential' findings, not confirmed activity.",
        "Every detection requires human analyst verification before any conclusion.",
    ]
    for li in limitations:
        elems.append(Paragraph(f"• {li}", s["body"]))
    elems.append(Paragraph(
        "Confidence values are algorithmic measures of visual signal strength, not "
        "probabilities from a trained network. No targeting or personnel analysis is "
        "performed or intended.", s["small"],
    ))

    # --- 7. Conclusion ---
    elems.append(Paragraph("7. Conclusion", s["h1"]))
    conclusion = (
        f"This assessment identified {total} visual change region(s) between the "
        f"provided before/after imagery. The findings are presented as evidence-based "
        f"visual observations requiring analyst verification. No independent "
        f"intelligence claim is made; all conclusions must be confirmed by a human analyst."
    )
    elems.append(Paragraph(conclusion, s["body"]))

    elems.append(Spacer(1, 8 * mm))
    elems.append(Paragraph(f"Generated {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC", s["small"]))

    doc.build(elems)
    logger.info("Report generated -> %s", out_path)
    return out_path
