# Ring & Vinn — Live Game Show

## Koncept

En webb-baserad game show som visas på en TV/skärm. En illustrerad SVG-programledare kör showen automatiskt. Folk ringer in via 46elks, hamnar i kö, och plockas live för att svara på frågor. Rätt svar ger poäng och firande. Byggt som demo men kan bli permanent installation på kontoret.

## Komponenter

### 1. Show-sida (TV:n)

Fullskärms webbsida i klassisk game show-layout:

- **Vänster (40%):** Animerad SVG-karaktär med uttryck:
  - `idle` — neutral, blinkande ögon
  - `asking` — pratande mun-animation
  - `listening` — hand vid örat, nyfiket uttryck
  - `correct` — stort leende, händer upp, konfetti
  - `wrong` — ledsen mun, axelryckning
  - `waiting` — tittar på klockan, väntar på uppringare
- **Höger (60%):** Fråga-panel med:
  - Frågenummer ("Fråga 3 av 10")
  - Frågetexten
  - Kö-status ("📞 3 i kö")
  - Aktiv tävlande ("🎤 Erik svarar...")
- **Topp-bar:** Logotyp "RING & VINN" + LIVE-indikator
- **Botten-ticker:** Telefonnummer att ringa + leaderboard med poäng
- **Effekter:** CSS-animationer för rätt svar (konfetti, glow), fel svar (skakning), ny tävlande (slide-in)
- **Ljud:** Jingles via Web Audio API — intro, rätt svar, fel svar, ny tävlande, tromvirvel

Sidan ansluter via WebSocket till backend och reagerar på events i realtid.

### 2. Voice Agent (backend)

Python + asyncio, samma arkitektur som oloppnare voice_agent.py:

- **46elks WebSocket-samtal** via WS-nummer
- **Kö-hantering:**
  - Inkommande samtal läggs i FIFO-kö
  - Uppringare hör kö-musik/meddelande medan de väntar
  - Show Engine plockar nästa person när den är redo
- **Samtalsflöde per tävlande:**
  1. Plockas ur kö → spela välkommen-clip
  2. Fråga presenteras (TTS-clip + visas på TV)
  3. Lyssna på svar (Whisper transkribering)
  4. Bedöm svar (GPT-4o-mini: rätt/fel + förklaring)
  5. Spela resultat-clip (rätt/fel) → häng upp
- **WebSocket-server** (port 8115) för show-sidan, skickar events:
  - `question` — ny fråga visas
  - `caller_active` — tävlande plockas ur kö
  - `answer` — svar transkriberat
  - `result` — rätt/fel med poäng
  - `queue_update` — kö-storlek ändrad
  - `leaderboard` — uppdaterad poängtavla
  - `show_state` — idle/asking/listening/celebrating

### 3. Show Engine

Automatisk programledare som styr flödet:

- **Rund-baserat:** Laddar frågor, kör genom dem en i taget
- **Per fråga:**
  1. Presentera frågan (TTS + skärm)
  2. Vänta på uppringare i kön (timeout 30s, annars skippa)
  3. Plocka nästa ur kön
  4. Ge tävlande 15s att svara
  5. Bedöm och visa resultat
  6. Kort paus, nästa fråga
- **Mellan frågor:** Visa leaderboard, spela jingle
- **Slut:** Visa vinnare, firande-animation

### 4. Fråge-system

JSON-fil (`questions.json`):

```json
[
  {
    "id": 1,
    "type": "quiz",
    "question": "Hur många invånare har Hudiksvall?",
    "answer": "15000",
    "accept": ["15000", "femtontusen", "15 000", "ca 15000"],
    "points": 1,
    "hint": "Det är en stad i Hälsingland"
  },
  {
    "id": 2,
    "type": "price",
    "question": "Vad kostar en mass på Oktoberfest?",
    "answer": "150 kr",
    "accept_range": [120, 180],
    "points": 2
  }
]
```

