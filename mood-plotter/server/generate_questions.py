"""Engangsskript: generera q_NN.mp3 i audio/ via ElevenLabs (direkt REST).

Kor en gang efter setup. Skapar ocksa ack_fallback.mp3.

Anvander INTE elevenlabs-SDK:n eftersom dess output ger 'Bad audio data'
i 46elks play-action. Direkt REST-anrop (samma monster som hangupdemo
och oloppnare) ger en MP3 som 46elks accepterar.
"""
import json
import urllib.request
from pathlib import Path

import config

QUESTIONS = [
    "Hur står det till med min herre denna dag?",
    "Goddag goddag, hur befinner sig herrn?",
    "Får jag fråga hur dagen behandlat herrn?",
    "Hur mår min herre idag?",
    "Goddag, är allt väl med herrn?",
]

FALLBACK_ACK = "Här min herre, ett mood-kort till er. Hoppas dagen blir vacker."


def synthesize(text: str, out_path: Path):
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{config.ELEVENLABS_VOICE_ID}"
    )
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

    for i, text in enumerate(QUESTIONS, start=1):
        synthesize(text, config.AUDIO_DIR / f"q_{i:02d}.mp3")

    synthesize(FALLBACK_ACK, config.AUDIO_DIR / "ack_fallback.mp3")
    print("Klart.")


if __name__ == "__main__":
    main()
