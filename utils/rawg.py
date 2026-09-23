import os
import re
import time
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

import requests

BASE_URL = "https://api.rawg.io/api"
REQUEST_TIMEOUT = 12
CACHE_TTL = 120
SEARCH_PAGE_SIZE = 40
MAX_SERIES_PAGES = 8

GENRE_IDS = {
    "action": "4", "adventure": "3", "rpg": "5", "strategy": "10",
    "shooter": "2", "racing": "1", "sports": "15", "indie": "51",
}

PLATFORM_IDS = {
    "pc": "4",
    "playstation": "187,18,16,15,27,19",
    "xbox": "186,14,80,1",
    "switch": "7",
}

ADDITION_TERMS = {
    "dlc", "expansion", "expansion pack", "season pass", "soundtrack",
    "ost", "demo", "beta", "trial", "companion app", "artbook", "wallpaper",
}

_cache = {}


class RAWGError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def _api_key():
    key = os.getenv("RAWG_API_KEY", "").strip()
    if not key:
        raise RAWGError("La clé RAWG_API_KEY n'est pas configurée.", 503)
    return key


def _cache_get(key):
    item = _cache.get(key)
    if not item:
        return None
    timestamp, value = item
    if time.monotonic() - timestamp > CACHE_TTL:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key, value):
    _cache[key] = (time.monotonic(), value)


