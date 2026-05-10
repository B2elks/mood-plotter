# mood-plotter

PIR-triggad butler-uppringning som plottar mood-kort med AxiDraw.

## Översikt

PIR-sensor → samtal till mobil → butler frågar "hur mår herrn?" → svar tolkas → DALL·E-bild vektoriseras → AxiDraw plottar.

Se [`docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md`](../docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md) för fullständig design.

## Setup — server (skyttberg.nu)

```bash
ssh kumamonwithme@skyttberg.nu
cd ~
git clone <repo> mood-plotter
cd mood-plotter
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt
cp .env.example .env
# fyll i .env med riktiga värden
.venv/bin/python server/generate_questions.py
sudo cp server/mood-plotter-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-server
journalctl -u mood-plotter-server -f
```

Lägg upp nginx-proxy för `moodplotter.skyttberg.nu` → `127.0.0.1:8095` (inkl. WS-upgrade) och Let's Encrypt-cert.

## Setup — Pi

```bash
ssh pi@<pi-ip>
git clone <repo> mood-plotter
cd mood-plotter
python3 -m venv .venv
.venv/bin/pip install -r pi/requirements.txt
# pyaxidraw distribueras separat:
.venv/bin/pip install "https://cdn.evilmadscientist.com/dl/ad/public/AxiDraw_API.zip"
cp .env.example .env
# fyll i .env med Pi-värden (SERVER_URL, PI_TOKEN, GPIO-pin)
sudo cp pi/mood-plotter-pir.service /etc/systemd/system/
sudo cp pi/mood-plotter-plotter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-plotter mood-plotter-pir
```

## Smoke-test

Med `DRY_RUN=true` i serverns env:

```bash
curl -X POST https://moodplotter.skyttberg.nu/trigger \
  -H "Authorization: Bearer $PI_TOKEN" \
  -d '{"pi_id":"desk1"}'
```

Förvänta: 200 + JSON med `call_id` och `dry_run: true`. Inga riktiga samtal.

Sätt `DRY_RUN=false` när allt verifierats. Trigga manuellt en gång till — telefonen ska ringa, butlern fråga, AxiDraw börja rita.

## Fil-layout

| Fil | Vad |
|---|---|
| `server/server.py` | aiohttp-app + routes |
| `server/elks_handler.py` | 46elks API + actions |
| `server/voice_butler.py` | Whisper + GPT-4o-mini |
| `server/tts_cache.py` | Pre-genererad fråge-MP3-väljare |
| `server/tts_live.py` | ElevenLabs ack-generator |
| `server/image_pipeline.py` | DALL·E + vpype |
| `server/ws_dispatcher.py` | WS-klient-pool |
| `server/cooldown.py` | sqlite-cooldown |
| `server/generate_questions.py` | Engångsskript för fråge-MP3 |
| `pi/pir_watcher.py` | GPIO + HTTP trigger |
| `pi/plotter_client.py` | WS + AxiDraw |

## Tester

```bash
cd mood-plotter
.venv/bin/pytest -v
```

38 tester totalt över alla servermoduler.

## Troubleshooting

- **`vpype iread` saknas:** `pipx install vpype && pipx inject vpype vpype-vectrace`
- **Pi triggar inte:** kolla `journalctl -u mood-plotter-pir -f` på Pi:n
- **Inget samtal kommer fram:** verifiera 46elks-konto, telefonnummer, och webhook-URL
- **AxiDraw plottar inte:** kontrollera USB-anslutning, kör `python pi/plotter_client.py` manuellt
- **Cooldown blockerar:** ta bort `server/cooldown.db` på servern
