# BallDrop — Level Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bygg in level editor i appen — spelaren skapar layout-baserade banor med fasta block, score-zoner och spawn-punkt; spar i UserDefaults; spelar via existerande LevelGameScreen.

**Architecture:** Ny datamodell `UserLevel` + `UserLevelStore` (JSON i UserDefaults). Ny `LevelEditorScreen` som använder en `GameScene` i editor-mode (ingen ball-spawn, ingen score-räkning, drag-mekanik för block/zoner/spawn). `GameScene` får ny `loadUserLevel(_:)`-metod som rensar scenen och placerar layout. `LevelGameScreen` får alternativ init för `UserLevel`. `LevelSelectScreen` får ny "Mina banor"-sektion med "+"-kort + sparade banor. `ContentView` router får två nya states.

**Tech Stack:** SwiftUI, SpriteKit, Foundation (Codable, UserDefaults).

**Spec:** `docs/superpowers/specs/2026-05-02-balldrop-level-editor-design.md`

**Notes om testning:** Inga unit-tester. Verifiering via `swift build` + `xcodebuild` clean efter varje task + manuell verifiering i slutet.

---

## File Structure

**Filer att skapa:**
- `BallDrop/BallDrop/UserLevels.swift` — `PlacedBlock`, `PlacedZone`, `UserLevel`-structs + `UserLevelStore`-klass.
- `BallDrop/BallDrop/LevelEditorScreen.swift` — editor-vyn.

**Filer att modifiera:**
- `BallDrop/BallDrop/Levels.swift` — gör `BlockType` Codable (om den inte redan är det).
- `BallDrop/BallDrop/ScoreZone.swift` — gör `Edge` Codable.
- `BallDrop/BallDrop/GameScene.swift` — `editorMode` flagga + `loadUserLevel(_:)` + custom-zone-logik i `didBegin`.
- `BallDrop/BallDrop/LevelGameScreen.swift` — alternativ init för `UserLevel` + dynamisk header/budget.
- `BallDrop/BallDrop/LevelSelectScreen.swift` — "Mina banor"-sektion.
- `BallDrop/BallDrop/ContentView.swift` — nya screen-states + `userLevels` store.

---

## Task 1: Datamodell — UserLevel + UserLevelStore + Codable conformance

**Files:**
- Create: `BallDrop/BallDrop/UserLevels.swift`
- Modify: `BallDrop/BallDrop/Levels.swift`
- Modify: `BallDrop/BallDrop/ScoreZone.swift`

- [ ] **Step 1: Gör BlockType Codable**

I `BallDrop/BallDrop/Levels.swift`, kontrollera att `BlockType` har Codable. Den definieras dock i `BlockNode.swift` (eller liknande). Hitta enum-definitionen.

Run från `/Users/b2/Documents/Proj/LLM`:

```bash
grep -n "enum BlockType" BallDrop/BallDrop/*.swift
```

Förväntat: returnerar fil + radnummer för enum BlockType.

Öppna den filen. Ändra:

```swift
enum BlockType: String, CaseIterable {
```

till:

```swift
enum BlockType: String, CaseIterable, Codable, Hashable {
```

(`Hashable` syntheseras automatiskt för String-rawValue-enums men explicit krävs ibland när enum används som dictionary-key-i-codable.)

- [ ] **Step 2: Gör ScoreZone.Edge Codable**

I `BallDrop/BallDrop/ScoreZone.swift`, hitta:

```swift
enum Edge {
    case bottom, left, right
}
```

Ändra till:

```swift
enum Edge: String, Codable, Hashable {
    case bottom, left, right
}
```

- [ ] **Step 3: Skapa UserLevels.swift**

Skapa fil `BallDrop/BallDrop/UserLevels.swift`:

