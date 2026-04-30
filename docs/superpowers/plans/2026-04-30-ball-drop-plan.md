# Ball Drop Sandbox Game — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a native macOS sandbox game where balls fall with realistic physics and bounce off player-placed blocks.

**Architecture:** Swift + SpriteKit app. SwiftUI sidebar for tool palette, SpriteKit scene for physics simulation. Balls auto-spawn from a draggable point, blocks are placed by dragging from palette or freehand drawing. No external dependencies.

**Tech Stack:** Swift, SpriteKit, SwiftUI, macOS 14+, Xcode

---

### Task 1: Xcode project scaffold and app shell

**Files:**
- Create: `BallDrop/BallDrop/BallDropApp.swift`
- Create: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Create Xcode project via command line**

```bash
mkdir -p /Users/b2/Documents/Proj/LLM/BallDrop/BallDrop
```

- [ ] **Step 2: Create BallDropApp.swift**

```swift
import SwiftUI

@main
struct BallDropApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 900, minHeight: 600)
        }
        .windowStyle(.titleBar)
        .defaultSize(width: 1100, height: 750)
    }
}
```

Write to `BallDrop/BallDrop/BallDropApp.swift`.

- [ ] **Step 3: Create ContentView.swift — empty shell with sidebar + SpriteKit area**

```swift
import SwiftUI
import SpriteKit

struct ContentView: View {
    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.0
    @State private var isPaused: Bool = false

    var body: some View {
        HStack(spacing: 0) {
            // Sidebar placeholder
            VStack {
                Text("Tools")
                    .font(.headline)
                    .padding()
                Spacer()
            }
            .frame(width: 200)
            .background(Color.white)

            // Game area placeholder
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.53, green: 0.81, blue: 0.92),
                            Color(red: 0.60, green: 0.85, blue: 0.78)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
        }
    }
}
```

Write to `BallDrop/BallDrop/ContentView.swift`.

- [ ] **Step 4: Create Package.swift for SPM-based build (no Xcode project file needed)**

```swift
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "BallDrop",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "BallDrop",
            path: "BallDrop"
        )
    ]
)
```

Write to `BallDrop/Package.swift`.

- [ ] **Step 5: Verify it builds**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

Expected: BUILD SUCCEEDED

- [ ] **Step 6: Commit**

```bash
git add BallDrop/
git commit -m "feat: scaffold BallDrop macOS app with SwiftUI shell"
```

---

### Task 2: GameScene — SpriteKit scene with physics world and background

**Files:**
- Create: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Create GameScene.swift**

