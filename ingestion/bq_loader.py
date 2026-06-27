import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "creatorradar-tr")
BQ_DATASET = "creatorradar"

# Maps GCS entity names to BigQuery raw table names
TABLE_MAP = {
    "channels": "raw_youtube_channels",
    "videos": "raw_youtube_videos",
    "search": "raw_youtube_search",
}


def load_gcs_to_bq(gcs_uri: str, entity: str) -> int:
    """Load a GCS newline-delimited JSON file into the corresponding BigQuery raw table.

    Uses batch load (free). Schema autodetect is on — BigQuery infers types on first load.
    Returns the number of rows loaded.
    """
    table_name = TABLE_MAP.get(entity)
    if not table_name:
        raise ValueError(f"Unknown entity '{entity}'. Must be one of: {list(TABLE_MAP)}")

    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_ref = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    load_job.result()  # wait for completion

    table = client.get_table(table_ref)
    return table.num_rows
