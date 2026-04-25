# Ring & Vinn Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live game show where people call in via 46elks, answer questions, and see results on a TV screen with an animated SVG host character.

**Architecture:** Python asyncio backend handles 46elks WebSocket calls, call queue, Whisper transcription, and GPT answer judging. A show engine orchestrates the game flow and pushes events via WebSocket to a vanilla HTML/JS frontend that displays the animated host, questions, callers, and leaderboard.

**Tech Stack:** Python 3 + asyncio + websockets 14, 46elks WebSocket API, ElevenLabs TTS, OpenAI Whisper + GPT-4o-mini, Vanilla HTML/CSS/JS

---

### Task 1: Project scaffold and questions

**Files:**
- Create: `ring-och-vinn/questions.json`
- Create: `ring-och-vinn/requirements.txt`
- Create: `ring-och-vinn/.env.example`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p /Users/b2/Documents/Proj/LLM/ring-och-vinn/clips/questions
mkdir -p /Users/b2/Documents/Proj/LLM/ring-och-vinn/site/sounds
```

- [ ] **Step 2: Create requirements.txt**

```
websockets==14.2
python-dotenv
```

Write to `ring-och-vinn/requirements.txt`.

- [ ] **Step 3: Create .env.example**

```
OPENAI_API_KEY=sk-...
ELKS_USER=u...
ELKS_PASS=...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=N9IXqS4mrPh2ORd2JQei
ELKS_WS_NUMBER=+4600700021
SHOW_WS_PORT=8115
ELKS_WS_PORT=8116
HTTP_PORT=8117
```

Write to `ring-och-vinn/.env.example`.

- [ ] **Step 4: Create questions.json with 10 demo questions**

```json
[
  {
    "id": 1,
    "type": "quiz",
    "question": "Hur många invånare har Hudiksvall?",
    "answer": "15000",
    "accept": ["15000", "femtontusen", "15 000", "ca 15000", "cirka 15000"],
    "points": 1
  },
  {
    "id": 2,
    "type": "quiz",
    "question": "Vilket år grundades 46elks?",
    "answer": "2014",
    "accept": ["2014", "tvåtusenfjorton"],
    "points": 1
  },
  {
    "id": 3,
    "type": "price",
    "question": "Vad kostar en liter mjölk på ICA?",
    "answer": "15",
    "accept_range": [12, 20],
    "points": 1
  },
  {
    "id": 4,
    "type": "quiz",
    "question": "Vad heter Sveriges längsta flod?",
    "answer": "Klarälven",
    "accept": ["Klarälven", "klarälven", "Göta älv", "Göta älv Klarälven"],
    "points": 1
  },
  {
    "id": 5,
    "type": "quiz",
    "question": "Vilken svensk stad kallas 'Nordens Venedig'?",
    "answer": "Stockholm",
    "accept": ["Stockholm", "stockholm"],
    "points": 1
  },
  {
    "id": 6,
    "type": "open",
    "question": "Nämn ett svenskt varumärke som alla känner till!",
    "answer": "Any well-known Swedish brand like IKEA, Volvo, H&M, Spotify, Ericsson, etc.",
    "points": 2
  },
  {
    "id": 7,
    "type": "price",
    "question": "Vad kostar en Big Mac på McDonalds i Sverige?",
    "answer": "69",
    "accept_range": [55, 85],
    "points": 1
  },
  {
    "id": 8,
    "type": "quiz",
    "question": "Hur många landskap finns det i Sverige?",
    "answer": "25",
    "accept": ["25", "tjugofem"],
    "points": 1
  },
  {
    "id": 9,
    "type": "quiz",
    "question": "Vad heter landskapet där Hudiksvall ligger?",
    "answer": "Hälsingland",
    "accept": ["Hälsingland", "hälsingland"],
    "points": 1
  },
  {
    "id": 10,
    "type": "open",
    "question": "Vad är det bästa med Hudiksvall?",
    "answer": "Any positive answer about Hudiksvall is correct.",
    "points": 2
  }
]
```

Write to `ring-och-vinn/questions.json`.

- [ ] **Step 5: Commit**

```bash
git add ring-och-vinn/
git commit -m "feat: scaffold ring-och-vinn project with questions"
```

---

### Task 2: TTS clip generator

**Files:**
- Create: `ring-och-vinn/generate_clips.py`

- [ ] **Step 1: Create generate_clips.py**

Based on the oloppnare pattern (`/Users/b2/Documents/Proj/LLM/oloppnare/generate_clips.py`). Uses ElevenLabs TTS to generate PCM 24kHz clips.

```python
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
```

Write to `ring-och-vinn/generate_clips.py`.

- [ ] **Step 2: Commit**

```bash
git add ring-och-vinn/generate_clips.py
git commit -m "feat: add TTS clip generator for Ring & Vinn"
```

---

### Task 3: Backend — audio helpers and answer judging

**Files:**
- Create: `ring-och-vinn/audio.py`
- Create: `ring-och-vinn/judge.py`

- [ ] **Step 1: Create audio.py — audio playback and transcription helpers**

Extracted from oloppnare voice_agent.py patterns. Handles PCM audio sending, WAV conversion, Whisper transcription, and silence detection.

```python
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
```

Write to `ring-och-vinn/audio.py`.

- [ ] **Step 2: Create judge.py — answer judging logic**

```python
"""Answer judging — checks caller's transcribed answer against the question."""

