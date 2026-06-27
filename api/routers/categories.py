from fastapi import APIRouter
from google.cloud import bigquery

from api.bq import client, ref

router = APIRouter(tags=["categories"])


@router.get("/categories")
def list_categories() -> list[dict]:
    bq = client()
    query = f"""
        SELECT * FROM {ref("mart_category_demand_daily")}
        WHERE ingested_date = (
            SELECT MAX(ingested_date) FROM {ref("mart_category_demand_daily")}
        )
        ORDER BY demand_score DESC
    """
    return [dict(row) for row in bq.query(query).result()]


@router.get("/categories/trending")
def trending_categories() -> list[dict]:
    bq = client()
    query = f"""
        SELECT * FROM {ref("mart_category_trending")}
        ORDER BY demand_delta_pct DESC NULLS LAST
    """
    return [dict(row) for row in bq.query(query).result()]


@router.get("/categories/{topic}/creators")
def creators_by_topic(topic: str) -> list[dict]:
    bq = client()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("topic", "STRING", topic)
        ]
    )
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
    return [dict(row) for row in bq.query(query, job_config=job_config).result()]
