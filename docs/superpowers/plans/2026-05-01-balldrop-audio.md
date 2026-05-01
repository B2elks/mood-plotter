# BallDrop — Ljudsystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lägg till runtime-syntheserade kontaktljud i BallDrop. Tonens frekvens bestäms av bollens färg (5 färger = 5 toner i pentatonisk dur), tonens karaktär av ytan (block, studsmatta, katapult, scoreZone, vägg). Mute-knapp i sidopanelen.

**Architecture:** Ny klass `SoundManager` äger en `AVAudioEngine` med 8 `AVAudioPlayerNode` (round-robin polyphoni). Vid init synthseras 25 PCM-buffrar (5 färger × 5 ytor) med rena sinussvängningar och olika envelope/pitch-funktioner per yta. `GameScene` håller en `SoundManager`-instans, sätter `colorIndex` i ball.userData när bollen spawnas, och anropar `play(...)` från didBegin-grenarna. Walls och blocks får nya `PhysicsCategory`-bitar så ball↔wall och ball↔block-kontakter triggar didBegin.

**Tech Stack:** AVFoundation, SpriteKit, SwiftUI. macOS 14+, iPadOS 17+.

**Spec:** `docs/superpowers/specs/2026-05-01-balldrop-audio-design.md`

**Notes om testning:** Inget XCTest-target. Verifiering: `swift build` + `xcodebuild` (Mac + iOS) clean, plus manuell hörselkontroll efter implementering.

---

## File Structure

**Filer att skapa:**
- `BallDrop/BallDrop/SoundManager.swift` — AVAudioEngine-wrapper med synthesis och uppspelnings-API.

**Filer att modifiera:**
- `BallDrop/BallDrop/GameScene.swift` — `PhysicsCategory.block`, `.wall`, `SoundManager`-instans, ball userData, didBegin-grenar för alla ytor, walls bitmasks i `rebuildLayout`.
- `BallDrop/BallDrop/BlockNode.swift` — sätter `categoryBitMask = .block` på alla blocktyper (förutom katapult som behåller `.block | .catapult`), `contactTestBitMask = .ball`.
- `BallDrop/BallDrop/FreeDrawTool.swift` — sätter samma bitmasks på frihandsritade block.
- `BallDrop/BallDrop/SidebarView.swift` — mute-knapp + binding.
- `BallDrop/BallDrop/ContentView.swift` — `@State var isMuted` + onChange-wiring.

---

## Task 1: SoundManager — synth + audio engine

**Files:**
- Create: `BallDrop/BallDrop/SoundManager.swift`

- [ ] **Step 1: Skapa SoundManager.swift**

Skapa filen `BallDrop/BallDrop/SoundManager.swift` med innehåll:

