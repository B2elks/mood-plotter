# PIR Mood Plotter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bygg en självkiosk där en PIR-sensor på en Raspberry Pi triggar ett kort butler-samtal som genererar och plottar ett DALL·E-baserat mood-kort på en AxiDraw.

**Architecture:** Server/klient i två noder. Server (`mood-plotter-server`, port 8095, skyttberg.nu) orkestrerar 46elks-samtal, Whisper-transkribering, GPT-4o-mini-tolkning, ElevenLabs-TTS och DALL·E + vpype. Klient (`mood-plotter-pi`, Raspberry Pi) läser PIR och kör AxiDraw via WebSocket-koppling till servern.

**Tech Stack:** Python 3.11, aiohttp, websockets, gpiozero, pyaxidraw, vpype + vpype-vectrace, OpenAI SDK (Whisper + DALL·E 3 + GPT-4o-mini), ElevenLabs SDK, sqlite3, systemd, nginx.

**Spec:** [`docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md`](../specs/2026-05-09-pir-mood-plotter-design.md)

---

## Filstruktur

```
mood-plotter/
├── server/
│   ├── server.py                  # aiohttp-app, routes
│   ├── elks_handler.py            # 46elks-actions + signaturkontroll
│   ├── voice_butler.py            # GPT-4o-mini-tolkning av svar
│   ├── tts_cache.py               # Slumpa pre-genererad fråga
│   ├── tts_live.py                # ElevenLabs API för ack
│   ├── image_pipeline.py          # DALL·E → vpype → SVG
│   ├── ws_dispatcher.py           # WS-klientregistry + broadcast
│   ├── cooldown.py                # sqlite-baserad cooldown
│   ├── config.py                  # Konfig läses från env + .env
│   ├── generate_questions.py      # Engångsskript: skapa fråge-MP3:er
│   ├── audio/                     # Pre-genererade och live ack-MP3:er
│   ├── requirements.txt
│   └── mood-plotter-server.service
├── pi/
│   ├── pir_watcher.py             # gpiozero MotionSensor + HTTP trigger
│   ├── plotter_client.py          # WS-klient + pyaxidraw
│   ├── config.py
│   ├── requirements.txt
│   └── mood-plotter-pi.service
├── tests/
│   ├── test_cooldown.py
│   ├── test_elks_handler.py
│   ├── test_voice_butler.py
│   ├── test_tts_cache.py
│   ├── test_image_pipeline.py
│   ├── test_ws_dispatcher.py
│   └── test_server_integration.py
├── pytest.ini
└── README.md
```

---

## Task 1: Projekt-scaffolding och beroenden

**Files:**
- Create: `mood-plotter/server/requirements.txt`
- Create: `mood-plotter/pi/requirements.txt`
- Create: `mood-plotter/server/config.py`
- Create: `mood-plotter/pi/config.py`
- Create: `mood-plotter/.env.example`
- Create: `mood-plotter/.gitignore`
- Create: `mood-plotter/pytest.ini`
- Create: `mood-plotter/README.md`

- [ ] **Step 1: Skapa katalogstrukturen**

```bash
mkdir -p mood-plotter/server/audio mood-plotter/pi mood-plotter/tests
```

- [ ] **Step 2: Skriv `mood-plotter/server/requirements.txt`**

```
aiohttp==3.9.5
openai==1.30.0
elevenlabs==1.2.2
vpype==1.14
vpype-vectrace==0.2.0
Pillow==10.3.0
python-dotenv==1.0.1
pytest==8.2.0
pytest-asyncio==0.23.7
pytest-mock==3.14.0
aiohttp-pytest==0.1.0
```

- [ ] **Step 3: Skriv `mood-plotter/pi/requirements.txt`**

```
websocket-client==1.8.0
gpiozero==2.0.1
RPi.GPIO==0.7.1
requests==2.32.0
pyaxidraw==3.9.1
python-dotenv==1.0.1
```

- [ ] **Step 4: Skriv `mood-plotter/.env.example`**

```
# 46elks
ELKS_API_USERNAME=
ELKS_API_PASSWORD=
ELKS_FROM_NUMBER=+46xxxxxxxxx
USER_PHONE_NUMBER=+46xxxxxxxxx

# OpenAI
OPENAI_API_KEY=

# ElevenLabs
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Server
SERVER_PUBLIC_URL=https://moodplotter.skyttberg.nu
PI_TOKEN=changeme-shared-secret
COOLDOWN_SECONDS=300
DRY_RUN=false

# Pi
SERVER_URL=https://moodplotter.skyttberg.nu
SERVER_WS_URL=wss://moodplotter.skyttberg.nu/ws
PIR_GPIO_PIN=4
PIR_DEBOUNCE_SECONDS=30
```

- [ ] **Step 5: Skriv `mood-plotter/.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
server/audio/ack_*.mp3
server/cooldown.db
*.swp
```

- [ ] **Step 6: Skriv `mood-plotter/server/config.py`**

```python
"""Server-konfiguration läses från env-variabler / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ELKS_API_USERNAME = os.environ["ELKS_API_USERNAME"]
ELKS_API_PASSWORD = os.environ["ELKS_API_PASSWORD"]
ELKS_FROM_NUMBER = os.environ["ELKS_FROM_NUMBER"]
USER_PHONE_NUMBER = os.environ["USER_PHONE_NUMBER"]

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.environ["ELEVENLABS_VOICE_ID"]

SERVER_PUBLIC_URL = os.environ["SERVER_PUBLIC_URL"].rstrip("/")
PI_TOKEN = os.environ["PI_TOKEN"]
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "300"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

PORT = int(os.environ.get("PORT", "8095"))

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
COOLDOWN_DB = BASE_DIR / "cooldown.db"
```

- [ ] **Step 7: Skriv `mood-plotter/pi/config.py`**

```python
"""Pi-klient-konfiguration."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SERVER_URL = os.environ["SERVER_URL"].rstrip("/")
SERVER_WS_URL = os.environ["SERVER_WS_URL"]
PI_TOKEN = os.environ["PI_TOKEN"]
PI_ID = os.environ.get("PI_ID", "desk1")

PIR_GPIO_PIN = int(os.environ.get("PIR_GPIO_PIN", "4"))
PIR_DEBOUNCE_SECONDS = int(os.environ.get("PIR_DEBOUNCE_SECONDS", "30"))

AXIDRAW_PEN_POS_DOWN = int(os.environ.get("AXIDRAW_PEN_POS_DOWN", "40"))
AXIDRAW_PEN_POS_UP = int(os.environ.get("AXIDRAW_PEN_POS_UP", "60"))
AXIDRAW_SPEED_PENDOWN = int(os.environ.get("AXIDRAW_SPEED_PENDOWN", "25"))
```

