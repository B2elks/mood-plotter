import SpriteKit
#if os(iOS)
import UIKit
#endif

enum PhysicsCategory {
    static let ball: UInt32       = 1 << 0
    static let scoreZone: UInt32  = 1 << 1
    static let catapult: UInt32   = 1 << 2
    static let block: UInt32      = 1 << 3
    static let wall: UInt32       = 1 << 4
}

class GameScene: SKScene, SKPhysicsContactDelegate {

    var spawnRate: TimeInterval = 1.5
    var ballRadius: CGFloat = 8
    var isPaused_: Bool = false
    var drawMode: Bool = false
    private var freeDrawTool: FreeDrawTool?
    private var lastSpawnTime: TimeInterval = 0
    private let maxBalls = 100
    var draggedNode: SKNode?
    private var spawnPointNode: SpawnPoint!
    var score: Int = 0 {
        didSet { onScoreChanged?(score) }
    }
    var onScoreChanged: ((Int) -> Void)?
    private var scoreZone: ScoreZone?
    private var rotatingNode: SKNode?
    private var rotateInitialAngle: CGFloat = 0
    private var rotateInitialZRotation: CGFloat = 0
    let soundManager = SoundManager()

    override func didMove(to view: SKView) {
        backgroundColor = .clear

        physicsWorld.gravity = CGVector(dx: 0, dy: -9.8)
        physicsWorld.contactDelegate = self

        spawnPointNode = SpawnPoint()
        addChild(spawnPointNode)

        freeDrawTool = FreeDrawTool(scene: self)

        rebuildLayout()
    }

    override func didChangeSize(_ oldSize: CGSize) {
        super.didChangeSize(oldSize)
        rebuildLayout()
    }

    private func rebuildLayout() {
        guard size.width > 0, size.height > 0 else { return }

        children.filter { $0.name == "wall" }.forEach { $0.removeFromParent() }

        let wallThickness: CGFloat = 1
        let leftWall = SKNode()
        leftWall.name = "wall"
        leftWall.position = CGPoint(x: 0, y: size.height / 2)
        leftWall.physicsBody = SKPhysicsBody(rectangleOf: CGSize(width: wallThickness, height: size.height))
        leftWall.physicsBody?.isDynamic = false
        leftWall.physicsBody?.friction = 0.2
        leftWall.physicsBody?.categoryBitMask = PhysicsCategory.wall
        leftWall.physicsBody?.contactTestBitMask = PhysicsCategory.ball
        addChild(leftWall)

        let rightWall = SKNode()
        rightWall.name = "wall"
        rightWall.position = CGPoint(x: size.width, y: size.height / 2)
        rightWall.physicsBody = SKPhysicsBody(rectangleOf: CGSize(width: wallThickness, height: size.height))
        rightWall.physicsBody?.isDynamic = false
        rightWall.physicsBody?.friction = 0.2
        rightWall.physicsBody?.categoryBitMask = PhysicsCategory.wall
        rightWall.physicsBody?.contactTestBitMask = PhysicsCategory.ball
        addChild(rightWall)

        spawnPointNode?.position = CGPoint(x: size.width / 2, y: size.height - 30)

        if scoreZone == nil {
            spawnScoreZone()
        }
    }

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

    func spawnBall() {
        let ballCount = children.filter { $0.name == "ball" }.count
        if ballCount >= maxBalls {
            if let oldest = children.first(where: { $0.name == "ball" }) {
                oldest.removeFromParent()
            }
        }

        let radius: CGFloat = ballRadius
        let colors: [SKColor] = [
            SKColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
            SKColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
            SKColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
            SKColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
            SKColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
        ]
        let colorIndex = Int.random(in: 0..<colors.count)

        let ball = SKShapeNode(circleOfRadius: radius)
        ball.name = "ball"
        ball.fillColor = colors[colorIndex]
        ball.userData = ["colorIndex": colorIndex]
        ball.strokeColor = .white
        ball.lineWidth = 2
        ball.position = spawnPointNode.position

        ball.physicsBody = SKPhysicsBody(circleOfRadius: radius)
        ball.physicsBody?.restitution = 0.7
        ball.physicsBody?.friction = 0.3
        ball.physicsBody?.linearDamping = 0.1
        ball.physicsBody?.angularDamping = 0.1
        ball.physicsBody?.mass = 0.1
        ball.physicsBody?.categoryBitMask = PhysicsCategory.ball
        ball.physicsBody?.contactTestBitMask = PhysicsCategory.scoreZone | PhysicsCategory.catapult | PhysicsCategory.block | PhysicsCategory.wall

        let dx = CGFloat.random(in: -0.3...0.3)
        ball.physicsBody?.applyImpulse(CGVector(dx: dx, dy: 0))

        addChild(ball)
    }

