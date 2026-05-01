import SwiftUI
import SpriteKit

struct LevelGameScreen: View {
    let level: Level
    @ObservedObject var progress: ProgressStore
    var onCompleted: () -> Void
    var onCancel: () -> Void

    @State private var ballsRemaining: Int
    @State private var blocksRemaining: [BlockType: Int]
    @State private var score: Int = 0
    @State private var outcome: Outcome? = nil
    @State private var isMuted: Bool = false
    @State private var gameScene: GameScene

    enum Outcome {
        case won
        case lost
    }

    init(level: Level,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = level
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: level.ballCount)
        self._blocksRemaining = State(initialValue: level.blockBudget)
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        self._gameScene = State(initialValue: scene)
    }

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 220)
                .background(Color(white: 0.95))

            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(gameBackground)
                #else
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(gameBackground)
                #endif

                Text("\(score)")
                    .font(.system(size: 48, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.4), radius: 4, x: 0, y: 2)
                    .padding(.top, 16)
                    .padding(.trailing, 24)
            }
        }
        .onAppear {
            gameScene.onScoreChanged = { new in
                Task { @MainActor in score = new }
            }
            gameScene.onBallsRemainingChanged = { remaining in
                Task { @MainActor in ballsRemaining = remaining }
            }
            gameScene.onBlocksRemainingChanged = { remaining in
                Task { @MainActor in blocksRemaining = remaining }
            }
            gameScene.onLevelCompleted = {
                Task { @MainActor in
                    outcome = .won
                    progress.markCompleted(level.id)
                }
            }
            gameScene.onLevelFailed = {
                Task { @MainActor in outcome = .lost }
            }
            gameScene.startLevel(LevelConfig(
                blockBudget: level.blockBudget,
                ballCount: level.ballCount,
                scoreTarget: level.scoreTarget
            ))
        }
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
        .overlay {
            if let outcome = outcome {
                outcomeModal(outcome)
            }
        }
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

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(level.tier.displayName) — \(level.name)")
                    .font(.system(size: 14, weight: .bold))
                Text("Mål: \(level.scoreTarget)p")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal)
            .padding(.top, 16)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BOLLAR KVAR")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                Text("\(ballsRemaining)")
                    .font(.system(size: 28, weight: .bold))
            }
            .padding(.horizontal)

            VStack(alignment: .leading, spacing: 6) {
                Text("SCORE")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                Text("\(score)")
                    .font(.system(size: 28, weight: .bold))
            }
            .padding(.horizontal)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BLOCK")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(orderedBlockTypes, id: \.rawValue) { type in
                    let count = blocksRemaining[type] ?? 0
                    Button(action: { placeBlock(type) }) {
                        HStack {
                            Text(label(for: type))
                                .font(.system(size: 13))
                            Spacer()
                            Text("\(count)")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(count > 0 ? .blue : .secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(Color.gray.opacity(count > 0 ? 0.08 : 0.04))
                        )
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                    .disabled(count == 0)
                }
            }

            Spacer()

            Button(action: onCancel) {
                Label("Avbryt", systemImage: "xmark")
                    .font(.system(size: 13))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.red.opacity(0.15))
                    .foregroundColor(.red)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
            .padding(.horizontal)
            .padding(.bottom, 16)
        }
    }

    private var orderedBlockTypes: [BlockType] {
        BlockType.allCases.filter { level.blockBudget[$0] != nil }
    }

    private func label(for type: BlockType) -> String {
        switch type {
        case .horizontalRect: return "Horisontell"
        case .verticalRect:   return "Vertikal"
        case .diagonal:       return "Diagonal"
        case .circle:         return "Cirkel"
        case .triangle:       return "Triangel"
        case .trampoline:     return "Studsmatta"
        case .catapult:       return "Katapult"
        }
    }

    private func placeBlock(_ type: BlockType) {
        gameScene.addBlock(type: type,
            at: CGPoint(x: gameScene.size.width / 2, y: gameScene.size.height / 2))
    }

    @ViewBuilder
    private func outcomeModal(_ outcome: Outcome) -> some View {
        ZStack {
            Color.black.opacity(0.5).ignoresSafeArea()
            VStack(spacing: 20) {
                Text(outcome == .won ? "Bana klarad!" : "Försök igen")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                Text(outcome == .won ? "🎉" : "😅")
                    .font(.system(size: 56))
                HStack(spacing: 12) {
                    Button(action: { onCancel() }) {
                        Text("Tillbaka")
                            .font(.system(size: 16, weight: .medium))
                            .frame(width: 110, height: 44)
                            .background(Color.gray.opacity(0.2))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)

                    if outcome == .won {
                        Button(action: { onCompleted() }) {
                            Text("Vidare")
                                .font(.system(size: 16, weight: .semibold))
                                .frame(width: 110, height: 44)
                                .background(Color.green)
                                .foregroundColor(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    } else {
                        Button(action: { restartLevel() }) {
                            Text("Försök igen")
                                .font(.system(size: 16, weight: .semibold))
                                .frame(width: 110, height: 44)
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(28)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
    }

    private func restartLevel() {
        outcome = nil
        gameScene.startLevel(LevelConfig(
            blockBudget: level.blockBudget,
            ballCount: level.ballCount,
            scoreTarget: level.scoreTarget
        ))
    }
}
