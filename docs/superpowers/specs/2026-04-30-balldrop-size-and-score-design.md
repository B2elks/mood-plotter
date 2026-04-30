# BallDrop — bollstorlek och poängzoner

**Datum:** 2026-04-30
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop` (Swift Package, macOS 14+, SpriteKit + SwiftUI)

## Mål

Lägg till två funktioner i BallDrop:

1. Justerbar bollstorlek via slider i sidopanelen.
2. Slumpmässigt placerade poängzoner på spelytans kanter — bollen ger poäng när den träffar en zon, zonen försvinner och en ny dyker upp på ny slumpmässig position.

## Funktionella krav

### Bollstorlek

- Slider i sidopanelen, range **4–30** pixlar (radie), step 1, default **8** (nuvarande hardcoded värde).
- Slidern påverkar endast **nya** bollar som spawnas. Befintliga bollar behåller sin storlek.
- Etikett: "Storlek".
- Slidern placeras i sektionen "KONTROLL" i `SidebarView`, mellan eller bredvid den befintliga "Hastighet"-slidern.

### Poängzoner

- **En zon i taget**, alltid synlig på spelytan.
- Zonen kan dyka upp på **botten**, **vänster** eller **höger** kant — aldrig toppen.
- Slumpmässig position längs den valda kanten med marginal så zonen ryms inom synligt område.
- **Fast storlek**: 80px längs kanten, 12px tjocklek ut från kanten.
- Visuellt: pulserande, färgad (guld-orange) rektangel, liknande pulse-animationen i `SpawnPoint`.
- När en boll träffar zonen:
  1. Poängräknaren ökar med 1.
  2. Bollen tas bort.
  3. Visuell feedback: kort flash/scale-out på bollens position och på zonens position innan den försvinner.
  4. Den gamla zonen tas bort och en ny slumpas på ny position/kant.
- **Ingen ljudeffekt i v1.** Visuell feedback räcker. Ljud kan adderas senare.

### Poängvisning

- **I sidopanelen**: ny sektion "POÄNG" ovanför "KONTROLL", stor siffra (font 24, bold) + knapp "Nollställ poäng".
- **Overlay i spelytan**: stor vit text i övre högra hörnet med poängen, lätt skugga, fast position oavsett spelytans skala.
- **Nollställ-knappen**:
  - Sätter poängen till 0.
  - Tar bort den nuvarande zonen och spawnar en ny.

## Arkitektur

Approachen följer existerande mönster i projektet (`BlockNode`, `SpawnPoint` är egna SKShapeNode-klasser, ContentView kommunicerar med scenen via closure-properties).

### Nya filer

**`BallDrop/ScoreZone.swift`** — egen `SKShapeNode`-klass.

```swift
class ScoreZone: SKShapeNode {
    enum Edge { case bottom, left, right }

    static let zoneLength: CGFloat = 80
    static let zoneThickness: CGFloat = 12

    let edge: Edge

