# BallDrop — Game mode + skill tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lägg till ett spel-läge med 9 banor i 3 tier (Brons/Silver/Guld) plus hemskärm + bana-väljare. Spelaren får begränsade block och bollar per bana och måste scora ett målantal för att klara. Progression sparas i `UserDefaults` och låser upp nästa tier.

**Architecture:** Datamodell (`Level`, `Tier`, `ProgressStore`) + tre nya SwiftUI-skärmar (`HomeScreen`, `LevelSelectScreen`, `LevelGameScreen`). `ContentView` blir router med fyra states (home, build, levelSelect, levelGame). `BuildView` extraheras från nuvarande `ContentView` (behåller exakt nuvarande beteende). `GameScene` får ett valbart `LevelConfig` + callbacks; när satt ändras spawn/budget/win-checks, annars bygg-läge oförändrat.

**Tech Stack:** SwiftUI, SpriteKit, Foundation (UserDefaults), Combine. macOS 14+, iPadOS 17+.

**Spec:** `docs/superpowers/specs/2026-05-01-balldrop-game-mode-design.md`

**Notes om testning:** Inga unit-tester. Verifiering: `swift build` (Mac) + `xcodebuild` (iOS) clean efter varje task, plus manuell verifiering i slutet (Task 8).

---

## File Structure

**Filer att skapa:**
- `BallDrop/BallDrop/Levels.swift` — Level + Tier datamodell + 9 hardcoded banor.
- `BallDrop/BallDrop/ProgressStore.swift` — UserDefaults-wrapper med `ObservableObject`.
- `BallDrop/BallDrop/HomeScreen.swift` — startskärm (titel + två knappar).
- `BallDrop/BallDrop/LevelSelectScreen.swift` — bana-grid grupperad per tier.
- `BallDrop/BallDrop/LevelGameScreen.swift` — gameplay-vy med level-specifik sidopanel.
- `BallDrop/BallDrop/BuildView.swift` — extraherad från nuvarande ContentView (sandbox-vy).

**Filer att modifiera:**
- `BallDrop/BallDrop/GameScene.swift` — `LevelConfig` + callbacks + level-mode i `update`/`addBlock`/scoreZone-grenen.
- `BallDrop/BallDrop/ContentView.swift` — router med Screen-enum och `@StateObject` ProgressStore.
- `BallDrop/BallDrop.xcodeproj/...` — regenereras via XcodeGen efter att nya filer lagts till.

---

## Task 1: Datamodell — Levels + ProgressStore

**Files:**
- Create: `BallDrop/BallDrop/Levels.swift`
- Create: `BallDrop/BallDrop/ProgressStore.swift`

- [ ] **Step 1: Skapa Levels.swift**

Skapa fil `BallDrop/BallDrop/Levels.swift` med innehåll:

```swift
import SwiftUI

enum Tier: String, Codable, CaseIterable, Identifiable {
    case bronze, silver, gold

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .bronze: return "Brons"
        case .silver: return "Silver"
        case .gold:   return "Guld"
        }
    }
}

struct Level: Identifiable, Hashable {
    let id: String
    let tier: Tier
    let name: String
    let blockBudget: [BlockType: Int]
    let ballCount: Int
    let scoreTarget: Int
}

extension Level {
    static let all: [Level] = [
        Level(id: "b1", tier: .bronze, name: "Första bollen",
              blockBudget: [.horizontalRect: 3],
              ballCount: 3, scoreTarget: 1),
        Level(id: "b2", tier: .bronze, name: "Trappa",
              blockBudget: [.horizontalRect: 4],
              ballCount: 5, scoreTarget: 2),
        Level(id: "b3", tier: .bronze, name: "Korridor",
              blockBudget: [.horizontalRect: 2, .verticalRect: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s1", tier: .silver, name: "Diagonalen",
              blockBudget: [.horizontalRect: 2, .diagonal: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s2", tier: .silver, name: "Studsa",
              blockBudget: [.diagonal: 3, .circle: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s3", tier: .silver, name: "Triangelpussel",
              blockBudget: [.horizontalRect: 2, .triangle: 3, .circle: 1],
              ballCount: 7, scoreTarget: 4),
        Level(id: "g1", tier: .gold, name: "Studsmatta",
              blockBudget: [.horizontalRect: 2, .trampoline: 1],
              ballCount: 5, scoreTarget: 3),
        Level(id: "g2", tier: .gold, name: "Katapulten",
              blockBudget: [.horizontalRect: 2, .catapult: 1],
              ballCount: 5, scoreTarget: 4),
        Level(id: "g3", tier: .gold, name: "Frihandsmästaren",
              blockBudget: [.horizontalRect: 1, .trampoline: 1, .catapult: 1],
              ballCount: 8, scoreTarget: 5),
    ]

    static func levels(in tier: Tier) -> [Level] {
        all.filter { $0.tier == tier }
    }
}
```

