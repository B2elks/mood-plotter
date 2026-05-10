"""Generera unik ack-MP3 per samtal via ElevenLabs."""
import logging
from pathlib import Path

from elevenlabs.client import ElevenLabs

log = logging.getLogger(__name__)


def _call_elevenlabs(text: str, voice_id: str, api_key: str) -> bytes:
    """Faktiskt API-anrop. Egen funktion för att kunna mocka i test."""
    client = ElevenLabs(api_key=api_key)
    audio_iter = client.generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    return b"".join(audio_iter)


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
