# BallDrop — Ljudsystem (kontaktbaserade toner)

**Datum:** 2026-05-01
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop`
**Plattformar:** macOS 14+, iPadOS 17+

## Mål

Lägga till audio till BallDrop så att bollar producerar en kort ton vid varje kontakt med en yta. Tonens **frekvens** bestäms av bollens färg (pentatonisk dur-skala, 5 färger = 5 toner). Tonens **karaktär** (envelope, pitch-sweep, harmoniker, filter) bestäms av ytan (block, studsmatta, katapult, poängzon, vägg). Allt ljud genereras runtime via `AVAudioEngine` — inga ljudfiler i app-bundeln. En mute-knapp i sidopanelen stänger av all output.

## Funktionella krav

### Ljud per kontakt-typ

Fem **ytor** trigggar ljud:

| Yta | Envelope-karaktär | Längd |
|-----|-------------------|-------|
| Block (horisontell, vertikal, diagonal, cirkel, triangel, freedraw) | Kort attack, snabb exponentiell decay — marimbaaktig pling | ~150 ms |
| Studsmatta | Pitch sweep upp 50% → tillbaka (frekvens × 1.5 vid mitten) — boing | ~250 ms |
| Katapult | Sänkt en oktav (frekvens × 0.5) + tyngre attack — thock | ~200 ms |
| Poängzon | Mjuk attack + harmonisk femte (frekvens × 1.5) blandad — bell-aktig, längre decay | ~600 ms |
| Vägg | Sinussvängning med 50% amplitud + low-pass-känsla (mörkare ton via 1:a oktavs-undertown) — kort dunk | ~80 ms |

Fem **bollfärger** mappar till frekvens (pentatonisk C-dur, oktav 5):

| Färg | Not | Frekvens (Hz) |
|------|-----|---------------|
| Pink `(1.0, 0.42, 0.54)` | C5 | 523.25 |
| Orange `(1.0, 0.70, 0.28)` | D5 | 587.33 |
| Grön `(0.53, 0.84, 0.55)` | E5 | 659.25 |
| Lila `(0.70, 0.53, 0.87)` | G5 | 783.99 |
| Gul `(1.0, 0.87, 0.37)` | A5 | 880.00 |

Totalt 5 × 5 = 25 buffert-kombinationer. Pre-syntheseras vid `SoundManager.init`.

### Polyphoni

Pool av 8 `AVAudioPlayerNode` (round-robin scheduling). Räcker för spel med upp till ~8 samtidiga kontakter — bortom det "stjäl" nyaste sounds gamla nodes (befintligt ljud avbryts). 50+ bollar kan i värsta fall trigga simultant; i praktiken sprids kontakter över tid och 8 noder räcker.

### Mute

`var isMuted: Bool = false` på `SoundManager`. När `true`: `play(...)` returnerar tidigt utan att schemalägga något. Mute-läget stänger inte ner audio engine — bara bypassar uppspelning.

### Mute-knapp i sidopanel

Ny knapp i `KONTROLL`-sektionen, placerad efter befintliga `Pausa`/`Rensa`:
- Symbol: `Image(systemName: "speaker.wave.2.fill")` när på, `"speaker.slash.fill"` när av.
- Tap: växlar `isMuted`.
- Layout: bredvid övriga kontrollknappar, samma höjd och stil.

## Arkitektur

### Ny fil: `BallDrop/BallDrop/SoundManager.swift`

```swift
import AVFoundation
#if os(iOS)
import UIKit
#endif

final class SoundManager {
    enum Surface: String { case block, trampoline, catapult, scoreZone, wall }

    var isMuted: Bool = false

    private let engine = AVAudioEngine()
    private let mixer: AVAudioMixerNode
    private var playerNodes: [AVAudioPlayerNode] = []
    private var nextNodeIndex = 0
    private var buffers: [String: AVAudioPCMBuffer] = [:]

    private static let frequencies: [Double] = [
        523.25,  // C5 — pink
        587.33,  // D5 — orange
        659.25,  // E5 — green
        783.99,  // G5 — purple
        880.00,  // A5 — yellow
    ]

    init() {
        configureAudioSession()
        mixer = engine.mainMixerNode
        // ... attach 8 AVAudioPlayerNodes, connect to mixer
        // ... synthesize 25 buffers and store in dictionary
        // ... start engine
    }

    func play(colorIndex: Int, surface: Surface) { ... }

