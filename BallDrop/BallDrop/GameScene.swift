import SpriteKit

class GameScene: SKScene, SKPhysicsContactDelegate {

    var spawnRate: TimeInterval = 1.5
    var isPaused_: Bool = false
    var drawMode: Bool = false
    private var freeDrawTool: FreeDrawTool?
    private var lastSpawnTime: TimeInterval = 0
    private let maxBalls = 100
    var draggedNode: SKNode?

    override func didMove(to view: SKView) {
        backgroundColor = .clear

        physicsWorld.gravity = CGVector(dx: 0, dy: -9.8)
        physicsWorld.contactDelegate = self

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

        freeDrawTool = FreeDrawTool(scene: self)
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

        let radius: CGFloat = 8
        let colors: [NSColor] = [
            NSColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
            NSColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
            NSColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
            NSColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
            NSColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
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

    override func mouseDragged(with event: NSEvent) {
        let location = event.location(in: self)

        if drawMode {
            freeDrawTool?.continueDraw(at: location)
            return
        }

        guard let node = draggedNode else { return }
        node.position = location
    }

    override func mouseUp(with event: NSEvent) {
        if drawMode {
            if let block = freeDrawTool?.endDraw() {
                addChild(block)
            }
            return
        }
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
        if node.name == "block" { block = node }
        else if node.parent?.name == "block" { block = node.parent }
        else { block = nil }
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
}
