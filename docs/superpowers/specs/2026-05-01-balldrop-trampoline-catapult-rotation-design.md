# BallDrop — studsmatta, katapult och rotationshandtag

**Datum:** 2026-05-01
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop` (Swift Package, macOS 14+, SpriteKit + SwiftUI)

## Mål

1. Lägga till två nya blocktyper: **studsmatta** (mjuk extra-studs) och **katapult** (kraftig impuls vinkelrätt mot ytan).
2. Lägga till **rotationshandtag** på varje block — en synlig liten markör som man drar i för att rotera blocket. Ersätter behovet av scroll-hjul (som behålls som alternativ för fin justering).

## Funktionella krav

### Blocktyp 1: studsmatta (`trampoline`)

- Form & storlek: rektangel ~100×12 (samma som befintlig `horizontalRect`).
- Visuellt: grön fyllning, vit kant. Liten zigzag-linje (`SKShapeNode` child) ovanpå för att signalera "studsmatta".
- Fysik: `restitution = 1.4` (vanliga block har 0.5, normal yta 1.0). Bollen studsar tillbaka snabbare än den kom in.
- Hanteras helt av SpriteKits standardkollision — ingen kontaktdetektering nödvändig.

### Blocktyp 2: katapult (`catapult`)

- Form & storlek: rektangel ~100×12.
- Visuellt: orange fyllning, vit kant. Vit pil-ikon (uppåt-pekande triangel) ovanpå som visar vinkelrätt-riktningen — pilen följer blockets rotation.
- Fysik: vanlig restitution (0.5). Den kraftiga impulsen kommer från en kontakt-callback istället.
- Kontaktdetektering:
  - Ny `PhysicsCategory.catapult: UInt32 = 1 << 2`.
  - I `BlockNode`-init för `.catapult`: `physicsBody.categoryBitMask = .catapult`, `contactTestBitMask = .ball`. `collisionBitMask` default (bollen studsar fysiskt mot ytan innan impulsen).
  - I `spawnBall()`: bollen får `contactTestBitMask = .scoreZone | .catapult`.
  - I `GameScene.didBegin(_:)`: ny gren för ball↔catapult:
    1. Beräkna riktningsvektor från katapultens `zRotation`: `dir = (-sin(zRotation), cos(zRotation))` — det är y-axeln roterad, dvs "upp" i blockets eget koordinatsystem.
    2. Applicera impuls: `ball.physicsBody?.applyImpulse(CGVector(dx: dir.dx * impulse, dy: dir.dy * impulse))` med `impulse: CGFloat = 1.2`.
    3. Visuell flash på katapulten: `SKAction.sequence([scale(to: 1.15, duration: 0.08), scale(to: 1.0, duration: 0.08)])`.
    4. Inget bollborttagande, ingen score-ändring.
- Edge case: flera bollar i samma physics step — varje får sin egen impuls oberoende, ingen claim-guard behövs (katapulten återanvänds).

### Rotationshandtag på alla blocktyper

- Varje `BlockNode` (alla 7 typer inklusive de två nya) får två child-nodes vid init:
  - En tunn linje (`SKShapeNode`-path från blockets origo till handtagets position) — visualiserar rotationsaxeln.
  - En liten cirkel (radie 6, ljusblå halv-genomskinlig fyllning, vit kant). `name = "rotateHandle"`.
- Handtagets lokala position: `(handleOffset.x, handleOffset.y)` där:
  - För `horizontalRect`, `trampoline`, `catapult`, `diagonal`: `(blockHalfWidth + 12, 0)` — ut till höger.
  - För `verticalRect`: `(0, blockHalfHeight + 12)` — ut uppåt.
  - För `circle`: `(radius + 12, 0)`.
  - För `triangle`: `(0, size/2 + 12)` — ut uppåt från spetsen.
- Handtaget följer blockets `zRotation` automatiskt eftersom det är ett barn-node.

### Mouse-hantering för rotation

I `GameScene`:

- Ny private property: `private var rotatingNode: SKNode?`, `private var rotateInitialAngle: CGFloat = 0`, `private var rotateInitialZRotation: CGFloat = 0`.
- `mouseDown`: tidigt i metoden (innan blockdrag-grenen), kontrollera om `node.name == "rotateHandle"`. Om ja:
  - `rotatingNode = node.parent`
  - Beräkna `rotateInitialAngle = atan2(mousePos.y - blockCenter.y, mousePos.x - blockCenter.x)`
  - `rotateInitialZRotation = rotatingNode.zRotation`
  - `return` (inte gå vidare till blockdrag)
- `mouseDragged`: om `rotatingNode != nil`:
  - Beräkna ny vinkel: `currentAngle = atan2(mousePos.y - blockCenter.y, mousePos.x - blockCenter.x)`
  - Sätt: `rotatingNode.zRotation = rotateInitialZRotation + (currentAngle - rotateInitialAngle)`
  - `return`
- `mouseUp`: nollställ `rotatingNode = nil`.

Scrollwheel-rotationen i `scrollWheel` lämnas orörd.

### Sidopanel

I `SidebarView`, `ForEach` över `BlockType.allCases`, utöka label-listan från:
```
["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel"]
```
till:
```
["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel", "Studsmatta", "Katapult"]
```

I `blockIcon(_:)`-helper, lägg till `case`-grenar:
- `.trampoline`: grön rundad rektangel 24×6, samma form som `.horizontalRect` men grön fyllning.
- `.catapult`: orange rundad rektangel 24×6 med en liten vit triangel ovanpå som pil.

Hjälptexten längst ned utökas med en rad:
```
Drag blå handtag = rotera
```

## Arkitektur

Följer befintliga mönster:

- **`BlockNode.swift`**: `BlockType` enum får två nya cases. `init(type:)`-switchen får två nya grenar med fysik-setup. En ny privat helper `addRotateHandle(at: CGPoint)` anropas i slutet av init oavsett typ.
- **`GameScene.swift`**: ny gren i `didBegin` för catapult, nya properties + mouse-handling för rotation.
- **`SidebarView.swift`**: utökar label-array och `blockIcon`-switch.
- **Inga nya filer** — ändringarna passar rent i befintliga filer.

## Dataflöde

```
SidebarView "Studsmatta"/"Katapult" knapp → onPlaceBlock(type) → ContentView → gameScene.addBlock → BlockNode init → addRotateHandle
mouse på rotateHandle → mouseDown sparar state → mouseDragged uppdaterar zRotation → mouseUp avslutar
ball physics step → didBegin(catapult) → applyImpulse + flash
```

## Edge cases

- **Studsmatta och katapult kombinerad med rotation**: båda funkar — restitution är riktningsoberoende, katapultens impuls använder zRotation-baserad riktning.
- **Bollen fastnar i katapult-kontakt**: SpriteKit kan trigga didBegin om bollen ligger an mot ytan. Impulsen från första kontakten skickar iväg den, och den fysiska studsen (default collision) ser till att den lämnar ytan. Inget specialfall behövs.
- **Drag på handtag medan blocket roterar redan via scroll**: två rotation-källor — användaren kan kombinera dem, ingen konflikt eftersom de skriver till samma `zRotation`-property.
- **Rotation av cirkel-block**: visuellt meningslöst (cirkeln ser likadan ut), men handtaget visar fortfarande att blocket är interaktivt. Acceptabelt — vi lägger inte till special-case.
- **Bollen träffar handtaget**: handtaget har inget `physicsBody`, så det är osynligt för fysiken. Bara click-target.

## Testning

Manuell verifiering:

1. `swift build` lyckas.
2. Klicka "Studsmatta" → grön rektangel placeras. Bollar studsar tydligt högre på den än på vanliga horisontella block.
3. Klicka "Katapult" → orange rektangel placeras med pil uppåt. Bollar som träffar skjuts iväg uppåt med ett visuellt flash.
4. Rotera katapulten via handtag (drag i cirkel) — pilen följer rotationen, och bollar skjuts nu i den nya riktningen.
5. Rotera vanliga block (horisontell etc) via handtaget — fungerar smidigt utan att flytta blocket.
6. Drag handtaget på en katapult i 90° → bollar skjuts åt höger/vänster.
7. Scroll-hjul-rotation fungerar fortfarande som tidigare.
8. Multipla bollar samtidigt på katapult — alla får impulsen, inget glitchar.

## Out of scope (v1)

- Snäpp till fasta vinklar (15°/45°/90°). Rotation är kontinuerlig.
- Ljudeffekt på katapult/studsmatta.
- Justerbar impulsstyrka via slider — `impulse = 1.2` är hårdkodat.
- Justerbar restitution på studsmatta — hårdkodat 1.4.
- Visuella partiklar vid katapultflash (bara scale-flash).
- Selection-state för block (handtag är alltid synligt).
