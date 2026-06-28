# dbt Agent Log

## Session: Pipeline Debug & First Successful Airflow Run (2026-06-28)

### Completed

**`transform` DAG fix — ExternalTaskSensor `execution_delta`:**
- Sorun: `ExternalTaskSensor` varsayılan olarak aynı `execution_date`'e sahip bir `youtube_ingest` run'ı arıyordu — execution_date'ler hiçbir zaman eşleşmiyordu.
- Fix: `execution_delta=timedelta(hours=2)` eklendi. Sensor artık 2 saat önceki ingest run'ını arıyor. Commit: `2de89bc`.

**Schedule güncellendi (2026-06-28):** `schedule="0 8 * * *"` (08:00 UTC = 11:00 Turkey). `catchup=True`, `max_active_runs=1`, `start_date=2026-06-29`. `execution_delta=timedelta(hours=2)` korundu (ingest 06:00, transform 08:00). Commit: `e4f5eef`.

**İlk başarılı end-to-end Airflow pipeline (2026-06-28):**
- `wait_for_ingest` → `dbt_run_staging` → `dbt_test_staging` → `dbt_run_intermediate` → `dbt_run_marts` → `dbt_test_marts` — 6/6 success.
- Bu run için sensor `execution_delta` fix'i öncesinde tetiklendi, manuel olarak `mark-success` ile geçirildi.

**Not:** `transform` DAG de pause'luydu ama bu session'da unpaused. Scheduled run'larda artık `execution_delta` ile doğru çalışacak.

---

## Session: Phase 6 — Bug Fix & Pipeline Test (2026-06-27)

### Completed

**Test fixes:**
- Removed `unique` tests on `stg_youtube_channels.channel_id` and `stg_youtube_videos.video_id` — staging keeps all ingested_dates, so channel/video ID is not globally unique. Correct key is (id, ingested_date).
- Removed `accepted_values` tests on BOOL columns `has_sponsor_signal` / `has_commerce_intent` — BigQuery cannot compare `BOOL IN ('True', 'False')`. `not_null` + BOOL type is sufficient.
- Result: **32/32 dbt tests pass**.

**`mart_category_demand_daily` fix:**
- Changed INNER JOIN → LEFT JOIN between `stg_youtube_search` and `int_yt_content_signals`. The INNER JOIN produced only 1 row (only 1 watchlist video appeared in keyword search results). With LEFT JOIN, all 17 keyword topics produce rows.
- `demand_score` formula changed from `ln(1 + sum(view_count)) * ...` to `ln(1 + count(distinct video_id)) * ...` — view counts are only available for watchlist-channel videos; video_count is a better proxy when most search results are from non-watchlist channels.
- `mart_category_trending` rebuilt automatically (reads from demand_daily). Now has 17 rows.

**`.gitignore`:** Added `dbt_project/target/` and `frontend/node_modules/`.

### Current model state (all confirmed running against BigQuery)

| Model | Type | Rows | Notes |
|---|---|---|---|
| `stg_youtube_channels` | VIEW | 10 (2 dates × 5) | |
| `stg_youtube_videos` | VIEW | 500 (2 dates × 250) | |
| `stg_youtube_search` | VIEW | ~288 | deduped by (video_id, topic, ingested_date) |
| `int_yt_channel_baseline` | TABLE | 5 | 30-day median, latest date only |
| `int_yt_content_signals` | TABLE | 250 | latest ingested_date only |
| `mart_creator_profiles` | TABLE | 5 | one row per watchlist channel |
| `mart_category_demand_daily` | TABLE | 17 | all keyword topics, latest date |
| `mart_category_trending` | TABLE | 17 | 7-day delta; delta_pct NULL (need 14 days) |
| `mart_brand_mentions` | TABLE | ~20 | 20 brands × channels with mentions |

### Known limitation
`mart_category_demand_daily` join to watchlist channel signals is sparse — only 1 watchlist video matched keyword search results. This is expected with 5 channels. With more channels in `tracking_config.yaml`, coverage improves automatically.

---

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
