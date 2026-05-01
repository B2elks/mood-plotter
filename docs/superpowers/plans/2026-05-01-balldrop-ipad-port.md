# BallDrop — iPad-port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lägga till en iPad-version av BallDrop som distribueras via TestFlight, där samma SpriteKit-spel-kod fungerar på både macOS (oförändrat `swift run`) och iPadOS (nytt Xcode-projekt med två app-targets).

**Architecture:** Hybrid SPM + Xcode. Existerande `Package.swift` behålls oförändrat för Mac-CLI-bygget. Ett nytt `BallDrop.xcodeproj` (genererat via XcodeGen från `project.yml`) hostar två app-targets (BallDrop-Mac, BallDrop-iOS) som båda inkluderar samma `.swift`-filer i `BallDrop/BallDrop/`. Plattformsspecifik kod separeras med `#if os(macOS)` / `#if os(iOS)` direktiv. Färger byts från `NSColor` till SpriteKit's plattform-neutrala `SKColor`-typealias. Mouse-handlers extraheras till delade helpers; iOS får `touchesBegan/Moved/Ended` + ett `UIViewRepresentable`-wrapper för pinch-rotation och long-press-delete.

**Tech Stack:** Swift 5.9, SpriteKit, SwiftUI, macOS 14+, iPadOS 17+, Xcode 26.1.1, XcodeGen (via Homebrew), Swift Package Manager.

**Spec:** `docs/superpowers/specs/2026-05-01-balldrop-ipad-port-design.md`

**Notes om testning:** Inget XCTest-target. Verifiering sker via `swift build` (Mac) och `xcodebuild` (iOS Simulator). Slutgiltig fysisk-iPad-test är manuell via TestFlight (kräver Xcode GUI för signing — kan inte automatiseras). Subagenter ska aldrig köra `swift run` (öppnar GUI och blockerar).

---

## File Structure

**Filer att modifiera:**
- `BallDrop/BallDrop/BlockNode.swift` — `NSColor` → `SKColor`.
- `BallDrop/BallDrop/GameScene.swift` — `NSColor` → `SKColor`; extrahera `handlePrimaryDown/Dragged/Up` + `rotateBlock(at:by:)` + `removeBlock(at:)`; wrappa befintliga AppKit-overrides i `#if os(macOS)`; lägg till iOS touch-overrides; `import UIKit` på iOS.
- `BallDrop/BallDrop/ScoreZone.swift` — `NSColor` → `SKColor`.
- `BallDrop/BallDrop/SpawnPoint.swift` — `NSColor` → `SKColor`.
- `BallDrop/BallDrop/FreeDrawTool.swift` — `NSColor` → `SKColor`.
- `BallDrop/BallDrop/ContentView.swift` — `#if os(iOS)` SpriteKitView, `#else` SpriteView.

**Nya filer:**
- `BallDrop/BallDrop/iOS/SpriteKitView.swift` — `UIViewRepresentable`-wrapper för iOS, hanterar UIRotationGestureRecognizer + UILongPressGestureRecognizer.
- `BallDrop/BallDrop/iOS/Info.plist` — bundle config för iOS-targeten.
- `BallDrop/BallDrop/iOS/LaunchScreen.storyboard` — tom launch screen.
- `BallDrop/project.yml` — XcodeGen-config för `BallDrop.xcodeproj`.
- `BallDrop/BallDrop.xcodeproj` — genererat av XcodeGen (committeras inte direkt — eller committeras som autogenererat artefakt; vi committar den för enkel klone-and-open).

---

## Task 1: Färgabstraktion (NSColor → SKColor)

**Files:**
- Modify: `BallDrop/BallDrop/BlockNode.swift`
- Modify: `BallDrop/BallDrop/GameScene.swift`
- Modify: `BallDrop/BallDrop/ScoreZone.swift`
- Modify: `BallDrop/BallDrop/SpawnPoint.swift`
- Modify: `BallDrop/BallDrop/FreeDrawTool.swift`

`SpriteKit` definierar `typealias SKColor = NSColor` på macOS och `SKColor = UIColor` på iOS. Initiziern `SKColor(red:green:blue:alpha:)` och statiska egenskaperna (`.white`, `.gray`) finns på båda — så ändringen är ren namn-ersättning.

