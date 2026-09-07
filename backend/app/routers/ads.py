import re
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import SessionLocal, get_db
from ..services import captions, heygen, script_writer

router = APIRouter(prefix="/api", tags=["ads"])

POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 900


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", text).strip("_").lower()
    return slug or "pub"


@router.post("/generate-script", response_model=schemas.GenerateScriptResponse)
def generate_script(payload: schemas.GenerateScriptRequest):
    try:
        script = script_writer.generate_script(payload.product_name, payload.product_description)
    except script_writer.ScriptWriterNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except script_writer.ScriptWriterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return schemas.GenerateScriptResponse(script=script)


def _process_ad(ad_id: int) -> None:
    db = SessionLocal()
    try:
        ad = db.get(models.Ad, ad_id)
        if not ad:
            return

        raw_path = config.VIDEOS_DIR / f"{ad_id}_{uuid.uuid4().hex[:8]}_raw.mp4"
        try:
            ad.status = models.AdStatus.generating
            db.commit()
            video_id = heygen.generate_video(ad.script_text, ad.avatar_id, ad.voice_id, ad.aspect)
            ad.heygen_video_id = video_id
            db.commit()

            waited = 0
            video_url = None
            while waited < MAX_WAIT_SECONDS:
                info = heygen.get_video_status(video_id)
                if info["status"] == "completed":
                    video_url = info["video_url"]
                    break
                if info["status"] == "failed":
                    raise heygen.HeyGenError(info.get("error") or "Échec de la génération HeyGen.")
                time.sleep(POLL_INTERVAL_SECONDS)
                waited += POLL_INTERVAL_SECONDS
            if not video_url:
                raise heygen.HeyGenError("Délai dépassé en attendant la génération HeyGen.")

            ad.status = models.AdStatus.downloading
            db.commit()
            heygen.download_video(video_url, raw_path)

            final_path = config.VIDEOS_DIR / f"{ad_id}_final.mp4"
            if ad.captions_enabled:
                ad.status = models.AdStatus.captioning
                db.commit()
                duration = captions.get_duration_seconds(raw_path)
                srt_path = config.VIDEOS_DIR / f"{ad_id}_captions.srt"
                captions.build_srt(ad.script_text, duration, srt_path)
                captions.burn_captions(raw_path, srt_path, final_path)
                srt_path.unlink(missing_ok=True)
                raw_path.unlink(missing_ok=True)
            else:
                raw_path.rename(final_path)

            ad.video_filename = final_path.name
            ad.status = models.AdStatus.done
            ad.error = None
            db.commit()
        except (heygen.HeyGenError, captions.CaptionError) as exc:
            ad.status = models.AdStatus.error
            ad.error = str(exc)
            db.commit()
        except Exception as exc:  # pragma: no cover - safety net
            ad.status = models.AdStatus.error
            ad.error = f"Erreur inattendue : {exc}"
            db.commit()
        finally:
            raw_path.unlink(missing_ok=True)
    finally:
        db.close()


@router.post("/ads", response_model=None)
def create_ad(payload: schemas.CreateAdRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.aspect not in ("vertical", "horizontal"):
        raise HTTPException(status_code=400, detail="Format invalide : vertical ou horizontal.")
    if not payload.script_text.strip():
        raise HTTPException(status_code=400, detail="Le script est requis.")
    if len(payload.script_text) > config.MAX_SCRIPT_CHARS:
        raise HTTPException(status_code=400, detail=f"Script trop long (max {config.MAX_SCRIPT_CHARS} caractères).")
    if not payload.avatar_id or not payload.voice_id:
        raise HTTPException(status_code=400, detail="Un avatar et une voix sont requis.")

    ad = models.Ad(
        product_name=payload.product_name.strip() or "Pub sans nom",
        script_text=payload.script_text.strip(),
        avatar_id=payload.avatar_id,
        voice_id=payload.voice_id,
        aspect=payload.aspect,
        captions_enabled=payload.captions_enabled,
        status=models.AdStatus.pending,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)

    background_tasks.add_task(_process_ad, ad.id)

    return {"id": ad.id, "status": ad.status.value}


@router.get("/ads", response_model=list[schemas.AdListItem])
def list_ads(db: Session = Depends(get_db)):
    return db.query(models.Ad).order_by(models.Ad.created_at.desc()).all()


@router.get("/ads/{ad_id}", response_model=schemas.AdOut)
def get_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pub introuvable")
    return ad


@router.get("/ads/{ad_id}/video")
def download_ad_video(ad_id: int, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pub introuvable")
    if not ad.video_filename:
        raise HTTPException(status_code=404, detail="Cette pub n'a pas encore été générée.")

    path = config.VIDEOS_DIR / ad.video_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier vidéo introuvable sur le disque.")

    download_name = f"{_safe_slug(ad.product_name)}_{ad.aspect}.mp4"
    return FileResponse(path, media_type="video/mp4", filename=download_name)


@router.delete("/ads/{ad_id}", status_code=204)
def delete_ad(ad_id: int, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pub introuvable")

    if ad.video_filename:
        (config.VIDEOS_DIR / ad.video_filename).unlink(missing_ok=True)

    db.delete(ad)
    db.commit()
    return None
