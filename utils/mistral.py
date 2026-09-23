import json
import os
import re
from datetime import date

from mistralai.client import Mistral


class MistralError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


DEFAULT_MODEL = os.getenv("MISTRAL_MODEL", "ministral-3b-latest").strip() or "ministral-3b-latest"


def _client():
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        raise MistralError("La clé MISTRAL_API_KEY n'est pas configurée.", 503)
    return Mistral(api_key=key)


def _extract_json(text):
    if not text:
        raise MistralError("Mistral a renvoyé une réponse vide.", 502)

    text = text.strip()

    # Nettoyage des éventuels blocs markdown.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            value = json.loads(match.group(0))
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    raise MistralError("Mistral n'a pas renvoyé un JSON exploitable.", 502)


def _clean_list(value, limit=8):
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str):
            item = item.strip()
            if item and item not in result:
                result.append(item)
    return result[:limit]


def _clean_date(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if not value:
        return ""
    try:
        date.fromisoformat(value)
        return value
    except ValueError:
        return ""


def normalize_criteria(data):
    if not isinstance(data, dict):
        raise MistralError("Critères Mistral invalides.", 502)

    ordering = str(data.get("ordering") or "-rating").strip()
    allowed_ordering = {"-rating", "rating", "-released", "released", "name", "-name", "metacritic", "-metacritic"}
    if ordering not in allowed_ordering:
        ordering = "-rating"

    return {
        "search": str(data.get("search") or "").strip()[:100],
        "genres": _clean_list(data.get("genres")),
        "platforms": _clean_list(data.get("platforms")),
        "tags": _clean_list(data.get("tags")),
        "saga": str(data.get("saga") or "").strip()[:100],
        "ordering": ordering,
        "released_after": _clean_date(data.get("released_after")),
        "released_before": _clean_date(data.get("released_before")),
    }


def recommend_games(message):
    message = (message or "").strip()
    if not message:
        raise MistralError("La demande est vide.", 400)
    if len(message) > 800:
        raise MistralError("La demande est trop longue.", 400)

    system_prompt = """
Tu es GameBot pour un catalogue de jeux vidéo.
Ton rôle est UNIQUEMENT de transformer la demande utilisateur en critères de recherche.
Tu ne dois JAMAIS inventer de jeux.
Réponds uniquement avec un objet JSON valide, sans markdown et sans explication.

Format obligatoire :
{
  "search": "",
  "genres": [],
  "platforms": [],
  "tags": [],
  "saga": "",
  "ordering": "-rating",
  "released_after": "",
  "released_before": ""
}

Règles :
- search = nom du jeu seulement si l'utilisateur recherche un titre précis.
- genres et platforms = valeurs courtes en anglais quand possible.
- saga = nom de la saga uniquement si demandé explicitement ou clairement.
- ordering doit être l'une de : -rating, rating, -released, released, name, -name, metacritic, -metacritic.
- dates au format YYYY-MM-DD, sinon chaîne vide.
- ne complète pas une information qui n'est pas demandée.
""".strip()

    try:
        response = _client().chat.complete(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=500,
        )
    except Exception as exc:
        text = str(exc).lower()
        if "401" in text or "unauthorized" in text:
            raise MistralError("La clé Mistral est invalide ou refusée.", 502) from exc
        if "403" in text or "forbidden" in text:
            raise MistralError("Le modèle Mistral configuré n'est pas disponible avec cette clé.", 403) from exc
        if "429" in text or "rate limit" in text:
            raise MistralError("La limite de requêtes Mistral a été atteinte. Réessayez plus tard.", 429) from exc
        raise MistralError("Mistral est momentanément indisponible.", 502) from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        raise MistralError("Réponse Mistral invalide.", 502) from exc

    if isinstance(content, list):
        content = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )

    criteria = normalize_criteria(_extract_json(str(content)))
    return criteria
