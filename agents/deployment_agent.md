# Deployment Agent Log

## Agent Scope

Handles: GCP infrastructure setup, Airflow Docker build/startup, environment variable validation, docker compose operations.

---

## Infrastructure State

| Component | Status | Notes |
|---|---|---|
| GCP Project | ✅ Done | `creatorradar-tr` |
| Billing Account | ✅ Done | `01B85D-22AD3C-A5264E` linked |
| BigQuery Dataset | ✅ Done | `creatorradar-tr:creatorradar`, region `us-central1` |
| GCS Bucket | ✅ Done | `gs://creatorradar-raw`, region `us-central1` |
| Service Account | ✅ Done | `creatorradar-sa@creatorradar-tr.iam.gserviceaccount.com` |
| Service Account Key | ✅ Done | `config/gcp-key.json` (gitignored) |
| `.env` GCP vars | ✅ Done | `GCP_PROJECT_ID`, `GCS_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS` set |
| Docker image | ✅ Done | Airflow 2.9.2 + dbt-bigquery 1.8.2 + google-cloud libs |
| docker-compose.yml | ✅ Done | Airflow webserver + scheduler + PostgreSQL |
| Airflow UI | ✅ Done | localhost:8080 (admin/admin) |

---

## Session Log

### 2026-06-27 — Session 1: GCP Setup Start

**Action:** Deployment Agent activated. Beginning Phase 1 infrastructure setup.

**Current state:** Repo initialized. `ingestion/`, `dbt_project/`, `config/` directories exist. No GCP resources created yet. `docker-compose.yml` is empty. `.env.example` lacks GCP variables.

**Next step:** Step 1 — Create GCP project and enable required APIs.

---

## GCP Setup Checklist

### Step 1 — GCP Project
- [ ] Create GCP project named `creatorradar` (or similar)
- [ ] Note `GCP_PROJECT_ID`
- [ ] Link billing account

### Step 2 — Enable APIs
- [x] `bigquery.googleapis.com`
- [x] `storage.googleapis.com`
- [x] `iam.googleapis.com`

### Step 3 — BigQuery
- [x] Create dataset: `creatorradar` in region `us-central1`

### Step 4 — GCS
- [x] Create bucket: `creatorradar-raw` in region `us-central1`

### Step 5 — Service Account
- [x] Create service account: `creatorradar-sa`
- [x] Grant roles: `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`, `roles/storage.objectAdmin`, `roles/storage.legacyBucketReader` (bucket-level)
- [x] Create and download JSON key at `config/gcp-key.json` (gitignored)

### Step 6 — Environment Variables
- [x] Add to `.env`: `GCP_PROJECT_ID`, `GCS_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS`
- [x] Update `.env.example` with placeholders

### Step 7 — Docker / Airflow
- [x] Write `Dockerfile` (custom Airflow image with dbt-bigquery)
- [x] Write `docker-compose.yml` (Airflow + PostgreSQL)
- [x] Airflow UI live at localhost:8080 (admin/admin)

### Step 8 — Ingestion (Phase 2)
- [x] `ingestion/gcs_uploader.py`
- [x] `ingestion/bq_loader.py`
- [x] `ingestion/discover_videos.py`
- [x] Manual test: 144 search + 5 channels + 250 videos loaded to BQ (2026-06-26)

### Step 9 — API & Frontend (Phase 6)
- [x] `api/` FastAPI package (see below)
- [x] `frontend/` Vite + React app
- [x] `requirements.txt` updated with `fastapi`, `uvicorn[standard]`

---

## Phase 6 — FastAPI + React (2026-06-27)

### API service

**Location:** `api/` (project root Python package)

**Start command (local):**
```bash
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-key.json \
  .venv/bin/uvicorn api.main:app --port 8000 --reload
```

Reads `GOOGLE_APPLICATION_CREDENTIALS` from `.env` via `python-dotenv` (loaded in `api/main.py`). Ensure `.env` has the key path relative to the project root: `GOOGLE_APPLICATION_CREDENTIALS=config/gcp-key.json`.

**Endpoints:**
| Endpoint | Source table |
|---|---|
| `GET /api/creators` | `mart_creator_profiles` |
| `GET /api/creators?category=X` | `mart_creator_profiles` + `stg_youtube_search` |
| `GET /api/creators/{id}` | `mart_creator_profiles` + `int_yt_content_signals` |
| `GET /api/categories` | `mart_category_demand_daily` |
| `GET /api/categories/trending` | `mart_category_trending` |
| `GET /api/categories/{topic}/creators` | `mart_creator_profiles` + `stg_youtube_search` |
| `GET /api/brands` | `mart_brand_mentions` |

All queries use BigQuery parameterized inputs (`@param`).

### Frontend service

**Location:** `frontend/` (Vite + React)

**Start command:**
```bash
cd frontend && npm run dev   # serves at http://localhost:5173
```

Vite proxies `/api/*` → `http://localhost:8000` — no CORS issues in dev.

**Pages:** Creator Leaderboard (`/`), Category Intelligence (`/categories`), Creator Detail (`/creators/:channelId`)

### Infrastructure state
The API is a local service — not containerized. No Docker changes needed. If containerizing in the future, add a `uvicorn` service to `docker-compose.yml` with the same volume/env config as airflow-common.
