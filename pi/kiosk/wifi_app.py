"""Local Flask-app pa Pi:n.

- Visar WiFi-setup om ingen anslutning
- Annars embed:ar mood-plotter-galleriet + en knapp att trigga samtal direkt
- Inställningsmeny dar man kan byta telefonnummer (proxas till servern)
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

SERVER_URL = os.environ.get("SERVER_URL", "https://moodplotter.skyttberg.nu").rstrip("/")
GALLERY_URL = os.environ.get("GALLERY_URL", f"{SERVER_URL}/")
PI_TOKEN = os.environ.get("PI_TOKEN", "")


# === Subprocess-hjalpare ===

def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", str(e)


# === Server-anrop (med PI_TOKEN) ===

def _server_request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    """Anropa moodplotter-servern. Returnerar (status, json-body)."""
    url = f"{SERVER_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {PI_TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode()
            try:
                return resp.status, json.loads(text)
            except Exception:
                return resp.status, {"raw": text}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


# === WiFi via nmcli ===

def is_online() -> bool:
    code, out, _ = _run(["nmcli", "-t", "-f", "STATE", "general"], timeout=3)
    if code != 0:
        return False
    return "connected" in out.lower()


def list_networks() -> list[dict]:
    _run(["nmcli", "dev", "wifi", "rescan"], timeout=8)
    code, out, _ = _run(
        ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
        timeout=8,
    )
    if code != 0:
        return []
    seen: dict[str, dict] = {}
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) < 3:
            continue
        ssid = parts[0].strip()
        if not ssid or ssid == "--":
            continue
        try:
            signal = int(parts[1] or "0")
        except ValueError:
            signal = 0
        security = parts[2].strip()
        if ssid not in seen or signal > seen[ssid]["signal"]:
            seen[ssid] = {
                "ssid": ssid,
                "signal": signal,
                "secured": bool(security and security != "--"),
            }
    return sorted(seen.values(), key=lambda x: -x["signal"])


def connect_wifi(ssid: str, password: str) -> tuple[bool, str]:
    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    code, out, err = _run(cmd, timeout=40)
    if code == 0:
        return True, out.strip() or "ansluten"
    return False, err.strip() or out.strip() or "okant fel"


# === Routes ===

@app.route("/")
def index():
    if is_online():
        return render_template("gallery.html", gallery_url=GALLERY_URL)
    return redirect("/wifi-setup")


@app.route("/wifi-setup")
def wifi_setup():
    return render_template("wifi_setup.html")


@app.route("/phone")
def phone_page():
    status, body = _server_request("GET", "/api/phone")
    current = body.get("phone", "") if status == 200 else ""
    return render_template("phone.html", current_phone=current)


@app.route("/settings")
def settings():
    s1, body1 = _server_request("GET", "/api/phone")
    current = body1.get("phone", "") if s1 == 200 else ""
    s2, body2 = _server_request("GET", "/api/pir")
    pir_enabled = bool(body2.get("enabled", True)) if s2 == 200 else True
    s3, body3 = _server_request("GET", "/api/mode")
    mode = body3.get("mode", "voice") if s3 == 200 else "voice"
    return render_template(
        "settings.html",
        current_phone=current,
        pir_enabled=pir_enabled,
        mode=mode,
    )


# WiFi-API

@app.route("/api/networks")
def api_networks():
    return jsonify(list_networks())


@app.route("/api/status")
def api_status():
    return jsonify({"online": is_online()})


@app.route("/api/connect", methods=["POST"])
def api_connect():
    data = request.get_json(silent=True) or {}
    ssid = (data.get("ssid") or "").strip()
    password = data.get("password") or ""
    if not ssid:
        return jsonify({"ok": False, "error": "saknar SSID"}), 400
    ok, msg = connect_wifi(ssid, password)
    if ok:
        for _ in range(5):
            time.sleep(1)
            if is_online():
                return jsonify({"ok": True, "message": msg})
    return jsonify({"ok": ok, "message": msg, "error": "" if ok else msg})


# Server-proxy: trigger + phone-state

@app.route("/api/trigger", methods=["POST"])
def api_trigger():
    status, body = _server_request(
        "POST", "/trigger", body={"pi_id": "kiosk", "source": "manual"}
    )
    return jsonify(body), status if status > 0 else 502


@app.route("/api/draw-frame", methods=["POST"])
def api_draw_frame():
    """Trigga rit av kalibrerings-ram (10x10cm rektangel) pa plottern."""
    status, body = _server_request("POST", "/draw-frame")
    return jsonify(body), status if status > 0 else 502


@app.route("/api/pir", methods=["GET"])
def api_pir_get():
    status, body = _server_request("GET", "/api/pir")
    return jsonify(body), status if status > 0 else 502


@app.route("/api/pir", methods=["PUT"])
def api_pir_set():
    data = request.get_json(silent=True) or {}
    status, body = _server_request("PUT", "/api/pir", body={"enabled": bool(data.get("enabled"))})
    return jsonify(body), status if status > 0 else 502


@app.route("/api/mode", methods=["GET"])
def api_mode_get():
    status, body = _server_request("GET", "/api/mode")
    return jsonify(body), status if status > 0 else 502


@app.route("/api/mode", methods=["PUT"])
def api_mode_set():
    data = request.get_json(silent=True) or {}
    status, body = _server_request("PUT", "/api/mode", body={"mode": data.get("mode", "")})
    return jsonify(body), status if status > 0 else 502


@app.route("/api/poweroff", methods=["POST"])
def api_poweroff():
    """Stang av Pi:n. Kraver sudoers-regel for /usr/sbin/shutdown."""
    subprocess.Popen(["sudo", "/usr/sbin/shutdown", "-h", "+0"])
    return jsonify({"ok": True})


@app.route("/api/reboot", methods=["POST"])
def api_reboot():
    """Starta om Pi:n."""
    subprocess.Popen(["sudo", "/usr/sbin/reboot"])
    return jsonify({"ok": True})


@app.route("/api/phone", methods=["GET"])
def api_phone_get():
    status, body = _server_request("GET", "/api/phone")
    return jsonify(body), status if status > 0 else 502


@app.route("/api/phone", methods=["PUT"])
def api_phone_set():
    data = request.get_json(silent=True) or {}
    status, body = _server_request("PUT", "/api/phone", body={"phone": data.get("phone", "")})
    return jsonify(body), status if status > 0 else 502


@app.route("/api/cards/recent")
def api_cards_recent():
    """Proxar till servern (samma origin som kiosk-sidan, ingen CORS)."""
    status, body = _server_request("GET", "/api/cards/recent")
    return jsonify(body), status if status > 0 else 502


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
