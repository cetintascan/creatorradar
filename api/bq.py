import os
from google.cloud import bigquery

_PROJECT = os.getenv("GCP_PROJECT_ID", "creatorradar-tr")
_DATASET = "creatorradar"


def client() -> bigquery.Client:
    return bigquery.Client(project=_PROJECT)


def ref(table: str) -> str:
    """Return a fully-qualified BigQuery table reference."""
    return f"`{_PROJECT}.{_DATASET}.{table}`"