import json
import os
import urllib.request

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def judge_answer(question, transcript):
    """Judge if the transcript answers the question correctly.
    Returns {"correct": bool, "explanation": str}
    """
    if not transcript or not transcript.strip():
        return {"correct": False, "explanation": "Inget svar hördes."}

    q_type = question.get("type", "quiz")
    answer_text = transcript.strip()

    # Quiz: check against accept list
    if q_type == "quiz":
        accept = question.get("accept", [])
        answer_lower = answer_text.lower()
        for variant in accept:
            if variant.lower() in answer_lower:
                return {"correct": True, "explanation": f"Rätt! Svaret var {question['answer']}."}
        # Fallback: ask GPT
        return _gpt_judge(question, answer_text)

    # Price/number: check range
    if q_type in ("price", "number"):
        accept_range = question.get("accept_range")
        if accept_range:
            # Extract number from answer
            num = _extract_number(answer_text)
            if num is not None and accept_range[0] <= num <= accept_range[1]:
                return {"correct": True, "explanation": f"Rätt! Svaret var {question['answer']}."}
            elif num is not None:
                return {"correct": False, "explanation": f"Tyvärr! Du sa {num}, rätt svar var {question['answer']}."}
        return _gpt_judge(question, answer_text)

    # Open: always GPT
    return _gpt_judge(question, answer_text)


def _extract_number(text):
    """Try to extract a number from text."""
    import re
    nums = re.findall(r'\d+', text.replace(" ", ""))
    if nums:
        return int(nums[0])
    return None


def _gpt_judge(question, answer_text):
    """Use GPT-4o-mini to judge an answer."""
    system_msg = (
        f"You are judging a game show answer. "
        f"Question: {question['question']}. "
        f"Correct answer: {question['answer']}. "
        f"The contestant said: \"{answer_text}\". "
        f"Is this correct or close enough? Reply with JSON: "
        f'{{\"correct\": true/false, \"explanation\": \"short explanation in Swedish\"}}'
    )

    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": answer_text},
        ],
        "max_tokens": 100,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"].strip()
        return json.loads(content)
    except Exception:
        return {"correct": False, "explanation": "Kunde inte bedöma svaret."}
```

Write to `ring-och-vinn/judge.py`.

- [ ] **Step 3: Commit**

```bash
git add ring-och-vinn/audio.py ring-och-vinn/judge.py
git commit -m "feat: add audio helpers and answer judging"
```

---

### Task 4: Backend — main server with show engine, voice agent, and call queue

**Files:**
- Create: `ring-och-vinn/server.py`

This is the main backend. It runs three async servers:
1. WebSocket for 46elks calls (port 8116)
2. WebSocket for the show frontend (port 8115)
3. HTTP for voice_start webhook (port 8117)

Plus the show engine that orchestrates the game flow.

- [ ] **Step 1: Create server.py**

```python
#!/usr/bin/env python3
"""Ring & Vinn — Live game show server.

Runs:
- 46elks WebSocket server (ELKS_WS_PORT) for phone calls
- Show WebSocket server (SHOW_WS_PORT) for the TV frontend
- HTTP server (HTTP_PORT) for voice_start webhook
- Show engine that orchestrates the game
"""

import asyncio
import base64
import glob as glob_module
import json
import logging
import os
import random
import sys
from collections import deque
from datetime import datetime, timezone

import websockets
from dotenv import load_dotenv

from audio import play_audio, transcribe_audio, wait_for_speech_then_silence, CODEC
from judge import judge_answer

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELKS_USER = os.getenv("ELKS_USER")
ELKS_PASS = os.getenv("ELKS_PASS")

if not OPENAI_API_KEY or not ELKS_USER or not ELKS_PASS:
    log.error("Missing env vars: OPENAI_API_KEY, ELKS_USER, ELKS_PASS")
    sys.exit(1)

SHOW_WS_PORT = int(os.getenv("SHOW_WS_PORT", "8115"))
ELKS_WS_PORT = int(os.getenv("ELKS_WS_PORT", "8116"))
HTTP_PORT = int(os.getenv("HTTP_PORT", "8117"))
ELKS_WS_NUMBER = os.getenv("ELKS_WS_NUMBER", "+4600700021")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIPS_DIR = os.path.join(BASE_DIR, "clips")
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
LEADERBOARD_FILE = os.path.join(BASE_DIR, "leaderboard.json")

# --- Clip loading ---

clips = {}  # category -> list of pcm bytes
question_clips = {}  # question_id -> pcm bytes


