import os
import uuid
import json
from flask import (
    Flask, request, jsonify, render_template,
    send_from_directory, make_response, redirect, url_for
)
from PIL import Image
from config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS, MAX_IMAGE_DIM, SETTINGS_SLUG
from database import init_db, add_checkin, get_checkins, get_settings, update_setting, reset_all

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

COOKIE_NAME = "hej_felai"
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file):
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    img = Image.open(file.stream)
    img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
    if img.mode == "RGBA":
        img = img.convert("RGB")
        filename = filename.rsplit(".", 1)[0] + ".jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
    img.save(filepath, quality=85)
    return filename


# --- Pages ---

@app.route("/")
def index():
    cookie_data = {}
    raw = request.cookies.get(COOKIE_NAME)
    if raw:
        try:
            cookie_data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    settings = get_settings()
    resp = make_response(render_template("index.html", prefill=cookie_data, settings=settings, kiosk=False))
    if raw:
        resp.set_cookie(COOKIE_NAME, raw, max_age=COOKIE_MAX_AGE, samesite="Lax")
    return resp


@app.route("/kiosk")
def kiosk():
    settings = get_settings()
    return render_template("index.html", prefill={}, settings=settings, kiosk=True)


@app.route("/show")
def show():
    settings = get_settings()
    return render_template("show.html", settings=settings)


@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/settings/<slug>")
def settings_page(slug):
    if slug != SETTINGS_SLUG:
        return "Not found", 404
    settings = get_settings()
    return render_template("settings.html", settings=settings, slug=slug)


# --- API ---

@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip()
    link = request.form.get("link", "").strip()
    is_kiosk = request.form.get("kiosk") == "1"

    if not name or not role:
        return jsonify({"error": "Namn och sysselsättning krävs"}), 400

    photo_filename = ""
    if "photo" in request.files:
        file = request.files["photo"]
        if file.filename and allowed_file(file.filename):
            photo_filename = save_photo(file)

    add_checkin(name, role, link, photo_filename)

    resp = jsonify({"ok": True, "name": name})
    if not is_kiosk:
        cookie_val = json.dumps({"name": name, "role": role, "link": link})
        resp.set_cookie(COOKIE_NAME, cookie_val, max_age=COOKIE_MAX_AGE, samesite="Lax")
    return resp


@app.route("/api/checkins")
def api_checkins():
    return jsonify(get_checkins())


@app.route("/api/settings")
def api_settings():
    return jsonify(get_settings())


@app.route("/api/settings/<slug>", methods=["POST"])
def api_update_settings(slug):
    if slug != SETTINGS_SLUG:
        return "Not found", 404
    data = request.get_json() or {}
    for key in ("bg_color", "bg_image", "event_title"):
        if key in data:
            update_setting(key, data[key])
    return jsonify(get_settings())


@app.route("/api/reset/<slug>", methods=["POST"])
def api_reset(slug):
    if slug != SETTINGS_SLUG:
        return "Not found", 404
    reset_all()
    return jsonify({"ok": True})


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=8110, debug=True)
