from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models
from .database import Base, engine, run_light_migrations
from .routers import import_video, movies, recap, search, story

Base.metadata.create_all(bind=engine)
run_light_migrations()

app = FastAPI(title="Mansa - Import & Résumé de films")

app.include_router(search.router)
app.include_router(movies.router)
app.include_router(import_video.router)
app.include_router(recap.router)
app.include_router(story.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