- [ ] **Step 8: Skriv `mood-plotter/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
pythonpath = server pi
```

- [ ] **Step 9: Skriv `mood-plotter/README.md` (kort placeholder)**

```markdown
# mood-plotter

PIR-triggad butler-uppringning som plottar mood-kort med AxiDraw.

Se `docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md` för fullständig design.

## Setup
1. Kopiera `.env.example` → `.env` och fyll i värden
2. `pip install -r server/requirements.txt` (server)
3. `pip install -r pi/requirements.txt` (Pi)
4. `python server/generate_questions.py` (engångskörning)
5. Starta server- och pi-tjänsten via systemd
```

- [ ] **Step 10: Commit**

```bash
git add mood-plotter/
git commit -m "feat(mood-plotter): scaffold project structure and config"
```

---

## Task 2: Cooldown-modul

**Files:**
- Create: `mood-plotter/server/cooldown.py`
- Test: `mood-plotter/tests/test_cooldown.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_cooldown.py
import time
from pathlib import Path

import pytest

from cooldown import Cooldown


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "cooldown.db"


def test_cooldown_allows_first_call(db_path):
    cd = Cooldown(db_path, seconds=300)
    assert cd.try_acquire() is True


def test_cooldown_blocks_second_call_within_window(db_path):
    cd = Cooldown(db_path, seconds=300)
    cd.try_acquire()
    assert cd.try_acquire() is False


def test_cooldown_allows_after_window(db_path):
    cd = Cooldown(db_path, seconds=1)
    cd.try_acquire()
    time.sleep(1.1)
    assert cd.try_acquire() is True


def test_cooldown_release_clears_lock(db_path):
    cd = Cooldown(db_path, seconds=300)
    cd.try_acquire()
    cd.release()
    assert cd.try_acquire() is True


def test_cooldown_persists_across_instances(db_path):
    cd1 = Cooldown(db_path, seconds=300)
    cd1.try_acquire()
    cd2 = Cooldown(db_path, seconds=300)
    assert cd2.try_acquire() is False
```

- [ ] **Step 2: Kör testet — det ska faila**

```bash
cd mood-plotter && pytest tests/test_cooldown.py -v
```
Expected: FAIL — `cooldown` module not found

- [ ] **Step 3: Implementera `cooldown.py`**

```python
"""Cooldown-spärr i sqlite för att begränsa antal samtal per tidsfönster."""
import sqlite3
import time
from pathlib import Path


class Cooldown:
    def __init__(self, db_path: Path, seconds: int):
        self.db_path = Path(db_path)
        self.seconds = seconds
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cooldown (id INTEGER PRIMARY KEY, "
                "last_acquired REAL NOT NULL)"
            )

    def try_acquire(self) -> bool:
        """Returnera True om vi får ringa, False om vi är inom cooldown."""
        now = time.time()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT last_acquired FROM cooldown WHERE id = 1"
            ).fetchone()
            if row and now - row[0] < self.seconds:
                return False
            conn.execute(
                "INSERT OR REPLACE INTO cooldown (id, last_acquired) VALUES (1, ?)",
                (now,),
            )
            return True

    def release(self):
        """Rensa cooldown så nästa try_acquire lyckas (vid t.ex. missat samtal)."""
        with self._conn() as conn:
            conn.execute("DELETE FROM cooldown WHERE id = 1")
```

- [ ] **Step 4: Kör testet igen — det ska passera**

```bash
pytest tests/test_cooldown.py -v
```
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/cooldown.py mood-plotter/tests/test_cooldown.py
git commit -m "feat(cooldown): sqlite-backed call cooldown with TDD"
```

---

## Task 3: 46elks webhook signaturkontroll

**Files:**
- Create: `mood-plotter/server/elks_handler.py`
- Test: `mood-plotter/tests/test_elks_handler.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_elks_handler.py
from elks_handler import (
    build_answer_response,
    build_record_response,
    build_hangup_response,
    verify_signature,
)


def test_build_answer_response_returns_play_with_next_record():
    resp = build_answer_response(
        play_url="https://example.com/q.mp3",
        record_callback="https://example.com/recording",
    )
    assert resp == {
        "play": "https://example.com/q.mp3",
        "next": {
            "record": {
                "timeout": 4,
                "maxlength": 8,
                "callbackurl": "https://example.com/recording",
            }
        },
    }


def test_build_record_response_returns_play_then_hangup():
    resp = build_record_response(play_url="https://example.com/ack.mp3")
    assert resp == {
        "play": "https://example.com/ack.mp3",
        "next": {"hangup": ""},
    }


def test_build_hangup_response_is_empty_dict():
    assert build_hangup_response() == {}


def test_verify_signature_accepts_valid_signature():
    # Faktisk signatur enligt 46elks-dokumentation:
    # base64(hmac_sha256(api_password, callback_url))
    api_password = "test-pass"
    url = "https://example.com/callback"
    import base64
    import hashlib
    import hmac

    sig = base64.b64encode(
        hmac.new(api_password.encode(), url.encode(), hashlib.sha256).digest()
    ).decode()

    assert verify_signature(api_password, url, sig) is True


def test_verify_signature_rejects_invalid_signature():
    assert verify_signature("test-pass", "https://example.com/cb", "wrongsig") is False
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_elks_handler.py -v
```
Expected: FAIL — module not found

- [ ] **Step 3: Implementera `elks_handler.py`**

```python
"""46elks webhook-actions och signaturkontroll."""
import base64
import hashlib
import hmac


def build_answer_response(play_url: str, record_callback: str) -> dict:
    """Svar på voice_start: spela frågan, spela in svaret."""
    return {
        "play": play_url,
        "next": {
            "record": {
                "timeout": 4,
                "maxlength": 8,
                "callbackurl": record_callback,
            }
        },
    }


def build_record_response(play_url: str) -> dict:
    """Svar på recording-callback: spela ack, lägg på."""
    return {
        "play": play_url,
        "next": {"hangup": ""},
    }


def build_hangup_response() -> dict:
    """Svar på whenhangup — ingen action behövs."""
    return {}


