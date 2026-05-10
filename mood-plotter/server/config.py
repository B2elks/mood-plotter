"""Server-konfiguration läses från env-variabler / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ELKS_API_USERNAME = os.environ["ELKS_API_USERNAME"]
ELKS_API_PASSWORD = os.environ["ELKS_API_PASSWORD"]
ELKS_FROM_NUMBER = os.environ["ELKS_FROM_NUMBER"]
USER_PHONE_NUMBER = os.environ["USER_PHONE_NUMBER"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.environ["ELEVENLABS_VOICE_ID"]

SERVER_PUBLIC_URL = os.environ["SERVER_PUBLIC_URL"].rstrip("/")
PI_TOKEN = os.environ["PI_TOKEN"]
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "300"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

PORT = int(os.environ.get("PORT", "8095"))

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
COOLDOWN_DB = BASE_DIR / "cooldown.db"
