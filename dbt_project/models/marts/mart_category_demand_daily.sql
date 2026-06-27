with search_topics as (
    select * from {{ ref('stg_youtube_search') }}
),

content_signals as (
    select * from {{ ref('int_yt_content_signals') }}
),

-- Left join so every keyword-search result contributes a row, even when the video
-- belongs to a non-watchlist channel (where we have no view/engagement data).
-- Demand score uses video_count instead of sum(view_count) because view counts are
-- only populated for the small subset of results that match watchlist channel videos.
tagged as (
    select
        st.topic,
        st.ingested_date,
        st.video_id,
        cs.view_count,
        cs.engagement_rate,
        cs.has_sponsor_signal,
        cs.has_commerce_intent
    from search_topics st
    left join content_signals cs on st.video_id = cs.video_id
)

select
    topic,
    ingested_date,
    count(distinct video_id)                                                        as video_count,
    sum(view_count)                                                                 as total_views,
    avg(engagement_rate)                                                            as avg_engagement_rate,
    avg(case when has_sponsor_signal then 1.0 else 0.0 end)                         as sponsor_density,
    avg(case when has_commerce_intent then 1.0 else 0.0 end)                        as commerce_intent_density,
    round(
        ln(1 + count(distinct video_id))
        * (1 + coalesce(avg(case when has_commerce_intent then 1.0 else 0.0 end), 0))
        * (1 + coalesce(avg(case when has_sponsor_signal then 1.0 else 0.0 end), 0)),
        4
    )                                                                               as demand_score
from tagged
group by topic, ingested_date
