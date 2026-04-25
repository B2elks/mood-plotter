#!/usr/bin/env python3
"""Generate pre-recorded audio clips for Ring & Vinn using ElevenLabs TTS.

Run on the server:
  cd ~/ring-och-vinn && venv/bin/python generate_clips.py
"""

import json
import os
import time
import urllib.request


def load_env():
    env = {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


env = load_env()
API_KEY = env["ELEVENLABS_API_KEY"]
VOICE_ID = env.get("ELEVENLABS_VOICE_ID", "N9IXqS4mrPh2ORd2JQei")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
QUESTIONS_DIR = os.path.join(CLIPS_DIR, "questions")
os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(QUESTIONS_DIR, exist_ok=True)

INTROS = [
    "Välkommen till Ring och Vinn! Ringen som ger dig chansen att vinna!",
    "Ring och Vinn är igång! Vem vågar ringa?",
    "Hej och välkomna till Ring och Vinn! Är ni redo?",
]

WELCOME = [
    "Välkommen! Du är live! Lyssna nu på frågan!",
    "Hej där! Du är med i Ring och Vinn! Här kommer frågan!",
    "Grattis, du är live! Redo? Här kommer det!",
    "Välkommen in! Nu gäller det! Lyssna noga!",
]

QUESTION_INTROS = [
    "Och frågan lyder...",
    "Här kommer frågan!",
    "Lyssna noga nu...",
]

CORRECT = [
    "RÄTT SVAR! Fantastiskt! Du får poäng!",
    "Helt rätt! Vilken hjärna! Poäng till dig!",
    "KORREKT! Snyggt jobbat! Du är med i toppen!",
    "JA! Det var rätt! Vilken vinnarskalle!",
]

WRONG = [
    "Tyvärr, det var inte rätt! Bättre lycka nästa gång!",
    "Nej, det stämmer inte! Men tack för att du ringde!",
    "Aj aj aj, fel svar! Men det var nära!",
    "Inte riktigt! Det rätta svaret var ett annat!",
]

QUEUE = [
    "Du är i kön! Häng kvar, vi plockar dig snart!",
    "Vänta lite, du är snart live! Häng kvar i luren!",
    "Bra att du ringde! Du står i kö, vi kommer till dig strax!",
]

ENDING = [
    "Tack för idag alla! Det var allt för denna omgång av Ring och Vinn!",
]

NEXT_QUESTION = [
    "Nästa fråga! Här kommer den!",
    "Vi går vidare! Redo för nästa?",
]

NO_CALLERS = [
    "Ingen har ringt in ännu! Ring numret på skärmen!",
    "Telefonerna är tysta! Våga ring!",
]


def generate_clip(text, filepath):
    """Generate a TTS clip using ElevenLabs and save as raw PCM 24kHz."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        duration = os.path.getsize(filepath) / 48000
        print(f"  {os.path.basename(filepath)}: exists ({duration:.1f}s) — skipping")
        return

    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        f"?output_format=pcm_24000"
    )
    data = json.dumps({
        "text": text,
        "model_id": "eleven_turbo_v2_5",
    }).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    pcm_data = resp.read()

    with open(filepath, "wb") as f:
        f.write(pcm_data)

    duration = len(pcm_data) / 48000
    print(f"  {os.path.basename(filepath)}: {len(pcm_data):,} bytes ({duration:.1f}s)")
    time.sleep(0.3)


def generate_category(name, texts, prefix):
    print(f"\n{name}...")
    for i, text in enumerate(texts):
        generate_clip(text, os.path.join(CLIPS_DIR, f"{prefix}_{i}.pcm"))


print(f"Voice: {VOICE_ID}")

generate_category("Intros", INTROS, "intro")
generate_category("Welcome", WELCOME, "welcome")
generate_category("Question intros", QUESTION_INTROS, "qintro")
generate_category("Correct", CORRECT, "correct")
generate_category("Wrong", WRONG, "wrong")
generate_category("Queue", QUEUE, "queue")
generate_category("Ending", ENDING, "ending")
generate_category("Next question", NEXT_QUESTION, "next")
generate_category("No callers", NO_CALLERS, "nocallers")

# Generate per-question clips
print("\nQuestion clips...")
with open(os.path.join(BASE_DIR, "questions.json")) as f:
    questions = json.load(f)

for q in questions:
    filepath = os.path.join(QUESTIONS_DIR, f"q_{q['id']}.pcm")
    generate_clip(q["question"], filepath)

total = sum(len(x) for x in [INTROS, WELCOME, QUESTION_INTROS, CORRECT, WRONG, QUEUE, ENDING, NEXT_QUESTION, NO_CALLERS]) + len(questions)
print(f"\nDone! {total} clips generated in {CLIPS_DIR}/")