Frågetyper:
- `quiz` — exakt svar (med varianter i `accept`)
- `price` — närmast rätt inom `accept_range`
- `number` — gissa antal, närmast rätt
- `open` — GPT bedömer fritt (t.ex. "Nämn en svensk uppfinning")

### 5. TTS-clips

Förinspelade via ElevenLabs (samma röst/mönster som ölöppnaren):

- **Intro:** "Välkommen till Ring och Vinn!" (2-3 varianter)
- **Välkommen tävlande:** "Välkommen! Du är live! Är du redo?" (3-4 varianter)
- **Fråga-intro:** "Och frågan lyder..." (2-3 varianter)
- **Rätt svar:** "RÄTT! Fantastiskt!" (3-4 varianter)
- **Fel svar:** "Tyvärr, det var inte rätt!" (3-4 varianter)
- **Kö-meddelande:** "Du är i kön, vänta kvar!" (2-3 varianter)
- **Avslutning:** "Tack för idag! Och vinnaren är..."
- **Frågor:** Varje fråga som eget TTS-clip (genereras vid uppstart)

## Tech stack

| Komponent | Teknologi |
|-----------|-----------|
| Frontend (show) | Vanilla HTML/CSS/JS, WebSocket |
| Backend | Python 3, asyncio, websockets |
| Samtal | 46elks WebSocket-nummer |
| TTS | ElevenLabs (förinspelade clips) |
| STT | OpenAI Whisper |
| Bedömning | GPT-4o-mini |
| Server | elkwonders.46elks.com |
| Data | JSON-filer (frågor, leaderboard) |

## Dataflöde

```
┌─────────────┐     WebSocket (8115)     ┌──────────────┐
│  TV-skärm   │◄────── events ──────────│  Show Engine  │
│  (browser)  │                          │  (Python)     │
└─────────────┘                          └──────┬───────┘
                                                │
                                         ┌──────┴───────┐
                                         │ Voice Agent   │
                                         │ (samtal +     │
                                         │  kö + STT)    │
                                         └──────┬───────┘
                                                │
                                    46elks WebSocket (8116)
                                                │
                                         ┌──────┴───────┐
                                         │  Telefon      │
                                         │  (uppringare) │
                                         └──────────────┘
```

## Portar

- `8115` — WebSocket för show-sidan (frontend events)
- `8116` — WebSocket för 46elks (samtalsljud)
- `8117` — HTTP API (voice_start webhook, admin)

## Filstruktur

```
ring-och-vinn/
├── server.py              # Main: show engine + voice agent + HTTP
├── questions.json          # Frågor
├── leaderboard.json        # Poängtavla (auto-genererad)
├── generate_clips.py       # Generera TTS-clips
├── clips/                  # Förinspelade TTS-clips
│   ├── intro_*.pcm
│   ├── welcome_*.pcm
│   ├── correct_*.pcm
│   ├── wrong_*.pcm
│   ├── queue_*.pcm
│   └── questions/          # Per-fråga clips
├── site/
│   ├── index.html          # Show-sidan (TV)
│   ├── style.css
│   ├── show.js             # WebSocket + animationer
│   └── sounds/             # Jingles (mp3)
├── .env                    # API-nycklar
├── requirements.txt
└── ring-och-vinn.service   # systemd
```

## 46elks-setup

- Behöver: 1 mobilnummer (inkommande) + 1 WS-nummer
- Mobilnumret har `voice_start: {"connect": "+46007000XX"}` (WS-numret)
- WS-numret pekar på `ws://elkwonders.46elks.com:8116`
- Alternativt: återanvänd ett befintligt nummer

## Scope — vad som INTE ingår

- Ingen admin-webapp (frågor redigeras direkt i JSON)
- Ingen användarregistrering/login
- Ingen persistent historik mellan sessioner (leaderboard nollställs per omgång)
- Inget video/kamera — bara animerad SVG-karaktär
- Inget multiplayer-svar (en tävlande åt gången)
