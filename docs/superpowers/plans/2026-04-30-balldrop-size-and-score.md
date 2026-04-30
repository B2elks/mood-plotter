# BallDrop — bollstorlek + poängzoner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lägg till justerbar bollstorlek (slider 4–30 px) och slumpmässigt placerade poängzoner på bottom/left/right-kanterna. När en boll träffar en zon: poäng tickar upp, bollen försvinner, ny zon spawnas på ny slumpmässig position.

**Architecture:** Egna `SKShapeNode`-klasser (`ScoreZone`) som matchar existerande mönster (`BlockNode`, `SpawnPoint`). Score-state lever på `GameScene` med en closure-callback (`onScoreChanged`) till `ContentView`. `ContentView` propagerar score till SwiftUI-overlay och `SidebarView`. Bollstorlek wiras via `@Binding` precis som befintlig `spawnRate`-slider.

**Tech Stack:** Swift 5.9, SpriteKit, SwiftUI, macOS 14+, Swift Package Manager (`swift run` för bygg/körning).

**Spec:** `docs/superpowers/specs/2026-04-30-balldrop-size-and-score-design.md`

**Notes om testning:** Projektet har idag inget XCTest-target (bara `executableTarget` i `Package.swift`). Att sätta upp ett test-target för en grafisk SpriteKit-app med fysik-kollisioner ger marginellt värde — verifieringen sker via `swift run` + visuell kontroll. Jag inkluderar därför inga unit-tester i denna plan, bara manuella verifieringssteg per task. Att lägga till tester senare är inget problem.

---

## File Structure

**Filer att skapa:**
- `BallDrop/BallDrop/ScoreZone.swift` — ny `SKShapeNode`-subklass som representerar en poängzon på en av tre kanter, med pulse-animation och physics-kategori för kontaktdetektering.

**Filer att modifiera:**
- `BallDrop/BallDrop/GameScene.swift` — `ballRadius`-property, `score`-property med `didSet`-callback, `PhysicsCategory`-enum, `spawnScoreZone()`, `resetScore()`, `didBegin(_ contact:)`, `SKPhysicsContactDelegate`-konformans (redan på plats), kontakt-bitmasks i `spawnBall()`.
- `BallDrop/BallDrop/SidebarView.swift` — ny "POÄNG"-sektion (siffra + nollställ-knapp), ny "Storlek"-slider i "KONTROLL"-sektionen, nya bindings/callbacks i view-signaturen.
- `BallDrop/BallDrop/ContentView.swift` — `@State` för `ballRadius` och `score`, `onChange` för `ballRadius` → `gameScene.ballRadius`, set `gameScene.onScoreChanged`, ny callback för reset, `ZStack` med score-overlay i övre högra hörnet.

---

## Task 1: ScoreZone-klassen

**Files:**
- Create: `BallDrop/BallDrop/ScoreZone.swift`

- [ ] **Step 1: Skapa ScoreZone.swift**

Skapa ny fil `BallDrop/BallDrop/ScoreZone.swift`:

```swift
import SpriteKit

class ScoreZone: SKShapeNode {

    enum Edge {
        case bottom, left, right
    }

    static let zoneLength: CGFloat = 80
    static let zoneThickness: CGFloat = 12

    let edge: Edge

    init(edge: Edge) {
        self.edge = edge
        super.init()

        name = "scoreZone"

        let size: CGSize
        switch edge {
        case .bottom:
            size = CGSize(width: ScoreZone.zoneLength, height: ScoreZone.zoneThickness)
        case .left, .right:
            size = CGSize(width: ScoreZone.zoneThickness, height: ScoreZone.zoneLength)
        }

        let rect = CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2), size: size)
        path = CGPath(roundedRect: rect, cornerWidth: 3, cornerHeight: 3, transform: nil)

        fillColor = NSColor(red: 1.0, green: 0.75, blue: 0.20, alpha: 0.85)
        strokeColor = NSColor(red: 1.0, green: 0.85, blue: 0.40, alpha: 1)
        lineWidth = 2

        physicsBody = SKPhysicsBody(rectangleOf: size)
        physicsBody?.isDynamic = false
        physicsBody?.categoryBitMask = PhysicsCategory.scoreZone
        physicsBody?.contactTestBitMask = PhysicsCategory.ball
        physicsBody?.collisionBitMask = 0  // ingen fysisk kollision — bollen passerar fritt

        let pulse = SKAction.sequence([
            SKAction.scale(to: 1.15, duration: 0.6),
            SKAction.scale(to: 1.0, duration: 0.6),
        ])
        run(SKAction.repeatForever(pulse))
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not implemented")
    }
}
```

