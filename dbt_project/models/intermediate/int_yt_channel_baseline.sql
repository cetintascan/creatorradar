with recent_videos as (
    select *
    from {{ ref('stg_youtube_videos') }}
    where ingested_date = (
            select max(ingested_date) from {{ ref('stg_youtube_videos') }}
        )
      and published_at >= timestamp_sub(current_timestamp(), interval 30 day)
      and view_count is not null
)

select
    channel_id,
    approx_quantiles(view_count, 2)[offset(1)]  as median_view_count,
    count(*)                                     as video_count_30d,
    avg(view_count)                              as avg_view_count_30d
from recent_videos
group by channel_id
