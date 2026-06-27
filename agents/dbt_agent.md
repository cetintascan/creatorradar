# dbt Agent Log

## Session: Phase 5 — Category Intelligence Layer (2026-06-27)

### Completed

**Staging** (`models/staging/`):
- `stg_youtube_search.sql` — `_keyword` → `topic`, `id.videoId` → `video_id`. Dedup by (video_id, topic, ingested_date). `ingested_date` cast to DATE explicitly.

**Marts** (`models/marts/`):
- `mart_category_demand_daily.sql` — join `stg_youtube_search` × `int_yt_content_signals` on video_id. One row per (topic, ingested_date). `demand_score = ln(1+total_views) * (1+commerce_intent_density) * (1+sponsor_density)`.
- `mart_category_trending.sql` — current 7-day vs prior 7-day demand_score. `demand_delta_pct` = % change. Anchors to `max(ingested_date)` in data.
- `mart_brand_mentions.sql` — UNNEST(20 brands) × CROSS JOIN content, lowercased LIKE match. One row per (brand_name, channel_id). Commit: `b726bbf`.

**DAG** (`dags/`):
- `transform.py` — `schedule="0 4 * * *"` (04:00 UTC daily). ExternalTaskSensor ile `youtube_ingest` başarısını bekler, sonra dbt_run_staging → dbt_test_staging → dbt_run_intermediate → dbt_run_marts → dbt_test_marts çalışır. Externally triggered değil — kendi schedule'ında çalışır.

### Design note
`mart_category_demand_daily` uses latest video stats from `int_yt_content_signals` joined to historical search dates. Demand scores reflect current performance of videos surfaced each day — acceptable MVP trade-off.

### Verified
- `dbt parse --no-partial-parse` — clean, no warnings. Commit: `b726bbf`.
- **Not yet run against BigQuery** — requires `youtube_ingest` DAG and live data.

### Run command (full pipeline)
```
cd /opt/airflow/dbt_project
dbt run --profiles-dir . --select staging intermediate marts
dbt test --profiles-dir . --select staging intermediate marts
```

### Pending (Phase 6)
- FastAPI backend (`api/`) reading from mart tables
- `dags/youtube_ingest.py` — daily ingestion DAG (Ingestion Agent scope)
- End-to-end test with real BigQuery data once `youtube_ingest` DAG is live

---

## Session: Phase 4 — Commercial Signal Layer (2026-06-27)

### Completed

**Macros** (`dbt_project/macros/`):
- `detect_sponsor_signal.sql` — Turkish sponsor keywords
- `detect_commerce_intent.sql` — Turkish commerce intent keywords
- `normalize_score.sql` — min-max normalization; pass `1` for global normalization

**Intermediate** (`models/intermediate/`):
- `int_yt_channel_baseline.sql` — 30-day median views per channel
- `int_yt_content_signals.sql` — per-video engagement, sponsor, commerce, relative performance. Bug fix: `coalesce(like_count, 0)` for NULL safety.

**Mart** (`models/marts/`):
- `mart_creator_profiles.sql` — `commercial_fit_score = 0.40*norm_rel_perf + 0.30*norm_engagement + 0.20*norm_commerce + 0.10*norm_sponsor`

**Tests**:
- `tests/assert_commercial_fit_score_range.sql`