- [ ] **Step 2: Skapa ProgressStore.swift**

Skapa fil `BallDrop/BallDrop/ProgressStore.swift` med innehåll:

```swift
import Foundation
import Combine

final class ProgressStore: ObservableObject {
    @Published private(set) var completedIds: Set<String>

    private let key = "BallDrop.completedLevels.v1"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let stored = defaults.array(forKey: key) as? [String] {
            self.completedIds = Set(stored)
        } else {
            self.completedIds = []
        }
    }

    func markCompleted(_ id: String) {
        completedIds.insert(id)
        defaults.set(Array(completedIds), forKey: key)
    }

    func reset() {
        completedIds = []
        defaults.removeObject(forKey: key)
    }

    func isCompleted(_ id: String) -> Bool {
        completedIds.contains(id)
    }

    func isUnlocked(tier: Tier) -> Bool {
        switch tier {
        case .bronze:
            return true
        case .silver:
            return Level.levels(in: .bronze).allSatisfy { isCompleted($0.id) }
        case .gold:
            return Level.levels(in: .silver).allSatisfy { isCompleted($0.id) }
        }
    }
}
```

- [ ] **Step 3: Regenerera Xcode-projektet**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodegen generate 2>&1 | tail -3
```

Förväntat: `Created project at .../BallDrop.xcodeproj`.

- [ ] **Step 4: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -3
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
git add BallDrop/BallDrop/Levels.swift BallDrop/BallDrop/ProgressStore.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add Level + ProgressStore data models for game mode"
```

---

## Task 2: GameScene level-mode hooks

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till LevelConfig + property + callbacks i GameScene**

I `BallDrop/BallDrop/GameScene.swift`, lägg till en struct ovanför `class GameScene`-deklarationen (efter `enum PhysicsCategory`):

```swift
struct LevelConfig {
    let blockBudget: [BlockType: Int]
    let ballCount: Int
    let scoreTarget: Int
}
```

Lägg till nya properties i `class GameScene`, intill övriga (bra plats: efter `let soundManager = SoundManager()`):

```swift
    var levelConfig: LevelConfig?
    private var ballsRemaining: Int = 0
    private var blocksRemaining: [BlockType: Int] = [:]

    var onLevelCompleted: (() -> Void)?
    var onLevelFailed: (() -> Void)?
    var onBallsRemainingChanged: ((Int) -> Void)?
    var onBlocksRemainingChanged: (([BlockType: Int]) -> Void)?
```

- [ ] **Step 2: Lägg till startLevel-metod**

I `class GameScene`, lägg till en ny metod (bra plats: efter `resetScore()`):

```swift
    func startLevel(_ config: LevelConfig) {
        levelConfig = config
        ballsRemaining = config.ballCount
        blocksRemaining = config.blockBudget
        score = 0
        clearAllBlocks()
        children.filter { $0.name == "ball" }.forEach { $0.removeFromParent() }
        scoreZone?.removeFromParent()
        scoreZone = nil
        spawnScoreZone()
        onBallsRemainingChanged?(ballsRemaining)
        onBlocksRemainingChanged?(blocksRemaining)
    }
```

