import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
AUDIO_DIR = DATA_DIR / "audio"
RECAPS_DIR = DATA_DIR / "recaps"
STORY_IMAGES_DIR = DATA_DIR / "story_images"
STORY_VIDEOS_DIR = DATA_DIR / "story_videos"
DB_PATH = DATA_DIR / "mansa.db"

for directory in (DATA_DIR, VIDEOS_DIR, AUDIO_DIR, RECAPS_DIR, STORY_IMAGES_DIR, STORY_VIDEOS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_MB", "3000")) * 1024 * 1024

TTS_VOICE = os.getenv("TTS_VOICE", "fr-FR-DeniseNeural")
RECAP_CLIP_SECONDS = float(os.getenv("RECAP_CLIP_SECONDS", "4"))
