# Ingestion Agent Log

## Handoff from Deployment Session (2026-06-27)

Files written and tested:
- `ingestion/youtube_client.py` — YouTube API wrapper (search, channels, playlistItems, videos)
- `ingestion/gcs_uploader.py` — NDJSON upload, append-only
- `ingestion/bq_loader.py` — batch load to BQ, WRITE_APPEND
- `ingestion/discover_videos.py` — keyword search + creator watchlist orchestration

Config single source of truth: `data/tracking_config.yaml` (18 keywords, 5 handles, 20 brands)

Manual test 2026-06-26: 144 search + 5 channels + 250 videos → GCS → BQ raw tables ✅

**Completed (2026-06-27):** `dags/youtube_ingest.py` — `dag_id="youtube_ingest"`. `fetch_and_upload` → parallel `load_bq_search` + `load_bq_channels` + `load_bq_videos`. BQ load tasks skip silently if GCS file absent. Commit: `d9ba24e`.

**Schedule güncellendi (2026-06-28):** `schedule="0 6 * * *"` (06:00 UTC = 09:00 Turkey). `catchup=True`, `max_active_runs=1`, `start_date=2026-06-29`. Bilgisayar geç açılsa bile o günün run'ı startup'ta otomatik tetiklenir. Commit: `e4f5eef`.

## Handoff from dbt Phase 5 Session (2026-06-27)

`dags/transform.py` yazıldı — schedule: `"0 4 * * *"` (04:00 UTC), `ExternalTaskSensor` ile `youtube_ingest` DAG'ının başarısını bekliyor.

`youtube_ingest.py` yazılırken **`TriggerDagRunOperator` ekleme** — `transform.py` zaten kendi schedule'ında çalışıp sensor ile bekliyor. İkisi ayrı tutulacak.

`youtube_ingest.py`'da `dag_id="youtube_ingest"` kullanılmalı — sensor tam bu ID'yi izliyor.

## Handoff from Phase 6 Session (2026-06-27)

**Watchlist genişletme önceliği:** `GET /api/creators?category=X` endpoint'i `stg_youtube_search.channel_id` ile watchlist kanallarını eşleştiriyor. Test: 17 keyword topic'inden yalnızca 1'i ("biten ürünler") bir watchlist kanalı videosuyla örtüştü. Bu, 5-kanallı watchlist'in keyword aramasında temsil edilmediğini gösteriyor.

**Etki:** Category → creator bağlantısı anlamlı olmak için `data/tracking_config.yaml`'daki `creator_watchlist` bölümünün genişletilmesi gerekiyor. Her yeni handle eklendiğinde Ingestion Agent bir sonraki çalışmada o kanalın videolarını otomatik çeker.

**Veri durumu:** BQ raw tablolarında 2026-06-26 ve 2026-06-27 verisi mevcut (10 kanal + 500 video + ~288 search satırı). PYTHONPATH sorunu docker-compose.yml'ye `PYTHONPATH: /opt/airflow` eklenerek çözüldü — `youtube_ingest` DAG'ı artık `ingestion` modülünü buluyor.

## Session: Pipeline Debug & First Successful End-to-End Run (2026-06-28)

**Sorunlar tespit edildi ve çözüldü:**
- `youtube_ingest` DAG pause'luydu — tüm run'lar stuck "running" durumunda kalıyordu. `airflow dags unpause youtube_ingest` ile çözüldü.
- Eski stuck run'lar `airflow tasks clear youtube_ingest --yes` ile temizlendi.

**İlk başarılı Airflow run (2026-06-28):**
- `fetch_and_upload` → `load_bq_search` + `load_bq_channels` + `load_bq_videos` — 4/4 success.
- BQ'da 2026-06-28 tarihli yeni veri satırları oluştu.

**Güncel BQ raw tablo durumu:** 3 günlük veri (2026-06-26, 2026-06-27, 2026-06-28).
