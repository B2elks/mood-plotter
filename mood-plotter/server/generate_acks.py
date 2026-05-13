"""Engangsskript: generera forinspelade ack-MP3:er per kansla-kategori.

Anvander direkt REST mot ElevenLabs (SDK ger badaudio i 46elks).
"""
import json
import urllib.request
from pathlib import Path

import config

ACKS = {
    "neutral_01": "Tack min herre. Ett mood-kort är på väg till er. Håll till godo.",
    "neutral_02": "Förträffligt. Ett kort sänds härmed. Hoppas det piggar upp dagen.",
    "neutral_03": "Min herre, tack ska ni ha. Ett kort är på väg. Trevlig dag.",
    "neutral_04": "Tackar ödmjukast. Mood-kortet anländer inom kort. Håll till godo.",
}


def synthesize(text: str, out_path: Path):
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{config.ELEVENLABS_VOICE_ID}"
    )
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out_path.write_bytes(resp.read())
    print(f"Skapade {out_path}")


def main():
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for category, text in ACKS.items():
        synthesize(text, config.AUDIO_DIR / f"ack_{category}.mp3")
    print("Klart.")


if __name__ == "__main__":
    main()
