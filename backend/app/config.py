import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = DATA_DIR / "videos"
DB_PATH = DATA_DIR / "ugc_ads.db"

for directory in (DATA_DIR, VIDEOS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_BASE_URL = "https://api.heygen.com"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

MAX_SCRIPT_CHARS = 1200
