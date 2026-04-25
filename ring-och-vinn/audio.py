"""Audio utilities — PCM playback, WAV conversion, Whisper transcription, silence detection."""

import asyncio
import base64
import json
import os
import struct
import urllib.request

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CODEC = "pcm_24000"
AUDIO_CHUNK = 24000  # bytes per send (~0.25s at 24kHz 16-bit)


async def play_audio(ws, pcm_data, interrupt_event=None):
    """Send PCM audio to 46elks WebSocket. Stops early if interrupt_event fires."""
    try:
        for i in range(0, len(pcm_data), AUDIO_CHUNK):
            if interrupt_event and interrupt_event.is_set():
                return True
            chunk = pcm_data[i:i + AUDIO_CHUNK]
            b64 = base64.b64encode(chunk).decode()
            await ws.send(json.dumps({"t": "audio", "data": b64}))
        duration = len(pcm_data) / 48000
        remaining = duration + 0.1
        while remaining > 0:
            if interrupt_event and interrupt_event.is_set():
                return True
            step = min(0.05, remaining)
            await asyncio.sleep(step)
            remaining -= step
    except Exception:
        pass
    return False


def pcm_to_wav(pcm_data, sample_rate=24000):
    """Create WAV file bytes from raw PCM."""
    n = len(pcm_data)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + n, b'WAVE',
        b'fmt ', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
        b'data', n,
    )
    return header + pcm_data


async def transcribe_audio(pcm_data):
    """Transcribe caller audio using OpenAI Whisper."""
    if len(pcm_data) < 4800:
        return ""

    wav_data = pcm_to_wav(bytes(pcm_data))
    boundary = 'b' + os.urandom(8).hex()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        f'Content-Type: audio/wav\r\n\r\n'
    ).encode() + wav_data + (
        f'\r\n--{boundary}\r\n'
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f'whisper-1'
        f'\r\n--{boundary}--\r\n'
    ).encode()

    def _do():
        req = urllib.request.Request(
            'https://api.openai.com/v1/audio/transcriptions',
            data=body,
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': f'multipart/form-data; boundary={boundary}',
            },
        )
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read()).get('text', '')

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _do)
    except Exception:
        return ""


async def wait_for_speech_then_silence(caller_audio, call_closed, start_pos=0,
                                       timeout_checks=60):
    """Wait until caller speaks and then goes silent (~1.5s). Returns True if speech detected."""
    CHECK_SIZE = 12000
    SPEECH_THRESH = 500
    SILENCE_CHECKS_NEEDED = 6

    speech_detected = False
    quiet_count = 0

    for _ in range(timeout_checks):
        await asyncio.sleep(0.25)
        if call_closed.is_set():
            return False

        buf = caller_audio[start_pos:]
        if len(buf) < CHECK_SIZE:
            continue

        recent = bytes(buf[-CHECK_SIZE:])
        samples = struct.unpack(f'<{CHECK_SIZE // 2}h', recent)
        rms = int((sum(s * s for s in samples) / len(samples)) ** 0.5)

        if rms > SPEECH_THRESH:
            speech_detected = True
            quiet_count = 0
        elif speech_detected:
            quiet_count += 1
            if quiet_count >= SILENCE_CHECKS_NEEDED:
                return True

    return speech_detected
