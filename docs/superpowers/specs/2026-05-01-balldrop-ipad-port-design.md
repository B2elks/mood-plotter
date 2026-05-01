# BallDrop — iPad-port (parallella Mac + iOS targets)

**Datum:** 2026-05-01
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop` (Swift Package, macOS 14+, SpriteKit + SwiftUI)
**Toolchain:** Xcode 26.1.1, iPadOS 17+

## Mål

Lägga till en iPad-version av BallDrop som distribueras via TestFlight (Apple Developer Program finns), med samma SpriteKit-spel som idag fungerar på macOS men anpassat för touch-input. Mac-versionen ska fortsätta fungera oförändrat — `swift run` ska bygga och köra som idag.

## Arkitektur

Hybrid-strategi: **behåll `Package.swift`** för Mac-CLI-bygget, **lägg till en `BallDrop.xcodeproj`** som hostar två app-targets (Mac och iOS) som båda inkluderar samma `.swift`-filer i `BallDrop/BallDrop/`. Plattformsspecifik kod separeras med `#if os(macOS)` / `#if os(iOS)` direktiv inline i varje fil.

```
BallDrop/
├── Package.swift                    (oförändrad — bygger Mac via swift run)
├── BallDrop.xcodeproj               (NY)
│   └── targets:
│       - BallDrop-Mac (com.b2.balldrop.mac, macOS 14+)
│       - BallDrop-iOS (com.b2.balldrop, iPadOS 17+)
└── BallDrop/                        (gemensamma källfiler, inkluderade i båda targets)
    ├── BallDropApp.swift
    ├── ContentView.swift
    ├── GameScene.swift              (mouse + touch)
    ├── BlockNode.swift
    ├── ScoreZone.swift
    ├── SpawnPoint.swift
    ├── FreeDrawTool.swift
    ├── SidebarView.swift
    └── iOS/                         (NY — iOS-bara filer)
        ├── Info.plist
        ├── LaunchScreen.storyboard  (tom — Xcode-mall räcker)
        └── SpriteKitView.swift      (UIViewRepresentable för pinch + long-press)
```

## Funktionella krav

### Plattform-abstraktion

#### Färger

Alla `NSColor(...)`-referenser i koden ersätts med `SKColor(...)`. SpriteKit definierar redan:

```swift
#if os(macOS)
public typealias SKColor = NSColor
#else
public typealias SKColor = UIColor
#endif
```

`SKColor(red:green:blue:alpha:)`-initiziern fungerar identiskt på båda plattformarna. Inga andra färgrelaterade ändringar krävs.

Filer som påverkas: `BlockNode.swift`, `GameScene.swift` (`spawnBall` colors-arrayen), `ScoreZone.swift`, `SpawnPoint.swift`, `FreeDrawTool.swift`. SidebarView.swift använder SwiftUI `Color` redan, alltså cross-platform.

#### Input-hantering

I `GameScene`:

- **Befintliga macOS-overrides** (`mouseDown(with:)`, `mouseDragged(with:)`, `mouseUp(with:)`, `rightMouseDown(with:)`, `scrollWheel(with:)`, `keyDown(with:)`) wrappas i `#if os(macOS)`.
- **Tre nya gemensamma helpers** extraheras (kapslar in den platformsoberoende logiken):
  ```swift
  private func handlePrimaryDown(at location: CGPoint)
  private func handlePrimaryDragged(at location: CGPoint)
  private func handlePrimaryUp()
  ```
  Dessa innehåller den befintliga logiken från `mouseDown`/`mouseDragged`/`mouseUp` (rotation handle-detektering, spawnPoint-drag, drawMode, block-drag).
- **Befintliga macOS-overrides** ändras till tunna wrappers som anropar dessa helpers med `event.location(in: self)`.
- **Nya iOS-overrides** under `#if os(iOS)`:
  ```swift
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
  ```

#### Multi-touch gester

Two iPad-only gestures replace macOS-only mechanisms:

- **Rotation** (ersätter scroll-wheel) — `UIRotationGestureRecognizer` på SKView. När gesten triggas (`state == .changed`), anropa `gameScene.rotateBlock(at: locationInScene, by: rotation)` där `rotation` är gesturens delta-rotation.
- **Long-press → ta bort** (ersätter högerklick) — `UILongPressGestureRecognizer` med `minimumPressDuration = 0.5`. När gesten triggas (`state == .began`), anropa `gameScene.removeBlock(at: locationInScene)`.

Två nya publika metoder på `GameScene` (cross-platform — kallas från Mac scrollWheel/rightMouseDown också):

```swift
func rotateBlock(at location: CGPoint, by delta: CGFloat) {
    let node = atPoint(location)
    let block: SKNode?
    if node.name == "block" { block = node }
    else if node.parent?.name == "block" { block = node.parent }
    else { block = nil }
    block?.zRotation += delta
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

Mac:s `scrollWheel(with:)` ändras till att anropa `rotateBlock(at: location, by: event.deltaY * 0.02)`. Mac:s `rightMouseDown(with:)` ändras till att anropa `removeBlock(at: location)`.

#### SpriteView-host på iOS

SwiftUI's `SpriteView` exponerar inte den underliggande `UIView` på ett bra sätt för att binda gesture recognizers. På iOS introduceras därför en `UIViewRepresentable`-wrapper:

```swift
#if os(iOS)
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

        init(scene: GameScene) { self.scene = scene }

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