- [ ] **Step 3: Modifiera update() för level-mode**

Hitta nuvarande `override func update(_ currentTime: TimeInterval)` i `BallDrop/BallDrop/GameScene.swift`:

```swift
    override func update(_ currentTime: TimeInterval) {
        guard !isPaused_ else { return }

        if currentTime - lastSpawnTime >= spawnRate {
            spawnBall()
            lastSpawnTime = currentTime
        }

        for node in children where node.name == "ball" {
            if node.position.y < -20 {
                node.removeFromParent()
            }
        }
    }
```

Ersätt med:

```swift
    override func update(_ currentTime: TimeInterval) {
        guard !isPaused_ else { return }

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
            if currentTime - lastSpawnTime >= spawnRate {
                spawnBall()
                lastSpawnTime = currentTime
            }
        }

        for node in children where node.name == "ball" {
            if node.position.y < -20 {
                node.removeFromParent()
            }
        }
    }
```

- [ ] **Step 4: Modifiera addBlock() för level-mode**

Hitta:

```swift
    func addBlock(type: BlockType, at position: CGPoint) {
        let block = BlockNode(type: type)
        block.position = position
        addChild(block)
    }
```

Ersätt med:

```swift
    @discardableResult
    func addBlock(type: BlockType, at position: CGPoint) -> Bool {
        if levelConfig != nil {
            guard let count = blocksRemaining[type], count > 0 else {
                return false
            }
            blocksRemaining[type] = count - 1
            onBlocksRemainingChanged?(blocksRemaining)
        }
        let block = BlockNode(type: type)
        block.position = position
        addChild(block)
        return true
    }
```

- [ ] **Step 5: Lägg till win-check i scoreZone-grenen**

I `didBegin(_:)`, hitta scoreZone-grenens slut:

```swift
        soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .scoreZone)
        score += 1
        spawnScoreZone()
    }
```

Ersätt med:

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

- [ ] **Step 6: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 7: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 8: Commit**

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: add level-mode support to GameScene with budget + win/fail callbacks"
```

---

## Task 3: Extrahera BuildView från ContentView

**Files:**
- Create: `BallDrop/BallDrop/BuildView.swift`
- Modify: `BallDrop/BallDrop/ContentView.swift`

Detta är ren refactor — flytta nuvarande ContentView-innehåll till BuildView, gör ContentView till en passthrough. Inget beteende ändras.

- [ ] **Step 1: Skapa BuildView.swift med nuvarande ContentView-logik**

Skapa fil `BallDrop/BallDrop/BuildView.swift` med innehåll (kopia av nuvarande ContentView, omdöpt till BuildView, plus optional onHome-callback):

```swift
import SwiftUI
import SpriteKit

struct BuildView: View {
    var onHome: (() -> Void)? = nil

    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.5
    @State private var ballRadius: Double = 8
    @State private var isPaused: Bool = false
    @State private var score: Int = 0
    @State private var isMuted: Bool = false
    @State private var gameScene: GameScene = {
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        return scene
    }()

    var body: some View {
        HStack(spacing: 0) {
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
                },
                onHome: onHome
            )

            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
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
                #else
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
                #endif

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
        }
        .onChange(of: spawnRate) { _, newValue in
            gameScene.spawnRate = newValue
        }
        .onChange(of: isPaused) { _, newValue in
            gameScene.isPaused_ = newValue
        }
        .onChange(of: selectedTool) { _, newValue in
            gameScene.drawMode = newValue == "draw"
        }
        .onChange(of: ballRadius) { _, newValue in
            gameScene.ballRadius = CGFloat(newValue)
        }
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
        .onAppear {
            gameScene.onScoreChanged = { newScore in
                Task { @MainActor in
                    score = newScore
                }
            }
        }
    }
}
```

(Notera tillägget av `onHome: onHome` i SidebarView-anropet — vi förbereder för Task 7.)

- [ ] **Step 2: Lägg till onHome-binding i SidebarView**

I `BallDrop/BallDrop/SidebarView.swift`, ändra struct-deklarationen från:

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
    var onHome: (() -> Void)? = nil
```

