import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import config, models
from ..database import SessionLocal, get_db
from ..services import summarizer, transcription

router = APIRouter(prefix="/api/import", tags=["import"])

ALLOWED_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^\w\-]+", "_", stem).strip("_")
    return stem or "video"


def _process_video(movie_id: int, video_path: Path, audio_path: Path) -> None:
    db = SessionLocal()
    try:
        movie = db.get(models.Movie, movie_id)
        if not movie:
            return
        try:
            movie.job_status = models.JobStatus.extracting_audio
            db.commit()
            transcription.extract_audio(video_path, audio_path)

            movie.job_status = models.JobStatus.transcribing
            db.commit()
            transcript = transcription.transcribe_audio(audio_path)
            movie.transcript = transcript

            movie.job_status = models.JobStatus.summarizing
            db.commit()
            summary, summary_source = summarizer.generate_summary(transcript, movie.title)
            movie.summary = summary
            movie.summary_source = summary_source
            movie.job_status = models.JobStatus.done
            db.commit()
        except transcription.TranscriptionError as exc:
            movie.job_status = models.JobStatus.error
            movie.job_error = str(exc)
            db.commit()
        except Exception as exc:  # pragma: no cover - safety net for unexpected failures
            movie.job_status = models.JobStatus.error
            movie.job_error = f"Erreur inattendue: {exc}"
            db.commit()
        finally:
            audio_path.unlink(missing_ok=True)
    finally:
        db.close()


@router.post("/video", response_model=None)
async def import_video(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    db: Session = Depends(get_db),
):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée ({extension}). Formats acceptés: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    unique_id = uuid.uuid4().hex[:8]
    stored_filename = f"{_safe_stem(file.filename or 'video')}_{unique_id}{extension}"
    video_path = config.VIDEOS_DIR / stored_filename
    audio_path = config.AUDIO_DIR / f"{stored_filename}.wav"

    size = 0
    try:
        with open(video_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > config.MAX_UPLOAD_SIZE_BYTES:
                    out_file.close()
                    video_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Fichier trop volumineux (max {config.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} Mo)",
                    )
                out_file.write(chunk)
    finally:
        await file.close()

    title_guess = _safe_stem(file.filename or "Film importé").replace("_", " ").strip() or "Film importé"

    movie = models.Movie(
        title=title_guess,
        source=models.ImportSource.video,
        video_filename=stored_filename,
        job_status=models.JobStatus.pending,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)

    background_tasks.add_task(_process_video, movie.id, video_path, audio_path)

    return {"id": movie.id, "job_status": movie.job_status.value}
