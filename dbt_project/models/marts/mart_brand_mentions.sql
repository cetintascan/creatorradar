with brands as (
    select brand_name
    from unnest([
        'The Purest Solutions', 'La Roche-Posay', 'CeraVe', 'Bioderma',
        'Garnier', 'Maybelline', "L'Oréal", 'Yves Rocher', 'Sephora',
        'Gratis', 'Watsons', 'Bee Beauty', 'Pastel', 'Flormar',
        'Note', 'Revolution', 'Nivea', 'Neutrogena', 'Sebamed', 'Cosmed'
    ]) as brand_name
),

content as (
    select
        cs.video_id,
        cs.channel_id,
        cs.video_title,
        cs.published_at,
        ch.handle,
        ch.channel_title,
        lower(cs.video_title || ' ' || coalesce(cs.description, '')) as text_content
    from {{ ref('int_yt_content_signals') }} cs
    left join (
        select channel_id, handle, channel_title
        from {{ ref('stg_youtube_channels') }}
        where ingested_date = (
            select max(ingested_date) from {{ ref('stg_youtube_channels') }}
        )
    ) ch on cs.channel_id = ch.channel_id
),

brand_matches as (
    select
        b.brand_name,
        c.channel_id,
        c.handle,
        c.channel_title,
        c.video_id,
        c.published_at
    from brands b
    cross join content c
    where c.text_content like '%' || lower(b.brand_name) || '%'
)

select
    brand_name,
    channel_id,
    handle,
    channel_title,
    count(distinct video_id)    as mention_count,
    max(published_at)           as latest_mention_date
from brand_matches
group by brand_name, channel_id, handle, channel_title
