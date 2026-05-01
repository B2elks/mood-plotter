import SwiftUI

struct HomeScreen: View {
    var onBuild: () -> Void
    var onPlay: () -> Void
    var onResetProgress: () -> Void

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

            VStack(spacing: 32) {
                Spacer()

                Text("BallDrop")
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: .black.opacity(0.3), radius: 6, x: 0, y: 3)

                VStack(spacing: 16) {
                    Button(action: onPlay) {
                        Label("Spela", systemImage: "play.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .frame(width: 220, height: 56)
                            .background(Color.white.opacity(0.85))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)

                    Button(action: onBuild) {
                        Label("Bygg", systemImage: "hammer.fill")
                            .font(.system(size: 22, weight: .semibold))
                            .frame(width: 220, height: 56)
                            .background(Color.white.opacity(0.85))
                            .foregroundColor(.black)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                    .buttonStyle(.plain)
                }

                Spacer()

                Button(action: onResetProgress) {
                    Text("Återställ progress")
                        .font(.system(size: 12))
                        .foregroundColor(.white.opacity(0.7))
                }
                .buttonStyle(.plain)
                .padding(.bottom, 24)
            }
        }
    }
}
