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
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "300"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
# Tillåt samtal även när ingen plotter är ansluten via WS (för server-only-läge).
ALLOW_NO_PLOTTER = os.environ.get("ALLOW_NO_PLOTTER", "false").lower() == "true"

# 46elks WS-anslutet "voice number" som routar samtalet till var WS-handler.
# Konfigureras via 46elks API: numrets ws_url ska peka pa ws://server:PORT/ws-voice
WS_CONNECT_NUMBER = os.environ.get("WS_CONNECT_NUMBER", "")

PORT = int(os.environ.get("PORT", "8095"))
# Separat port for raw WS-trafik fran 46elks (utanfor nginx).
WS_VOICE_PORT = int(os.environ.get("WS_VOICE_PORT", "8121"))

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
CARDS_DIR = BASE_DIR / "cards"
COOLDOWN_DB = BASE_DIR / "cooldown.db"
PHONE_STATE = BASE_DIR / "phone_state.json"
PIR_STATE = BASE_DIR / "pir_state.json"
MODE_STATE = BASE_DIR / "mode_state.json"