    private func configureAudioSession() {
        #if os(iOS)
        try? AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default)
        try? AVAudioSession.sharedInstance().setActive(true)
        #endif
    }

    private func synthesize(frequency: Double, surface: Surface, format: AVAudioFormat) -> AVAudioPCMBuffer { ... }
}
```

### Modifierad fil: `BallDrop/BallDrop/GameScene.swift`

**PhysicsCategory** utökas:
```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
    static let catapult: UInt32   = 1 << 2
    static let block: UInt32      = 1 << 3
    static let wall: UInt32       = 1 << 4
}
```

**Ball-spawn:**
- `ball.physicsBody?.contactTestBitMask = .scoreZone | .catapult | .block | .wall`
- `ball.userData = ["colorIndex": idx]` — sparar vilken färg-index som valdes från `colors`-arrayen.

**Walls i rebuildLayout:**
- `wall.physicsBody?.categoryBitMask = .wall`
- `wall.physicsBody?.contactTestBitMask = .ball`

**SoundManager-instans:** `let soundManager = SoundManager()` som property på GameScene.

**didBegin** utökas:
- Befintlig ball↔catapult-gren: i slutet, anropa `soundManager.play(colorIndex: ..., surface: .catapult)`.
- Befintlig ball↔scoreZone-gren: i slutet, anropa `soundManager.play(colorIndex: ..., surface: .scoreZone)`.
- Ny gren ball↔wall: hämta colorIndex från ball.userData, anropa `soundManager.play(..., surface: .wall)`. Inget annat.
- Ny gren ball↔block (icke-katapult): inspektera blockNode — om `BlockNode` och `.blockType == .trampoline` → `.trampoline` surface, annars `.block`. Anropa `soundManager.play(...)`.

### Modifierad fil: `BallDrop/BallDrop/BlockNode.swift`

I init, sätt:
```swift
physicsBody?.categoryBitMask = PhysicsCategory.block
physicsBody?.contactTestBitMask = PhysicsCategory.ball
```
för alla blocktyper. För `.catapult` bibehålls den befintliga override-sekvensen som sätter `.catapult`-kategorin (och utökas till `categoryBitMask = .block | .catapult` så ball↔catapult-grenen fortfarande triggar OCH ljudet kategoriseras rätt).

### Modifierad fil: `BallDrop/BallDrop/FreeDrawTool.swift`

I `endDraw()` när blocket skapas, sätt `block.physicsBody?.categoryBitMask = PhysicsCategory.block` och `block.physicsBody?.contactTestBitMask = PhysicsCategory.ball`.

### Modifierad fil: `BallDrop/BallDrop/SidebarView.swift`

Ny knapp i KONTROLL-sektionen efter Pausa/Rensa:

```swift
Button(action: { isMuted.toggle() }) {
    Image(systemName: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
        .font(.system(size: 12))
        .frame(maxWidth: .infinity)
}
.controlSize(.small)
```

Ny `@Binding var isMuted: Bool` i SidebarView's signatur.

### Modifierad fil: `BallDrop/BallDrop/ContentView.swift`

- Ny `@State private var isMuted: Bool = false`.
- Ny `.onChange(of: isMuted) { _, newValue in gameScene.soundManager.isMuted = newValue }`.
- Skickar `$isMuted` till SidebarView.

## Synthesizer-detaljer

Buffer-format: 44100 Hz, mono, float32. Genererad direkt i Swift.

För varje (frequency, surface)-kombination:

```swift
let sampleRate: Double = 44100
let totalFrames = AVAudioFrameCount(sampleRate * surface.duration)
let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: totalFrames)!
buffer.frameLength = totalFrames
let samples = buffer.floatChannelData![0]

for frame in 0..<Int(totalFrames) {
    let t = Double(frame) / sampleRate
    let envelope = surface.envelope(at: t, duration: surface.duration)
    let pitch = surface.pitch(at: t, duration: surface.duration, base: frequency)
    let sample = sin(2 * .pi * pitch * t) * envelope * surface.gain
    samples[frame] = Float(sample) * 0.5  // headroom
}
```

`Surface`-tabellen definierar:
- **duration**: `block=0.15, trampoline=0.25, catapult=0.20, scoreZone=0.60, wall=0.08`.
- **envelope(t, duration)**: exponentiell decay `exp(-t / (duration * decayFactor))` där decayFactor varierar per yta.
- **pitch(t, duration, base)**:
  - `block`: `base` (konstant).
  - `trampoline`: `base * (1 + 0.5 * sin(π * t / duration))` — sweep upp och tillbaka.
  - `catapult`: `base * 0.5` (oktav ner).
  - `scoreZone`: blanda `base` + `base * 1.5` (femte) → returnera `(sin(2π·base·t) + 0.6 * sin(2π·base·1.5·t))` (hanteras direkt i syntheseringen).
  - `wall`: `base * 0.5` med 50% amplitud (mörkare och tystare).
- **gain**: per yta, så amplituden balanseras (wall lägre, scoreZone högre).

(Exakta dB/gain-värden trimmas under implementeringen; spec accepterar variationer i amplitude.)

## Edge cases

- **AVAudioSession misslyckas på iOS** (t.ex. annan app blockerar): Engine kan ändå starta, ljud blir bara tystare. `try?` swallowing accepteras.
- **Engine `start()` kastar:** Logga och fortsätt — appen fungerar utan ljud snarare än att krascha.
- **Boll utan colorIndex i userData:** default till 0 (pink). Förhindrar krasch om någon kontaktbana råkar leda till en ball-node som inte spawnades med rätt setup.
- **Många simultana ljud:** Pool av 8 player-nodes. När alla används cycleras nästa via round-robin → äldsta avbryts. Acceptabelt — alternativet (skala upp pool dynamiskt) är onödig komplexitet.
- **macOS — ingen AVAudioSession:** `#if os(iOS)`-skydd runt session-config.
- **Mute under aktivt ljud:** Befintligt schemalagt ljud spelas klart; nya bypassar.

## Testning

Inga unit-tester (project saknar test-target). Manuell verifiering:

1. Mac `swift build` clean.
2. iOS `xcodebuild` clean.
3. Spela appen → bollar plingar tydligt vid kontakt med olika ytor.
4. 5 färger ger 5 distinkta toner (öron-test).
5. Studsmatta = boing, katapult = thock, scoreZone = ding, wall = dunk, vanlig block = pling.
6. Mute-knapp toggar — tystnad omedelbart vid press.
7. På iOS: ljud spelas inte över musik från andra appar (ambient-kategori).
8. iPad: ingen latency-glitch (50+ aktiva bollar samtidigt).

## Out of scope (v1)

- Volume-slider — bara mute on/off.
- Olika ljudtema (möjligt att byta tonschema från pentatonisk dur till t.ex. moll i framtiden).
- Hapticfeedback — separat ärende.
- Musikbakgrund.
- Boll-mot-boll-ljud (skulle bli rörigt med 50+ bollar).
- Persistent mute-state (om man stänger appen är ljud påslagen igen).
