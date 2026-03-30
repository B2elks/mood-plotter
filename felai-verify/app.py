import os
import uuid
import random
import io
import logging
from threading import Thread

import requests as http_requests
import qrcode
import qrcode.image.svg
from flask import Flask, request, jsonify, render_template, abort

from config import (
    ELKS_NUMBER, VERIFY_SECRET, CODE_ALPHABET, CODE_LENGTH,
    CODE_EXPIRY_MINUTES, BASE_URL,
)
from database import (
    init_db, create_verification, get_verification,
    find_pending_by_code, mark_verified, upsert_known_number, lookup_number,
)

app = Flask(__name__)
logger = logging.getLogger(__name__)


def generate_code():
    return "".join(random.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalize_phone(phone):
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+46" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+" + phone
    return phone


def format_phone_display(phone):
    if phone.startswith("+46") and len(phone) == 12:
        return f"+46 {phone[3:5]} {phone[5:8]} {phone[8:12]}"
    return phone


def check_auth():
    auth = request.headers.get("Authorization", "")
    if auth == f"Bearer {VERIFY_SECRET}":
        return True
    return False


def send_callback(url, data):
    try:
        http_requests.post(url, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Callback failed to {url}: {e}")


# --- API ---

@app.route("/api/verify", methods=["POST"])
def api_create_verify():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    callback_url = data.get("callback_url", "").strip()

    if not name or not phone:
        return jsonify({"error": "name and phone required"}), 400

    phone = normalize_phone(phone)
    vid = uuid.uuid4().hex[:16]
    code = generate_code()

    create_verification(vid, code, phone, name, callback_url)

    return jsonify({
        "id": vid,
        "status": "pending",
        "verify_url": f"{BASE_URL}/verify/{vid}",
        "code": code,
        "sms_number": ELKS_NUMBER,
    })


@app.route("/api/verify/<vid>")
def api_get_verify(vid):
    v = get_verification(vid)
    if not v:
        return jsonify({"error": "Not found"}), 404

    # Lazy expiry
    from datetime import datetime, timedelta
    created = datetime.strptime(v["created_at"], "%Y-%m-%d %H:%M:%S")
    if v["status"] == "pending" and datetime.utcnow() - created > timedelta(minutes=CODE_EXPIRY_MINUTES):
        v["status"] = "expired"

    return jsonify({
        "id": v["id"],
        "status": v["status"],
        "name": v["name"],
        "phone": v["phone"],
        "verified_at": v["verified_at"],
    })


@app.route("/sms/incoming", methods=["POST"])
def sms_incoming():
    sender = request.form.get("from", "")
    message = request.form.get("message", "").strip().upper()

    if not sender or not message:
        return "", 200

    code = message.strip()
    v = find_pending_by_code(code)

    if not v:
        logger.info(f"No matching verification for code '{code}' from {sender}")
        return "", 200

    verified_at = mark_verified(v["id"])
    upsert_known_number(v["phone"], v["name"])
    logger.info(f"Verified {v['name']} ({v['phone']}) with code {code}")

    if v["callback_url"]:
        callback_data = {
            "id": v["id"],
            "status": "verified",
            "name": v["name"],
            "phone": v["phone"],
            "verified_at": verified_at,
        }
        Thread(target=send_callback, args=(v["callback_url"], callback_data), daemon=True).start()

    return "", 200


@app.route("/api/lookup/<path:phone>")
def api_lookup(phone):
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    phone = normalize_phone(phone)
    result = lookup_number(phone)
    if not result:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "phone": result["phone"],
        "name": result["name"],
        "verified_at": result["verified_at"],
        "expires_at": result["expires_at"],
    })


@app.route("/api/qr")
def api_qr():
    text = request.args.get("text", "")
    if not text:
        return "Missing text param", 400
    img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathFillImage)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return buf.getvalue(), 200, {"Content-Type": "image/svg+xml"}


# --- Pages ---

@app.route("/verify/<vid>")
def verify_page(vid):
    v = get_verification(vid)
    if not v:
        abort(404)

    sms_uri = f"sms:{ELKS_NUMBER}?body={v['code']}"
    phone_display = format_phone_display(ELKS_NUMBER)

    return render_template("verify.html",
        verification=v,
        sms_uri=sms_uri,
        phone_display=phone_display,
        vid=vid,
    )


@app.route("/")
def index():
    return jsonify({"service": "felai.se SMS Verify", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=8111, debug=True)
