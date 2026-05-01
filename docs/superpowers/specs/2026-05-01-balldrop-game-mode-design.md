# BallDrop — Game mode + skill tree

**Datum:** 2026-05-01
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop`
**Plattformar:** macOS 14+, iPadOS 17+

## Mål

Lägga till ett **spel-läge** vid sidan av befintlig **bygg-läge** (sandbox). Spel-läget består av 9 fördefinierade banor i 3 tier (Brons, Silver, Guld). Varje bana ger spelaren ett begränsat antal block och ett begränsat antal bollar; målet är att scora ett visst antal poäng. Banor klaras gradvis och låser upp nästa tier (och därmed nya blocktyper). Progression sparas i `UserDefaults`. Appen får också en hemskärm som väg in.

## Funktionella krav

### Lägen + navigation

Ny rotvy: **HomeScreen** med två stora knappar:
- **Bygg** → öppnar nuvarande sandbox-vy oförändrad (`BuildView`).
- **Spela** → öppnar `LevelSelectScreen`.

Från LevelSelectScreen kan spelaren:
- Tappa på en upplåst bana → laddar `LevelGameScreen` med banans config.
- Tappa "Tillbaka" → hemskärmen.

I LevelGameScreen visar UI bana-info, block-budget kvar, bollar kvar, score, och en "Avbryt"-knapp för att gå tillbaka till LevelSelect.

### Banor

Totalt 9 banor, 3 per tier. Varje bana definieras av:
- `id: String` (stabil unik identifierare för persistens)
- `tier: Tier` (.bronze, .silver, .gold)
- `name: String` (t.ex. "Första bollen")
- `blockBudget: [BlockType: Int]` — vilka blocktyper och hur många av varje
- `ballCount: Int` — totalt antal bollar spelaren har
- `scoreTarget: Int` — hur många träffar på poängzonen krävs för att klara

**Banauppsättning v1** (tweakas under playtest):

| ID | Tier | Namn | Block | Bollar | Mål |
|----|------|------|-------|--------|-----|
| `b1` | Brons | Första bollen | 3× horisontell | 3 | 1p |
| `b2` | Brons | Trappa | 4× horisontell | 5 | 2p |
| `b3` | Brons | Korridor | 2× horisontell, 2× vertikal | 6 | 3p |
| `s1` | Silver | Diagonalen | 2× horisontell, 2× diagonal | 6 | 3p |
| `s2` | Silver | Studsa | 3× diagonal, 2× cirkel | 6 | 3p |
| `s3` | Silver | Triangelpussel | 2× horisontell, 3× triangel, 1× cirkel | 7 | 4p |
| `g1` | Guld | Studsmatta | 2× horisontell, 1× studsmatta | 5 | 3p |
| `g2` | Guld | Katapulten | 2× horisontell, 1× katapult | 5 | 4p |
| `g3` | Guld | Frihandsmästaren | 1× horisontell, 1× studsmatta, 1× katapult, 5× frihandsritning | 8 | 5p |

(Frihandsritning räknas i budget — varje "rita fritt" som spelaren använder dekrementerar.)

### Tier-baserad upplåsning

- **Brons**: alltid upplåst.
- **Silver**: upplåst när alla 3 Brons-banor är klara.
- **Guld**: upplåst när alla 3 Silver-banor är klara.

Inom en tier är alla banor i den tier valbara om tier:n är upplåst (ingen sub-låsning mellan b1/b2/b3 inom Brons).

### Klar/inte-klar status

Per bana sparas bara om den är klar eller inte (`Set<String>` av klarade IDs). Inga stjärnor, ingen high-score, ingen tidsregistrering. (Out of scope för v1.)

### LevelSelect-skärmens layout

- Tre sektioner under varandra: Brons, Silver, Guld.
- Varje sektion visar 3 bana-kort i en horisontell rad (eller VStack på smal layout).
- Varje kort visar:
  - Banans namn.
  - Status-ikon: ☑️ (`checkmark.circle.fill`, grön) om klarad, 🔒 (`lock.fill`, grå) om låst tier, ▶️ (`play.circle.fill`, blå) om tillgänglig och inte klarad.
  - Bana-info: bollar och mål, t.ex. "5 bollar → 2p".
- Låsta banor är inte tappable.

### LevelGameScreen-layout

- HStack: sidopanel (~220pt bred) + spelyta.
- Sidopanel ovanifrån-och-ner:
  - Bana-info: "Brons 1 — Första bollen" (header) + "Mål: 1p" (subhead).
  - "Bollar kvar" — stor siffra som dekrementeras vid spawn.
  - "Score" — stor siffra som ökar vid zon-träff.
  - "BLOCK" — lista över tillgängliga block-typer med antal kvar (`Horisontell: 3`). Tap på en blocktyp placerar ett block i mitten av spelytan (samma som befintlig "addBlock"-knapp), dekrementerar antalet. När antal = 0 är knappen disabled (gråad).
  - "Avbryt"-knapp → tillbaka till LevelSelect.
- Spelyta: samma SpriteKit-vy som i bygg-läge, samma kontroller (drag block, rotation handle, scroll, longpress, etc).
- ScoreZone fungerar precis som i bygg-läge — slumpmässig spawn-position på en av tre kanter, respawnar efter varje träff (`A` från fråga 6).

### Win/Lose-flow

- **Win**: när `score == scoreTarget`, visa modal: "Bana klarad! 🎉" + två knappar: "Nästa bana" (om finns) eller "Tillbaka". Markera banan som klarad i ProgressStore.
- **Lose**: när alla bollar har spawnats OCH inga bollar är aktiva (alla har trillat ut botten eller försvunnit i scoreZone) OCH score < target → visa modal "Försök igen" + "Tillbaka".
- Modal är en SwiftUI overlay (Sheet eller fullscreenCover), inte SpriteKit.

## Arkitektur

### Nya filer

**`BallDrop/BallDrop/Levels.swift`** — datamodell:

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

OBS: g3 nämner "5× frihandsritning" i den informella tabellen, men i kod-modellen tar vi bort frihand från budget-strukturen för v1 — det är onödig komplexitet att räkna penn-användningar. Frihandsritning-knappen är aktiv på Guld-tier oavsett, men antar fri användning. (Specens tabell-text uppdateras nedan i avsnitt "Out of scope" så det blir konsekvent.)

**`BallDrop/BallDrop/ProgressStore.swift`** — UserDefaults-wrapper:

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

**`BallDrop/BallDrop/HomeScreen.swift`** — entry-skärm:

- VStack med BallDrop-titel (stor font), två knappar (Bygg, Spela), kanske en "Återställ progress"-knapp i ett litet hörn.
- Bakgrund: samma sky-blue/mint LinearGradient.

**`BallDrop/BallDrop/LevelSelectScreen.swift`** — bana-grid:

- ScrollView med tre Section per tier.
- Varje Section header: tier-namn + ev. lås-ikon för låsta tiers.
- Banor som LazyVGrid eller HStack med tap-bara cards.

**`BallDrop/BallDrop/LevelGameScreen.swift`** — gameplay-vy:

- HStack: special-sidopanel + SpriteKit-vy.
- Sidopanelen har bana-info, ballsRemaining, score, blockBudget-knappar, avbryt.
- Modal-overlay för win/lose-state via `@State var outcome: Outcome?`.

### Modifierade filer

**`BallDrop/BallDrop/ContentView.swift`** — blir router:

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
                onPlay: { screen = .levelSelect }
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

(Tidigare `ContentView`-innehåll flyttas till `BuildView.swift` — enklare att hantera än att hålla två varianter i samma fil.)

**`BallDrop/BallDrop/BuildView.swift`** (ny — extraheras från nuvarande ContentView):

- Innehåller exakt nuvarande sandbox-logik: SidebarView + SpriteKitView/SpriteView, score overlay, alla onChange-modifierar.
- Ny "Hem"-knapp i sidopanelen (eller i sidans hörn) som anropar `onHome()`.

**`BallDrop/BallDrop/SidebarView.swift`** — utökas marginellt:

- Ny `var onHome: (() -> Void)?` callback (optional). Om satt, visas en "Hem"-knapp överst i sidopanelen.
- (Om vi hellre vill ha en separat sidopanel för bygg-läget — vi behåller en i v1, callback är cleanaste vägen.)

**`BallDrop/BallDrop/GameScene.swift`** — utökas med level-mode:

```swift
struct LevelConfig {
    let blockBudget: [BlockType: Int]
    let ballCount: Int
    let scoreTarget: Int
}

