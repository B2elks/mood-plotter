import SwiftUI

enum Tier: String, Codable, CaseIterable, Identifiable {
    case bronze, silver, gold

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .bronze: return "Brons"
        case .silver: return "Silver"
        case .gold:   return "Guld"
        }
    }
}

struct Level: Identifiable, Hashable {
    let id: String
    let tier: Tier
    let name: String
    let blockBudget: [BlockType: Int]
    let ballCount: Int
    let scoreTarget: Int
}

extension Level {
    static let all: [Level] = [
        Level(id: "b1", tier: .bronze, name: "Första bollen",
              blockBudget: [.horizontalRect: 3],
              ballCount: 3, scoreTarget: 1),
        Level(id: "b2", tier: .bronze, name: "Trappa",
              blockBudget: [.horizontalRect: 4],
              ballCount: 5, scoreTarget: 2),
        Level(id: "b3", tier: .bronze, name: "Korridor",
              blockBudget: [.horizontalRect: 2, .verticalRect: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s1", tier: .silver, name: "Diagonalen",
              blockBudget: [.horizontalRect: 2, .diagonal: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s2", tier: .silver, name: "Studsa",
              blockBudget: [.diagonal: 3, .circle: 2],
              ballCount: 6, scoreTarget: 3),
        Level(id: "s3", tier: .silver, name: "Triangelpussel",
              blockBudget: [.horizontalRect: 2, .triangle: 3, .circle: 1],
              ballCount: 7, scoreTarget: 4),
        Level(id: "g1", tier: .gold, name: "Studsmatta",
              blockBudget: [.horizontalRect: 2, .trampoline: 1],
              ballCount: 5, scoreTarget: 3),
        Level(id: "g2", tier: .gold, name: "Katapulten",
              blockBudget: [.horizontalRect: 2, .catapult: 1],
              ballCount: 5, scoreTarget: 4),
        Level(id: "g3", tier: .gold, name: "Frihandsmästaren",
              blockBudget: [.horizontalRect: 1, .trampoline: 1, .catapult: 1],
              ballCount: 8, scoreTarget: 5),
    ]

    static func levels(in tier: Tier) -> [Level] {
        all.filter { $0.tier == tier }
    }
}