    init(edge: Edge) {
        self.edge = edge
        super.init()
        // Bygg rektangulär path beroende på kant (horisontell vid botten, vertikal på sidor),
        // sätt fillColor (guld-orange), pulse-animation,
        // physicsBody med isDynamic=false, categoryBitMask = scoreZone,
        // contactTestBitMask = ball, collisionBitMask = 0 (så bollar passerar fritt).
        // name = "scoreZone".
    }
}
```

### Ändrade filer

**`BallDrop/GameScene.swift`**:

- Ny property `var ballRadius: CGFloat = 8` (default).
- Ny property `var score: Int = 0` med `didSet { onScoreChanged?(score) }`.
- Ny property `var onScoreChanged: ((Int) -> Void)?` (callback till ContentView).
- Ny property `private var scoreZone: ScoreZone?`.
- Ny enum eller struct `PhysicsCategory` med `ball = 1<<0`, `scoreZone = 1<<1`.
- I `spawnBall()`: använd `ballRadius` istället för hardcoded `8`. Sätt `physicsBody.categoryBitMask = PhysicsCategory.ball` och `contactTestBitMask = PhysicsCategory.scoreZone`.
- Ny metod `spawnScoreZone()` — slumpar `Edge` och position, skapar `ScoreZone`, placerar.
- I `didMove(to:)`: anropa `spawnScoreZone()` för initial zon.
- Ny metod `resetScore()` — sätter `score = 0`, tar bort zonen, anropar `spawnScoreZone()`.
- `didBegin(_ contact:)` — om kollision mellan ball och scoreZone:
  1. Identifiera vilken kropp som är vilken via `categoryBitMask`.
  2. Visuell feedback: scale+fade-out på bollen, flash på zonen (`SKAction`).
  3. Ta bort bollen.
  4. Ta bort zonen.
  5. `score += 1`.
  6. Anropa `spawnScoreZone()`.

**`BallDrop/SidebarView.swift`**:

- Nytt `@Binding var ballRadius: Double`.
- Nytt `@Binding var score: Int`.
- Nytt `var onResetScore: () -> Void`.
- Ny "POÄNG"-sektion ovanför "KONTROLL": stor siffra (font 24, bold) + knapp "Nollställ poäng" som anropar `onResetScore()`.
- Ny "Storlek"-slider i "KONTROLL"-sektionen, range 4...30, step 1.

**`BallDrop/ContentView.swift`**:

- Ny `@State var ballRadius: Double = 8`.
- Ny `@State var score: Int = 0`.
- I scen-setup: `gameScene.onScoreChanged = { score = $0 }`.
- `.onChange(of: ballRadius) { _, new in gameScene.ballRadius = CGFloat(new) }`.
- Skicka `$ballRadius`, `$score`, `onResetScore: { gameScene.resetScore() }` till `SidebarView`.
- Wrap `SpriteView` i `ZStack` med score-overlay i övre högra hörnet (stor vit text + lätt skugga).

## Dataflöde

```
SidebarView (slider)  →  $ballRadius (Binding)  →  ContentView @State  →  onChange  →  gameScene.ballRadius
GameScene.didBegin    →  score += 1 (didSet)    →  onScoreChanged()    →  ContentView @State  →  SidebarView + overlay
SidebarView (knapp)   →  onResetScore()         →  gameScene.resetScore()
```

## Felhantering / edge cases

- **Boll träffar zonen flera gånger**: löses genom att bollen tas bort omedelbart i `didBegin` — ingen risk för dubbla poäng från samma boll/kontakt.
- **Många bollar träffar samtidigt**: varje kontakt hanteras separat av SpriteKits physics-engine, varje boll registrerar sin egen poäng. Den första kontakten tar bort zonen och spawnar en ny — efterföljande samtidiga kontakter kommer inte hitta någon zon att träffa (zonen är borta från scenen). Acceptabelt beteende.
- **Slumpad position går utanför skärmen**: `spawnScoreZone()` använder `scene.size` med margin lika med halv zonlängd för att garantera zonen ryms.
- **Reset under flygande boll**: `resetScore()` rör inte befintliga bollar — endast zonen och poängen. Bollar fortsätter falla mot ny zon.

## Testning

Manuell verifiering på macOS 14+:

1. Bygg: `cd BallDrop && swift run` — appen startar utan kompilatorfel.
2. Storlek-slider: dra slidern, verifiera att nyligen spawnade bollar har ny storlek. Befintliga bollar oförändrade.
3. Zon syns vid start på en av tre kanter (bottom/left/right), pulserande.
4. Boll träffar zon → poäng tickar upp i sidopanel + overlay, bollen försvinner, zon försvinner, ny zon dyker upp.
5. Reset-knapp nollställer poäng och respawnar zon.
6. Ingen krasch när många bollar (>50) är aktiva samtidigt.

## Out of scope (v1)

- Ljudeffekter (kan läggas till senare).
- Olika poängvärden per zon-storlek/typ.
- Flera zoner samtidigt.
- Slumpmässig variation i bollstorlek.
- Highscore-lagring mellan sessioner.
- Toppen som möjlig zon-kant.