def load_clips():
    for prefix in ("intro", "welcome", "qintro", "correct", "wrong",
                   "queue", "ending", "next", "nocallers"):
        clips[prefix] = []
        for f in sorted(glob_module.glob(os.path.join(CLIPS_DIR, f"{prefix}_*.pcm"))):
            with open(f, "rb") as fh:
                clips[prefix].append(fh.read())
        log.info("Loaded %d %s clips", len(clips[prefix]), prefix)

    for f in sorted(glob_module.glob(os.path.join(CLIPS_DIR, "questions", "q_*.pcm"))):
        qid = int(os.path.basename(f).split("_")[1].split(".")[0])
        with open(f, "rb") as fh:
            question_clips[qid] = fh.read()
    log.info("Loaded %d question clips", len(question_clips))


def random_clip(category):
    c = clips.get(category, [])
    return random.choice(c) if c else None


# --- State ---

show_clients = set()  # connected show frontends
call_queue = deque()  # [(call_id, caller_ws, caller_audio, call_closed)]
leaderboard = {}  # caller_name -> points
questions = []
current_question_idx = 0
show_running = False


def load_questions():
    global questions
    with open(QUESTIONS_FILE) as f:
        questions = json.load(f)
    log.info("Loaded %d questions", len(questions))


def save_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)


# --- Show WebSocket (frontend) ---

async def broadcast(event):
    """Send event to all connected show frontends."""
    msg = json.dumps(event)
    for ws in list(show_clients):
        try:
            await ws.send(msg)
        except Exception:
            show_clients.discard(ws)


async def handle_show_client(ws):
    show_clients.add(ws)
    log.info("Show client connected (%d total)", len(show_clients))
    try:
        # Send current state
        await ws.send(json.dumps({
            "type": "init",
            "leaderboard": leaderboard,
            "queue_size": len(call_queue),
            "question_idx": current_question_idx,
            "total_questions": len(questions),
            "running": show_running,
        }))
        async for msg in ws:
            pass  # frontend doesn't send commands (yet)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        show_clients.discard(ws)
        log.info("Show client disconnected (%d total)", len(show_clients))


# --- 46elks call handling ---

