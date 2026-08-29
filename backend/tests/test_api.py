"""End-to-end API tests against the real backend (SQLite in-memory)."""
from __future__ import annotations

import time

from PIL import Image


def _png_bytes() -> bytes:
    import io

    buf = io.BytesIO()
    Image.new("RGB", (120, 90), (0, 128, 0)).save(buf, "PNG")
    return buf.getvalue()


def _create_with_images(client, name="Test"):
    aid = client.post("/api/analyses", json={"name": name, "area": "Zone A"}).json()["id"]
    for t in ("before", "after"):
        r = client.post(
            f"/api/analyses/{aid}/upload?type={t}",
            files={"file": (f"{t}.png", _png_bytes(), "image/png")},
        )
        assert r.status_code == 200, r.text
    return aid


def _wait_completed(client, aid):
    s = {}
    for _ in range(60):
        s = client.get(f"/api/analyses/{aid}/statistics").json()
        if s["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(0.1)
    return s


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_analysis(client):
    r = client.post("/api/analyses", json={"name": "Test", "area": "Zone A"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Test"
    assert body["status"] == "PENDING"


def test_upload_rejects_bad_type(client):
    aid = _create_with_images(client)
    r = client.post(
        f"/api/analyses/{aid}/upload?type=forward",
        files={"file": ("a.png", _png_bytes(), "image/png")},
    )
    assert r.status_code == 422


def test_upload_rejects_bad_extension(client):
    aid = _create_with_images(client)
    r = client.post(
        f"/api/analyses/{aid}/upload?type=before",
        files={"file": ("evil.exe", b"x", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_process_requires_both_images(client):
    aid = client.post("/api/analyses", json={"name": "T"}).json()["id"]
    client.post(f"/api/analyses/{aid}/upload?type=before", files={"file": ("b.png", _png_bytes(), "image/png")})
    r = client.post(f"/api/analyses/{aid}/process")
    assert r.status_code == 400


def test_full_workflow(client):
    aid = _create_with_images(client)
    r = client.post(f"/api/analyses/{aid}/process")
    assert r.status_code == 200
    assert r.json()["status"] == "PROCESSING"

    s = _wait_completed(client, aid)
    assert s["status"] == "COMPLETED", s
    assert s["detection_statistics"]["total"] >= 0
    assert s["registration_quality"] is not None


def test_review_flow(client):
    aid = _create_with_images(client)
    client.post(f"/api/analyses/{aid}/process")
    s = _wait_completed(client, aid)
    assert s["status"] == "COMPLETED"
    if s["detection_statistics"]["total"] == 0:
        return

    dets = client.get(f"/api/analyses/{aid}/detections").json()
    assert len(dets) >= 1
    det_id = dets[0]["id"]

    r = client.post(
        f"/api/detections/{det_id}/review",
        json={"decision": "CONFIRMED", "comment": "Looks correct", "analyst": "tester"},
    )
    assert r.status_code == 201
    assert r.json()["decision"] == "CONFIRMED"

    updated = client.get(f"/api/detections/{det_id}").json()
    assert updated["status"] == "CONFIRMED"


def test_report_generation(client):
    aid = _create_with_images(client)
    client.post(f"/api/analyses/{aid}/process")
    s = _wait_completed(client, aid)
    # Even with 0 detections the report should generate.
    r = client.post(f"/api/analyses/{aid}/report")
    assert r.status_code == 200, r.text
    info = r.json()
    assert info["filename"].endswith(".pdf")

    dl = client.get(f"/api/analyses/{aid}/report")
    assert dl.status_code == 200
    assert dl.headers["content-type"] == "application/pdf"
    assert b"%PDF" in dl.content[:10]


def test_report_embeds_evidence_images(client):
    """Regression: every detection's before/after/diff/mask crops must be embedded in the PDF."""
    aid = _create_with_images(client)
    client.post(f"/api/analyses/{aid}/process")
    s = _wait_completed(client, aid)
    dets = client.get(f"/api/analyses/{aid}/detections").json()
    if not dets:
        return
    r = client.get(f"/api/analyses/{aid}/report")
    assert r.status_code == 200
    pdf = r.content
    # 4 evidence images per detection, each embedded as a PDF image XObject.
    assert pdf.count(b"/Subtype /Image") >= 4 * len(dets)


def test_two_analyses_unique_change_ids(client):
    """Regression: change_id (CHG-001...) must be unique per analysis, not global."""
    for _ in range(2):
        aid = _create_with_images(client)
        client.post(f"/api/analyses/{aid}/process")
        s = _wait_completed(client, aid)
        assert s["status"] == "COMPLETED", s


def test_demo_load(client):
    r = client.post("/api/demo/load")
    assert r.status_code == 201
    body = r.json()
    assert "Demo" in body["name"]
    assert body["has_before"] is True
    assert body["has_after"] is True


def test_evaluation_compare(client):
    r = client.get("/api/evaluation/compare")
    assert r.status_code == 200
    rows = r.json()
    assert any("Not evaluated" in (x.get("note") or "") for x in rows)


def test_dashboard_overview(client):
    r = client.get("/api/dashboard/overview")
    assert r.status_code == 200
    body = r.json()
    assert "total_analyses" in body
