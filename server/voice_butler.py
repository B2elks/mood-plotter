"""Tolka transkriberat svar och generera butler-ack + bild-prompt."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du är en charmig brittisk-svensk butler.
Användaren har precis svarat på frågan "Hur mår min herre idag?".

Användarens svar: "{user_response}"

Returnera ENDAST följande JSON-objekt, inget annat:
{{
  "image_prompt": "<an English prompt for image generation. The image MUST be an EXTREMELY MINIMAL BLACK INK LINE DRAWING — like a child's stick-figure sketch — on pure WHITE background. Only 3-7 main lines total. ABSOLUTELY no shading, no hatching, no cross-hatching, no gradients, no fill, no color, no grayscale, no texture, no patterns, no thick areas, no background details. Just a few clean thin black outlines depicting a single simple subject. Examples: a single tree (just a trunk and a few branches), a sun (just a circle with rays), a heart, a smiley face, a flower with 5 petals, a sailboat, a teacup. Avoid all complexity. Always end the prompt with: ', ultra-minimal black line drawing, 5 lines only, child-like simplicity, no shading, no details, pure white background, suitable for AxiDraw pen plotter'.>",
  "butler_ack": "<1-2 meningar svensk butler-replik. Erkänn humöret mjukt, meddela att kortet är på väg. Tilltala alltid 'min herre' eller 'herrn'.>"
}}"""

FALLBACK = (
    "a single tree on a small hill with two birds in the sky, "
    "minimalist black line drawing on white, single thin pen stroke, "
    "no shading, suitable for AxiDraw pen plotter",
    "Här min herre, ett mood-kort till er. Hoppas dagen blir vacker.",
)


@dataclass
class ButlerResult:
    image_prompt: str
    butler_ack: str


def _call_openai(system: str, api_key: str):
    client = OpenAI(api_key=api_key)
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}],
        temperature=0.8,
        response_format={"type": "json_object"},
    )


def analyze_response(transcribed_text: str, api_key: str) -> ButlerResult:
    """Returnera ButlerResult med bildprompt + butler-ack. Fallback vid fel."""
    if not transcribed_text or not transcribed_text.strip():
        return ButlerResult(*FALLBACK)

    try:
        prompt = SYSTEM_PROMPT.format(user_response=transcribed_text.replace('"', "'"))
        response = _call_openai(prompt, api_key)
        content = response.choices[0].message.content
        data = json.loads(content)
        return ButlerResult(
            image_prompt=data["image_prompt"],
            butler_ack=data["butler_ack"],
        )
    except Exception as e:
        log.error("LLM-fel, använder fallback: %s", e)
        return ButlerResult(*FALLBACK)


def _call_whisper(audio_file, api_key: str):
    client = OpenAI(api_key=api_key)
    return client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="sv",
    )


def transcribe_audio(audio_path: Path, api_key: str) -> str:
    """Transkribera en wav/mp3-fil. Returnerar tom sträng vid fel."""
    try:
        with open(audio_path, "rb") as f:
            response = _call_whisper(f, api_key)
        return response.text.strip()
    except Exception as e:
        log.error("Whisper-fel: %s", e)
        return ""