async def handle_elks_call(ws):
    """Handle incoming call from 46elks WebSocket."""
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(raw)
    except Exception:
        return

    msg_type = data.get("t") or data.get("type")
    if msg_type not in ("hello", "call_started"):
        return

    call_id = data.get("callid") or data.get("call_id", "unknown")
    caller_from = data.get("from", "anonymous")
    log.info("Call from %s (id=%s)", caller_from, call_id)

    # Start audio streams
    await ws.send(json.dumps({"t": "sending", "format": CODEC}))
    await ws.send(json.dumps({"t": "listening", "format": CODEC}))

    # Record caller audio
    caller_audio = bytearray()
    call_closed = asyncio.Event()

    async def record():
        try:
            async for message in ws:
                msg = json.loads(message)
                mt = msg.get("t") or msg.get("type")
                if mt == "audio":
                    caller_audio.extend(base64.b64decode(msg["data"]))
                elif mt in ("bye", "close", "hangup"):
                    break
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            call_closed.set()

    record_task = asyncio.create_task(record())

    # Play queue message
    queue_clip = random_clip("queue")
    if queue_clip and not call_closed.is_set():
        await play_audio(ws, queue_clip)

    # Add to queue
    ready_event = asyncio.Event()
    entry = {
        "call_id": call_id,
        "caller_from": caller_from,
        "ws": ws,
        "caller_audio": caller_audio,
        "call_closed": call_closed,
        "record_task": record_task,
        "ready_event": ready_event,
    }
    call_queue.append(entry)
    await broadcast({"type": "queue_update", "size": len(call_queue)})
    log.info("Caller %s added to queue (size=%d)", caller_from, len(call_queue))

    # Wait until show engine picks us or call hangs up
    done, pending = await asyncio.wait(
        [asyncio.create_task(ready_event.wait()),
         asyncio.create_task(call_closed.wait())],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
        t.cancel()

    if call_closed.is_set() and not ready_event.is_set():
        # Caller hung up before being picked
        if entry in call_queue:
            call_queue.remove(entry)
            await broadcast({"type": "queue_update", "size": len(call_queue)})
        log.info("Caller %s hung up from queue", caller_from)
        return

    # Caller was picked by show engine — wait for show to finish with them
    # The show engine handles the rest via the entry dict
    await call_closed.wait()

    if not record_task.done():
        try:
            await asyncio.wait_for(record_task, timeout=3)
        except asyncio.TimeoutError:
            record_task.cancel()


# --- Show Engine ---

async def run_show():
    """Main show loop — runs through questions, picks callers, judges answers."""
    global current_question_idx, show_running
    show_running = True

    load_questions()
    leaderboard.clear()

    # Play intro
    await broadcast({"type": "show_state", "state": "intro"})
    intro_clip = random_clip("intro")
    # No caller to play to yet — intro is visual only
    await asyncio.sleep(3)

    for idx, question in enumerate(questions):
        current_question_idx = idx

        # Broadcast question
        await broadcast({
            "type": "question",
            "idx": idx,
            "total": len(questions),
            "question": question["question"],
            "q_type": question.get("type", "quiz"),
            "points": question.get("points", 1),
        })
        await broadcast({"type": "show_state", "state": "asking"})
        log.info("Question %d: %s", idx + 1, question["question"])

        # Wait for a caller in queue (up to 30s)
        waited = 0
        while not call_queue and waited < 30:
            await asyncio.sleep(1)
            waited += 1
            if waited % 10 == 0:
                await broadcast({"type": "show_state", "state": "waiting"})

        if not call_queue:
            log.info("No callers for question %d, skipping", idx + 1)
            await broadcast({"type": "show_state", "state": "waiting"})
            await asyncio.sleep(2)
            continue

        # Pick first caller from queue
        entry = call_queue.popleft()
        await broadcast({"type": "queue_update", "size": len(call_queue)})

        caller_ws = entry["ws"]
        caller_audio = entry["caller_audio"]
        call_closed = entry["call_closed"]
        caller_from = entry["caller_from"]
        caller_name = caller_from[-4:] if len(caller_from) > 4 else caller_from

        await broadcast({
            "type": "caller_active",
            "name": caller_name,
            "caller_from": caller_from,
        })
        await broadcast({"type": "show_state", "state": "listening"})
        log.info("Picked caller %s for question %d", caller_name, idx + 1)

        # Signal the caller handler that they're live
        entry["ready_event"].set()

        if call_closed.is_set():
            log.info("Caller already gone")
            continue

        # Play welcome + question
        welcome_clip = random_clip("welcome")
        if welcome_clip and not call_closed.is_set():
            await play_audio(caller_ws, welcome_clip)

        q_clip = question_clips.get(question["id"])
        if q_clip and not call_closed.is_set():
            await play_audio(caller_ws, q_clip)

        # Listen for answer (15s timeout)
        if not call_closed.is_set():
            speech_start = len(caller_audio)
            spoke = await wait_for_speech_then_silence(
                caller_audio, call_closed, start_pos=speech_start, timeout_checks=60
            )

            if spoke:
                speech_data = bytes(caller_audio[speech_start:])
                transcript = await transcribe_audio(speech_data)
                log.info("Transcript: %s", transcript)

                await broadcast({
                    "type": "answer",
                    "name": caller_name,
                    "transcript": transcript,
                })

                # Judge answer
                result = judge_answer(question, transcript)
                log.info("Result: %s", result)

                if result["correct"]:
                    pts = question.get("points", 1)
                    leaderboard[caller_name] = leaderboard.get(caller_name, 0) + pts
                    save_leaderboard()
                    correct_clip = random_clip("correct")
                    if correct_clip and not call_closed.is_set():
                        await play_audio(caller_ws, correct_clip)
                    await broadcast({"type": "show_state", "state": "correct"})
                else:
                    wrong_clip = random_clip("wrong")
                    if wrong_clip and not call_closed.is_set():
                        await play_audio(caller_ws, wrong_clip)
                    await broadcast({"type": "show_state", "state": "wrong"})

                await broadcast({
                    "type": "result",
                    "name": caller_name,
                    "correct": result["correct"],
                    "explanation": result.get("explanation", ""),
                    "points": question.get("points", 1) if result["correct"] else 0,
                })
                await broadcast({"type": "leaderboard", "scores": leaderboard})
            else:
                log.info("No speech detected from caller")
                await broadcast({"type": "show_state", "state": "wrong"})

        # Hang up the caller
        if not call_closed.is_set():
            try:
                await caller_ws.send(json.dumps({"t": "hangup"}))
            except Exception:
                pass

        await asyncio.sleep(3)

        # Next question transition
        if idx < len(questions) - 1:
            await broadcast({"type": "show_state", "state": "idle"})
            await broadcast({"type": "leaderboard", "scores": leaderboard})
            await asyncio.sleep(2)

    # Show ended
    await broadcast({"type": "show_state", "state": "ended"})
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    winner = sorted_lb[0] if sorted_lb else None
    await broadcast({
        "type": "show_ended",
        "winner": {"name": winner[0], "points": winner[1]} if winner else None,
        "leaderboard": leaderboard,
    })
    log.info("Show ended! Winner: %s", winner)
    show_running = False


# --- HTTP server ---

async def handle_http(reader, writer):
    """HTTP server for voice_start webhook."""
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=5)
        if not request_line:
            return

        parts = request_line.decode().strip().split()
        method = parts[0] if parts else "GET"
        path = (parts[1] if len(parts) > 1 else "/").split("?")[0]

        # Read headers
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break

        body = json.dumps({"connect": ELKS_WS_NUMBER}).encode()
        if path == "/voice/start":
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"\r\n"
            ).encode()
        elif path == "/api/start":
            if not show_running:
                asyncio.create_task(run_show())
                resp = json.dumps({"ok": True, "message": "Show started"}).encode()
            else:
                resp = json.dumps({"ok": False, "message": "Show already running"}).encode()
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(resp)}\r\n"
                f"\r\n"
            ).encode()
            body = resp
        elif path == "/api/status":
            status = json.dumps({
                "running": show_running,
                "queue_size": len(call_queue),
                "question_idx": current_question_idx,
                "total_questions": len(questions),
                "leaderboard": leaderboard,
            }).encode()
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: application/json\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Content-Length: {len(status)}\r\n"
                f"\r\n"
            ).encode()
            body = status
        else:
            msg = b'{"error":"not found"}'
            header = (
                f"HTTP/1.1 404 Not Found\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(msg)}\r\n"
                f"\r\n"
            ).encode()
            body = msg

        writer.write(header + body)
        await writer.drain()
    except Exception as e:
        log.error("HTTP error: %s", e)
    finally:
        writer.close()


