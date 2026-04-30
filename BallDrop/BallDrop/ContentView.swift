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
        .onChange(of: selectedTool) { _, newValue in
            gameScene.drawMode = newValue == "draw"
        }
    }
}
