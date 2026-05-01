#!/usr/bin/env swift

import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

let size: CGFloat = 1024
let outputURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    .appendingPathComponent("BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png")

let colorSpace = CGColorSpace(name: CGColorSpace.sRGB)!

guard let ctx = CGContext(
    data: nil,
    width: Int(size),
    height: Int(size),
    bitsPerComponent: 8,
    bytesPerRow: 0,
    space: colorSpace,
    bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
) else {
    print("Failed to create CGContext")
    exit(1)
}

// Background gradient: sky-blue (top) → mint (bottom).
// CoreGraphics origin is bottom-left, so the "top" color is at endY (size).
let gradientColors = [
    CGColor(colorSpace: colorSpace, components: [0.60, 0.85, 0.78, 1.0])!, // mint at bottom
    CGColor(colorSpace: colorSpace, components: [0.53, 0.81, 0.92, 1.0])!  // sky at top
] as CFArray
let gradient = CGGradient(colorsSpace: colorSpace, colors: gradientColors, locations: [0.0, 1.0])!
ctx.drawLinearGradient(
    gradient,
    start: CGPoint(x: size / 2, y: 0),
    end: CGPoint(x: size / 2, y: size),
    options: []
)

// Spawn-point: white circle + small downward arrow.
// Centered horizontally, ~25% from the top.
let spawnCenter = CGPoint(x: size / 2, y: size - 256)  // y from bottom
let spawnRadius: CGFloat = 80

ctx.setFillColor(CGColor(colorSpace: colorSpace, components: [1.0, 1.0, 1.0, 0.6])!)
ctx.fillEllipse(in: CGRect(
    x: spawnCenter.x - spawnRadius,
    y: spawnCenter.y - spawnRadius,
    width: spawnRadius * 2,
    height: spawnRadius * 2
))
ctx.setStrokeColor(CGColor(colorSpace: colorSpace, components: [1.0, 1.0, 1.0, 1.0])!)
ctx.setLineWidth(8)
ctx.strokeEllipse(in: CGRect(
    x: spawnCenter.x - spawnRadius,
    y: spawnCenter.y - spawnRadius,
    width: spawnRadius * 2,
    height: spawnRadius * 2
))

// Arrow under the spawn-point (lines forming a downward chevron).
ctx.setLineCap(.round)
ctx.setLineWidth(8)
let arrowTip = CGPoint(x: spawnCenter.x, y: spawnCenter.y - spawnRadius - 22)
let arrowLeft = CGPoint(x: spawnCenter.x - 22, y: spawnCenter.y - spawnRadius + 8)
let arrowRight = CGPoint(x: spawnCenter.x + 22, y: spawnCenter.y - spawnRadius + 8)
ctx.move(to: arrowLeft)
ctx.addLine(to: arrowTip)
ctx.addLine(to: arrowRight)
ctx.strokePath()

// Four falling balls — graduated in size, alternating slightly off-center to suggest motion.
struct Ball {
    let position: CGPoint
    let radius: CGFloat
    let color: [CGFloat] // RGBA
}

let balls: [Ball] = [
    Ball(position: CGPoint(x: size / 2,        y: 600), radius: 30, color: [1.0, 0.42, 0.54, 1.0]), // pink
    Ball(position: CGPoint(x: size / 2 - 32,   y: 460), radius: 40, color: [1.0, 0.70, 0.28, 1.0]), // orange
    Ball(position: CGPoint(x: size / 2 + 8,    y: 290), radius: 50, color: [0.53, 0.84, 0.55, 1.0]), // green
    Ball(position: CGPoint(x: size / 2 - 16,   y: 110), radius: 60, color: [0.70, 0.53, 0.87, 1.0]), // purple
]

for ball in balls {
    let rect = CGRect(
        x: ball.position.x - ball.radius,
        y: ball.position.y - ball.radius,
        width: ball.radius * 2,
        height: ball.radius * 2
    )
    ctx.setFillColor(CGColor(colorSpace: colorSpace, components: ball.color)!)
    ctx.fillEllipse(in: rect)
    ctx.setStrokeColor(CGColor(colorSpace: colorSpace, components: [1.0, 1.0, 1.0, 1.0])!)
    ctx.setLineWidth(6)
    ctx.strokeEllipse(in: rect)
}

// Export as PNG.
guard let cgImage = ctx.makeImage() else {
    print("Failed to create CGImage")
    exit(1)
}

guard let dest = CGImageDestinationCreateWithURL(
    outputURL as CFURL,
    UTType.png.identifier as CFString,
    1,
    nil
) else {
    print("Failed to create CGImageDestination at \(outputURL.path)")
    exit(1)
}

CGImageDestinationAddImage(dest, cgImage, nil)
guard CGImageDestinationFinalize(dest) else {
    print("Failed to write PNG")
    exit(1)
}

print("Wrote \(outputURL.path)")
