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
  → mart_creator_profiles JOIN stg_youtube_search ON channel_id WHERE topic = @topic

GET /api/creators?category={topic}
  → mart_creator_profiles JOIN stg_youtube_search ON channel_id WHERE topic = @topic
  → ORDER BY commercial_fit_score DESC

GET /api/brands
  → mart_brand_mentions GROUP BY brand_name, SUM(mention_count) ORDER BY mentions DESC
```

### Frontend sayfaları (tümü unblocked)
- **Creator leaderboard** — `mart_creator_profiles`, `?category=` filtresi artık aktif
- **Category trends** — `mart_category_trending` ile bar chart, `demand_delta_pct` toggle
- **Creator detail** — `mart_brand_mentions` ile marka timeline eklenebilir
