import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

GCS_BUCKET = os.getenv("GCS_BUCKET", "creatorradar-raw")


def upload_json(data: list[dict], gcs_path: str) -> None:
    """Upload a list of dicts as a newline-delimited JSON file to GCS.

    Never overwrites an existing file — raises if the path already exists.
    """
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(gcs_path)

    if blob.exists():
        raise FileExistsError(f"GCS path already exists: gs://{GCS_BUCKET}/{gcs_path}")

    ndjson = "\n".join(json.dumps(row, ensure_ascii=False) for row in data)
    blob.upload_from_string(ndjson, content_type="application/json")


def make_gcs_path(entity: str, category: str, run_date: date, filename: str) -> str:
    """Build the standard GCS path for a raw file.

    Pattern: youtube/{entity}/{category}/YYYY-MM-DD/{filename}.json
    """
    return f"youtube/{entity}/{category}/{run_date.isoformat()}/{filename}.json"
