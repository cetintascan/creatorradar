with source as (
    select * from {{ source('raw', 'raw_youtube_videos') }}
),

deduped as (
    select *,
        row_number() over (
            partition by id, ingested_date
            order by ingested_date desc
        ) as row_num
    from source
    where id is not null
),

final as (
    select
        id                                          as video_id,
        snippet.channelId                           as channel_id,
        snippet.title                               as video_title,
        snippet.description                         as description,
        snippet.publishedAt                         as published_at,
        snippet.channelTitle                        as channel_title,
        snippet.categoryId                          as category_id,
        snippet.defaultAudioLanguage                as audio_language,
        contentDetails.duration                     as duration_iso,
        contentDetails.definition                   as definition,
        cast(statistics.viewCount as int64)         as view_count,
        cast(statistics.likeCount as int64)         as like_count,
        cast(statistics.commentCount as int64)      as comment_count,
        ingested_date
    from deduped
    where row_num = 1
)

select * from final
