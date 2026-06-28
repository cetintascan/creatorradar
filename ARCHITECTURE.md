# CreatorRadar — Technical Architecture

## Stack

```
YouTube Data API v3
        ↓
Apache Airflow (Docker — Local)
        ↓
Google Cloud Storage (raw JSON lake)
        ↓
BigQuery (raw tables)
        ↓
dbt-bigquery (staging → intermediate → marts)
        ↓
FastAPI (REST API)
        ↓
React + Recharts (frontend)
```

## Infrastructure

**Orchestration:** Apache Airflow running in Docker via docker-compose. Custom image includes dbt-bigquery. LocalExecutor — no Celery, no Redis. PostgreSQL container handles Airflow metadata only.

**Raw storage:** Google Cloud Storage, append-only. One JSON file per batch per day. Path format: `gs://creatorradar-raw/youtube/{category}/YYYY-MM-DD/{filename}.json`. Retention: indefinite (source of truth for reprocessing).

**Warehouse:** BigQuery. Dataset: `creatorradar`. All dbt models land here. Partitioned by date where applicable.

**GCS region:** us-central1 (required for Always Free tier).

## Airflow DAGs

Two DAGs, separated by responsibility:

**`youtube_ingest.py`** — runs daily at 06:00 UTC (09:00 Turkey). `catchup=True`, `max_active_runs=1` — runs on startup if missed.
```
fetch_channels → fetch_videos → fetch_discovery → upload_to_gcs → load_to_bq
```

**`transform.py`** — runs daily at 08:00 UTC (11:00 Turkey). `catchup=True`, `max_active_runs=1`. ExternalTaskSensor waits for `youtube_ingest` success (`execution_delta=2h`).
```
dbt_run_staging → dbt_test_staging → dbt_run_intermediate → dbt_run_marts → dbt_test_marts
```

Separation allows ingestion failures to be debugged without re-running transforms, and transform failures to be fixed and re-triggered without re-fetching data.

## Ingestion layer

### `ingestion/youtube_client.py`
Wraps YouTube Data API v3. Three endpoints used:
- `channels.list` — channel metadata and statistics
- `videos.list` — video metadata and statistics
- `search.list` — keyword-based video discovery (used sparingly, 100 units/call)

Quota management: daily 10,000 unit budget. `search.list` calls are batched and limited per run. `videos.list` is 1 unit per 50-video batch.

### `ingestion/gcs_uploader.py`
Writes JSON to GCS. Append-only. Never overwrites existing files.

### `ingestion/bq_loader.py`
Loads GCS JSON to BigQuery raw tables using batch load jobs (free, no streaming inserts). Schema autodetect on first load, explicit schema on subsequent loads.

### Raw tables in BigQuery

| Table | Source | Partition |
|---|---|---|
| `raw_youtube_channels` | channels.list | ingested_date |
| `raw_youtube_videos` | videos.list | ingested_date |
| `raw_youtube_search` | search.list | ingested_date |

## dbt layer

### Directory structure
```
dbt_project/
├── dbt_project.yml
├── profiles.yml          ← BigQuery connection
├── models/
│   ├── staging/
│   │   ├── stg_youtube_videos.sql
│   │   ├── stg_youtube_channels.sql
│   │   └── stg_youtube_search.sql
│   ├── intermediate/
│   │   ├── int_yt_channel_baseline.sql
│   │   └── int_yt_content_signals.sql
│   └── marts/
│       ├── mart_creator_profiles.sql
│       ├── mart_category_demand_daily.sql
│       ├── mart_category_trending.sql
│       └── mart_brand_mentions.sql
├── macros/
│   ├── detect_sponsor_signal.sql
│   ├── detect_commerce_intent.sql
│   └── normalize_score.sql
└── tests/
    └── assert_commercial_fit_score_range.sql
```

### Model descriptions

**Staging** — type casting, deduplication, null handling. One staging model per raw table. No business logic.

**`int_yt_channel_baseline`** — 30-day rolling median views per channel. Used to compute `relative_performance_score = video_views / channel_median_views`.

**`int_yt_content_signals`** — per-video aggregation of engagement rate, sponsor signal, commerce intent signal, and brand mentions. Joins staging video data with channel baseline.

