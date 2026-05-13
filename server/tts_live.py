"""Generera unik ack-MP3 per samtal via ElevenLabs (direkt REST)."""
import json
import logging
import urllib.request
from pathlib import Path

log = logging.getLogger(__name__)


def _call_elevenlabs(text: str, voice_id: str, api_key: str) -> bytes:
    """Direkt REST-anrop till ElevenLabs.

    Anvander INTE elevenlabs-SDK:n eftersom dess output (oavsett output_format)
    ger 'Bad audio data' i 46elks play-action. Bade hangupdemo och oloppnare
    anvander direkt REST och deras MP3:er funkar.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def generate_ack_mp3(
    text: str,
    call_id: str,
    audio_dir: Path,
    public_base_url: str,
    voice_id: str,
    api_key: str,
) -> str:
    """Skapa ack_<call_id>.mp3 från text. Vid fel: fallback."""
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    try:
        audio = _call_elevenlabs(text, voice_id, api_key)
        out_path = audio_dir / f"ack_{call_id}.mp3"
        out_path.write_bytes(audio)
        return f"{public_base_url.rstrip('/')}/audio/{out_path.name}"
    except Exception as e:
        log.error("ElevenLabs-fel, använder fallback: %s", e)
        fallback = audio_dir / "ack_fallback.mp3"
        if not fallback.exists():
            log.error("Ingen ack_fallback.mp3 finns! Skapa en manuellt.")
        return f"{public_base_url.rstrip('/')}/audio/ack_fallback.mp3"
