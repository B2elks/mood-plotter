#!/usr/bin/env bash
# Installerar mood-plotter pa en NY Raspberry Pi (Pi OS Bookworm 64-bit).
#
# Antar att SD-kortet ar fresh-flashat med Pi Imager + customizing
# (hostname, SSH, wifi) och att du SSH:at in som pi-anvandaren.
#
# Anvandning (rekommenderat):
#
#   PI_ID=desk2 \
#   PI_TOKEN=<token-fran-fora-Pi> \
#   bash <(curl -sL https://raw.githubusercontent.com/B2elks/mood-plotter/main/pi/install.sh)
#
# Argument via env:
#   PI_ID          UNIK identifier (default: hostname)
#   PI_TOKEN       Samma som forsta Pi:n (fran ~/mood-plotter/.env dar)
#   SERVER_URL     Default: https://moodplotter.skyttberg.nu
#   SERVER_WS_URL  Default: wss://moodplotter.skyttberg.nu/ws
#   SKIP_KIOSK     Sant att hoppa over touchskarm-installation
set -euo pipefail


# ─── 0) Prep ─────────────────────────────────────────────────────────
if [[ "${EUID}" -eq 0 ]]; then
  echo "Kor INTE som root. Kor som pi-anvandaren."
  exit 1
fi

PI_ID="${PI_ID:-$(hostname)}"
SERVER_URL="${SERVER_URL:-https://moodplotter.skyttberg.nu}"
SERVER_WS_URL="${SERVER_WS_URL:-wss://moodplotter.skyttberg.nu/ws}"
SKIP_KIOSK="${SKIP_KIOSK:-}"

if [[ -z "${PI_TOKEN:-}" ]]; then
  echo "FEL: PI_TOKEN saknas."
  echo "Hamta den fran forsta Pi:n med:"
  echo "  ssh pi@moodplotter.local 'grep PI_TOKEN ~/mood-plotter/.env'"
  exit 1
fi

echo "=== mood-plotter installation ==="
echo "  PI_ID:         $PI_ID"
echo "  SERVER_URL:    $SERVER_URL"
echo "  SERVER_WS_URL: $SERVER_WS_URL"
echo "  Kiosk:         $([ -z "$SKIP_KIOSK" ] && echo "ja" || echo "nej")"
echo ""


# ─── 1) Systempaket ─────────────────────────────────────────────────
echo "=== Installerar systempaket ==="
sudo apt-get update
sudo apt-get install -y git python3-venv python3-pip


# ─── 2) Klona repo ──────────────────────────────────────────────────
cd ~
if [[ ! -d mood-plotter/.git ]]; then
  echo "=== Klonar mood-plotter ==="
  git clone https://github.com/B2elks/mood-plotter.git
else
  echo "=== mood-plotter finns redan, pullar senaste ==="
  cd mood-plotter && git pull && cd ~
fi
cd mood-plotter


# ─── 3) Venv + Python-deps ──────────────────────────────────────────
echo "=== Bygger venv + Python-deps ==="
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r pi/requirements.txt
echo "=== Installerar pyaxidraw fran Evil Mad Scientist ==="
.venv/bin/pip install -q "https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip"


# ─── 4) .env ────────────────────────────────────────────────────────
echo "=== Skriver .env ==="
cat > .env <<ENVEOF
PI_TOKEN=$PI_TOKEN
SERVER_URL=$SERVER_URL
SERVER_WS_URL=$SERVER_WS_URL
PI_ID=$PI_ID
PIR_GPIO_PIN=4
AXIDRAW_PEN_POS_DOWN=40
AXIDRAW_PEN_POS_UP=60
AXIDRAW_SPEED_PENDOWN=25
ENVEOF
chmod 600 .env


# ─── 5) Plotter-service ─────────────────────────────────────────────
echo "=== Installerar plotter-service ==="
sudo cp pi/mood-plotter-plotter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-plotter


# ─── 6) Kiosk (om touchskarm) ───────────────────────────────────────
if [[ -z "$SKIP_KIOSK" ]]; then
  echo "=== Installerar kiosk (touchskarm + Chromium + Sway) ==="
  bash pi/kiosk/install.sh
else
  echo "=== Hoppar over kiosk (SKIP_KIOSK satt) ==="
fi


# ─── 7) Klart ───────────────────────────────────────────────────────
echo ""
echo "================================================================"
echo "Klart! mood-plotter installerat pa $(hostname)."
echo ""
echo "Naasta steg:"
echo "  1) Anslut AxiDraw via USB"
echo "  2) sudo reboot"
echo "  3) Verifiera: journalctl -u mood-plotter-plotter -f"
echo "================================================================"
