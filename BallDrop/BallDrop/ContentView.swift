import SwiftUI

enum Screen: Hashable {
    case home
    case build
    case levelSelect
    case levelGame(Level)
    case levelEditor
    case userLevelGame(UserLevel)
}

struct ContentView: View {
    @State private var screen: Screen = .home
    @StateObject private var progress = ProgressStore()
    @StateObject private var userLevels = UserLevelStore()

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
                userLevels: userLevels,
                onSelect: { level in screen = .levelGame(level) },
                onSelectUserLevel: { ul in screen = .userLevelGame(ul) },
                onCreateLevel: { screen = .levelEditor },
                onHome: { screen = .home }
            )
        case .levelGame(let level):
            LevelGameScreen(
                level: level,
                progress: progress,
                onCompleted: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        case .levelEditor:
            LevelEditorScreen(
                userLevels: userLevels,
                onSaved: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        case .userLevelGame(let userLevel):
            LevelGameScreen(
                userLevel: userLevel,
                progress: progress,
                onCompleted: { screen = .levelSelect },
                onCancel: { screen = .levelSelect }
            )
        }
    }
}
