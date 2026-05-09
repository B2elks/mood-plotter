# PIR Mood Plotter — Design

**Datum:** 2026-05-09
**Status:** Förslag
**Författare:** Björn + Claude
**Bakgrund:** Fork/återanvändning av [46elks/elkplotter](https://github.com/46elks/elkplotter)

## Översikt

En självkiosk byggd kring en AxiDraw pen-plotter och en Raspberry Pi. När en PIR-sensor på Pi:n upptäcker rörelse ringer systemet upp ägarens mobil. En charmig butler frågar hur dagen är, lyssnar några sekunder, säger en hummande bekräftelse — och under tiden ritar AxiDraw ett "mood-kort" anpassat efter svaret.

Originalprojektet (`elkplotter`) tar emot SMS, genererar DALL·E-bilder, vektoriserar med vpype och plottar via AxiDraw genom en server/klient-uppdelning. Det här projektet behåller exakt samma slutsteg (DALL·E → vpype → WebSocket → AxiDraw) men byter ut SMS-triggern mot en PIR-triggad telefondialog.

## Mål

- PIR-rörelse → uppringning till ett förkonfigurerat nummer
- 15–25 sek samtal med butler-personlighet på svenska
- Svaret tolkas och styr både butler-replik och bildmotivet
- Plotter ritar ett uppmuntrande kort medan/strax efter samtalet
- Driftas på existerande infrastruktur (`skyttberg.nu` + Pi)

## Icke-mål

- Stöd för flera samtidiga användare eller konton
- Frontend-app, inloggning, statistik
- Realtids-konversationsagent (det här är ett kort utbyte, inte en dialog)
- Stöd för andra plottertyper än AxiDraw

## Arkitektur

Två noder i en server/klient-uppdelning:

```
┌────────────────────────────┐         ┌──────────────────────────────┐
│  Pi (på skrivbordet)       │         │  skyttberg.nu (server)       │
│  ─────────────────────     │         │  ─────────────────────       │
│  • PIR-läsare (GPIO)       │  HTTP   │  • aiohttp app (port 8095)   │
│  • WebSocket-klient        │ ──────> │  • 46elks call orchestrator  │
│  • AxiDraw plotter         │         │  • ElevenLabs TTS (cached)   │
│  • Lokal cooldown-debounce │  WS     │  • OpenAI Whisper + DALL·E   │
│                            │ <────── │  • vpype + vectrace          │
└────────────────────────────┘   SVG   └──────────────────────────────┘
                                              │       ▲
                                              │ outb. │ webhooks
                                              ▼       │
                                         ┌────────────────┐
                                         │   46elks       │
                                         └────────────────┘
                                              │ PSTN
                                              ▼
                                         📞 Användarens mobil
```

**Stack:** Python 3.11 på båda sidorna. `aiohttp` på servern (matchar busring), `RPi.GPIO`/`gpiozero` + `websocket-client` + `pyaxidraw` på Pi:n. Båda körs som systemd-tjänster.

**Domän/exponering:** `https://moodplotter.skyttberg.nu` (nytt subdomän bakom nginx, samma mönster som `granny.skyttberg.nu`/`busring.skyttberg.nu`).

## Komponenter

### Server (`mood-plotter-server`, port 8095)

| Modul | Ansvar |
|---|---|
| `server.py` | aiohttp-app: routes `/trigger`, `/elks/answer`, `/elks/recording`, `/elks/hangup`, `/audio/<file>`, `/ws` |
| `elks_handler.py` | Bygg 46elks-actions (`play`, `record`, `next`, `hangup`), verifiera webhook-signaturer |
| `voice_butler.py` | LLM-anrop (GPT-4o-mini): tolka transkriberat svar → `(image_prompt, butler_ack)` |
| `tts_cache.py` | Pre-genererade ElevenLabs-frågevarianter på disk; väljer slumpmässigt |
| `tts_live.py` | Generera unik ack-fras per samtal via ElevenLabs API, returnerar publik URL |
| `image_pipeline.py` | DALL·E call → bytes → temp PNG → vpype + vpype-vectrace → SVG-sträng |
| `ws_dispatcher.py` | Hantera registrerade WS-klienter (ready/busy), skicka SVG till första ready |
| `cooldown.py` | sqlite-baserad senast-samtalstid, default 5 min mellan samtal |
| `config.py` | API-nycklar, telefonnummer, ws-token, cooldown-tid, audio-mapp |
| `mood-plotter.service` | Systemd-unit |

### Klient (`mood-plotter-pi` på Pi:n)

| Modul | Ansvar |
|---|---|
| `pir_watcher.py` | GPIO-läsare med `gpiozero.MotionSensor`, debounce 30s, anropar trigger |
| `plotter_client.py` | WS-anslutning till servern, registrera "ready", ta emot SVG, kör AxiDraw |
| `config.py` | Server-URL, ws-token, GPIO-pin, AxiDraw-options |
| `mood-plotter.service` | Systemd-unit som auto-startar och restartar |

### Förinspelade tillgångar

5–8 MP3-filer för fråga-varianter genererade en gång via ett separat skript (`generate_questions.py`). Exempel:
- "Hur står det till med min herre denna dag?"
- "Goddag goddag, hur befinner sig herrn?"
- "Får jag fråga hur dagen behandlat herrn?"
- "Hur mår min herre idag?"
- "Goddag, är allt väl med herrn?"

Filerna serveras från `/audio/`-mappen via servern.

## Dataflöde

**T+0 — PIR triggar:**
```
Pi: PIR HIGH → debounce 30s → POST https://moodplotter.skyttberg.nu/trigger
                              Authorization: Bearer <PI_TOKEN>
                              Body: {"pi_id": "desk1"}
```

**T+0.1 — Server tar emot trigger:**
```
- Cooldown-check (sqlite). Om <5 min sedan senaste samtal → 429.
- Check att en WS-klient är "ready". Om inte → 503.
- Spara CALL_STATE = {state: "calling", started: now, pi_id, call_id}
- POST https://api.46elks.com/a1/calls
    from=<46elks-nummer>
    to=<användarens mobil>
    voice_start=https://moodplotter.skyttberg.nu/elks/answer
    whenhangup=https://moodplotter.skyttberg.nu/elks/hangup
- Returnera 200 till Pi:n
```

**T+~5s — Användaren svarar, 46elks anropar voice_start:**
```json
{
  "play": "https://moodplotter.skyttberg.nu/audio/q_03.mp3",
  "next": {
    "record": {
      "timeout": 4,
      "maxlength": 8,
      "callbackurl": "https://moodplotter.skyttberg.nu/elks/recording"
    }
  }
}
```

**T+~15s — Användaren talat klart, 46elks POSTar inspelning:**
```
- Hämta recordingurl → temp.wav
- Whisper API → transkribering, t.ex. "Trött, lite stressad"
- voice_butler.py kallar GPT-4o-mini med systemprompt:
    "Du är en charmig brittisk-svensk butler. Användaren svarade: '<text>'.
     Returnera JSON:
     {
       image_prompt: <kort engelsk DALL·E-prompt för en uppmuntrande,
                      lugn, vacker bild som muntrar upp någon i detta humör.
                      Helst med tydliga konturer som funkar för pen-plotter>,
       butler_ack: <1-2 meningar svensk butler-replik som mjukt erkänner
                    humöret och meddelar att kortet är på väg>
     }"
- ElevenLabs TTS: butler_ack → ack_<call_id>.mp3 sparas i /audio/
- Returnera till 46elks (response till record-callback):
    {
      "play": "https://moodplotter.skyttberg.nu/audio/ack_<call_id>.mp3",
      "next": {"hangup": "..."}
    }
- Parallellt (asyncio.create_task): kör image_pipeline.py
```

**T+~20s — Bildpipelinen:**
```
- DALL·E 3 generate → PNG bytes (~1024x1024)
- vpype: read PNG → vectrace → linemerge → linesimplify
- Skriv SVG till sträng
- ws_dispatcher: skicka {"method": "plot", "svg": <svg>} till första ready-klient
- Markera klient som busy
```

**T+~25s — Pi plottar:**
```
- WS-klient tar emot SVG → ad.plot_setup(svg) → ad.plot_run()
- När klar: skicka {"method": "ready"} tillbaka
```

Cooldown uppdateras vid `POST /a1/calls`-anropet (inte vid PIR), så missade samtal blockerar inte fler triggers.

## Felhantering

### På Pi:n

| Fel | Hantering |
|---|---|
| PIR triggar igen inom 30s | Debounce — ignorera |
| Server svarar 429 (cooldown) | Logga, ingen feedback |
| Server svarar 503 (ingen plotter ready) | Borde inte hända — Pi:n är ju ready om den lever |
| WS-anslutning tappas | Auto-reconnect med exponentiell backoff (1s, 2s, 4s, max 30s) |
| AxiDraw-fel mitt i plot | Logga, skicka `{"method": "ready"}` ändå när det är klart |
| AxiDraw inte ansluten vid start | Vänta 5s, försök igen i loop (samma som originalets klient) |

### På servern

| Fel | Hantering |
|---|---|
| Användaren svarar inte (voicemail/missat) | 46elks `whenhangup`-webhook → städa state, ingen plot, rensa cooldown |
| Inspelning är tom/för kort | LLM får tom text → fallback-prompt "a peaceful watercolor landscape", standard-butler-ack |
| Whisper-fel | Samma fallback |
| LLM-fel | Samma fallback |
| ElevenLabs-fel för ack | Fallback till generic pre-genererad ack-MP3 ("Här min herre, ett kort till er") |
| DALL·E-fel | Logga, hoppa över plot, samtalet är redan avslutat |
| vpype-fel | Logga, hoppa över plot |
| Ingen WS-klient ready vid plot | Logga, kasta SVG |
| 46elks `POST /a1/calls` returnerar fel | Rensa cooldown direkt, logga |

### Cooldown-logik

- Sätt cooldown vid `POST /a1/calls`-anropet
- Rensa cooldown om 46elks-anropet misslyckas
- Default 5 minuter, konfigurerbart via `config.py`

### Logging

Standard Python logging till stdout, fångas av systemd journalctl. Varje samtal har ett `call_id` som följer hela kedjan (trigger → call → recording → image → plot) för enkel felsökning.

## Test & verifiering

### Manuella tester (innan deploy)

| Test | Hur |
|---|---|
| ElevenLabs-frågevariant låter butler-mässig | Lyssna på alla 5–8 pre-genererade MP3:er |
| 46elks `play` + `record`-flöde fungerar | Mocka `/elks/answer` med curl, verifiera JSON-svar |
| Whisper transkriberar svenska rätt | 3 testsvar genom pipelinen |
| LLM ger rimliga prompts + ack | Kör `voice_butler.py` standalone med 5 sample-svar |
| DALL·E + vpype ger plottbar SVG | Kör `image_pipeline.py` standalone, öppna SVG i Inkscape |
| AxiDraw plottar | Kör `plotter_client.py` med en handgjord SVG från servern |

### Integrationstest

- `DRY_RUN=true` — servern ringer inte riktigt utan loggar 46elks-anropet, kör resten av pipelinen med hårdkodad transkribering
- End-to-end: manuell PIR-knapp på Pi:n → server ringer testnummer → svara → invänta plot

### Smoke-test efter deploy

- `curl -X POST https://moodplotter.skyttberg.nu/trigger -H "Authorization: Bearer ..."` i live-läge
- Bekräfta uppringning, fråga spelas, ack ljuder, AxiDraw startar

### Inte i scope

- Enhetstester på 46elks-webhookens parsing
- Auto-test av AxiDraw (kräver hårdvara)
- Stresstest

## Säkerhet

- 46elks webhook-anrop verifieras med signaturkontroll (`elks_handler.verify_signature`)
- `/trigger` skyddas med shared bearer token (`PI_TOKEN`) i HTTP-header
- WS-klienter autentiserar med samma token vid registrering
- Audio-mapp serveras read-only via `/audio/<file>`, ingen path traversal
- API-nycklar (46elks, OpenAI, ElevenLabs) i `config.py` utanför git, läses via miljövariabler där det går

## Driftnotis

- Domän: `moodplotter.skyttberg.nu` med Let's Encrypt-cert
- Nginx proxy → `127.0.0.1:8095`
- 46elks utgående nummer: ett befintligt eller ett nyallokerat
- Servern: systemd-tjänst `mood-plotter-server`
- Pi:n: systemd-tjänst `mood-plotter-pi`, auto-restart
- Audio-cache rensas via cron eller TTL i koden (ack-MP3:er äldre än 1 dygn)