    func addBlock(type: BlockType, at position: CGPoint) {
        let block = BlockNode(type: type)
        block.position = position
        addChild(block)
    }

    func clearAllBlocks() {
        children.filter { $0.name == "block" }.forEach { $0.removeFromParent() }
    }

    func spawnScoreZone() {
        let margin = ScoreZone.zoneLength / 2 + 10
        guard size.width > margin * 2, size.height > margin * 2 else { return }

        let edges: [ScoreZone.Edge] = [.bottom, .left, .right]
        let edge = edges.randomElement()!
        let zone = ScoreZone(edge: edge)

        let halfThick = ScoreZone.zoneThickness / 2

        switch edge {
        case .bottom:
            let x = CGFloat.random(in: margin...(size.width - margin))
            zone.position = CGPoint(x: x, y: halfThick)
        case .left:
            let y = CGFloat.random(in: margin...(size.height - margin))
            zone.position = CGPoint(x: halfThick, y: y)
        case .right:
            let y = CGFloat.random(in: margin...(size.height - margin))
            zone.position = CGPoint(x: size.width - halfThick, y: y)
        }

        scoreZone = zone
        addChild(zone)
    }

    func resetScore() {
        score = 0
        scoreZone?.removeFromParent()
        scoreZone = nil
        spawnScoreZone()
    }

    func didBegin(_ contact: SKPhysicsContact) {
        let bodyA = contact.bodyA
        let bodyB = contact.bodyB

        // Ball ↔ wall: pure sound, no other physics effect.
        if (bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.wall) ||
           (bodyA.categoryBitMask == PhysicsCategory.wall && bodyB.categoryBitMask == PhysicsCategory.ball) {
            let ballNode = bodyA.categoryBitMask == PhysicsCategory.ball ? bodyA.node : bodyB.node
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .wall)
            return
        }