`ContentView` får en conditional:

```swift
#if os(iOS)
SpriteKitView(scene: gameScene)
#else
SpriteView(scene: gameScene, options: [.allowsTransparency])
#endif
```

(Resten av ContentView — overlay-text, ZStack, sidebar — fungerar identiskt på båda plattformarna.)

### iOS app-konfig

#### Info.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>BallDrop</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
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

#### LaunchScreen.storyboard

Tom storyboard genererad av Xcode (vit bakgrund). Inga modifieringar krävs.

#### Bundle ID och signing

- iOS bundle ID: `com.b2.balldrop`
- Mac bundle ID: `com.b2.balldrop.mac`
- Signing: automatisk via Xcode, ADP-team väljs i Xcode Signing & Capabilities-fliken.

### Layout

`SidebarView` är 200pt bred. På iPad i landskap (1024×768 eller större) fungerar layouten utan ändring. På iPad i porträtt blir sidopanelen 26-30% av bredden — trångt men användbart, OK för v1.

**Out of scope för v1:**
- Adaptiv kollapsbar sidopanel.
- Apple Pencil-input.
- Haptic feedback.
- iCloud-sync av sparade banor.
- iPhone-stöd (`UIDeviceFamily` = [2] låser till iPad).

## Build- och distributionsflöde

### Mac-bygge (oförändrat)

```bash
cd BallDrop && swift run
```

### iOS-bygge

1. Öppna `BallDrop/BallDrop.xcodeproj` i Xcode.
2. Välj scheme "BallDrop-iOS".
3. Välj target-device: "Any iOS Device (arm64)" för archive.
4. **Product → Archive**.
5. I Organizer-fönstret: **Distribute App → App Store Connect → Upload**.
6. Vänta tills App Store Connect har behandlat builden (~5-15 min).
7. På iPaden: öppna **TestFlight**-appen, hitta BallDrop, installera.

För simulator-test under utveckling: välj t.ex. "iPad Pro 13-inch" i Xcode, **Cmd+R** kör i simulator.

## Edge cases

- **Rotation-gesture på en plats utan block:** `rotateBlock(at:)` blir no-op (block? är nil), gesturen förkastas tyst. Acceptabelt.
- **Long-press utan att hitta block:** `removeBlock(at:)` blir no-op. Acceptabelt.
- **Rotation-gesture under en pågående drag (touchesMoved):** Båda systemen skriver till samma scen. UIGestureRecognizer's standardbeteende är att `requiresExclusiveTouchType = false` — gesturen kan triggas oberoende. Acceptabelt risk i v1, kan leda till småjank om användaren startar en single-touch drag och sedan lägger till ett finger för rotation. Om det blir störande kan man sätta `requireGestureRecognizerToFail` mellan systemen, men v1 lämnas som det är.
- **Pinch-konflikt med rotation-gesture:** UIRotationGestureRecognizer triggar oberoende av pinch (de kan båda triggas samtidigt). Vi använder bara rotation, inte pinch. OK.
- **iPad sleep mid-game:** SpriteKit pauses automatiskt när appen går till bakgrund. Inga ändringar krävs.

## Testning

Manuell verifiering på simulator OCH fysisk iPad (via TestFlight):

1. Bygg Mac-version som idag — `swift run` fungerar utan ändringar i bygglog.
2. Öppna `BallDrop.xcodeproj` i Xcode → kompilerar både Mac-target och iOS-target utan fel.
3. Kör iOS-target i simulator → appen startar, sidopanelen syns till vänster, en zon dyker upp på spelytan, bollar börjar spawna.
4. **Touch-tester** (simulator/iPad):
   - Tap & drag block → flyttas korrekt.
   - Tap & drag rotation handle → blocket roterar.
   - Två-finger-rotation över ett block → blocket roterar.
   - Long-press på ett block → tas bort.
   - Tap på sidopanel-knapp ("Studsmatta", "Katapult", "Pausa", "Rensa", "Nollställ poäng") → fungerar.
   - Slider för storlek/hastighet → fungerar med touch.
5. **Spelmekanik** (simulator/iPad):
   - Bollar studsar mot studsmatta som förväntat.
   - Katapult skjuter iväg bollar i rätt riktning.
   - Poäng tickar upp i sidopanel + overlay.
   - Reset-knapp fungerar.
6. **Distribution:** archive → TestFlight upload lyckas. Installation på fysisk iPad via TestFlight-app fungerar.

## Out of scope (v1)

- Adaptiv layout.
- Apple Pencil-stöd, haptic feedback.
- iPhone-stöd.
- Saved levels via iCloud.
- Visuell polish av iOS-specifika UI-element (LaunchScreen, AppIcon, settings).
- Konvertering av ScoreZone visuell flash till partikelsystem som kan behöva anpassas för iOS.
