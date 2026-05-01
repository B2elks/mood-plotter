import SwiftUI

@main
struct BallDropApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
#if os(macOS)
                .frame(minWidth: 900, minHeight: 600)
#endif
        }
#if os(macOS)
        .windowStyle(.titleBar)
        .defaultSize(width: 1100, height: 750)
#endif
    }
}
