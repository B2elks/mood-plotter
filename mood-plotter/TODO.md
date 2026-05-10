# TODO innan live-deploy

Status efter implementationsfas: 39/39 tester gröna. Följande punkter kvar från slutreview (`code-reviewer` 2026-05-10).

## Bör fixas innan publik server (live-trafik)

### 1. Verifiera 46elks webhook-signaturer

`server/elks_handler.py` har `verify_signature()` skriven och testad — men den är inte påkopplad i någon route. Det betyder att vem som helst på internet kan POSTa till `/elks/answer`, `/elks/recording`, `/elks/hangup` och tvinga servern att spendera OpenAI/ElevenLabs-credits.

**Fix:** Lägg till en liten dekorator som verifierar `X-46elks-Signature`-headern mot HMAC av callback-URL:

```python
# I server.py
def verify_elks_webhook(handler):
    async def wrapper(request):
        sig = request.headers.get("X-46elks-Signature", "")
        url = str(request.url)
        if not elks_handler.verify_signature(config.ELKS_API_PASSWORD, url, sig):
            return web.Response(status=403, text="invalid signature")
        return await handler(request)
    return wrapper

# Wrap each elks route:
app.router.add_get("/elks/answer", verify_elks_webhook(elks_answer_handler))
# ... etc
```

## Bör fixas men inte blockerande

### 2. Audio-cache TTL-cleanup

`server/audio/ack_<call_id>.mp3` ackumuleras för alltid. Spec sa "äldre än 1 dygn → städa".

**Fix:** Lägg till en cron-task ELLER en aiohttp `on_startup` som med jämna mellanrum rensar `ack_*.mp3` äldre än 1 dygn.

```bash
# crontab på servern
0 4 * * * find /home/kumamonwithme/mood-plotter/server/audio -name 'ack_*.mp3' -mtime +1 -delete
```

### 3. Per-steg-timeouts i recording-handlern

Synchronous-pipelinen i `elks_recording_handler` håller HTTP-svaret i 3-7 sekunder. Om Whisper/ElevenLabs degraderar kan callbacken pusha förbi 46elks-timeouten.

**Fix:** Wrappa varje extern call i `asyncio.wait_for(..., timeout=N)`:
- WAV-download: 5s
- Whisper: 5s
- LLM: 5s
- ElevenLabs: 5s

Vid timeout: degradera till fallback-ack, fortsätt med image-generering ändå.

### 4. ElevenLabs `client.generate()` är deprecated

I elevenlabs SDK 1.x+ är canoniska metoden `client.text_to_speech.convert(...)`. Vår pinned 1.2.2 har fortfarande `.generate` så det funkar idag, men byt vid nästa SDK-bump.

Påverkar: `server/tts_live.py:_call_elevenlabs` och `server/generate_questions.py:synthesize`.

### 5. Dokumentera AxiDraw-tunables i `.env.example`

`pi/config.py` läser `AXIDRAW_PEN_POS_DOWN`, `AXIDRAW_PEN_POS_UP`, `AXIDRAW_SPEED_PENDOWN` med defaults. Lägg till som kommenterade rader i `.env.example` så operatören ser dem.

### 6. systemd-units antar `User=pi`

På Bookworm+ är default-användaren det operatören skapade, inte `pi`. Antingen parametriera eller dokumentera tydligt.

## Smårytt

- `tests/test_server_integration.py:test_elks_answer_returns_play_record_action` använder `?callid=abc` (utan underscore). Servern läser `call_id` med underscore. Testet passerar för fel anledning. Ändra till `?call_id=abc` eller stärk assertionen.
- 46elks recording-callback fältnamn antas vara `recordurl` eller `url`. Verifiera mot 46elks aktuella docs vid första smoke-test (kan vara `wav`).
- DRY_RUN går runt även Whisper/LLM/DALL·E. Ursprungliga specen ville ha en hardkodad transkribering så hela pipelinen kan testas utan riktigt samtal. Lägg till `DRY_RUN_TRANSCRIPT="trött och stressad"` om det blir aktuellt.

## Verifierat fungerar (39 tester gröna)

- Cooldown sqlite-baserad, persistent över restarts, släpps korrekt vid missade samtal men INTE vid svarade samtal (fixat post-review)
- 46elks action-byggare och signaturhjälp (helper, ej påkopplad)
- 46elks `initiate_call` med BasicAuth
- TTS-cache: slumpa fråge-MP3
- TTS-live: ElevenLabs-anrop med fallback till `ack_fallback.mp3`
- Voice-butler: GPT-4o-mini → `(image_prompt, butler_ack)` med fallback för tomt/error/invalid-JSON
- Whisper-transkribering med tom-sträng-fallback
- Image-pipeline: DALL·E PNG → vpype iread → linemerge → linesimplify → scaleto → SVG
- WS-dispatcher: register/unregister/mark_busy/mark_ready/send_svg, unregistrerar döda klienter
- Server-routes: `/trigger` (auth, cooldown, dispatcher-check), `/elks/answer` (sätter state=answered), `/elks/recording` (synchronous Whisper+LLM+TTS, async DALL·E+plot), `/elks/hangup` (släpper cooldown bara om aldrig svarat), `/audio/<file>` (path-traversal-skydd), `/ws` (token-auth, register/ready)
- Pi PIR-watcher: gpiozero MotionSensor + debounce + HTTP-trigger
- Pi plotter-klient: WS + pyaxidraw + reconnect-backoff
- systemd-units för server och Pi (server- + pir- + plotter-tjänst)
