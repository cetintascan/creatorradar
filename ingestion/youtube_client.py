import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    pass


def _get(endpoint: str, params: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    if not YOUTUBE_API_KEY:
        raise YouTubeAPIError("Missing YOUTUBE_API_KEY in .env")

    url = f"{BASE_URL}/{endpoint}"
    params = {**params, "key": YOUTUBE_API_KEY}

    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            return response.json()

        if response.status_code in {429, 500, 502, 503, 504} and attempt < max_retries - 1:
            time.sleep(2 ** attempt)
            continue

        raise YouTubeAPIError(
            f"API error: {response.status_code} | {response.text}"
        )

    raise YouTubeAPIError("API request failed after retries.")


def search_videos(keyword: str, published_after: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Keyword bazlı video keşfi. published_after: RFC3339 format (2026-06-25T00:00:00Z)"""
    data = _get("search", {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "relevanceLanguage": "tr",
        "regionCode": "TR",
    })
    return data.get("items", [])


def get_channel_by_handle(handle: str) -> Optional[Dict[str, Any]]:
    clean_handle = handle.strip().lstrip("@")
    data = _get("channels", {
        "part": "snippet,contentDetails,statistics",
        "forHandle": clean_handle,
    })
    items = data.get("items", [])
    return items[0] if items else None


def get_upload_playlist_items(playlist_id: str, max_videos: int = 50) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    next_page_token = None

    while len(items) < max_videos:
        page_size = min(50, max_videos - len(items))
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": page_size,
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        data = _get("playlistItems", params)
        items.extend(data.get("items", []))
        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break

    return items


def get_videos_by_ids(video_ids: List[str]) -> List[Dict[str, Any]]:
    all_items: List[Dict[str, Any]] = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i: i + 50]
        data = _get("videos", {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(batch),
            "maxResults": 50,
        })
        all_items.extend(data.get("items", []))

    return all_items


def get_comment_threads(video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
    try:
        data = _get("commentThreads", {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(max_results, 100),
            "order": "relevance",
        })
        return data.get("items", [])
    except YouTubeAPIError:
        # Comments disabled on some videos
        return []
