from typing import Optional

from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

from api.bq import client, ref

router = APIRouter(tags=["creators"])


@router.get("/creators")
def list_creators(category: Optional[str] = None) -> list[dict]:
    bq = client()

    if category:
        query = f"""
            SELECT p.*
            FROM {ref("mart_creator_profiles")} p
            WHERE p.channel_id IN (
                SELECT DISTINCT channel_id
                FROM {ref("stg_youtube_search")}
                WHERE topic = @topic
            )
            ORDER BY p.commercial_fit_score DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("topic", "STRING", category)
            ]
        )
        rows = bq.query(query, job_config=job_config).result()
    else:
        query = f"""
            SELECT * FROM {ref("mart_creator_profiles")}
            ORDER BY commercial_fit_score DESC
        """
        rows = bq.query(query).result()

    return [dict(row) for row in rows]


@router.get("/creators/{channel_id}")
def get_creator(channel_id: str) -> dict:
    bq = client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("channel_id", "STRING", channel_id)
        ]
    )

    profile_rows = list(
        bq.query(
            f"SELECT * FROM {ref('mart_creator_profiles')} WHERE channel_id = @channel_id",
            job_config=job_config,
        ).result()
    )
    if not profile_rows:
        raise HTTPException(status_code=404, detail="Creator not found")

    signal_rows = list(
        bq.query(
            f"""
            SELECT video_id, video_title, published_at, view_count,
                   engagement_rate, has_sponsor_signal, has_commerce_intent,
                   relative_performance
            FROM {ref("int_yt_content_signals")}
            WHERE channel_id = @channel_id
            ORDER BY published_at DESC
            LIMIT 30
            """,
            job_config=job_config,
        ).result()
    )

    return {
        "profile": dict(profile_rows[0]),
        "videos": [dict(r) for r in signal_rows],
    }
