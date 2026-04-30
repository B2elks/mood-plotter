import SwiftUI
import SpriteKit

struct ContentView: View {
    @State private var selectedTool: String = "pointer"
    @State private var spawnRate: Double = 1.0
    @State private var isPaused: Bool = false

    var body: some View {
        HStack(spacing: 0) {
            // Sidebar placeholder
            VStack {
                Text("Tools")
                    .font(.headline)
                    .padding()
                Spacer()
            }
            .frame(width: 200)
            .background(Color.white)

            // Game area placeholder
            Rectangle()
                .fill(
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
    }
}
