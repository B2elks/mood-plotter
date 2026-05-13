#!/usr/bin/env bash
# Installer for mood-plotter kiosk-mode pa Raspberry Pi.
# Antar Pi OS Lite (Bookworm 64-bit) med NetworkManager (default).
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "Kor INTE som root. Kor som pi-anvandaren — sudo anvands dar det behovs."
  exit 1
fi

# === Paket: Chromium + Cage + ffmpeg (for plotter_client SVG-prep) ===
sudo apt-get update
sudo apt-get install -y \
  chromium-browser \
  cage \
  python3-venv \
  python3-pip \
  network-manager \
  fonts-noto-color-emoji

# === Venv + Flask ===
cd "$(dirname "$0")/../.."   # → mood-plotter/
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r pi/kiosk/requirements.txt

# === Tillat pi att kora nmcli utan losen ===
SUDOERS_LINE="pi ALL=(ALL) NOPASSWD: /usr/bin/nmcli"
if ! sudo grep -q "NOPASSWD: /usr/bin/nmcli" /etc/sudoers.d/mood-plotter 2>/dev/null; then
  echo "${SUDOERS_LINE}" | sudo tee /etc/sudoers.d/mood-plotter > /dev/null
  sudo chmod 440 /etc/sudoers.d/mood-plotter
fi

# === Systemd-units ===
sudo cp pi/kiosk/mood-plotter-wifi.service /etc/systemd/system/
sudo cp pi/kiosk/mood-plotter-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-wifi.service
sudo systemctl enable mood-plotter-kiosk.service

# === Default till graphical.target sa kiosk auto-startar vid boot ===
sudo systemctl set-default graphical.target

echo
echo "Klart. Starta om Pi:n med 'sudo reboot' — sen visas WiFi-setup pa LCD:n."
echo "Om du redan ar pa WiFi: 'sudo systemctl start mood-plotter-kiosk' for att starta nu."
