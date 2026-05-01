# BallDrop — studsmatta, katapult och rotationshandtag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lägg till två nya blocktyper — studsmatta (mjuk extra-studs via hög `restitution`) och katapult (kraftig impuls vinkelrätt mot ytan via kontakt-callback) — samt ett synligt rotationshandtag på alla block för att möjliggöra rotation utan scroll-hjul.

**Architecture:** Blocktyperna är nya cases på existerande `BlockType`-enum. Studsmattan hanteras helt av SpriteKits standardkollision (ingen kontaktdetektering behövs). Katapulten använder en ny `PhysicsCategory.catapult` och en gren i existerande `didBegin(_:)` för att applicera impulsen. Rotationshandtaget är ett barn-node på varje `BlockNode` (en cirkel + linje från center) — `GameScene` upptäcker drag på handtaget i `mouseDown/Dragged/Up` och uppdaterar blockets `zRotation`.

**Tech Stack:** Swift 5.9, SpriteKit, SwiftUI, macOS 14+, Swift Package Manager (`swift build`).

**Spec:** `docs/superpowers/specs/2026-05-01-balldrop-trampoline-catapult-rotation-design.md`

**Notes om testning:** Inget XCTest-target i projektet — verifiering sker via `swift build` (måste lyckas) + manuell visuell kontroll. Kör aldrig `swift run` från en subagent (öppnar GUI och blockerar).

---

## File Structure

**Filer att modifiera:**

- `BallDrop/BallDrop/BlockNode.swift` — utöka `BlockType`-enum med `.trampoline` och `.catapult`, lägg till case-grenar i init med rätt fysik och färg, lägg till rotationshandtags-child på alla blocktyper.
- `BallDrop/BallDrop/GameScene.swift` — `PhysicsCategory.catapult`, utöka bollens `contactTestBitMask`, ny gren i `didBegin(_:)` för katapult, properties för rotation-state, mouse-handling i `mouseDown`/`mouseDragged`/`mouseUp`.
- `BallDrop/BallDrop/SidebarView.swift` — utöka labels-array i `ForEach`-loopen, lägg till case-grenar i `blockIcon(_:)`-helper, utöka hjälptexten med rotation-instruktion.

**Inga nya filer.**

---

## Task 1: Studsmatta (trampoline)

**Files:**
- Modify: `BallDrop/BallDrop/BlockNode.swift`
- Modify: `BallDrop/BallDrop/SidebarView.swift`

- [ ] **Step 1: Lägg till .trampoline case i BlockType**

I `BallDrop/BallDrop/BlockNode.swift`, ändra enum från:

```swift
enum BlockType: String, CaseIterable {
    case horizontalRect
    case verticalRect
    case diagonal
    case circle
    case triangle
}
```

till:

```swift
enum BlockType: String, CaseIterable {
    case horizontalRect
    case verticalRect
    case diagonal
    case circle
    case triangle
    case trampoline
}
```

- [ ] **Step 2: Lägg till .trampoline-gren i BlockNode init switch**

I `BlockNode.init(type:)`, i den befintliga `switch type`-blocket, lägg till en ny case-gren EFTER `.triangle`-grenen och INNAN den stängande `}`:

```swift
        case .trampoline:
            let size = CGSize(width: 100, height: 12)
            path = CGPath(roundedRect: CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2),
                                               size: size),
                          cornerWidth: 4, cornerHeight: 4, transform: nil)
            physicsBody = SKPhysicsBody(rectangleOf: size)
            fillColor = NSColor(red: 0.40, green: 0.78, blue: 0.45, alpha: 1)

            let zigzag = SKShapeNode()
            let zPath = CGMutablePath()
            let segmentWidth: CGFloat = 10
            let zigzagHeight: CGFloat = 3
            var x: CGFloat = -size.width/2 + 5
            zPath.move(to: CGPoint(x: x, y: 0))
            var up = true
            while x < size.width/2 - 5 {
                x += segmentWidth
                zPath.addLine(to: CGPoint(x: x, y: up ? zigzagHeight : -zigzagHeight))
                up.toggle()
            }
            zigzag.path = zPath
            zigzag.strokeColor = NSColor.white.withAlphaComponent(0.85)
            zigzag.lineWidth = 1.5
            addChild(zigzag)
```