- [ ] **Step 1: Byt NSColor → SKColor i BlockNode.swift**

I `BallDrop/BallDrop/BlockNode.swift`, ersätt alla förekomster av `NSColor` med `SKColor`. Specifikt:

```swift
// Före:
fillColor = .white
strokeColor = NSColor(white: 0.85, alpha: 1)

// Efter:
fillColor = .white  // .white finns på SKColor — ingen ändring
strokeColor = SKColor(white: 0.85, alpha: 1)
```

Och i alla `.trampoline`/`.catapult`-cases:

```swift
// Före:
fillColor = NSColor(red: 0.40, green: 0.78, blue: 0.45, alpha: 1)
zigzag.strokeColor = NSColor.white.withAlphaComponent(0.85)
fillColor = NSColor(red: 1.0, green: 0.55, blue: 0.20, alpha: 1)
arrow.fillColor = NSColor.white
arrow.strokeColor = NSColor.white

// Efter:
fillColor = SKColor(red: 0.40, green: 0.78, blue: 0.45, alpha: 1)
zigzag.strokeColor = SKColor.white.withAlphaComponent(0.85)
fillColor = SKColor(red: 1.0, green: 0.55, blue: 0.20, alpha: 1)
arrow.fillColor = SKColor.white
arrow.strokeColor = SKColor.white
```

Och i `addRotateHandle`:

```swift
// Före:
line.strokeColor = NSColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.5)
handle.fillColor = NSColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.7)
handle.strokeColor = NSColor.white

// Efter:
line.strokeColor = SKColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.5)
handle.fillColor = SKColor(red: 0.4, green: 0.6, blue: 1.0, alpha: 0.7)
handle.strokeColor = SKColor.white
```

Söka och byt hela filen är säkert — det finns inga AppKit-specifika NSColor-egenskaper som inte finns på UIColor.

- [ ] **Step 2: Byt NSColor → SKColor i GameScene.swift**

I `BallDrop/BallDrop/GameScene.swift`, hitta `spawnBall()`-metoden. Ändra:

```swift
let colors: [NSColor] = [
    NSColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
    NSColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
    NSColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
    NSColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
    NSColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
]
```

till:

```swift
let colors: [SKColor] = [
    SKColor(red: 1.0, green: 0.42, blue: 0.54, alpha: 1),
    SKColor(red: 1.0, green: 0.70, blue: 0.28, alpha: 1),
    SKColor(red: 0.53, green: 0.84, blue: 0.55, alpha: 1),
    SKColor(red: 0.70, green: 0.53, blue: 0.87, alpha: 1),
    SKColor(red: 1.0, green: 0.87, blue: 0.37, alpha: 1),
]
```

- [ ] **Step 3: Byt NSColor → SKColor i ScoreZone.swift**

I `BallDrop/BallDrop/ScoreZone.swift`, ersätt:

```swift
fillColor = NSColor(red: 1.0, green: 0.75, blue: 0.20, alpha: 0.85)
strokeColor = NSColor(red: 1.0, green: 0.85, blue: 0.40, alpha: 1)
```

med:

```swift
fillColor = SKColor(red: 1.0, green: 0.75, blue: 0.20, alpha: 0.85)
strokeColor = SKColor(red: 1.0, green: 0.85, blue: 0.40, alpha: 1)
```

- [ ] **Step 4: Byt NSColor → SKColor i SpawnPoint.swift**

I `BallDrop/BallDrop/SpawnPoint.swift`, ersätt:

```swift
fillColor = NSColor.white.withAlphaComponent(0.6)
```

med:

```swift
fillColor = SKColor.white.withAlphaComponent(0.6)
```

- [ ] **Step 5: Byt NSColor → SKColor i FreeDrawTool.swift**

I `BallDrop/BallDrop/FreeDrawTool.swift`, ersätt:

```swift
previewNode?.strokeColor = NSColor.white.withAlphaComponent(0.5)
```

med:

```swift
previewNode?.strokeColor = SKColor.white.withAlphaComponent(0.5)
```

