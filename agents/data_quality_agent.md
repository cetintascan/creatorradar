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

### Run sonrası kontrol sorgusu (BigQuery)
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
