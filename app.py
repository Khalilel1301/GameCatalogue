import json
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)

from utils.mistral import (
    MistralError,
    recommend_games,
)
from utils.rawg import (
    RAWGError,
    get_game,
    get_games,
    get_screenshots,
)
from utils.youtube import (
    YouTubeError,
    search_trailer,
)


load_dotenv()


app = Flask(
    __name__,
)

app.config[
    "JSON_SORT_KEYS"
] = False


MAX_QUERY_LENGTH = 100
MAX_RECOMMENDATION_LENGTH = 800

DATA_DIR = (
    Path(__file__).resolve().parent
    / "data"
)

FAVORITES_FILE = (
    DATA_DIR
    / "favorites.json"
)


# ==========================================================
# FAVORIS
# ==========================================================

def _ensure_favorites_file():
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not FAVORITES_FILE.exists():
        FAVORITES_FILE.write_text(
            json.dumps(
                {
                    "favorites": []
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def _load_favorites():
    _ensure_favorites_file()

    try:
        data = json.loads(
            FAVORITES_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []


    if not isinstance(
        data,
        dict,
    ):
        return []

    favorites = data.get(
        "favorites",
        [],
    )

    return (
        favorites
        if isinstance(
            favorites,
            list,
        )
        else []
    )


def _save_favorites(favorites):
    _ensure_favorites_file()

    FAVORITES_FILE.write_text(
        json.dumps(
            {
                "favorites": favorites
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _favorite_payload_is_valid(payload):
    if not isinstance(
        payload,
        dict,
    ):
        return False

    try:
        int(
            payload.get(
                "id"
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    name = payload.get(
        "name"
    )

    return isinstance(
        name,
        str,
    ) and bool(
        name.strip()
    )


def _clean_favorite(payload):
    game_id = int(
        payload.get(
            "id"
        )
    )

    name = str(
        payload.get(
            "name",
            "Information non disponible",
        )
    ).strip()

    slug = str(
        payload.get(
            "slug",
            "",
        )
    ).strip()

    image = str(
        payload.get(
            "image"
            or payload.get(
                "background_image",
                "",
            ),
        )
        or ""
    ).strip()

    rating = payload.get(
        "rating"
    )

    released = payload.get(
        "released"
    )

    genres = payload.get(
        "genres"
    )

    if not isinstance(
        genres,
        list,
    ):
        genres = []

    return {
        "id": game_id,
        "name": name,
        "slug": slug,
        "image": image,
        "background_image": image,
        "rating": rating,
        "released": released,
        "genres": genres,
    }


# ==========================================================
# UTILITAIRES
# ==========================================================

def _error_response(message, status=500):
    return (
        jsonify(
            {
                "error": message
            }
        ),
        status,
    )


def _safe_external_url(value):
    if not value:
        return ""

    try:
        parsed = urlparse(
            str(value)
        )
    except Exception:
        return ""

    if parsed.scheme not in (
        "http",
        "https",
    ):
        return ""

    return str(value)


# ==========================================================
# PAGE PRINCIPALE
# ==========================================================

@app.get("/")
def index():
    return render_template(
        "index.html"
    )


# ==========================================================
# GAMES
# ==========================================================

@app.get("/api/games")
def api_games():

    search = (
        request.args.get(
            "search",
            "",
        )
        .strip()
    )

    if len(search) > MAX_QUERY_LENGTH:
        return _error_response(
            "Recherche trop longue.",
            400,
        )

    genre = (
        request.args.get(
            "genre",
            "",
        )
        .strip()
    )

    platform = (
        request.args.get(
            "platform",
            "",
        )
        .strip()
    )

    saga = (
        request.args.get(
            "saga",
            "",
        )
        .strip()
    )

    ordering = (
        request.args.get(
            "ordering",
            "-rating",
        )
        .strip()
    )

    released_after = (
        request.args.get(
            "released_after",
            "",
        )
        .strip()
    )

    released_before = (
        request.args.get(
            "released_before",
            "",
        )
        .strip()
    )

    page = request.args.get(
        "page",
        1,
        type=int,
    )

    page_size = request.args.get(
        "page_size",
        20,
        type=int,
    )

    try:
        data = get_games(
            page=page,
            page_size=page_size,
            search=search,
            genre=genre,
            platform=platform,
            saga=saga,
            ordering=ordering,
            released_after=released_after,
            released_before=released_before,
        )

        return jsonify(
            data
        )

    except RAWGError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except Exception as exc:
        app.logger.exception(
            "Erreur /api/games"
        )

        return _error_response(
            f"Erreur interne : {exc}",
            500,
        )


# ==========================================================
# GAME DETAIL
# ==========================================================

@app.get("/api/games/<int:game_id>")
def api_game_detail(
    game_id,
):

    try:
        return jsonify(
            get_game(
                game_id
            )
        )

    except RAWGError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except Exception as exc:
        app.logger.exception(
            "Erreur détail jeu"
        )

        return _error_response(
            f"Erreur interne : {exc}",
            500,
        )


# ==========================================================
# SCREENSHOTS
# ==========================================================

@app.get(
    "/api/games/<int:game_id>/screenshots"
)
def api_game_screenshots(
    game_id,
):

    try:
        return jsonify(
            get_screenshots(
                game_id
            )
        )

    except RAWGError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except Exception as exc:
        app.logger.exception(
            "Erreur screenshots"
        )

        return _error_response(
            f"Erreur interne : {exc}",
            500,
        )


# ==========================================================
# YOUTUBE TRAILER
# ==========================================================

@app.get("/api/trailer")
def api_trailer():

    game_name = (
        request.args.get(
            "game",
            "",
        )
        .strip()
    )

    if not game_name:
        return _error_response(
            "Nom du jeu manquant.",
            400,
        )

    if len(game_name) > MAX_QUERY_LENGTH:
        return _error_response(
            "Nom du jeu trop long.",
            400,
        )

    try:
        trailer = search_trailer(
            game_name
        )

        return jsonify(
            {
                "trailer": trailer
            }
        )

    except YouTubeError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except Exception as exc:
        app.logger.exception(
            "Erreur YouTube"
        )

        return _error_response(
            f"Erreur YouTube : {exc}",
            502,
        )


# ==========================================================
# FAVORITES - GET
# ==========================================================

@app.get("/api/favorites")
def api_favorites_get():
    return jsonify(
        {
            "favorites": _load_favorites()
        }
    )


# ==========================================================
# FAVORITES - ADD
# ==========================================================

@app.post("/api/favorites")
def api_favorites_add():

    payload = request.get_json(
        silent=True
    )

    if not _favorite_payload_is_valid(
        payload
    ):
        return _error_response(
            "Données de favori invalides.",
            400,
        )

    favorite = _clean_favorite(
        payload
    )

    favorites = _load_favorites()

    favorites = [
        item
        for item in favorites
        if str(
            item.get("id")
        )
        != str(
            favorite["id"]
        )
    ]

    favorites.insert(
        0,
        favorite,
    )

    _save_favorites(
        favorites
    )

    return jsonify(
        {
            "favorites": favorites
        }
    )


# ==========================================================
# FAVORITES - DELETE ONE
# ==========================================================

@app.delete(
    "/api/favorites/<int:game_id>"
)
def api_favorites_delete(
    game_id,
):

    favorites = _load_favorites()

    favorites = [
        item
        for item in favorites
        if str(
            item.get("id")
        )
        != str(game_id)
    ]

    _save_favorites(
        favorites
    )

    return jsonify(
        {
            "favorites": favorites
        }
    )


# ==========================================================
# FAVORITES - DELETE ALL
# ==========================================================

@app.delete("/api/favorites")
def api_favorites_delete_all():

    _save_favorites([])

    return jsonify(
        {
            "favorites": []
        }
    )


# ==========================================================
# MISTRAL GAMEBOT
# ==========================================================

@app.post("/api/recommend")
def api_recommend():

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        return _error_response(
            "Requête invalide.",
            400,
        )

    message = str(
        payload.get(
            "message",
            "",
        )
    ).strip()

    if not message:
        return _error_response(
            "Message manquant.",
            400,
        )

    if len(message) > MAX_RECOMMENDATION_LENGTH:
        return _error_response(
            "Message trop long.",
            400,
        )

    try:
        recommendation = recommend_games(
            message
        )

        # Le module Mistral du projet peut déjà
        # renvoyer une réponse complète.
        if isinstance(
            recommendation,
            dict,
        ):

            criteria = recommendation.get(
                "criteria"
            )

            results = recommendation.get(
                "results"
            )

            response_message = recommendation.get(
                "message"
            )

            if (
                criteria is not None
                and results is not None
            ):
                return jsonify(
                    {
                        "message": (
                            response_message
                            or "Voici les résultats correspondant à ta demande."
                        ),
                        "criteria": criteria,
                        "results": (
                            results
                            if isinstance(
                                results,
                                list,
                            )
                            else []
                        ),
                    }
                )

            # Certains modules peuvent renvoyer
            # directement les critères.
            if criteria is None:
                criteria = recommendation

        else:
            criteria = {}

        if not isinstance(
            criteria,
            dict,
        ):
            criteria = {}

        search = str(
            criteria.get(
                "search",
                "",
            )
            or ""
        ).strip()

        genres = criteria.get(
            "genres",
            [],
        )

        platforms = criteria.get(
            "platforms",
            [],
        )

        tags = criteria.get(
            "tags",
            [],
        )

        ordering = str(
            criteria.get(
                "ordering",
                "-rating",
            )
            or "-rating"
        )

        released_after = str(
            criteria.get(
                "released_after",
                "",
            )
            or ""
        )

        released_before = str(
            criteria.get(
                "released_before",
                "",
            )
            or ""
        )

        genre = (
            genres[0]
            if isinstance(
                genres,
                list,
            )
            and genres
            else ""
        )

        platform = (
            platforms[0]
            if isinstance(
                platforms,
                list,
            )
            and platforms
            else ""
        )

        # Les tags restent disponibles dans la structure
        # mais RAWG ne reçoit que les critères réellement
        # supportés par le moteur actuel.
        del tags

        data = get_games(
            page=1,
            page_size=8,
            search=search,
            genre=genre,
            platform=platform,
            ordering=ordering,
            released_after=released_after,
            released_before=released_before,
        )

        response_criteria = {
            "search": search,
            "genres": (
                genres
                if isinstance(
                    genres,
                    list,
                )
                else []
            ),
            "platforms": (
                platforms
                if isinstance(
                    platforms,
                    list,
                )
                else []
            ),
            "tags": (
                criteria.get(
                    "tags",
                    [],
                )
                if isinstance(
                    criteria.get(
                        "tags",
                        [],
                    ),
                    list,
                )
                else []
            ),
            "ordering": ordering,
            "released_after": released_after,
            "released_before": released_before,
        }

        return jsonify(
            {
                "message": (
                    "Voici les jeux correspondant aux critères compris par GameBot."
                ),
                "criteria": response_criteria,
                "results": data.get(
                    "results",
                    [],
                ),
            }
        )

    except MistralError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except RAWGError as exc:
        return _error_response(
            str(exc),
            getattr(
                exc,
                "status_code",
                502,
            ),
        )

    except Exception as exc:
        app.logger.exception(
            "Erreur GameBot"
        )

        return _error_response(
            f"Erreur GameBot : {exc}",
            502,
        )


# ==========================================================
# ERREURS
# ==========================================================

@app.errorhandler(
    404
)
def handle_404(
    error,
):
    return _error_response(
        "Route introuvable.",
        404,
    )


@app.errorhandler(
    500
)
def handle_500(
    error,
):
    app.logger.exception(
        "Erreur Flask 500"
    )

    return _error_response(
        "Erreur interne du serveur.",
        500,
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    _ensure_favorites_file()

    port = int(
        os.getenv(
            "PORT",
            "5000",
        )
    )

    app.run(
        host="127.0.0.1",
        port=port,
        debug=True,
    )