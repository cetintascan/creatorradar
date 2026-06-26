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

**`youtube_ingest.py`** — runs daily at 02:00 UTC
```
fetch_channels → fetch_videos → fetch_discovery → upload_to_gcs → load_to_bq
```

**`transform.py`** — triggered on success of `youtube_ingest`
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
dbt/
├── dbt_project.yml
├── profiles.yml          ← BigQuery connection
├── models/
│   ├── staging/
│   │   ├── stg_youtube_videos.sql
│   │   └── stg_youtube_channels.sql
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
    ├── assert_demand_score_range.sql
    └── assert_no_null_topics.sql
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

**`mart_category_demand_daily`** — one row per topic per day. Aggregates video count, view volume, sponsor density, commerce intent density into a `demand_score`.

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

**Endpoints:**

`GET /api/creators` — `commercial_fit_score` ranked list, optional `?category=` filter

`GET /api/creators/{channel_id}` — full creator signal detail

`GET /api/categories` — yesterday's demand_score by topic

`GET /api/categories/trending` — 7-day delta, ordered by `demand_delta_pct`

`GET /api/categories/{topic}/creators` — top creators for a specific category

## Frontend

React + Recharts. Three pages:

**Creator leaderboard** — sortable table by `commercial_fit_score`. Filter by category. Click through to creator detail.

**Category trends** — bar chart of `demand_score` by topic. Toggle to 7-day delta view. Recharts `BarChart` with `XAxis`, `YAxis`, `Tooltip`.

**Creator detail** — single creator view. Video history, signal breakdown, brand mention timeline.

## GCP free tier compliance

| Resource | Monthly usage | Free limit | Status |
|---|---|---|---|
| GCS storage | ~300-750 MB | 5 GB (US regions) | Safe |
| GCS operations | ~3,000/month | 5,000/month | Safe |
| BQ storage | ~50-100 MB | 10 GB | Safe |
| BQ query processing | ~5-10 GB | 1 TB | Safe |
| BQ batch load | Free | Free | Safe |

GCS bucket must be in `us-central1`, `us-east1`, or `us-west1` for Always Free to apply.
