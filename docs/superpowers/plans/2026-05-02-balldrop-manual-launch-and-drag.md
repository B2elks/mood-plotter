# BallDrop — Manuell ball-skjutning + drag-from-sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Förbättra spel-läget: manuell "Skjut iväg!"-knapp ersätter auto-spawn, och block placeras genom att draga ikoner från sidopanelen istället för tap → spawn-i-mitten.

**Architecture:** Liten flagga `manualSpawnMode` + ny `launchBall()`-metod på `GameScene`. `LevelGameScreen` får en stor "Skjut iväg!"-knapp + omdesignad block-lista där varje rad är en drag-källa. Drag-och-drop sker via SwiftUI's `DragGesture(coordinateSpace: .global)` + `GeometryReader` för att veta scenens globala frame. Bygg-läget oförändrat. `blockIcon`-helpern flyttas till en delad fil så både `SidebarView` och `LevelGameScreen` kan använda den.

**Tech Stack:** SwiftUI (`DragGesture`, `GeometryReader`, `.overlay`), SpriteKit (`convertPoint(fromView:)`), Foundation. macOS 14+, iPadOS 17+.

**Spec:** `docs/superpowers/specs/2026-05-02-balldrop-manual-launch-and-drag-design.md`

**Notes om testning:** Inga unit-tester. Verifiering: `swift build` + `xcodebuild` clean efter varje task, plus manuell verifiering i slutet.

---

## File Structure

**Filer att skapa:**
- `BallDrop/BallDrop/BlockIcon.swift` — extraherad delad icon-helper + Triangle-shape.

**Filer att modifiera:**
- `BallDrop/BallDrop/SidebarView.swift` — ta bort lokal `blockIcon` + `Triangle`.
- `BallDrop/BallDrop/GameScene.swift` — `manualSpawnMode` + `launchBall()` + `update()`-conditional.
- `BallDrop/BallDrop/LevelGameScreen.swift` — "Skjut iväg!"-knapp + drag-from-sidebar block-lista.

---

## Task 1: Extrahera BlockIcon

**Files:**
- Create: `BallDrop/BallDrop/BlockIcon.swift`
- Modify: `BallDrop/BallDrop/SidebarView.swift`

- [ ] **Step 1: Skapa BlockIcon.swift**

Skapa fil `BallDrop/BallDrop/BlockIcon.swift` med innehåll:

```swift
import SwiftUI

@ViewBuilder
func blockIcon(_ type: BlockType) -> some View {
    switch type {
    case .horizontalRect:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 24, height: 6)
    case .verticalRect:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 6, height: 24)
    case .diagonal:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 24, height: 6)
            .rotationEffect(.degrees(-30))
    case .circle:
        Circle()
            .fill(Color.gray.opacity(0.4))
            .frame(width: 18, height: 18)
    case .triangle:
        Triangle()
            .fill(Color.gray.opacity(0.4))
            .frame(width: 20, height: 18)
    case .trampoline:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color(red: 0.40, green: 0.78, blue: 0.45))
            .frame(width: 24, height: 6)
    case .catapult:
        ZStack {
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(red: 1.0, green: 0.55, blue: 0.20))
                .frame(width: 24, height: 6)
            Triangle()
                .fill(Color.white)
                .frame(width: 6, height: 5)
                .offset(y: -1)
        }
    }
}

struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        Path { p in
            p.move(to: CGPoint(x: rect.midX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
            p.closeSubpath()
        }
    }
}
```

- [ ] **Step 2: Ta bort blockIcon + Triangle från SidebarView.swift**

I `BallDrop/BallDrop/SidebarView.swift`, hitta `@ViewBuilder private func blockIcon(_ type: BlockType) -> some View`-funktionen — den är den enda definitionen i filen efter body-closingen. Ta bort hela funktionsdefinitionen plus `Triangle: Shape`-strukten i botten av filen.

OBS: Befintliga anrop `blockIcon(type)` i SidebarView's body fungerar fortfarande eftersom funktionen nu är fil-scope global (i BlockIcon.swift). Inga andra ändringar i SidebarView krävs.

