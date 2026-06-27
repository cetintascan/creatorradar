# Data Quality Agent Log

## Handoff from dbt Phase 4 Session (2026-06-27)

Phase 4 ürettiği tablolar izlemeye hazır. İlk `dbt run` sonrasında aşağıdaki kontrolleri yap:

### İzlenecek tablolar (Phase 4)

**`int_yt_channel_baseline`**
- Her aktif kanalın bir satırı olmalı (şu an 5 kanal takipte)
- `median_view_count` NULL olmamalı — NULL ise kanalın son 30 günde yayınladığı video yok veya `published_at` verisi eksik

**`int_yt_content_signals`**
- Row count ≈ `stg_youtube_videos` son snapshot row count ile eşleşmeli
- `has_sponsor_signal = TRUE` oranı: Türk güzellik içeriğinde %5–25 bant bekleniyor; sıfır ise keyword listesi hiç firing etmiyor, %90+ ise yanlış pozitif riski
- `has_commerce_intent = TRUE` oranı: daha geniş bir kapsam nedeniyle %30–70 bant bekleniyor (özellikle `link` keyword'ü geniş yakalıyor)
- `engagement_rate` > 1.0 olan satırlar kontrol edilmeli (like+comment > view_count ise veri anomalisi)
- `relative_performance` NULL oranı: kanal baseline'ı hesaplanamayan videolar; bootstrap döneminde yüksek olabilir ama zamanla sıfıra düşmeli

**`mart_creator_profiles`**
- `commercial_fit_score` dağılımı non-trivial olmalı: tüm yaratıcıların skoru aynı değilse sorun yok; tek bir creator max skoru alıyorsa normalizasyon çalışmıyor olabilir (creator sayısı çok düşük)
- `commercial_fit_score` NULL olmamalı (schema testi zaten kapsıyor)
- `commercial_fit_score` < 0 veya > 1 satır döndürmemeli (custom test: `assert_commercial_fit_score_range`)

### Önemli not
`detect_commerce_intent` içindeki `like '%link%'` keyword'ü çok geniş. Gerçek veri gelince intent oranı çok yüksek çıkarsa bu keyword filtreye alınabilir. İlk çalıştırmada gözlemle ve gerekirse `dbt_agent`'ı bildir.

---

## Handoff from dbt Phase 5 Session (2026-06-27)

### İzlenecek tablolar (Phase 5)

**`stg_youtube_search`**
- Row count ≈ `raw_youtube_search` satır sayısı (dedup sonrası biraz düşük olabilir)
- Her satırda `topic` (keyword) ve `video_id` NULL olmamalı — schema testi kapsıyor
- `topic` değerleri `tracking_config.yaml`'daki 18 keyword ile eşleşmeli; farklı bir değer varsa ingestion'da sorun var

**`mart_category_demand_daily`**
- Her aktif keyword için veri olmalı; eksik keyword varsa o gün arama yapılmamış veya 0 sonuç dönmüş
- `demand_score` > 0 olmalı — 0 çıkarsa `total_views` sıfır (video bulunmuş ama view yok) veya join başarısız
- (topic, ingested_date) kombinasyonu unique olmalı — GROUP BY garantiliyor ama composite test yok, anomali şüphesinde elle kontrol:
  ```sql
  select topic, ingested_date, count(*) as cnt
  from `creatorradar-tr.creatorradar.mart_category_demand_daily`
  group by 1,2 having cnt > 1
  ```

**`mart_category_trending`**
- `demand_delta_pct` NULL olan topic'ler = geçen hafta veri yok (yeni keyword veya bootstrap); beklenen durum
- `demand_delta_pct` > +200% veya < -80% gibi uç değerler anomali sinyali — gerçek mi yoksa veri eksikliği mi kontrol et

**`mart_brand_mentions`**
- 20 marka × 5 kanal = maksimum 100 satır; gerçekte çok daha az (her kanal her markayı mention etmez)
- `mention_count` = 0 olan satır gelmemeli (GROUP BY zaten filtreler, ama kontrol et)
- Beklenmedik yüksek mention_count: tek bir kanalın çok fazla bir markayı mention etmesi gerçek mi yoksa keyword çok geniş mi?

### Run sonrası kontrol sorgusu
```sql
select
  count(*) as total_videos,
  countif(has_sponsor_signal) as sponsor_signals,
  countif(has_commerce_intent) as commerce_intents,
  round(countif(has_sponsor_signal) / count(*), 3) as sponsor_rate,
  round(countif(has_commerce_intent) / count(*), 3) as commerce_rate,
  countif(engagement_rate > 1) as anomalous_engagement,
  countif(relative_performance is null) as missing_baseline
from `creatorradar-tr.creatorradar.int_yt_content_signals`
```