- [ ] **Step 3: Sätt restitution 1.4 på trampolinen**

Vid SLUTET av `init`-metoden (efter den befintliga `physicsBody?.restitution = 0.5`), lägg till:

```swift
        if type == .trampoline {
            physicsBody?.restitution = 1.4
        }
```

- [ ] **Step 4: Lägg till "Studsmatta" i sidopanelens labels**

I `BallDrop/BallDrop/SidebarView.swift`, hitta `ForEach`-loopen som börjar med:

```swift
                ForEach(Array(zip(BlockType.allCases, ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel"])), id: \.0.rawValue) { type, label in
```

Ändra labels-arrayen till:

```swift
                ForEach(Array(zip(BlockType.allCases, ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel", "Studsmatta"])), id: \.0.rawValue) { type, label in
```

- [ ] **Step 5: Lägg till .trampoline-ikon i blockIcon-helper**

I `BallDrop/BallDrop/SidebarView.swift`, hitta `@ViewBuilder private func blockIcon(_ type: BlockType)`-funktionen. Lägg till en ny case INNAN den stängande `}` på switch-uttrycket:

```swift
        case .trampoline:
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(red: 0.40, green: 0.78, blue: 0.45))
                .frame(width: 24, height: 6)
```

- [ ] **Step 6: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!` utan fel.

(Kör INTE `swift run`.)

- [ ] **Step 7: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/BlockNode.swift BallDrop/BallDrop/SidebarView.swift
git commit -m "feat: add trampoline block with high-restitution bounce"
```

---

## Task 2: Katapult (catapult) med kontakt-impuls

**Files:**
- Modify: `BallDrop/BallDrop/BlockNode.swift`
- Modify: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/SidebarView.swift`

- [ ] **Step 1: Lägg till .catapult case i BlockType**

I `BallDrop/BallDrop/BlockNode.swift`, utöka enum:

```swift
enum BlockType: String, CaseIterable {
    case horizontalRect
    case verticalRect
    case diagonal
    case circle
    case triangle
    case trampoline
    case catapult
}
```

- [ ] **Step 2: Lägg till PhysicsCategory.catapult**

I `BallDrop/BallDrop/GameScene.swift`, ändra `enum PhysicsCategory` från:

```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
}
```

till:

```swift
enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
    static let catapult: UInt32   = 1 << 2
}
```

- [ ] **Step 3: Lägg till .catapult-gren i BlockNode init switch**

I `BlockNode.init(type:)`, lägg till en ny case-gren EFTER `.trampoline`:

```swift
        case .catapult:
            let size = CGSize(width: 100, height: 12)
            path = CGPath(roundedRect: CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2),
                                               size: size),
                          cornerWidth: 4, cornerHeight: 4, transform: nil)
            physicsBody = SKPhysicsBody(rectangleOf: size)
            fillColor = NSColor(red: 1.0, green: 0.55, blue: 0.20, alpha: 1)

            let arrow = SKShapeNode()
            let aPath = CGMutablePath()
            aPath.move(to: CGPoint(x: 0, y: 4))
            aPath.addLine(to: CGPoint(x: -5, y: -2))
            aPath.addLine(to: CGPoint(x: 5, y: -2))
            aPath.closeSubpath()
            arrow.path = aPath
            arrow.fillColor = NSColor.white
            arrow.strokeColor = NSColor.white
            arrow.alpha = 0.9
            addChild(arrow)