def verify_signature(api_password: str, callback_url: str, signature: str) -> bool:
    """Kontrollera 46elks X-46elks-Signature mot förväntad HMAC."""
    expected = base64.b64encode(
        hmac.new(
            api_password.encode(), callback_url.encode(), hashlib.sha256
        ).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_elks_handler.py -v
```
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/elks_handler.py mood-plotter/tests/test_elks_handler.py
git commit -m "feat(elks): webhook action builders and signature verification"
```

---

## Task 4: Initiera utgående 46elks-samtal

**Files:**
- Modify: `mood-plotter/server/elks_handler.py`
- Modify: `mood-plotter/tests/test_elks_handler.py`

- [ ] **Step 1: Lägg till test för `initiate_call`**

```python
# Lägg till i tests/test_elks_handler.py
import pytest
from unittest.mock import AsyncMock, patch

from elks_handler import initiate_call


@pytest.mark.asyncio
async def test_initiate_call_posts_to_46elks(mocker):
    mock_post = AsyncMock()
    mock_post.return_value.__aenter__.return_value.status = 200
    mock_post.return_value.__aenter__.return_value.json = AsyncMock(
        return_value={"id": "call-123", "state": "ongoing"}
    )

    with patch("aiohttp.ClientSession.post", mock_post):
        result = await initiate_call(
            api_username="u",
            api_password="p",
            from_number="+46111",
            to_number="+46222",
            voice_start_url="https://x/answer",
            whenhangup_url="https://x/hangup",
        )

    assert result == "call-123"


@pytest.mark.asyncio
async def test_initiate_call_returns_none_on_error(mocker):
    mock_post = AsyncMock()
    mock_post.return_value.__aenter__.return_value.status = 400
    mock_post.return_value.__aenter__.return_value.text = AsyncMock(
        return_value="bad request"
    )

    with patch("aiohttp.ClientSession.post", mock_post):
        result = await initiate_call(
            api_username="u",
            api_password="p",
            from_number="+46111",
            to_number="+46222",
            voice_start_url="https://x/answer",
            whenhangup_url="https://x/hangup",
        )

    assert result is None
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_elks_handler.py::test_initiate_call_posts_to_46elks -v
```
Expected: FAIL — `initiate_call` not defined

- [ ] **Step 3: Lägg till `initiate_call` i `elks_handler.py`**

```python
# Lägg till längst ner i elks_handler.py
import json
import logging

import aiohttp

log = logging.getLogger(__name__)


async def initiate_call(
    api_username: str,
    api_password: str,
    from_number: str,
    to_number: str,
    voice_start_url: str,
    whenhangup_url: str,
) -> str | None:
    """Initiera utgående samtal. Returnerar elks call_id eller None."""
    payload = {
        "from": from_number,
        "to": to_number,
        "voice_start": voice_start_url,
        "whenhangup": whenhangup_url,
    }
    auth = aiohttp.BasicAuth(api_username, api_password)
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(
                "https://api.46elks.com/a1/calls", data=payload
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("id")
                body = await resp.text()
                log.error("46elks API-fel %s: %s", resp.status, body)
                return None
    except Exception as e:
        log.exception("Fel vid utgående samtal: %s", e)
        return None
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_elks_handler.py -v
```
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/elks_handler.py mood-plotter/tests/test_elks_handler.py
git commit -m "feat(elks): outbound call initiation via 46elks API"
```

---

## Task 5: TTS-cache (slumpa fråga från katalog)

**Files:**
- Create: `mood-plotter/server/tts_cache.py`
- Test: `mood-plotter/tests/test_tts_cache.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_tts_cache.py
import pytest

from tts_cache import pick_question_url


def test_pick_question_url_returns_url_to_existing_file(tmp_path):
    audio_dir = tmp_path
    (audio_dir / "q_01.mp3").write_bytes(b"x")
    (audio_dir / "q_02.mp3").write_bytes(b"x")

    url = pick_question_url(
        audio_dir=audio_dir,
        public_base_url="https://example.com",
    )

    assert url in (
        "https://example.com/audio/q_01.mp3",
        "https://example.com/audio/q_02.mp3",
    )


def test_pick_question_url_raises_if_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        pick_question_url(
            audio_dir=tmp_path,
            public_base_url="https://example.com",
        )


def test_pick_question_url_only_picks_q_prefix_files(tmp_path):
    audio_dir = tmp_path
    (audio_dir / "q_01.mp3").write_bytes(b"x")
    (audio_dir / "ack_xyz.mp3").write_bytes(b"x")
    (audio_dir / "junk.txt").write_text("x")

    for _ in range(20):
        url = pick_question_url(
            audio_dir=audio_dir,
            public_base_url="https://example.com",
        )
        assert url.endswith("q_01.mp3")
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_tts_cache.py -v
```
Expected: FAIL — module not found

- [ ] **Step 3: Implementera `tts_cache.py`**

```python
"""Välj slumpmässigt en pre-genererad fråge-MP3."""
import random
from pathlib import Path


def pick_question_url(audio_dir: Path, public_base_url: str) -> str:
    """Returnera en publik URL till en slumpmässig q_*.mp3-fil."""
    candidates = sorted(Path(audio_dir).glob("q_*.mp3"))
    if not candidates:
        raise FileNotFoundError(
            f"Inga q_*.mp3 i {audio_dir} — kör generate_questions.py först"
        )
    chosen = random.choice(candidates)
    return f"{public_base_url.rstrip('/')}/audio/{chosen.name}"
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_tts_cache.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/tts_cache.py mood-plotter/tests/test_tts_cache.py
git commit -m "feat(tts): random question picker from pre-generated cache"
```

---

## Task 6: Live ElevenLabs-TTS för butler-ack

**Files:**
- Create: `mood-plotter/server/tts_live.py`
- Test: `mood-plotter/tests/test_tts_live.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_tts_live.py
from pathlib import Path
from unittest.mock import patch

import pytest

from tts_live import generate_ack_mp3


def test_generate_ack_mp3_writes_file_and_returns_url(tmp_path):
    fake_audio = b"fake-mp3-bytes"

    with patch("tts_live._call_elevenlabs", return_value=fake_audio):
        url = generate_ack_mp3(
            text="Förträffligt min herre",
            call_id="abc123",
            audio_dir=tmp_path,
            public_base_url="https://example.com",
            voice_id="voice-x",
            api_key="key",
        )

    assert url == "https://example.com/audio/ack_abc123.mp3"
    assert (tmp_path / "ack_abc123.mp3").read_bytes() == fake_audio


def test_generate_ack_mp3_returns_fallback_url_on_error(tmp_path):
    # Skapa fallback-fil
    (tmp_path / "ack_fallback.mp3").write_bytes(b"fallback")

    with patch("tts_live._call_elevenlabs", side_effect=RuntimeError("boom")):
        url = generate_ack_mp3(
            text="x",
            call_id="abc",
            audio_dir=tmp_path,
            public_base_url="https://example.com",
            voice_id="v",
            api_key="k",
        )

    assert url == "https://example.com/audio/ack_fallback.mp3"
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_tts_live.py -v
```
Expected: FAIL — module not found

- [ ] **Step 3: Implementera `tts_live.py`**

```python
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
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_tts_live.py -v
```
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/tts_live.py mood-plotter/tests/test_tts_live.py
git commit -m "feat(tts): live ElevenLabs ack generation with fallback"
```

---

## Task 7: Voice-butler (LLM-tolkning av svar)

**Files:**
- Create: `mood-plotter/server/voice_butler.py`
- Test: `mood-plotter/tests/test_voice_butler.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_voice_butler.py
import json
from unittest.mock import patch, MagicMock

from voice_butler import analyze_response, ButlerResult


def _mock_chat_completion(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def test_analyze_response_parses_json_from_llm():
    fake = _mock_chat_completion(json.dumps({
        "image_prompt": "a peaceful forest in soft watercolor",
        "butler_ack": "Förträffligt min herre, kortet är på väg",
    }))

    with patch("voice_butler._call_openai", return_value=fake):
        result = analyze_response("Trött och stressad", api_key="k")

    assert isinstance(result, ButlerResult)
    assert result.image_prompt == "a peaceful forest in soft watercolor"
    assert result.butler_ack == "Förträffligt min herre, kortet är på väg"


def test_analyze_response_uses_fallback_on_empty_text():
    result = analyze_response("", api_key="k")
    assert "watercolor" in result.image_prompt.lower() or "landscape" in result.image_prompt.lower()
    assert "min herre" in result.butler_ack.lower() or "herre" in result.butler_ack.lower()


def test_analyze_response_uses_fallback_on_llm_error():
    with patch("voice_butler._call_openai", side_effect=RuntimeError("boom")):
        result = analyze_response("trött", api_key="k")

    assert result.image_prompt
    assert result.butler_ack


def test_analyze_response_uses_fallback_on_invalid_json():
    fake = _mock_chat_completion("not valid json at all")
    with patch("voice_butler._call_openai", return_value=fake):
        result = analyze_response("trött", api_key="k")

    assert result.image_prompt
    assert result.butler_ack
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_voice_butler.py -v
```
Expected: FAIL — module not found

- [ ] **Step 3: Implementera `voice_butler.py`**

```python
"""Tolka transkriberat svar och generera butler-ack + bild-prompt."""
import json
import logging
from dataclasses import dataclass

from openai import OpenAI

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du är en charmig brittisk-svensk butler.
Användaren har precis svarat på frågan "Hur mår min herre idag?".

Användarens svar: "{user_response}"

Returnera ENDAST följande JSON-objekt, inget annat:
{{
  "image_prompt": "<en kort engelsk DALL·E-prompt för en uppmuntrande, lugn, vacker bild som muntrar upp någon i detta humör. Tydliga konturer, minimal skuggning, lämplig för pen plotter.>",
  "butler_ack": "<1-2 meningar svensk butler-replik. Erkänn humöret mjukt, meddela att kortet är på väg. Tilltala alltid 'min herre' eller 'herrn'.>"
}}"""

FALLBACK = (
    "a peaceful watercolor landscape with soft hills and a single tree, line drawing",
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
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_voice_butler.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/voice_butler.py mood-plotter/tests/test_voice_butler.py
git commit -m "feat(butler): LLM analysis of user response with fallback"
```

---

## Task 8: Whisper-transkribering

**Files:**
- Modify: `mood-plotter/server/voice_butler.py`
- Modify: `mood-plotter/tests/test_voice_butler.py`

- [ ] **Step 1: Lägg till test**

```python
# tests/test_voice_butler.py — lägg till
from unittest.mock import MagicMock, patch

from voice_butler import transcribe_audio


def test_transcribe_audio_returns_text(tmp_path):
    wav_path = tmp_path / "rec.wav"
    wav_path.write_bytes(b"fake-wav")

    fake_response = MagicMock()
    fake_response.text = "Trött och lite stressad"

    with patch("voice_butler._call_whisper", return_value=fake_response):
        text = transcribe_audio(wav_path, api_key="k")

    assert text == "Trött och lite stressad"


def test_transcribe_audio_returns_empty_on_error(tmp_path):
    wav_path = tmp_path / "rec.wav"
    wav_path.write_bytes(b"fake-wav")

    with patch("voice_butler._call_whisper", side_effect=RuntimeError("api down")):
        text = transcribe_audio(wav_path, api_key="k")

    assert text == ""
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_voice_butler.py::test_transcribe_audio_returns_text -v
```
Expected: FAIL — `transcribe_audio` not defined

- [ ] **Step 3: Lägg till funktioner i `voice_butler.py`**

```python
# Lägg till i voice_butler.py
from pathlib import Path


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
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_voice_butler.py -v
```
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/voice_butler.py mood-plotter/tests/test_voice_butler.py
git commit -m "feat(butler): Whisper transcription with error fallback"
```

---

## Task 9: Image-pipeline (DALL·E + vpype → SVG)

**Files:**
- Create: `mood-plotter/server/image_pipeline.py`
- Test: `mood-plotter/tests/test_image_pipeline.py`
- Test fixture: `mood-plotter/tests/fixtures/test_image.png` (simpel testbild)

- [ ] **Step 1: Skapa fixturen**

```bash
mkdir -p mood-plotter/tests/fixtures
python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (256, 256), 'white')
d = ImageDraw.Draw(img)
d.ellipse([50, 50, 200, 200], outline='black', width=3)
d.line([100, 100, 150, 150], fill='black', width=3)
img.save('mood-plotter/tests/fixtures/test_image.png')
"
```

- [ ] **Step 2: Skriv testet**

```python
# tests/test_image_pipeline.py
from pathlib import Path
from unittest.mock import patch

