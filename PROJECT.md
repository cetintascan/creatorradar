# CreatorRadar — Project Brief

## What it is

CreatorRadar is a creator commerce intelligence platform for the Turkish beauty and personal care market. It collects and analyzes public YouTube data daily to help influencer marketing agencies identify the right creators, topics, and commercial signals for their clients' campaigns.

## Who it is for

**Primary: Influencer marketing agencies**

Agencies sit at the intersection of brands and creators. They already pay for tools like Modash and HypeAuditor, understand the value of data-driven decisions, and move faster than brands when evaluating new tools. Turkish agencies serve beauty and personal care brands who need creator discovery and campaign intelligence.

Other potential users (post-MVP): beauty brands, e-commerce and marketplace teams, retail marketing teams.

## The three questions it answers

**1. Which creators should I work with for this campaign?**
`commercial_fit_score` ranked creator list, filterable by category. Replaces gut-feel decisions with a scored, explainable ranking.

**2. Is this creator actually doing commercial content?**
`sponsor_signal` + `commerce_intent_signal` detection from video titles and descriptions. Agencies often discover too late that a creator with good numbers has never done a paid collaboration.

**3. Which categories are rising right now?**
`mart_category_trending` — 7-day momentum score. Lets agencies tell clients "this category is spiking, we should move now" with data behind it.

## What it is not

- Not a campaign management tool
- Not a social listening tool
- Not an Instagram analytics tool
- Not a generic YouTube dashboard

## MVP scope

- Platform: YouTube only
- Market: Turkey
- Vertical: Beauty and personal care
- Creator universe: Turkish beauty/personal care YouTubers
- Data source: YouTube Data API v3 (public data only)

## Why YouTube, not Instagram

YouTube beauty content carries stronger commercial signals. Long-form video means more text to analyze — titles, descriptions, pinned comments all contain sponsor signals, brand mentions, product links, and commerce keywords. Instagram caption analysis is thinner and less reliable. Turkish beauty creators are also highly active on YouTube.

## Architecture principle

The system starts with beauty/TR but is designed to expand. Adding a new vertical means updating `tracking_config.yaml`. Adding a new market means updating creator and keyword configs. The pipeline, warehouse, and scoring logic do not change.

## Business model (future)

SaaS subscription for agencies. Tiered by number of tracked categories, creator universe size, and API access. Not in scope for MVP — MVP validates the product with real agency users first.

---

## Implementation roadmap

### ✅ Phase 1 — Infrastructure
- GCP project, billing account, BigQuery dataset, GCS bucket
- Service account and credentials
- Custom Airflow Docker image (includes dbt-bigquery)
- docker-compose.yml with Airflow + PostgreSQL (Airflow metadata only)
- Airflow UI running at localhost:8080

### ✅ Phase 2 — Ingestion
- `ingestion/youtube_client.py` — channels, videos, search endpoints
- `ingestion/gcs_uploader.py` — raw JSON to GCS
- `ingestion/bq_loader.py` — GCS to BigQuery batch load
- Manual test: raw data visible in BigQuery
- `dags/youtube_ingest.py` — scheduled daily ingestion DAG (`schedule="0 2 * * *"`)

### ✅ Phase 3 — dbt staging
- `dbt init`, `profiles.yml` for BigQuery
- `stg_youtube_videos.sql`, `stg_youtube_channels.sql`, `stg_youtube_search.sql`
- dbt tests: not_null on all key fields
- `dags/transform.py` — `schedule="0 4 * * *"`, ExternalTaskSensor on `youtube_ingest`

### ✅ Phase 4 — Commercial signal layer
- `macros/detect_sponsor_signal.sql` — Turkish sponsor keywords
- `macros/detect_commerce_intent.sql` — Turkish commerce keywords
- `macros/normalize_score.sql` — min-max normalization per category
- `int_yt_channel_baseline.sql` — 30-day channel median views
- `int_yt_content_signals.sql` — per-video signal aggregation
- `mart_creator_profiles.sql` — `commercial_fit_score` per creator

### ✅ Phase 5 — Category intelligence
- `mart_category_demand_daily.sql` — daily demand score per category (LEFT JOIN, video_count based)
- `mart_category_trending.sql` — 7-day delta
- `mart_brand_mentions.sql` — brand visibility across creator content
- End-to-end pipeline test: 32/32 dbt tests pass

### ✅ Phase 6 — API and frontend
- `api/` FastAPI package: 7 endpoints connected to BigQuery
- `frontend/` Vite + React + Recharts
- Creator leaderboard, category intelligence, creator detail pages
- Run: `.venv/bin/uvicorn api.main:app --port 8000` + `cd frontend && npm run dev`
