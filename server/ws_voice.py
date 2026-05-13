"""46elks WebSocket Voice (Beta) — realtids-ljudhantering.

Foljande monster (kopierat fran oloppnare):
1. 46elks oppnar WS efter att samtalet kopplats
2. Vi tar emot {"t":"hello", ...}
3. Vi skickar {"t":"sending", "format":"pcm_24000"} och {"t":"listening",...}
4. Vi stromar fraga (PCM i 0.25s chunks)
5. Vi tar emot uppringarens ljud som {"t":"audio","data":"<base64>"}-meddelanden
6. Custom VAD: nar uppringaren tystnat (RMS lagt i ~1s) -> stoppa lyssna
7. Vi stromar ack-frasen
8. Vi skickar {"t":"hangup"}
9. Bakgrund: WAV fran ackumulerat PCM -> Whisper -> LLM -> DALL-E -> kort
"""
import asyncio
import base64
import json
import logging
import random
import uuid
from pathlib import Path

from aiohttp import web, WSMsgType

from audio_clips import pcm_to_wav, rms

log = logging.getLogger(__name__)

CODEC = "pcm_24000"
AUDIO_CHUNK = 24000  # bytes per send (~0.25s @ 24kHz 16-bit mono)
SAMPLE_RATE = 24000

# VAD-parametrar
RMS_SPEECH_THRESHOLD = 500
SILENCE_CHUNK_DURATION = 0.25  # sek per VAD-check
SILENCE_CHUNKS_TO_END = 4  # 4 * 0.25 = 1s tystnad
MAX_LISTEN_SECONDS = 10  # hardcap nar nan pratar pa


async def stream_pcm(ws, pcm_data: bytes):
    """Skicka PCM som base64-chunks via WS. Pacar inte — 46elks buffrar.
    Vantar sen pa att audio ska hinna spela klart innan vi fortsatter."""
    for i in range(0, len(pcm_data), AUDIO_CHUNK):
        chunk = pcm_data[i:i + AUDIO_CHUNK]
        b64 = base64.b64encode(chunk).decode()
        await ws.send_str(json.dumps({"t": "audio", "data": b64}))
    duration = len(pcm_data) / (SAMPLE_RATE * 2)
    await asyncio.sleep(duration + 0.1)


async def handle_ws_voice(request):
    """Aiohttp handler for 46elks WebSocket Voice."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    app = request.app
    question_clips = app.get("question_clips") or []
    ack_clips = app.get("ack_clips") or []

    if not question_clips or not ack_clips:
        log.error("ws_voice: inga ljud-klipp laddade")
        await ws.close()
        return ws

    # Forsta meddelandet: hello / call_started
    try:
        raw = await asyncio.wait_for(ws.receive_str(), timeout=10)
        data = json.loads(raw)
    except Exception as e:
        log.error("ws_voice: kunde inte ta emot hello: %s", e)
        return ws

    msg_type = data.get("t") or data.get("type", "")
    if msg_type not in ("hello", "call_started"):
        log.error("ws_voice: ovantat forsta meddelande: %s", data)
        return ws

    elks_call_id = data.get("callid") or data.get("call_id", "")
    call_id = str(uuid.uuid4())[:8]
    log.info("ws_voice call_id=%s (elks=%s) ansluten", call_id, elks_call_id)

    # Aktivera audio-strommar
    await ws.send_str(json.dumps({"t": "sending", "format": CODEC}))
    await ws.send_str(json.dumps({"t": "listening", "format": CODEC}))

    # Bakgrundstask: ackumulera uppringarens audio
    caller_audio = bytearray()
    closed = asyncio.Event()

    async def receive_loop():
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        ev = json.loads(msg.data)
                    except Exception:
                        continue
                    et = ev.get("t") or ev.get("type", "")
                    if et == "audio":
                        try:
                            caller_audio.extend(base64.b64decode(ev.get("data", "")))
                        except Exception:
                            pass
                    elif et in ("bye", "close", "hangup"):
                        break
                elif msg.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                    break
        finally:
            closed.set()

    rx = asyncio.create_task(receive_loop())

    try:
        # 1. Spela fraga (slumpad)
        question = random.choice(question_clips)
        log.info("call_id=%s stromar fraga (%d B PCM)", call_id, len(question))
        await stream_pcm(ws, question)

        # 2. Vanta pa tal-sen-tystnad (custom VAD)
        await _wait_for_speech_then_silence(caller_audio, closed)

        # 3. Spela ack
        ack = random.choice(ack_clips)
        log.info("call_id=%s stromar ack (%d B PCM)", call_id, len(ack))
        await stream_pcm(ws, ack)

        # 4. Lagg pa
        try:
            await ws.send_str(json.dumps({"t": "hangup"}))
        except Exception:
            pass

        # 5. Kicka igang bakgrunds-pipeline med uppringarens audio
        audio_snapshot = bytes(caller_audio)
        if audio_snapshot:
            asyncio.create_task(
                _process_caller_audio(app, call_id, audio_snapshot)
            )

    except Exception as e:
        log.exception("ws_voice call_id=%s fel: %s", call_id, e)
    finally:
        await asyncio.sleep(0.2)
        try:
            await ws.close()
        except Exception:
            pass
        rx.cancel()

    return ws


async def _wait_for_speech_then_silence(caller_audio: bytearray, closed: asyncio.Event):
    """Vanta tills nagon talar och sedan tystnar (~1 sek tystnad)."""
    chunk_samples = int(SAMPLE_RATE * SILENCE_CHUNK_DURATION)
    chunk_bytes = chunk_samples * 2
    speech_detected = False
    quiet_count = 0
    max_iters = int(MAX_LISTEN_SECONDS / SILENCE_CHUNK_DURATION)

    for _ in range(max_iters):
        await asyncio.sleep(SILENCE_CHUNK_DURATION)
        if closed.is_set():
            return

        if len(caller_audio) < chunk_bytes:
            continue

        recent = bytes(caller_audio[-chunk_bytes:])
        r = rms(recent)
        if r > RMS_SPEECH_THRESHOLD:
            speech_detected = True
            quiet_count = 0
        elif speech_detected:
            quiet_count += 1
            if quiet_count >= SILENCE_CHUNKS_TO_END:
                return


async def _process_caller_audio(app, call_id: str, pcm: bytes):
    """Bakgrund: WAV -> Whisper -> LLM -> DALL-E -> spara kort."""
    import card_store
    import config
    import image_pipeline
    import voice_butler

    try:
        wav_bytes = pcm_to_wav(pcm)
        wav_path = config.AUDIO_DIR / f"rec_{call_id}.wav"
        wav_path.write_bytes(wav_bytes)

        text = voice_butler.transcribe_audio(wav_path, config.OPENAI_API_KEY)
        log.info("call_id=%s transkribering: %r", call_id, text)

        result = voice_butler.analyze_response(text, config.OPENAI_API_KEY)
        log.info("call_id=%s image_prompt: %s", call_id, result.image_prompt[:80])

        png = image_pipeline.generate_png(result.image_prompt, config.OPENAI_API_KEY)
        svg = image_pipeline.png_to_svg(png)
        card_store.save_card(
            cards_dir=config.CARDS_DIR,
            call_id=call_id,
            png_bytes=png,
            svg_text=svg,
            transcription=text,
            image_prompt=result.image_prompt,
            butler_ack=result.butler_ack,
        )
        sent = await app["ws_dispatcher"].send_svg(svg)
        log.info("call_id=%s kort sparat + plotter=%s", call_id, sent)

        wav_path.unlink(missing_ok=True)
    except Exception as e:
        log.exception("call_id=%s background-fel: %s", call_id, e)
