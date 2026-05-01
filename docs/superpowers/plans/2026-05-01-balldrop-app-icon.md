# BallDrop — App-ikon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skapa en programmatiskt-genererad 1024×1024 PNG app-ikon för BallDrop iOS, baserad på spelets sky-blue → mint gradient med en spawn-point och fyra fallande färgade bollar. Skriptet committas så designen är reproducerbar.

**Architecture:** Ett fristående Swift-skript (`BallDrop/scripts/GenerateAppIcon.swift`) använder Foundation + CoreGraphics + ImageIO för att rita en `CGContext`, fylla en gradient, lägga på spawn-point och bollar, och skriva resultatet till `AppIcon.appiconset/Icon-1024.png`. Inga externa beroenden. `Contents.json` i asset-katalogen uppdateras med `"filename": "Icon-1024.png"` så Xcode plockar upp filen.

**Tech Stack:** Swift 5.9, Foundation, CoreGraphics, ImageIO, macOS 14+ (för att köra skriptet).

**Spec:** `docs/superpowers/specs/2026-05-01-balldrop-app-icon-design.md`

**Notes om testning:** Inga unit-tester. Verifiering sker via:
1. PNG existerar och är 1024×1024 (`sips -g pixelWidth -g pixelHeight`).
2. iOS-bygget i Xcode lyckas och Asset-katalogen kompileras utan varningar.
3. Visuell granskning av PNG (ej automatiserad).

---

## File Structure

**Filer att skapa:**
- `BallDrop/scripts/GenerateAppIcon.swift` — fristående Swift-skript som genererar PNG.

**Filer att modifiera:**
- `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Contents.json` — lägg till `"filename": "Icon-1024.png"` på image-entryn.

**Filer att skapa via skriptkörning (binärt artifact):**
- `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png` — den genererade ikonen, committas till git.

---

## Task 1: Skapa generator-skriptet och rendrera PNG

**Files:**
- Create: `BallDrop/scripts/GenerateAppIcon.swift`
- Create (via script): `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png`
- Modify: `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Contents.json`

- [ ] **Step 1: Skapa scripts-katalogen**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
mkdir -p scripts
```

- [ ] **Step 2: Skapa Swift-skriptet**

Skapa filen `BallDrop/scripts/GenerateAppIcon.swift` med följande innehåll:

```swift
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
```

- [ ] **Step 3: Kör skriptet och rendrera PNG**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift scripts/GenerateAppIcon.swift
```

Förväntat output: `Wrote /Users/b2/Documents/Proj/LLM/BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png`

- [ ] **Step 4: Verifiera PNG-storlek**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
sips -g pixelWidth -g pixelHeight BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png 2>&1 | tail -3
```

Förväntat: `pixelWidth: 1024` och `pixelHeight: 1024`.

- [ ] **Step 5: Uppdatera Contents.json**

Läs `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Contents.json`. Ersätt hela innehållet med:

```json
{
  "images" : [
    {
      "filename" : "Icon-1024.png",
      "idiom" : "universal",
      "platform" : "ios",
      "size" : "1024x1024"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}
```

(Enda skillnaden mot tidigare: `"filename": "Icon-1024.png"` är tillagd.)

- [ ] **Step 6: Bygg iOS-target i Xcode för att verifiera asset-katalogen**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -target BallDrop-iOS -sdk iphoneos26.1 CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO build 2>&1 | tail -5
```

Förväntat: `** BUILD SUCCEEDED **` utan asset-relaterade varningar.

- [ ] **Step 7: Bygg Mac-target också för att vara säker på att inget gick sönder**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -3
```

Förväntat: `Build complete!`.

- [ ] **Step 8: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/scripts/GenerateAppIcon.swift BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Contents.json
git commit -m "feat: add programmatically generated app icon"
```

---

## Verifiering mot specen

- [x] 1024×1024 sRGB PNG utan alpha — Step 2 (CGContext med `noneSkipLast` bitmapInfo).
- [x] Sky-blue → mint gradient — Step 2 (gradient mellan `(0.53, 0.81, 0.92)` och `(0.60, 0.85, 0.78)`).
- [x] Spawn-point centrerat ~25 % från toppen, vit cirkel + arrow — Step 2.
- [x] Fyra fallande bollar med varierande storlek + spelets färger — Step 2.
- [x] Genererad via Swift-skript som committas — Step 2.
- [x] PNG sparad till `AppIcon.appiconset/Icon-1024.png` — Step 3.
- [x] Contents.json uppdaterad med filename — Step 5.
- [x] Inga unit-tester (out of scope per spec) — bekräftat.

---

## Rollback om något går fel

En enda commit. För att rulla tillbaka: `git reset --hard HEAD~1`. Skriptet kan köras om för att rendrera PNG på nytt.
