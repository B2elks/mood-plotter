import Foundation
import Combine
import CoreGraphics

struct PlacedBlock: Codable, Hashable {
    let type: BlockType
    let position: CGPoint
    let zRotation: CGFloat
}

struct PlacedZone: Codable, Hashable {
    let position: CGPoint
    let edge: ScoreZone.Edge
}

struct UserLevel: Identifiable, Codable, Hashable {
    let id: String
    var name: String
    let createdAt: Date
    var placedBlocks: [PlacedBlock]
    var spawnPosition: CGPoint
    var scoreZones: [PlacedZone]
    var extraBudget: [BlockType: Int]
    var ballCount: Int

    static func newDraft() -> UserLevel {
        UserLevel(
            id: UUID().uuidString,
            name: "Min bana",
            createdAt: Date(),
            placedBlocks: [],
            spawnPosition: CGPoint(x: 400, y: 670),
            scoreZones: [],
            extraBudget: [:],
            ballCount: 5
        )
    }
}

final class UserLevelStore: ObservableObject {
    @Published private(set) var levels: [UserLevel] = []

    private let key = "BallDrop.userLevels.v1"
    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        load()
    }

    func save(_ level: UserLevel) {
        if let i = levels.firstIndex(where: { $0.id == level.id }) {
            levels[i] = level
        } else {
            levels.append(level)
        }
        persist()
    }

    func delete(id: String) {
        levels.removeAll { $0.id == id }
        persist()
    }

    private func load() {
        guard let data = defaults.data(forKey: key) else { return }
        if let decoded = try? JSONDecoder().decode([UserLevel].self, from: data) {
            levels = decoded
        }
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(levels) {
            defaults.set(data, forKey: key)
        }
    }
}