- [ ] **Step 6: Verifiera att inga `NSColor`-referenser kvarstår**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
grep -rn "NSColor" BallDrop/ 2>&1 | head -20
```

Förväntat: ingen output (tom resultat).

- [ ] **Step 7: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!` utan fel.

- [ ] **Step 8: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/BlockNode.swift BallDrop/BallDrop/GameScene.swift BallDrop/BallDrop/ScoreZone.swift BallDrop/BallDrop/SpawnPoint.swift BallDrop/BallDrop/FreeDrawTool.swift
git commit -m "refactor: replace NSColor with SKColor for cross-platform support"
```

---

## Task 2: GameScene refactor — extract shared input helpers

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

Vi extraherar gemensam logik från `mouseDown/Dragged/Up` till tre privata helpers, samt `rotateBlock` och `removeBlock` som publika metoder. Mac-overrides anropar dessa. Detta lägger grunden för iOS touch-overrides i Task 3.

- [ ] **Step 1: Lägg till handlePrimaryDown/Dragged/Up helpers**

I `BallDrop/BallDrop/GameScene.swift`, INNAN den befintliga `override func mouseDown(with event: NSEvent)` (men efter `didBegin` osv.), lägg till tre nya privata helper-metoder:

```swift
    private func handlePrimaryDown(at location: CGPoint) {
        rotatingNode = nil

        let node = atPoint(location)
        if node.name == "rotateHandle", let block = node.parent {
            rotatingNode = block
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            rotateInitialAngle = atan2(dy, dx)
            rotateInitialZRotation = block.zRotation
            return
        }

        if node.name == "spawnPoint" || node.parent?.name == "spawnPoint" {
            draggedNode = spawnPointNode
            return
        }

        if drawMode {
            freeDrawTool?.beginDraw(at: location)
            return
        }

        if node.name == "block" || node.parent?.name == "block" {
            let block = node.name == "block" ? node : node.parent!
            draggedNode = block
        }
    }

    private func handlePrimaryDragged(at location: CGPoint) {
        if let block = rotatingNode {
            let dx = location.x - block.position.x
            let dy = location.y - block.position.y
            let currentAngle = atan2(dy, dx)
            block.zRotation = rotateInitialZRotation + (currentAngle - rotateInitialAngle)
            return
        }

        if drawMode {
            freeDrawTool?.continueDraw(at: location)
            return
        }

        guard let node = draggedNode else { return }
        node.position = location
    }

    private func handlePrimaryUp() {
        if rotatingNode != nil {
            rotatingNode = nil
            return
        }

        if drawMode {
            if let block = freeDrawTool?.endDraw() {
                addChild(block)
            }
            return
        }
        draggedNode = nil
    }
```

- [ ] **Step 2: Lägg till rotateBlock och removeBlock publika metoder**

I `BallDrop/BallDrop/GameScene.swift`, EFTER `handlePrimaryUp()` (men före `mouseDown`), lägg till:

```swift
    func rotateBlock(at location: CGPoint, by delta: CGFloat) {
        let node = atPoint(location)
        let block: SKNode?
        if node.name == "block" { block = node }
        else if node.parent?.name == "block" { block = node.parent }
        else { block = nil }
        if let block = block {
            block.zRotation += delta
        }
    }

    func removeBlock(at location: CGPoint) {
        let node = atPoint(location)
        if node.name == "block" {
            node.removeFromParent()
        } else if node.parent?.name == "block" {
            node.parent?.removeFromParent()
        }
    }
```

- [ ] **Step 3: Wrappa Mac-overrides i `#if os(macOS)` och tunna ned dem till helpers**

I `BallDrop/BallDrop/GameScene.swift`, ersätt hela blocket från `override func mouseDown(with event: NSEvent)` till slutet av `override func keyDown(with event: NSEvent)` med:

