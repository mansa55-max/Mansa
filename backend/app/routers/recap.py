import re
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import SessionLocal, get_db
from ..services import recap, tts

router = APIRouter(prefix="/api/movies", tags=["recap"])

VALID_FORMATS = {"vertical", "horizontal"}


def _safe_slug(title: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", title).strip("_").lower()
    return slug or "film"


def _process_recap(movie_id: int, formats: list[str]) -> None:
    db = SessionLocal()
    try:
        movie = db.get(models.Movie, movie_id)
        if not movie:
            return

        narration_path = config.RECAPS_DIR / f"{movie_id}_narration.mp3"
        srt_path = config.RECAPS_DIR / f"{movie_id}_captions.srt"
        source_video = config.VIDEOS_DIR / movie.video_filename

        try:
            movie.recap_status = models.RecapStatus.narrating
            db.commit()
            duration = tts.generate_narration(movie.summary or "", narration_path, srt_path)

            movie.recap_status = models.RecapStatus.assembling
            db.commit()
            for fmt in formats:
                out_path = config.RECAPS_DIR / f"{movie_id}_{fmt}.mp4"
                recap.build_recap_video(source_video, narration_path, srt_path, duration, fmt, out_path)
                if fmt == "vertical":
                    movie.recap_vertical_filename = out_path.name
                else:
                    movie.recap_horizontal_filename = out_path.name
                db.commit()

            movie.recap_status = models.RecapStatus.done
            movie.recap_error = None
            db.commit()
        except (tts.TtsError, recap.RecapError) as exc:
            movie.recap_status = models.RecapStatus.error
            movie.recap_error = str(exc)
            db.commit()
        except Exception as exc:  # pragma: no cover - safety net
            movie.recap_status = models.RecapStatus.error
            movie.recap_error = f"Erreur inattendue : {exc}"
            db.commit()
        finally:
            narration_path.unlink(missing_ok=True)
            srt_path.unlink(missing_ok=True)
    finally:
        db.close()


@router.post("/{movie_id}/recap", response_model=None)
def generate_recap(
    movie_id: int,
    payload: schemas.RecapRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    movie = db.get(models.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film introuvable")
    if movie.source != models.ImportSource.video or not movie.video_filename:
        raise HTTPException(
            status_code=400,
            detail="La génération de vidéo résumé n'est disponible que pour un film importé via un fichier vidéo.",
        )
    if not (config.VIDEOS_DIR / movie.video_filename).exists():
        raise HTTPException(status_code=404, detail="Le fichier vidéo original est introuvable sur le disque.")
    if movie.job_status != models.JobStatus.done or not movie.summary:
        raise HTTPException(
            status_code=400,
            detail="Le résumé du film doit être prêt avant de générer une vidéo résumé.",
        )

    formats = [f for f in payload.formats if f in VALID_FORMATS]
    if not formats:
        raise HTTPException(status_code=400, detail=f"Formats valides : {', '.join(sorted(VALID_FORMATS))}")

    movie.recap_status = models.RecapStatus.pending
    movie.recap_error = None
    for fmt in formats:
        if fmt == "vertical":
            movie.recap_vertical_filename = None
        else:
            movie.recap_horizontal_filename = None
    db.commit()

    background_tasks.add_task(_process_recap, movie.id, formats)

    return {"id": movie.id, "recap_status": movie.recap_status.value}


@router.get("/{movie_id}/recap/{fmt}")
def download_recap(movie_id: int, fmt: str, db: Session = Depends(get_db)):
    if fmt not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Formats valides : {', '.join(sorted(VALID_FORMATS))}")

    movie = db.get(models.Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film introuvable")

    filename = movie.recap_vertical_filename if fmt == "vertical" else movie.recap_horizontal_filename
    if not filename:
        raise HTTPException(status_code=404, detail="Cette vidéo résumé n'a pas encore été générée.")

    path = config.RECAPS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo introuvable sur le disque.")

    download_name = f"{_safe_slug(movie.title)}_{fmt}.mp4"
    return FileResponse(path, media_type="video/mp4", filename=download_name)