```swift
import Foundation
import Combine
import CoreGraphics

struct PlacedBlock: Codable, Hashable {
    let type: BlockType
    let position: CGPoint
    let zRotation: CGFloat
}

struct PlacedZone: Codable, Hashable {
    let position: CGPoint
    let edge: ScoreZone.Edge
}

struct UserLevel: Identifiable, Codable, Hashable {
    let id: String
    var name: String
    let createdAt: Date
    var placedBlocks: [PlacedBlock]
    var spawnPosition: CGPoint
    var scoreZones: [PlacedZone]
    var extraBudget: [BlockType: Int]
    var ballCount: Int

    static func newDraft() -> UserLevel {
        UserLevel(
            id: UUID().uuidString,
            name: "Min bana",
            createdAt: Date(),
            placedBlocks: [],
            spawnPosition: CGPoint(x: 400, y: 670),
            scoreZones: [],
            extraBudget: [:],
            ballCount: 5
        )
    }
}

final class UserLevelStore: ObservableObject {
    @Published private(set) var levels: [UserLevel] = []

    private let key = "BallDrop.userLevels.v1"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    func save(_ level: UserLevel) {
        if let i = levels.firstIndex(where: { $0.id == level.id }) {
            levels[i] = level
        } else {
            levels.append(level)
        }
        persist()
    }

    func delete(id: String) {
        levels.removeAll { $0.id == id }
        persist()
    }

    private func load() {
        guard let data = defaults.data(forKey: key) else { return }
        if let decoded = try? JSONDecoder().decode([UserLevel].self, from: data) {
            levels = decoded
        }
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(levels) {
            defaults.set(data, forKey: key)
        }
    }
}
```

- [ ] **Step 4: Regenerera Xcode-projektet**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 5: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 6: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 7: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/UserLevels.swift BallDrop/BallDrop/BlockNode.swift BallDrop/BallDrop/ScoreZone.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add UserLevel data model + Codable conformance for editor"
```

(BlockNode.swift med BlockType enum kanske eller kanske inte behöver ändras beroende på var enum-deklarationen ligger — använd den fil git status visar.)

---

## Task 2: GameScene editor-mode + loadUserLevel + custom-zon-logik

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till editor + custom layout properties**

I `BallDrop/BallDrop/GameScene.swift`, hitta property-blocket. Lägg till efter `manualSpawnMode`:

```swift
    var editorMode: Bool = false
    var hasCustomLayout: Bool = false
    private var customScoreZones: [ScoreZone] = []
```

- [ ] **Step 2: Hoppa över ball-spawning i editor-mode**

I `update(_:)`, ändra start på metoden från:

```swift
    override func update(_ currentTime: TimeInterval) {
        guard !isPaused_ else { return }
```

till:

```swift
    override func update(_ currentTime: TimeInterval) {
        guard !isPaused_ else { return }
        if editorMode { return }
```

- [ ] **Step 3: Lägg till loadUserLevel**

I `BallDrop/BallDrop/GameScene.swift`, lägg till en ny metod efter `startLevel(_:)`:

```swift
    func loadUserLevel(_ level: UserLevel) {
        hasCustomLayout = true
        manualSpawnMode = true
        editorMode = false
        levelConfig = LevelConfig(
            blockBudget: level.extraBudget,
            ballCount: level.ballCount,
            scoreTarget: level.scoreZones.count
        )
        ballsRemaining = level.ballCount
        blocksRemaining = level.extraBudget
        score = 0

        clearAllBlocks()
        children.filter { $0.name == "ball" }.forEach { $0.removeFromParent() }
        scoreZone?.removeFromParent()
        scoreZone = nil
        customScoreZones.forEach { $0.removeFromParent() }
        customScoreZones.removeAll()

        spawnPointNode?.position = level.spawnPosition

        for pb in level.placedBlocks {
            let block = BlockNode(type: pb.type)
            block.position = pb.position
            block.zRotation = pb.zRotation
            addChild(block)
        }

        for pz in level.scoreZones {
            let zone = ScoreZone(edge: pz.edge)
            zone.position = pz.position
            customScoreZones.append(zone)
            addChild(zone)
        }

        onBallsRemainingChanged?(ballsRemaining)
        onBlocksRemainingChanged?(blocksRemaining)
    }
```

- [ ] **Step 4: Modifiera spawnScoreZone för custom layout**

Hitta `func spawnScoreZone()`. Lägg till early-return överst:

```swift
    func spawnScoreZone() {
        if hasCustomLayout { return }
        let margin = ScoreZone.zoneLength / 2 + 10
        ...
```

- [ ] **Step 5: Modifiera didBegin scoreZone-grenen för custom zones**

Hitta scoreZone-grenen i didBegin (där `guard let currentZone = scoreZone, zoneNode === currentZone else { return }`). Den måste hantera båda fallen:

Ersätt:

```swift
        guard let ballNode = ballBody?.node, let zoneNode = zoneBody?.node else { return }
        guard let currentZone = scoreZone, zoneNode === currentZone else { return }
        scoreZone = nil
```

med:

```swift
        guard let ballNode = ballBody?.node, let zoneNode = zoneBody?.node else { return }
        if hasCustomLayout {
            guard let zone = zoneNode as? ScoreZone, customScoreZones.contains(where: { $0 === zone }) else { return }
            customScoreZones.removeAll { $0 === zone }
        } else {
            guard let currentZone = scoreZone, zoneNode === currentZone else { return }
            scoreZone = nil
        }
```

Och i samma gren längre ner, hitta:

```swift
        soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .scoreZone)
        score += 1
        if let cfg = levelConfig, score >= cfg.scoreTarget {
            onLevelCompleted?()
            levelConfig = nil
        }
        spawnScoreZone()
    }
```

Ändra till (hoppa över respawn när custom layout):

```swift
        soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .scoreZone)
        score += 1
        if let cfg = levelConfig, score >= cfg.scoreTarget {
            onLevelCompleted?()
            levelConfig = nil
        }
        if !hasCustomLayout {
            spawnScoreZone()
        }
    }
