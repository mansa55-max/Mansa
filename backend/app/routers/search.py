from fastapi import APIRouter, HTTPException, Query

from ..services import tmdb

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_movies(q: str = Query(..., min_length=1)):
    try:
        return tmdb.search_movies(q)
    except tmdb.TmdbNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except tmdb.TmdbError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
