import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "hej-felai.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_DIM = 400
SETTINGS_SLUG = os.environ.get("HEJ_SLUG", "propell2026")

DEFAULT_SETTINGS = {
    "bg_color": "#0a0a1a",
    "bg_image": "",
    "event_title": "Teknikfrukost",
}