```

- [ ] **Step 6: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 7: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

- [ ] **Step 8: Commit**

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: add editor-mode + loadUserLevel + custom score zone handling"
```

---

## Task 3: LevelEditorScreen

**Files:**
- Create: `BallDrop/BallDrop/LevelEditorScreen.swift`

- [ ] **Step 1: Skapa LevelEditorScreen.swift**

Skapa fil `BallDrop/BallDrop/LevelEditorScreen.swift` med innehåll:

```swift
import SwiftUI
import SpriteKit

struct LevelEditorScreen: View {
    @ObservedObject var userLevels: UserLevelStore
    var onSaved: () -> Void
    var onCancel: () -> Void

    @State private var draft: UserLevel = UserLevel.newDraft()
    @State private var sceneFrame: CGRect = .zero
    @State private var gameScene: GameScene = {
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        scene.editorMode = true
        return scene
    }()

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 250)
                .background(Color(white: 0.95))

            ZStack {
                GeometryReader { proxy in
                    spriteHost(proxy: proxy)
                }
            }
        }
    }

    private var sidebar: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("Skapa bana")
                    .font(.system(size: 18, weight: .bold))
                    .padding(.horizontal)
                    .padding(.top, 16)

                VStack(alignment: .leading, spacing: 6) {
                    Text("NAMN").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
                    TextField("Min bana", text: $draft.name)
                        .textFieldStyle(.roundedBorder)
                }.padding(.horizontal)

                VStack(alignment: .leading, spacing: 6) {
                    Text("BOLLAR").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
                    Stepper("Antal: \(draft.ballCount)", value: $draft.ballCount, in: 1...30)
                        .font(.system(size: 13))
                }.padding(.horizontal)

                Divider()

                Text("DRA UT TILL SCENEN").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary).padding(.horizontal)

                ForEach(BlockType.allCases, id: \.rawValue) { type in
                    editorRow(label: blockLabel(type), iconType: type) { drop in
                        let scenePos = sceneCoord(from: drop)
                        let block = BlockNode(type: type)
                        block.position = scenePos
                        gameScene.addChild(block)
                    }
                }

                editorRowZone()
                editorRowSpawn()

                Divider()

                Text("EXTRA BLOCK ÅT SPELAREN").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary).padding(.horizontal)
                ForEach(BlockType.allCases, id: \.rawValue) { type in
                    HStack {
                        blockIcon(type).frame(width: 22, height: 22)
                        Text(blockLabel(type)).font(.system(size: 12))
                        Spacer()
                        Stepper("\(draft.extraBudget[type] ?? 0)",
                                value: Binding(
                                    get: { draft.extraBudget[type] ?? 0 },
                                    set: { draft.extraBudget[type] = $0 == 0 ? nil : $0 }
                                ),
                                in: 0...20)
                        .labelsHidden()
                    }
                    .padding(.horizontal)
                }

                Spacer(minLength: 8)

                HStack(spacing: 8) {
                    Button(action: onCancel) {
                        Text("Avbryt").font(.system(size: 13)).frame(maxWidth: .infinity).padding(.vertical, 10).background(Color.gray.opacity(0.2)).foregroundColor(.black).clipShape(RoundedRectangle(cornerRadius: 8))
                    }.buttonStyle(.plain)

                    Button(action: saveLevel) {
                        Text("Spara").font(.system(size: 13, weight: .semibold)).frame(maxWidth: .infinity).padding(.vertical, 10).background(canSave ? Color.green : Color.gray.opacity(0.3)).foregroundColor(.white).clipShape(RoundedRectangle(cornerRadius: 8))
                    }.buttonStyle(.plain).disabled(!canSave)
                }.padding(.horizontal).padding(.bottom, 16)
            }
        }
    }

    private var canSave: Bool {
        !draft.name.trimmingCharacters(in: .whitespaces).isEmpty
            && draft.ballCount >= 1
            && currentZoneCount() >= 1
    }

    @ViewBuilder
    private func editorRow(label: String, iconType: BlockType, onDrop: @escaping (CGPoint) -> Void) -> some View {
        HStack(spacing: 10) {
            blockIcon(iconType).frame(width: 28, height: 28)
            Text(label).font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    onDrop(value.location)
                }
        )
    }

    @ViewBuilder
    private func editorRowZone() -> some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 2).fill(Color(red: 1.0, green: 0.75, blue: 0.20)).frame(width: 24, height: 8)
            Text("Score zone").font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    let scenePos = sceneCoord(from: value.location)
                    let edge = nearestEdge(scenePos)
                    let zone = ScoreZone(edge: edge)
                    zone.position = scenePos
                    gameScene.addChild(zone)
                }
        )
    }

    @ViewBuilder
    private func editorRowSpawn() -> some View {
        HStack(spacing: 10) {
            Circle().fill(Color.white).overlay(Circle().stroke(Color.gray, lineWidth: 1)).frame(width: 22, height: 22)
            Text("Spawn-punkt").font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    let scenePos = sceneCoord(from: value.location)
                    gameScene.spawnPointNode?.position = scenePos
                }
        )
    }

    private func nearestEdge(_ p: CGPoint) -> ScoreZone.Edge {
        let s = gameScene.size
        let dBottom = p.y
        let dLeft = p.x
        let dRight = s.width - p.x
        let m = min(dBottom, dLeft, dRight)
        if m == dBottom { return .bottom }
        if m == dLeft { return .left }
        return .right
    }

    private func sceneCoord(from globalLocation: CGPoint) -> CGPoint {
        let viewLoc = CGPoint(
            x: globalLocation.x - sceneFrame.origin.x,
            y: globalLocation.y - sceneFrame.origin.y
        )
        return gameScene.convertPoint(fromView: viewLoc)
    }

    private func currentZoneCount() -> Int {
        gameScene.children.compactMap { $0 as? ScoreZone }.count
    }

    private func saveLevel() {
        var saved = draft
        saved.placedBlocks = gameScene.children.compactMap { node in
            guard let bn = node as? BlockNode else { return nil }
            return PlacedBlock(type: bn.blockType, position: bn.position, zRotation: bn.zRotation)
        }
        saved.scoreZones = gameScene.children.compactMap { node in
            guard let zn = node as? ScoreZone else { return nil }
            return PlacedZone(position: zn.position, edge: zn.edge)
        }
        saved.spawnPosition = gameScene.spawnPointNode?.position ?? draft.spawnPosition
        userLevels.save(saved)
        onSaved()
    }

    @ViewBuilder
    private func spriteHost(proxy: GeometryProxy) -> some View {
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

    private var gameBackground: some View {
        LinearGradient(
            colors: [
                Color(red: 0.53, green: 0.81, blue: 0.92),
                Color(red: 0.60, green: 0.85, blue: 0.78)
            ],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    private func blockLabel(_ type: BlockType) -> String {
        switch type {
        case .horizontalRect: return "Horisontell"
        case .verticalRect:   return "Vertikal"
        case .diagonal:       return "Diagonal"
        case .circle:         return "Cirkel"
        case .triangle:       return "Triangel"
        case .trampoline:     return "Studsmatta"
        case .catapult:       return "Katapult"
        }
    }
}
```

