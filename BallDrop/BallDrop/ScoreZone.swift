import SpriteKit

class ScoreZone: SKShapeNode {

    enum Edge {
        case bottom, left, right
    }

    static let zoneLength: CGFloat = 80
    static let zoneThickness: CGFloat = 12

    let edge: Edge

    init(edge: Edge) {
        self.edge = edge
        super.init()

        name = "scoreZone"

        let size: CGSize
        switch edge {
        case .bottom:
            size = CGSize(width: ScoreZone.zoneLength, height: ScoreZone.zoneThickness)
        case .left, .right:
            size = CGSize(width: ScoreZone.zoneThickness, height: ScoreZone.zoneLength)
        }

        let rect = CGRect(origin: CGPoint(x: -size.width/2, y: -size.height/2), size: size)
        path = CGPath(roundedRect: rect, cornerWidth: 3, cornerHeight: 3, transform: nil)

        fillColor = NSColor(red: 1.0, green: 0.75, blue: 0.20, alpha: 0.85)
        strokeColor = NSColor(red: 1.0, green: 0.85, blue: 0.40, alpha: 1)
        lineWidth = 2

        physicsBody = SKPhysicsBody(rectangleOf: size)
        physicsBody?.isDynamic = false
        physicsBody?.categoryBitMask = PhysicsCategory.scoreZone
        physicsBody?.contactTestBitMask = PhysicsCategory.ball
        physicsBody?.collisionBitMask = 0  // ingen fysisk kollision — bollen passerar fritt

        let pulse = SKAction.sequence([
            SKAction.scale(to: 1.15, duration: 0.6),
            SKAction.scale(to: 1.0, duration: 0.6),
        ])
        run(SKAction.repeatForever(pulse))
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not implemented")
    }
}