```swift
    #if os(macOS)
    override func mouseDown(with event: NSEvent) {
        handlePrimaryDown(at: event.location(in: self))
    }

    override func mouseDragged(with event: NSEvent) {
        handlePrimaryDragged(at: event.location(in: self))
    }

    override func mouseUp(with event: NSEvent) {
        handlePrimaryUp()
    }

    override func rightMouseDown(with event: NSEvent) {
        removeBlock(at: event.location(in: self))
    }

    override func scrollWheel(with event: NSEvent) {
        rotateBlock(at: event.location(in: self), by: event.deltaY * 0.02)
    }

    override func keyDown(with event: NSEvent) {
        switch event.charactersIgnoringModifiers {
        case " ":
            isPaused_ = !isPaused_
        case "c":
            clearAllBlocks()
        case "+", "=":
            spawnRate = max(0.2, spawnRate - 0.2)
        case "-":
            spawnRate = min(5.0, spawnRate + 0.2)
        default:
            break
        }
    }
    #endif
```

- [ ] **Step 4: Bygg**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`

- [ ] **Step 5: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "refactor: extract shared input helpers; gate AppKit overrides behind #if os(macOS)"
```

---

## Task 3: iOS touch-handlers + UIKit import i GameScene

**Files:**
- Modify: `BallDrop/BallDrop/GameScene.swift`

- [ ] **Step 1: Lägg till `import UIKit` under `#if os(iOS)`**

I `BallDrop/BallDrop/GameScene.swift`, ändra raden:

```swift
import SpriteKit
```

till:

```swift
import SpriteKit
#if os(iOS)
import UIKit
#endif
```

- [ ] **Step 2: Lägg till iOS touch-handlers**

I `BallDrop/BallDrop/GameScene.swift`, EFTER `#endif`-raden från Task 2 (efter Mac-overrides), lägg till:

```swift
    #if os(iOS)
    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first else { return }
        handlePrimaryDown(at: touch.location(in: self))
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first else { return }
        handlePrimaryDragged(at: touch.location(in: self))
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        handlePrimaryUp()
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        handlePrimaryUp()
    }
    #endif
```

- [ ] **Step 3: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!` utan fel. (iOS-koden kompileras inte här eftersom Package.swift bara targetar macOS, men `#if os(iOS)`-blocket parsas och syntaxkollas.)

- [ ] **Step 4: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/GameScene.swift
git commit -m "feat: add iOS touch handlers in GameScene"
```

---

## Task 4: SpriteKitView.swift (iOS UIViewRepresentable)

**Files:**
- Create: `BallDrop/BallDrop/iOS/SpriteKitView.swift`

OBS: filen läggs i en ny `iOS/`-undermapp. Hela innehållet wrappas i `#if os(iOS)` så att Mac-bygget (som inkluderar alla `.swift`-filer i `BallDrop/`) inte ser någon UIKit-kod. (Vi exkluderar `iOS/`-mappen från Mac-targeten i Xcode-projektet i Task 6, men för Package.swift-bygget på Mac räcker det att blocket är tomt.)

- [ ] **Step 1: Skapa iOS-katalogen**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
mkdir -p BallDrop/iOS
```

- [ ] **Step 2: Skapa SpriteKitView.swift**

Skapa filen `BallDrop/BallDrop/iOS/SpriteKitView.swift` med innehåll:

```swift
#if os(iOS)
import SwiftUI
import SpriteKit
import UIKit

struct SpriteKitView: UIViewRepresentable {
    let scene: GameScene

