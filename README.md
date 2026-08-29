# DefenceVision

AI-assisted geospatial infrastructure change detection — a Docker-first, full-stack research/academic prototype. Upload before/after imagery, run a classical computer-vision change-detection pipeline behind a pluggable interface, and review, map, and report the results with **AI assisting the analyst** (no autonomous decisions).

> **Responsible-use notice:** This prototype is for research and synthetic/public demonstration data only. It does **not** implement weapon targeting, autonomous targeting, facial recognition, personnel tracking/identification, or offensive decision-making. Findings are labeled "potential" and confidence is labeled `algorithmic`. Demo imagery is labeled `PUBLIC / SYNTHETIC DEMONSTRATION DATA`.

---

## Feature overview

- **Upload** paired before/after imagery (JPG/PNG/TIFF, ≤ 25 MB each default).
- **Preprocess** (normalize resolution/noise, CLAHE, color correction), **register** (ORB + RANSAC with identity fallback + quality score), **detect changes** (classical diff + morphology), **segment** change regions, **classify** (rule-based), **score** confidence + severity (customizable thresholds).
- **Pluggable detector seam** — swap the classical baseline for a deep-learning model (Siamese, U-Net, ChangeFormer, BIT) later.
- **Human-in-the-loop review** — analyst confirms/dismisses findings; the review is persisted.
- **Geospatial map** (Leaflet) — `CRS.Simple` image coordinates, or real lat/lng when geo-referenced imagery is provided.
- **PDF report** — analysis info, executive summary, methodology, change findings with embedded evidence crops, spatial summary, limitations, neutral conclusion.
- **Evaluation** — synthetic ground-truth based metrics (honest, no fabricated numbers) and a model comparison table (baseline evaluated, DL models marked "Not evaluated").

## Architecture

```
┌───────────────────────┐         ┌───────────────────────────────┐
│   React + Vite + TS   │  HTTP   │         FastAPI backend        │
│   (nginx :3000)       │ ─────►  │          (:8000)              │
│  Dashboard / Analysis │  /api/* │  cv/pipeline ─ registrars     │
│  Viewer / Map / Report│         │   │ detectors ─ classifiers   │
└───────────────────────┘         │   │ regions   ─ severity      │
                                  │  services ─ storage/demo/report│
                                  │  reports/pdf_report.py        │
                                  └──────────────┬────────────────┘
                                                 │ SQLAlchemy
                                        ┌────────▼────────┐
                                        │  PostgreSQL      │
                                        │  + PostGIS :5432 │
                                        └─────────────────┘
```

