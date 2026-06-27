import os
from datetime import date, timedelta
from pathlib import Path

import yaml
from dotenv import load_dotenv

from ingestion.gcs_uploader import make_gcs_path, upload_json
from ingestion.youtube_client import get_channel_by_handle, get_upload_playlist_items, get_videos_by_ids, search_videos

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

TRACKING_CONFIG = Path(__file__).resolve().parents[1] / "data" / "tracking_config.yaml"


def _load_config() -> tuple[list[str], list[str]]:
    with open(TRACKING_CONFIG, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["discovery_keywords"], config["creator_watchlist"]


def run_discovery(run_date: date | None = None) -> dict:
    """Fetch videos via keyword search and creator watchlist, upload raw JSON to GCS.

    Returns a summary dict with counts for logging.
    """
    if run_date is None:
        run_date = date.today() - timedelta(days=1)

    published_after = f"{run_date.isoformat()}T00:00:00Z"
    keywords, handles = _load_config()

    # --- keyword search ---
    search_results: list[dict] = []
    for keyword in keywords:
        results = search_videos(keyword, published_after=published_after, max_results=10)
        for item in results:
            item["_keyword"] = keyword
            item["ingested_date"] = run_date.isoformat()
        search_results.extend(results)

    if search_results:
        gcs_path = make_gcs_path("search", "beauty", run_date, "search_results")
        upload_json(search_results, gcs_path)

    # --- creator watchlist ---
    channel_rows: list[dict] = []
    video_rows: list[dict] = []

    for handle in handles:
        channel = get_channel_by_handle(handle)
        if not channel:
            continue

        channel["_handle"] = handle
        channel["ingested_date"] = run_date.isoformat()
        channel_rows.append(channel)

        playlist_id = (
            channel.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )
        if not playlist_id:
            continue

        playlist_items = get_upload_playlist_items(playlist_id, max_videos=50)
        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_items
            if "contentDetails" in item
        ]
        if not video_ids:
            continue

        videos = get_videos_by_ids(video_ids)
        for v in videos:
            v["ingested_date"] = run_date.isoformat()
        video_rows.extend(videos)

    if channel_rows:
        gcs_path = make_gcs_path("channels", "beauty", run_date, "channels")
        upload_json(channel_rows, gcs_path)

    if video_rows:
        gcs_path = make_gcs_path("videos", "beauty", run_date, "videos")
        upload_json(video_rows, gcs_path)

    return {
        "run_date": run_date.isoformat(),
        "search_results": len(search_results),
        "channels": len(channel_rows),
        "videos": len(video_rows),
    }
