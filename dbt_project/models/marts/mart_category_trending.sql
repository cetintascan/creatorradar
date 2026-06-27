with daily_demand as (
    select * from {{ ref('mart_category_demand_daily') }}
),

-- Anchor to the latest date present in the data
latest as (
    select max(ingested_date) as latest_date from daily_demand
),

current_week as (
    select
        d.topic,
        avg(d.demand_score)     as current_7d_demand,
        sum(d.video_count)      as current_7d_video_count,
        sum(d.total_views)      as current_7d_total_views
    from daily_demand d
    cross join latest l
    where d.ingested_date between date_sub(l.latest_date, interval 6 day) and l.latest_date
    group by d.topic
),

prior_week as (
    select
        d.topic,
        avg(d.demand_score)     as prior_7d_demand
    from daily_demand d
    cross join latest l
    where d.ingested_date between date_sub(l.latest_date, interval 13 day)
                              and date_sub(l.latest_date, interval 7 day)
    group by d.topic
)

select
    c.topic,
    c.current_7d_demand,
    p.prior_7d_demand,
    c.current_7d_video_count,
    c.current_7d_total_views,
    round(
        safe_divide(c.current_7d_demand - p.prior_7d_demand, p.prior_7d_demand) * 100,
        2
    )                           as demand_delta_pct
from current_week c
left join prior_week p on c.topic = p.topic