**`mart_creator_profiles`** — creator-level aggregation. One row per channel. Output includes `commercial_fit_score`:
```
commercial_fit_score =
  0.40 * normalized_relative_performance
+ 0.30 * normalized_engagement_rate
+ 0.20 * normalized_commerce_intent
+ 0.10 * normalized_sponsor_signal
```

**`mart_category_demand_daily`** — one row per topic per day. LEFT JOIN between `stg_youtube_search` and `int_yt_content_signals` on video_id. `demand_score = ln(1 + video_count) * (1 + commerce_intent_density) * (1 + sponsor_density)`. Uses `video_count` (not `sum(view_count)`) because keyword search results are mostly from non-watchlist channels with no view data.

**`mart_category_trending`** — 7-day delta. Compares current week demand_score to prior week. Output: `demand_delta_pct` used for trending UI.

**`mart_brand_mentions`** — brand visibility across creator content. Detected via `detect_commerce_intent` macro extended with `tracking_config.yaml` brand list.

### Key macros

**`detect_sponsor_signal(col)`** — returns boolean. Checks title and description for Turkish sponsor keywords: `iş birliği`, `işbirliği`, `reklam`, `sponsor`, `affiliate`, `indirim kodu`, `kodum`, `trendyol link`, `gratis link`, `watsons link`.

**`detect_commerce_intent(col)`** — returns boolean. Checks for purchase-oriented language: `nereden aldım`, `fiyatı`, `link`, `indirim`, `alınır mı`, `muadil`, `gratis`, `watsons`, `trendyol`, `sephora`.

**`normalize_score(col, partition_col)`** — min-max normalization within a partition (typically topic/category). Ensures scores are comparable across categories of different sizes.

## Config files

**`data/tracking_config.yaml`** — single source of truth for tracked topics, categories, and brand keywords. Used by ingestion (which keywords to search), dbt macros (which brands to detect), and frontend (which categories to display).

**`.env`** — `YOUTUBE_API_KEY`, `GCP_PROJECT_ID`, `GCS_BUCKET`, `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`.

## API layer

FastAPI connected to BigQuery via `google-cloud-bigquery`. All queries use parameterized inputs (`@param` syntax) to prevent injection.

**Location:** `api/` (project root package — `api/main.py`, `api/bq.py`, `api/routers/`)

**Start:** `GOOGLE_APPLICATION_CREDENTIALS=config/gcp-key.json .venv/bin/uvicorn api.main:app --port 8000 --reload`

**Endpoints:**

`GET /api/creators` — `commercial_fit_score` ranked list, optional `?category=` filter

`GET /api/creators/{channel_id}` — full creator signal detail + last 30 videos from `int_yt_content_signals`

`GET /api/categories` — latest demand_score by topic from `mart_category_demand_daily`

`GET /api/categories/trending` — 7-day delta, ordered by `demand_delta_pct`

`GET /api/categories/{topic}/creators` — creators matched via `stg_youtube_search.channel_id`

`GET /api/brands` — brand mention totals from `mart_brand_mentions`

## Frontend

React + Recharts. Three pages.

**Location:** `frontend/` (Vite + React)

**Start:** `cd frontend && npm run dev` — serves at `http://localhost:5173`. Vite proxies `/api/*` → `http://localhost:8000`.

**Creator leaderboard** (`/`) — table ranked by `commercial_fit_score` with score bar, sponsor/commerce signal dots. Category filter dropdown. Click row → creator detail.

**Category intelligence** (`/categories`) — Recharts `BarChart` of `demand_score` by topic. Toggle to 7-day delta view. Detail table below chart.

**Creator detail** (`/creators/:channelId`) — stat cards (fit score, subscribers, rates), video history table with sponsor/commerce badges.

## GCP free tier compliance

| Resource | Monthly usage | Free limit | Status |
|---|---|---|---|
| GCS storage | ~300-750 MB | 5 GB (US regions) | Safe |
| GCS operations | ~3,000/month | 5,000/month | Safe |
| BQ storage | ~50-100 MB | 10 GB | Safe |
| BQ query processing | ~5-10 GB | 1 TB | Safe |
| BQ batch load | Free | Free | Safe |

GCS bucket must be in `us-central1`, `us-east1`, or `us-west1` for Always Free to apply.
