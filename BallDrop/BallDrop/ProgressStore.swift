import Foundation
import Combine

final class ProgressStore: ObservableObject {
    @Published private(set) var completedIds: Set<String>

    private let key = "BallDrop.completedLevels.v1"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let stored = defaults.array(forKey: key) as? [String] {
            self.completedIds = Set(stored)
        } else {
            self.completedIds = []
        }
    }

    func markCompleted(_ id: String) {
        completedIds.insert(id)
        defaults.set(Array(completedIds), forKey: key)
    }

    func reset() {
        completedIds = []
        defaults.removeObject(forKey: key)
    }

    func isCompleted(_ id: String) -> Bool {
        completedIds.contains(id)
    }

    func isUnlocked(tier: Tier) -> Bool {
        switch tier {
        case .bronze:
            return true
        case .silver:
            return Level.levels(in: .bronze).allSatisfy { isCompleted($0.id) }
        case .gold:
            return Level.levels(in: .silver).allSatisfy { isCompleted($0.id) }
        }
    }
}
