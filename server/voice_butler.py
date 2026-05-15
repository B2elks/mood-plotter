"""Tolka transkriberat svar och generera butler-ack + bild-prompt."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du är en varm psykolog/psykoanalytiker som just frågat
någon "Hur har du det idag?".

Användarens svar: "{user_response}"

Din uppgift: omvandla deras svar till en symbolisk skiss som FANGAR
KANSLAN de beskriver. Tänk Rorschach mötet ett vykort — en visuell
metafor som speglar exakt det de sa.

Returnera ENDAST följande JSON, inget annat:
{{
  "image_prompt": "<English prompt for image generation. Translate the user's feeling into ONE simple visual metaphor. Examples of mappings: 'tired/stressed' -> a curled sleeping cat OR a tea cup with steam OR a hammock between two trees; 'happy/glad' -> a bird in flight OR a sunflower OR a paper boat with sails; 'sad/down' -> a single tree in rain OR a lone bench under a streetlight; 'busy/jaktig' -> a clock with running hands OR scattered leaves blown by wind. PICK ONE concrete symbol that best matches THEIR specific words. The image MUST be a SIMPLE HAND-DRAWN MONOLINE SKETCH — pure WHITE background, CLEAN BLACK OUTLINES only, ~10-20 strokes, no fills/shading/color/gradients. End with: ', simple monoline sketch, hand-drawn doodle style, single thin black pen stroke on white, no shading, no fills, line art only, suitable for AxiDraw pen plotter'.>",
  "butler_ack": "<1-2 meningar svensk replik, varm psykolog-stil men lite gladtig. Ingen 'min herre'-formalia. Meddela att du återskapar känslan i en bild. Exempel: 'Tack för att du delar. Jag återskapar känslan i en bild åt dig nu.'>"
}}"""

FALLBACK = (
    "a single tree on a small hill with two birds in the sky, "
    "simple monoline sketch, hand-drawn doodle style, single thin black "
    "pen stroke on white, no shading, line art only, suitable for AxiDraw "
    "pen plotter",
    "Tack för att du delar. Jag återskapar känslan i en bild åt dig.",
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