```

- [ ] **Step 4: Sätt categoryBitMask + contactTestBitMask på catapult**

I `BlockNode.init(type:)`, vid SLUTET av metoden (efter `physicsBody?.restitution = 0.5` och efter trampoline-grenen från Task 1), lägg till:

```swift
        if type == .catapult {
            physicsBody?.categoryBitMask = PhysicsCategory.catapult
            physicsBody?.contactTestBitMask = PhysicsCategory.ball
        }
```

OBS: `collisionBitMask` lämnas default — bollen ska studsa fysiskt mot ytan innan impulsen läggs till.

- [ ] **Step 5: Utöka bollens contactTestBitMask**

I `BallDrop/BallDrop/GameScene.swift`, hitta i `spawnBall()`:

```swift
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone
```

Ändra till:

```swift
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone | PhysicsCategory.catapult
```

- [ ] **Step 6: Lägg till catapult-gren i didBegin**

I `BallDrop/BallDrop/GameScene.swift`, hitta början av `func didBegin(_ contact: SKPhysicsContact)`. Direkt efter raderna:

```swift
        let bodyA = contact.bodyA
        let bodyB = contact.bodyB
```

Lägg till en ny gren INNAN den befintliga score-zone-logiken (innan `let ballBody: SKPhysicsBody?` deklarationen):

```swift
        if (bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.catapult) ||
           (bodyA.categoryBitMask == PhysicsCategory.catapult && bodyB.categoryBitMask == PhysicsCategory.ball) {
            let ballPB = bodyA.categoryBitMask == PhysicsCategory.ball ? bodyA : bodyB
            let catPB = ballPB === bodyA ? bodyB : bodyA
            guard let ballNode = ballPB.node, let catNode = catPB.node else { return }

            let theta = catNode.zRotation
            let impulse: CGFloat = 1.2
            let dirX = -sin(theta)
            let dirY = cos(theta)
            ballNode.physicsBody?.applyImpulse(CGVector(dx: dirX * impulse, dy: dirY * impulse))

            let flash = SKAction.sequence([
                SKAction.scale(to: 1.15, duration: 0.08),
                SKAction.scale(to: 1.0, duration: 0.08),
            ])
            catNode.run(flash)
            return
        }