(Default `nil` så befintliga anropare inte bryter — vi anropar med callback i BuildView.)

- [ ] **Step 3: Lägg till "Hem"-knapp överst i sidopanelen om onHome är satt**

I `BallDrop/BallDrop/SidebarView.swift`, hitta `body` — den första raden efter VStack-öppningen är:

```swift
            Text("Ball Drop")
                .font(.system(size: 18, weight: .bold))
                .padding(.horizontal)
                .padding(.top, 16)
```

Direkt FÖRE `Text("Ball Drop")`, lägg till:

```swift
            if let onHome = onHome {
                Button(action: onHome) {
                    Label("Hem", systemImage: "house.fill")
                        .font(.system(size: 13))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 12)
                .padding(.top, 12)
            }
```

(När `onHome == nil` — som idag — ritas inget. Vid Task 7 sätter vi callback från router.)

- [ ] **Step 4: Förenkla ContentView till en passthrough**

I `BallDrop/BallDrop/ContentView.swift`, ersätt hela filinnehållet med:

```swift
import SwiftUI

struct ContentView: View {
    var body: some View {
        BuildView()
    }
}
```

Resten av filen (alla @State, gameScene, body med HStack etc) tas bort — den finns i BuildView nu.

- [ ] **Step 5: Regenerera Xcode-projektet**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 6: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 7: Bygg på iOS**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 8: Commit**

```bash
git add BallDrop/BallDrop/BuildView.swift BallDrop/BallDrop/ContentView.swift BallDrop/BallDrop/SidebarView.swift BallDrop/BallDrop.xcodeproj
git commit -m "refactor: extract BuildView from ContentView; add optional onHome to SidebarView"
```

---

## Task 4: HomeScreen

**Files:**
- Create: `BallDrop/BallDrop/HomeScreen.swift`

- [ ] **Step 1: Skapa HomeScreen.swift**

Skapa fil `BallDrop/BallDrop/HomeScreen.swift`:

```swift
import SwiftUI

struct HomeScreen: View {
    var onBuild: () -> Void
    var onPlay: () -> Void
    var onResetProgress: () -> Void

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.53, green: 0.81, blue: 0.92),
                    Color(red: 0.60, green: 0.85, blue: 0.78)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                Text("BallDrop")
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.3), radius: 6, x: 0, y: 3)

                VStack(spacing: 16) {
                    Button(action: onPlay) {
                        Label("Spela", systemImage: "play.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .frame(width: 220, height: 56)
                            .background(Color.white.opacity(0.85))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)

                    Button(action: onBuild) {
                        Label("Bygg", systemImage: "hammer.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .frame(width: 220, height: 56)
                            .background(Color.white.opacity(0.85))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)
                }

                Spacer()

                Button(action: onResetProgress) {
                    Text("Återställ progress")
                        .font(.system(size: 12))
                        .foregroundColor(.white.opacity(0.7))
                }
                .buttonStyle(.plain)
                .padding(.bottom, 24)
            }
        }
    }
}
```

- [ ] **Step 2: Regenerera Xcode-projektet**

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 3: Bygg på Mac**

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 4: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 5: Commit**

```bash
git add BallDrop/BallDrop/HomeScreen.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add HomeScreen with Build/Play buttons"
```

---

## Task 5: LevelSelectScreen

**Files:**
- Create: `BallDrop/BallDrop/LevelSelectScreen.swift`

- [ ] **Step 1: Skapa LevelSelectScreen.swift**

Skapa fil `BallDrop/BallDrop/LevelSelectScreen.swift`:

```swift
import SwiftUI

struct LevelSelectScreen: View {
    @ObservedObject var progress: ProgressStore
    var onSelect: (Level) -> Void
    var onHome: () -> Void

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.53, green: 0.81, blue: 0.92),
                    Color(red: 0.60, green: 0.85, blue: 0.78)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Button(action: onHome) {
                        Label("Hem", systemImage: "chevron.left")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white)
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Text("Spela")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(.white)

                    Spacer()

                    Color.clear.frame(width: 60)
                }
                .padding()

                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        ForEach(Tier.allCases) { tier in
                            tierSection(tier)
                        }
                    }
                    .padding()
                }
            }
        }
    }

    @ViewBuilder
    private func tierSection(_ tier: Tier) -> some View {
        let unlocked = progress.isUnlocked(tier: tier)
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(tier.displayName)
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(.white)
                if !unlocked {
                    Image(systemName: "lock.fill")
                        .foregroundColor(.white.opacity(0.7))
                }
            }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 200), spacing: 12)], spacing: 12) {
                ForEach(Level.levels(in: tier)) { level in
                    levelCard(level, unlocked: unlocked)
                }
            }
        }
    }

    @ViewBuilder
    private func levelCard(_ level: Level, unlocked: Bool) -> some View {
        let completed = progress.isCompleted(level.id)
        let canTap = unlocked

        Button(action: { if canTap { onSelect(level) } }) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(level.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)
                    Spacer()
                    statusIcon(completed: completed, unlocked: unlocked)
                }
                Text("\(level.ballCount) bollar → \(level.scoreTarget)p")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .background(Color.white.opacity(unlocked ? 0.9 : 0.5))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
        .disabled(!canTap)
    }

    @ViewBuilder
    private func statusIcon(completed: Bool, unlocked: Bool) -> some View {
        if !unlocked {
            Image(systemName: "lock.fill").foregroundColor(.gray)
        } else if completed {
            Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
        } else {
            Image(systemName: "play.circle.fill").foregroundColor(.blue)
        }
    }
}
```

- [ ] **Step 2: Regenerera Xcode-projektet**

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 3: Bygg på Mac**

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 4: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 5: Commit**

```bash
git add BallDrop/BallDrop/LevelSelectScreen.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add LevelSelectScreen with tier-grouped level cards"
```

---

## Task 6: LevelGameScreen

**Files:**
- Create: `BallDrop/BallDrop/LevelGameScreen.swift`

- [ ] **Step 1: Skapa LevelGameScreen.swift**

Skapa fil `BallDrop/BallDrop/LevelGameScreen.swift`:

