import os
import time
from functools import lru_cache

import requests

BASE_URL = "https://www.googleapis.com/youtube/v3/search"
REQUEST_TIMEOUT = 12
_CACHE_TTL = 600
_cache = {}


class YouTubeError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def _api_key():
    key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise YouTubeError("La clé YOUTUBE_API_KEY n'est pas configurée.", 503)
    return key


def _cache_get(key):
    item = _cache.get(key)
    if not item:
        return None
    timestamp, value = item
    if time.monotonic() - timestamp > _CACHE_TTL:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key, value):
    _cache[key] = (time.monotonic(), value)


def _search(query):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 10,
        "order": "relevance",
        "videoEmbeddable": "true",
        "safeSearch": "moderate",
        "key": _api_key(),
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise YouTubeError("YouTube est inaccessible pour le moment.") from exc

    if response.status_code in (400, 403):
        raise YouTubeError("La clé YouTube est invalide, inactive ou sans quota disponible.", 502)
    if response.status_code == 429:
        raise YouTubeError("La limite de requêtes YouTube a été atteinte.", 429)
    if not response.ok:
        raise YouTubeError("Impossible de rechercher le trailer sur YouTube.", 502)

    try:
        return response.json()
    except ValueError as exc:
        raise YouTubeError("YouTube a renvoyé une réponse invalide.", 502) from exc


def _score(item, game_name):
    title = (item.get("snippet", {}).get("title") or "").lower()
    channel = (item.get("snippet", {}).get("channelTitle") or "").lower()
    score = 0
    official_words = ("official", "playstation", "xbox", "nintendo", "ea", "ubisoft", "bethesda", "rockstar", "bandai namco", "square enix", "capcom", "sega", "2k", "valve")
    if "trailer" in title:
        score += 4
    if "official" in title or any(word in channel for word in official_words):
        score += 5
    if game_name.lower() in title:
        score += 3
    if "fan trailer" in title or "concept" in title or "reaction" in title:
        score -= 6
    return score


@lru_cache(maxsize=128)
def search_trailer(game_name):
    cache_key = game_name.casefold()
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    data = _search(f"{game_name} official trailer")
    items = data.get("items") or []
    if not items:
        data = _search(f"{game_name} trailer")
        items = data.get("items") or []

    if not items:
        result = None
    else:
        item = max(items, key=lambda x: _score(x, game_name))
        video_id = (item.get("id") or {}).get("videoId")
        snippet = item.get("snippet") or {}
        if not video_id:
            result = None
        else:
            result = {
                "video_id": video_id,
                "title": snippet.get("title") or "Information non disponible",
                "channel": snippet.get("channelTitle") or "Information non disponible",
                "thumbnail": (snippet.get("thumbnails") or {}).get("high", {}).get("url"),
                "published_at": snippet.get("publishedAt"),
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            }

    _cache_set(cache_key, result)
    return result
