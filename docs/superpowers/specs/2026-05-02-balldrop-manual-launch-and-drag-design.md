# BallDrop — Manuell ball-skjutning + drag-from-sidebar

**Datum:** 2026-05-02
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop`

## Mål

Förbättra spel-läget i två steg:
1. Ersätta auto-spawn med en manuell **"Skjut iväg!"**-knapp så spelaren kan tänka mellan varje boll.
2. Göra block-placeringen **drag-from-sidebar** istället för "tap → spawnas i mitten" — spelaren drar block-ikoner från sidopanelen och släpper dem på spelytan.

Bygg-läget oförändrat (auto-spawn + tap-knappar fortsätter fungera som idag).

## Funktionella krav

### Manuell ball-spawn (level-mode)

- Ny property på `GameScene`: `var manualSpawnMode: Bool = false`. Sätts till `true` i `startLevel(_:)`.
- I `update()`: när `levelConfig != nil && manualSpawnMode == true` — auto-spawn-blocket hoppas över. Fail-detection och ball-cleanup (y < -20) körs som tidigare.
- Ny metod på `GameScene`:
  ```swift
  func launchBall() {
      guard levelConfig != nil, ballsRemaining > 0 else { return }
      spawnBall()
      ballsRemaining -= 1
      onBallsRemainingChanged?(ballsRemaining)
  }
  ```
  Bygg-läget anropar inte denna metod — `manualSpawnMode == false` där.
- I `LevelGameScreen`: ny stor knapp i sidopanelen, placerad mellan SCORE-blocket och BLOCK-listan:
  - Storlek: ~50pt hög, full sidebar-bredd minus padding.
  - Bakgrund: grön (`Color.green`), vit text + ikon.
  - Etikett: `"Skjut iväg! (\(ballsRemaining) kvar)"` med `Image(systemName: "arrow.up.forward.circle.fill")`.
  - Disabled när `ballsRemaining == 0` (grå bakgrund, ingen tap-respons).
  - Tap → `gameScene.launchBall()`.

### Drag-from-sidebar block-placering

I `LevelGameScreen` ändras block-listan från knappar (tap → spawn i mitten) till drag-källor.

**Sidopanel-layout per block-typ:**
```
[ikon] Horisontell        3
[ikon] Vertikal           2
[ikon] Studsmatta         0  (gråad)
```
- Ikon: befintlig `blockIcon(_:)`-helper från `SidebarView`. För att undvika dubblettkod flyttar vi `blockIcon` + `Triangle: Shape` till en ny fil `BallDrop/BallDrop/BlockIcon.swift` så både `SidebarView` och `LevelGameScreen` kan använda den.
- Räknaren till höger: `(blocksRemaining[type] ?? 0)` i blå när > 0, grå när = 0.
- Hela raden är drag-källa när `count > 0`. När `count == 0`: drag-gesture inaktiv, opacity 0.4.

**Drag-mekanik:**
- En `@State var dragState: DragState?` på LevelGameScreen:
  ```swift
  struct DragState {
      let type: BlockType
      var globalLocation: CGPoint
  }
  ```
- Varje block-rad applicerar:
  ```swift
  .gesture(
      DragGesture(coordinateSpace: .global)
          .onChanged { value in
              dragState = DragState(type: type, globalLocation: value.location)
          }
          .onEnded { value in
              handleDrop(at: value.location, type: type)
              dragState = nil
          }
  )
  ```
- Ghost-preview: ovanpå hela `LevelGameScreen` (i `.overlay { ... }`), om `dragState != nil`, visa en `blockIcon(dragState.type)` skalad till ~60×60pt med `opacity(0.7)` och positionerad via `.position(x: dragState.globalLocation.x, y: dragState.globalLocation.y)`. Använd `allowsHitTesting(false)` så ghost inte blockerar gesten.
- `sceneFrame: CGRect` lagras via `GeometryReader { proxy in ... }` runt SpriteKit-vyn med `.onAppear` och `.onChange(of: proxy.frame(in: .global))`.

**Drop-handling:**
```swift
private func handleDrop(at globalLocation: CGPoint, type: BlockType) {
    guard sceneFrame.contains(globalLocation) else { return }
    guard (blocksRemaining[type] ?? 0) > 0 else { return }
    
    // Convert global → scene coordinates.
    let viewLoc = CGPoint(
        x: globalLocation.x - sceneFrame.origin.x,
        y: globalLocation.y - sceneFrame.origin.y
    )
    let sceneLoc = gameScene.convertPoint(fromView: viewLoc)
    gameScene.addBlock(type: type, at: sceneLoc)
}
```

`gameScene.addBlock(...)` (befintlig metod) dekrementerar räknaren och anropar `onBlocksRemainingChanged`.

### Bygg-läget oförändrat

- Auto-spawn fortsätter (manualSpawnMode = false som default).
- SidebarView's tap-knappar för block fortsätter fungera (anropar `onPlaceBlock` som spawnar i mitten).
- Ingen drag-gesture i bygg-läget (ut av v1-scope för Del A).

## Arkitektur

### Nya filer

**`BallDrop/BallDrop/BlockIcon.swift`** — extraherar `blockIcon(_:)`-funktionen + `Triangle: Shape` från SidebarView till en delad fil:

```swift
import SwiftUI

