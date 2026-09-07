from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401 - registers models with Base metadata
from .database import Base, engine
from .routers import ads, options

Base.metadata.create_all(bind=engine)

app = FastAPI(title="UGC Ads Studio")

app.include_router(options.router)
app.include_router(ads.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
