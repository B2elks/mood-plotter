import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "verify.db")

ELKS_USERNAME = os.environ.get("ELKS_USERNAME", "")
ELKS_PASSWORD = os.environ.get("ELKS_PASSWORD", "")
ELKS_NUMBER = os.environ.get("ELKS_NUMBER", "")
VERIFY_SECRET = os.environ.get("VERIFY_SECRET", "felai-verify-2026")

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 5
CODE_EXPIRY_MINUTES = 10
KNOWN_NUMBER_DAYS = 90

BASE_URL = os.environ.get("BASE_URL", "https://felai.se")