```swift
import AVFoundation
#if os(iOS)
import UIKit
#endif

final class SoundManager {
    enum Surface: String {
        case block, trampoline, catapult, scoreZone, wall
    }

    var isMuted: Bool = false

    private let engine = AVAudioEngine()
    private var playerNodes: [AVAudioPlayerNode] = []
    private var nextNodeIndex = 0
    private var buffers: [String: AVAudioPCMBuffer] = [:]

    private static let frequencies: [Double] = [
        523.25,  // C5  — pink (index 0)
        587.33,  // D5  — orange (index 1)
        659.25,  // E5  — green (index 2)
        783.99,  // G5  — purple (index 3)
        880.00,  // A5  — yellow (index 4)
    ]

    private static let surfaces: [Surface] = [.block, .trampoline, .catapult, .scoreZone, .wall]
    private static let polyphony = 8

    init() {
        configureAudioSession()

        let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 1)!

        // Pre-render all 25 buffers.
        for (colorIndex, freq) in Self.frequencies.enumerated() {
            for surface in Self.surfaces {
                let buffer = synthesize(frequency: freq, surface: surface, format: format)
                buffers[Self.key(colorIndex: colorIndex, surface: surface)] = buffer
            }
        }

        // Wire up player-node pool.
        for _ in 0..<Self.polyphony {
            let node = AVAudioPlayerNode()
            engine.attach(node)
            engine.connect(node, to: engine.mainMixerNode, format: format)
            playerNodes.append(node)
        }

        do {
            try engine.start()
            for node in playerNodes { node.play() }
        } catch {
            print("SoundManager: AVAudioEngine failed to start: \(error)")
        }
    }

    func play(colorIndex: Int, surface: Surface) {
        guard !isMuted else { return }
        let safeIndex = max(0, min(colorIndex, Self.frequencies.count - 1))
        let key = Self.key(colorIndex: safeIndex, surface: surface)
        guard let buffer = buffers[key] else { return }

        let node = playerNodes[nextNodeIndex]
        nextNodeIndex = (nextNodeIndex + 1) % playerNodes.count

        // Stop any in-flight buffer on this node so we don't queue up.
        node.stop()
        node.scheduleBuffer(buffer, at: nil, options: [], completionHandler: nil)
        node.play()
    }

    private static func key(colorIndex: Int, surface: Surface) -> String {
        "\(colorIndex)-\(surface.rawValue)"
    }

    private func configureAudioSession() {
        #if os(iOS)
        try? AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default)
        try? AVAudioSession.sharedInstance().setActive(true)
        #endif
    }

    private func synthesize(frequency: Double, surface: Surface, format: AVAudioFormat) -> AVAudioPCMBuffer {
        let sampleRate = format.sampleRate
        let duration: Double
        let gain: Double
        switch surface {
        case .block:      duration = 0.15; gain = 0.55
        case .trampoline: duration = 0.25; gain = 0.55
        case .catapult:   duration = 0.20; gain = 0.65
        case .scoreZone:  duration = 0.60; gain = 0.55
        case .wall:       duration = 0.08; gain = 0.30
        }

        let totalFrames = AVAudioFrameCount(sampleRate * duration)
        let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: totalFrames)!
        buffer.frameLength = totalFrames
        let samples = buffer.floatChannelData![0]

        var phase: Double = 0
        for frame in 0..<Int(totalFrames) {
            let t = Double(frame) / sampleRate
            let progress = t / duration  // 0..1

            // Per-surface envelope.
            let envelope: Double
            switch surface {
            case .block:
                envelope = exp(-t / (duration * 0.30))
            case .trampoline:
                envelope = exp(-t / (duration * 0.50))
            case .catapult:
                let attack = min(1.0, t / 0.005)  // 5 ms ramp
                envelope = attack * exp(-t / (duration * 0.40))
            case .scoreZone:
                let attack = min(1.0, t / 0.020)  // 20 ms ramp
                envelope = attack * exp(-t / (duration * 0.60))
            case .wall:
                envelope = exp(-t / (duration * 0.30))
            }

            // Per-surface instantaneous frequency.
            let f: Double
            switch surface {
            case .block, .scoreZone:
                f = frequency
            case .trampoline:
                f = frequency * (1.0 + 0.5 * sin(.pi * progress))
            case .catapult, .wall:
                f = frequency * 0.5
            }

            phase += 2 * .pi * f / sampleRate

            // Per-surface waveform (mostly sine, scoreZone adds a fifth).
            let core: Double
            switch surface {
            case .scoreZone:
                core = sin(phase) * 0.6 + sin(phase * 1.5) * 0.4
            default:
                core = sin(phase)
            }

            samples[frame] = Float(core * envelope * gain)
        }

        return buffer
    }
}
```

- [ ] **Step 2: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`. SoundManager ska kompilera utan användning.

- [ ] **Step 3: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -5
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 4: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/SoundManager.swift
git commit -m "feat: add SoundManager with synthesized 25-buffer tone palette"
```

---

