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

### Bekleyen (Phase 5 bitmeden önce yapılamaz)
- `?category=` filtresi — `mart_category_demand_daily` ve topic ataması Phase 5'te geliyor
- Category trends sayfası — `mart_category_trending` Phase 5 çıktısı
