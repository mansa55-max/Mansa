from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import summarizer, tmdb

router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.post("/import-from-search", response_model=schemas.MovieOut)
def import_from_search(payload: schemas.ImportFromSearchRequest, db: Session = Depends(get_db)):
    try:
        details = tmdb.get_movie_details(payload.tmdb_id)
    except tmdb.TmdbNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except tmdb.TmdbError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    summary, summary_source = summarizer.generate_summary(details.get("overview") or "", details.get("title"))

    movie = models.Movie(
        title=details["title"],
        year=details.get("year"),
        poster_url=details.get("poster_url"),
        genres=details.get("genres"),
        overview=details.get("overview"),
        summary=summary or details.get("overview"),
        summary_source=summary_source,
        source=models.ImportSource.search,
        tmdb_id=details["tmdb_id"],
        job_status=models.JobStatus.done,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@router.get("", response_model=list[schemas.MovieListItem])
def list_movies(db: Session = Depends(get_db)):
    return db.query(models.Movie).order_by(models.Movie.created_at.desc()).all()


@router.get("/{movie_id}", response_model=schemas.MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(models.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film introuvable")
    return movie


@router.delete("/{movie_id}", status_code=204)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(models.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film introuvable")
    db.delete(movie)
    db.commit()
    return None
