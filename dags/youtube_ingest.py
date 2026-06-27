from datetime import date, datetime, timedelta
import os

from airflow import DAG
from airflow.operators.python import PythonOperator

GCS_BUCKET = os.getenv("GCS_BUCKET", "creatorradar-raw")

default_args = {
    "owner": "creatorradar",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def _fetch_and_upload(ds: str, **_) -> dict:
    """Fetch channels, videos, and search results; upload raw NDJSON to GCS."""
    from ingestion.discover_videos import run_discovery
    run_date = date.fromisoformat(ds)
    return run_discovery(run_date=run_date)


def _load_bq(entity: str, filename: str, ds: str, **_) -> int:
    """Load one GCS entity file into the corresponding BigQuery raw table.

    Returns 0 and skips silently if the GCS file does not exist
    (entity had zero results for this run).
    """
    from google.cloud import storage
    from ingestion.bq_loader import load_gcs_to_bq

    gcs_path = f"youtube/{entity}/beauty/{ds}/{filename}.json"
    gcs_uri = f"gs://{GCS_BUCKET}/{gcs_path}"

    blob = storage.Client().bucket(GCS_BUCKET).blob(gcs_path)
    if not blob.exists():
        return 0

    return load_gcs_to_bq(gcs_uri, entity)


with DAG(
    dag_id="youtube_ingest",
    description="Daily YouTube ingestion: fetch channels, videos, search → GCS → BigQuery.",
    schedule="0 2 * * *",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "youtube"],
) as dag:

    fetch_and_upload = PythonOperator(
        task_id="fetch_and_upload",
        python_callable=_fetch_and_upload,
    )

    load_bq_search = PythonOperator(
        task_id="load_bq_search",
        python_callable=_load_bq,
        op_kwargs={"entity": "search", "filename": "search_results"},
    )

    load_bq_channels = PythonOperator(
        task_id="load_bq_channels",
        python_callable=_load_bq,
        op_kwargs={"entity": "channels", "filename": "channels"},
    )

    load_bq_videos = PythonOperator(
        task_id="load_bq_videos",
        python_callable=_load_bq,
        op_kwargs={"entity": "videos", "filename": "videos"},
    )

    fetch_and_upload >> [load_bq_search, load_bq_channels, load_bq_videos]
