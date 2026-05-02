import SwiftUI
import SpriteKit

struct LevelGameScreen: View {
    let level: Level?
    let userLevel: UserLevel?
    @ObservedObject var progress: ProgressStore
    var onCompleted: () -> Void
    var onCancel: () -> Void

    @State private var ballsRemaining: Int
    @State private var blocksRemaining: [BlockType: Int]
    @State private var score: Int = 0
    @State private var outcome: Outcome? = nil
    @State private var isMuted: Bool = false
    @State private var gameScene: GameScene
    @State private var dragState: DragState? = nil
    @State private var sceneFrame: CGRect = .zero

    enum Outcome {
        case won
        case lost
    }

    struct DragState {
        let type: BlockType
        var globalLocation: CGPoint
    }

    init(level: Level,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = level
        self.userLevel = nil
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: level.ballCount)
        self._blocksRemaining = State(initialValue: level.blockBudget)
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        self._gameScene = State(initialValue: scene)
    }

    init(userLevel: UserLevel,
         progress: ProgressStore,
         onCompleted: @escaping () -> Void,
         onCancel: @escaping () -> Void) {
        self.level = nil
        self.userLevel = userLevel
        self.progress = progress
        self.onCompleted = onCompleted
        self.onCancel = onCancel
        self._ballsRemaining = State(initialValue: userLevel.ballCount)
        self._blocksRemaining = State(initialValue: userLevel.extraBudget)
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
                GeometryReader { proxy in
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
                    let id = level?.id ?? userLevel?.id ?? ""
                    if !id.isEmpty { progress.markCompleted(id) }
                }
            }
            gameScene.onLevelFailed = {
                Task { @MainActor in outcome = .lost }
            }
            if let lvl = level {
                gameScene.startLevel(LevelConfig(
                    blockBudget: lvl.blockBudget,
                    ballCount: lvl.ballCount,
                    scoreTarget: lvl.scoreTarget
                ))
            } else if let ul = userLevel {
                gameScene.loadUserLevel(ul)
            }
        }
        .onChange(of: isMuted) { _, newValue in
            gameScene.soundManager.isMuted = newValue
        }
        .overlay { ghostOverlay }
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
                Text(headerTitle)
                    .font(.system(size: 14, weight: .bold))
                Text(headerSubtitle)
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

            Button(action: { gameScene.launchBall() }) {
                HStack {
                    Image(systemName: "arrow.up.forward.circle.fill")
                        .font(.system(size: 20))
                    Text("Skjut iväg! (\(ballsRemaining) kvar)")
                        .font(.system(size: 14, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(ballsRemaining > 0 ? Color.green : Color.gray.opacity(0.3))
                .foregroundColor(.white)
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }
            .buttonStyle(.plain)
            .disabled(ballsRemaining == 0)
            .padding(.horizontal)

            Divider()

            VStack(alignment: .leading, spacing: 6) {
                Text("BLOCK — DRA UT")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(orderedBlockTypes, id: \.rawValue) { type in
                    blockRow(type)
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

    @ViewBuilder
    private func blockRow(_ type: BlockType) -> some View {
        let count = blocksRemaining[type] ?? 0
        let enabled = count > 0
        HStack(spacing: 10) {
            blockIcon(type)
                .frame(width: 28, height: 28)
            Text(label(for: type))
                .font(.system(size: 13))
            Spacer()
            Text("\(count)")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(enabled ? .blue : .secondary)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.white)
        )
        .opacity(enabled ? 1.0 : 0.4)
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onChanged { value in
                    guard enabled else { return }
                    dragState = DragState(type: type, globalLocation: value.location)
                }
                .onEnded { value in
                    guard enabled else { return }
                    handleDrop(at: value.location, type: type)
                    dragState = nil
                }
        )
    }

    private func handleDrop(at globalLocation: CGPoint, type: BlockType) {
        guard sceneFrame.contains(globalLocation) else { return }
        guard (blocksRemaining[type] ?? 0) > 0 else { return }
        let viewLoc = CGPoint(
            x: globalLocation.x - sceneFrame.origin.x,
            y: globalLocation.y - sceneFrame.origin.y
        )
        let sceneLoc = gameScene.convertPoint(fromView: viewLoc)
        gameScene.addBlock(type: type, at: sceneLoc)
    }

    @ViewBuilder
    private var ghostOverlay: some View {
        if let drag = dragState {
            blockIcon(drag.type)
                .scaleEffect(2.5)
                .opacity(0.7)
                .position(x: drag.globalLocation.x, y: drag.globalLocation.y)
                .ignoresSafeArea()
                .allowsHitTesting(false)
        }
    }

    private var orderedBlockTypes: [BlockType] {
        let budget = level?.blockBudget ?? userLevel?.extraBudget ?? [:]
        return BlockType.allCases.filter { budget[$0] != nil }
    }

    private var headerTitle: String {
        if let l = level { return "\(l.tier.displayName) — \(l.name)" }
        if let u = userLevel { return u.name }
        return ""
    }

    private var headerSubtitle: String {
        if let l = level { return "Mål: \(l.scoreTarget)p" }
        if let u = userLevel { return "Mål: \(u.scoreZones.count) zoner" }
        return ""
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
        if let lvl = level {
            gameScene.startLevel(LevelConfig(
                blockBudget: lvl.blockBudget,
                ballCount: lvl.ballCount,
                scoreTarget: lvl.scoreTarget
            ))
        } else if let ul = userLevel {
            gameScene.loadUserLevel(ul)
        }
    }
}