import pytest

from image_pipeline import generate_svg, png_to_svg


FIXTURE = Path(__file__).parent / "fixtures" / "test_image.png"


def test_png_to_svg_produces_svg_string():
    png_bytes = FIXTURE.read_bytes()
    svg = png_to_svg(png_bytes)
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert "</svg>" in svg
    assert len(svg) > 100


def test_generate_svg_calls_dalle_then_vectorizes():
    fake_png = FIXTURE.read_bytes()

    with patch("image_pipeline._call_dalle", return_value=fake_png):
        svg = generate_svg(prompt="a happy moose", api_key="k")

    assert "<svg" in svg
    assert "</svg>" in svg


def test_generate_svg_raises_on_dalle_failure():
    with patch("image_pipeline._call_dalle", side_effect=RuntimeError("nope")):
        with pytest.raises(RuntimeError):
            generate_svg(prompt="x", api_key="k")
```

- [ ] **Step 3: Kör testet — ska faila**

```bash
pytest tests/test_image_pipeline.py -v
```
Expected: FAIL — module not found

- [ ] **Step 4: Implementera `image_pipeline.py`**

```python
"""DALL·E → PNG → vpype-vektorisering → SVG."""
import logging
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

log = logging.getLogger(__name__)


def _call_dalle(prompt: str, api_key: str) -> bytes:
    """Generera en PNG från en prompt med DALL·E 3."""
    import base64

    client = OpenAI(api_key=api_key)
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="b64_json",
    )
    return base64.b64decode(resp.data[0].b64_json)