# --- Main ---

async def main():
    load_clips()
    load_questions()

    # Start servers
    await asyncio.start_server(handle_http, "0.0.0.0", HTTP_PORT)
    log.info("HTTP server on port %d", HTTP_PORT)

    async with websockets.serve(handle_show_client, "0.0.0.0", SHOW_WS_PORT):
        log.info("Show WS on port %d", SHOW_WS_PORT)
        async with websockets.serve(handle_elks_call, "0.0.0.0", ELKS_WS_PORT):
            log.info("46elks WS on port %d", ELKS_WS_PORT)
            log.info("Ring & Vinn ready! POST /api/start to begin")
            await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
```

Write to `ring-och-vinn/server.py`.

- [ ] **Step 2: Commit**

```bash
git add ring-och-vinn/server.py
git commit -m "feat: add main server with show engine, voice agent, and queue"
```

---

### Task 5: Frontend — Show page with SVG character

**Files:**
- Create: `ring-och-vinn/site/index.html`
- Create: `ring-och-vinn/site/style.css`
- Create: `ring-och-vinn/site/show.js`

- [ ] **Step 1: Create index.html — game show layout**

Classic game show layout: top bar with logo + live indicator, left side with SVG character (40%), right side with question + caller info (60%), bottom ticker with phone number + leaderboard.

Write to `ring-och-vinn/site/index.html`:

```html
<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ring & Vinn</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- Top bar -->
  <div class="topbar">
    <div class="logo">📺 RING & VINN</div>
    <div class="live-badge"><span class="live-dot"></span> LIVE</div>
  </div>

  <!-- Main area -->
  <div class="main">
    <!-- Left: Character -->
    <div class="character-panel" id="character-panel">
      <svg id="host" viewBox="0 0 200 280" class="host-svg">
        <!-- Body -->
        <rect x="50" y="140" width="100" height="100" rx="20" fill="#ff8800"/>
        <!-- Jacket lapels -->
        <polygon points="80,140 100,180 50,240" fill="#e07000" opacity="0.5"/>
        <polygon points="120,140 100,180 150,240" fill="#e07000" opacity="0.5"/>
        <!-- Head -->
        <circle cx="100" cy="90" r="50" fill="#ffcc66"/>
        <!-- Eyes -->
        <g id="eyes">
          <ellipse cx="80" cy="82" rx="8" ry="10" fill="#333"/>
          <ellipse cx="120" cy="82" rx="8" ry="10" fill="#333"/>
          <circle cx="83" cy="79" r="3" fill="white" opacity="0.7"/>
          <circle cx="123" cy="79" r="3" fill="white" opacity="0.7"/>
        </g>
        <!-- Eyebrows -->
        <g id="eyebrows">
          <line x1="68" y1="68" x2="90" y2="70" stroke="#8B6914" stroke-width="4" stroke-linecap="round"/>
          <line x1="110" y1="70" x2="132" y2="68" stroke="#8B6914" stroke-width="4" stroke-linecap="round"/>
        </g>
        <!-- Mouth -->
        <g id="mouth">
          <path d="M75 105 Q100 125 125 105" stroke="#333" stroke-width="4" fill="none" stroke-linecap="round"/>
        </g>
        <!-- Bow tie -->
        <polygon points="85,142 100,150 115,142 100,158" fill="#ff4444"/>
        <!-- Microphone -->
        <g id="mic" transform="translate(145,100)">
          <rect x="0" y="0" width="10" height="30" rx="5" fill="#666"/>
          <circle cx="5" cy="-2" r="8" fill="#888"/>
          <circle cx="5" cy="-2" r="5" fill="#999"/>
        </g>
        <!-- Arms -->
        <g id="left-arm">
          <path d="M50,160 Q20,180 30,220" stroke="#ff8800" stroke-width="16" fill="none" stroke-linecap="round"/>
        </g>
        <g id="right-arm">
          <path d="M150,160 Q180,180 170,220" stroke="#ff8800" stroke-width="16" fill="none" stroke-linecap="round"/>
        </g>
      </svg>
      <div class="host-name">PROGRAMLEDAREN</div>
    </div>

    <!-- Right: Question panel -->
    <div class="question-panel">
      <div class="question-box" id="question-box">
        <div class="question-num" id="question-num">VÄNTAR PÅ START</div>
        <div class="question-text" id="question-text">Ring numret nedan för att vara med!</div>
      </div>
      <div class="caller-area">
        <div class="caller-status" id="queue-info">📞 0 i kö</div>
        <div class="caller-status caller-active" id="caller-info" style="display:none;">🎤 <span id="caller-name"></span></div>
      </div>
      <div class="answer-area" id="answer-area" style="display:none;">
        <div class="answer-label">SVAR:</div>
        <div class="answer-text" id="answer-text"></div>
      </div>
      <div class="result-area" id="result-area" style="display:none;">
        <div class="result-icon" id="result-icon"></div>
        <div class="result-text" id="result-text"></div>
      </div>
    </div>
  </div>

  <!-- Bottom ticker -->
  <div class="ticker">
    <div class="phone-number" id="phone-number">📞 Ring: XXX-XXX XX XX</div>
    <div class="leaderboard" id="leaderboard">⭐ Väntar på deltagare...</div>
  </div>

  <!-- Confetti canvas -->
  <canvas id="confetti" style="position:fixed;inset:0;pointer-events:none;z-index:100;"></canvas>

  <script src="show.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create style.css — game show styling**

