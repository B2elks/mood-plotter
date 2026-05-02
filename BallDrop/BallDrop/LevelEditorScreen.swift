import SwiftUI
import SpriteKit

struct LevelEditorScreen: View {
    @ObservedObject var userLevels: UserLevelStore
    var onSaved: () -> Void
    var onCancel: () -> Void

    @State private var draft: UserLevel = UserLevel.newDraft()
    @State private var sceneFrame: CGRect = .zero
    @State private var gameScene: GameScene = {
        let scene = GameScene(size: CGSize(width: 800, height: 700))
        scene.scaleMode = .resizeFill
        scene.editorMode = true
        return scene
    }()

    var body: some View {
        HStack(spacing: 0) {
            sidebar
                .frame(width: 250)
                .background(Color(white: 0.95))

            ZStack {
                GeometryReader { proxy in
                    spriteHost(proxy: proxy)
                }
            }
        }
    }

    private var sidebar: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("Skapa bana")
                    .font(.system(size: 18, weight: .bold))
                    .padding(.horizontal)
                    .padding(.top, 16)

                nameField
                ballCountField

                Divider()

                Text("DRA UT TILL SCENEN")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(BlockType.allCases, id: \.rawValue) { type in
                    blockDragRow(type)
                }

                editorRowZone
                editorRowSpawn

                Divider()

                Text("EXTRA BLOCK ÅT SPELAREN")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(BlockType.allCases, id: \.rawValue) { type in
                    extraBudgetRow(type)
                }

                Spacer(minLength: 8)

                actionButtons
            }
        }
    }

    private var nameField: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("NAMN").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
            TextField("Min bana", text: $draft.name)
                .textFieldStyle(.roundedBorder)
        }.padding(.horizontal)
    }

    private var ballCountField: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("BOLLAR").font(.system(size: 10, weight: .semibold)).foregroundColor(.secondary)
            Stepper("Antal: \(draft.ballCount)", value: $draft.ballCount, in: 1...30)
                .font(.system(size: 13))
        }.padding(.horizontal)
    }

    private var actionButtons: some View {
        HStack(spacing: 8) {
            Button(action: onCancel) {
                Text("Avbryt")
                    .font(.system(size: 13))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(Color.gray.opacity(0.2))
                    .foregroundColor(.black)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }.buttonStyle(.plain)

            Button(action: saveLevel) {
                Text("Spara")
                    .font(.system(size: 13, weight: .semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(canSave ? Color.green : Color.gray.opacity(0.3))
                    .foregroundColor(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .buttonStyle(.plain)
            .disabled(!canSave)
        }
        .padding(.horizontal)
        .padding(.bottom, 16)
    }

    @ViewBuilder
    private func blockDragRow(_ type: BlockType) -> some View {
        HStack(spacing: 10) {
            blockIcon(type).frame(width: 28, height: 28)
            Text(blockLabel(type)).font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    let scenePos = sceneCoord(from: value.location)
                    let block = BlockNode(type: type)
                    block.position = scenePos
                    gameScene.addChild(block)
                }
        )
    }

    private var editorRowZone: some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(red: 1.0, green: 0.75, blue: 0.20))
                .frame(width: 24, height: 8)
            Text("Score zone").font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    let scenePos = sceneCoord(from: value.location)
                    let edge = nearestEdge(scenePos)
                    let zone = ScoreZone(edge: edge)
                    zone.position = scenePos
                    gameScene.addChild(zone)
                }
        )
    }

    private var editorRowSpawn: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(Color.white)
                .overlay(Circle().stroke(Color.gray, lineWidth: 1))
                .frame(width: 22, height: 22)
            Text("Spawn-punkt").font(.system(size: 13))
            Spacer()
            Image(systemName: "hand.draw").font(.system(size: 11)).foregroundColor(.secondary)
        }
        .padding(.horizontal, 12).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white))
        .padding(.horizontal, 8)
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onEnded { value in
                    guard sceneFrame.contains(value.location) else { return }
                    let scenePos = sceneCoord(from: value.location)
                    gameScene.spawnPointNode?.position = scenePos
                }
        )
    }

    @ViewBuilder
    private func extraBudgetRow(_ type: BlockType) -> some View {
        HStack {
            blockIcon(type).frame(width: 22, height: 22)
            Text(blockLabel(type)).font(.system(size: 12))
            Spacer()
            Stepper(
                "\(draft.extraBudget[type] ?? 0)",
                value: Binding(
                    get: { draft.extraBudget[type] ?? 0 },
                    set: { draft.extraBudget[type] = $0 == 0 ? nil : $0 }
                ),
                in: 0...20
            )
            .labelsHidden()
        }
        .padding(.horizontal)
    }

    private var canSave: Bool {
        !draft.name.trimmingCharacters(in: .whitespaces).isEmpty
            && draft.ballCount >= 1
            && currentZoneCount() >= 1
    }

    private func nearestEdge(_ p: CGPoint) -> ScoreZone.Edge {
        let s = gameScene.size
        let dBottom = p.y
        let dLeft = p.x
        let dRight = s.width - p.x
        let m = min(dBottom, dLeft, dRight)
        if m == dBottom { return .bottom }
        if m == dLeft { return .left }
        return .right
    }

    private func sceneCoord(from globalLocation: CGPoint) -> CGPoint {
        let viewLoc = CGPoint(
            x: globalLocation.x - sceneFrame.origin.x,
            y: globalLocation.y - sceneFrame.origin.y
        )
        return gameScene.convertPoint(fromView: viewLoc)
    }

    private func currentZoneCount() -> Int {
        gameScene.children.compactMap { $0 as? ScoreZone }.count
    }

    private func saveLevel() {
        var saved = draft
        saved.placedBlocks = gameScene.children.compactMap { node in
            guard let bn = node as? BlockNode else { return nil }
            return PlacedBlock(type: bn.blockType, position: bn.position, zRotation: bn.zRotation)
        }
        saved.scoreZones = gameScene.children.compactMap { node in
            guard let zn = node as? ScoreZone else { return nil }
            return PlacedZone(position: zn.position, edge: zn.edge)
        }
        saved.spawnPosition = gameScene.spawnPointNode?.position ?? draft.spawnPosition
        userLevels.save(saved)
        onSaved()
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

    private func blockLabel(_ type: BlockType) -> String {
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
}
