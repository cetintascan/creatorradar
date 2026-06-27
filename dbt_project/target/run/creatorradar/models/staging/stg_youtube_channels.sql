

  create or replace view `creatorradar-tr`.`creatorradar`.`stg_youtube_channels`
  OPTIONS()
  as with source as (
    select * from `creatorradar-tr`.`creatorradar`.`raw_youtube_channels`
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
        id                                          as channel_id,
        _handle                                     as handle,
        snippet.title                               as channel_title,
        snippet.description                         as description,
        snippet.customUrl                           as custom_url,
        snippet.country                             as country,
        snippet.publishedAt                         as channel_published_at,
        cast(statistics.subscriberCount as int64)   as subscriber_count,
        cast(statistics.viewCount as int64)         as total_view_count,
        cast(statistics.videoCount as int64)        as video_count,
        statistics.hiddenSubscriberCount            as hidden_subscriber_count,
        ingested_date
    from deduped
    where row_num = 1
)

select * from final;

