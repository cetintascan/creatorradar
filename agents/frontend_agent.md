# Frontend Agent Log

## Handoff from dbt Phase 4 Session (2026-06-27)

Creator leaderboard sayfası için kaynak mart tablosu hazır.

### `mart_creator_profiles` schema (BigQuery: `creatorradar-tr.creatorradar.mart_creator_profiles`)

| Sütun | Tip | Açıklama |
|---|---|---|
| `channel_id` | STRING | YouTube channel ID (PK) |
| `handle` | STRING | YouTube @handle |
| `channel_title` | STRING | Kanal adı |
| `subscriber_count` | INT64 | Abone sayısı |
| `video_count` | INT64 | Toplam video sayısı (snapshot) |
| `avg_engagement_rate` | FLOAT64 | (like+comment)/view ortalaması |
| `avg_relative_performance` | FLOAT64 | video views / kanal median views |
| `sponsor_signal_rate` | FLOAT64 | Sponsor sinyali taşıyan video oranı [0,1] |
| `commerce_intent_rate` | FLOAT64 | Ticaret niyeti taşıyan video oranı [0,1] |
| `normalized_relative_performance` | FLOAT64 | Min-max normalize [0,1] |
| `normalized_engagement_rate` | FLOAT64 | Min-max normalize [0,1] |
| `normalized_commerce_intent` | FLOAT64 | Min-max normalize [0,1] |
| `normalized_sponsor_signal` | FLOAT64 | Min-max normalize [0,1] |
| `commercial_fit_score` | FLOAT64 | Ağırlıklı final skor [0,1] |

### FastAPI endpoint hedefleri (Phase 6)

```
GET /api/creators
  → mart_creator_profiles ORDER BY commercial_fit_score DESC
  → optional: ?category= (Phase 5'te topic sütunu eklenince aktif)

GET /api/creators/{channel_id}
  → mart_creator_profiles WHERE channel_id = @channel_id
  → + int_yt_content_signals WHERE channel_id = @channel_id (video geçmişi)
```

### Creator leaderboard UI kolonları
`handle` · `channel_title` · `subscriber_count` · `commercial_fit_score` · `sponsor_signal_rate` · `commerce_intent_rate`

---

## Handoff from dbt Phase 5 Session (2026-06-27)

Phase 5 tamamlandı — tüm mart tabloları hazır. Aşağıdaki endpoint'ler ve sayfalar artık yazılabilir.

### Yeni mart tabloları

**`mart_category_demand_daily`** (`creatorradar-tr.creatorradar.mart_category_demand_daily`)
| Sütun | Tip | Açıklama |
|---|---|---|
| `topic` | STRING | Discovery keyword |
| `ingested_date` | DATE | Arama tarihi |
| `video_count` | INT64 | O gün bulunan video sayısı |
| `total_views` | INT64 | Toplam görüntülenme |
| `avg_engagement_rate` | FLOAT64 | Ortalama etkileşim oranı |
| `sponsor_density` | FLOAT64 | Sponsor sinyali oranı [0,1] |
| `commerce_intent_density` | FLOAT64 | Ticaret niyeti oranı [0,1] |
| `demand_score` | FLOAT64 | Kompozit talep skoru |

**`mart_category_trending`** (`creatorradar-tr.creatorradar.mart_category_trending`)
| Sütun | Tip | Açıklama |
|---|---|---|
| `topic` | STRING | Discovery keyword (PK) |
| `current_7d_demand` | FLOAT64 | Son 7 gün ortalama demand_score |
| `prior_7d_demand` | FLOAT64 | Önceki 7 gün ortalama demand_score |
| `current_7d_video_count` | INT64 | Son 7 günde video sayısı |
| `current_7d_total_views` | INT64 | Son 7 günde toplam görüntülenme |
| `demand_delta_pct` | FLOAT64 | % değişim (NULL = geçen hafta veri yok) |

**`mart_brand_mentions`** (`creatorradar-tr.creatorradar.mart_brand_mentions`)
| Sütun | Tip | Açıklama |
|---|---|---|
| `brand_name` | STRING | Marka adı |
| `channel_id` | STRING | YouTube channel ID |
| `handle` | STRING | YouTube @handle |
| `channel_title` | STRING | Kanal adı |
| `mention_count` | INT64 | Markayı içeren video sayısı |
| `latest_mention_date` | TIMESTAMP | En son bahseden videonun yayın tarihi |

