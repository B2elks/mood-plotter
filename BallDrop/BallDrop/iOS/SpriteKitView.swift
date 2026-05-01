#if os(iOS)
import SwiftUI
import SpriteKit
import UIKit

struct SpriteKitView: UIViewRepresentable {
    let scene: GameScene

    func makeUIView(context: Context) -> SKView {
        let view = SKView()
        view.allowsTransparency = true
        view.presentScene(scene)

        let rotate = UIRotationGestureRecognizer(target: context.coordinator,
                                                 action: #selector(Coordinator.handleRotate(_:)))
        view.addGestureRecognizer(rotate)

        let longPress = UILongPressGestureRecognizer(target: context.coordinator,
                                                     action: #selector(Coordinator.handleLongPress(_:)))
        longPress.minimumPressDuration = 0.5
        view.addGestureRecognizer(longPress)

        return view
    }

    func updateUIView(_ uiView: SKView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(scene: scene) }

    class Coordinator: NSObject {
        let scene: GameScene
        var lastRotation: CGFloat = 0

        init(scene: GameScene) {
            self.scene = scene
        }

        @objc func handleRotate(_ gr: UIRotationGestureRecognizer) {
            guard let view = gr.view as? SKView else { return }
            let viewLoc = gr.location(in: view)
            let sceneLoc = scene.convertPoint(fromView: viewLoc)
            switch gr.state {
            case .began:
                lastRotation = 0
            case .changed:
                let delta = gr.rotation - lastRotation
                scene.rotateBlock(at: sceneLoc, by: delta)
                lastRotation = gr.rotation
            default:
                break
            }
        }

        @objc func handleLongPress(_ gr: UILongPressGestureRecognizer) {
            guard gr.state == .began,
                  let view = gr.view as? SKView else { return }
            let viewLoc = gr.location(in: view)
            let sceneLoc = scene.convertPoint(fromView: viewLoc)
            scene.removeBlock(at: sceneLoc)
        }
    }
}
#endif