Write to `ring-och-vinn/site/style.css`. Full game show styling with:
- Dark gradient background
- Animated top bar with red/orange gradient
- Character panel with subtle glow
- Question box with border animations
- Caller status badges
- Result animations (correct=green glow+confetti, wrong=red shake)
- Leaderboard ticker
- CSS keyframes for blink, pulse, shake, slide-in, glow

```css
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #0d0d20;
  --surface: #1a1a3a;
  --accent: #ff8800;
  --accent2: #ffcc00;
  --correct: #22c55e;
  --wrong: #ef4444;
  --text: #f0f0f0;
  --muted: #888;
}

body {
  font-family: 'DM Sans', system-ui, sans-serif;
  background: linear-gradient(135deg, #0d0d20, #1a0a2a);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Top bar */
.topbar {
  background: linear-gradient(90deg, #cc2200, #ff8800);
  padding: 12px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.logo {
  font-family: 'Syne', sans-serif;
  font-weight: 800;
  font-size: 1.4rem;
  letter-spacing: 0.05em;
}
.live-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}
.live-dot {
  width: 10px; height: 10px;
  background: white;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0.6); }
  50% { opacity: 0.7; box-shadow: 0 0 0 8px transparent; }
}

/* Main layout */
.main {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* Character panel */
.character-panel {
  width: 40%;
  background: linear-gradient(180deg, rgba(255,136,0,0.05), rgba(255,136,0,0.02));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  position: relative;
}
.host-svg {
  width: 60%;
  max-width: 280px;
  filter: drop-shadow(0 4px 20px rgba(255,136,0,0.2));
}
.host-name {
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--accent2);
  letter-spacing: 0.15em;
}

/* Question panel */
.question-panel {
  width: 60%;
  padding: 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 20px;
}
.question-box {
  background: var(--surface);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  transition: border-color 0.3s;
}
.question-box.active {
  border-color: var(--accent);
  box-shadow: 0 0 30px rgba(255,136,0,0.1);
}
.question-num {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 12px;
}
.question-text {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.4;
}

/* Caller area */
.caller-area {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.caller-status {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 0.9rem;
}
.caller-active {
  background: rgba(34,197,94,0.1);
  border-color: rgba(34,197,94,0.3);
  color: var(--correct);
  animation: glow-green 2s ease-in-out infinite;
}
@keyframes glow-green {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.2); }
  50% { box-shadow: 0 0 20px 0 rgba(34,197,94,0.1); }
}

/* Answer area */
.answer-area {
  text-align: center;
  padding: 16px;
}
.answer-label {
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  color: var(--muted);
  margin-bottom: 6px;
}
.answer-text {
  font-size: 1.2rem;
  font-style: italic;
  color: var(--accent2);
}

/* Result area */
.result-area {
  text-align: center;
  padding: 20px;
  animation: pop-in 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes pop-in {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}
.result-icon { font-size: 3rem; margin-bottom: 8px; }
.result-text { font-size: 1.1rem; font-weight: 600; }
.result-area.correct { color: var(--correct); }
.result-area.wrong { color: var(--wrong); }

/* Ticker */
.ticker {
  background: rgba(0,0,0,0.5);
  border-top: 1px solid rgba(255,255,255,0.1);
  padding: 10px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}
.phone-number { color: var(--accent2); font-weight: 600; }
.leaderboard { color: var(--muted); }

/* Shake animation for wrong answer */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}
.shake { animation: shake 0.5s ease; }

/* SVG character animations */
@keyframes blink {
  0%, 45%, 55%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.1); }
}
#eyes { transform-origin: center; animation: blink 4s ease-in-out infinite; }

@keyframes talk {
  0%, 100% { d: path("M75 105 Q100 125 125 105"); }
  25% { d: path("M75 108 Q100 118 125 108"); }
  50% { d: path("M75 105 Q100 128 125 105"); }
  75% { d: path("M75 110 Q100 115 125 110"); }
}

.host-talking #mouth path {
  animation: talk 0.3s ease-in-out infinite;
}

.host-celebrating #right-arm {
  animation: wave 0.5s ease-in-out infinite alternate;
}
@keyframes wave {
  from { transform: rotate(0deg); }
  to { transform: rotate(-20deg); }
}
```