- [ ] **Step 3: Regenerera Xcode-projektet**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 4: Bygg på Mac**

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 5: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 6: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/BlockIcon.swift BallDrop/BallDrop/SidebarView.swift BallDrop/BallDrop.xcodeproj
git commit -m "refactor: extract blockIcon and Triangle to shared file"
```

---

## Task 2: GameScene manualSpawnMode + launchBall()

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till manualSpawnMode property**

I `BallDrop/BallDrop/GameScene.swift`, hitta:

```swift
    var levelConfig: LevelConfig?
    private var ballsRemaining: Int = 0
    private var blocksRemaining: [BlockType: Int] = [:]
```

Lägg till en ny property direkt under:

```swift
    var manualSpawnMode: Bool = false
```

- [ ] **Step 2: Sätt manualSpawnMode = true i startLevel**

Hitta `func startLevel(_ config: LevelConfig)`. Ändra första raden från:

```swift
    func startLevel(_ config: LevelConfig) {
        levelConfig = config
```

till:

```swift
    func startLevel(_ config: LevelConfig) {
        levelConfig = config
        manualSpawnMode = true
```

- [ ] **Step 3: Lägg till launchBall()-metod**

Direkt efter `startLevel(_:)`-metoden, lägg till:

```swift
    func launchBall() {
        guard levelConfig != nil, ballsRemaining > 0 else { return }
        spawnBall()
        ballsRemaining -= 1
        onBallsRemainingChanged?(ballsRemaining)
    }
```

- [ ] **Step 4: Hoppa över auto-spawn i level-mode när manualSpawnMode**

Hitta `update(_:)`. Inuti `if let cfg = levelConfig {`-grenen, ändra:

```swift
        if let cfg = levelConfig {
            if ballsRemaining > 0 && currentTime - lastSpawnTime >= spawnRate {
                spawnBall()
                ballsRemaining -= 1
                onBallsRemainingChanged?(ballsRemaining)
                lastSpawnTime = currentTime
            }
            if ballsRemaining == 0
                && children.first(where: { $0.name == "ball" }) == nil
                && score < cfg.scoreTarget {
                onLevelFailed?()
                levelConfig = nil
            }
        } else {
```

till:

```swift
        if let cfg = levelConfig {
            if !manualSpawnMode && ballsRemaining > 0 && currentTime - lastSpawnTime >= spawnRate {
                spawnBall()
                ballsRemaining -= 1
                onBallsRemainingChanged?(ballsRemaining)
                lastSpawnTime = currentTime
            }
            if ballsRemaining == 0
                && children.first(where: { $0.name == "ball" }) == nil
                && score < cfg.scoreTarget {
                onLevelFailed?()
                levelConfig = nil
            }
        } else {
```

(Bara en `!manualSpawnMode &&` lagts till på första `if` inuti grenen. Fail-detection oförändrad.)

- [ ] **Step 5: Bygg på Mac**

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 6: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 7: Commit**

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: add manualSpawnMode + launchBall() for player-controlled spawn in levels"
```

---

## Task 3: "Skjut iväg!"-knapp + drag-from-sidebar i LevelGameScreen

**Files:**
- Modify: `BallDrop/BallDrop/LevelGameScreen.swift`

Detta är den största tasken — block-listan byggs om från grunden + ny knapp + drag-state + ghost-overlay.

- [ ] **Step 1: Lägg till state för drag + sceneFrame**

I `BallDrop/BallDrop/LevelGameScreen.swift`, lägg till nya `@State`-properties intill övriga (efter `@State private var isMuted: Bool = false`):

```swift
    @State private var dragState: DragState? = nil
    @State private var sceneFrame: CGRect = .zero

    struct DragState {
        let type: BlockType
        var globalLocation: CGPoint
    }
```

- [ ] **Step 2: Wrappa SpriteKitView/SpriteView i GeometryReader för att fånga sceneFrame**

I `body`, hitta blocket:

```swift
            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(gameBackground)
                #else
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(gameBackground)
                #endif
```

Ersätt med:

```swift
            ZStack(alignment: .topTrailing) {
                GeometryReader { proxy in
                    #if os(iOS)
                    SpriteKitView(scene: gameScene)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(gameBackground)
                        .onAppear { sceneFrame = proxy.frame(in: .global) }
                        .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
                    #else
                    SpriteView(scene: gameScene, options: [.allowsTransparency])
                        .background(gameBackground)
                        .onAppear { sceneFrame = proxy.frame(in: .global) }
                        .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
                    #endif
                }
```

- [ ] **Step 3: Stäng GeometryReader-block korrekt**

Den befintliga `Text("\(score)")`-overlayen är kvar i `ZStack`. Eftersom GeometryReader nu wrappar SpriteKit-vyn behöver vi stänga den korrekt. Det innebär:

```swift
            ZStack(alignment: .topTrailing) {
                GeometryReader { proxy in
                    #if os(iOS)
                    SpriteKitView(scene: gameScene)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(gameBackground)
                        .onAppear { sceneFrame = proxy.frame(in: .global) }
                        .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
                    #else
                    SpriteView(scene: gameScene, options: [.allowsTransparency])
                        .background(gameBackground)
                        .onAppear { sceneFrame = proxy.frame(in: .global) }
                        .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
                    #endif
                }

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
```

- [ ] **Step 4: Lägg till "Skjut iväg!"-knapp i sidebar och redesigna block-listan**

I `LevelGameScreen.swift`, hitta hela `private var sidebar: some View`-computed property och ersätt den med:

```swift
    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(level.tier.displayName) — \(level.name)")
                    .font(.system(size: 14, weight: .bold))
                Text("Mål: \(level.scoreTarget)p")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal)
            .padding(.top, 16)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BOLLAR KVAR")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                Text("\(ballsRemaining)")
                    .font(.system(size: 28, weight: .bold))
            }
            .padding(.horizontal)

            VStack(alignment: .leading, spacing: 6) {
                Text("SCORE")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                Text("\(score)")
                    .font(.system(size: 28, weight: .bold))
            }
            .padding(.horizontal)

            Button(action: { gameScene.launchBall() }) {
                HStack {
                    Image(systemName: "arrow.up.forward.circle.fill")
                        .font(.system(size: 20))
                    Text("Skjut iväg! (\(ballsRemaining) kvar)")
                        .font(.system(size: 14, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(ballsRemaining > 0 ? Color.green : Color.gray.opacity(0.3))
                .foregroundColor(.white)
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(.plain)
            .disabled(ballsRemaining == 0)
            .padding(.horizontal)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BLOCK — DRA UT")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(orderedBlockTypes, id: \.rawValue) { type in
                    blockRow(type)
                }
            }

            Spacer()

            Button(action: onCancel) {
                Label("Avbryt", systemImage: "xmark")
                    .font(.system(size: 13))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.red.opacity(0.15))
                    .foregroundColor(.red)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
            .padding(.horizontal)
            .padding(.bottom, 16)
        }
    }

    @ViewBuilder
    private func blockRow(_ type: BlockType) -> some View {
        let count = blocksRemaining[type] ?? 0
        let enabled = count > 0
        HStack(spacing: 10) {
            blockIcon(type)
                .frame(width: 28, height: 28)
            Text(label(for: type))
                .font(.system(size: 13))
            Spacer()
            Text("\(count)")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(enabled ? .blue : .secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.white)
        )
        .opacity(enabled ? 1.0 : 0.4)
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onChanged { value in
                    guard enabled else { return }
                    dragState = DragState(type: type, globalLocation: value.location)
                }
                .onEnded { value in
                    guard enabled else { return }
                    handleDrop(at: value.location, type: type)
                    dragState = nil
                }
        )
    }
```

- [ ] **Step 5: Ta bort gamla placeBlock-helpern (inte längre använd)**

I `LevelGameScreen.swift`, hitta och ta bort hela `private func placeBlock(_ type: BlockType)`-metoden — den anropades bara av den gamla tap-knappen som nu ersatts.

- [ ] **Step 6: Lägg till handleDrop + ghost-overlay**

I `LevelGameScreen.swift`, lägg till två nya hjälp-metoder/computed properties intill `gameBackground`:

```swift
    private func handleDrop(at globalLocation: CGPoint, type: BlockType) {
        guard sceneFrame.contains(globalLocation) else { return }
        guard (blocksRemaining[type] ?? 0) > 0 else { return }
        let viewLoc = CGPoint(
            x: globalLocation.x - sceneFrame.origin.x,
            y: globalLocation.y - sceneFrame.origin.y
        )
        let sceneLoc = gameScene.convertPoint(fromView: viewLoc)
        gameScene.addBlock(type: type, at: sceneLoc)
    }

    @ViewBuilder
    private var ghostOverlay: some View {
        if let drag = dragState {
            blockIcon(drag.type)
                .scaleEffect(2.5)
                .opacity(0.7)
                .position(x: drag.globalLocation.x, y: drag.globalLocation.y)
                .ignoresSafeArea()
                .allowsHitTesting(false)
        }
    }
```

Lägg till `.overlay { ghostOverlay }` på topnivå-HStack:

Hitta:

```swift
        .overlay {
            if let outcome = outcome {
                outcomeModal(outcome)
            }
        }
```

Ändra till:

```swift
        .overlay { ghostOverlay }
        .overlay {
            if let outcome = outcome {
                outcomeModal(outcome)
            }
        }
```

(Två `.overlay`-modifierar — ghost först, modal ovanpå.)

OBS: ghost-overlay positioneras i global koordinatrymd. SwiftUI `.position` använder lokal koordinatrymd, så vi behöver `.ignoresSafeArea()` för att slippa safe-area-inset och `.position` mot HStack-koordinatrymden. Eftersom HStack täcker hela skärmen och vi använder global-coords på drag, fungerar `.position(x: drag.globalLocation.x, y: drag.globalLocation.y)` korrekt på iPad i full-screen.

- [ ] **Step 7: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 8: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 9: Commit**

```bash
git add BallDrop/BallDrop/LevelGameScreen.swift
git commit -m "feat: drag blocks from sidebar + Skjut iväg button in level mode"
```

---

## Task 4: Manuell verifiering

- [ ] **Step 1: Kör Mac-versionen**

```bash
swift run
```

(Kör av användaren — öppnar GUI.)

- [ ] **Step 2: Verifiera bygg-läget oförändrat**

1. HomeScreen → Bygg → bollar spawnas automatiskt som tidigare. Block placeras genom tap på sidopanel-knapp som tidigare. Allt oförändrat.

- [ ] **Step 3: Verifiera "Skjut iväg!"-knappen**

1. HomeScreen → Spela → välj Brons 1.
2. Inga bollar spawnas automatiskt.
3. "Skjut iväg!"-knapp synlig i grön, säger "Skjut iväg! (3 kvar)".
4. Tryck → en boll spawnas, knappens räknare blir "(2 kvar)".
5. Vänta — inga fler bollar spawnas av sig själva.
6. När räknare når 0 — knappen blir grå/disabled.

- [ ] **Step 4: Verifiera drag-from-sidebar**

1. I level-läge: tryck och håll på en block-rad i sidopanelen.
2. Ghost-preview (block-ikon, skalad upp + halv-transparent) följer fingret/markören.
3. Släpp inom spelytan → block placeras där, räknaren dekrementeras.
4. Släpp utanför spelytan → ghost försvinner, ingenting placeras, räknaren oförändrad.
5. Försök dra ett block med räknare 0 → ingen ghost visas (eller ghost visas men drop blir no-op).

- [ ] **Step 5: Verifiera win/lose-flow oförändrat**

1. Klara banan → "Bana klarad!"-modal som tidigare.
2. Misslyckas (slut på bollar utan att nå mål) → "Försök igen"-modal.

- [ ] **Step 6: Verifiera iOS i simulator**

I Xcode, scheme `BallDrop-iOS`, kör i iPad-simulator (eller fysisk iPad). Samma checklist som ovan men med touch.

---

## Verifiering mot specen

- [x] manualSpawnMode = true sätts i startLevel — Task 2 step 2.
- [x] launchBall() med guard på ballsRemaining + dekrement — Task 2 step 3.
- [x] update() hoppar över auto-spawn när manualSpawnMode — Task 2 step 4.
- [x] "Skjut iväg!"-knapp grön/grå med räknare — Task 3 step 4.
- [x] BlockIcon delad mellan SidebarView och LevelGameScreen — Task 1.
- [x] Drag-gesture på block-rader — Task 3 step 4.
- [x] Ghost-overlay följer fingret — Task 3 step 6.
- [x] sceneFrame fångas via GeometryReader — Task 3 step 2.
- [x] handleDrop konverterar global→scene-koord och anropar addBlock — Task 3 step 6.
- [x] Bygg-läget oförändrat — bekräftat genom att inga ändringar i BuildView.

---

## Rollback

Tre commits + en docs-commit. För att rulla tillbaka allt: `git reset --hard HEAD~3`.
