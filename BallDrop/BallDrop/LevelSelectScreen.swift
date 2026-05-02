import SwiftUI

struct LevelSelectScreen: View {
    @ObservedObject var progress: ProgressStore
    @ObservedObject var userLevels: UserLevelStore
    var onSelect: (Level) -> Void
    var onSelectUserLevel: (UserLevel) -> Void
    var onCreateLevel: () -> Void
    var onHome: () -> Void

    @State private var pendingDelete: UserLevel? = nil

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.53, green: 0.81, blue: 0.92),
                    Color(red: 0.60, green: 0.85, blue: 0.78)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Button(action: onHome) {
                        Label("Hem", systemImage: "chevron.left")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white)
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Text("Spela")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundColor(.white)

                    Spacer()

                    Color.clear.frame(width: 60)
                }
                .padding()

                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        ForEach(Tier.allCases) { tier in
                            tierSection(tier)
                        }
                        userLevelsSection()
                    }
                    .padding()
                }
            }
        }
        .alert(item: $pendingDelete) { lvl in
            Alert(
                title: Text("Ta bort \"\(lvl.name)\"?"),
                primaryButton: .destructive(Text("Ta bort")) {
                    userLevels.delete(id: lvl.id)
                },
                secondaryButton: .cancel()
            )
        }
    }

    @ViewBuilder
    private func userLevelsSection() -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Mina banor")
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(.white)

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 200), spacing: 12)], spacing: 12) {
                Button(action: onCreateLevel) {
                    VStack(spacing: 8) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 36))
                            .foregroundColor(.blue)
                        Text("Skapa ny")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.black)
                    }
                    .frame(maxWidth: .infinity, minHeight: 72)
                    .padding(12)
                    .background(Color.white.opacity(0.9))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .buttonStyle(.plain)

                ForEach(userLevels.levels) { ul in
                    userLevelCard(ul)
                }
            }
        }
    }

    @ViewBuilder
    private func userLevelCard(_ level: UserLevel) -> some View {
        let completed = progress.isCompleted(level.id)
        Button(action: { onSelectUserLevel(level) }) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(level.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)
                    Spacer()
                    if completed {
                        Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                    } else {
                        Image(systemName: "play.circle.fill").foregroundColor(.blue)
                    }
                }
                Text("\(level.ballCount) bollar → \(level.scoreZones.count) zoner")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .background(Color.white.opacity(0.9))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
        .onLongPressGesture {
            pendingDelete = level
        }
    }

    @ViewBuilder
    private func tierSection(_ tier: Tier) -> some View {
        let unlocked = progress.isUnlocked(tier: tier)
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(tier.displayName)
                    .font(.system(size: 22, weight: .semibold))
                    .foregroundColor(.white)
                if !unlocked {
                    Image(systemName: "lock.fill")
                        .foregroundColor(.white.opacity(0.7))
                }
            }

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 200), spacing: 12)], spacing: 12) {
                ForEach(Level.levels(in: tier)) { level in
                    levelCard(level, unlocked: unlocked)
                }
            }
        }
    }

    @ViewBuilder
    private func levelCard(_ level: Level, unlocked: Bool) -> some View {
        let completed = progress.isCompleted(level.id)
        let canTap = unlocked

        Button(action: { if canTap { onSelect(level) } }) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(level.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)
                    Spacer()
                    statusIcon(completed: completed, unlocked: unlocked)
                }
                Text("\(level.ballCount) bollar → \(level.scoreTarget)p")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 72, alignment: .leading)
            .background(Color.white.opacity(unlocked ? 0.9 : 0.5))
            .clipShape(RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
        .disabled(!canTap)
    }

    @ViewBuilder
    private func statusIcon(completed: Bool, unlocked: Bool) -> some View {
        if !unlocked {
            Image(systemName: "lock.fill").foregroundColor(.gray)
        } else if completed {
            Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
        } else {
            Image(systemName: "play.circle.fill").foregroundColor(.blue)
        }
    }
}