## Task 2: PhysicsCategory + bitmasks på block och walls

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/BlockNode.swift`
- Modify: `BallDrop/BallDrop/FreeDrawTool.swift`

- [ ] **Step 1: Utöka PhysicsCategory**

I `BallDrop/BallDrop/GameScene.swift`, ändra:

```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
    static let catapult: UInt32   = 1 << 2
}
```

till:

```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
    static let catapult: UInt32   = 1 << 2
    static let block: UInt32      = 1 << 3
    static let wall: UInt32       = 1 << 4
}
```

- [ ] **Step 2: Sätt wall-bitmasks i rebuildLayout**

I `BallDrop/BallDrop/GameScene.swift`, hitta `rebuildLayout()`-metoden. Inuti den, för `leftWall` och `rightWall`, lägg till bitmask-rader EFTER `physicsBody?.friction = 0.2` på respektive vägg. Slutresultatet för båda väggarna ska se ut så här (visar bara en, gör samma på båda):

```swift
        let leftWall = SKNode()
        leftWall.name = "wall"
        leftWall.position = CGPoint(x: 0, y: size.height / 2)
        leftWall.physicsBody = SKPhysicsBody(rectangleOf: CGSize(width: wallThickness, height: size.height))
        leftWall.physicsBody?.isDynamic = false
        leftWall.physicsBody?.friction = 0.2
        leftWall.physicsBody?.categoryBitMask = PhysicsCategory.wall
        leftWall.physicsBody?.contactTestBitMask = PhysicsCategory.ball
        addChild(leftWall)
```

(Och samma två rader på rightWall.)

- [ ] **Step 3: Sätt categoryBitMask på alla BlockNode-typer**

I `BallDrop/BallDrop/BlockNode.swift`, hitta slutet av `init(type:)`. Just nu finns där ett block med:

```swift
        physicsBody?.isDynamic = false
        physicsBody?.friction = 0.3
        physicsBody?.restitution = 0.5

        if type == .trampoline {
            physicsBody?.restitution = 1.4
        }

        if type == .catapult {
            physicsBody?.categoryBitMask = PhysicsCategory.catapult
            physicsBody?.contactTestBitMask = PhysicsCategory.ball
        }
```

Ändra till:

```swift
        physicsBody?.isDynamic = false
        physicsBody?.friction = 0.3
        physicsBody?.restitution = 0.5
        physicsBody?.categoryBitMask = PhysicsCategory.block
        physicsBody?.contactTestBitMask = PhysicsCategory.ball

        if type == .trampoline {
            physicsBody?.restitution = 1.4
        }

        if type == .catapult {
            physicsBody?.categoryBitMask = PhysicsCategory.block | PhysicsCategory.catapult
            physicsBody?.contactTestBitMask = PhysicsCategory.ball
        }
```

(Default är nu `.block`-kategori. Katapult OR-ar med `.catapult` så befintlig didBegin-gren fortfarande fungerar.)

- [ ] **Step 4: Sätt bitmasks på frihandsritade block**

I `BallDrop/BallDrop/FreeDrawTool.swift`, hitta `endDraw()`-metoden. Hitta blocket:

```swift
        if !bodies.isEmpty {
            block.physicsBody = SKPhysicsBody(bodies: bodies)
            block.physicsBody?.isDynamic = false
            block.physicsBody?.friction = 0.3
            block.physicsBody?.restitution = 0.5
        }
```

Ändra till:

```swift
        if !bodies.isEmpty {
            block.physicsBody = SKPhysicsBody(bodies: bodies)
            block.physicsBody?.isDynamic = false
            block.physicsBody?.friction = 0.3
            block.physicsBody?.restitution = 0.5
            block.physicsBody?.categoryBitMask = PhysicsCategory.block
            block.physicsBody?.contactTestBitMask = PhysicsCategory.ball
        }
```

- [ ] **Step 5: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 6: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 7: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/GameScene.swift BallDrop/BallDrop/BlockNode.swift BallDrop/BallDrop/FreeDrawTool.swift
git commit -m "feat: add block + wall physics categories for contact-based audio"
```

---

## Task 3: GameScene-wiring — SoundManager + ball userData + didBegin-grenar

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till SoundManager-instans + utöka ball contactTestBitMask**

