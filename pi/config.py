"""Pi-klient-konfiguration."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SERVER_URL = os.environ["SERVER_URL"].rstrip("/")
SERVER_WS_URL = os.environ["SERVER_WS_URL"]
PI_TOKEN = os.environ["PI_TOKEN"]
PI_ID = os.environ.get("PI_ID", "desk1")

PIR_GPIO_PIN = int(os.environ.get("PIR_GPIO_PIN", "4"))
PIR_DEBOUNCE_SECONDS = int(os.environ.get("PIR_DEBOUNCE_SECONDS", "30"))

AXIDRAW_PEN_POS_DOWN = int(os.environ.get("AXIDRAW_PEN_POS_DOWN", "40"))
AXIDRAW_PEN_POS_UP = int(os.environ.get("AXIDRAW_PEN_POS_UP", "60"))
AXIDRAW_SPEED_PENDOWN = int(os.environ.get("AXIDRAW_SPEED_PENDOWN", "25"))