- [ ] **Step 3: Create show.js — WebSocket client and animations**

Write to `ring-och-vinn/site/show.js`:

```javascript
const WS_URL = `ws://${location.hostname}:8115`;

const questionNum = document.getElementById('question-num');
const questionText = document.getElementById('question-text');
const questionBox = document.getElementById('question-box');
const queueInfo = document.getElementById('queue-info');
const callerInfo = document.getElementById('caller-info');
const callerName = document.getElementById('caller-name');
const answerArea = document.getElementById('answer-area');
const answerText = document.getElementById('answer-text');
const resultArea = document.getElementById('result-area');
const resultIcon = document.getElementById('result-icon');
const resultText = document.getElementById('result-text');
const leaderboardEl = document.getElementById('leaderboard');
const hostSvg = document.getElementById('host');
const confettiCanvas = document.getElementById('confetti');
const ctx = confettiCanvas.getContext('2d');

let ws = null;
let confettiParticles = [];

function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => console.log('Show WS connected');

  ws.onmessage = (e) => {
    const event = JSON.parse(e.data);
    handleEvent(event);
  };

  ws.onclose = () => {
    console.log('Show WS disconnected, reconnecting...');
    setTimeout(connect, 2000);
  };
}

function handleEvent(event) {
  switch (event.type) {
    case 'init':
      updateLeaderboard(event.leaderboard);
      queueInfo.textContent = `📞 ${event.queue_size} i kö`;
      break;

    case 'question':
      questionNum.textContent = `FRÅGA ${event.idx + 1} AV ${event.total}`;
      questionText.textContent = event.question;
      questionBox.classList.add('active');
      answerArea.style.display = 'none';
      resultArea.style.display = 'none';
      callerInfo.style.display = 'none';
      setHostState('asking');
      break;

    case 'caller_active':
      callerName.textContent = event.name + ' svarar...';
      callerInfo.style.display = '';
      setHostState('listening');
      break;

    case 'queue_update':
      queueInfo.textContent = `📞 ${event.size} i kö`;
      break;

    case 'answer':
      answerArea.style.display = '';
      answerText.textContent = event.transcript;
      break;

    case 'result':
      resultArea.style.display = '';
      resultArea.className = 'result-area ' + (event.correct ? 'correct' : 'wrong');
      resultIcon.textContent = event.correct ? '🎉' : '😢';
      resultText.textContent = event.explanation;
      if (event.correct) {
        setHostState('celebrating');
        fireConfetti();
      } else {
        setHostState('sad');
        questionBox.classList.add('shake');
        setTimeout(() => questionBox.classList.remove('shake'), 600);
      }
      break;

    case 'leaderboard':
      updateLeaderboard(event.scores);
      break;

    case 'show_state':
      if (event.state === 'idle') {
        setHostState('idle');
        questionBox.classList.remove('active');
        callerInfo.style.display = 'none';
        answerArea.style.display = 'none';
        resultArea.style.display = 'none';
      } else if (event.state === 'waiting') {
        setHostState('waiting');
      } else if (event.state === 'ended') {
        setHostState('celebrating');
      }
      break;

    case 'show_ended':
      questionNum.textContent = 'SHOWEN ÄR SLUT!';
      if (event.winner) {
        questionText.textContent = `🏆 Vinnare: ${event.winner.name} med ${event.winner.points} poäng!`;
      } else {
        questionText.textContent = 'Ingen vinnare denna gång!';
      }
      fireConfetti();
      break;
  }
}

function setHostState(state) {
  const panel = document.getElementById('character-panel');
  panel.className = 'character-panel';
  if (state === 'asking') panel.classList.add('host-talking');
  else if (state === 'celebrating') panel.classList.add('host-celebrating');
}

function updateLeaderboard(scores) {
  if (!scores || Object.keys(scores).length === 0) {
    leaderboardEl.textContent = '⭐ Väntar på deltagare...';
    return;
  }
  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const medals = ['🥇', '🥈', '🥉'];
  leaderboardEl.textContent = sorted.slice(0, 5).map((entry, i) =>
    `${medals[i] || '⭐'} ${entry[0]} ${entry[1]}p`
  ).join('  ·  ');
}

// --- Confetti ---
function fireConfetti() {
  confettiCanvas.width = window.innerWidth;
  confettiCanvas.height = window.innerHeight;
  confettiParticles = [];
  const colors = ['#ff8800', '#ffcc00', '#ff4444', '#22c55e', '#3b82f6', '#fff'];
  for (let i = 0; i < 150; i++) {
    confettiParticles.push({
      x: Math.random() * confettiCanvas.width,
      y: -20 - Math.random() * 200,
      w: 6 + Math.random() * 6,
      h: 4 + Math.random() * 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 4,
      vy: 2 + Math.random() * 4,
      rot: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 10,
    });
  }
  animateConfetti();
}

