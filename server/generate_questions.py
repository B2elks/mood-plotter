"""Engångsskript: generera q_NN.mp3 i audio/ via ElevenLabs.

Kör en gång efter setup. Skapar också ack_fallback.mp3.
"""
import sys
from pathlib import Path

from elevenlabs.client import ElevenLabs

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
    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
    audio_iter = client.generate(
        text=text,
        voice=config.ELEVENLABS_VOICE_ID,
        model="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    out_path.write_bytes(b"".join(audio_iter))
    print(f"Skapade {out_path}")


def main():
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for i, text in enumerate(QUESTIONS, start=1):
        synthesize(text, config.AUDIO_DIR / f"q_{i:02d}.mp3")

    synthesize(FALLBACK_ACK, config.AUDIO_DIR / "ack_fallback.mp3")
    print("Klart.")


if __name__ == "__main__":
    main()