- **backend/** — Python 3.11 + FastAPI + SQLAlchemy; OpenCV classical CV pipeline; ReportLab PDFs.
- **frontend/** — Vite + React + TypeScript + TailwindCSS + Recharts + Leaflet + lucide-react + react-dropzone.
- **db** — `postgis/postgis:16-3.4`.
- Filesystem outputs under `./data/` (binds to `/app/data` in the container): uploaded images, masks, evidence crops, PDFs.

---

## Prerequisites

- **Docker Desktop** with **Docker Compose v2** (tested on macOS arm64, Docker 29.x).
- No local Node or Python needed — everything runs in containers.
- On Apple Silicon, PostGIS runs under amd64 emulation (works but slower).

## Quick start

```bash
# 1. Configure environment (optional — defaults work out of the box)
cp .env.example .env

# 2. Build and start the full stack (Postgres + backend + frontend)
make up            # or: docker compose up -d --build

# 3. Verify health
docker compose ps                      # all three services "healthy"/"Up"
curl http://localhost:8000/api/health  # {"status":"ok","database":"postgresql"}

# 4. Open the app
open http://localhost:3000             # frontend
# API docs / Swagger UI:
open http://localhost:8000/docs
```

## Useful commands (Makefile)

| Command | Purpose |
|---|---|
| `make up` | Build + start the full stack |
| `make down` | Stop containers |
| `make logs` | Tail combined logs |
| `make backend-test` | Run the backend pytest suite (inside container) |
| `make demo` | Headless end-to-end demo through the API |
| `make clean` | Remove containers and **volumes** (resets the database) |

## Running a demo end-to-end

With the stack running:

```bash
# Option A — headless demo (creates a synthetic analysis, processes it, writes a PDF)
make demo            # or: docker compose exec backend python scripts/run_demo.py

# Option B — via UI at http://localhost:3000
#   1. New Analysis → name it (optionally add geo/notes)
#   2. Upload a before and an after image (or click "Load synthetic demo pair")
#   3. Process → review change list, evidence crops, map, confidence
#   4. Reports → Download PDF
```

## Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql://defence:defence@db:5432/defencevision` | PostGIS via Docker |
| `DATA_ROOT` | `./data` (host) / `/app/data` (container) | uploads, masks, evidence, PDFs |
| `MAX_UPLOAD_MB` | `25` | max per-image upload size |
| `ALLOWED_IMAGE_EXTENSIONS` | `.jpg,.jpeg,.png,.tif,.tiff` | accepted upload types |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | allowed browser origins |
| `POSTGRES_*` | `defence` / `defence` / `defencevision` | DB credentials |

**SQLite fallback:** swap `DATABASE_URL=sqlite:///./data/defencevision.db` if you want to run the backend without the Postgres service. (Tests always run against SQLite.)

## API surface

Interactive docs at `GET /docs`. Key endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | service + DB health |
| `POST` | `/api/analyses` | create an analysis |
| `POST` | `/api/analyses/{id}/upload` | upload before/after images |
| `POST` | `/api/analyses/{id}/process` | run the CV pipeline (async) |
| `GET` | `/api/analyses/{id}/detections` | list change findings |
| `GET` | `/api/analyses/{id}/statistics` | per-analysis stats |
| `POST`/`GET` | `/api/analyses/{id}/report` | generate / download PDF |
| `GET` | `/api/analyses/{id}/mask`, `/image/{type}` | visual overlays |
| `POST` | `/api/detections/{id}/review` | analyst HITL decision |
| `GET` | `/api/evidence/{det_id}/{filename}` | before/after/diff/mask crops |
| `GET` | `/api/evaluation/compare` | model comparison table |
| `POST` | `/api/demo/load` | load synthetic demo pair + ground truth |

## Evaluation

The classical baseline is evaluated on **synthetic ground truth** (honest metrics — no fabricated numbers). `GET /api/evaluation/compare` returns a comparison table across baseline + DL model slots (Siamese, U-Net, ChangeFormer, BIT); slots without an implementation are marked **"Not evaluated"** rather than showing fake scores.

## Integrating a deep-learning detector

The pipeline consumes detectors through a pluggable interface:

- Implement `BaseChangeDetector` (see `backend/app/cv/detection.py`), returning a mask of changed pixels.
- Register it in the `get_detector(model_name)` factory for the chosen model name.
- Optionally wire real dataset ground-truth (see below) into `backend/app/services/evaluation.py` for metrics.

## Datasets

The architecture supports standard change-detection / remote-sensing datasets for future training and evaluation:

- **LEVIR-CD** — building change detection pairs + masks.
- **xBD** (xView2) — pre/post-disaster building damage.
- **DOTA** — multi-class aerial object detection.
- **xView** — overhead object detection (large, multi-class).
- **SpaceNet** — building/road footprints in satellite imagery.

No dataset downloads are bundled; add your own data pipelines over these to train/validate a model, then plug it into the detector seam above.

### Importing real xBD (xView2) pairs

A helper script stages real xBD `{disaster}_{tile}_pre_disaster.png` / `_post_disaster.png` pairs into `./data/imports/<tile>/` and runs them through the pipeline via the API:

```bash
# 1. Download the dataset (host machine — requires the kagglehub package)
pip install kagglehub
python -c "import kagglehub; print(kagglehub.dataset_download('qianlanzz/xbd-dataset'))"

# 2. Import N pairs into DefenceVision (stack must be up)
XBD=$(python -c "import kagglehub; print(kagglehub.dataset_download('qianlanzz/xbd-dataset'))")
docker compose exec backend python scripts/import_xbd.py "$XBD" --limit 1

# optional: limit to one disaster, or just stage without running the pipeline
docker compose exec backend python scripts/import_xbd.py "$XBD" --filter hurricane --limit 1
docker compose exec backend python scripts/import_xbd.py "$XBD" --stage-only
```

Notes:
- Each imported tile becomes its own analysis (New Analysis → upload before/after → process → review → report) and is visible at `http://localhost:3000/analyses`.
- Each pair is copied to `./data/imports/<tile>/pre.png|post.png` and, when present, the ground-truth damage mask to `gt.png` for future evaluation wiring.
- xBD tiles are 1024×1024 PNGs (well under the 25 MB upload limit). Two 1024×1024 tiles can take longer to process than the small demo images.
- Real imagery is kept under `./data/imports` so it is clearly distinct from the bundled synthetic demo data.

## Tests

```bash
make backend-test        # 26 tests: validation, CV pipeline, API workflow (incl. review + PDF)
```

Tests force a SQLite database and a scratch `DATA_ROOT`; they never touch the live Postgres or real uploads.

## Limitations

- Classical diff + morphology baseline: sensitive to illumination/registration noise (preprocessing mitigates but does not eliminate).
- Rule-based severity/classification are heuristic; DL labels are placeholders.
- PostGIS runs under emulation on Apple Silicon — slower than native amd64.
- No user auth/roles — single-analyst prototype scope.
- Frontend bundle exceeds the 500 kB Vite advisory warning (prototype only, non-blocking).

## Responsible use

AI assists the analyst; decisions remain human. Outputs are labeled as potential findings with `algorithmic` confidence, and all bundled imagery is public/synthetic demonstration data.
