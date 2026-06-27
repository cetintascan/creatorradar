from fastapi import APIRouter

from api.bq import client, ref

router = APIRouter(tags=["brands"])


@router.get("/brands")
def list_brands() -> list[dict]:
    bq = client()
    query = f"""
        SELECT
            brand_name,
            SUM(mention_count)        AS total_mentions,
            COUNT(DISTINCT channel_id) AS creator_count
        FROM {ref("mart_brand_mentions")}
        GROUP BY brand_name
        ORDER BY total_mentions DESC
    """
    return [dict(row) for row in bq.query(query).result()]