def png_to_svg(png_bytes: bytes) -> str:
    """Vektorisera PNG till SVG via vpype-vectrace."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        png_path = tmp_path / "in.png"
        svg_path = tmp_path / "out.svg"
        png_path.write_bytes(png_bytes)

        cmd = [
            "vpype",
            "vectrace", str(png_path), "--no-pixel-art",
            "linemerge", "--tolerance", "0.5mm",
            "linesimplify", "--tolerance", "0.2mm",
            "scaleto", "20cm", "20cm",
            "write", str(svg_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"vpype failed: {result.stderr}")

        return svg_path.read_text()


def generate_svg(prompt: str, api_key: str) -> str:
    """Full pipeline: prompt → DALL·E → vpype → SVG-sträng."""
    log.info("Genererar bild för prompt: %s", prompt[:80])
    png = _call_dalle(prompt, api_key)
    log.info("DALL·E PNG mottagen, %d bytes", len(png))
    svg = png_to_svg(png)
    log.info("SVG genererad, %d tecken", len(svg))
    return svg
```

- [ ] **Step 5: Kör testet — ska passera (kräver vpype installerat)**

```bash
pip install -r server/requirements.txt
pytest tests/test_image_pipeline.py -v
```
Expected: PASS (3 tests). Om vpype saknas: installera först.

- [ ] **Step 6: Commit**

```bash
git add mood-plotter/server/image_pipeline.py mood-plotter/tests/test_image_pipeline.py mood-plotter/tests/fixtures/
git commit -m "feat(image): DALL-E to vpype SVG pipeline with TDD"
```

---

## Task 10: WebSocket-dispatcher

**Files:**
- Create: `mood-plotter/server/ws_dispatcher.py`
- Test: `mood-plotter/tests/test_ws_dispatcher.py`

- [ ] **Step 1: Skriv testet**

```python
# tests/test_ws_dispatcher.py
import asyncio

import pytest

from ws_dispatcher import WSDispatcher


class FakeWS:
    def __init__(self):
        self.sent = []
        self.closed = False

    async def send_json(self, obj):
        self.sent.append(obj)

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_register_adds_ready_client():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    assert d.get_ready_client() is ws


@pytest.mark.asyncio
async def test_unregister_removes_client():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    d.unregister(ws)
    assert d.get_ready_client() is None


@pytest.mark.asyncio
async def test_send_svg_marks_client_busy():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")

    sent = await d.send_svg("<svg/>")

    assert sent is True
    assert ws.sent == [{"method": "plot", "svg": "<svg/>"}]
    assert d.get_ready_client() is None  # busy nu


@pytest.mark.asyncio
async def test_mark_ready_returns_to_ready_pool():
    d = WSDispatcher()
    ws = FakeWS()
    d.register(ws, pi_id="desk1")
    await d.send_svg("<svg/>")

    d.mark_ready(ws)
    assert d.get_ready_client() is ws


@pytest.mark.asyncio
async def test_send_svg_returns_false_when_no_ready():
    d = WSDispatcher()
    sent = await d.send_svg("<svg/>")
    assert sent is False
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_ws_dispatcher.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementera `ws_dispatcher.py`**

```python
"""Hantera WebSocket-anslutna AxiDraw-klienter."""
import logging

log = logging.getLogger(__name__)


class WSDispatcher:
    def __init__(self):
        # ws -> {"pi_id": str, "ready": bool}
        self._clients: dict = {}

    def register(self, ws, pi_id: str):
        self._clients[ws] = {"pi_id": pi_id, "ready": True}
        log.info("Klient registrerad: %s (totalt: %d)", pi_id, len(self._clients))

    def unregister(self, ws):
        info = self._clients.pop(ws, None)
        if info:
            log.info("Klient bortkopplad: %s (kvar: %d)", info["pi_id"], len(self._clients))

    def mark_ready(self, ws):
        if ws in self._clients:
            self._clients[ws]["ready"] = True

    def mark_busy(self, ws):
        if ws in self._clients:
            self._clients[ws]["ready"] = False

    def get_ready_client(self):
        for ws, info in self._clients.items():
            if info["ready"]:
                return ws
        return None

    async def send_svg(self, svg: str) -> bool:
        """Skicka SVG till första ready-klienten. Returnerar True om någon fick den."""
        ws = self.get_ready_client()
        if ws is None:
            log.warning("Ingen ready-klient — SVG kastas")
            return False
        await ws.send_json({"method": "plot", "svg": svg})
        self.mark_busy(ws)
        return True
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_ws_dispatcher.py -v
```
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/ws_dispatcher.py mood-plotter/tests/test_ws_dispatcher.py
git commit -m "feat(ws): WebSocket dispatcher for plotter clients"
```

---

## Task 11: Engångsskript för fråge-MP3:er

**Files:**
- Create: `mood-plotter/server/generate_questions.py`

- [ ] **Step 1: Skriv skriptet**

```python
# server/generate_questions.py
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
```

- [ ] **Step 2: Manuell körning + lyssna**

```bash
cd mood-plotter
python server/generate_questions.py
ls -la server/audio/
# Spela varje fil — låter de butler-mässiga?
```

Förvänta: 5 q_NN.mp3 + 1 ack_fallback.mp3 i `server/audio/`. Lyssna och godkänn.

- [ ] **Step 3: Commit (utan att inkludera MP3:erna i git)**

```bash
git add mood-plotter/server/generate_questions.py
git commit -m "feat(tts): one-shot script to generate butler question MP3s"
```

> **Notera:** `.gitignore` för servern bör utesluta MP3-cachen. Lägg till om det inte redan är gjort:
> ```
> server/audio/*.mp3
> ```

---

## Task 12: aiohttp-server med routes

**Files:**
- Create: `mood-plotter/server/server.py`
- Test: `mood-plotter/tests/test_server_integration.py`

- [ ] **Step 1: Skriv integrationstestet**

```python
# tests/test_server_integration.py
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import server


@pytest.fixture
async def client(tmp_path, monkeypatch):
    # Patcha config för isolerad test-miljö
    monkeypatch.setattr("config.AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr("config.COOLDOWN_DB", tmp_path / "cd.db")
    monkeypatch.setattr("config.PI_TOKEN", "test-token")
    monkeypatch.setattr("config.DRY_RUN", True)
    (tmp_path / "audio").mkdir()
    (tmp_path / "audio" / "q_01.mp3").write_bytes(b"x")

    app = server.create_app()
    async with TestClient(TestServer(app)) as c:
        yield c


@pytest.mark.asyncio
async def test_trigger_requires_auth(client):
    resp = await client.post("/trigger", json={"pi_id": "desk1"})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_trigger_calls_46elks_when_authorized(client):
    with patch("server.elks_handler.initiate_call", new=AsyncMock(return_value="call-1")):
        resp = await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status == 200


@pytest.mark.asyncio
async def test_trigger_returns_429_on_cooldown(client):
    with patch("server.elks_handler.initiate_call", new=AsyncMock(return_value="call-1")):
        await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
        resp = await client.post(
            "/trigger",
            json={"pi_id": "desk1"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status == 429


@pytest.mark.asyncio
async def test_elks_answer_returns_play_record_action(client):
    resp = await client.get("/elks/answer?callid=abc")
    body = await resp.json()
    assert "play" in body
    assert "next" in body
    assert "record" in body["next"]


@pytest.mark.asyncio
async def test_audio_serves_existing_file(client, tmp_path):
    (tmp_path / "audio" / "q_test.mp3").write_bytes(b"hello")
    resp = await client.get("/audio/q_test.mp3")
    assert resp.status == 200
    assert await resp.read() == b"hello"


@pytest.mark.asyncio
async def test_audio_404_for_missing_file(client):
    resp = await client.get("/audio/nope.mp3")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_audio_blocks_path_traversal(client):
    resp = await client.get("/audio/../config.py")
    assert resp.status in (400, 404)
```

- [ ] **Step 2: Kör testet — ska faila**

```bash
pytest tests/test_server_integration.py -v
```
Expected: FAIL — `server.create_app` not defined

- [ ] **Step 3: Implementera `server.py`**

```python
"""mood-plotter aiohttp-server."""
import asyncio
import logging
import uuid
from pathlib import Path

from aiohttp import web

import config
import elks_handler
import image_pipeline
import tts_cache
import tts_live
import voice_butler
from cooldown import Cooldown
from ws_dispatcher import WSDispatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mood-plotter")


def _check_auth(request) -> bool:
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {config.PI_TOKEN}"


async def trigger_handler(request):
    if not _check_auth(request):
        return web.Response(status=401, text="unauthorized")

    cd: Cooldown = request.app["cooldown"]
    if not cd.try_acquire():
        return web.Response(status=429, text="cooldown")

    dispatcher: WSDispatcher = request.app["ws_dispatcher"]
    if dispatcher.get_ready_client() is None:
        cd.release()
        return web.Response(status=503, text="no plotter ready")

    call_id = str(uuid.uuid4())[:8]
    request.app["pending_calls"][call_id] = {"state": "calling"}

    if config.DRY_RUN:
        log.info("[DRY_RUN] skulle ringa %s, call_id=%s", config.USER_PHONE_NUMBER, call_id)
        return web.json_response({"call_id": call_id, "dry_run": True})

    elks_id = await elks_handler.initiate_call(
        api_username=config.ELKS_API_USERNAME,
        api_password=config.ELKS_API_PASSWORD,
        from_number=config.ELKS_FROM_NUMBER,
        to_number=config.USER_PHONE_NUMBER,
        voice_start_url=f"{config.SERVER_PUBLIC_URL}/elks/answer?call_id={call_id}",
        whenhangup_url=f"{config.SERVER_PUBLIC_URL}/elks/hangup?call_id={call_id}",
    )
    if elks_id is None:
        cd.release()
        request.app["pending_calls"].pop(call_id, None)
        return web.Response(status=502, text="elks call failed")

    request.app["pending_calls"][call_id]["elks_id"] = elks_id
    return web.json_response({"call_id": call_id, "elks_id": elks_id})


async def elks_answer_handler(request):
    call_id = request.query.get("call_id", "")
    play_url = tts_cache.pick_question_url(
        audio_dir=config.AUDIO_DIR,
        public_base_url=config.SERVER_PUBLIC_URL,
    )
    record_callback = (
        f"{config.SERVER_PUBLIC_URL}/elks/recording?call_id={call_id}"
    )
    log.info("call_id=%s answer → fråga %s", call_id, play_url)
    return web.json_response(
        elks_handler.build_answer_response(play_url, record_callback)
    )


async def elks_recording_handler(request):
    call_id = request.query.get("call_id", "")
    data = await request.post()
    recording_url = data.get("recordurl") or data.get("url", "")
    log.info("call_id=%s inspelning klar: %s", call_id, recording_url)

    asyncio.create_task(_process_recording(request.app, call_id, recording_url))

    fallback_url = f"{config.SERVER_PUBLIC_URL}/audio/ack_fallback.mp3"
    return web.json_response(elks_handler.build_record_response(fallback_url))


async def _process_recording(app, call_id: str, recording_url: str):
    """Bakgrundstask: hämta inspelning, transkribera, generera ack + bild."""
    try:
        # Hämta wav
        import aiohttp as _aiohttp
        wav_path = config.AUDIO_DIR / f"rec_{call_id}.wav"
        async with _aiohttp.ClientSession() as session:
            async with session.get(recording_url) as resp:
                wav_path.write_bytes(await resp.read())

        # Whisper
        text = voice_butler.transcribe_audio(wav_path, config.OPENAI_API_KEY)
        log.info("call_id=%s transkribering: %r", call_id, text)

        # LLM
        result = voice_butler.analyze_response(text, config.OPENAI_API_KEY)
        log.info("call_id=%s prompt: %s | ack: %s", call_id, result.image_prompt[:60], result.butler_ack[:60])

        # Generera ack-MP3
        tts_live.generate_ack_mp3(
            text=result.butler_ack,
            call_id=call_id,
            audio_dir=config.AUDIO_DIR,
            public_base_url=config.SERVER_PUBLIC_URL,
            voice_id=config.ELEVENLABS_VOICE_ID,
            api_key=config.ELEVENLABS_API_KEY,
        )

        # Generera SVG och skicka till plotter
        svg = image_pipeline.generate_svg(result.image_prompt, config.OPENAI_API_KEY)
        sent = await app["ws_dispatcher"].send_svg(svg)
        log.info("call_id=%s SVG skickad till plotter: %s", call_id, sent)
    except Exception as e:
        log.exception("call_id=%s fel i _process_recording: %s", call_id, e)
    finally:
        try:
            (config.AUDIO_DIR / f"rec_{call_id}.wav").unlink(missing_ok=True)
        except Exception:
            pass


async def elks_hangup_handler(request):
    call_id = request.query.get("call_id", "")
    pending = request.app["pending_calls"].pop(call_id, None)
    if pending and pending.get("state") == "calling":
        # Aldrig svarad — rensa cooldown så nästa PIR-trigger får ringa
        request.app["cooldown"].release()
        log.info("call_id=%s missat samtal — cooldown rensad", call_id)
    return web.json_response({})


async def audio_handler(request):
    name = request.match_info["name"]
    if "/" in name or ".." in name:
        return web.Response(status=400)
    path = config.AUDIO_DIR / name
    if not path.is_file():
        return web.Response(status=404)
    return web.FileResponse(path)


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    dispatcher: WSDispatcher = request.app["ws_dispatcher"]
    pi_id = "unknown"
    registered = False

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            continue
        try:
            data = msg.json()
        except Exception:
            continue

        method = data.get("method")
        if method == "register":
            params = data.get("params", {})
            if params.get("token") != config.PI_TOKEN:
                await ws.close(code=4401, message=b"unauthorized")
                return ws
            pi_id = params.get("pi_id", "unknown")
            dispatcher.register(ws, pi_id=pi_id)
            registered = True
            await ws.send_json({"method": "registered"})
        elif method == "ready":
            dispatcher.mark_ready(ws)

    if registered:
        dispatcher.unregister(ws)
    return ws


def create_app():
    app = web.Application()
    app["cooldown"] = Cooldown(config.COOLDOWN_DB, config.COOLDOWN_SECONDS)
    app["ws_dispatcher"] = WSDispatcher()
    app["pending_calls"] = {}

    app.router.add_post("/trigger", trigger_handler)
    app.router.add_get("/elks/answer", elks_answer_handler)
    app.router.add_post("/elks/answer", elks_answer_handler)
    app.router.add_post("/elks/recording", elks_recording_handler)
    app.router.add_get("/elks/hangup", elks_hangup_handler)
    app.router.add_post("/elks/hangup", elks_hangup_handler)
    app.router.add_get("/audio/{name}", audio_handler)
    app.router.add_get("/ws", ws_handler)

    return app


def main():
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=config.PORT)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Kör testet — ska passera**

```bash
pytest tests/test_server_integration.py -v
```
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add mood-plotter/server/server.py mood-plotter/tests/test_server_integration.py
git commit -m "feat(server): aiohttp routes for trigger, elks webhooks, ws, audio"
```

---

## Task 13: Pi — PIR-watcher

**Files:**
- Create: `mood-plotter/pi/pir_watcher.py`

- [ ] **Step 1: Skriv koden**

```python
# pi/pir_watcher.py
"""Läs PIR-sensor, skicka HTTP-trigger till servern med debounce."""
import logging
import time

import requests
from gpiozero import MotionSensor

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("pir-watcher")


def trigger_server():
    try:
        resp = requests.post(
            f"{config.SERVER_URL}/trigger",
            headers={"Authorization": f"Bearer {config.PI_TOKEN}"},
            json={"pi_id": config.PI_ID},
            timeout=5,
        )
        log.info("trigger → %d %s", resp.status_code, resp.text[:100])
    except Exception as e:
        log.error("Trigger-fel: %s", e)


def main():
    log.info("Startar PIR-watcher på GPIO %d", config.PIR_GPIO_PIN)
    pir = MotionSensor(config.PIR_GPIO_PIN)
    last_trigger = 0.0

    while True:
        pir.wait_for_motion()
        now = time.time()
        if now - last_trigger < config.PIR_DEBOUNCE_SECONDS:
            log.debug("Debounce-block, hoppar över")
            pir.wait_for_no_motion()
            continue
        last_trigger = now
        log.info("Rörelse detekterad → triggar")
        trigger_server()
        pir.wait_for_no_motion()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manuellt sanity-test (på Pi:n eller med stub)**

På Pi:n:
```bash
cd mood-plotter
python pi/pir_watcher.py
# Vifta för PIR — ska se "Rörelse detekterad" och POST-resultat
```

På utvecklingsmaskin (utan PIR): testa import i isolering:
```bash
python -c "import sys; sys.path.insert(0, 'pi'); from pir_watcher import trigger_server; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add mood-plotter/pi/pir_watcher.py
git commit -m "feat(pi): PIR motion detector with debounced HTTP trigger"
```

---

## Task 14: Pi — plotter-klient

**Files:**
- Create: `mood-plotter/pi/plotter_client.py`

- [ ] **Step 1: Skriv koden**

```python
# pi/plotter_client.py
"""WS-klient som tar emot SVG och kör AxiDraw."""
import json
import logging
import tempfile
import time
from pathlib import Path

import websocket
from pyaxidraw import axidraw

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("plotter-client")


def connect_axidraw():
    ad = axidraw.AxiDraw()
    ad.interactive()
    while not ad.connect():
        log.warning("AxiDraw inte ansluten — försöker igen om 5s")
        time.sleep(5)
    ad.options.pen_pos_down = config.AXIDRAW_PEN_POS_DOWN
    ad.options.pen_pos_up = config.AXIDRAW_PEN_POS_UP
    ad.options.speed_pendown = config.AXIDRAW_SPEED_PENDOWN
    return ad


def plot_svg(ad, svg_text: str):
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(svg_text.encode())
        svg_path = f.name
    try:
        ad.plot_setup(svg_path)
        ad.options.preview = False
        ad.plot_run()
        log.info("Plot klar")
    finally:
        Path(svg_path).unlink(missing_ok=True)


def run():
    ad = connect_axidraw()
    backoff = 1

    while True:
        try:
            ws = websocket.create_connection(config.SERVER_WS_URL, timeout=30)
            log.info("WS ansluten")
            backoff = 1

            ws.send(json.dumps({
                "method": "register",
                "params": {"token": config.PI_TOKEN, "pi_id": config.PI_ID},
            }))

            while True:
                raw = ws.recv()
                if not raw:
                    break
                msg = json.loads(raw)
                if msg.get("method") == "plot":
                    log.info("SVG mottagen, %d tecken — plottar", len(msg.get("svg", "")))
                    try:
                        plot_svg(ad, msg["svg"])
                    except Exception as e:
                        log.exception("Plot-fel: %s", e)
                    ws.send(json.dumps({"method": "ready"}))
        except Exception as e:
            log.error("WS-fel: %s — reconnect om %ds", e, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Manuellt test (kräver server uppe + AxiDraw)**

```bash
# På Pi:n
cd mood-plotter
python pi/plotter_client.py
# Borde se "WS ansluten" och inget mer förrän en plot kommer
```

- [ ] **Step 3: Commit**

```bash
git add mood-plotter/pi/plotter_client.py
git commit -m "feat(pi): WebSocket plotter client with AxiDraw integration"
```

---

## Task 15: Systemd-units

**Files:**
- Create: `mood-plotter/server/mood-plotter-server.service`
- Create: `mood-plotter/pi/mood-plotter-pi.service` (för PIR + plotter)

- [ ] **Step 1: Skriv server-unit**

```ini
# server/mood-plotter-server.service
[Unit]
Description=Mood Plotter Server
After=network.target

[Service]
Type=simple
User=kumamonwithme
WorkingDirectory=/home/kumamonwithme/mood-plotter/server
ExecStart=/home/kumamonwithme/mood-plotter/.venv/bin/python server.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Skriv Pi-units (en per process)**

```ini
# pi/mood-plotter-pir.service
[Unit]
Description=Mood Plotter PIR Watcher
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mood-plotter/pi
ExecStart=/home/pi/mood-plotter/.venv/bin/python pir_watcher.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# pi/mood-plotter-plotter.service
[Unit]
Description=Mood Plotter Client (AxiDraw)
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mood-plotter/pi
ExecStart=/home/pi/mood-plotter/.venv/bin/python plotter_client.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Commit**

```bash
git add mood-plotter/server/mood-plotter-server.service mood-plotter/pi/mood-plotter-pir.service mood-plotter/pi/mood-plotter-plotter.service
git commit -m "feat(deploy): systemd units for server and pi processes"
```

---

## Task 16: Deploy-anvisningar i README

**Files:**
- Modify: `mood-plotter/README.md`

- [ ] **Step 1: Skriv ut komplett README**

```markdown
# mood-plotter

PIR-triggad butler-uppringning som plottar mood-kort med AxiDraw.

## Översikt

PIR-sensor → samtal till mobil → butler frågar "hur mår herrn?" → svar tolkas → DALL·E-bild vektoriseras → AxiDraw plottar.

Se [`docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md`](../docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md) för fullständig design.

## Setup — server (skyttberg.nu)

```bash
ssh kumamonwithme@skyttberg.nu
cd ~
git clone <repo> mood-plotter
cd mood-plotter
python3 -m venv .venv
.venv/bin/pip install -r server/requirements.txt
cp .env.example .env
# fyll i .env med riktiga värden
.venv/bin/python server/generate_questions.py
sudo cp server/mood-plotter-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-server
journalctl -u mood-plotter-server -f
```

Lägg upp nginx-proxy för `moodplotter.skyttberg.nu` → `127.0.0.1:8095` (inkl. WS-upgrade) och Let's Encrypt-cert.

## Setup — Pi

```bash
ssh pi@<pi-ip>
git clone <repo> mood-plotter
cd mood-plotter
python3 -m venv .venv
.venv/bin/pip install -r pi/requirements.txt
cp .env.example .env
# fyll i .env med Pi-värden (server-URL, token, GPIO-pin)
sudo cp pi/mood-plotter-pir.service /etc/systemd/system/
sudo cp pi/mood-plotter-plotter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mood-plotter-plotter mood-plotter-pir
```

## Smoke-test

Med `DRY_RUN=true` i serverns env:

```bash
curl -X POST https://moodplotter.skyttberg.nu/trigger \
  -H "Authorization: Bearer $PI_TOKEN" \
  -d '{"pi_id":"desk1"}'
```

Förvänta: 200 + JSON med `call_id` och `dry_run: true`. Inga riktiga samtal.

Sätt `DRY_RUN=false` när allt verifierats. Trigga manuellt en gång till — telefonen ska ringa, butlern fråga, AxiDraw börja rita.

## Fil-layout

| Fil | Vad |
|---|---|
| `server/server.py` | aiohttp-app + routes |
| `server/elks_handler.py` | 46elks API + actions |
| `server/voice_butler.py` | Whisper + GPT-4o-mini |
| `server/tts_cache.py` | Pre-genererad fråge-MP3-väljare |
| `server/tts_live.py` | ElevenLabs ack-generator |
| `server/image_pipeline.py` | DALL·E + vpype |
| `server/ws_dispatcher.py` | WS-klient-pool |
| `server/cooldown.py` | sqlite-cooldown |
| `server/generate_questions.py` | Engångsskript för fråge-MP3 |
| `pi/pir_watcher.py` | GPIO + HTTP trigger |
| `pi/plotter_client.py` | WS + AxiDraw |

## Tester

```bash
cd mood-plotter
pytest -v
```
```

- [ ] **Step 2: Commit**

```bash
git add mood-plotter/README.md
git commit -m "docs(readme): full setup, deploy and smoke-test instructions"
```

---

## Self-Review

Efter alla tasks ovan, kontrollera:

**Spec-täckning** — varje sektion i specen har en task:
- Översikt/Mål → tasks 1, 12 (server-skelett), 13–14 (Pi)
- Arkitektur → tasks 12 (server), 13–14 (Pi), 15 (deploy)
- Komponenter (server) → tasks 2, 3–4, 5, 6, 7–8, 9, 10, 11, 12
- Komponenter (klient) → tasks 13, 14
- Förinspelade tillgångar → task 11
- Dataflöde → tasks 12 (routes) + 13–14 (klientsida)
- Felhantering → inbyggt i tasks 2, 6, 7, 8, 9, 10, 12 (cooldown release, fallback ack, WS reconnect)
- Test → varje implementations-task har test
- Säkerhet → tasks 3 (signaturkontroll), 12 (auth-check, path traversal), 12 (WS auth)
- Driftnotis → tasks 15, 16

**Inga placeholders** — varje step har faktisk kod, kommando eller fil. Inget "TBD".

**Typkonsistens** — `WSDispatcher`, `ButlerResult`, `Cooldown`, `pick_question_url`, `generate_ack_mp3`, `generate_svg` används med samma signaturer i tasks som definierar dem och i task 12 som integrerar.

**Ej täckt i plan men dokumenterat utanför scope** — webhook-signaturkontroll (impl. finns i task 3 men inte påkopplad i route-handlers; lämnas som hardening-pass när first-mile fungerar). Lägg till om det blir ett krav.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-09-pir-mood-plotter.md`.