I `BallDrop/BallDrop/GameScene.swift`, lägg till en property på GameScene-klassen, intill övriga properties (bra plats: efter `private var rotateInitialZRotation: CGFloat = 0`):

```swift
    let soundManager = SoundManager()
```

Sedan i `spawnBall()`, hitta:

```swift
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone | PhysicsCategory.catapult
```

Ändra till:

```swift
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone | PhysicsCategory.catapult | PhysicsCategory.block | PhysicsCategory.wall
```

- [ ] **Step 2: Spara colorIndex i ball.userData**

I `spawnBall()`, hitta:

```swift
        let colors: [SKColor] = [
            SKColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
            SKColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
            SKColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
            SKColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
            SKColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
        ]

        let ball = SKShapeNode(circleOfRadius: radius)
        ball.name = "ball"
        ball.fillColor = colors.randomElement()!
```

Ändra till:

```swift
        let colors: [SKColor] = [
            SKColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
            SKColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
            SKColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
            SKColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
            SKColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
        ]
        let colorIndex = Int.random(in: 0..<colors.count)

        let ball = SKShapeNode(circleOfRadius: radius)
        ball.name = "ball"
        ball.fillColor = colors[colorIndex]
        ball.userData = ["colorIndex": colorIndex]
```

- [ ] **Step 3: Lägg till hjälpare för colorIndex-extraktion**

I `BallDrop/BallDrop/GameScene.swift`, lägg till en privat helper-metod intill övriga (bra plats: efter `removeBlock`):

```swift
    private func colorIndex(of node: SKNode?) -> Int {
        (node?.userData?["colorIndex"] as? Int) ?? 0
    }
```

- [ ] **Step 4: Lägg till ljud i befintliga catapult- och scoreZone-grenar**

I `didBegin(_:)`, hitta catapult-grenen som slutar med:

```swift
            let flash = SKAction.sequence([
                SKAction.scale(to: 1.15, duration: 0.08),
                SKAction.scale(to: 1.0, duration: 0.08),
            ])
            catNode.run(flash)
            return
        }
```

Lägg till `soundManager.play(...)` direkt EFTER `catNode.run(flash)`:

```swift
            let flash = SKAction.sequence([
                SKAction.scale(to: 1.15, duration: 0.08),
                SKAction.scale(to: 1.0, duration: 0.08),
            ])
            catNode.run(flash)
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .catapult)
            return
        }
```

I scoreZone-grenen, hitta slutet:

```swift
        score += 1
        spawnScoreZone()
    }
```

Ändra till:

```swift
        soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .scoreZone)
        score += 1
        spawnScoreZone()
    }
```

(Lägg `play`-anropet INNAN `score += 1`/`spawnScoreZone()` så ljudet hinner schemaläggas tidigt.)

- [ ] **Step 5: Uppdatera den befintliga catapult-grenens condition**

Catapult-bodyn har efter Task 2 `categoryBitMask = .block | .catapult` (två bitar). Den befintliga catapult-grenen i didBegin använder strikt `==`-jämförelse och slutar matcha. Hitta:

```swift
        if (bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.catapult) ||
           (bodyA.categoryBitMask == PhysicsCategory.catapult && bodyB.categoryBitMask == PhysicsCategory.ball) {
```

Ändra till att testa bit-mask-bit istället för strikt likhet:

```swift
        if (bodyA.categoryBitMask == PhysicsCategory.ball && (bodyB.categoryBitMask & PhysicsCategory.catapult) != 0) ||
           ((bodyA.categoryBitMask & PhysicsCategory.catapult) != 0 && bodyB.categoryBitMask == PhysicsCategory.ball) {
```

Resten av branchens kropp behöver inte ändras (ballPB-resolutionen använder `bodyA.categoryBitMask == .ball` vilket fortfarande är giltigt eftersom bollen har ren `.ball`-mask).