OBS: ScoreZone.swift behöver exponera `edge`-property (kontrollera att `let edge: Edge` redan är tillgänglig — den är publikt accessbar default).

- [ ] **Step 2: Regenerera Xcode-projektet**

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 3: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 4: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

- [ ] **Step 5: Commit**

```bash
git add BallDrop/BallDrop/LevelEditorScreen.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add LevelEditorScreen for layout-based level creation"
```

---

## Task 4: LevelGameScreen — alternativ init för UserLevel

**Files:**
- Modify: `BallDrop/BallDrop/LevelGameScreen.swift`

- [ ] **Step 1: Refaktorera LevelGameScreen att stödja båda level-typer**

I `BallDrop/BallDrop/LevelGameScreen.swift`, ändra struktur. Den befintliga `let level: Level` blir optional och `userLevel: UserLevel?` läggs till. För enkelhet: byt ut hela structens egenskapsdeklaration + init.

Hitta:

```swift
struct LevelGameScreen: View {
    let level: Level
    @ObservedObject var progress: ProgressStore
    var onCompleted: () -> Void
    var onCancel: () -> Void
```

Ersätt med:

```swift
struct LevelGameScreen: View {
    let level: Level?
    let userLevel: UserLevel?
    @ObservedObject var progress: ProgressStore
    var onCompleted: () -> Void
    var onCancel: () -> Void
```