def _request(path, params=None):
    params = dict(params or {})
    params["key"] = _api_key()
    try:
        response = requests.get(f"{BASE_URL}/{path.lstrip('/')}", params=params, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RAWGError("RAWG est inaccessible pour le moment.", 502) from exc

    if response.status_code == 401:
        raise RAWGError("La clé RAWG est invalide ou refusée.", 502)
    if response.status_code == 404:
        raise RAWGError("Jeu RAWG introuvable.", 404)
    if response.status_code == 429:
        raise RAWGError("La limite de requêtes RAWG a été atteinte. Réessayez plus tard.", 429)
    if not response.ok:
        raise RAWGError("Impossible de récupérer les données RAWG.", 502)

    try:
        return response.json()
    except ValueError as exc:
        raise RAWGError("RAWG a renvoyé une réponse invalide.", 502) from exc


def _normalize_text(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _compact(value):
    return _normalize_text(value).replace(" ", "")


def _tokens(value):
    return [x for x in _normalize_text(value).split() if len(x) > 1]


def _acronym(value):
    result = ""
    for token in _tokens(value):
        result += token if token.isdigit() else token[0]
    return result


def _levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _similarity(a, b):
    a = _normalize_text(a)
    b = _normalize_text(b)
    if not a or not b:
        return 0.0
    longest = max(len(a), len(b))
    lev = 1 - (_levenshtein(a, b) / longest)
    seq = SequenceMatcher(None, a, b).ratio()
    return max(lev, seq)


def _search_score(query, game):
    query = _normalize_text(query)
    name = _normalize_text(game.get("name") or "")
    if not query or not name:
        return 0

    score = 0
    if query == name:
        score += 1000
    if query in name:
        score += 500
    if len(_compact(query)) >= 4 and _compact(query) in _compact(name):
        score += 450
    if _acronym(name) == _compact(query) or _acronym(name).startswith(_compact(query)):
        score += 400

    q_tokens = _tokens(query)
    n_tokens = _tokens(name)
    token_scores = []
    for q in q_tokens:
        token_scores.append(max((_similarity(q, n) for n in n_tokens), default=0))
    if token_scores:
        score += int(sum(token_scores) / len(token_scores) * 400)
        score += int(min(token_scores) * 200)
    score += int(_similarity(query, name) * 300)
    score += min(60, int((game.get("ratings_count") or 0) ** 0.5))
    return score


def _relevant(query, game):
    query = _normalize_text(query)
    name = _normalize_text(game.get("name") or "")
    if not query or not name:
        return False
    if query in name or _compact(query) in _compact(name):
        return True
    if _acronym(name) == _compact(query):
        return True

    q_tokens = _tokens(query)
    n_tokens = _tokens(name)
    if not q_tokens or not n_tokens:
        return False

    similarities = [max((_similarity(q, n) for n in n_tokens), default=0) for q in q_tokens]
    average = sum(similarities) / len(similarities)
    weakest = min(similarities)

    if len(q_tokens) == 1:
        qlen = len(q_tokens[0])
        threshold = 0.90 if qlen <= 3 else 0.82 if qlen <= 5 else 0.74
        return similarities[0] >= threshold
    return average >= 0.70 and weakest >= 0.55


def _normalize_game(game):
    return {
        "id": game.get("id"),
        "name": game.get("name") or "Information non disponible",
        "slug": game.get("slug"),
        "rating": game.get("rating"),
        "ratings_count": game.get("ratings_count"),
        "released": game.get("released"),
        "background_image": game.get("background_image"),
        "metacritic": game.get("metacritic"),
        "genres": [{"id": g.get("id"), "name": g.get("name")} for g in (game.get("genres") or [])],
        "platforms": [
            {"id": p.get("platform", {}).get("id"), "name": p.get("platform", {}).get("name")}
            for p in (game.get("platforms") or []) if p.get("platform")
        ],
    }


def _dedupe(games):
    result = []
    seen_ids = set()
    seen_names = set()
    for game in games:
        gid = game.get("id")
        name = _normalize_text(game.get("name"))
        if gid in seen_ids or not name or name in seen_names:
            continue
        seen_ids.add(gid)
        seen_names.add(name)
        result.append(game)
    return result


def _apply_filters(games, genre="", platform="", released_after="", released_before="", ordering="-rating"):
    filtered = list(games)
    if genre:
        wanted = _normalize_text(genre)
        filtered = [g for g in filtered if any(_normalize_text(x.get("name")) == wanted for x in g.get("genres", []))]
    if platform:
        wanted = _normalize_text(platform)
        filtered = [g for g in filtered if any(wanted in _normalize_text(x.get("name")) for x in g.get("platforms", []))]
    if released_after:
        filtered = [g for g in filtered if (g.get("released") or "") >= released_after]
    if released_before:
        filtered = [g for g in filtered if (g.get("released") or "") <= released_before]

    if ordering == "-released":
        filtered.sort(key=lambda g: g.get("released") or "", reverse=True)
    elif ordering == "released":
        filtered.sort(key=lambda g: g.get("released") or "")
    elif ordering == "name":
        filtered.sort(key=lambda g: _normalize_text(g.get("name")))
    elif ordering == "-name":
        filtered.sort(key=lambda g: _normalize_text(g.get("name")), reverse=True)
    elif ordering in {"metacritic", "-metacritic"}:
        filtered.sort(key=lambda g: g.get("metacritic") or 0, reverse=ordering.startswith("-"))
    else:
        filtered.sort(key=lambda g: (g.get("rating") or 0, g.get("ratings_count") or 0), reverse=ordering == "-rating")
    return filtered


def _find_anchor(search):
    params = {"search": search, "search_precise": "false", "exclude_additions": "true", "page_size": SEARCH_PAGE_SIZE, "ordering": "-rating"}
    data = _request("/games", params)
    candidates = [_normalize_game(x) for x in (data.get("results") or [])]
    candidates = [x for x in candidates if _relevant(search, x)] or candidates
    if not candidates:
        return None
    return max(candidates, key=lambda x: _search_score(search, x))


def _get_series(anchor_id):
    all_games = []
    for page in range(1, MAX_SERIES_PAGES + 1):
        data = _request(f"/games/{anchor_id}/game-series", {"page": page, "page_size": 40})
        results = data.get("results") or []
        all_games.extend(_normalize_game(x) for x in results)
        if not data.get("next") or not results:
            break
    return _dedupe(all_games)


def get_games(page=1, page_size=20, search="", genre="", platform="", ordering="-rating", released_after="", released_before="", saga=""):
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), 40))
    search = str(search or "").strip()
    saga = str(saga or "").strip()

    cache_key = ("games", page, page_size, search, genre, platform, ordering, released_after, released_before, saga)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if saga:
        anchor = _find_anchor(saga)
        if not anchor:
            result = {"count": 0, "next": False, "previous": False, "results": []}
            _cache_set(cache_key, result)
            return result
        games = _get_series(anchor["id"])
        if search:
            games = [g for g in games if _relevant(search, g)]
        games = _apply_filters(games, genre, platform, released_after, released_before, ordering)
        start = (page - 1) * page_size
        results = games[start:start + page_size]
        result = {
            "count": len(games),
            "next": start + page_size < len(games),
            "previous": page > 1,
            "results": results,
        }
        _cache_set(cache_key, result)
        return result

    params = {"page": page, "page_size": page_size, "ordering": ordering}
    if genre:
        params["genres"] = GENRE_IDS.get(_normalize_text(genre), genre)
    if platform:
        platform_id = PLATFORM_IDS.get(_normalize_text(platform))
        if platform_id:
            params["platforms"] = platform_id
    if released_after or released_before:
        params["dates"] = f"{released_after or '1970-01-01'},{released_before or '2999-12-31'}"

    if search:
        params["search"] = search
        params["search_precise"] = "false"
        params["exclude_additions"] = "true"
        params["page_size"] = max(page_size, SEARCH_PAGE_SIZE)
        if ordering != "-rating":
            params["ordering"] = "-rating"

    data = _request("/games", params)
    raw = [_normalize_game(x) for x in (data.get("results") or [])]

    if search:
        relevant = []
        for game in raw:
            if _relevant(search, game):
                game["_score"] = _search_score(search, game)
                relevant.append(game)

        # Recherche tolérante générique pour les petites fautes.
        if not relevant:
            for variant in _search_variants(search):
                fallback = _request("/games", {
                    "search": variant,
                    "search_precise": "false",
                    "exclude_additions": "true",
                    "page_size": SEARCH_PAGE_SIZE,
                })
                for game in [_normalize_game(x) for x in (fallback.get("results") or [])]:
                    if _relevant(search, game):
                        game["_score"] = _search_score(search, game)
                        relevant.append(game)
                if relevant:
                    break

        relevant = _dedupe(relevant)
        relevant.sort(key=lambda g: (g.get("_score", 0), g.get("rating") or 0, g.get("ratings_count") or 0), reverse=True)
        for game in relevant:
            game.pop("_score", None)
        results = relevant[:page_size]
        result = {"count": len(relevant), "next": False, "previous": page > 1, "results": results}
    else:
        result = {
            "count": data.get("count", 0),
            "next": bool(data.get("next")),
            "previous": bool(data.get("previous")),
            "results": raw,
        }

    _cache_set(cache_key, result)
    return result