```swift
import SpriteKit

class GameScene: SKScene, SKPhysicsContactDelegate {

    var spawnRate: TimeInterval = 1.5
    var isPaused_: Bool = false
    private var lastSpawnTime: TimeInterval = 0
    private let maxBalls = 100

    override func didMove(to view: SKView) {
        backgroundColor = .clear

        // Physics world
        physicsWorld.gravity = CGVector(dx: 0, dy: -9.8)
        physicsWorld.contactDelegate = self

        // Side walls (invisible)
        let wallThickness: CGFloat = 1
        let leftWall = SKNode()
        leftWall.position = CGPoint(x: 0, y: size.height / 2)
        leftWall.physicsBody = SKPhysicsBody(rectangleOf: CGSize(width: wallThickness, height: size.height))
        leftWall.physicsBody?.isDynamic = false
        leftWall.physicsBody?.friction = 0.2
        addChild(leftWall)

        let rightWall = SKNode()
        rightWall.position = CGPoint(x: size.width, y: size.height / 2)
        rightWall.physicsBody = SKPhysicsBody(rectangleOf: CGSize(width: wallThickness, height: size.height))
        rightWall.physicsBody?.isDynamic = false
        rightWall.physicsBody?.friction = 0.2
        addChild(rightWall)
    }

    override func update(_ currentTime: TimeInterval) {
        guard !isPaused_ else { return }

        // Auto-spawn balls
        if currentTime - lastSpawnTime >= spawnRate {
            spawnBall()
            lastSpawnTime = currentTime
        }

        // Remove balls that fell below screen
        for node in children where node.name == "ball" {
            if node.position.y < -20 {
                node.removeFromParent()
            }
        }
    }

    private func spawnBall() {
        let ballCount = children.filter { $0.name == "ball" }.count
        if ballCount >= maxBalls {
            // Remove oldest
            if let oldest = children.first(where: { $0.name == "ball" }) {
                oldest.removeFromParent()
            }
        }

        let radius: CGFloat = 8
        let colors: [NSColor] = [
            NSColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),   // rosa
            NSColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),   // orange
            NSColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),  // grön
            NSColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),  // lila
            NSColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),   // gul
        ]

        let ball = SKShapeNode(circleOfRadius: radius)
        ball.name = "ball"
        ball.fillColor = colors.randomElement()!
        ball.strokeColor = .white
        ball.lineWidth = 2
        ball.position = CGPoint(x: size.width / 2, y: size.height - 30)

        ball.physicsBody = SKPhysicsBody(circleOfRadius: radius)
        ball.physicsBody?.restitution = 0.7
        ball.physicsBody?.friction = 0.3
        ball.physicsBody?.linearDamping = 0.1
        ball.physicsBody?.angularDamping = 0.1
        ball.physicsBody?.mass = 0.1

        // Small random horizontal impulse
        let dx = CGFloat.random(in: -0.3...0.3)
        ball.physicsBody?.applyImpulse(CGVector(dx: dx, dy: 0))

        addChild(ball)
    }

    func clearAllBlocks() {
        children.filter { $0.name == "block" }.forEach { $0.removeFromParent() }
    }
}
```

Write to `BallDrop/BallDrop/GameScene.swift`.

- [ ] **Step 2: Update ContentView.swift to embed GameScene**

```swift
import SwiftUI
import SpriteKit

struct ContentView: View {
    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.5
    @State private var isPaused: Bool = false
    @State private var gameScene: GameScene = {
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        return scene
    }()

    var body: some View {
        HStack(spacing: 0) {
            // Sidebar placeholder
            VStack {
                Text("Tools")
                    .font(.headline)
                    .padding()
                Spacer()
            }
            .frame(width: 200)
            .background(Color.white)

            // Game area
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
        }
        .onAppear {
            gameScene.spawnRate = spawnRate
        }
    }
}
```

Write to `BallDrop/BallDrop/ContentView.swift`.

- [ ] **Step 3: Build and verify balls fall**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

Run the app to verify: balls spawn from top center, fall down, bounce off side walls, disappear at bottom.

- [ ] **Step 4: Commit**

```bash
git add BallDrop/
git commit -m "feat: add GameScene with ball spawning and physics"
```

---

### Task 3: BlockNode — placeable blocks with physics

**Files:**
- Create: `BallDrop/BallDrop/BlockNode.swift`
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Create BlockNode.swift**

