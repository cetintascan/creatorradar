with source as (
    select * from {{ source('raw', 'raw_youtube_search') }}
),

deduped as (
    select *,
        row_number() over (
            partition by id.videoId, _keyword, ingested_date
            order by ingested_date desc
        ) as row_num
    from source
    where id.videoId is not null
      and _keyword is not null
)

select
    id.videoId          as video_id,
    _keyword            as topic,
    snippet.channelId   as channel_id,
    snippet.title       as video_title,
    date(ingested_date) as ingested_date
from deduped
where row_num = 1