OBS: `PhysicsCategory` är inte definierad än — den läggs till i Task 2. Detta gör att bygget går sönder mellan Task 1 och Task 2; det är OK eftersom vi commitar först efter Task 2.

- [ ] **Step 2: Verifiera fil skapad**

Run: `ls -la BallDrop/BallDrop/ScoreZone.swift`
Expected: filen listas (ingen "No such file").

(Ingen commit än — vänta tills `PhysicsCategory` är definierad i Task 2.)

---

## Task 2: PhysicsCategory + bollstorlek-property

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till PhysicsCategory överst i filen**

Öppna `BallDrop/BallDrop/GameScene.swift`. Direkt efter `import SpriteKit` (ovanför `class GameScene`), lägg till:

```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
}
```

- [ ] **Step 2: Lägg till ballRadius-property**

I `class GameScene`, intill övriga properties (efter `var spawnRate: TimeInterval = 1.5`), lägg till:

```swift
    var ballRadius: CGFloat = 8
```

- [ ] **Step 3: Använd ballRadius i spawnBall()**

I `spawnBall()`, byt:

```swift
        let radius: CGFloat = 8
```

till:

```swift
        let radius: CGFloat = ballRadius
```

- [ ] **Step 4: Sätt physics-kategorier på bollen**

I `spawnBall()`, efter raden:

```swift
        ball.physicsBody?.mass = 0.1
```

lägg till (före `applyImpulse`):

```swift
        ball.physicsBody?.categoryBitMask = PhysicsCategory.ball
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone
```

- [ ] **Step 5: Bygg och kör**

Run: `cd BallDrop && swift build 2>&1 | tail -20`
Expected: `Build complete!` utan errors.

Run: `cd BallDrop && swift run` och verifiera att appen startar och att bollar fortfarande spawnas (ingen zon syns än — det kommer i Task 3). Stäng appen.

- [ ] **Step 6: Commit**

```bash
git add BallDrop/BallDrop/ScoreZone.swift BallDrop/BallDrop/GameScene.swift
git commit -m "feat: add ScoreZone class and PhysicsCategory bitmasks"
```

---

## Task 3: Score-state och spawnScoreZone

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till score-property med didSet**

I `class GameScene`, intill övriga properties, lägg till:

```swift
    var score: Int = 0 {
        didSet { onScoreChanged?(score) }
    }
    var onScoreChanged: ((Int) -> Void)?
    private var scoreZone: ScoreZone?
```

- [ ] **Step 2: Implementera spawnScoreZone()**

Efter `clearAllBlocks()`-metoden, lägg till:

```swift
    func spawnScoreZone() {
        let edges: [ScoreZone.Edge] = [.bottom, .left, .right]
        let edge = edges.randomElement()!
        let zone = ScoreZone(edge: edge)

        let margin = ScoreZone.zoneLength / 2 + 10
        let halfThick = ScoreZone.zoneThickness / 2

        switch edge {
        case .bottom:
            let x = CGFloat.random(in: margin...(size.width - margin))
            zone.position = CGPoint(x: x, y: halfThick)
        case .left:
            let y = CGFloat.random(in: margin...(size.height - margin))
            zone.position = CGPoint(x: halfThick, y: y)
        case .right:
            let y = CGFloat.random(in: margin...(size.height - margin))
            zone.position = CGPoint(x: size.width - halfThick, y: y)
        }

        scoreZone = zone
        addChild(zone)
    }
```

- [ ] **Step 3: Anropa spawnScoreZone() från didMove**

I `didMove(to view: SKView)`, sist i metoden (efter `freeDrawTool = FreeDrawTool(scene: self)`), lägg till:

```swift
        spawnScoreZone()
```

- [ ] **Step 4: Implementera resetScore()**

Efter `spawnScoreZone()`-metoden, lägg till:

```swift
    func resetScore() {
        score = 0
        scoreZone?.removeFromParent()
        scoreZone = nil
        spawnScoreZone()
    }
```

- [ ] **Step 5: Bygg och kör — verifiera att zon syns**

Run: `cd BallDrop && swift run`
Expected: appen startar, en pulserande guld-orange rektangel syns på en av tre kanter (bottom, left, eller right). Bollar studsar förbi/igenom utan fysisk kollision (collisionBitMask = 0). Stäng appen.