class GameScene: SKScene, SKPhysicsContactDelegate {
    var levelConfig: LevelConfig?
    private var ballsRemaining: Int = 0
    private var blocksRemaining: [BlockType: Int] = [:]

    var onLevelCompleted: (() -> Void)?
    var onLevelFailed: (() -> Void)?
    var onBallsRemainingChanged: ((Int) -> Void)?
    var onBlocksRemainingChanged: (([BlockType: Int]) -> Void)?

    func startLevel(_ config: LevelConfig) {
        levelConfig = config
        ballsRemaining = config.ballCount
        blocksRemaining = config.blockBudget
        score = 0
        clearAllBlocks()
        scoreZone?.removeFromParent()
        scoreZone = nil
        spawnScoreZone()
        onBallsRemainingChanged?(ballsRemaining)
        onBlocksRemainingChanged?(blocksRemaining)
    }
}
```

**Ändrad logik i `update()`** (level-mode):

```swift
override func update(_ currentTime: TimeInterval) {
    guard !isPaused_ else { return }

    if levelConfig != nil {
        if ballsRemaining > 0 && currentTime - lastSpawnTime >= spawnRate {
            spawnBall()
            ballsRemaining -= 1
            onBallsRemainingChanged?(ballsRemaining)
            lastSpawnTime = currentTime
        }
        // Check fail condition
        if ballsRemaining == 0 && children.first(where: { $0.name == "ball" }) == nil && score < (levelConfig?.scoreTarget ?? 0) {
            onLevelFailed?()
            levelConfig = nil  // prevent repeat triggers
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

**Ändrad logik i `addBlock(type:at:)`** (level-mode):

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

**Ändrad logik i `didBegin` scoreZone-grenen**: efter `score += 1`, om `levelConfig != nil` och `score == levelConfig?.scoreTarget`:
```swift
if let cfg = levelConfig, score == cfg.scoreTarget {
    onLevelCompleted?()
    levelConfig = nil
}
```

I bygg-läge (`levelConfig == nil`): allt fungerar som idag (ingen budget, ingen ball-cap, ingen win/lose-trigger).

## Edge cases

- **Användaren går till hemskärm mitt i en level**: avbryt-knappen anropar callback, scenen avallokeras med Swift's automatic memory management. Ingen state att städa.
- **Avbruten level räknas inte som klar**: `markCompleted` anropas bara via `onLevelCompleted`-callback.
- **Reset progress**: knapp i HomeScreen anropar `progress.reset()`. Återställer allt till Brons-tier.
- **Spelaren placerar block, klarar mål, och har bollar kvar**: spelet visar win-modal omedelbart, ytterligare ball-spawning stoppas genom `levelConfig = nil`.
- **Fail-detection race**: `update()` körs varje frame; villkoret `ballsRemaining == 0 && no balls in scene` triggar bara när scenen är "tom på bollar". Eftersom score-zon-träff tar bort bollen omedelbart, säkerställs att vi inte triggar fail mitt under en räknande-poäng-träff. (Score-uppdatering går samtidigt eller före.)
- **App-start utan tidigare progression**: `ProgressStore.completedIds` startar tom, bara Brons är tillgänglig.
- **iCloud-sync**: out of scope. Progression är lokal till enheten.

## Testning

Inga unit-tester (project saknar test-target). Manuell verifiering:

1. Mac `swift build` clean. iOS `xcodebuild` clean.
2. App startar i HomeScreen.
3. "Bygg"-knapp → BuildView fungerar precis som idag (alla befintliga features). "Hem"-knapp → tillbaka till HomeScreen.
4. "Spela"-knapp → LevelSelectScreen visar 3 Brons-banor som tillgängliga, Silver+Guld som låsta.
5. Klara Brons 1: starta → placera block → klara mål → win-modal → bana markerad ☑️.
6. Klara alla 3 Brons → Silver tier öppnas.
7. Klara alla 3 Silver → Guld tier öppnas.
8. Misslyckas en bana (slut på bollar utan att nå mål) → fail-modal → "Försök igen" startar om banan.
9. "Avbryt" mitt i en bana → tillbaka till LevelSelect, banan oförändrad i progress.
10. Stäng appen, öppna igen → progression kvar (UserDefaults).
11. "Återställ progress"-knapp på HomeScreen → tillbaka till bara Brons tillgänglig.
12. iPad: alla skärmar fungerar i landskap och porträtt.

## Out of scope (v1)

- Stjärnor / 1-3 stars per bana — bara klar/inte klar.
- Banor med bestämda block-positioner (allt placeras av spelaren).
- Tidsgräns per bana (bara bollantal).
- Frihandsritning som budgeterad resurs — antingen alltid tillåten eller helt deaktiverad per bana. v1: vi inkluderar inte frihandsritning i level-läge alls (för att undvika balansproblem). Bygg-läget oförändrat.
- Per-bana high-score eller best-time.
- iCloud-sync av progression.
- Undo-knapp i level-läge.
- Animerad celebration vid bana-klar.
- Ljud-effekter på win/lose-modal (utöver befintliga kontaktljud).
- Onboarding-tutorial.
- Banor med tre stjärnor eller alternativa win-conditions.