```swift
import SpriteKit

enum BlockType: String, CaseIterable {
    case horizontalRect
    case verticalRect
    case diagonal
    case circle
    case triangle
}

class BlockNode: SKShapeNode {

    let blockType: BlockType

    init(type: BlockType) {
        self.blockType = type
        super.init()

        name = "block"
        fillColor = .white
        strokeColor = NSColor(white: 0.85, alpha: 1)
        lineWidth = 1
        alpha = 0.9

        switch type {
        case .horizontalRect:
            let size = CGSize(width: 100, height: 12)
            path = CGPath(roundedRect: CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2),
                                               size: size),
                          cornerWidth: 4, cornerHeight: 4, transform: nil)
            physicsBody = SKPhysicsBody(rectangleOf: size)

        case .verticalRect:
            let size = CGSize(width: 12, height: 100)
            path = CGPath(roundedRect: CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2),
                                               size: size),
                          cornerWidth: 4, cornerHeight: 4, transform: nil)
            physicsBody = SKPhysicsBody(rectangleOf: size)

        case .diagonal:
            let size = CGSize(width: 100, height: 12)
            path = CGPath(roundedRect: CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2),
                                               size: size),
                          cornerWidth: 4, cornerHeight: 4, transform: nil)
            physicsBody = SKPhysicsBody(rectangleOf: size)
            zRotation = -.pi / 6  // 30 degrees

        case .circle:
            let radius: CGFloat = 20
            path = CGPath(ellipseIn: CGRect(x: -radius, y: -radius, width: radius*2, height: radius*2), transform: nil)
            physicsBody = SKPhysicsBody(circleOfRadius: radius)

        case .triangle:
            let size: CGFloat = 40
            let triPath = CGMutablePath()
            triPath.move(to: CGPoint(x: 0, y: size/2))
            triPath.addLine(to: CGPoint(x: -size/2, y: -size/2))
            triPath.addLine(to: CGPoint(x: size/2, y: -size/2))
            triPath.closeSubpath()
            path = triPath
            physicsBody = SKPhysicsBody(polygonFrom: triPath)
        }

        // Shadow effect
        let shadow = SKEffectNode()
        shadow.shouldRasterize = true
        shadow.filter = CIFilter(name: "CIGaussianBlur", parameters: ["inputRadius": 3])

        physicsBody?.isDynamic = false
        physicsBody?.friction = 0.3
        physicsBody?.restitution = 0.5
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not implemented")
    }
}
```

Write to `BallDrop/BallDrop/BlockNode.swift`.

- [ ] **Step 2: Add block placement to GameScene**

Add these methods to `GameScene.swift`:

```swift
// Add to GameScene class:

func addBlock(type: BlockType, at position: CGPoint) {
    let block = BlockNode(type: type)
    block.position = position
    addChild(block)
}

// Mouse interaction for dragging and deleting blocks
private var draggedNode: SKNode?

override func mouseDown(with event: NSEvent) {
    let location = event.location(in: self)
    let node = atPoint(location)

    if node.name == "block" || node.parent?.name == "block" {
        let block = node.name == "block" ? node : node.parent!
        draggedNode = block
    }
}

override func mouseDragged(with event: NSEvent) {
    guard let node = draggedNode else { return }
    node.position = event.location(in: self)
}

override func mouseUp(with event: NSEvent) {
    draggedNode = nil
}

override func rightMouseDown(with event: NSEvent) {
    let location = event.location(in: self)
    let node = atPoint(location)

    if node.name == "block" {
        node.removeFromParent()
    } else if node.parent?.name == "block" {
        node.parent?.removeFromParent()
    }
}

override func scrollWheel(with event: NSEvent) {
    let location = event.location(in: self)
    let node = atPoint(location)

    let block: SKNode?
    if node.name == "block" {
        block = node
    } else if node.parent?.name == "block" {
        block = node.parent
    } else {
        block = nil
    }

    if let block = block {
        block.zRotation += event.deltaY * 0.02
    }
}

override func keyDown(with event: NSEvent) {
    switch event.charactersIgnoringModifiers {
    case " ":
        isPaused_ = !isPaused_
    case "c":
        clearAllBlocks()
    case "+", "=":
        spawnRate = max(0.2, spawnRate - 0.2)
    case "-":
        spawnRate = min(5.0, spawnRate + 0.2)
    default:
        break
    }
}
```

- [ ] **Step 3: Build and verify**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

- [ ] **Step 4: Commit**

```bash
git add BallDrop/
git commit -m "feat: add BlockNode with drag, rotate, and delete"
```

---

### Task 4: SidebarView — tool palette with drag-to-place

**Files:**
- Create: `BallDrop/BallDrop/SidebarView.swift`
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Create SidebarView.swift**

