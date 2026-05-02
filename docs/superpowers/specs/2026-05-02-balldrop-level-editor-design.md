# BallDrop — Level Editor

**Datum:** 2026-05-02
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop`

## Mål

Ge spelaren möjlighet att bygga egna banor i appen och spara dem. Sparade banor är layout-baserade — blockens positioner, rotationer, score-zoner och spawn-punktens placering ingår i banan. Spelaren kan därutöver få ett extra block-budget att placera ovanpå editorns layout. Sparade banor visas i en ny "Mina banor"-sektion i LevelSelect och spelas via existerande LevelGameScreen.

## Funktionella krav

### Datamodell

```swift
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
    let id: String              // UUID-string
    var name: String
    let createdAt: Date
    var placedBlocks: [PlacedBlock]
    var spawnPosition: CGPoint
    var scoreZones: [PlacedZone]
    var extraBudget: [BlockType: Int]
    var ballCount: Int
}
```

`BlockType` får `Codable, Hashable` (har redan `String`-rawValue). `ScoreZone.Edge` får `Codable, Hashable`.

### UserLevelStore

`final class UserLevelStore: ObservableObject` — samma mönster som `ProgressStore`:
- `@Published var levels: [UserLevel]` — alla sparade banor.
- `func save(_ level: UserLevel)` — uppsert via id.
- `func delete(id: String)`.
- Persistens: JSON i UserDefaults under nyckeln `BallDrop.userLevels.v1`.

### LevelEditorScreen

Ny SwiftUI-vy, layout = HStack (sidopanel ~250pt + canvas).

**Sidopanelen:**
- Namnfält (TextField, default "Min bana").
- Bollantal (Stepper 1...30, default 5).
- "Extra block till spelaren" — för varje BlockType en Stepper 0...20 (default 0).
- "Block — dra ut" — drag-rader för att placera fasta layout-block (samma drag-mekanik som existerande LevelGameScreen).
- "Score zone — dra ut" — special drag-row som placerar en fast `ScoreZone` på den kant som matchar drop-positionen (närmaste kant: bottom/left/right).
- "Spawn-punkt — dra för att flytta" — visar nuvarande position; tryck-och-dra på denna rad flyttar `spawnPointNode` till drop-positionen.
- Spara-knapp (grön) — validerar namn ej tomt, ballCount ≥ 1, scoreZones ≥ 1. Persisterar via `userLevels.save(...)`. Returnerar till LevelSelect.
- Avbryt-knapp (röd) — returnerar utan att spara. Ingen konfirmation i v1.

**Canvas:**
- En `GameScene`-instans med ny flagga `editorMode: Bool = true`.
- I editor-mode:
  - Ingen ball-spawn (varken auto eller manual).
  - Ingen score-räkning, ingen score-zon-respawn.
  - Drag-from-sidebar fungerar för block, zon och spawn-punkt.
  - Block och zoner som placerats kan flyttas (befintlig drag), roteras (befintliga handtag), tas bort (högerklick / long-press).
  - Spawn-punkten är dragbar (befintligt beteende).
- Vid save: gå igenom `scene.children`, samla alla `BlockNode` → PlacedBlock, alla `ScoreZone` → PlacedZone, läs `spawnPointNode.position` → spawnPosition.

### Spel-läge för user-banor (LevelGameScreen utökas)

Lägg till alternativ init på `LevelGameScreen`:

```swift
init(userLevel: UserLevel,
     progress: ProgressStore,
     onCompleted: @escaping () -> Void,
     onCancel: @escaping () -> Void)
