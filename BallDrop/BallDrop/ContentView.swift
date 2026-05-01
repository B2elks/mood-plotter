import SwiftUI
import SpriteKit

struct ContentView: View {
    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.5
    @State private var ballRadius: Double = 8
    @State private var isPaused: Bool = false
    @State private var score: Int = 0
    @State private var isMuted: Bool = false
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
                ballRadius: $ballRadius,
                isPaused: $isPaused,
                isMuted: $isMuted,
                score: $score,
                onPlaceBlock: { type in
                    gameScene.addBlock(type: type,
                        at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
                },
                onClearBlocks: {
                    gameScene.clearAllBlocks()
                },
                onResetScore: {
                    gameScene.resetScore()
                }
            )

            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
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
                #else
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
                #endif

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
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
        .onChange(of: ballRadius) { _, newValue in
            gameScene.ballRadius = CGFloat(newValue)
        }
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
        .onAppear {
            gameScene.onScoreChanged = { newScore in
                Task { @MainActor in
                    score = newScore
                }
            }
        }
    }
}