- [ ] **Step 6: Commit**

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: spawn ScoreZone on random edge at scene start"
```

---

## Task 4: Kontaktdetektering (didBegin) + feedback

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Implementera didBegin(_ contact:)**

I `class GameScene`, lägg till metoden (kan läggas före `mouseDown`-metoden):

```swift
    func didBegin(_ contact: SKPhysicsContact) {
        let bodyA = contact.bodyA
        let bodyB = contact.bodyB

        let ballBody: SKPhysicsBody?
        let zoneBody: SKPhysicsBody?

        if bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.scoreZone {
            ballBody = bodyA
            zoneBody = bodyB
        } else if bodyA.categoryBitMask == PhysicsCategory.scoreZone && bodyB.categoryBitMask == PhysicsCategory.ball {
            ballBody = bodyB
            zoneBody = bodyA
        } else {
            return
        }

        guard let ballNode = ballBody?.node, let zoneNode = zoneBody?.node else { return }

        let flash = SKAction.sequence([
            SKAction.group([
                SKAction.scale(to: 1.6, duration: 0.15),
                SKAction.fadeOut(withDuration: 0.15),
            ]),
            SKAction.removeFromParent(),
        ])
        ballNode.physicsBody = nil
        ballNode.run(flash)

        let zoneFlash = SKAction.sequence([
            SKAction.group([
                SKAction.scale(to: 1.4, duration: 0.12),
                SKAction.fadeOut(withDuration: 0.12),
            ]),
            SKAction.removeFromParent(),
        ])
        zoneNode.physicsBody = nil
        zoneNode.run(zoneFlash)

        scoreZone = nil
        score += 1
        spawnScoreZone()
    }
```

- [ ] **Step 2: Bygg och kör — verifiera kontakt funkar**

Run: `cd BallDrop && swift run`
Expected: när en boll träffar zonen ska:
1. Bollen växa lite + fade ut + försvinna.
2. Zonen växa lite + fade ut + försvinna.
3. En ny zon dyker upp på ny slumpmässig position/kant.
4. (Poäng tickar upp internt — vi ser det i nästa task.)

Stäng appen.

- [ ] **Step 3: Commit**

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: handle ball/score-zone contacts with flash feedback"
```

---

## Task 5: Sidebar — POÄNG-sektion + storlek-slider

**Files:**
- Modify: `BallDrop/BallDrop/SidebarView.swift`

- [ ] **Step 1: Utöka SidebarView-signaturen**

I `BallDrop/BallDrop/SidebarView.swift`, ändra `struct SidebarView`-deklarationen från:

```swift
struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var isPaused: Bool
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void
```

till:

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

- [ ] **Step 2: Lägg till POÄNG-sektion ovanför KONTROLL-sektionen**

I `body`, hitta `Divider()` som står precis ovanför `VStack` med "KONTROLL"-texten. Direkt **efter** den dividern (men innan KONTROLL-VStack), lägg in en ny block:

```swift
            VStack(alignment: .leading, spacing: 8) {
                Text("POÄNG")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                Text("\(score)")
                    .font(.system(size: 24, weight: .bold))
                    .padding(.horizontal)

                Button(action: onResetScore) {
                    Label("Nollställ poäng", systemImage: "arrow.counterclockwise")
                        .font(.system(size: 12))
                        .frame(maxWidth: .infinity)
                }
                .controlSize(.small)
                .padding(.horizontal)
            }

            Divider()
```

- [ ] **Step 3: Lägg till Storlek-slider i KONTROLL-sektionen**

I "KONTROLL"-VStack, direkt efter den befintliga `HStack` med "Hastighet"-slidern (slutar med `.padding(.horizontal)`), lägg till en ny `HStack`:

```swift
                HStack {
                    Text("Storlek")
                        .font(.system(size: 12))
                    Slider(value: $ballRadius, in: 4...30, step: 1)
                }
                .padding(.horizontal)
```

- [ ] **Step 4: Bygg (förväntas misslyckas tills ContentView är uppdaterad i Task 6)**

Run: `cd BallDrop && swift build 2>&1 | tail -20`
Expected: bygget misslyckas med fel om att `SidebarView`-init saknar `ballRadius`/`score`/`onResetScore` (kommer från ContentView). Detta är OK — fortsätt till Task 6.

(Ingen commit än — vänta tills ContentView är uppdaterad.)

---

## Task 6: ContentView — wiring + score-overlay

**Files:**
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Lägg till nya @State-properties**

I `struct ContentView: View`, intill befintliga `@State`-properties, lägg till:

```swift
    @State private var ballRadius: Double = 8
    @State private var score: Int = 0
```

- [ ] **Step 2: Uppdatera SidebarView-anropet**

Hitta `SidebarView(...)`-anropet i `body`. Ändra det till:

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

- [ ] **Step 3: Wrap SpriteView i ZStack med score-overlay**

Ändra `SpriteView(scene: gameScene, options: [.allowsTransparency])`-blocket från:

```swift
            SpriteView(scene: gameScene, options: [.allowsTransparency])
                .background(
                    LinearGradient(
                        colors: [
                            Color(red: 0.53, green: 0.81, blue: 0.92),
                            Color(red: 0.60, green: 0.85, blue: 0.78)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
```