function animateConfetti() {
  ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
  let alive = false;
  for (const p of confettiParticles) {
    if (p.y > confettiCanvas.height + 20) continue;
    alive = true;
    p.x += p.vx;
    p.y += p.vy;
    p.rot += p.rotSpeed;
    p.vy += 0.05;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot * Math.PI / 180);
    ctx.fillStyle = p.color;
    ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
    ctx.restore();
  }
  if (alive) requestAnimationFrame(animateConfetti);
  else ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
}

// --- Start ---
connect();
```

- [ ] **Step 4: Commit**

```bash
git add ring-och-vinn/site/
git commit -m "feat: add show page with SVG character and game UI"
```

---

### Task 6: Systemd service and nginx config

**Files:**
- Create: `ring-och-vinn/ring-och-vinn.service`
- Create: `ring-och-vinn/ring-och-vinn-nginx.conf`

- [ ] **Step 1: Create systemd service file**

```ini
[Unit]
Description=Ring & Vinn Game Show
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/ring-och-vinn
Environment=PATH=/var/www/ring-och-vinn/venv/bin
EnvironmentFile=/var/www/ring-och-vinn/.env
ExecStart=/var/www/ring-och-vinn/venv/bin/python server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Write to `ring-och-vinn/ring-och-vinn.service`.

- [ ] **Step 2: Create nginx config**

```nginx
server {
    server_name ringochvinn.46hudik.se;

    root /var/www/ring-och-vinn/site;
    index index.html;

    # Voice webhook
    location /voice/start {
        proxy_pass http://127.0.0.1:8117;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8117;
        proxy_set_header Host $host;
    }

    # Show WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8115;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    location / {
        try_files $uri $uri/ =404;
    }

    listen 80;
}
```

Write to `ring-och-vinn/ring-och-vinn-nginx.conf`.

- [ ] **Step 3: Commit**

```bash
git add ring-och-vinn/ring-och-vinn.service ring-och-vinn/ring-och-vinn-nginx.conf
git commit -m "feat: add systemd service and nginx config"
```

---

### Task 7: Deploy to server and test

- [ ] **Step 1: Deploy files**

```bash
rsync -avz --exclude='__pycache__' --exclude='venv' --exclude='clips' --exclude='.env' \
  /Users/b2/Documents/Proj/LLM/ring-och-vinn/ \
  root@elkwonders.46elks.com:/var/www/ring-och-vinn/
```

- [ ] **Step 2: Setup venv and install deps on server**

```bash
ssh root@elkwonders.46elks.com "cd /var/www/ring-och-vinn && python3 -m venv venv && venv/bin/pip install -r requirements.txt"
```

- [ ] **Step 3: Create .env on server**

Copy from `.env.example` and fill in real values. Use same API keys as oloppnare:

```bash
ssh root@elkwonders.46elks.com "cp /home/kumamonwithme/oloppnare/.env /var/www/ring-och-vinn/.env"
```

Then edit to add the Ring & Vinn specific ports:

```bash
ssh root@elkwonders.46elks.com "cat >> /var/www/ring-och-vinn/.env << 'EOF'
SHOW_WS_PORT=8115
ELKS_WS_PORT=8116
HTTP_PORT=8117
ELKS_WS_NUMBER=+4600700021
EOF"
```

- [ ] **Step 4: Generate TTS clips**

```bash
ssh root@elkwonders.46elks.com "cd /var/www/ring-och-vinn && venv/bin/python generate_clips.py"
```

- [ ] **Step 5: Open firewall ports**

```bash
ssh root@elkwonders.46elks.com "ufw allow 8115 && ufw allow 8116 && ufw allow 8117"
```

- [ ] **Step 6: Install and start service**

```bash
ssh root@elkwonders.46elks.com "cp /var/www/ring-och-vinn/ring-och-vinn.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable ring-och-vinn && systemctl start ring-och-vinn"
```

- [ ] **Step 7: Setup nginx + SSL**

```bash
ssh root@elkwonders.46elks.com "cp /var/www/ring-och-vinn/ring-och-vinn-nginx.conf /etc/nginx/sites-available/ringochvinn.46hudik.se && ln -sf /etc/nginx/sites-available/ringochvinn.46hudik.se /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx"
```

SSL with certbot (once DNS for 46hudik.se propagates):

```bash
ssh root@elkwonders.46elks.com "certbot --nginx -d ringochvinn.46hudik.se --non-interactive --agree-tos"
```

- [ ] **Step 8: Update show.js to use proxied WebSocket**

Change the WS_URL in show.js to use the nginx-proxied path instead of a direct port:

```javascript
const WS_URL = `wss://${location.hostname}/ws`;
```

- [ ] **Step 9: Test the show**

Start the show: `curl -X POST https://ringochvinn.46hudik.se/api/start`

Open `https://ringochvinn.46hudik.se` in browser to see the show page.

- [ ] **Step 10: Commit final adjustments**

```bash
git add -A ring-och-vinn/
git commit -m "feat: deployment config and final adjustments"
```