```swift
import SwiftUI

struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var isPaused: Bool
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Ball Drop")
                .font(.system(size: 18, weight: .bold))
                .padding(.horizontal)
                .padding(.top, 16)

            Divider()

            // Block palette
            VStack(alignment: .leading, spacing: 8) {
                Text("BLOCKS")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(Array(zip(BlockType.allCases, blockLabels())), id: \.0.rawValue) { type, label in
                    Button(action: { onPlaceBlock(type) }) {
                        HStack(spacing: 10) {
                            blockIcon(type)
                                .frame(width: 28, height: 28)
                            Text(label)
                                .font(.system(size: 13))
                            Spacer()
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(Color.gray.opacity(0.08))
                        )
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                }

                // Free draw toggle
                Button(action: { selectedTool = selectedTool == "draw" ? "pointer" : "draw" }) {
                    HStack(spacing: 10) {
                        Image(systemName: "pencil.line")
                            .frame(width: 28, height: 28)
                        Text("Rita fritt")
                            .font(.system(size: 13))
                        Spacer()
                        if selectedTool == "draw" {
                            Image(systemName: "checkmark")
                                .foregroundColor(.blue)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(selectedTool == "draw" ? Color.blue.opacity(0.1) : Color.gray.opacity(0.08))
                    )
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 8)
            }

            Divider()

            // Controls
            VStack(alignment: .leading, spacing: 8) {
                Text("KONTROLL")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                HStack {
                    Text("Hastighet")
                        .font(.system(size: 12))
                    Slider(value: $spawnRate, in: 0.2...5.0, step: 0.1)
                }
                .padding(.horizontal)

                HStack(spacing: 8) {
                    Button(action: { isPaused.toggle() }) {
                        Label(isPaused ? "Starta" : "Pausa",
                              systemImage: isPaused ? "play.fill" : "pause.fill")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)

                    Button(action: onClearBlocks) {
                        Label("Rensa", systemImage: "trash")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)
                }
                .padding(.horizontal)
            }

            Spacer()

            // Keyboard shortcuts hint
            VStack(alignment: .leading, spacing: 2) {
                Text("Space = pausa")
                Text("C = rensa block")
                Text("+/- = hastighet")
                Text("Scroll = rotera block")
                Text("Högerklick = ta bort")
            }
            .font(.system(size: 10))
            .foregroundColor(.secondary)
            .padding()
        }
        .frame(width: 200)
        .background(Color(NSColor.windowBackgroundColor))
    }

    private func blockLabels() -> [String] {
        ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel"]
    }

    @ViewBuilder
    private func blockIcon(_ type: BlockType) -> some View {
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

Write to `BallDrop/BallDrop/SidebarView.swift`.

- [ ] **Step 2: Update ContentView.swift to use SidebarView**

```swift
import SwiftUI
import SpriteKit

struct ContentView: View {
    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.5
    @State private var isPaused: Bool = false
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
                isPaused: $isPaused,
                onPlaceBlock: { type in
                    gameScene.addBlock(type: type,
                        at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
                },
                onClearBlocks: {
                    gameScene.clearAllBlocks()
                }
            )

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
        }
        .onChange(of: spawnRate) { _, newValue in
            gameScene.spawnRate = newValue
        }
        .onChange(of: isPaused) { _, newValue in
            gameScene.isPaused_ = newValue
        }
    }
}
```

Write to `BallDrop/BallDrop/ContentView.swift`.

- [ ] **Step 3: Build and verify**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

- [ ] **Step 4: Commit**

```bash
git add BallDrop/
git commit -m "feat: add sidebar with block palette and controls"
```

---

### Task 5: FreeDrawTool — freehand drawing becomes physics blocks

**Files:**
- Create: `BallDrop/BallDrop/FreeDrawTool.swift`
- Modify: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/ContentView.swift`