### FastAPI endpoint hedefleri (Phase 6 — tümü yazılabilir)

```
GET /api/categories
  → mart_category_demand_daily WHERE ingested_date = max(ingested_date)
  → ORDER BY demand_score DESC

GET /api/categories/trending
  → mart_category_trending ORDER BY demand_delta_pct DESC

GET /api/categories/{topic}/creators
  → ⚠️  stg_youtube_search'te channel_id sütunu YOK — doğrudan join yapılamaz
  → Gerçek path: mart_creator_profiles.channel_id
                 → stg_youtube_videos.channel_id + video_id
                 → stg_youtube_search.video_id WHERE topic = @topic
  → Alternatif: dbt agent'a mart_topic_creators yaptırılabilir (Phase 6 başında karar ver)

GET /api/creators?category={topic}
  → yukarıdaki aynı join path
  → ORDER BY commercial_fit_score DESC

GET /api/brands
  → mart_brand_mentions GROUP BY brand_name, SUM(mention_count) ORDER BY mentions DESC
```

### Frontend sayfaları (tümü unblocked)
- **Creator leaderboard** — `mart_creator_profiles`, `?category=` filtresi artık aktif
- **Category trends** — `mart_category_trending` ile bar chart, `demand_delta_pct` toggle
- **Creator detail** — `mart_brand_mentions` ile marka timeline eklenebilir

---

## Phase 6 — Tamamlandı (2026-06-27)

### Yazılan dosyalar

**FastAPI (`api/`):**
- `api/main.py` — CORS middleware, router registration, dotenv load
- `api/bq.py` — BigQuery client + `ref()` helper
- `api/routers/creators.py` — `/api/creators`, `/api/creators/{id}`
- `api/routers/categories.py` — `/api/categories`, `/api/categories/trending`, `/api/categories/{topic}/creators`
- `api/routers/brands.py` — `/api/brands`

**React (`frontend/src/`):**
- `App.jsx` — BrowserRouter, indigo nav bar, 3 routes
- `api.js` — minimal fetch wrapper
- `pages/CreatorLeaderboard.jsx` — skor çubuğu, sinyal dotları, kategori dropdown, satır tıklama → detail
- `pages/CategoryTrends.jsx` — Recharts BarChart, "Demand Today" / "7-Day Trend" toggle, detay tablosu
- `pages/CreatorDetail.jsx` — 5 stat kartı, video geçmişi tablosu, sponsor/commerce badge'leri

### Çalışma durumu (2026-06-27 itibarıyla)

| Endpoint | Durum | Notlar |
|---|---|---|
| `GET /api/creators` | ✅ Çalışıyor | 5 creator, score 0.32–0.66 |
| `GET /api/creators?category=X` | ⚠️ Seyrek | Watchlist kanalları keyword aramasında nadiren çıkıyor |
| `GET /api/creators/{id}` | ✅ Çalışıyor | 30 video, sinyal verileri |
| `GET /api/categories` | ✅ Çalışıyor | 17 topic, demand_score (video_count bazlı) |
| `GET /api/categories/trending` | ✅ Çalışıyor | delta_pct NULL (14 gün veri gerekli) |
| `GET /api/categories/{topic}/creators` | ⚠️ Seyrek | Yukarıdaki ile aynı kısıt |
| `GET /api/brands` | ✅ Çalışıyor | Sephora, Maybelline, Revolution... |

### ?category= filtresi sınırlılığı
`/api/creators?category=X` ve `/api/categories/{topic}/creators` endpoint'leri `stg_youtube_search.channel_id` üzerinden watchlist kanallarını buluyor. YouTube keyword araması genel ekosistemden video döndürür — 5 watchlist kanalı bu aramalarda nadiren çıkıyor (test: 17 topic'ten yalnızca "biten ürünler" 1 eşleşme). Daha fazla kanal `tracking_config.yaml`'a eklendiğinde bu otomatik düzelir.

### Gelecek iyileştirmeler (post-MVP)
- Kategori dropdown "No creators found" yerine "showing top creators (no category match)" fallback gösterebilir
- `demand_delta_pct` için %14 veri birikince trending chart anlamlı hale gelir
- Creator detail sayfasına `mart_brand_mentions` marka kartları eklenebilir