```swift
import SwiftUI
import SpriteKit

struct LevelGameScreen: View {
    let level: Level
    @ObservedObject var progress: ProgressStore
    var onCompleted: () -> Void
    var onCancel: () -> Void

    @State private var ballsRemaining: Int
    @State private var blocksRemaining: [BlockType: Int]
    @State private var score: Int = 0
    @State private var outcome: Outcome? = nil
    @State private var isMuted: Bool = false
    @State private var gameScene: GameScene

    enum Outcome {
        case won
        case lost
    }

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

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 220)
                .background(Color(white: 0.95))

            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(gameBackground)
                #else
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(gameBackground)
                #endif

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
        }
        .onAppear {
            gameScene.onScoreChanged = { new in
                Task { @MainActor in score = new }
            }
            gameScene.onBallsRemainingChanged = { remaining in
                Task { @MainActor in ballsRemaining = remaining }
            }
            gameScene.onBlocksRemainingChanged = { remaining in
                Task { @MainActor in blocksRemaining = remaining }
            }
            gameScene.onLevelCompleted = {
                Task { @MainActor in
                    outcome = .won
                    progress.markCompleted(level.id)
                }
            }
            gameScene.onLevelFailed = {
                Task { @MainActor in outcome = .lost }
            }
            gameScene.startLevel(LevelConfig(
                blockBudget: level.blockBudget,
                ballCount: level.ballCount,
                scoreTarget: level.scoreTarget
            ))
        }
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
        .overlay {
            if let outcome = outcome {
                outcomeModal(outcome)
            }
        }
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

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BLOCK")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(orderedBlockTypes, id: \.rawValue) { type in
                    let count = blocksRemaining[type] ?? 0
                    Button(action: { placeBlock(type) }) {
                        HStack {
                            Text(label(for: type))
                                .font(.system(size: 13))
                            Spacer()
                            Text("\(count)")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(count > 0 ? .blue : .secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(Color.gray.opacity(count > 0 ? 0.08 : 0.04))
                        )
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                    .disabled(count == 0)
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

    private var orderedBlockTypes: [BlockType] {
        BlockType.allCases.filter { level.blockBudget[$0] != nil }
    }

    private func label(for type: BlockType) -> String {
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

    private func placeBlock(_ type: BlockType) {
        gameScene.addBlock(type: type,
            at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
    }

    @ViewBuilder
    private func outcomeModal(_ outcome: Outcome) -> some View {
        ZStack {
            Color.black.opacity(0.5).ignoresSafeArea()
            VStack(spacing: 20) {
                Text(outcome == .won ? "Bana klarad!" : "Försök igen")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                Text(outcome == .won ? "🎉" : "😅")
                    .font(.system(size: 56))
                HStack(spacing: 12) {
                    Button(action: { onCancel() }) {
                        Text("Tillbaka")
                            .font(.system(size: 16, weight: .medium))
                            .frame(width: 110, height: 44)
                            .background(Color.gray.opacity(0.2))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)

                    if outcome == .won {
                        Button(action: { onCompleted() }) {
                            Text("Vidare")
                                .font(.system(size: 16, weight: .semibold))
                                .frame(width: 110, height: 44)
                                .background(Color.green)
                                .foregroundColor(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    } else {
                        Button(action: { restartLevel() }) {
                            Text("Försök igen")
                                .font(.system(size: 16, weight: .semibold))
                                .frame(width: 110, height: 44)
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(28)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
    }

    private func restartLevel() {
        outcome = nil
        gameScene.startLevel(LevelConfig(
            blockBudget: level.blockBudget,
            ballCount: level.ballCount,
            scoreTarget: level.scoreTarget
        ))
    }
}
```

- [ ] **Step 2: Regenerera Xcode-projektet**

```bash
xcodegen generate 2>&1 | tail -3
```

- [ ] **Step 3: Bygg på Mac**

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 4: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 5: Commit**

```bash
git add BallDrop/BallDrop/LevelGameScreen.swift BallDrop/BallDrop.xcodeproj
git commit -m "feat: add LevelGameScreen with budget sidebar and win/lose modal"
```

---

## Task 7: ContentView router + wire screens

**Files:**
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Implementera routern**

I `BallDrop/BallDrop/ContentView.swift`, ersätt hela filen med:

```swift
import SwiftUI

enum Screen: Hashable {
    case home
    case build
    case levelSelect
    case levelGame(Level)
}

struct ContentView: View {
    @State private var screen: Screen = .home
    @StateObject private var progress = ProgressStore()

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
                onSelect: { level in screen = .levelGame(level) },
                onHome: { screen = .home }
            )
        case .levelGame(let level):
            LevelGameScreen(
                level: level,
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
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 3: Bygg på iOS**

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -3
```

Förväntat: `** BUILD SUCCEEDED **`.

- [ ] **Step 4: Commit**

```bash
git add BallDrop/BallDrop/ContentView.swift
git commit -m "feat: route between Home, Build, LevelSelect, and LevelGame screens"
```

---

## Task 8: Manuell verifiering

- [ ] **Step 1: Kör Mac-versionen**

```bash
swift run
```

(Kör av användaren — öppnar GUI.)

- [ ] **Step 2: Verifiera HomeScreen**

