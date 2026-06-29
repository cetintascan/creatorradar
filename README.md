# CreatorRadar

Creator commerce intelligence platform for the Turkish beauty and personal care market. Collects and analyzes public YouTube data daily to help influencer marketing agencies identify the right creators, topics, and commercial signals for their campaigns.

## What it does

- **Creator scoring** — ranks creators by `commercial_fit_score` combining engagement rate, relative performance, sponsor signal, and commerce intent
- **Sponsor & commerce signal detection** — identifies paid collaborations and purchase-intent content from Turkish-language video titles and descriptions
- **Category intelligence** — tracks daily demand scores and 7-day momentum across beauty/personal care topics
- **Brand visibility** — surfaces which creators mention tracked brands across their content

## Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.9 (Docker, LocalExecutor) |
| Raw storage | Google Cloud Storage (append-only NDJSON) |
| Warehouse | BigQuery |
| Transformation | dbt-bigquery (staging → intermediate → marts) |
| API | FastAPI + google-cloud-bigquery |
| Frontend | React + Recharts (Vite) |
| Data source | YouTube Data API v3 |

## Architecture

```
YouTube Data API v3
        ↓
Airflow DAG: youtube_ingest (daily, 09:00 TR)
        ↓
Google Cloud Storage  →  BigQuery raw tables
                                ↓
                    Airflow DAG: transform (daily, 11:00 TR)
                                ↓
                    dbt: staging → intermediate → marts
                                ↓
                    FastAPI (REST API)
                                ↓
                    React frontend
```

## dbt Model Layers

**Staging** — type casting, deduplication, null handling per raw table

**Intermediate**
- `int_yt_channel_baseline` — 30-day rolling median views per channel
- `int_yt_content_signals` — per-video engagement rate, sponsor signal, commerce intent, relative performance

**Marts**
- `mart_creator_profiles` — `commercial_fit_score` per creator
- `mart_category_demand_daily` — daily demand score per topic
- `mart_category_trending` — 7-day momentum delta
- `mart_brand_mentions` — brand visibility across creator content

## Scoring

```
commercial_fit_score =
  0.40 × normalized_relative_performance
+ 0.30 × normalized_engagement_rate
+ 0.20 × normalized_commerce_intent
+ 0.10 × normalized_sponsor_signal
```

Scores are min-max normalized within each category using a custom dbt macro.

## Signal Detection

Turkish-language keyword matching in video titles and descriptions:

**Sponsor signal** — `iş birliği`, `reklam`, `sponsor`, `affiliate`, `indirim kodu`, `kodum`, `trendyol link`, `gratis link`

**Commerce intent** — `nereden aldım`, `fiyatı`, `link`, `indirim`, `alınır mı`, `muadil`, `gratis`, `watsons`, `trendyol`, `sephora`

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/creators` | Creator leaderboard ranked by `commercial_fit_score` |
| `GET /api/creators?category={topic}` | Filtered by category |
| `GET /api/creators/{channel_id}` | Creator detail + last 30 videos |
| `GET /api/categories` | Demand scores by topic |
| `GET /api/categories/trending` | 7-day momentum ranking |
| `GET /api/categories/{topic}/creators` | Creators matched to a topic |
| `GET /api/brands` | Brand mention totals |

## Running Locally

**Prerequisites:** Docker, Python 3.11+, Node 18+, GCP service account with BigQuery and GCS access.

```bash
# Copy and fill environment variables
cp .env.example .env

# Start Airflow
docker compose up -d

# Airflow UI → localhost:8080

# Start API
GOOGLE_APPLICATION_CREDENTIALS=config/gcp-key.json \
  .venv/bin/uvicorn api.main:app --port 8000 --reload

# Start frontend
cd frontend && npm install && npm run dev
# → localhost:5173
```

## GCP Free Tier

Designed to run within GCP Always Free limits: GCS in `us-central1`, BigQuery batch loads (free), ~5-10 GB query processing/month against a 1 TB free quota.
