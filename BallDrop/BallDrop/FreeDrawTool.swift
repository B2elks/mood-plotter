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

        var bodies: [SKPhysicsBody] = []
        for i in 0..<simplified.count - 1 {
            let edge = SKPhysicsBody(edgeFrom: simplified[i], to: simplified[i + 1])
            bodies.append(edge)
        }
        if !bodies.isEmpty {
            block.physicsBody = SKPhysicsBody(bodies: bodies)
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
}