Hitta init-konstruktorn:

```swift
    init(level: Level,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = level
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: level.ballCount)
        self._blocksRemaining = State(initialValue: level.blockBudget)
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        self._gameScene = State(initialValue: scene)
    }
```

Ersätt med två inits:

```swift
    init(level: Level,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = level
        self.userLevel = nil
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: level.ballCount)
        self._blocksRemaining = State(initialValue: level.blockBudget)
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        self._gameScene = State(initialValue: scene)
    }

    init(userLevel: UserLevel,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = nil
        self.userLevel = userLevel
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: userLevel.ballCount)
        self._blocksRemaining = State(initialValue: userLevel.extraBudget)
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        self._gameScene = State(initialValue: scene)
    }
```

- [ ] **Step 2: Uppdatera onAppear-logik**

Hitta i `body`'s `.onAppear` blocket. Lägg till detta efter callbacks-sätten men där `gameScene.startLevel(...)` anropas:

Ersätt:

```swift
            gameScene.startLevel(LevelConfig(
                blockBudget: level.blockBudget,
                ballCount: level.ballCount,
                scoreTarget: level.scoreTarget
            ))
```

med:

```swift
            if let lvl = level {
                gameScene.startLevel(LevelConfig(
                    blockBudget: lvl.blockBudget,
                    ballCount: lvl.ballCount,
                    scoreTarget: lvl.scoreTarget
                ))
            } else if let ul = userLevel {
                gameScene.loadUserLevel(ul)
            }
```

- [ ] **Step 3: Uppdatera levelId-helper för markCompleted**

Hitta:

```swift
            gameScene.onLevelCompleted = {
                Task { @MainActor in
                    outcome = .won
                    progress.markCompleted(level.id)
                }
            }
```

Ersätt med:

```swift
            gameScene.onLevelCompleted = {
                Task { @MainActor in
                    outcome = .won
                    let id = level?.id ?? userLevel?.id ?? ""
                    if !id.isEmpty { progress.markCompleted(id) }
                }
            }
```

- [ ] **Step 4: Uppdatera sidebar-headern + restartLevel**

Hitta i `sidebar`-computed property:

```swift
                Text("\(level.tier.displayName) — \(level.name)")
                    .font(.system(size: 14, weight: .bold))
                Text("Mål: \(level.scoreTarget)p")
```

Ersätt med:

```swift
                Text(headerTitle)
                    .font(.system(size: 14, weight: .bold))
                Text(headerSubtitle)
```

Lägg till två nya computed properties intill `orderedBlockTypes`:

```swift
    private var headerTitle: String {
        if let l = level { return "\(l.tier.displayName) — \(l.name)" }
        if let u = userLevel { return u.name }
        return ""
    }

    private var headerSubtitle: String {
        if let l = level { return "Mål: \(l.scoreTarget)p" }
        if let u = userLevel { return "Mål: \(u.scoreZones.count) zoner" }
        return ""
    }
```

Hitta `orderedBlockTypes`:

```swift
    private var orderedBlockTypes: [BlockType] {
        BlockType.allCases.filter { level.blockBudget[$0] != nil }
    }
```

Ersätt med:

```swift
    private var orderedBlockTypes: [BlockType] {
        let budget = level?.blockBudget ?? userLevel?.extraBudget ?? [:]
        return BlockType.allCases.filter { budget[$0] != nil }
    }
```