@ViewBuilder
func blockIcon(_ type: BlockType) -> some View {
    switch type {
    case .horizontalRect:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 24, height: 6)
    // ... resten av cases (samma kod som SidebarView idag)
    }
}

struct Triangle: Shape {
    func path(in rect: CGRect) -> Path { ... }
}
```

### Modifierade filer

**`BallDrop/BallDrop/GameScene.swift`**:
- Ny `var manualSpawnMode: Bool = false`.
- I `startLevel(_:)`: `manualSpawnMode = true`.
- Ny metod `launchBall()`.
- I `update()`: när `levelConfig != nil && manualSpawnMode`, hoppa över auto-spawn-grenen (fail-detection + ball-cleanup oförändrat).

**`BallDrop/BallDrop/LevelGameScreen.swift`**:
- Lägg till "Skjut iväg!"-knapp.
- Ersätt nuvarande block-listans `Button { ... }` med rader som har drag-gesture.
- Lägg till `dragState` + `sceneFrame` properties.
- Lägg till GeometryReader runt SpriteView/SpriteKitView för att fånga sceneFrame.
- Lägg till ghost-overlay.

**`BallDrop/BallDrop/SidebarView.swift`**:
- Ta bort lokal `blockIcon(_:)` och `Triangle: Shape` (flyttade till BlockIcon.swift). Importera + använd den nya delade.

## Edge cases

- **Drag avbryts utanför scenen**: `handleDrop` returnerar tidigt om `sceneFrame.contains(globalLocation) == false`. Inget block placeras, ingen räknare-dekrement.
- **Drag av block med count = 0**: drag-gesture är inaktiv (eller no-op om vi tillåter visuell drag men droppen returnerar tidigt på `count > 0`-check).
- **"Skjut iväg" tryckt med 0 bollar kvar**: knappen är disabled visuellt; om händelsen ändå kommer (race) returnerar `launchBall` tidigt på `ballsRemaining > 0`-guard.
- **Drag start på iPad utan att fingrarna lyfts**: `onChanged` körs medan dragState uppdateras. Ghost följer fingret. Vid `onEnded` (finger upp) körs drop-logik.
- **Multi-touch under drag**: SwiftUI's DragGesture är single-touch. Andra fingrar ignoreras under aktiv drag.
- **Skärmrotation under drag**: sceneFrame uppdateras via GeometryReader's onChange-modifier, så drag-positionen är konsistent.

## Testning

Manuell verifiering:
1. Mac `swift build` clean. iOS `xcodebuild` clean.
2. Bygg-läge: oförändrat — auto-spawn, tap-knappar för block.
3. Spela-läge → välj en bana:
   - "Skjut iväg!"-knapp synlig, räknare matchar bollar kvar.
   - Tap → en boll spawnas, räknare dekrementeras med 1.
   - Inga bollar spawnas automatiskt.
   - När räknare = 0: knapp gråad, ingen tap-respons.
4. Drag block från sidopanelen:
   - Tryck och håll på en block-rad → ghost-preview följer fingret.
   - Släpp inom spelytan → block placeras där fingret var, räknare dekrementeras.
   - Släpp utanför → ghost försvinner, ingenting placeras.
   - Drag på block med 0 kvar → ingen drag triggas (eller drag triggas men drop blir no-op).
5. Klara en bana → "Bana klarad!"-modal som tidigare.
6. Misslyckas (slut på bollar) → "Försök igen"-modal.
7. iPad: drag fungerar med touch i båda orienteringar.

## Out of scope (v1 av Del A)

- Drag-from-sidebar i bygg-läget (kan läggas till senare).
- Tillbaka-undo av placerade block (spelaren placerar fel → räknaren är borta).
- Visuell highlight av drop-zonen under drag.
- Haptic feedback på drag/drop.
- Anpassad sidebar-bredd (220pt fast som idag).
