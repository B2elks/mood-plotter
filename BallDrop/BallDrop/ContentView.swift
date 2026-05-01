import SwiftUI

enum Screen: Hashable {
    case home
    case build
    case levelSelect
    case levelGame(Level)
}

struct ContentView: View {
    @State private var screen: Screen = .home
    @StateObject private var progress = ProgressStore()

    var body: some View {
        switch screen {
        case .home:
            HomeScreen(
                onBuild: { screen = .build },
                onPlay: { screen = .levelSelect },
                onResetProgress: { progress.reset() }
            )
        case .build:
            BuildView(onHome: { screen = .home })
        case .levelSelect:
            LevelSelectScreen(
                progress: progress,
                onSelect: { level in screen = .levelGame(level) },
                onHome: { screen = .home }
            )
        case .levelGame(let level):
            LevelGameScreen(
                level: level,
                progress: progress,
                onCompleted: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        }
    }
}