Hitta `restartLevel`:

```swift
    private func restartLevel() {
        outcome = nil
        gameScene.startLevel(LevelConfig(
            blockBudget: level.blockBudget,
            ballCount: level.ballCount,
            scoreTarget: level.scoreTarget
        ))
    }
```

Ersätt med:

```swift
    private func restartLevel() {
        outcome = nil
        if let lvl = level {
            gameScene.startLevel(LevelConfig(
                blockBudget: lvl.blockBudget,
                ballCount: lvl.ballCount,
                scoreTarget: lvl.scoreTarget
            ))
        } else if let ul = userLevel {
            gameScene.loadUserLevel(ul)
        }
    }
```

- [ ] **Step 5: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

- [ ] **Step 6: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

- [ ] **Step 7: Commit**

```bash
git add BallDrop/BallDrop/LevelGameScreen.swift
git commit -m "feat: support UserLevel playback in LevelGameScreen"
```

---

## Task 5: LevelSelectScreen — Mina banor-sektion

**Files:**
- Modify: `BallDrop/BallDrop/LevelSelectScreen.swift`

- [ ] **Step 1: Lägg till userLevels + callbacks i signaturen**

I `BallDrop/BallDrop/LevelSelectScreen.swift`, ändra:

```swift
struct LevelSelectScreen: View {
    @ObservedObject var progress: ProgressStore
    var onSelect: (Level) -> Void
    var onHome: () -> Void
```

till:

```swift
struct LevelSelectScreen: View {
    @ObservedObject var progress: ProgressStore
    @ObservedObject var userLevels: UserLevelStore
    var onSelect: (Level) -> Void
    var onSelectUserLevel: (UserLevel) -> Void
    var onCreateLevel: () -> Void
    var onHome: () -> Void

    @State private var pendingDelete: UserLevel? = nil
```

- [ ] **Step 2: Lägg till userLevels-sektion i body**

Hitta i body:

```swift
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        ForEach(Tier.allCases) { tier in
                            tierSection(tier)
                        }
                    }
                    .padding()
                }
```

Ersätt med:

```swift
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        ForEach(Tier.allCases) { tier in
                            tierSection(tier)
                        }
                        userLevelsSection()
                    }
                    .padding()
                }
            .alert(item: $pendingDelete) { lvl in
                Alert(
                    title: Text("Ta bort \"\(lvl.name)\"?"),
                    primaryButton: .destructive(Text("Ta bort")) {
                        userLevels.delete(id: lvl.id)
                    },
                    secondaryButton: .cancel()
                )
            }
```

(Notera: closure-blocket `}` på .alert-modifieraren ersätter motsvarande slutparentes på den outer VStack — anpassa parentes-struktur för Swift-build).

(Praktisk regel: håll `.alert` på samma nivå som `ScrollView` vilket den är när du wrapps `VStack(alignment: .leading, spacing: 0)`-blocket runt header + scrollview. Anpassa tills bygget passar.)

- [ ] **Step 3: Lägg till userLevelsSection helper**

Lägg till en ny @ViewBuilder-metod intill `tierSection`:

```swift
    @ViewBuilder
    private func userLevelsSection() -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Mina banor")
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(.white)

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 200), spacing: 12)], spacing: 12) {
                Button(action: onCreateLevel) {
                    VStack(spacing: 8) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 36))
                            .foregroundColor(.blue)
                        Text("Skapa ny")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.black)
                    }
                    .frame(maxWidth: .infinity, minHeight: 72)
                    .padding(12)
                    .background(Color.white.opacity(0.9))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .buttonStyle(.plain)

                ForEach(userLevels.levels) { ul in
                    userLevelCard(ul)
                }
            }
        }
    }

    @ViewBuilder
    private func userLevelCard(_ level: UserLevel) -> some View {
        let completed = progress.isCompleted(level.id)
        Button(action: { onSelectUserLevel(level) }) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(level.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)
                    Spacer()
                    if completed {
                        Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                    } else {
                        Image(systemName: "play.circle.fill").foregroundColor(.blue)
                    }
                }
                Text("\(level.ballCount) bollar → \(level.scoreZones.count) zoner")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .background(Color.white.opacity(0.9))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
        .onLongPressGesture {
            pendingDelete = level
        }
    }
```

