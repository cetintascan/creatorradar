with search_topics as (
    select * from {{ ref('stg_youtube_search') }}
),

content_signals as (
    select * from {{ ref('int_yt_content_signals') }}
),

-- Each search result is tagged with the keyword that surfaced it.
-- A video can appear under multiple topics if it was returned by multiple keyword searches.
tagged_signals as (
    select
        st.topic,
        st.ingested_date,
        cs.video_id,
        cs.view_count,
        cs.engagement_rate,
        cs.has_sponsor_signal,
        cs.has_commerce_intent
    from search_topics st
    inner join content_signals cs on st.video_id = cs.video_id
)

select
    topic,
    ingested_date,
    count(distinct video_id)                                                    as video_count,
    sum(view_count)                                                             as total_views,
    avg(engagement_rate)                                                        as avg_engagement_rate,
    avg(case when has_sponsor_signal then 1.0 else 0.0 end)                     as sponsor_density,
    avg(case when has_commerce_intent then 1.0 else 0.0 end)                    as commerce_intent_density,
    round(
        ln(1 + coalesce(sum(view_count), 1))
        * (1 + avg(case when has_commerce_intent then 1.0 else 0.0 end))
        * (1 + avg(case when has_sponsor_signal then 1.0 else 0.0 end)),
        4
    )                                                                           as demand_score
from tagged_signals
group by topic, ingested_date
