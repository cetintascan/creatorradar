with videos as (
    select
        v.*,
        lower(v.video_title || ' ' || coalesce(v.description, '')) as text_content
    from {{ ref('stg_youtube_videos') }} v
    where v.ingested_date = (
        select max(ingested_date) from {{ ref('stg_youtube_videos') }}
    )
),

channel_baseline as (
    select * from {{ ref('int_yt_channel_baseline') }}
)

select
    v.video_id,
    v.channel_id,
    v.video_title,
    v.description,
    v.published_at,
    v.view_count,
    v.like_count,
    v.comment_count,
    v.ingested_date,
    safe_divide(
        coalesce(v.like_count, 0) + coalesce(v.comment_count, 0),
        nullif(v.view_count, 0)
    )                                                                   as engagement_rate,
    {{ detect_sponsor_signal('v.text_content') }}                       as has_sponsor_signal,
    {{ detect_commerce_intent('v.text_content') }}                      as has_commerce_intent,
    safe_divide(v.view_count, nullif(cb.median_view_count, 0))          as relative_performance,
    cb.median_view_count                                                as channel_median_views
from videos v
left join channel_baseline cb on v.channel_id = cb.channel_id