```

Den interna staten ändras:
- `level: Level?` (existing, sätts till nil för user-banor).
- `userLevel: UserLevel?` (ny, sätts till värde för user-banor).
- I onAppear:
  - För hardcoded level: `gameScene.startLevel(LevelConfig(...))` som idag.
  - För user-level: `gameScene.loadUserLevel(userLevel)` (ny metod).
- Header och budget-sektion visar antingen tier+namn+target eller userLevel-namn+"Mål: \(scoreZones.count) zoner".

### GameScene utökningar

- Ny `var hasCustomLayout: Bool = false` (false = befintligt random-zon-beteende).
- Ny array `private var customScoreZones: [ScoreZone] = []`.
- Ny metod:
  ```swift
  func loadUserLevel(_ level: UserLevel) {
      hasCustomLayout = true
      manualSpawnMode = true
      levelConfig = LevelConfig(
          blockBudget: level.extraBudget,
          ballCount: level.ballCount,
          scoreTarget: level.scoreZones.count
      )
      ballsRemaining = level.ballCount
      blocksRemaining = level.extraBudget
      score = 0
      // Clear scene
      clearAllBlocks()
      children.filter { $0.name == "ball" }.forEach { $0.removeFromParent() }
      scoreZone?.removeFromParent()
      scoreZone = nil
      customScoreZones.forEach { $0.removeFromParent() }
      customScoreZones.removeAll()
      // Place spawn
      spawnPointNode?.position = level.spawnPosition
      // Place blocks
      for pb in level.placedBlocks {
          let block = BlockNode(type: pb.type)
          block.position = pb.position
          block.zRotation = pb.zRotation
          addChild(block)
      }
      // Place fixed zones
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
- I `didBegin` scoreZone-grenen: när `hasCustomLayout`, ta bort den specifika zonen från scenen och från `customScoreZones`-arrayen, increment score, men kalla INTE `spawnScoreZone()`. Win-check fungerar oförändrat (score >= scoreTarget).
- I `spawnScoreZone()`: tidig return om `hasCustomLayout` (vi placerar inga slumpzoner i custom layout).

### LevelSelectScreen integration

Lägg till "Mina banor"-sektion efter Guld:

```swift
ForEach(Tier.allCases) { tierSection($0) }
userLevelsSection()
```

`userLevelsSection`:
- Header "Mina banor".
- Grid: första kortet är "+ Skapa ny" (visuellt avvikande, blå+plus). Tap → openEditor callback.
- Resten = sparade banor (samma kort-stil som hardcoded levels). Tap → onSelectUserLevel callback. Long-press → konfirmationsdialog för delete.
- Status-ikon: ☑️ om `progress.isCompleted(level.id)`.

### ContentView router

Två nya screen-states:
```swift
case levelEditor
case userLevelGame(UserLevel)
```

Ny `@StateObject var userLevels = UserLevelStore()`. Skickas som binding/observed till LevelSelectScreen och LevelEditorScreen.

### Win/Lose för user-banor

Samma flow som hardcoded levels — `gameScene.onLevelCompleted/onLevelFailed` triggar modal. När wonner: `progress.markCompleted(userLevel.id)` (UUID-baserad). Tier-upplåsning oförändrad (user-banor påverkar inte Brons/Silver/Guld-progression).

## Edge cases

- **Tom layout**: editor tillåter inte save om `scoreZones.empty` eller `ballCount == 0`. Spara-knapp disabled.
- **Block utanför scenen**: editor klampar inte — om användaren placerar blocket utanför syns det inte men scenen accepterar det. v1 acceptabelt.
- **Många bollar + zoner**: ingen explicit gräns. ballCount-stepper 1...30 ger naturlig övre gräns.
- **Delete kort som är öppet**: kan inte hända — du kan bara delete från LevelSelect, inte i editor.
- **Edit befintlig**: out of scope för v1. Bara create + delete.
- **Migrering om data-strukturen ändras**: v1 nyckel `BallDrop.userLevels.v1`. Senare versioner får v2-nyckel + migration.
- **iCloud/sync**: out of scope för v1.

## Testning

Manuell verifiering:

1. Mac `swift build` clean. iOS `xcodebuild` clean.
2. HomeScreen → Spela → LevelSelect: ny "Mina banor"-sektion synlig med "+"-kort.
3. Tap "+" → LevelEditorScreen öppnas.
4. Skriv namn, sätt bollantal till 3, sätt extra block budget Horisontell=2.
5. Drag in 2 horisontella block + 1 score zone i scenen.
6. Tap Spara → tillbaka till LevelSelect, ny bana synlig under Mina banor.
7. Tap på sparad bana → LevelGameScreen öppnas med blocken på plats, score-zonen synlig, "Skjut iväg"-knappen visar "(3 kvar)".
8. Skjut bollar, träffa zonen → score 1/1, modal "Bana klarad!".
9. Tillbaka, banan markerad som ☑️.
10. Long-press på banan → "Ta bort denna bana?" → "Ja" → banan försvinner.
11. Stäng/öppna app → sparade banor kvar.

## Out of scope (v1)

- Edit av sparad bana — bara create + delete.
- Test-knapp i editorn — användaren sparar och spelar via LevelSelect.
- Validering att bana är lösbar.
- iCloud-sync.
- Dela banor mellan enheter (export/import via QR/JSON).
- Stjärn-rating per bana (klar/inte klar bara).
- Editor-mode tutorial.
- Multipla spawn-punkter.
- Animerade/rörliga block.
