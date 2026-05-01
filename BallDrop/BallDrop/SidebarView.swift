import SwiftUI

struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var ballRadius: Double
    @Binding var isPaused: Bool
    @Binding var score: Int
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void
    var onResetScore: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Ball Drop")
                .font(.system(size: 18, weight: .bold))
                .padding(.horizontal)
                .padding(.top, 16)

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("BLOCKS")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                ForEach(Array(zip(BlockType.allCases, ["Horisontell", "Vertikal", "Diagonal", "Cirkel", "Triangel", "Studsmatta", "Katapult"])), id: \.0.rawValue) { type, label in
                    Button(action: { onPlaceBlock(type) }) {
                        HStack(spacing: 10) {
                            blockIcon(type)
                                .frame(width: 28, height: 28)
                            Text(label)
                                .font(.system(size: 13))
                            Spacer()
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(
                            RoundedRectangle(cornerRadius: 6)
                                .fill(Color.gray.opacity(0.08))
                        )
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 8)
                }

                Button(action: { selectedTool = selectedTool == "draw" ? "pointer" : "draw" }) {
                    HStack(spacing: 10) {
                        Image(systemName: "pencil.line")
                            .frame(width: 28, height: 28)
                        Text("Rita fritt")
                            .font(.system(size: 13))
                        Spacer()
                        if selectedTool == "draw" {
                            Image(systemName: "checkmark")
                                .foregroundColor(.blue)
                        }
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(selectedTool == "draw" ? Color.blue.opacity(0.1) : Color.gray.opacity(0.08))
                    )
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 8)
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("POÄNG")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                Text("\(score)")
                    .font(.system(size: 24, weight: .bold))
                    .padding(.horizontal)

                Button(action: onResetScore) {
                    Label("Nollställ poäng", systemImage: "arrow.counterclockwise")
                        .font(.system(size: 12))
                        .frame(maxWidth: .infinity)
                }
                .controlSize(.small)
                .padding(.horizontal)
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("KONTROLL")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)

                HStack {
                    Text("Hastighet")
                        .font(.system(size: 12))
                    Slider(value: $spawnRate, in: 0.2...5.0, step: 0.1)
                }
                .padding(.horizontal)

                HStack {
                    Text("Storlek")
                        .font(.system(size: 12))
                    Slider(value: $ballRadius, in: 4...30, step: 1)
                }
                .padding(.horizontal)

                HStack(spacing: 8) {
                    Button(action: { isPaused.toggle() }) {
                        Label(isPaused ? "Starta" : "Pausa",
                              systemImage: isPaused ? "play.fill" : "pause.fill")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)

                    Button(action: onClearBlocks) {
                        Label("Rensa", systemImage: "trash")
                            .font(.system(size: 12))
                            .frame(maxWidth: .infinity)
                    }
                    .controlSize(.small)
                }
                .padding(.horizontal)
            }

            Spacer()

            VStack(alignment: .leading, spacing: 2) {
                Text("Space = pausa")
                Text("C = rensa block")
                Text("+/- = hastighet")
                Text("Scroll = rotera block")
                Text("Högerklick = ta bort")
            }
            .font(.system(size: 10))
            .foregroundColor(.secondary)
            .padding()
        }
        .frame(width: 200)
        .background(Color(NSColor.windowBackgroundColor))
    }

    @ViewBuilder
    private func blockIcon(_ type: BlockType) -> some View {
        switch type {
        case .horizontalRect:
            RoundedRectangle(cornerRadius: 2)
                .fill(Color.gray.opacity(0.4))
                .frame(width: 24, height: 6)
        case .verticalRect:
            RoundedRectangle(cornerRadius: 2)
                .fill(Color.gray.opacity(0.4))
                .frame(width: 6, height: 24)
        case .diagonal:
            RoundedRectangle(cornerRadius: 2)
                .fill(Color.gray.opacity(0.4))
                .frame(width: 24, height: 6)
                .rotationEffect(.degrees(-30))
        case .circle:
            Circle()
                .fill(Color.gray.opacity(0.4))
                .frame(width: 18, height: 18)
        case .triangle:
            Triangle()
                .fill(Color.gray.opacity(0.4))
                .frame(width: 20, height: 18)
        case .trampoline:
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(red: 0.40, green: 0.78, blue: 0.45))
                .frame(width: 24, height: 6)
        case .catapult:
            ZStack {
                RoundedRectangle(cornerRadius: 2)
                    .fill(Color(red: 1.0, green: 0.55, blue: 0.20))
                    .frame(width: 24, height: 6)
                Triangle()
                    .fill(Color.white)
                    .frame(width: 6, height: 5)
                    .offset(y: -1)
            }
        }
    }
}

struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        Path { p in
            p.move(to: CGPoint(x: rect.midX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
            p.closeSubpath()
        }
    }
}
