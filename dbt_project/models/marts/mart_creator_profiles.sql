with content_signals as (
    select * from {{ ref('int_yt_content_signals') }}
),

channels as (
    select *
    from {{ ref('stg_youtube_channels') }}
    where ingested_date = (
        select max(ingested_date) from {{ ref('stg_youtube_channels') }}
    )
),

creator_aggregates as (
    select
        channel_id,
        count(*)                                                        as video_count,
        avg(engagement_rate)                                            as avg_engagement_rate,
        avg(relative_performance)                                       as avg_relative_performance,
        avg(case when has_sponsor_signal then 1.0 else 0.0 end)         as sponsor_signal_rate,
        avg(case when has_commerce_intent then 1.0 else 0.0 end)        as commerce_intent_rate
    from content_signals
    group by channel_id
),

with_channel_info as (
    select
        ca.channel_id,
        ch.handle,
        ch.channel_title,
        ch.subscriber_count,
        ca.video_count,
        ca.avg_engagement_rate,
        ca.avg_relative_performance,
        ca.sponsor_signal_rate,
        ca.commerce_intent_rate
    from creator_aggregates ca
    left join channels ch on ca.channel_id = ch.channel_id
),

normalized as (
    select
        *,
        {{ normalize_score('avg_relative_performance', '1') }}          as normalized_relative_performance,
        {{ normalize_score('avg_engagement_rate', '1') }}               as normalized_engagement_rate,
        {{ normalize_score('commerce_intent_rate', '1') }}              as normalized_commerce_intent,
        {{ normalize_score('sponsor_signal_rate', '1') }}               as normalized_sponsor_signal
    from with_channel_info
)

select
    channel_id,
    handle,
    channel_title,
    subscriber_count,
    video_count,
    avg_engagement_rate,
    avg_relative_performance,
    sponsor_signal_rate,
    commerce_intent_rate,
    normalized_relative_performance,
    normalized_engagement_rate,
    normalized_commerce_intent,
    normalized_sponsor_signal,
    round(
        0.40 * coalesce(normalized_relative_performance, 0)
        + 0.30 * coalesce(normalized_engagement_rate, 0)
        + 0.20 * coalesce(normalized_commerce_intent, 0)
        + 0.10 * coalesce(normalized_sponsor_signal, 0),
        4
    ) as commercial_fit_score
from normalized
