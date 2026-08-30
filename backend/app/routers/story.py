import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import SessionLocal, get_db
from ..services import storyvideo, tts

router = APIRouter(prefix="/api/story-videos", tags=["story"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES = 30
VALID_FORMATS = {"vertical", "horizontal"}


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", text).strip("_").lower()
    return slug or "story"


async def _save_upload(file: UploadFile, out_path: Path) -> None:
    size = 0
    with open(out_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > config.MAX_UPLOAD_SIZE_BYTES:
                out_file.close()
                out_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Image trop volumineuse (max {config.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} Mo)",
                )
            out_file.write(chunk)
    await file.close()


def _process_story_video(story_id: int, formats: list[str]) -> None:
    db = SessionLocal()
    try:
        story = db.get(models.StoryVideo, story_id)
        if not story:
            return

        narration_path = config.STORY_VIDEOS_DIR / f"{story_id}_narration.mp3"
        srt_path = config.STORY_VIDEOS_DIR / f"{story_id}_captions.srt"
        image_paths = [config.STORY_IMAGES_DIR / name for name in story.image_filenames]

        try:
            story.status = models.StoryVideoStatus.narrating
            db.commit()
            duration = tts.generate_narration(story.story_text, narration_path, srt_path)

            story.status = models.StoryVideoStatus.assembling
            db.commit()
            for fmt in formats:
                out_path = config.STORY_VIDEOS_DIR / f"{story_id}_{fmt}.mp4"
                storyvideo.build_story_video(image_paths, narration_path, srt_path, duration, fmt, out_path)
                if fmt == "vertical":
                    story.vertical_filename = out_path.name
                else:
                    story.horizontal_filename = out_path.name
                db.commit()

            story.status = models.StoryVideoStatus.done
            story.error = None
            db.commit()
        except (tts.TtsError, storyvideo.StoryVideoError) as exc:
            story.status = models.StoryVideoStatus.error
            story.error = str(exc)
            db.commit()
        except Exception as exc:  # pragma: no cover - safety net
            story.status = models.StoryVideoStatus.error
            story.error = f"Erreur inattendue : {exc}"
            db.commit()
        finally:
            narration_path.unlink(missing_ok=True)
            srt_path.unlink(missing_ok=True)
    finally:
        db.close()


@router.post("", response_model=None)
async def create_story_video(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    story: str = Form(...),
    formats: str = Form("vertical,horizontal"),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    if not story.strip():
        raise HTTPException(status_code=400, detail="Le texte de l'histoire est requis.")
    if not images:
        raise HTTPException(status_code=400, detail="Au moins une image est requise.")
    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_IMAGES} images.")

    requested_formats = [f.strip() for f in formats.split(",") if f.strip()]
    selected_formats = [f for f in requested_formats if f in VALID_FORMATS]
    if not selected_formats:
        raise HTTPException(status_code=400, detail=f"Formats valides : {', '.join(sorted(VALID_FORMATS))}")

    saved_filenames = []
    for image in images:
        extension = Path(image.filename or "").suffix.lower()
        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extension d'image non supportée ({extension}). "
                f"Formats acceptés : {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
            )
        unique_id = uuid.uuid4().hex[:8]
        stored_filename = f"{_safe_slug(Path(image.filename or 'image').stem)}_{unique_id}{extension}"
        await _save_upload(image, config.STORY_IMAGES_DIR / stored_filename)
        saved_filenames.append(stored_filename)

    story_row = models.StoryVideo(
        title=title.strip() or "Histoire sans titre",
        story_text=story.strip(),
        image_filenames=saved_filenames,
        status=models.StoryVideoStatus.pending,
    )
    db.add(story_row)
    db.commit()
    db.refresh(story_row)

    background_tasks.add_task(_process_story_video, story_row.id, selected_formats)

    return {"id": story_row.id, "status": story_row.status.value}


@router.get("", response_model=list[schemas.StoryVideoListItem])
def list_story_videos(db: Session = Depends(get_db)):
    return db.query(models.StoryVideo).order_by(models.StoryVideo.created_at.desc()).all()


@router.get("/{story_id}", response_model=schemas.StoryVideoOut)
def get_story_video(story_id: int, db: Session = Depends(get_db)):
    story = db.get(models.StoryVideo, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return story


@router.get("/{story_id}/video/{fmt}")
def download_story_video(story_id: int, fmt: str, db: Session = Depends(get_db)):
    if fmt not in VALID_FORMATS:
        raise HTTPException(status_code=400, detail=f"Formats valides : {', '.join(sorted(VALID_FORMATS))}")

    story = db.get(models.StoryVideo, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    filename = story.vertical_filename if fmt == "vertical" else story.horizontal_filename
    if not filename:
        raise HTTPException(status_code=404, detail="Cette vidéo n'a pas encore été générée.")

    path = config.STORY_VIDEOS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo introuvable sur le disque.")

    download_name = f"{_safe_slug(story.title)}_{fmt}.mp4"
    return FileResponse(path, media_type="video/mp4", filename=download_name)


@router.delete("/{story_id}", status_code=204)
def delete_story_video(story_id: int, db: Session = Depends(get_db)):
    story = db.get(models.StoryVideo, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    for name in story.image_filenames or []:
        (config.STORY_IMAGES_DIR / name).unlink(missing_ok=True)
    if story.vertical_filename:
        (config.STORY_VIDEOS_DIR / story.vertical_filename).unlink(missing_ok=True)
    if story.horizontal_filename:
        (config.STORY_VIDEOS_DIR / story.horizontal_filename).unlink(missing_ok=True)

    db.delete(story)
    db.commit()
    return None
