import SwiftUI
import SpriteKit

struct BuildView: View {
    var onHome: (() -> Void)? = nil

    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.5
    @State private var ballRadius: Double = 8
    @State private var isPaused: Bool = false
    @State private var score: Int = 0
    @State private var isMuted: Bool = false
    @State private var manualMode: Bool = false
    @State private var sceneFrame: CGRect = .zero
    @State private var gameScene: GameScene = {
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        return scene
    }()

    var body: some View {
        HStack(spacing: 0) {
            sidebar
            playArea
        }
        .modifier(StateBindings(
            spawnRate: spawnRate,
            isPaused: isPaused,
            selectedTool: selectedTool,
            ballRadius: ballRadius,
            isMuted: isMuted,
            manualMode: manualMode,
            gameScene: gameScene
        ))
        .onAppear {
            gameScene.onScoreChanged = { newScore in
                Task { @MainActor in
                    score = newScore
                }
            }
        }
    }

    private var sidebar: some View {
        SidebarView(
            selectedTool: $selectedTool,
            spawnRate: $spawnRate,
            ballRadius: $ballRadius,
            isPaused: $isPaused,
            isMuted: $isMuted,
            score: $score,
            manualMode: $manualMode,
            onPlaceBlock: { type in
                gameScene.addBlock(type: type,
                    at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
            },
            onClearBlocks: {
                gameScene.clearAllBlocks()
            },
            onResetScore: {
                gameScene.resetScore()
            },
            onLaunchBall: {
                gameScene.launchBall()
            },
            onDragBlock: { type, globalLocation in
                handleDrop(at: globalLocation, type: type)
            },
            onHome: onHome
        )
    }

    private var playArea: some View {
        ZStack(alignment: .topTrailing) {
            GeometryReader { proxy in
                spriteHost(proxy: proxy)
            }

            Text("\(score)")
                .font(.system(size: 48, weight: .bold, design: .rounded))
                .foregroundColor(.white)
                .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                .padding(.top, 16)
                .padding(.trailing, 24)
        }
    }

    @ViewBuilder
    private func spriteHost(proxy: GeometryProxy) -> some View {
        #if os(iOS)
        SpriteKitView(scene: gameScene)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(gameBackground)
            .onAppear { sceneFrame = proxy.frame(in: .global) }
            .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
        #else
        SpriteView(scene: gameScene, options: [.allowsTransparency])
            .background(gameBackground)
            .onAppear { sceneFrame = proxy.frame(in: .global) }
            .onChange(of: proxy.frame(in: .global)) { _, new in sceneFrame = new }
        #endif
    }

    private var gameBackground: some View {
        LinearGradient(
            colors: [
                Color(red: 0.53, green: 0.81, blue: 0.92),
                Color(red: 0.60, green: 0.85, blue: 0.78)
            ],
            startPoint: .top,
            endPoint: .bottom
        )
    }

    private func handleDrop(at globalLocation: CGPoint, type: BlockType) {
        guard sceneFrame.contains(globalLocation) else { return }
        let viewLoc = CGPoint(
            x: globalLocation.x - sceneFrame.origin.x,
            y: globalLocation.y - sceneFrame.origin.y
        )
        let sceneLoc = gameScene.convertPoint(fromView: viewLoc)
        gameScene.addBlock(type: type, at: sceneLoc)
    }
}

private struct StateBindings: ViewModifier {
    let spawnRate: Double
    let isPaused: Bool
    let selectedTool: String
    let ballRadius: Double
    let isMuted: Bool
    let manualMode: Bool
    let gameScene: GameScene

    func body(content: Content) -> some View {
        content
            .modifier(SpawnBindings(spawnRate: spawnRate, isPaused: isPaused, manualMode: manualMode, gameScene: gameScene))
            .modifier(ToolBindings(selectedTool: selectedTool, ballRadius: ballRadius, isMuted: isMuted, gameScene: gameScene))
    }
}

private struct SpawnBindings: ViewModifier {
    let spawnRate: Double
    let isPaused: Bool
    let manualMode: Bool
    let gameScene: GameScene

    func body(content: Content) -> some View {
        content
            .onChange(of: spawnRate) { _, newValue in
                gameScene.spawnRate = newValue
            }
            .onChange(of: isPaused) { _, newValue in
                gameScene.isPaused_ = newValue
            }
            .onChange(of: manualMode) { _, newValue in
                gameScene.manualSpawnMode = newValue
            }
    }
}

private struct ToolBindings: ViewModifier {
    let selectedTool: String
    let ballRadius: Double
    let isMuted: Bool
    let gameScene: GameScene

    func body(content: Content) -> some View {
        content
            .onChange(of: selectedTool) { _, newValue in
                gameScene.drawMode = newValue == "draw"
            }
            .onChange(of: ballRadius) { _, newValue in
                gameScene.ballRadius = CGFloat(newValue)
            }
            .onChange(of: isMuted) { _, newValue in
                gameScene.soundManager.isMuted = newValue
            }
    }
}
