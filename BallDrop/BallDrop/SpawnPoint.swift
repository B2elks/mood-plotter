import SpriteKit

class SpawnPoint: SKShapeNode {

    override init() {
        super.init()

        name = "spawnPoint"

        let radius: CGFloat = 14
        path = CGPath(ellipseIn: CGRect(x: -radius, y: -radius, width: radius*2, height: radius*2), transform: nil)
        fillColor = SKColor.white.withAlphaComponent(0.6)
        strokeColor = .white
        lineWidth = 2

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
