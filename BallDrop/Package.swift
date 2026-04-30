// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "BallDrop",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "BallDrop",
            path: "BallDrop"
        )
    ]
)