```

- [ ] **Step 7: Lägg till "Katapult" i sidopanelens labels**

I `BallDrop/BallDrop/SidebarView.swift`, ändra labels-arrayen från Task 1:

```swift
                ForEach(Array(zip(BlockType.allCases, ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel", "Studsmatta"])), id: \.0.rawValue) { type, label in
```

till:

```swift
                ForEach(Array(zip(BlockType.allCases, ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel", "Studsmatta", "Katapult"])), id: \.0.rawValue) { type, label in
```

- [ ] **Step 8: Lägg till .catapult-ikon i blockIcon-helper**

I `BallDrop/BallDrop/SidebarView.swift`, lägg till en ny case i `blockIcon`-switchen:

```swift
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
```

(`Triangle`-strukten finns redan i SidebarView.swift.)

- [ ] **Step 9: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`

- [ ] **Step 10: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/BlockNode.swift BallDrop/BallDrop/GameScene.swift BallDrop/BallDrop/SidebarView.swift
git commit -m "feat: add catapult block with perpendicular impulse on contact"
```

---

## Task 3: Rotationshandtag på alla block

**Files:**
- Modify: `BallDrop/BallDrop/BlockNode.swift`

- [ ] **Step 1: Lägg till privat helper `addRotateHandle(at:)`**

I `BallDrop/BallDrop/BlockNode.swift`, INNAN den stängande `}` på `class BlockNode` (efter `required init?(coder:)`), lägg till:

```swift
    private func addRotateHandle(at offset: CGPoint) {
        let line = SKShapeNode()
        let linePath = CGMutablePath()
        linePath.move(to: .zero)
        linePath.addLine(to: offset)
        line.path = linePath
        line.strokeColor = NSColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.5)
        line.lineWidth = 1
        addChild(line)

        let handle = SKShapeNode(circleOfRadius: 6)
        handle.position = offset
        handle.fillColor = NSColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.7)
        handle.strokeColor = NSColor.white
        handle.lineWidth = 1
        handle.name = "rotateHandle"
        addChild(handle)
    }
```

- [ ] **Step 2: Anropa addRotateHandle från init**

I `BlockNode.init(type:)`, vid SLUTET av metoden (efter alla physics-overrides från Task 1 och Task 2), lägg till:

```swift
        let handleOffset: CGPoint
        switch type {
        case .horizontalRect, .diagonal, .trampoline, .catapult:
            handleOffset = CGPoint(x: 50 + 12, y: 0)
        case .verticalRect:
            handleOffset = CGPoint(x: 0, y: 50 + 12)
        case .circle:
            handleOffset = CGPoint(x: 20 + 12, y: 0)
        case .triangle:
            handleOffset = CGPoint(x: 0, y: 20 + 12)
        }
        addRotateHandle(at: handleOffset)
```

- [ ] **Step 3: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`

- [ ] **Step 4: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/BlockNode.swift
git commit -m "feat: add rotation handle child node to all blocks"
```

---

## Task 4: Mouse-handling för rotation + hjälptext

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/SidebarView.swift`

- [ ] **Step 1: Lägg till rotation-state properties**

I `BallDrop/BallDrop/GameScene.swift`, i `class GameScene`, intill övriga private properties (bra plats: efter `private var scoreZone: ScoreZone?`), lägg till:

```swift
    private var rotatingNode: SKNode?
    private var rotateInitialAngle: CGFloat = 0
    private var rotateInitialZRotation: CGFloat = 0
```

- [ ] **Step 2: Hantera rotateHandle i mouseDown**

I `BallDrop/BallDrop/GameScene.swift`, hitta `override func mouseDown(with event: NSEvent)`. Direkt efter `let location = event.location(in: self)` och `let node = atPoint(location)` — INNAN den befintliga `if node.name == "spawnPoint"`-grenen — lägg till:

```swift
        if node.name == "rotateHandle", let block = node.parent {
            rotatingNode = block
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            rotateInitialAngle = atan2(dy, dx)
            rotateInitialZRotation = block.zRotation
            return
        }
```

- [ ] **Step 3: Hantera rotation-drag i mouseDragged**

I `BallDrop/BallDrop/GameScene.swift`, hitta `override func mouseDragged(with event: NSEvent)`. Direkt efter `let location = event.location(in: self)` — INNAN den befintliga `if drawMode`-grenen — lägg till:

```swift
        if let block = rotatingNode {
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            let currentAngle = atan2(dy, dx)
            block.zRotation = rotateInitialZRotation + (currentAngle - rotateInitialAngle)
            return
        }
```

- [ ] **Step 4: Rensa rotation-state i mouseUp**

I `BallDrop/BallDrop/GameScene.swift`, hitta `override func mouseUp(with event: NSEvent)`. Direkt vid metodens BÖRJAN (innan `if drawMode`-grenen), lägg till:

```swift
        if rotatingNode != nil {
            rotatingNode = nil
            return
        }
```

- [ ] **Step 5: Lägg till rotation-instruktion i sidopanelens hjälptext**

I `BallDrop/BallDrop/SidebarView.swift`, hitta hjälptext-blocket längst ned i body:

```swift
            VStack(alignment: .leading, spacing: 2) {
                Text("Space = pausa")
                Text("C = rensa block")
                Text("+/- = hastighet")
                Text("Scroll = rotera block")
                Text("Högerklick = ta bort")
            }
```

Lägg till en ny rad efter "Scroll = rotera block":

```swift
            VStack(alignment: .leading, spacing: 2) {
                Text("Space = pausa")
                Text("C = rensa block")
                Text("+/- = hastighet")
                Text("Scroll = rotera block")
                Text("Drag blå handtag = rotera")
                Text("Högerklick = ta bort")
            }
```

- [ ] **Step 6: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`

- [ ] **Step 7: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/GameScene.swift BallDrop/BallDrop/SidebarView.swift
git commit -m "feat: drag rotation handle to rotate blocks"
```

---

## Task 5: Manuell verifiering

- [ ] **Step 1: Bygg och kör**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift run
```

(Detta öppnar GUI — får göras av controller, inte av subagent.)

- [ ] **Step 2: Verifiera Studsmatta**

1. Klicka "Studsmatta" i sidopanelen → en grön rektangel med zigzag-mönster placeras i mitten av spelytan.
2. Bygg en bana som leder bollar att träffa studsmattan.
3. Verifiera: bollen studsar tydligt högre/snabbare än om den hade träffat ett vanligt horisontellt block.

- [ ] **Step 3: Verifiera Katapult**

1. Klicka "Katapult" → en orange rektangel med vit pil uppåt placeras.
2. Led bollar mot katapulten.
3. Verifiera: vid kontakt blinkar katapulten kort (scale 1.15→1.0), bollen skjuts iväg uppåt med tydligt mer fart än normalt.
4. Flera bollar samtidigt: alla får impulsen oberoende.

- [ ] **Step 4: Verifiera rotation via handtag**

1. För muspekaren över ett block — en liten ljusblå cirkel ("handtaget") syns vid blockets ena ände, kopplad till blockets center med en tunn linje.
2. Klicka och drag handtaget i en cirkulär rörelse → blocket roterar runt sin egen mitt.
3. Verifiera: blocket flyttas INTE under rotation (bara `zRotation` ändras).
4. Släpp musen → rotationen stannar där.

- [ ] **Step 5: Rotera katapulten + verifiera riktning**

1. Placera en katapult och rotera den 90° (pilen pekar nu åt höger).
2. Led en boll mot katapulten.
3. Verifiera: bollen skjuts åt höger (vinkelrätt mot katapultens nya yta), inte uppåt.
4. Rotera till 180° (pilen nedåt) — bollar skjuts nu nedåt.

- [ ] **Step 6: Verifiera scroll-rotation kvarstår**

1. Scroll-hjul över ett block → blocket roterar (befintlig funktion).

- [ ] **Step 7: Verifiera blockdrag**

1. Klicka och drag ett block (inte handtaget) → blocket flyttas, ingen rotation.
2. Högerklick på block → tas bort som tidigare.

- [ ] **Step 8: Slutgranska commits**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git log --oneline -6
```

Förväntat: fyra nya feature-commits ovanpå tidigare HEAD.

---

## Verifiering mot specen

- [x] Studsmatta visuell + restitution 1.4 — Task 1 (steg 2 + 3)
- [x] Katapult visuell + impuls 1.2 vinkelrätt mot ytan — Task 2 (steg 3 + 6)
- [x] PhysicsCategory.catapult = 1<<2 — Task 2 (steg 2)
- [x] Bollens contactTestBitMask utökas — Task 2 (steg 5)
- [x] didBegin catapult-gren med flash — Task 2 (steg 6)
- [x] Rotationshandtag (cirkel + linje) på alla 7 typer — Task 3
- [x] mouseDown/Dragged/Up för rotation — Task 4 (steg 2-4)
- [x] scrollWheel orörd — bekräftat genom frånvaro av ändring
- [x] Sidopanel labels Studsmatta + Katapult — Task 1 + 2
- [x] Hjälptext "Drag blå handtag = rotera" — Task 4 (steg 5)
- [x] Inga nya filer — bekräftat genom file structure ovan

---

## Rollback om något går fel

Fyra atomära feature-commits gör rollback enkel: `git reset --hard HEAD~N` för att rulla tillbaka N steg. Specen och planen ligger kvar oavsett.
