from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TmdbSearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: Optional[str] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None


class ImportFromSearchRequest(BaseModel):
    tmdb_id: int


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: Optional[str] = None
    poster_url: Optional[str] = None
    genres: Optional[list[str]] = None
    overview: Optional[str] = None
    summary: Optional[str] = None
    summary_source: Optional[str] = None
    source: str
    tmdb_id: Optional[int] = None
    video_filename: Optional[str] = None
    job_status: str
    job_error: Optional[str] = None
    created_at: datetime


class MovieListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: Optional[str] = None
    poster_url: Optional[str] = None
    summary: Optional[str] = None
    source: str
    job_status: str
    created_at: datetime
