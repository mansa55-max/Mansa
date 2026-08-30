import httpx

from .. import config


class TmdbError(Exception):
    pass


class TmdbNotConfiguredError(TmdbError):
    pass


def _client() -> httpx.Client:
    if not config.TMDB_API_KEY:
        raise TmdbNotConfiguredError(
            "TMDB_API_KEY manquant. Ajoute-le dans le fichier .env pour activer la recherche de films."
        )
    return httpx.Client(
        base_url=config.TMDB_BASE_URL,
        params={"api_key": config.TMDB_API_KEY, "language": "fr-FR"},
        timeout=15.0,
    )


def _poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{config.TMDB_IMAGE_BASE_URL}{poster_path}"


def search_movies(query: str) -> list[dict]:
    with _client() as client:
        response = client.get("/search/movie", params={"query": query})
        response.raise_for_status()
        data = response.json()

    results = []
    for item in data.get("results", [])[:10]:
        release_date = item.get("release_date") or ""
        results.append(
            {
                "tmdb_id": item["id"],
                "title": item.get("title") or item.get("original_title") or "Sans titre",
                "year": release_date[:4] if release_date else None,
                "poster_url": _poster_url(item.get("poster_path")),
                "overview": item.get("overview") or None,
            }
        )
    return results


def get_movie_details(tmdb_id: int) -> dict:
    with _client() as client:
        response = client.get(f"/movie/{tmdb_id}")
        if response.status_code == 404:
            raise TmdbError(f"Film TMDB introuvable (id={tmdb_id})")
        response.raise_for_status()
        data = response.json()

    release_date = data.get("release_date") or ""
    return {
        "tmdb_id": data["id"],
        "title": data.get("title") or data.get("original_title") or "Sans titre",
        "year": release_date[:4] if release_date else None,
        "poster_url": _poster_url(data.get("poster_path")),
        "genres": [g["name"] for g in data.get("genres", [])],
        "overview": data.get("overview") or None,
    }
