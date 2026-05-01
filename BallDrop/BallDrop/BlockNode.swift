import SpriteKit

enum BlockType: String, CaseIterable {
    case horizontalRect
    case verticalRect
    case diagonal
    case circle
    case triangle
    case trampoline
    case catapult
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
            zRotation = -.pi / 6

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
        }

        physicsBody?.isDynamic = false
        physicsBody?.friction = 0.3
        physicsBody?.restitution = 0.5

        if type == .trampoline {
            physicsBody?.restitution = 1.4
        }

        if type == .catapult {
            physicsBody?.categoryBitMask = PhysicsCategory.catapult
            physicsBody?.contactTestBitMask = PhysicsCategory.ball
        }

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
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not implemented")
    }

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
}