1. Appen öppnas i HomeScreen med stor "BallDrop"-titel.
2. Två stora knappar: "Spela" + "Bygg".
3. Liten "Återställ progress"-länk längst ner.

- [ ] **Step 3: Verifiera Bygg-läget oförändrat**

1. Tap "Bygg" → tidigare sandbox visas (sidopanel + spelyta + bollar spawnar).
2. "Hem"-knapp överst i sidopanelen.
3. Alla tidigare features fungerar: blockplacering, rotation, mute, slider, kontaktljud.
4. "Hem"-knapp → tillbaka till HomeScreen.

- [ ] **Step 4: Verifiera LevelSelect**

1. Tap "Spela" → LevelSelectScreen.
2. Tre tier-sektioner: Brons (3 banor synliga + tappable), Silver + Guld (3 banor synliga med lås-ikon, ej tappable).
3. Varje bana-kort visar namn + "X bollar → Yp".
4. "Hem" tar dig tillbaka.

- [ ] **Step 5: Verifiera bana-spel**

1. Tap "Brons 1 — Första bollen" → LevelGameScreen.
2. Sidopanelen visar "Brons — Första bollen", "Mål: 1p", "Bollar kvar: 3", "Score: 0", "Block: Horisontell: 3".
3. Tap "Horisontell"-knappen → ett block placeras i mitten av spelytan, räknaren ändras till 2.
4. Bollar börjar spawnas automatiskt, "Bollar kvar" tickar ner.
5. När en boll träffar zonen → score blir 1 → "Bana klarad!" modal visas.
6. Tap "Vidare" → tillbaka till LevelSelect, Brons 1 har nu ☑️.

- [ ] **Step 6: Verifiera fail-flow**

1. Tap "Brons 2" eller liknande svårare bana.
2. Placera inga block, låt bollarna ramla i botten.
3. När bollarna tar slut + alla har trillat ut → "Försök igen"-modal.
4. Tap "Försök igen" → banan startar om från noll (block-räknare återställd).

- [ ] **Step 7: Verifiera tier-upplåsning**

1. Klara alla 3 Brons-banor.
2. Tillbaka till LevelSelect → Silver-tier saknar nu lås-ikon, alla 3 silver-banor är tappable.
3. Klara alla 3 silver → guld låses upp.

- [ ] **Step 8: Verifiera persistens**

1. Stäng appen helt (Cmd+Q på Mac, swipe up på iPad).
2. Öppna igen → bana-status (☑️) bevaras.
3. På HomeScreen → "Återställ progress" → tillbaka i LevelSelect ska bara Brons vara upplåst.

- [ ] **Step 9: Verifiera iOS-versionen**

I Xcode, scheme `BallDrop-iOS`, kör i simulator. Samma checklist som ovan men med touch/pinch/long-press i level-mode.

---

## Verifiering mot specen

- [x] HomeScreen + Bygg/Spela-knappar — Task 4.
- [x] 9 banor i 3 tier med hardcoded budget/balls/target — Task 1.
- [x] Tier-baserad upplåsning (Bronze always, Silver/Gold gated) — Task 1 (ProgressStore).
- [x] Klar/inte-klar status i UserDefaults — Task 1.
- [x] LevelSelectScreen med ☑️/🔒/▶️-ikoner — Task 5.
- [x] LevelGameScreen med ball-räknare, block-budget, target — Task 6.
- [x] Win/Lose-modal — Task 6 (outcomeModal).
- [x] GameScene LevelConfig + callbacks — Task 2.
- [x] BuildView extraherad oförändrad — Task 3.
- [x] ContentView router — Task 7.
- [x] "Hem"-knapp i sidopanel (bygg-läget) — Task 3 step 3.
- [x] Återställ progress-knapp — Task 4.

---

## Rollback om något går fel

Sju feature-commits + en docs-commit. För att rulla tillbaka allt: `git reset --hard HEAD~7` (eller hur många commits som behöver bort). Specen + planen ligger kvar.