till:

```swift
            ZStack(alignment: .topTrailing) {
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(
                        LinearGradient(
                            colors: [
                                Color(red: 0.53, green: 0.81, blue: 0.92),
                                Color(red: 0.60, green: 0.85, blue: 0.78)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
```

- [ ] **Step 4: Lägg till onChange för ballRadius och .onAppear för score-callback**

Hitta `.onChange(of: selectedTool) { ... }`-modifieraren i botten av `body`. Direkt efter den (samma nivå), lägg till:

```swift
        .onChange(of: ballRadius) { _, newValue in
            gameScene.ballRadius = CGFloat(newValue)
        }
        .onAppear {
            gameScene.onScoreChanged = { newScore in
                score = newScore
            }
        }
```

- [ ] **Step 5: Bygg och kör**

Run: `cd BallDrop && swift build 2>&1 | tail -20`
Expected: `Build complete!` utan fel.

Run: `cd BallDrop && swift run`
Expected: appen startar, sidopanelen visar "POÄNG: 0" + "Nollställ poäng"-knapp + "Storlek"-slider, en pulserande zon syns på en av kanterna, en stor vit "0" syns i övre högra hörnet av spelytan.

- [ ] **Step 6: Commit**

```bash
git add BallDrop/BallDrop/SidebarView.swift BallDrop/BallDrop/ContentView.swift
git commit -m "feat: add score sidebar section, size slider, and score overlay"
```

---

## Task 7: Manuell verifiering

- [ ] **Step 1: Bygg och kör appen**

Run: `cd BallDrop && swift run`

- [ ] **Step 2: Verifiera bollstorlek-slider**

1. Dra "Storlek"-slidern till max (30). Vänta tills nya bollar spawnas.
2. Verifiera: nyligen spawnade bollar är märkbart större än de som redan finns på skärmen.
3. Dra till min (4). Verifiera: nya bollar är väldigt små.
4. Verifiera: befintliga bollar har inte ändrat storlek.

- [ ] **Step 3: Verifiera poängzon-funktion**

1. Verifiera: en pulserande guld-orange zon är synlig vid start på en av (bottom, left, right). Aldrig på toppen.
2. Bygg en bana med blocks så att bollar leds mot zonen.
3. När en boll träffar zonen, verifiera:
   - Bollen flashar (skala upp + fade ut) och försvinner.
   - Zonen flashar och försvinner.
   - En ny zon dyker upp på en ny slumpmässig position/kant.
   - Poängräknaren i sidopanelen ökar med 1.
   - Stora siffran i övre högra hörnet uppdateras.

- [ ] **Step 4: Verifiera reset**

1. Träffa zonen ett par gånger så poäng > 0.
2. Klicka "Nollställ poäng".
3. Verifiera: poäng = 0 både i sidopanelen och i overlayen. Befintlig zon ersätts av en ny på slumpmässig position. Bollar i flykten påverkas inte.

- [ ] **Step 5: Verifiera stress (många bollar)**

1. Dra "Hastighet"-slidern mot max (snabb spawn).
2. Vänta tills 50+ bollar är aktiva.
3. Verifiera: ingen krasch, poäng tickar upp korrekt när bollar passerar zoner, ingen visuell glitch.

- [ ] **Step 6: Stäng appen och slutgranska**

Run: `git status` och `git log --oneline -10`
Expected: arbetsträdet rent, fyra commits från denna feature ovanför `e4095cc`.

---

## Verifiering mot specen

- [x] Slider 4–30, default 8 — Task 2 (range), Task 5 (slider), Task 6 (state default)
- [x] Slidern påverkar endast nya bollar — Task 2 step 3 (`spawnBall()` läser `ballRadius` vid spawn)
- [x] En zon i taget på bottom/left/right — Task 3 step 2 (`spawnScoreZone()` med tre edges)
- [x] Fast 80px × 12px — Task 1 (statiska konstanter på `ScoreZone`)
- [x] Pulserande guld-orange — Task 1 (fillColor + repeatForever pulse)
- [x] Träff: poäng+1, boll bort, flash, ny zon — Task 4 (`didBegin`)
- [x] Inget ljud i v1 — bekräftat genom frånvaro
- [x] Sidopanel-siffra + reset-knapp — Task 5 step 2
- [x] Overlay i övre högra hörnet — Task 6 step 4
- [x] Reset nollställer + spawnar ny zon, rör inte bollar — Task 3 step 4 (`resetScore()`)

---

## Rollback om något går fel

Om någon task går snett: `git reset --hard HEAD~N` där N = antal commits från denna feature. De fyra commitsen är atomära per-task så det är säkert att rulla tillbaka enskilda steg.
