import enum
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text

from .database import Base


class ImportSource(str, enum.Enum):
    search = "search"
    video = "video"


class JobStatus(str, enum.Enum):
    pending = "pending"
    extracting_audio = "extracting_audio"
    transcribing = "transcribing"
    summarizing = "summarizing"
    done = "done"
    error = "error"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    year = Column(String, nullable=True)
    poster_url = Column(String, nullable=True)
    genres = Column(JSON, nullable=True)
    overview = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    summary_source = Column(String, nullable=True)
    source = Column(Enum(ImportSource), nullable=False)
    tmdb_id = Column(Integer, nullable=True)
    video_filename = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    job_status = Column(Enum(JobStatus), default=JobStatus.done, nullable=False)
    job_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