def _search_variants(query):
    """Variantes génériques de saisie, sans dictionnaire d'alias manuel."""
    variants = []
    normalized = _normalize_text(query)
    compact = normalized.replace(" ", "")
    if len(compact) >= 5:
        for i in range(len(compact)):
            variants.append(compact[:i] + compact[i + 1:])
        for i in range(len(compact) - 1):
            if compact[i] != compact[i + 1]:
                chars = list(compact)
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
                variants.append("".join(chars))
    return list(dict.fromkeys(v for v in variants if v and v != compact))[:12]


@lru_cache(maxsize=128)
def get_game(game_id):
    data = _request(f"/games/{game_id}")
    if not isinstance(data, dict):
        raise RAWGError("Réponse RAWG invalide.", 502)
    return {
        "id": data.get("id"),
        "name": data.get("name") or "Information non disponible",
        "slug": data.get("slug"),
        "description": data.get("description_raw") or "Information non disponible",
        "rating": data.get("rating"),
        "ratings_count": data.get("ratings_count"),
        "metacritic": data.get("metacritic"),
        "released": data.get("released"),
        "background_image": data.get("background_image"),
        "website": data.get("website"),
        "genres": [{"id": x.get("id"), "name": x.get("name")} for x in (data.get("genres") or [])],
        "platforms": [
            {"id": x.get("platform", {}).get("id"), "name": x.get("platform", {}).get("name")}
            for x in (data.get("platforms") or []) if x.get("platform")
        ],
        "developers": [{"id": x.get("id"), "name": x.get("name")} for x in (data.get("developers") or [])],
        "publishers": [{"id": x.get("id"), "name": x.get("name")} for x in (data.get("publishers") or [])],
    }


@lru_cache(maxsize=128)
def get_screenshots(game_id):
    data = _request(f"/games/{game_id}/screenshots", {"page_size": 20})
    return {
        "results": [
            {"id": x.get("id"), "image": x.get("image"), "width": x.get("width"), "height": x.get("height")}
            for x in (data.get("results") or []) if x.get("image")
        ]
    }