- [ ] **Step 1: Create FreeDrawTool.swift**

```swift
import SpriteKit

class FreeDrawTool {

    private var points: [CGPoint] = []
    private var previewNode: SKShapeNode?
    private weak var scene: SKScene?

    init(scene: SKScene) {
        self.scene = scene
    }

    func beginDraw(at point: CGPoint) {
        points = [point]
        previewNode?.removeFromParent()
        previewNode = SKShapeNode()
        previewNode?.strokeColor = NSColor.white.withAlphaComponent(0.5)
        previewNode?.lineWidth = 6
        previewNode?.lineCap = .round
        previewNode?.lineJoin = .round
        scene?.addChild(previewNode!)
    }

    func continueDraw(at point: CGPoint) {
        // Skip if too close to last point
        if let last = points.last {
            let dist = hypot(point.x - last.x, point.y - last.y)
            if dist < 5 { return }
        }
        points.append(point)
        updatePreview()
    }

    func endDraw() -> SKShapeNode? {
        previewNode?.removeFromParent()
        previewNode = nil

        guard points.count >= 2 else { return nil }

        // Simplify points (Douglas-Peucker-like: keep every Nth point)
        let simplified = simplify(points, tolerance: 8)
        guard simplified.count >= 2 else { return nil }

        let path = CGMutablePath()
        path.move(to: simplified[0])
        for i in 1..<simplified.count {
            path.addLine(to: simplified[i])
        }

        let block = SKShapeNode(path: path)
        block.name = "block"
        block.strokeColor = .white
        block.lineWidth = 8
        block.lineCap = .round
        block.lineJoin = .round
        block.alpha = 0.9

        // Create physics body from the path with volume
        let physicsBodies = makePhysicsBodies(from: simplified, width: 8)
        if !physicsBodies.isEmpty {
            block.physicsBody = SKPhysicsBody(bodies: physicsBodies)
            block.physicsBody?.isDynamic = false
            block.physicsBody?.friction = 0.3
            block.physicsBody?.restitution = 0.5
        }

        points = []
        return block
    }

    private func updatePreview() {
        guard points.count >= 2 else { return }
        let path = CGMutablePath()
        path.move(to: points[0])
        for i in 1..<points.count {
            path.addLine(to: points[i])
        }
        previewNode?.path = path
    }

    private func simplify(_ pts: [CGPoint], tolerance: CGFloat) -> [CGPoint] {
        guard pts.count > 2 else { return pts }
        var result: [CGPoint] = [pts[0]]
        for i in 1..<pts.count {
            let dist = hypot(pts[i].x - result.last!.x, pts[i].y - result.last!.y)
            if dist >= tolerance {
                result.append(pts[i])
            }
        }
        if result.last != pts.last {
            result.append(pts.last!)
        }
        return result
    }

    private func makePhysicsBodies(from pts: [CGPoint], width: CGFloat) -> [SKPhysicsBody] {
        var bodies: [SKPhysicsBody] = []
        for i in 0..<pts.count - 1 {
            let a = pts[i]
            let b = pts[i + 1]
            let mid = CGPoint(x: (a.x + b.x) / 2, y: (a.y + b.y) / 2)
            let length = hypot(b.x - a.x, b.y - a.y)
            let angle = atan2(b.y - a.y, b.x - a.x)

            let segment = SKPhysicsBody(rectangleOf: CGSize(width: length, height: width),
                                        center: mid)
            // Note: can't set rotation on individual physics body in compound body,
            // so we use edge-based instead
            let edge = SKPhysicsBody(edgeFrom: a, to: b)
            bodies.append(edge)
        }
        return bodies
    }
}
```

Write to `BallDrop/BallDrop/FreeDrawTool.swift`.

- [ ] **Step 2: Add free draw support to GameScene**

Add to `GameScene.swift`:

```swift
// Add property
var drawMode: Bool = false
private var freeDrawTool: FreeDrawTool?

// In didMove(to:), add:
freeDrawTool = FreeDrawTool(scene: self)

// Replace mouseDown:
override func mouseDown(with event: NSEvent) {
    let location = event.location(in: self)

    if drawMode {
        freeDrawTool?.beginDraw(at: location)
        return
    }

    let node = atPoint(location)
    if node.name == "block" || node.parent?.name == "block" {
        let block = node.name == "block" ? node : node.parent!
        draggedNode = block
    }
}

// Replace mouseDragged:
override func mouseDragged(with event: NSEvent) {
    let location = event.location(in: self)

    if drawMode {
        freeDrawTool?.continueDraw(at: location)
        return
    }

    guard let node = draggedNode else { return }
    node.position = location
}

// Replace mouseUp:
override func mouseUp(with event: NSEvent) {
    if drawMode {
        if let block = freeDrawTool?.endDraw() {
            addChild(block)
        }
        return
    }
    draggedNode = nil
}
```

- [ ] **Step 3: Wire drawMode from ContentView**

In `ContentView.swift`, add to `onChange` section:

```swift
.onChange(of: selectedTool) { _, newValue in
    gameScene.drawMode = newValue == "draw"
}
```

- [ ] **Step 4: Build and verify**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

- [ ] **Step 5: Commit**

```bash
git add BallDrop/
git commit -m "feat: add freehand drawing tool for custom blocks"
```

---

### Task 6: SpawnPoint — draggable ball origin

**Files:**
- Create: `BallDrop/BallDrop/SpawnPoint.swift`
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Create SpawnPoint.swift**

```swift
import SpriteKit

class SpawnPoint: SKShapeNode {

    override init() {
        super.init()

        name = "spawnPoint"

        let radius: CGFloat = 14
        path = CGPath(ellipseIn: CGRect(x: -radius, y: -radius, width: radius*2, height: radius*2), transform: nil)
        fillColor = NSColor.white.withAlphaComponent(0.6)
        strokeColor = .white
        lineWidth = 2

        // Arrow indicator
        let arrow = SKShapeNode()
        let arrowPath = CGMutablePath()
        arrowPath.move(to: CGPoint(x: 0, y: -radius - 4))
        arrowPath.addLine(to: CGPoint(x: -6, y: -radius + 4))
        arrowPath.move(to: CGPoint(x: 0, y: -radius - 4))
        arrowPath.addLine(to: CGPoint(x: 6, y: -radius + 4))
        arrow.path = arrowPath
        arrow.strokeColor = .white
        arrow.lineWidth = 2
        arrow.lineCap = .round
        addChild(arrow)

        // Pulse animation
        let pulse = SKAction.sequence([
            SKAction.scale(to: 1.1, duration: 0.8),
            SKAction.scale(to: 1.0, duration: 0.8),
        ])
        run(SKAction.repeatForever(pulse))
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not implemented")
    }
}
```

Write to `BallDrop/BallDrop/SpawnPoint.swift`.

- [ ] **Step 2: Add SpawnPoint to GameScene**

Modify `GameScene.swift`:

```swift
// Add property
private var spawnPointNode: SpawnPoint!

// In didMove(to:), add after walls:
spawnPointNode = SpawnPoint()
spawnPointNode.position = CGPoint(x: size.width / 2, y: size.height - 30)
addChild(spawnPointNode)

// In spawnBall(), change position line to:
ball.position = spawnPointNode.position

// In mouseDown, add before existing code:
if node.name == "spawnPoint" || node.parent?.name == "spawnPoint" {
    draggedNode = spawnPointNode
    return
}
```

- [ ] **Step 3: Build and verify**

```bash
cd /Users/b2/Documents/Proj/LLM/BallDrop && swift build
```

- [ ] **Step 4: Commit**

```bash
git add BallDrop/
git commit -m "feat: add draggable spawn point for balls"
```
