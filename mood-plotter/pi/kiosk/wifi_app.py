"""Local Flask-app pa Pi:n. Visar WiFi-setup om ingen anslutning, annars
embed:ar mood-plotter-galleriet. Drivs via Chromium-kiosk pa LCD:n.
"""
import json
import os
import subprocess
import time

from flask import Flask, jsonify, redirect, render_template, request

app = Flask(__name__)

GALLERY_URL = os.environ.get("GALLERY_URL", "https://moodplotter.skyttberg.nu/")


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """Kor en kommando, returnera (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", str(e)


def is_online() -> bool:
    """Snabbcheck: har vi internet?"""
    code, out, _ = _run(["nmcli", "-t", "-f", "STATE", "general"], timeout=3)
    if code != 0:
        return False
    return "connected" in out.lower()


def list_networks() -> list[dict]:
    """Returnera lista av synliga WiFi-nat (unika SSID, starkaste signal forst)."""
    _run(["nmcli", "dev", "wifi", "rescan"], timeout=8)
    code, out, _ = _run(
        ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
        timeout=8,
    )
    if code != 0:
        return []

    seen: dict[str, dict] = {}
    for line in out.splitlines():
        # nmcli -t escapes ':' i SSID-fal med backslash; enkel split rackare for de flesta fall
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
        # Behall starkaste signal per SSID
        if ssid not in seen or signal > seen[ssid]["signal"]:
            seen[ssid] = {
                "ssid": ssid,
                "signal": signal,
                "secured": bool(security and security != "--"),
            }
    return sorted(seen.values(), key=lambda x: -x["signal"])


def connect_wifi(ssid: str, password: str) -> tuple[bool, str]:
    """Forsok ansluta till WiFi-nat. Returnerar (success, message)."""
    cmd = ["nmcli", "dev", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    code, out, err = _run(cmd, timeout=40)
    if code == 0:
        return True, out.strip() or "ansluten"
    return False, err.strip() or out.strip() or "okant fel"


@app.route("/")
def index():
    if is_online():
        return render_template("gallery.html", gallery_url=GALLERY_URL)
    return redirect("/wifi-setup")


@app.route("/wifi-setup")
def wifi_setup():
    return render_template("wifi_setup.html")


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
        # Vanta lite och dubbelcheck connectivity
        for _ in range(5):
            time.sleep(1)
            if is_online():
                return jsonify({"ok": True, "message": msg})
    return jsonify({"ok": ok, "message": msg, "error": "" if ok else msg})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