- [ ] **Step 6: Lägg till ball↔wall-gren och ball↔block-gren i didBegin**

I `didBegin(_ contact: SKPhysicsContact)`, direkt efter raderna `let bodyA = contact.bodyA` och `let bodyB = contact.bodyB` men **FÖRE** den (nu uppdaterade) catapult-grenen, lägg till två nya tidiga grenar:

```swift
        // Ball ↔ wall: pure sound, no other physics effect.
        if (bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.wall) ||
           (bodyA.categoryBitMask == PhysicsCategory.wall && bodyB.categoryBitMask == PhysicsCategory.ball) {
            let ballNode = bodyA.categoryBitMask == PhysicsCategory.ball ? bodyA.node : bodyB.node
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .wall)
            return
        }

        // Ball ↔ block (incl. trampoline). Catapult bodies have .block|.catapult and are
        // explicitly excluded so the catapult branch below handles them.
        let aIsBall = bodyA.categoryBitMask == PhysicsCategory.ball
        let aIsBlock = (bodyA.categoryBitMask & PhysicsCategory.block) != 0 && (bodyA.categoryBitMask & PhysicsCategory.catapult) == 0
        let bIsBall = bodyB.categoryBitMask == PhysicsCategory.ball
        let bIsBlock = (bodyB.categoryBitMask & PhysicsCategory.block) != 0 && (bodyB.categoryBitMask & PhysicsCategory.catapult) == 0
        if (aIsBall && bIsBlock) || (aIsBlock && bIsBall) {
            let ballNode = aIsBall ? bodyA.node : bodyB.node
            let blockNode = aIsBall ? bodyB.node : bodyA.node
            let surface: SoundManager.Surface
            if let bn = blockNode as? BlockNode, bn.blockType == .trampoline {
                surface = .trampoline
            } else {
                surface = .block
            }
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: surface)
            return
        }
```

Slutgiltig branch-ordning i didBegin (uppifrån och ner): wall → block → catapult → scoreZone. Block-grenen exkluderar katapulter via `& .catapult == 0`, så katapult-kontakter når catapult-grenen.

- [ ] **Step 7: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 8: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 9: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: route contact events to SoundManager based on surface and ball color"
```

---

## Task 4: Mute-knapp i SidebarView + ContentView-wiring

**Files:**
- Modify: `BallDrop/BallDrop/SidebarView.swift`
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Lägg till `isMuted` binding i SidebarView**

I `BallDrop/BallDrop/SidebarView.swift`, ändra struct-deklarationen från:

```swift
struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var ballRadius: Double
    @Binding var isPaused: Bool
    @Binding var score: Int
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void
    var onResetScore: () -> Void
```

till:

```swift
struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var ballRadius: Double
    @Binding var isPaused: Bool
    @Binding var isMuted: Bool
    @Binding var score: Int
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void
    var onResetScore: () -> Void
```

- [ ] **Step 2: Lägg till mute-knappen i KONTROLL-sektionen**

I `body`, hitta blocket som har Pausa- och Rensa-knapparna:

```swift
                HStack(spacing: 8) {
                    Button(action: { isPaused.toggle() }) {
                        Label(isPaused ? "Starta" : "Pausa",
                              systemImage: isPaused ? "play.fill" : "pause.fill")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)

                    Button(action: onClearBlocks) {
                        Label("Rensa", systemImage: "trash")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)
                }
                .padding(.horizontal)