        // Ball ↔ block (incl. trampoline). Catapult bodies have .block|.catapult and are
        // explicitly excluded so the catapult branch below handles them.
        let aIsBall = bodyA.categoryBitMask == PhysicsCategory.ball
        let aIsBlock = (bodyA.categoryBitMask & PhysicsCategory.block) != 0 && (bodyA.categoryBitMask & PhysicsCategory.catapult) == 0
        let bIsBall = bodyB.categoryBitMask == PhysicsCategory.ball
        let bIsBlock = (bodyB.categoryBitMask & PhysicsCategory.block) != 0 && (bodyB.categoryBitMask & PhysicsCategory.catapult) == 0
        if (aIsBall && bIsBlock) || (aIsBlock && bIsBall) {
            let ballNode = aIsBall ? bodyA.node : bodyB.node
            let blockNode = aIsBall ? bodyB.node : bodyA.node
            let surface: SoundManager.Surface
            if let bn = blockNode as? BlockNode, bn.blockType == .trampoline {
                surface = .trampoline
            } else {
                surface = .block
            }
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: surface)
            return
        }

        if (bodyA.categoryBitMask == PhysicsCategory.ball && (bodyB.categoryBitMask & PhysicsCategory.catapult) != 0) ||
           ((bodyA.categoryBitMask & PhysicsCategory.catapult) != 0 && bodyB.categoryBitMask == PhysicsCategory.ball) {
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
            soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .catapult)
            return
        }

        let ballBody: SKPhysicsBody?
        let zoneBody: SKPhysicsBody?

        if bodyA.categoryBitMask == PhysicsCategory.ball && bodyB.categoryBitMask == PhysicsCategory.scoreZone {
            ballBody = bodyA
            zoneBody = bodyB
        } else if bodyA.categoryBitMask == PhysicsCategory.scoreZone && bodyB.categoryBitMask == PhysicsCategory.ball {
            ballBody = bodyB
            zoneBody = bodyA
        } else {
            return
        }

        guard let ballNode = ballBody?.node, let zoneNode = zoneBody?.node else { return }
        guard let currentZone = scoreZone, zoneNode === currentZone else { return }
        scoreZone = nil

        let flash = SKAction.sequence([
            SKAction.group([
                SKAction.scale(to: 1.6, duration: 0.15),
                SKAction.fadeOut(withDuration: 0.15),
            ]),
            SKAction.removeFromParent(),
        ])
        ballNode.physicsBody = nil
        ballNode.run(flash)

        let zoneFlash = SKAction.sequence([
            SKAction.group([
                SKAction.scale(to: 1.4, duration: 0.12),
                SKAction.fadeOut(withDuration: 0.12),
            ]),
            SKAction.removeFromParent(),
        ])
        zoneNode.physicsBody = nil
        zoneNode.run(zoneFlash)

        soundManager.play(colorIndex: colorIndex(of: ballNode), surface: .scoreZone)
        score += 1
        spawnScoreZone()
    }

    private func colorIndex(of node: SKNode?) -> Int {
        (node?.userData?["colorIndex"] as? Int) ?? 0
    }

    private func handlePrimaryDown(at location: CGPoint) {
        rotatingNode = nil

        let node = atPoint(location)
        if node.name == "rotateHandle", let block = node.parent {
            rotatingNode = block
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            rotateInitialAngle = atan2(dy, dx)
            rotateInitialZRotation = block.zRotation
            return
        }

        if node.name == "spawnPoint" || node.parent?.name == "spawnPoint" {
            draggedNode = spawnPointNode
            return
        }

        if drawMode {
            freeDrawTool?.beginDraw(at: location)
            return
        }

        if node.name == "block" || node.parent?.name == "block" {
            let block = node.name == "block" ? node : node.parent!
            draggedNode = block
        }
    }

    private func handlePrimaryDragged(at location: CGPoint) {
        if let block = rotatingNode {
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            let currentAngle = atan2(dy, dx)
            block.zRotation = rotateInitialZRotation + (currentAngle - rotateInitialAngle)
            return
        }

        if drawMode {
            freeDrawTool?.continueDraw(at: location)
            return
        }

        guard let node = draggedNode else { return }
        node.position = location
    }

    private func handlePrimaryUp() {
        if rotatingNode != nil {
            rotatingNode = nil
            return
        }

        if drawMode {
            if let block = freeDrawTool?.endDraw() {
                addChild(block)
            }
            return
        }
        draggedNode = nil
    }

    func rotateBlock(at location: CGPoint, by delta: CGFloat) {
        let node = atPoint(location)
        let block: SKNode?
        if node.name == "block" { block = node }
        else if node.parent?.name == "block" { block = node.parent }
        else { block = nil }
        if let block = block {
            block.zRotation += delta
        }
    }

    func removeBlock(at location: CGPoint) {
        let node = atPoint(location)
        if node.name == "block" {
            node.removeFromParent()
        } else if node.parent?.name == "block" {
            node.parent?.removeFromParent()
        }
    }

    #if os(macOS)
    override func mouseDown(with event: NSEvent) {
        handlePrimaryDown(at: event.location(in: self))
    }

    override func mouseDragged(with event: NSEvent) {
        handlePrimaryDragged(at: event.location(in: self))
    }

    override func mouseUp(with event: NSEvent) {
        handlePrimaryUp()
    }

    override func rightMouseDown(with event: NSEvent) {
        removeBlock(at: event.location(in: self))
    }

    override func scrollWheel(with event: NSEvent) {
        rotateBlock(at: event.location(in: self), by: event.deltaY * 0.02)
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
    #endif

    #if os(iOS)
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first else { return }
        handlePrimaryDown(at: touch.location(in: self))
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first else { return }
        handlePrimaryDragged(at: touch.location(in: self))
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        handlePrimaryUp()
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        handlePrimaryUp()
    }
    #endif
}
