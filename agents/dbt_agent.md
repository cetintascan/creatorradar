# dbt Agent Log

## Session: Phase 4 — Commercial Signal Layer (2026-06-27)

### Completed

**Macros** (`dbt_project/macros/`):
- `detect_sponsor_signal.sql` — Turkish sponsor keywords (`iş birliği`, `reklam`, `sponsor`, `affiliate`, `indirim kodu`, `kodum`, `trendyol link`, `gratis link`, `watsons link`, `işbirliği`)
- `detect_commerce_intent.sql` — Turkish commerce intent (`nereden aldım`, `fiyatı`, `link`, `indirim`, `alınır mı`, `muadil`, `gratis`, `watsons`, `trendyol`, `sephora`)
- `normalize_score.sql` — min-max normalization via BigQuery window functions (`safe_divide`); pass `1` as partition_col for global normalization

**Intermediate** (`models/intermediate/`):
- `int_yt_channel_baseline.sql` — 30-day median views per channel (`APPROX_QUANTILES`). Filters to latest `ingested_date` and videos with `published_at >= now - 30d`.
- `int_yt_content_signals.sql` — per-video signals at latest ingested snapshot: `engagement_rate`, `has_sponsor_signal`, `has_commerce_intent`, `relative_performance` (video views / channel median). Left-joins channel_baseline.

**Mart** (`models/marts/`):
- `mart_creator_profiles.sql` — one row per channel. `commercial_fit_score = 0.40*norm_rel_perf + 0.30*norm_engagement + 0.20*norm_commerce + 0.10*norm_sponsor`. All normalization is global (partition by 1).

**Tests**:
- `tests/assert_commercial_fit_score_range.sql` — custom test, returns rows where `commercial_fit_score` is outside [0, 1]
- `models/intermediate/schema.yml` — `not_null`, `unique`, `accepted_values` on signal booleans
- `models/marts/schema.yml` — `not_null`, `unique` on `channel_id`; `not_null` on `commercial_fit_score`

### Verified
- `dbt parse --no-partial-parse` — clean, no warnings. Commit: `b60aa5e`.
- **Not yet run against BigQuery** — requires live data in `raw_youtube_videos` / `raw_youtube_channels`.

### Run command
```
cd /opt/airflow/dbt_project && dbt run --profiles-dir . --select intermediate marts
dbt test --profiles-dir . --select intermediate marts
```

### Pending (Phase 5)
- `mart_category_demand_daily.sql` — daily demand score per topic
- `mart_category_trending.sql` — 7-day delta (`demand_delta_pct`)
- `mart_brand_mentions.sql` — brand visibility from `tracking_config.yaml` brand list
- End-to-end pipeline test (ingestion → staging → intermediate → marts)
