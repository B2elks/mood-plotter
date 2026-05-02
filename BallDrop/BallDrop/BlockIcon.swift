import SwiftUI

@ViewBuilder
func blockIcon(_ type: BlockType) -> some View {
    switch type {
    case .horizontalRect:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 24, height: 6)
    case .verticalRect:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 6, height: 24)
    case .diagonal:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color.gray.opacity(0.4))
            .frame(width: 24, height: 6)
            .rotationEffect(.degrees(-30))
    case .circle:
        Circle()
            .fill(Color.gray.opacity(0.4))
            .frame(width: 18, height: 18)
    case .triangle:
        Triangle()
            .fill(Color.gray.opacity(0.4))
            .frame(width: 20, height: 18)
    case .trampoline:
        RoundedRectangle(cornerRadius: 2)
            .fill(Color(red: 0.40, green: 0.78, blue: 0.45))
            .frame(width: 24, height: 6)
    case .catapult:
        ZStack {
            RoundedRectangle(cornerRadius: 2)
                .fill(Color(red: 1.0, green: 0.55, blue: 0.20))
                .frame(width: 24, height: 6)
            Triangle()
                .fill(Color.white)
                .frame(width: 6, height: 5)
                .offset(y: -1)
        }
    }
}

struct Triangle: Shape {
    func path(in rect: CGRect) -> Path {
        Path { p in
            p.move(to: CGPoint(x: rect.midX, y: rect.minY))
            p.addLine(to: CGPoint(x: rect.minX, y: rect.maxY))
            p.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))
            p.closeSubpath()
        }
    }
}