- [ ] **Step 4: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

- [ ] **Step 5: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

- [ ] **Step 6: Commit**

```bash
git add BallDrop/BallDrop/LevelSelectScreen.swift
git commit -m "feat: add Mina banor section to LevelSelectScreen"
```

---

## Task 6: ContentView router — nya states

**Files:**
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Uppdatera Screen-enum + lägg till userLevels store**

Ersätt hela `BallDrop/BallDrop/ContentView.swift` med:

```swift
import SwiftUI

enum Screen: Hashable {
    case home
    case build
    case levelSelect
    case levelGame(Level)
    case levelEditor
    case userLevelGame(UserLevel)
}

struct ContentView: View {
    @State private var screen: Screen = .home
    @StateObject private var progress = ProgressStore()
    @StateObject private var userLevels = UserLevelStore()

    var body: some View {
        switch screen {
        case .home:
            HomeScreen(
                onBuild: { screen = .build },
                onPlay: { screen = .levelSelect },
                onResetProgress: { progress.reset() }
            )
        case .build:
            BuildView(onHome: { screen = .home })
        case .levelSelect:
            LevelSelectScreen(
                progress: progress,
                userLevels: userLevels,
                onSelect: { level in screen = .levelGame(level) },
                onSelectUserLevel: { ul in screen = .userLevelGame(ul) },
                onCreateLevel: { screen = .levelEditor },
                onHome: { screen = .home }
            )
        case .levelGame(let level):
            LevelGameScreen(
                level: level,
                progress: progress,
                onCompleted: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        case .levelEditor:
            LevelEditorScreen(
                userLevels: userLevels,
                onSaved: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        case .userLevelGame(let userLevel):
            LevelGameScreen(
                userLevel: userLevel,
                progress: progress,
                onCompleted: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        }
    }
}
```

- [ ] **Step 2: Bygg på Mac**

```bash
swift build 2>&1 | tail -5
```

- [ ] **Step 3: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add BallDrop/BallDrop/ContentView.swift
git commit -m "feat: route between LevelEditor and userLevel game in ContentView"
```

---

## Task 7: Manuell verifiering

- [ ] **Step 1: Kör appen**

```bash
swift run
```

- [ ] **Step 2: Verifiera Mina banor**

1. HomeScreen → Spela → LevelSelect → ny "Mina banor"-sektion synlig.
2. "+ Skapa ny"-kort öppnar editor.

- [ ] **Step 3: Skapa en bana**

1. I editorn: skriv namn "Test", sätt bollar = 3.
2. Drag in 2 horisontella block + 1 score zone (släpp t.ex. mitten/botten).
3. Drag spawn-punkt till nya position.
4. Sätt extra block: Horisontell = 1.
5. Tap Spara → tillbaka till LevelSelect, banan "Test" syns under Mina banor.

- [ ] **Step 4: Spela banan**

1. Tap på "Test"-kortet → LevelGameScreen öppnas med blocken på plats, score-zonen synlig, spawn på nya plats.
2. Header: "Test", "Mål: 1 zoner".
3. "Skjut iväg!"-knapp visar (3 kvar). Block-budget visar Horisontell: 1.
4. Skjut bollar, träffa zonen → "Bana klarad!"-modal.

- [ ] **Step 5: Verifiera persistens**

1. Stäng appen, öppna igen → banan "Test" finns kvar med ☑️.

- [ ] **Step 6: Ta bort banan**

1. Long-press på banan → konfirmation → "Ta bort" → banan försvinner.

---

## Verifiering mot specen

- [x] Datamodell `UserLevel`, `PlacedBlock`, `PlacedZone` — Task 1.
- [x] UserLevelStore (UserDefaults JSON) — Task 1.
- [x] BlockType + ScoreZone.Edge Codable — Task 1.
- [x] LevelEditorScreen med drag block/zon/spawn + extra-budget + spara/avbryt — Task 3.
- [x] GameScene editor-mode + loadUserLevel + custom-zon-logik — Task 2.
- [x] LevelGameScreen alternativ init för UserLevel — Task 4.
- [x] LevelSelectScreen Mina banor-sektion + create + delete — Task 5.
- [x] ContentView router för editor + userLevel game — Task 6.

---

## Rollback

Sex feature-commits + en docs-commit. För rollback: `git reset --hard HEAD~6`.