```

Ändra till (lägger till en tredje knapp för mute):

```swift
                HStack(spacing: 8) {
                    Button(action: { isPaused.toggle() }) {
                        Label(isPaused ? "Starta" : "Pausa",
                              systemImage: isPaused ? "play.fill" : "pause.fill")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)

                    Button(action: onClearBlocks) {
                        Label("Rensa", systemImage: "trash")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)

                    Button(action: { isMuted.toggle() }) {
                        Image(systemName: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)
                }
                .padding(.horizontal)
```

- [ ] **Step 3: Lägg till `isMuted` state + onChange + binding i ContentView**

I `BallDrop/BallDrop/ContentView.swift`, lägg till en ny `@State`-property intill övriga (bra plats: efter `@State private var score: Int = 0`):

```swift
    @State private var isMuted: Bool = false
```

Hitta SidebarView-anropet:

```swift
            SidebarView(
                selectedTool: $selectedTool,
                spawnRate: $spawnRate,
                ballRadius: $ballRadius,
                isPaused: $isPaused,
                score: $score,
                onPlaceBlock: { type in
                    gameScene.addBlock(type: type,
                        at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
                },
                onClearBlocks: {
                    gameScene.clearAllBlocks()
                },
                onResetScore: {
                    gameScene.resetScore()
                }
            )
```

Ändra till (lägger till `isMuted: $isMuted`):

```swift
            SidebarView(
                selectedTool: $selectedTool,
                spawnRate: $spawnRate,
                ballRadius: $ballRadius,
                isPaused: $isPaused,
                isMuted: $isMuted,
                score: $score,
                onPlaceBlock: { type in
                    gameScene.addBlock(type: type,
                        at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
                },
                onClearBlocks: {
                    gameScene.clearAllBlocks()
                },
                onResetScore: {
                    gameScene.resetScore()
                }
            )
```

Hitta `.onChange`-blocken längst ner i body, lägg till en till EFTER den befintliga `onChange(of: ballRadius)`:

```swift
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
```

(Plac som syskon till de andra `.onChange`-modifierarna, alltså chained på HStack-nivån.)

- [ ] **Step 4: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 5: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 6: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/SidebarView.swift BallDrop/BallDrop/ContentView.swift
git commit -m "feat: add mute toggle in sidebar wired to SoundManager"
```

---

## Task 5: Manuell verifiering

- [ ] **Step 1: Kör Mac-versionen**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift run
```

(Detta öppnar GUI — får göras av användaren, inte av subagent.)

- [ ] **Step 2: Verifiera ljud**

1. Bollar plingar tydligt vid kontakt med vanliga block (kort marimba-pling, distinkt ton per färg).
2. Studsmatta — ljud böjs som en boing.
3. Katapult — kraftigare thock, lägre ton.
4. ScoreZone — ding/klocka, längre och mjukare.
5. Vägg — kort dunk, mörkare och tystare än block.
6. 5 olika bollfärger ger 5 distinkta toner.
7. Mute-knapp toggar — instant tystnad vid press.
8. Mute-ikonen växlar mellan högtalare och överstruken högtalare.

- [ ] **Step 3: Verifiera iOS i Xcode-simulator**

I Xcode, scheme `BallDrop-iOS`, välj iPad Pro-simulator, Cmd+R. Verifiera samma checklist som steg 2.

- [ ] **Step 4: Stress-test**

Hastighet på max, vänta tills 30+ bollar är aktiva. Verifiera att ljud fortfarande hörs (round-robin), inga krascher.

---

## Verifiering mot specen

- [x] 5 frekvenser per pentatonisk dur (C5/D5/E5/G5/A5) — Task 1.
- [x] 5 ytor (block/trampoline/catapult/scoreZone/wall) med olika envelope/pitch — Task 1.
- [x] 25 buffrar pre-renderade — Task 1.
- [x] 8 player-nodes round-robin — Task 1.
- [x] AVAudioSession ambient (iOS only) — Task 1.
- [x] PhysicsCategory.block + .wall + bitmasks på alla blocktyper, freedraw, walls — Task 2.
- [x] Ball userData colorIndex — Task 3 step 2.
- [x] didBegin-grenar för wall, block, trampoline (via blockType inspection), scoreZone, catapult — Task 3 step 4-5.
- [x] Mute-knapp i sidopanel — Task 4.
- [x] ContentView-wiring — Task 4 step 3.

---

## Rollback om något går fel

Fyra atomic feature-commits. För att rulla tillbaka: `git reset --hard HEAD~N`.
