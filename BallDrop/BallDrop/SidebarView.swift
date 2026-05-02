import SwiftUI

struct SidebarView: View {
    @Binding var selectedTool: String
    @Binding var spawnRate: Double
    @Binding var ballRadius: Double
    @Binding var isPaused: Bool
    @Binding var isMuted: Bool
    @Binding var score: Int
    @Binding var manualMode: Bool
    var onPlaceBlock: (BlockType) -> Void
    var onClearBlocks: () -> Void
    var onResetScore: () -> Void
    var onLaunchBall: () -> Void
    var onDragBlock: (BlockType, CGPoint) -> Void
    var onHome: (() -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let onHome = onHome {
                Button(action: onHome) {
                    Label("Hem", systemImage: "house.fill")
                        .font(.system(size: 13))
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 12)
                .padding(.top, 12)
            }

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
                    blockListRow(type: type, label: label)
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

                Picker("Läge", selection: $manualMode) {
                    Text("Auto").tag(false)
                    Text("Manuell").tag(true)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal)

                if manualMode {
                    Button(action: onLaunchBall) {
                        HStack {
                            Image(systemName: "arrow.up.forward.circle.fill")
                                .font(.system(size: 18))
                            Text("Skjut iväg!")
                                .font(.system(size: 13, weight: .semibold))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                        .background(Color.green)
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal)
                } else {
                    HStack {
                        Text("Hastighet")
                            .font(.system(size: 12))
                        Slider(value: $spawnRate, in: 0.2...5.0, step: 0.1)
                    }
                    .padding(.horizontal)
                }

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
                Text("Drag blå handtag = rotera")
                Text("Högerklick = ta bort")
            }
            .font(.system(size: 10))
            .foregroundColor(.secondary)
            .padding()
        }
        .frame(width: 200)
        #if os(macOS)
        .background(Color(NSColor.windowBackgroundColor))
        #else
        .background(Color(.systemBackground))
        #endif
    }

    @ViewBuilder
    private func blockListRow(type: BlockType, label: String) -> some View {
        if manualMode {
            HStack(spacing: 10) {
                blockIcon(type)
                    .frame(width: 28, height: 28)
                Text(label)
                    .font(.system(size: 13))
                Spacer()
                Image(systemName: "hand.draw")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray.opacity(0.08))
            )
            .padding(.horizontal, 8)
            .gesture(
                DragGesture(coordinateSpace: .global)
                    .onEnded { value in
                        onDragBlock(type, value.location)
                    }
            )
        } else {
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
    }
}