    func makeUIView(context: Context) -> SKView {
        let view = SKView()
        view.allowsTransparency = true
        view.presentScene(scene)

        let rotate = UIRotationGestureRecognizer(target: context.coordinator,
                                                 action: #selector(Coordinator.handleRotate(_:)))
        view.addGestureRecognizer(rotate)

        let longPress = UILongPressGestureRecognizer(target: context.coordinator,
                                                     action: #selector(Coordinator.handleLongPress(_:)))
        longPress.minimumPressDuration = 0.5
        view.addGestureRecognizer(longPress)

        return view
    }

    func updateUIView(_ uiView: SKView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(scene: scene) }

    class Coordinator: NSObject {
        let scene: GameScene
        var lastRotation: CGFloat = 0

        init(scene: GameScene) {
            self.scene = scene
        }

        @objc func handleRotate(_ gr: UIRotationGestureRecognizer) {
            guard let view = gr.view as? SKView else { return }
            let viewLoc = gr.location(in: view)
            let sceneLoc = scene.convertPoint(fromView: viewLoc)
            switch gr.state {
            case .began:
                lastRotation = 0
            case .changed:
                let delta = gr.rotation - lastRotation
                scene.rotateBlock(at: sceneLoc, by: delta)
                lastRotation = gr.rotation
            default:
                break
            }
        }

        @objc func handleLongPress(_ gr: UILongPressGestureRecognizer) {
            guard gr.state == .began,
                  let view = gr.view as? SKView else { return }
            let viewLoc = gr.location(in: view)
            let sceneLoc = scene.convertPoint(fromView: viewLoc)
            scene.removeBlock(at: sceneLoc)
        }
    }
}
#endif
```

- [ ] **Step 3: Bygg på Mac (filen ska vara osynlig för Mac-targeten)**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`. Filen är tom på Mac eftersom hela innehållet är under `#if os(iOS)`.

- [ ] **Step 4: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/iOS/SpriteKitView.swift
git commit -m "feat: add SpriteKitView UIViewRepresentable for iOS gestures"
```

---

## Task 5: ContentView conditional + iOS Info.plist + LaunchScreen

**Files:**
- Modify: `BallDrop/BallDrop/ContentView.swift`
- Create: `BallDrop/BallDrop/iOS/Info.plist`
- Create: `BallDrop/BallDrop/iOS/LaunchScreen.storyboard`

- [ ] **Step 1: Uppdatera ContentView med conditional SpriteView**

I `BallDrop/BallDrop/ContentView.swift`, hitta blocket i `body`:

```swift
            ZStack(alignment: .topTrailing) {
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(
                        LinearGradient(
                            colors: [
                                Color(red: 0.53, green: 0.81, blue: 0.92),
                                Color(red: 0.60, green: 0.85, blue: 0.78)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
```

Ersätt det med:

```swift
            ZStack(alignment: .topTrailing) {
                #if os(iOS)
                SpriteKitView(scene: gameScene)
                    .background(
                        LinearGradient(
                            colors: [
                                Color(red: 0.53, green: 0.81, blue: 0.92),
                                Color(red: 0.60, green: 0.85, blue: 0.78)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                #else
                SpriteView(scene: gameScene, options: [.allowsTransparency])
                    .background(
                        LinearGradient(
                            colors: [
                                Color(red: 0.53, green: 0.81, blue: 0.92),
                                Color(red: 0.60, green: 0.85, blue: 0.78)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                #endif
```

(Resten av ZStack — Text-overlay etc — lämnas oförändrad.)

- [ ] **Step 2: Skapa iOS Info.plist**

Skapa filen `BallDrop/BallDrop/iOS/Info.plist` med innehåll:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    <key>CFBundleDisplayName</key>
    <string>BallDrop</string>
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    <key>CFBundlePackageType</key>
    <string>$(PRODUCT_BUNDLE_PACKAGE_TYPE)</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>UIDeviceFamily</key>
    <array>
        <integer>2</integer>
    </array>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>arm64</string>
    </array>
    <key>UIRequiresFullScreen</key>
    <true/>
    <key>UISupportedInterfaceOrientations~ipad</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
</dict>
</plist>
```

- [ ] **Step 3: Skapa LaunchScreen.storyboard**

Skapa filen `BallDrop/BallDrop/iOS/LaunchScreen.storyboard` med innehåll:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="22154" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" launchScreen="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="01J-lp-oVM">
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="22131"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="EHf-IW-A2E">
            <objects>
                <viewController id="01J-lp-oVM" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="Ze5-6b-2t3">
                        <rect key="frame" x="0.0" y="0.0" width="375" height="667"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <viewLayoutGuide key="safeArea" id="6Tk-OE-BBY"/>
                        <color key="backgroundColor" systemColor="systemBackgroundColor"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="iYj-Kq-Ea1" userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>
    <resources>
        <systemColor name="systemBackgroundColor">
            <color white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/>
        </systemColor>
    </resources>
</document>
```

- [ ] **Step 4: Bygg på Mac**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -10
```

Förväntat: `Build complete!`. ContentView's `#if os(iOS)`-block parsas men kompileras inte på Mac.

- [ ] **Step 5: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/BallDrop/ContentView.swift BallDrop/BallDrop/iOS/Info.plist BallDrop/BallDrop/iOS/LaunchScreen.storyboard
git commit -m "feat: add iOS Info.plist + LaunchScreen + ContentView conditional"
```

---

## Task 6: Xcode-projekt via XcodeGen

**Files:**
- Create: `BallDrop/project.yml`
- Create: `BallDrop/BallDrop.xcodeproj/...` (genererad)

XcodeGen läser `project.yml` och producerar en `.xcodeproj`. Det är reproducerbart och granskbart i git.

- [ ] **Step 1: Installera XcodeGen om det saknas**

Kontrollera om `xcodegen` finns:

```bash
command -v xcodegen
```

Om det inte finns:

```bash
brew install xcodegen
```

Om Homebrew inte är installerat — escalate till user (kräver manuell installation, kan inte automatiseras).

- [ ] **Step 2: Skapa project.yml**

Skapa filen `BallDrop/project.yml` med innehåll:

```yaml
name: BallDrop
options:
  bundleIdPrefix: com.b2
  deploymentTarget:
    macOS: "14.0"
    iOS: "17.0"
  createIntermediateGroups: true

settings:
  base:
    SWIFT_VERSION: "5.9"
    MARKETING_VERSION: "1.0"
    CURRENT_PROJECT_VERSION: "1"

targets:
  BallDrop-Mac:
    type: application
    platform: macOS
    sources:
      - path: BallDrop
        excludes:
          - "iOS/**"
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.b2.balldrop.mac
        PRODUCT_NAME: BallDrop
        GENERATE_INFOPLIST_FILE: YES
        INFOPLIST_KEY_NSPrincipalClass: NSApplication
        INFOPLIST_KEY_LSApplicationCategoryType: public.app-category.games
        ENABLE_HARDENED_RUNTIME: YES

  BallDrop-iOS:
    type: application
    platform: iOS
    sources:
      - path: BallDrop
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.b2.balldrop
        PRODUCT_NAME: BallDrop
        INFOPLIST_FILE: BallDrop/iOS/Info.plist
        TARGETED_DEVICE_FAMILY: "2"
        ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon
```

- [ ] **Step 3: Generera Xcode-projektet**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodegen generate 2>&1 | tail -10
```

Förväntat: `Generated project successfully` (eller liknande), och en ny `BallDrop.xcodeproj/`-mapp har skapats.

- [ ] **Step 4: Verifiera Mac-build i Xcode**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -scheme BallDrop-Mac -configuration Debug build 2>&1 | tail -15
```

Förväntat: `BUILD SUCCEEDED`.

- [ ] **Step 5: Verifiera iOS Simulator-build**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
xcodebuild -project BallDrop.xcodeproj -scheme BallDrop-iOS -configuration Debug -destination 'generic/platform=iOS Simulator' build 2>&1 | tail -15
```

Förväntat: `BUILD SUCCEEDED`. Om ett signing-fel dyker upp på Mac-target eller iOS-target, lägg till `CODE_SIGN_IDENTITY=""` `CODE_SIGNING_REQUIRED=NO` `CODE_SIGNING_ALLOWED=NO` flaggor till xcodebuild-anropet — för Simulator behövs ingen signing.

- [ ] **Step 6: Verifiera att swift run fortfarande funkar (Mac)**

Kör från `/Users/b2/Documents/Proj/LLM/BallDrop`:

```bash
swift build 2>&1 | tail -5
```

Förväntat: `Build complete!`.

- [ ] **Step 7: Commit**

Kör från `/Users/b2/Documents/Proj/LLM`:

```bash
git add BallDrop/project.yml BallDrop/BallDrop.xcodeproj
git commit -m "feat: add XcodeGen config + generated BallDrop.xcodeproj for Mac+iOS targets"
```

---

## Task 7: Manuell verifiering + TestFlight-distribution

Detta är inte en subagent-task — den kräver Xcode GUI och App Store Connect. Subagenter ska SKIP detta och rapportera klar efter Task 6.

- [ ] **Step 1: Öppna Xcode-projektet**

```bash
open /Users/b2/Documents/Proj/LLM/BallDrop/BallDrop.xcodeproj
```

- [ ] **Step 2: Konfigurera signing för iOS-target**

I Xcode:
1. Välj `BallDrop-iOS`-target i projektnavigatorn.
2. Gå till "Signing & Capabilities"-fliken.
3. Bocka i "Automatically manage signing".
4. Välj ditt ADP Team i "Team"-dropdownen.
5. Verifiera att Bundle Identifier är `com.b2.balldrop` (justera om upptaget i App Store Connect).

- [ ] **Step 3: Kör i Simulator för snabb-verifiering**

I Xcode:
1. Välj scheme "BallDrop-iOS".
2. Välj device: t.ex. "iPad Pro (12.9-inch)".
3. Cmd+R.
4. Appen startar i simulator. Verifiera:
   - Sidopanel syns till vänster med alla knappar.
   - Bollar börjar spawna automatiskt.
   - Tap på t.ex. "Studsmatta" → grön rektangel placeras.
   - Tap & drag på blocket → flyttas.
   - Tap & drag på handtaget → roterar.
   - Två-finger-rotation över ett block → roterar.
   - Long-press på ett block → tas bort.
   - Slidrar och knappar i sidopanelen reagerar på touch.
   - Score-overlay i övre högra hörnet uppdateras vid zon-träff.

- [ ] **Step 4: Archive för App Store-distribution**

I Xcode:
1. Välj scheme "BallDrop-iOS".
2. Välj device "Any iOS Device (arm64)" (inte simulator).
3. **Product → Archive**.
4. Vänta tills archive är klar (1-3 minuter).
5. Organizer-fönstret öppnas automatiskt.

- [ ] **Step 5: Distribuera till TestFlight**

I Organizer:
1. Välj senaste archive.
2. Klicka **Distribute App**.
3. Välj **App Store Connect** → **Upload**.
4. Bekräfta default-options för signing och stripping.
5. Upload — väntar några minuter.
6. När klart, gå till [App Store Connect](https://appstoreconnect.apple.com).
7. TestFlight-fliken: bygget bör visas inom 5-15 minuter (efter Apple-bearbetning).
8. När bygget är "Ready to Test", lägg till dig själv som intern testare.

- [ ] **Step 6: Installera på iPad via TestFlight**

På iPaden:
1. Installera **TestFlight** från App Store om inte redan installerad.
2. Logga in med samma Apple ID som ADP.
3. Hitta BallDrop i listan över tillgängliga appar.
4. Tryck "Install".
5. Öppna BallDrop-appen.
6. Verifiera att alla touch-gester och spelmekanik fungerar (samma checklist som Step 3).

- [ ] **Step 7: Stäng av eventuell körning på Mac**

Om Mac-versionen kör fortfarande från `swift run`:
```bash
pkill -f ".build/arm64-apple-macosx/debug/BallDrop"
```

---

## Verifiering mot specen

- [x] Hybrid Package.swift + Xcode.xcodeproj — Task 6
- [x] NSColor → SKColor genom hela kodbasen — Task 1
- [x] handlePrimaryDown/Dragged/Up helpers + extracted rotateBlock/removeBlock — Task 2
- [x] Mac-overrides under #if os(macOS) — Task 2 step 3
- [x] iOS touch-overrides under #if os(iOS) — Task 3 step 2
- [x] import UIKit på iOS — Task 3 step 1
- [x] SpriteKitView UIViewRepresentable med UIRotationGestureRecognizer + UILongPressGestureRecognizer — Task 4
- [x] ContentView conditional SpriteView vs SpriteKitView — Task 5 step 1
- [x] iOS Info.plist med UIDeviceFamily=[2], full orientering — Task 5 step 2
- [x] LaunchScreen.storyboard — Task 5 step 3
- [x] XcodeGen project.yml för Mac + iOS targets — Task 6 step 2
- [x] Bundle ID com.b2.balldrop (iOS) och com.b2.balldrop.mac (Mac) — Task 6
- [x] swift run fortsatt fungerande — Task 6 step 6
- [x] Manuell signing + TestFlight via Xcode GUI — Task 7

---

## Rollback om något går fel

Sex atomic feature-commits + en eventuell Xcode-projekt-commit. För att rulla tillbaka allt: `git reset --hard HEAD~7` (eller vad antalet commits är efter denna feature). Specen och planen ligger kvar oavsett.
