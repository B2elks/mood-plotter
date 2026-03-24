# SketchDrive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP of SketchDrive — an iPad game where children photograph hand-drawn cars and race them on tracks with contour-derived physics.

**Architecture:** SwiftUI app shell wrapping SpriteKit game scenes. Pure-Swift models for physics and vehicle analysis are unit-tested independently. Vision framework handles contour extraction from photos. SwiftData persists the vehicle garage.

**Tech Stack:** Swift 6, iOS 17+, SpriteKit, SwiftUI, Vision, Core Image, AVFoundation, SwiftData, XCTest

**Spec:** `docs/superpowers/specs/2026-03-24-sketchdrive-design.md`

**Project location:** `/Users/b2/Documents/Proj/LLM/SketchDrive/`

---

## File Map

```
SketchDrive/
├── SketchDrive.xcodeproj
├── SketchDrive/
│   ├── App/
│   │   ├── SketchDriveApp.swift              # @main entry, WindowGroup
│   │   └── AppState.swift                     # Observable navigation state
│   ├── Models/
│   │   ├── VehicleData.swift                  # VehicleProperties struct (mass, cd, area, cog, stability)
│   │   ├── TrackData.swift                    # TrackDefinition, TrackSegment, TrackType enum
│   │   └── MissionData.swift                  # Mission struct, MissionStatus
│   ├── Vision/
│   │   ├── ContourExtractor.swift             # UIImage → CGPath via VNDetectContoursRequest
│   │   └── VehicleAnalyzer.swift              # CGPath → VehicleProperties
│   ├── Physics/
│   │   ├── AerodynamicsModel.swift            # Drag force, Cd calculation from contour
│   │   ├── VehiclePhysicsConfig.swift         # Map VehicleProperties → SKPhysicsBody config
│   │   └── DifficultyScaler.swift             # Scale physics parameters by difficulty
│   ├── Game/
│   │   ├── VehicleNode.swift                  # SKSpriteNode subclass with physics body from contour
│   │   ├── SideViewScene.swift                # Side-scrolling SpriteKit scene
│   │   ├── TopDownScene.swift                 # Top-down SpriteKit scene
│   │   ├── TrackBuilder.swift                 # TrackDefinition → SKNode tree
│   │   ├── SideViewControls.swift             # Gas/brake touch controls for side-view
│   │   └── TopDownControls.swift              # Gas/brake/steer touch controls for top-down
│   ├── Missions/
│   │   └── MissionManager.swift               # Load missions, track progress, star calculation
│   ├── Garage/
│   │   ├── StoredVehicle.swift                # SwiftData @Model
│   │   └── VehicleStore.swift                 # CRUD operations on StoredVehicle
│   ├── Camera/
│   │   └── CameraManager.swift                # AVFoundation camera capture coordinator
│   ├── UI/
│   │   ├── MainMenuView.swift                 # Start screen with Play / Garage buttons
│   │   ├── MissionListView.swift              # List of available missions
│   │   ├── MissionBriefingView.swift          # Mission description + track preview + "Take Photo" CTA
│   │   ├── CameraView.swift                   # Camera viewfinder with capture button
│   │   ├── VehicleResultView.swift            # Shows extracted vehicle with properties
│   │   ├── GameContainerView.swift            # SpriteKit scene wrapper (SpriteView)
│   │   ├── RaceResultView.swift               # Stars, feedback, retry/next
│   │   └── GarageView.swift                   # Grid of saved vehicles
│   └── Resources/
│       ├── Missions/
│       │   └── missions.json                  # 3 MVP missions
│       └── Tracks/
│           ├── track_flat_road.json           # Mission 1: flat side-view
│           ├── track_hills.json               # Mission 2: hilly side-view
│           └── track_oval.json                # Mission 3: top-down oval
├── SketchDriveTests/
│   ├── Physics/
│   │   ├── AerodynamicsModelTests.swift
│   │   ├── VehiclePhysicsConfigTests.swift
│   │   └── DifficultyScalerTests.swift
│   ├── Vision/
│   │   └── VehicleAnalyzerTests.swift
│   ├── Missions/
│   │   └── MissionManagerTests.swift
│   ├── Game/
│   │   └── TrackBuilderTests.swift
│   └── Garage/
│       └── VehicleStoreTests.swift
```

---

### Task 1: Xcode Project Setup

**Files:**
- Create: `SketchDrive/SketchDrive.xcodeproj` (via Xcode CLI)
- Create: `SketchDrive/SketchDrive/App/SketchDriveApp.swift`
- Create: `SketchDrive/SketchDrive/Info.plist`

- [ ] **Step 1: Create Xcode project directory structure**

```bash
mkdir -p /Users/b2/Documents/Proj/LLM/SketchDrive/SketchDrive/{App,Models,Vision,Physics,Game,Missions,Garage,Camera,UI,Resources/{Missions,Tracks}}
mkdir -p /Users/b2/Documents/Proj/LLM/SketchDrive/SketchDriveTests/{Physics,Vision,Missions,Game,Garage}
```

- [ ] **Step 2: Create the app entry point**

Create `SketchDrive/SketchDrive/App/SketchDriveApp.swift`:
```swift
import SwiftUI

@main
struct SketchDriveApp: App {
    var body: some Scene {
        WindowGroup {
            Text("SketchDrive")
                .font(.largeTitle)
        }
    }
}
```

- [ ] **Step 3: Install xcodegen**

```bash
brew install xcodegen
```

- [ ] **Step 4: Create xcodegen spec**

Create `SketchDrive/project.yml`:
```yaml
name: SketchDrive
options:
  bundleIdPrefix: com.sketchdrive
  deploymentTarget:
    iOS: "17.0"
  xcodeVersion: "16.0"
settings:
  TARGETED_DEVICE_FAMILY: 2  # iPad only
  SWIFT_VERSION: "5.0"
  SWIFT_STRICT_CONCURRENCY: minimal
targets:
  SketchDrive:
    type: application
    platform: iOS
    sources:
      - SketchDrive
    settings:
      GENERATE_INFOPLIST_FILE: YES
      INFOPLIST_KEY_NSCameraUsageDescription: "SketchDrive needs your camera to photograph your drawings"
    resources:
      - path: SketchDrive/Resources
  SketchDriveTests:
    type: bundle.unit-test
    platform: iOS
    sources:
      - SketchDriveTests
    dependencies:
      - target: SketchDrive
```

- [ ] **Step 5: Generate Xcode project**

Run:
```bash
cd /Users/b2/Documents/Proj/LLM/SketchDrive && xcodegen generate
```

**Fallback (if xcodegen unavailable):** Create project manually in Xcode: File → New → Project → App, name "SketchDrive", SwiftUI + SwiftData, iPad only, iOS 17.0. Add existing folders. Set `NSCameraUsageDescription` in Info.plist.

- [ ] **Step 6: Verify project builds**

```bash
cd /Users/b2/Documents/Proj/LLM/SketchDrive
xcodebuild -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' build 2>&1 | tail -5
```
Expected: `** BUILD SUCCEEDED **`

- [ ] **Step 7: Init git repo and commit**

```bash
cd /Users/b2/Documents/Proj/LLM/SketchDrive
git init
cat > .gitignore << 'EOF'
.DS_Store
*.xcuserdata
xcuserdata/
DerivedData/
build/
.build/
*.swp
EOF
git add -A
git commit -m "feat: initial SketchDrive project setup"
```

---

### Task 2: Vehicle Data Models

**Files:**
- Create: `SketchDrive/SketchDrive/Models/VehicleData.swift`
- Test: `SketchDrive/SketchDriveTests/VehicleDataTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/VehicleDataTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class VehicleDataTests: XCTestCase {

    func testVehiclePropertiesFromValues() {
        let props = VehicleProperties(
            mass: 1200,
            dragCoefficient: 0.32,
            frontalArea: 2.2,
            centerOfGravity: CGPoint(x: 0.5, y: 0.4),
            stability: 0.75,
            contourPath: CGMutablePath()
        )
        XCTAssertEqual(props.mass, 1200)
        XCTAssertEqual(props.dragCoefficient, 0.32)
        XCTAssertEqual(props.frontalArea, 2.2)
        XCTAssertEqual(props.stability, 0.75, accuracy: 0.01)
    }

    func testVehiclePropertiesWeightCategory() {
        let light = VehicleProperties(mass: 500, dragCoefficient: 0.25, frontalArea: 1.5, centerOfGravity: .zero, stability: 0.8, contourPath: CGMutablePath())
        let heavy = VehicleProperties(mass: 3000, dragCoefficient: 0.6, frontalArea: 4.0, centerOfGravity: .zero, stability: 0.5, contourPath: CGMutablePath())

        XCTAssertEqual(light.weightCategory, .light)
        XCTAssertEqual(heavy.weightCategory, .heavy)
    }

    func testVehiclePropertiesAeroCategory() {
        let streamlined = VehicleProperties(mass: 800, dragCoefficient: 0.2, frontalArea: 1.2, centerOfGravity: .zero, stability: 0.9, contourPath: CGMutablePath())
        let boxy = VehicleProperties(mass: 800, dragCoefficient: 0.7, frontalArea: 3.5, centerOfGravity: .zero, stability: 0.5, contourPath: CGMutablePath())

        XCTAssertEqual(streamlined.aeroCategory, .streamlined)
        XCTAssertEqual(boxy.aeroCategory, .boxy)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' -only-testing:SketchDriveTests/VehicleDataTests 2>&1 | tail -10
```
Expected: FAIL — `VehicleProperties` not defined

- [ ] **Step 3: Implement VehicleData**

Create `SketchDrive/SketchDrive/Models/VehicleData.swift`:
```swift
import CoreGraphics

struct VehicleProperties {
    let mass: CGFloat           // kg — derived from contour area
    let dragCoefficient: CGFloat // Cd — 0.0 (perfect) to 1.0+ (brick)
    let frontalArea: CGFloat    // m² — cross-section in travel direction
    let centerOfGravity: CGPoint // normalized 0–1 within bounding box
    let stability: CGFloat      // 0–1 — width/height ratio
    let contourPath: CGPath     // original contour for physics body

    enum WeightCategory: String {
        case light, medium, heavy
    }

    enum AeroCategory: String {
        case streamlined, average, boxy
    }

    var weightCategory: WeightCategory {
        if mass < 800 { return .light }
        if mass < 2000 { return .medium }
        return .heavy
    }

    var aeroCategory: AeroCategory {
        let score = dragCoefficient * frontalArea
        if score < 0.5 { return .streamlined }
        if score < 1.5 { return .average }
        return .boxy
    }

    /// Drag force at a given velocity: F = 0.5 * Cd * A * v²
    func dragForce(atVelocity v: CGFloat) -> CGFloat {
        0.5 * dragCoefficient * frontalArea * v * v
    }
}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' -only-testing:SketchDriveTests/VehicleDataTests 2>&1 | tail -10
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add SketchDrive/Models/VehicleData.swift SketchDriveTests/VehicleDataTests.swift
git commit -m "feat: add VehicleProperties data model with weight/aero categories"
```

---

### Task 3: Aerodynamics Model

**Files:**
- Create: `SketchDrive/SketchDrive/Physics/AerodynamicsModel.swift`
- Test: `SketchDrive/SketchDriveTests/Physics/AerodynamicsModelTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/Physics/AerodynamicsModelTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class AerodynamicsModelTests: XCTestCase {

    func testDragForceIncreasesWithVelocitySquared() {
        let model = AerodynamicsModel(cd: 0.3, frontalArea: 2.0)
        let f10 = model.dragForce(atVelocity: 10)
        let f20 = model.dragForce(atVelocity: 20)
        // At double speed, drag should be 4x
        XCTAssertEqual(f20, f10 * 4, accuracy: 0.01)
    }

    func testHighCdProducesMoreDrag() {
        let sleek = AerodynamicsModel(cd: 0.2, frontalArea: 1.5)
        let boxy = AerodynamicsModel(cd: 0.8, frontalArea: 3.0)
        let velocity: CGFloat = 15
        XCTAssertTrue(boxy.dragForce(atVelocity: velocity) > sleek.dragForce(atVelocity: velocity))
    }

    func testTopSpeedEstimate() {
        let model = AerodynamicsModel(cd: 0.3, frontalArea: 2.0)
        let engineForce: CGFloat = 500  // N
        let topSpeed = model.estimatedTopSpeed(engineForce: engineForce)
        // At top speed, drag = engine force → v = sqrt(2F / (Cd * A))
        let expectedDrag = model.dragForce(atVelocity: topSpeed)
        XCTAssertEqual(expectedDrag, engineForce, accuracy: 1.0)
    }

    func testCdFromContourRatio() {
        // Perfect circle has perimeter/sqrt(area) ratio ~3.54
        // A streamlined shape (low ratio) should get low Cd
        let lowRatio: CGFloat = 4.0   // close to circle — streamlined
        let highRatio: CGFloat = 12.0 // very jagged — boxy
        let cdLow = AerodynamicsModel.estimateCd(perimeterToAreaRatio: lowRatio)
        let cdHigh = AerodynamicsModel.estimateCd(perimeterToAreaRatio: highRatio)
        XCTAssertTrue(cdLow < cdHigh)
        XCTAssertTrue(cdLow >= 0.15 && cdLow <= 0.5)
        XCTAssertTrue(cdHigh >= 0.5 && cdHigh <= 1.2)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' -only-testing:SketchDriveTests/AerodynamicsModelTests 2>&1 | tail -10
```
Expected: FAIL

- [ ] **Step 3: Implement AerodynamicsModel**

Create `SketchDrive/SketchDrive/Physics/AerodynamicsModel.swift`:
```swift
import CoreGraphics

struct AerodynamicsModel {
    let cd: CGFloat        // drag coefficient
    let frontalArea: CGFloat // m²

    /// Drag force: F = 0.5 * Cd * A * v²
    func dragForce(atVelocity v: CGFloat) -> CGFloat {
        0.5 * cd * frontalArea * v * v
    }

    /// Top speed where drag equals engine force
    /// drag = engineForce → 0.5 * Cd * A * v² = F → v = sqrt(2F / (Cd * A))
    func estimatedTopSpeed(engineForce: CGFloat) -> CGFloat {
        let denominator = cd * frontalArea
        guard denominator > 0 else { return 0 }
        return sqrt(2 * engineForce / denominator)
    }

    /// Estimate Cd from the contour's perimeter-to-sqrt(area) ratio.
    /// A circle (most streamlined simple shape) has ratio ~3.54.
    /// Higher ratios = more jagged/boxy = higher Cd.
    static func estimateCd(perimeterToAreaRatio ratio: CGFloat) -> CGFloat {
        // Map ratio from ~3.5 (streamlined) to ~15 (very boxy)
        // onto Cd range 0.15 to 1.0
        let minRatio: CGFloat = 3.5
        let maxRatio: CGFloat = 15.0
        let minCd: CGFloat = 0.15
        let maxCd: CGFloat = 1.0

        let normalized = (ratio - minRatio) / (maxRatio - minRatio)
        let clamped = max(0, min(1, normalized))
        return minCd + clamped * (maxCd - minCd)
    }
}
```

- [ ] **Step 4: Run tests — verify they pass**

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add SketchDrive/Physics/AerodynamicsModel.swift SketchDriveTests/Physics/AerodynamicsModelTests.swift
git commit -m "feat: add AerodynamicsModel with drag force and Cd estimation"
```

---

### Task 4: Vehicle Physics Config

**Files:**
- Create: `SketchDrive/SketchDrive/Physics/VehiclePhysicsConfig.swift`
- Create: `SketchDrive/SketchDrive/Physics/DifficultyScaler.swift`
- Test: `SketchDrive/SketchDriveTests/Physics/VehiclePhysicsConfigTests.swift`
- Test: `SketchDrive/SketchDriveTests/Physics/DifficultyScalerTests.swift`

- [ ] **Step 1: Write VehiclePhysicsConfig test**

Create `SketchDrive/SketchDriveTests/Physics/VehiclePhysicsConfigTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class VehiclePhysicsConfigTests: XCTestCase {

    func testConfigFromVehicleProperties() {
        let props = VehicleProperties(
            mass: 1000,
            dragCoefficient: 0.3,
            frontalArea: 2.0,
            centerOfGravity: CGPoint(x: 0.5, y: 0.3),
            stability: 0.8,
            contourPath: CGMutablePath()
        )
        let config = VehiclePhysicsConfig.from(properties: props)

        XCTAssertEqual(config.mass, 1000)
        XCTAssertTrue(config.engineForce > 0)
        XCTAssertTrue(config.brakeForce > 0)
        XCTAssertTrue(config.maxSteeringAngle > 0)
        XCTAssertTrue(config.linearDamping >= 0)
    }

    func testHeavierCarHasMoreEngineForceButSlowerAcceleration() {
        let light = VehicleProperties(mass: 500, dragCoefficient: 0.3, frontalArea: 1.5, centerOfGravity: .zero, stability: 0.8, contourPath: CGMutablePath())
        let heavy = VehicleProperties(mass: 2500, dragCoefficient: 0.3, frontalArea: 3.0, centerOfGravity: .zero, stability: 0.6, contourPath: CGMutablePath())

        let lightConfig = VehiclePhysicsConfig.from(properties: light)
        let heavyConfig = VehiclePhysicsConfig.from(properties: heavy)

        // Heavy car has more raw force but lower acceleration (force/mass)
        let lightAccel = lightConfig.engineForce / lightConfig.mass
        let heavyAccel = heavyConfig.engineForce / heavyConfig.mass
        XCTAssertTrue(lightAccel > heavyAccel)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

Expected: FAIL

- [ ] **Step 3: Implement VehiclePhysicsConfig**

Create `SketchDrive/SketchDrive/Physics/VehiclePhysicsConfig.swift`:
```swift
import CoreGraphics

struct VehiclePhysicsConfig {
    let mass: CGFloat
    let engineForce: CGFloat       // N — base engine power
    let brakeForce: CGFloat        // N — braking power
    let maxSteeringAngle: CGFloat  // radians — for top-down
    let linearDamping: CGFloat     // SpriteKit linear damping
    let friction: CGFloat          // ground contact friction
    let restitution: CGFloat       // bounciness on collision
    let aerodynamics: AerodynamicsModel

    static func from(properties p: VehicleProperties) -> VehiclePhysicsConfig {
        // Engine force scales with mass but sub-linearly (heavier = stronger but not proportionally)
        let engineForce = 200 + p.mass * 0.4

        // Brake force proportional to mass
        let brakeForce = p.mass * 0.6

        // Steering angle: more stable cars steer tighter
        let maxSteeringAngle = CGFloat.pi / 6 * p.stability

        // Linear damping from drag coefficient (base friction + aero drag)
        let linearDamping = 0.1 + p.dragCoefficient * 0.3

        // Ground friction from stability
        let friction = 0.3 + p.stability * 0.4

        let aero = AerodynamicsModel(cd: p.dragCoefficient, frontalArea: p.frontalArea)

        return VehiclePhysicsConfig(
            mass: p.mass,
            engineForce: engineForce,
            brakeForce: brakeForce,
            maxSteeringAngle: maxSteeringAngle,
            linearDamping: linearDamping,
            friction: friction,
            restitution: 0.2,
            aerodynamics: aero
        )
    }
}
```

- [ ] **Step 4: Run tests — verify they pass**

Expected: PASS

- [ ] **Step 5: Write DifficultyScaler test**

Create `SketchDrive/SketchDriveTests/Physics/DifficultyScalerTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class DifficultyScalerTests: XCTestCase {

    func testPlayfulModeBoostsEngineAndReducesDrag() {
        let base = VehiclePhysicsConfig(
            mass: 1000, engineForce: 600, brakeForce: 600,
            maxSteeringAngle: 0.5, linearDamping: 0.2,
            friction: 0.5, restitution: 0.2,
            aerodynamics: AerodynamicsModel(cd: 0.3, frontalArea: 2.0)
        )
        let scaled = DifficultyScaler.scale(config: base, difficulty: .playful)

        XCTAssertTrue(scaled.engineForce > base.engineForce)
        XCTAssertTrue(scaled.linearDamping < base.linearDamping)
    }

    func testRealisticModeKeepsValuesUnchanged() {
        let base = VehiclePhysicsConfig(
            mass: 1000, engineForce: 600, brakeForce: 600,
            maxSteeringAngle: 0.5, linearDamping: 0.2,
            friction: 0.5, restitution: 0.2,
            aerodynamics: AerodynamicsModel(cd: 0.3, frontalArea: 2.0)
        )
        let scaled = DifficultyScaler.scale(config: base, difficulty: .realistic)

        XCTAssertEqual(scaled.engineForce, base.engineForce)
        XCTAssertEqual(scaled.linearDamping, base.linearDamping)
    }
}
```

- [ ] **Step 6: Implement DifficultyScaler**

Create `SketchDrive/SketchDrive/Physics/DifficultyScaler.swift`:
```swift
import CoreGraphics

enum Difficulty: String, Codable {
    case playful    // forgiving physics, all cars complete
    case realistic  // true physics, cars can fail
}

struct DifficultyScaler {
    static func scale(config c: VehiclePhysicsConfig, difficulty: Difficulty) -> VehiclePhysicsConfig {
        switch difficulty {
        case .playful:
            return VehiclePhysicsConfig(
                mass: c.mass,
                engineForce: c.engineForce * 1.5,       // 50% more power
                brakeForce: c.brakeForce * 1.3,          // 30% better brakes
                maxSteeringAngle: c.maxSteeringAngle * 1.2,
                linearDamping: c.linearDamping * 0.6,    // 40% less drag
                friction: min(c.friction * 1.3, 1.0),    // more grip
                restitution: c.restitution * 0.5,         // less bouncy
                aerodynamics: AerodynamicsModel(
                    cd: c.aerodynamics.cd * 0.6,
                    frontalArea: c.aerodynamics.frontalArea
                )
            )
        case .realistic:
            return c // no changes
        }
    }
}
```

- [ ] **Step 7: Run all physics tests**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' -only-testing:SketchDriveTests/DifficultyScalerTests 2>&1 | tail -10
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add SketchDrive/Physics/ SketchDriveTests/Physics/
git commit -m "feat: add VehiclePhysicsConfig and DifficultyScaler"
```

---

### Task 5: Vehicle Analyzer (Contour → Properties)

**Files:**
- Create: `SketchDrive/SketchDrive/Vision/VehicleAnalyzer.swift`
- Test: `SketchDrive/SketchDriveTests/Vision/VehicleAnalyzerTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/Vision/VehicleAnalyzerTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class VehicleAnalyzerTests: XCTestCase {

    /// Helper: create a rectangular contour path
    private func rectPath(width: CGFloat, height: CGFloat) -> CGPath {
        CGPath(rect: CGRect(x: 0, y: 0, width: width, height: height), transform: nil)
    }

    /// Helper: create an elliptical contour (streamlined shape)
    private func ellipsePath(width: CGFloat, height: CGFloat) -> CGPath {
        CGPath(ellipseIn: CGRect(x: 0, y: 0, width: width, height: height), transform: nil)
    }

    func testMassProportionalToArea() {
        let small = VehicleAnalyzer.analyze(contour: rectPath(width: 100, height: 50))
        let large = VehicleAnalyzer.analyze(contour: rectPath(width: 200, height: 100))
        XCTAssertTrue(large.mass > small.mass)
    }

    func testWideLowCarIsMoreStable() {
        let wide = VehicleAnalyzer.analyze(contour: rectPath(width: 200, height: 50))
        let tall = VehicleAnalyzer.analyze(contour: rectPath(width: 50, height: 200))
        XCTAssertTrue(wide.stability > tall.stability)
    }

    func testEllipseHasLowerCdThanRect() {
        let ellipse = VehicleAnalyzer.analyze(contour: ellipsePath(width: 200, height: 80))
        let rect = VehicleAnalyzer.analyze(contour: rectPath(width: 200, height: 80))
        XCTAssertTrue(ellipse.dragCoefficient < rect.dragCoefficient)
    }

    func testCenterOfGravityIsNormalized() {
        let props = VehicleAnalyzer.analyze(contour: rectPath(width: 100, height: 50))
        XCTAssertTrue(props.centerOfGravity.x >= 0 && props.centerOfGravity.x <= 1)
        XCTAssertTrue(props.centerOfGravity.y >= 0 && props.centerOfGravity.y <= 1)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

Expected: FAIL

- [ ] **Step 3: Implement VehicleAnalyzer**

Create `SketchDrive/SketchDrive/Vision/VehicleAnalyzer.swift`:
```swift
import CoreGraphics

struct VehicleAnalyzer {

    /// Analyze a contour path and derive vehicle physics properties.
    static func analyze(contour: CGPath) -> VehicleProperties {
        let bounds = contour.boundingBox
        let width = bounds.width
        let height = bounds.height

        // Area and perimeter
        let area = estimateArea(of: contour, bounds: bounds)
        let perimeter = estimatePerimeter(of: contour)

        // Mass: proportional to area (scaled to reasonable kg range)
        let mass = area * 0.05 + 200  // min ~200kg

        // Frontal area: height in travel direction (side-view proxy)
        let frontalArea = height * 0.01  // scale to m²

        // Stability: width/height ratio, clamped 0–1
        let stability = min(width / max(height, 1), 3.0) / 3.0

        // Center of gravity: centroid of bounding box, normalized 0–1
        let cogX = (bounds.midX - bounds.minX) / max(width, 1)
        let cogY = (bounds.midY - bounds.minY) / max(height, 1)

        // Cd from perimeter-to-sqrt(area) ratio
        let sqrtArea = sqrt(area)
        let ratio = sqrtArea > 0 ? perimeter / sqrtArea : 10.0
        let cd = AerodynamicsModel.estimateCd(perimeterToAreaRatio: ratio)

        return VehicleProperties(
            mass: mass,
            dragCoefficient: cd,
            frontalArea: frontalArea,
            centerOfGravity: CGPoint(x: cogX, y: cogY),
            stability: stability,
            contourPath: contour
        )
    }

    /// Estimate area by counting pixels inside the path on a bitmap.
    private static func estimateArea(of path: CGPath, bounds: CGRect) -> CGFloat {
        // Use bounding box area weighted by fill ratio
        // For simple shapes: rect fill = 1.0, ellipse fill ≈ 0.785
        let boxArea = bounds.width * bounds.height
        // Approximate: use the path's fill as a fraction of bounding box
        // For a proper implementation, rasterize and count pixels
        // For MVP, use bounding box area * 0.75 as rough estimate
        return boxArea * 0.75
    }

    /// Estimate perimeter by flattening the path and summing segment lengths.
    private static func estimatePerimeter(of path: CGPath) -> CGFloat {
        var perimeter: CGFloat = 0
        var currentPoint = CGPoint.zero
        var startPoint = CGPoint.zero

        path.applyWithBlock { element in
            switch element.pointee.type {
            case .moveToPoint:
                currentPoint = element.pointee.points[0]
                startPoint = currentPoint
            case .addLineToPoint:
                let next = element.pointee.points[0]
                perimeter += hypot(next.x - currentPoint.x, next.y - currentPoint.y)
                currentPoint = next
            case .addQuadCurveToPoint:
                let next = element.pointee.points[1]
                perimeter += hypot(next.x - currentPoint.x, next.y - currentPoint.y)
                currentPoint = next
            case .addCurveToPoint:
                let next = element.pointee.points[2]
                perimeter += hypot(next.x - currentPoint.x, next.y - currentPoint.y)
                currentPoint = next
            case .closeSubpath:
                perimeter += hypot(startPoint.x - currentPoint.x, startPoint.y - currentPoint.y)
                currentPoint = startPoint
            @unknown default:
                break
            }
        }
        return perimeter
    }
}
```

- [ ] **Step 4: Run tests — verify they pass**

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add SketchDrive/Vision/VehicleAnalyzer.swift SketchDriveTests/Vision/VehicleAnalyzerTests.swift
git commit -m "feat: add VehicleAnalyzer — derive physics properties from contour"
```

---

### Task 6: Contour Extractor (Photo → CGPath)

**Files:**
- Create: `SketchDrive/SketchDrive/Vision/ContourExtractor.swift`

No unit test for this task — it depends on Vision framework and real images. Verified manually in Task 12.

- [ ] **Step 1: Implement ContourExtractor**

Create `SketchDrive/SketchDrive/Vision/ContourExtractor.swift`:
```swift
import UIKit
import Vision

struct ContourExtractor {

    enum ExtractionError: Error {
        case noContoursFound
        case imageConversionFailed
    }

    /// Extract the largest contour from a UIImage.
    /// Returns the contour as a CGPath and the cropped texture image.
    static func extract(from image: UIImage) async throws -> (contour: CGPath, texture: UIImage) {
        guard let cgImage = image.cgImage else {
            throw ExtractionError.imageConversionFailed
        }

        let contourPath = try await detectContour(in: cgImage)
        let texture = cropImage(cgImage, toContour: contourPath, imageSize: image.size)

        return (contour: contourPath, texture: texture)
    }

    /// Use Vision to detect contours and return the largest one as CGPath.
    private static func detectContour(in cgImage: CGImage) async throws -> CGPath {
        let request = VNDetectContoursRequest()
        request.contrastAdjustment = 1.5
        request.maximumImageDimension = 1024

        let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
        try handler.perform([request])

        guard let result = request.results?.first else {
            throw ExtractionError.noContoursFound
        }

        // Find the largest child contour (skip the outermost which is the full image)
        let topLevel = result.topLevelContours
        guard let largest = topLevel.max(by: {
            $0.normalizedPath.boundingBox.width * $0.normalizedPath.boundingBox.height <
            $1.normalizedPath.boundingBox.width * $1.normalizedPath.boundingBox.height
        }) else {
            throw ExtractionError.noContoursFound
        }

        return largest.normalizedPath
    }

    /// Crop the original image to just the contour area, with transparent background.
    private static func cropImage(_ cgImage: CGImage, toContour normalizedPath: CGPath, imageSize: CGSize) -> UIImage {
        let width = imageSize.width
        let height = imageSize.height

        // Scale normalized path (0–1) to image coordinates
        var transform = CGAffineTransform(scaleX: width, y: height)
        guard let scaledPath = normalizedPath.copy(using: &transform) else {
            return UIImage(cgImage: cgImage)
        }

        let renderer = UIGraphicsImageRenderer(size: imageSize)
        let cropped = renderer.image { ctx in
            let context = ctx.cgContext
            context.addPath(scaledPath)
            context.clip()
            context.draw(cgImage, in: CGRect(origin: .zero, size: imageSize))
        }
        return cropped
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add SketchDrive/Vision/ContourExtractor.swift
git commit -m "feat: add ContourExtractor — Vision framework contour detection and image cropping"
```

---

### Task 7: Track Data Model & Builder

**Files:**
- Create: `SketchDrive/SketchDrive/Models/TrackData.swift`
- Create: `SketchDrive/SketchDrive/Game/TrackBuilder.swift`
- Create: `SketchDrive/SketchDrive/Resources/Tracks/track_flat_road.json`
- Create: `SketchDrive/SketchDrive/Resources/Tracks/track_hills.json`
- Create: `SketchDrive/SketchDrive/Resources/Tracks/track_oval.json`
- Test: `SketchDrive/SketchDriveTests/Game/TrackBuilderTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/Game/TrackBuilderTests.swift`:
```swift
import XCTest
import SpriteKit
@testable import SketchDrive

final class TrackBuilderTests: XCTestCase {

    func testLoadsSideViewTrackFromJSON() throws {
        let json = """
        {
            "id": "flat_road",
            "name": "Flat Road",
            "type": "sideView",
            "segments": [
                { "type": "flat", "length": 500, "surface": "road" },
                { "type": "hill", "length": 200, "height": 80, "surface": "road" },
                { "type": "flat", "length": 300, "surface": "road" }
            ]
        }
        """.data(using: .utf8)!

        let track = try JSONDecoder().decode(TrackDefinition.self, from: json)
        XCTAssertEqual(track.id, "flat_road")
        XCTAssertEqual(track.type, .sideView)
        XCTAssertEqual(track.segments.count, 3)
    }

    func testLoadsTopDownTrackFromJSON() throws {
        let json = """
        {
            "id": "oval",
            "name": "Oval Circuit",
            "type": "topDown",
            "waypoints": [
                { "x": 0, "y": 0 },
                { "x": 500, "y": 0 },
                { "x": 500, "y": 300 },
                { "x": 0, "y": 300 }
            ],
            "trackWidth": 80
        }
        """.data(using: .utf8)!

        let track = try JSONDecoder().decode(TrackDefinition.self, from: json)
        XCTAssertEqual(track.type, .topDown)
        XCTAssertEqual(track.waypoints?.count, 4)
        XCTAssertEqual(track.trackWidth, 80)
    }

    func testTrackBuilderCreatesSideViewNodes() throws {
        let track = TrackDefinition(
            id: "test",
            name: "Test",
            type: .sideView,
            segments: [
                TrackSegment(type: .flat, length: 500, height: nil, surface: .road)
            ],
            waypoints: nil,
            trackWidth: nil
        )
        let node = TrackBuilder.buildSideView(from: track)
        XCTAssertTrue(node.children.count > 0)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

Expected: FAIL

- [ ] **Step 3: Implement TrackData**

Create `SketchDrive/SketchDrive/Models/TrackData.swift`:
```swift
import CoreGraphics

enum TrackType: String, Codable {
    case sideView
    case topDown
}

enum SurfaceType: String, Codable {
    case road
    case boost
    case ice
    case gravel
}

enum SegmentType: String, Codable {
    case flat
    case hill
    case valley
    case jump
    case tunnel
}

struct TrackSegment: Codable {
    let type: SegmentType
    let length: CGFloat
    let height: CGFloat?    // for hills/valleys
    let surface: SurfaceType
}

struct TrackWaypoint: Codable {
    let x: CGFloat
    let y: CGFloat
}

struct TrackDefinition: Codable {
    let id: String
    let name: String
    let type: TrackType
    let segments: [TrackSegment]?    // for sideView
    let waypoints: [TrackWaypoint]?  // for topDown
    let trackWidth: CGFloat?         // for topDown
}
```

- [ ] **Step 4: Implement TrackBuilder**

Create `SketchDrive/SketchDrive/Game/TrackBuilder.swift`:
```swift
import SpriteKit

struct TrackBuilder {

    /// Build a side-view track as an SKNode tree from a TrackDefinition.
    static func buildSideView(from track: TrackDefinition) -> SKNode {
        let root = SKNode()
        root.name = "track_\(track.id)"

        guard let segments = track.segments else { return root }

        var currentX: CGFloat = 0
        var currentY: CGFloat = 200  // base ground height

        for segment in segments {
            let (node, endX, endY) = buildSideSegment(
                segment: segment,
                startX: currentX,
                startY: currentY
            )
            root.addChild(node)
            currentX = endX
            currentY = endY
        }

        return root
    }

    /// Build a single side-view segment as ground physics body.
    private static func buildSideSegment(
        segment: TrackSegment,
        startX: CGFloat,
        startY: CGFloat
    ) -> (node: SKNode, endX: CGFloat, endY: CGFloat) {
        let endX = startX + segment.length
        let endY: CGFloat

        switch segment.type {
        case .flat:
            endY = startY
        case .hill:
            endY = startY + (segment.height ?? 80)
        case .valley:
            endY = startY - (segment.height ?? 60)
        case .jump:
            endY = startY + (segment.height ?? 40)
        case .tunnel:
            endY = startY
        }

        let path = CGMutablePath()
        path.move(to: CGPoint(x: startX, y: startY))

        if segment.type == .flat || segment.type == .tunnel {
            path.addLine(to: CGPoint(x: endX, y: endY))
        } else {
            // Smooth curve for hills/valleys/jumps
            let midX = (startX + endX) / 2
            path.addQuadCurve(to: CGPoint(x: endX, y: endY),
                              control: CGPoint(x: midX, y: endY))
        }

        // Extend path down to form a solid ground shape
        path.addLine(to: CGPoint(x: endX, y: 0))
        path.addLine(to: CGPoint(x: startX, y: 0))
        path.closeSubpath()

        let node = SKShapeNode(path: path)
        node.fillColor = colorForSurface(segment.surface)
        node.strokeColor = .darkGray
        node.lineWidth = 2

        node.physicsBody = SKPhysicsBody(edgeChainFrom: {
            let edge = CGMutablePath()
            edge.move(to: CGPoint(x: startX, y: startY))
            if segment.type == .flat || segment.type == .tunnel {
                edge.addLine(to: CGPoint(x: endX, y: endY))
            } else {
                let midX = (startX + endX) / 2
                edge.addQuadCurve(to: CGPoint(x: endX, y: endY),
                                  control: CGPoint(x: midX, y: endY))
            }
            return edge
        }())
        node.physicsBody?.isDynamic = false
        node.physicsBody?.friction = frictionForSurface(segment.surface)
        node.physicsBody?.restitution = 0.1

        node.name = "segment_\(segment.type.rawValue)"

        return (node, endX, endY)
    }

    /// Build a top-down track from waypoints.
    static func buildTopDown(from track: TrackDefinition) -> SKNode {
        let root = SKNode()
        root.name = "track_\(track.id)"

        guard let waypoints = track.waypoints, waypoints.count >= 2 else { return root }
        let trackWidth = track.trackWidth ?? 80

        // Draw track as a thick path
        let path = CGMutablePath()
        path.move(to: CGPoint(x: waypoints[0].x, y: waypoints[0].y))
        for i in 1..<waypoints.count {
            path.addLine(to: CGPoint(x: waypoints[i].x, y: waypoints[i].y))
        }
        path.closeSubpath()

        let trackNode = SKShapeNode(path: path)
        trackNode.strokeColor = .darkGray
        trackNode.lineWidth = trackWidth
        trackNode.lineCap = .round
        trackNode.lineJoin = .round
        trackNode.name = "track_surface"

        // Edge boundaries (inner and outer walls)
        let boundaryBody = SKPhysicsBody(edgeLoopFrom: path)
        boundaryBody.isDynamic = false
        boundaryBody.friction = 0.3
        trackNode.physicsBody = boundaryBody

        root.addChild(trackNode)

        return root
    }

    private static func colorForSurface(_ surface: SurfaceType) -> SKColor {
        switch surface {
        case .road:   return SKColor(red: 0.4, green: 0.3, blue: 0.2, alpha: 1) // brown earth
        case .boost:  return SKColor(red: 1.0, green: 0.3, blue: 0.2, alpha: 1) // red
        case .ice:    return SKColor(red: 0.7, green: 0.85, blue: 1.0, alpha: 1) // light blue
        case .gravel: return SKColor(red: 0.6, green: 0.55, blue: 0.4, alpha: 1) // tan
        }
    }

    private static func frictionForSurface(_ surface: SurfaceType) -> CGFloat {
        switch surface {
        case .road:   return 0.5
        case .boost:  return 0.3
        case .ice:    return 0.05
        case .gravel: return 0.8
        }
    }
}
```

- [ ] **Step 5: Create track JSON files**

Create `SketchDrive/SketchDrive/Resources/Tracks/track_flat_road.json`:
```json
{
    "id": "flat_road",
    "name": "First Drive",
    "type": "sideView",
    "segments": [
        { "type": "flat", "length": 800, "surface": "road" },
        { "type": "hill", "length": 200, "height": 40, "surface": "road" },
        { "type": "flat", "length": 400, "surface": "road" }
    ]
}
```

Create `SketchDrive/SketchDrive/Resources/Tracks/track_hills.json`:
```json
{
    "id": "hills",
    "name": "Hill Climb",
    "type": "sideView",
    "segments": [
        { "type": "flat", "length": 300, "surface": "road" },
        { "type": "hill", "length": 250, "height": 120, "surface": "road" },
        { "type": "flat", "length": 150, "surface": "road" },
        { "type": "hill", "length": 300, "height": 200, "surface": "road" },
        { "type": "valley", "length": 200, "height": 80, "surface": "road" },
        { "type": "flat", "length": 300, "surface": "road" }
    ]
}
```

Create `SketchDrive/SketchDrive/Resources/Tracks/track_oval.json`:
```json
{
    "id": "oval",
    "name": "Oval Circuit",
    "type": "topDown",
    "waypoints": [
        { "x": 200, "y": 150 },
        { "x": 600, "y": 150 },
        { "x": 700, "y": 250 },
        { "x": 700, "y": 450 },
        { "x": 600, "y": 550 },
        { "x": 200, "y": 550 },
        { "x": 100, "y": 450 },
        { "x": 100, "y": 250 }
    ],
    "trackWidth": 80
}
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' -only-testing:SketchDriveTests/TrackBuilderTests 2>&1 | tail -10
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add SketchDrive/Models/TrackData.swift SketchDrive/Game/TrackBuilder.swift SketchDrive/Resources/Tracks/ SketchDriveTests/Game/TrackBuilderTests.swift
git commit -m "feat: add TrackData models, TrackBuilder, and 3 MVP tracks"
```

---

### Task 8: VehicleNode (SpriteKit)

**Files:**
- Create: `SketchDrive/SketchDrive/Game/VehicleNode.swift`

No unit test — this is a SpriteKit rendering component, verified visually in Task 12.

- [ ] **Step 1: Implement VehicleNode**

Create `SketchDrive/SketchDrive/Game/VehicleNode.swift`:
```swift
import SpriteKit

class VehicleNode: SKSpriteNode {

    let vehicleProperties: VehicleProperties
    let physicsConfig: VehiclePhysicsConfig

    /// Create a vehicle node from analyzed properties and a cropped texture image.
    init(texture: SKTexture, properties: VehicleProperties, difficulty: Difficulty) {
        self.vehicleProperties = properties
        self.physicsConfig = DifficultyScaler.scale(
            config: VehiclePhysicsConfig.from(properties: properties),
            difficulty: difficulty
        )

        // Scale texture to a reasonable game size (max 120pt wide)
        let maxWidth: CGFloat = 120
        let scale = min(maxWidth / texture.size().width, 1.0)
        let size = CGSize(
            width: texture.size().width * scale,
            height: texture.size().height * scale
        )

        super.init(texture: texture, color: .clear, size: size)

        self.name = "vehicle"
        setupPhysicsBody(size: size)
    }

    required init?(coder aDecoder: NSCoder) {
        fatalError("init(coder:) not supported")
    }

    private func setupPhysicsBody(size: CGSize) {
        // Use rectangle physics body for MVP (contour-based body is more complex)
        // TODO: Use contourPath for pixel-perfect physics in later iteration
        let body = SKPhysicsBody(rectangleOf: size)
        body.mass = physicsConfig.mass / 1000  // SpriteKit uses lighter units
        body.friction = physicsConfig.friction
        body.linearDamping = physicsConfig.linearDamping
        body.restitution = physicsConfig.restitution
        body.allowsRotation = true
        body.categoryBitMask = PhysicsCategory.vehicle
        body.contactTestBitMask = PhysicsCategory.ground | PhysicsCategory.finish
        body.collisionBitMask = PhysicsCategory.ground | PhysicsCategory.boundary

        self.physicsBody = body
    }

    /// Apply engine force in the vehicle's forward direction.
    func applyThrottle() {
        let force = CGVector(
            dx: physicsConfig.engineForce * cos(zRotation),
            dy: physicsConfig.engineForce * sin(zRotation)
        )
        physicsBody?.applyForce(force)
    }

    /// Apply brake force opposing current velocity.
    func applyBrake() {
        guard let velocity = physicsBody?.velocity else { return }
        let speed = hypot(velocity.dx, velocity.dy)
        guard speed > 1 else { return }

        let brakeVector = CGVector(
            dx: -velocity.dx / speed * physicsConfig.brakeForce,
            dy: -velocity.dy / speed * physicsConfig.brakeForce
        )
        physicsBody?.applyForce(brakeVector)
    }

    /// Apply steering torque (for top-down mode).
    func applySteer(direction: CGFloat) { // -1 = left, 1 = right
        let torque = -direction * physicsConfig.maxSteeringAngle * 0.5
        physicsBody?.applyTorque(torque)
    }

    /// Apply aerodynamic drag force opposing velocity.
    func applyAeroDrag() {
        guard let velocity = physicsBody?.velocity else { return }
        let speed = hypot(velocity.dx, velocity.dy)
        guard speed > 0.1 else { return }

        let dragMagnitude = physicsConfig.aerodynamics.dragForce(atVelocity: speed)
        let dragForce = CGVector(
            dx: -velocity.dx / speed * dragMagnitude * 0.001, // scale for SpriteKit
            dy: -velocity.dy / speed * dragMagnitude * 0.001
        )
        physicsBody?.applyForce(dragForce)
    }
}

/// Physics collision categories.
struct PhysicsCategory {
    static let vehicle: UInt32  = 0x1 << 0
    static let ground: UInt32   = 0x1 << 1
    static let boundary: UInt32 = 0x1 << 2
    static let finish: UInt32   = 0x1 << 3
}
```

- [ ] **Step 2: Commit**

```bash
git add SketchDrive/Game/VehicleNode.swift
git commit -m "feat: add VehicleNode — SpriteKit sprite with physics from contour analysis"
```

---

### Task 9: Side-View Scene

**Files:**
- Create: `SketchDrive/SketchDrive/Game/SideViewScene.swift`
- Create: `SketchDrive/SketchDrive/Game/SideViewControls.swift`

- [ ] **Step 1: Implement SideViewControls**

Create `SketchDrive/SketchDrive/Game/SideViewControls.swift`:
```swift
import SpriteKit

class SideViewControls: SKNode {

    var isGasPressed = false
    var isBrakePressed = false

    private let gasButton = SKShapeNode(rectOf: CGSize(width: 120, height: 80), cornerRadius: 16)
    private let brakeButton = SKShapeNode(rectOf: CGSize(width: 120, height: 80), cornerRadius: 16)

    // Track which touch activated which button to handle slide-off correctly
    private var gasTouches = Set<UITouch>()
    private var brakeTouches = Set<UITouch>()

    func setup(sceneSize: CGSize) {
        isUserInteractionEnabled = true
        zPosition = 100

        // Gas button — bottom right
        gasButton.position = CGPoint(x: sceneSize.width / 2 - 100, y: -sceneSize.height / 2 + 80)
        gasButton.fillColor = SKColor(red: 0.2, green: 0.8, blue: 0.3, alpha: 0.7)
        gasButton.name = "gas"
        let gasLabel = SKLabelNode(text: "GAS")
        gasLabel.fontName = "AvenirNext-Bold"
        gasLabel.fontSize = 24
        gasLabel.verticalAlignmentMode = .center
        gasButton.addChild(gasLabel)
        addChild(gasButton)

        // Brake button — bottom left
        brakeButton.position = CGPoint(x: -sceneSize.width / 2 + 100, y: -sceneSize.height / 2 + 80)
        brakeButton.fillColor = SKColor(red: 0.9, green: 0.3, blue: 0.2, alpha: 0.7)
        brakeButton.name = "brake"
        let brakeLabel = SKLabelNode(text: "BRAKE")
        brakeLabel.fontName = "AvenirNext-Bold"
        brakeLabel.fontSize = 24
        brakeLabel.verticalAlignmentMode = .center
        brakeButton.addChild(brakeLabel)
        addChild(brakeButton)
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches {
            let loc = touch.location(in: self)
            if gasButton.contains(loc) { gasTouches.insert(touch); isGasPressed = true }
            if brakeButton.contains(loc) { brakeTouches.insert(touch); isBrakePressed = true }
        }
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches {
            gasTouches.remove(touch)
            brakeTouches.remove(touch)
        }
        isGasPressed = !gasTouches.isEmpty
        isBrakePressed = !brakeTouches.isEmpty
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        gasTouches.removeAll()
        brakeTouches.removeAll()
        isGasPressed = false
        isBrakePressed = false
    }
}
```

- [ ] **Step 2: Implement SideViewScene**

Create `SketchDrive/SketchDrive/Game/SideViewScene.swift`:
```swift
import SpriteKit

class SideViewScene: SKScene, SKPhysicsContactDelegate {

    var vehicle: VehicleNode!
    var trackDefinition: TrackDefinition!
    var onFinish: ((TimeInterval) -> Void)?

    private let controls = SideViewControls()
    private let camera2D = SKCameraNode()
    private var startTime: TimeInterval = 0
    private var lastUpdateTime: TimeInterval = 0
    private var isRaceFinished = false

    override func didMove(to view: SKView) {
        backgroundColor = SKColor(red: 0.6, green: 0.85, blue: 1.0, alpha: 1) // sky blue

        physicsWorld.gravity = CGVector(dx: 0, dy: -9.8)
        physicsWorld.contactDelegate = self

        // Camera
        camera2D.position = CGPoint(x: size.width / 2, y: size.height / 2)
        addChild(camera2D)
        self.camera = camera2D

        // Build track
        let trackNode = TrackBuilder.buildSideView(from: trackDefinition)
        addChild(trackNode)

        // Place vehicle at start
        vehicle.position = CGPoint(x: 100, y: 350)
        vehicle.zRotation = 0
        addChild(vehicle)

        // Finish line at end of track
        let totalLength = trackDefinition.segments?.reduce(0) { $0 + $1.length } ?? 1000
        let finish = SKSpriteNode(color: .yellow, size: CGSize(width: 10, height: 200))
        finish.position = CGPoint(x: totalLength - 50, y: 300)
        finish.physicsBody = SKPhysicsBody(rectangleOf: finish.size)
        finish.physicsBody?.isDynamic = false
        finish.physicsBody?.categoryBitMask = PhysicsCategory.finish
        finish.name = "finish"
        addChild(finish)

        // Ground boundary
        let ground = SKNode()
        ground.position = CGPoint(x: 0, y: -50)
        ground.physicsBody = SKPhysicsBody(edgeFrom: CGPoint(x: -200, y: 0), to: CGPoint(x: totalLength + 200, y: 0))
        ground.physicsBody?.categoryBitMask = PhysicsCategory.boundary
        addChild(ground)

        // Controls
        controls.setup(sceneSize: size)
        camera2D.addChild(controls)

        startTime = 0
    }

    override func update(_ currentTime: TimeInterval) {
        guard !isRaceFinished else { return }

        // Use SpriteKit's own time source consistently
        if startTime == 0 { startTime = currentTime }
        lastUpdateTime = currentTime

        // Apply controls
        if controls.isGasPressed {
            vehicle.applyThrottle()
        }
        if controls.isBrakePressed {
            vehicle.applyBrake()
        }

        // Aero drag every frame
        vehicle.applyAeroDrag()

        // Camera follows vehicle
        camera2D.position.x = vehicle.position.x + 200
        camera2D.position.y = max(vehicle.position.y, size.height / 2)
    }

    func didBegin(_ contact: SKPhysicsContact) {
        let names = [contact.bodyA.node?.name, contact.bodyB.node?.name]
        if names.contains("finish") && names.contains("vehicle") {
            guard !isRaceFinished else { return }
            isRaceFinished = true
            let elapsed = lastUpdateTime - startTime
            onFinish?(elapsed)
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add SketchDrive/Game/SideViewScene.swift SketchDrive/Game/SideViewControls.swift
git commit -m "feat: add SideViewScene with terrain, controls, and finish detection"
```

---

### Task 10: Top-Down Scene

**Files:**
- Create: `SketchDrive/SketchDrive/Game/TopDownScene.swift`
- Create: `SketchDrive/SketchDrive/Game/TopDownControls.swift`

- [ ] **Step 1: Implement TopDownControls**

Create `SketchDrive/SketchDrive/Game/TopDownControls.swift`:
```swift
import SpriteKit

class TopDownControls: SKNode {

    var isGasPressed = false
    var isBrakePressed = false
    var steerDirection: CGFloat = 0  // -1 left, 0 center, 1 right

    private let gasButton = SKShapeNode(rectOf: CGSize(width: 120, height: 80), cornerRadius: 16)
    private let brakeButton = SKShapeNode(rectOf: CGSize(width: 120, height: 80), cornerRadius: 16)
    private let steerLeftButton = SKShapeNode(rectOf: CGSize(width: 80, height: 80), cornerRadius: 16)
    private let steerRightButton = SKShapeNode(rectOf: CGSize(width: 80, height: 80), cornerRadius: 16)

    // Track which touch activated which button to handle slide-off correctly
    private var gasTouches = Set<UITouch>()
    private var brakeTouches = Set<UITouch>()
    private var steerLeftTouches = Set<UITouch>()
    private var steerRightTouches = Set<UITouch>()

    func setup(sceneSize: CGSize) {
        isUserInteractionEnabled = true
        zPosition = 100

        // Gas — bottom right
        gasButton.position = CGPoint(x: sceneSize.width / 2 - 100, y: -sceneSize.height / 2 + 80)
        gasButton.fillColor = SKColor(red: 0.2, green: 0.8, blue: 0.3, alpha: 0.7)
        gasButton.name = "gas"
        let gasLabel = SKLabelNode(text: "GAS")
        gasLabel.fontName = "AvenirNext-Bold"
        gasLabel.fontSize = 24
        gasLabel.verticalAlignmentMode = .center
        gasButton.addChild(gasLabel)
        addChild(gasButton)

        // Brake — bottom right (above gas)
        brakeButton.position = CGPoint(x: sceneSize.width / 2 - 100, y: -sceneSize.height / 2 + 180)
        brakeButton.fillColor = SKColor(red: 0.9, green: 0.3, blue: 0.2, alpha: 0.7)
        brakeButton.name = "brake"
        let brakeLabel = SKLabelNode(text: "BRAKE")
        brakeLabel.fontName = "AvenirNext-Bold"
        brakeLabel.fontSize = 24
        brakeLabel.verticalAlignmentMode = .center
        brakeButton.addChild(brakeLabel)
        addChild(brakeButton)

        // Steer left — bottom left
        steerLeftButton.position = CGPoint(x: -sceneSize.width / 2 + 80, y: -sceneSize.height / 2 + 80)
        steerLeftButton.fillColor = SKColor(white: 0.5, alpha: 0.7)
        steerLeftButton.name = "steer_left"
        let leftLabel = SKLabelNode(text: "◀")
        leftLabel.fontSize = 32
        leftLabel.verticalAlignmentMode = .center
        steerLeftButton.addChild(leftLabel)
        addChild(steerLeftButton)

        // Steer right — bottom left (next to left)
        steerRightButton.position = CGPoint(x: -sceneSize.width / 2 + 180, y: -sceneSize.height / 2 + 80)
        steerRightButton.fillColor = SKColor(white: 0.5, alpha: 0.7)
        steerRightButton.name = "steer_right"
        let rightLabel = SKLabelNode(text: "▶")
        rightLabel.fontSize = 32
        rightLabel.verticalAlignmentMode = .center
        steerRightButton.addChild(rightLabel)
        addChild(steerRightButton)
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches {
            let loc = touch.location(in: self)
            if gasButton.contains(loc) { gasTouches.insert(touch); isGasPressed = true }
            if brakeButton.contains(loc) { brakeTouches.insert(touch); isBrakePressed = true }
            if steerLeftButton.contains(loc) { steerLeftTouches.insert(touch) }
            if steerRightButton.contains(loc) { steerRightTouches.insert(touch) }
            updateSteerDirection()
        }
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        for touch in touches {
            gasTouches.remove(touch)
            brakeTouches.remove(touch)
            steerLeftTouches.remove(touch)
            steerRightTouches.remove(touch)
        }
        isGasPressed = !gasTouches.isEmpty
        isBrakePressed = !brakeTouches.isEmpty
        updateSteerDirection()
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        gasTouches.removeAll()
        brakeTouches.removeAll()
        steerLeftTouches.removeAll()
        steerRightTouches.removeAll()
        isGasPressed = false
        isBrakePressed = false
        steerDirection = 0
    }

    private func updateSteerDirection() {
        let left = !steerLeftTouches.isEmpty
        let right = !steerRightTouches.isEmpty
        if left && !right { steerDirection = -1 }
        else if right && !left { steerDirection = 1 }
        else { steerDirection = 0 }
    }
}
```

- [ ] **Step 2: Implement TopDownScene**

Create `SketchDrive/SketchDrive/Game/TopDownScene.swift`:
```swift
import SpriteKit

class TopDownScene: SKScene, SKPhysicsContactDelegate {

    var vehicle: VehicleNode!
    var trackDefinition: TrackDefinition!
    var onFinish: ((TimeInterval) -> Void)?

    private let controls = TopDownControls()
    private let camera2D = SKCameraNode()
    private var startTime: TimeInterval = 0
    private var lastUpdateTime: TimeInterval = 0
    private var isRaceFinished = false
    private var lapStartPosition: CGPoint = .zero

    override func didMove(to view: SKView) {
        backgroundColor = SKColor(red: 0.3, green: 0.6, blue: 0.2, alpha: 1) // grass green

        physicsWorld.gravity = CGVector(dx: 0, dy: 0) // no gravity in top-down
        physicsWorld.contactDelegate = self

        // Camera
        addChild(camera2D)
        self.camera = camera2D

        // Build track
        let trackNode = TrackBuilder.buildTopDown(from: trackDefinition)
        addChild(trackNode)

        // Place vehicle at first waypoint
        if let first = trackDefinition.waypoints?.first {
            vehicle.position = CGPoint(x: first.x, y: first.y)
            lapStartPosition = vehicle.position
        }
        vehicle.zRotation = 0
        addChild(vehicle)

        // Finish line at start (complete a lap)
        let finish = SKSpriteNode(color: .yellow.withAlphaComponent(0.5), size: CGSize(width: 80, height: 20))
        finish.position = lapStartPosition
        finish.physicsBody = SKPhysicsBody(rectangleOf: finish.size)
        finish.physicsBody?.isDynamic = false
        finish.physicsBody?.categoryBitMask = PhysicsCategory.finish
        finish.name = "finish"
        addChild(finish)

        // Controls
        controls.setup(sceneSize: size)
        camera2D.addChild(controls)

        startTime = 0
    }

    override func update(_ currentTime: TimeInterval) {
        guard !isRaceFinished else { return }

        // Use SpriteKit's own time source consistently
        if startTime == 0 { startTime = currentTime }
        lastUpdateTime = currentTime

        if controls.isGasPressed {
            vehicle.applyThrottle()
        }
        if controls.isBrakePressed {
            vehicle.applyBrake()
        }
        if controls.steerDirection != 0 {
            vehicle.applySteer(direction: controls.steerDirection)
        }

        vehicle.applyAeroDrag()

        // Camera follows vehicle
        camera2D.position = vehicle.position
    }

    func didBegin(_ contact: SKPhysicsContact) {
        let names = [contact.bodyA.node?.name, contact.bodyB.node?.name]
        if names.contains("finish") && names.contains("vehicle") {
            // Only count finish after driving away from start
            let dist = hypot(vehicle.position.x - lapStartPosition.x, vehicle.position.y - lapStartPosition.y)
            guard dist > 200 else { return } // must drive away first — ignore start overlap

            guard !isRaceFinished else { return }
            isRaceFinished = true
            let elapsed = lastUpdateTime - startTime
            onFinish?(elapsed)
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add SketchDrive/Game/TopDownScene.swift SketchDrive/Game/TopDownControls.swift
git commit -m "feat: add TopDownScene with steering controls and lap detection"
```

---

### Task 11: Mission System

**Files:**
- Create: `SketchDrive/SketchDrive/Models/MissionData.swift`
- Create: `SketchDrive/SketchDrive/Missions/MissionManager.swift`
- Create: `SketchDrive/SketchDrive/Resources/Missions/missions.json`
- Test: `SketchDrive/SketchDriveTests/Missions/MissionManagerTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/Missions/MissionManagerTests.swift`:
```swift
import XCTest
@testable import SketchDrive

final class MissionManagerTests: XCTestCase {

    func testLoadMissionsFromJSON() throws {
        let json = """
        [
            {
                "id": "first_drive",
                "title": "First Drive!",
                "description": "Draw any car and see it drive!",
                "trackId": "flat_road",
                "photoAngle": "side",
                "starThresholds": [60, 40, 25],
                "unlockRequirement": 0
            }
        ]
        """.data(using: .utf8)!

        let missions = try JSONDecoder().decode([Mission].self, from: json)
        XCTAssertEqual(missions.count, 1)
        XCTAssertEqual(missions[0].id, "first_drive")
        XCTAssertEqual(missions[0].photoAngle, .side)
    }

    func testStarCalculation() {
        let thresholds: [TimeInterval] = [60, 40, 25] // 1 star < 60s, 2 stars < 40s, 3 stars < 25s
        XCTAssertEqual(MissionManager.calculateStars(time: 70, thresholds: thresholds), 0)
        XCTAssertEqual(MissionManager.calculateStars(time: 50, thresholds: thresholds), 1)
        XCTAssertEqual(MissionManager.calculateStars(time: 35, thresholds: thresholds), 2)
        XCTAssertEqual(MissionManager.calculateStars(time: 20, thresholds: thresholds), 3)
    }

    func testMissionUnlocking() {
        let manager = MissionManager()
        let missions = [
            Mission(id: "m1", title: "M1", description: "", trackId: "t1", photoAngle: .side, starThresholds: [60, 40, 25], unlockRequirement: 0),
            Mission(id: "m2", title: "M2", description: "", trackId: "t2", photoAngle: .side, starThresholds: [60, 40, 25], unlockRequirement: 1),
            Mission(id: "m3", title: "M3", description: "", trackId: "t3", photoAngle: .top, starThresholds: [60, 40, 25], unlockRequirement: 3),
        ]
        manager.missions = missions

        // Initially only m1 is unlocked (requires 0 total stars)
        XCTAssertTrue(manager.isUnlocked(missionId: "m1"))
        XCTAssertFalse(manager.isUnlocked(missionId: "m2"))

        // Complete m1 with 2 stars
        manager.recordResult(missionId: "m1", stars: 2)
        XCTAssertTrue(manager.isUnlocked(missionId: "m2"))   // needs 1 star
        XCTAssertFalse(manager.isUnlocked(missionId: "m3"))  // needs 3 stars

        // Complete m2 with 1 star (total = 3)
        manager.recordResult(missionId: "m2", stars: 1)
        XCTAssertTrue(manager.isUnlocked(missionId: "m3"))
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

Expected: FAIL

- [ ] **Step 3: Implement MissionData**

Create `SketchDrive/SketchDrive/Models/MissionData.swift`:
```swift
import Foundation

enum PhotoAngle: String, Codable {
    case side
    case top
}

struct Mission: Codable, Identifiable {
    let id: String
    let title: String
    let description: String
    let trackId: String
    let photoAngle: PhotoAngle
    let starThresholds: [TimeInterval]  // [1-star, 2-star, 3-star] time limits in seconds
    let unlockRequirement: Int          // total stars needed to unlock
}
```

- [ ] **Step 4: Implement MissionManager**

Create `SketchDrive/SketchDrive/Missions/MissionManager.swift`:
```swift
import Foundation

class MissionManager: ObservableObject {

    @Published var missions: [Mission] = []
    @Published var results: [String: Int] = [:]  // missionId → best stars

    var totalStars: Int {
        results.values.reduce(0, +)
    }

    func loadMissions() {
        guard let url = Bundle.main.url(forResource: "missions", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode([Mission].self, from: data) else {
            return
        }
        missions = decoded
    }

    func isUnlocked(missionId: String) -> Bool {
        guard let mission = missions.first(where: { $0.id == missionId }) else { return false }
        return totalStars >= mission.unlockRequirement
    }

    func recordResult(missionId: String, stars: Int) {
        let current = results[missionId] ?? 0
        results[missionId] = max(current, stars)  // keep best score
    }

    static func calculateStars(time: TimeInterval, thresholds: [TimeInterval]) -> Int {
        // thresholds = [1-star-limit, 2-star-limit, 3-star-limit]
        // Lower time = better. Earn stars for beating each threshold.
        var stars = 0
        for threshold in thresholds {
            if time <= threshold { stars += 1 }
        }
        return stars
    }
}
```

- [ ] **Step 5: Create missions.json**

Create `SketchDrive/SketchDrive/Resources/Missions/missions.json`:
```json
[
    {
        "id": "first_drive",
        "title": "First Drive!",
        "description": "Draw any car you like and take a photo from the side. Let's see it drive!",
        "trackId": "flat_road",
        "photoAngle": "side",
        "starThresholds": [60, 40, 25],
        "unlockRequirement": 0
    },
    {
        "id": "hill_climb",
        "title": "Steep Hills!",
        "description": "This road has big hills. You need a strong car! Draw something powerful.",
        "trackId": "hills",
        "photoAngle": "side",
        "starThresholds": [90, 60, 40],
        "unlockRequirement": 1
    },
    {
        "id": "oval_race",
        "title": "Race Track!",
        "description": "A real race track! Draw the fastest car you can and photograph it from above.",
        "trackId": "oval",
        "photoAngle": "top",
        "starThresholds": [45, 30, 20],
        "unlockRequirement": 3
    }
]
```

- [ ] **Step 6: Run tests — verify they pass**

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add SketchDrive/Models/MissionData.swift SketchDrive/Missions/MissionManager.swift SketchDrive/Resources/Missions/missions.json SketchDriveTests/Missions/MissionManagerTests.swift
git commit -m "feat: add Mission system with 3 MVP missions, star calculation, and unlock logic"
```

---

### Task 12: Garage (SwiftData Persistence)

**Files:**
- Create: `SketchDrive/SketchDrive/Garage/StoredVehicle.swift`
- Create: `SketchDrive/SketchDrive/Garage/VehicleStore.swift`
- Test: `SketchDrive/SketchDriveTests/Garage/VehicleStoreTests.swift`

- [ ] **Step 1: Write the test**

Create `SketchDrive/SketchDriveTests/Garage/VehicleStoreTests.swift`:
```swift
import XCTest
import SwiftData
@testable import SketchDrive

final class VehicleStoreTests: XCTestCase {

    var container: ModelContainer!

    override func setUp() {
        super.setUp()
        let schema = Schema([StoredVehicle.self])
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        container = try! ModelContainer(for: schema, configurations: [config])
    }

    func testSaveAndLoadVehicle() throws {
        let context = container.mainContext
        let store = VehicleStore(context: context)

        let vehicle = StoredVehicle(
            name: "Red Racer",
            photoData: Data([0xFF]),
            mass: 800,
            dragCoefficient: 0.25,
            frontalArea: 1.5,
            cogX: 0.5,
            cogY: 0.4,
            stability: 0.85
        )

        store.save(vehicle: vehicle)

        let loaded = store.allVehicles()
        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded[0].name, "Red Racer")
        XCTAssertEqual(loaded[0].mass, 800)
    }

    func testDeleteVehicle() throws {
        let context = container.mainContext
        let store = VehicleStore(context: context)

        let vehicle = StoredVehicle(
            name: "Delete Me",
            photoData: Data(),
            mass: 500,
            dragCoefficient: 0.3,
            frontalArea: 2.0,
            cogX: 0.5,
            cogY: 0.5,
            stability: 0.5
        )

        store.save(vehicle: vehicle)
        XCTAssertEqual(store.allVehicles().count, 1)

        store.delete(vehicle: vehicle)
        XCTAssertEqual(store.allVehicles().count, 0)
    }
}
```

- [ ] **Step 2: Run test — verify it fails**

Expected: FAIL

- [ ] **Step 3: Implement StoredVehicle**

Create `SketchDrive/SketchDrive/Garage/StoredVehicle.swift`:
```swift
import Foundation
import SwiftData

@Model
final class StoredVehicle {
    var name: String
    @Attribute(.externalStorage) var photoData: Data  // PNG of cropped texture
    var mass: Double
    var dragCoefficient: Double
    var frontalArea: Double
    var cogX: Double
    var cogY: Double
    var stability: Double
    var createdAt: Date

    init(name: String, photoData: Data, mass: Double, dragCoefficient: Double,
         frontalArea: Double, cogX: Double, cogY: Double, stability: Double) {
        self.name = name
        self.photoData = photoData
        self.mass = mass
        self.dragCoefficient = dragCoefficient
        self.frontalArea = frontalArea
        self.cogX = cogX
        self.cogY = cogY
        self.stability = stability
        self.createdAt = Date()
    }

    /// Convert back to VehicleProperties for gameplay.
    func toProperties() -> VehicleProperties {
        VehicleProperties(
            mass: CGFloat(mass),
            dragCoefficient: CGFloat(dragCoefficient),
            frontalArea: CGFloat(frontalArea),
            centerOfGravity: CGPoint(x: cogX, y: cogY),
            stability: CGFloat(stability),
            contourPath: CGMutablePath()  // contour not stored — uses rect physics
        )
    }
}
```

- [ ] **Step 4: Implement VehicleStore**

Create `SketchDrive/SketchDrive/Garage/VehicleStore.swift`:
```swift
import SwiftData
import Foundation

struct VehicleStore {
    let context: ModelContext

    func save(vehicle: StoredVehicle) {
        context.insert(vehicle)
        try? context.save()
    }

    func allVehicles() -> [StoredVehicle] {
        let descriptor = FetchDescriptor<StoredVehicle>(
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )
        return (try? context.fetch(descriptor)) ?? []
    }

    func delete(vehicle: StoredVehicle) {
        context.delete(vehicle)
        try? context.save()
    }
}
```

- [ ] **Step 5: Run tests — verify they pass**

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add SketchDrive/Garage/ SketchDriveTests/Garage/
git commit -m "feat: add SwiftData vehicle garage — save, load, delete vehicles"
```

---

### Task 13: Camera Manager

**Files:**
- Create: `SketchDrive/SketchDrive/Camera/CameraManager.swift`

No unit test — AVFoundation camera requires device. Verified on device in Task 15.

- [ ] **Step 1: Implement CameraManager**

Create `SketchDrive/SketchDrive/Camera/CameraManager.swift`:
```swift
import AVFoundation
import UIKit

class CameraManager: NSObject, ObservableObject {

    @Published var capturedImage: UIImage?
    @Published var isAuthorized = false

    private let session = AVCaptureSession()
    private let output = AVCapturePhotoOutput()

    var previewLayer: AVCaptureVideoPreviewLayer {
        let layer = AVCaptureVideoPreviewLayer(session: session)
        layer.videoGravity = .resizeAspectFill
        return layer
    }

    func requestPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isAuthorized = true
            setupSession()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    self?.isAuthorized = granted
                    if granted { self?.setupSession() }
                }
            }
        default:
            isAuthorized = false
        }
    }

    private func setupSession() {
        session.beginConfiguration()
        session.sessionPreset = .photo

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input = try? AVCaptureDeviceInput(device: device),
              session.canAddInput(input) else {
            session.commitConfiguration()
            return
        }

        session.addInput(input)

        if session.canAddOutput(output) {
            session.addOutput(output)
        }

        session.commitConfiguration()
    }

    func startSession() {
        guard !session.isRunning else { return }
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.startRunning()
        }
    }

    func stopSession() {
        guard session.isRunning else { return }
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            self?.session.stopRunning()
        }
    }

    func capturePhoto() {
        let settings = AVCapturePhotoSettings()
        output.capturePhoto(with: settings, delegate: self)
    }
}

extension CameraManager: AVCapturePhotoCaptureDelegate {
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        guard let data = photo.fileDataRepresentation(),
              let image = UIImage(data: data) else { return }
        DispatchQueue.main.async {
            self.capturedImage = image
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add SketchDrive/Camera/CameraManager.swift
git commit -m "feat: add CameraManager — AVFoundation photo capture for vehicle/track scanning"
```

---

### Task 14: SwiftUI Navigation & Views

**Files:**
- Create: `SketchDrive/SketchDrive/App/AppState.swift`
- Create: `SketchDrive/SketchDrive/UI/MainMenuView.swift`
- Create: `SketchDrive/SketchDrive/UI/MissionListView.swift`
- Create: `SketchDrive/SketchDrive/UI/MissionBriefingView.swift`
- Create: `SketchDrive/SketchDrive/UI/CameraView.swift`
- Create: `SketchDrive/SketchDrive/UI/VehicleResultView.swift`
- Create: `SketchDrive/SketchDrive/UI/GameContainerView.swift`
- Create: `SketchDrive/SketchDrive/UI/RaceResultView.swift`
- Create: `SketchDrive/SketchDrive/UI/GarageView.swift`
- Modify: `SketchDrive/SketchDrive/App/SketchDriveApp.swift`

- [ ] **Step 1: Implement AppState**

Create `SketchDrive/SketchDrive/App/AppState.swift`:
```swift
import SwiftUI

enum AppScreen: Hashable {
    case mainMenu
    case missionList
    case missionBriefing(Mission)
    case camera(Mission)
    case vehicleResult(mission: Mission, image: UIImage)
    case game(mission: Mission, properties: VehicleProperties, texture: UIImage)
    case raceResult(mission: Mission, time: TimeInterval, stars: Int)
    case garage

    // Hashable conformance for NavigationStack
    func hash(into hasher: inout Hasher) {
        switch self {
        case .mainMenu: hasher.combine(0)
        case .missionList: hasher.combine(1)
        case .missionBriefing(let m): hasher.combine(2); hasher.combine(m.id)
        case .camera(let m): hasher.combine(3); hasher.combine(m.id)
        case .vehicleResult(let m, _): hasher.combine(4); hasher.combine(m.id)
        case .game(let m, _, _): hasher.combine(5); hasher.combine(m.id)
        case .raceResult(let m, _, _): hasher.combine(6); hasher.combine(m.id)
        case .garage: hasher.combine(7)
        }
    }

    static func == (lhs: AppScreen, rhs: AppScreen) -> Bool {
        switch (lhs, rhs) {
        case (.mainMenu, .mainMenu): return true
        case (.missionList, .missionList): return true
        case (.missionBriefing(let a), .missionBriefing(let b)): return a.id == b.id
        case (.camera(let a), .camera(let b)): return a.id == b.id
        case (.vehicleResult(let a, _), .vehicleResult(let b, _)): return a.id == b.id
        case (.game(let a, _, _), .game(let b, _, _)): return a.id == b.id
        case (.raceResult(let a, _, _), .raceResult(let b, _, _)): return a.id == b.id
        case (.garage, .garage): return true
        default: return false
        }
    }
}

class AppState: ObservableObject {
    @Published var path = NavigationPath()

    func navigate(to screen: AppScreen) {
        path.append(screen)
    }

    func popToRoot() {
        path = NavigationPath()
    }

    func pop() {
        if !path.isEmpty { path.removeLast() }
    }
}
```

- [ ] **Step 2: Implement MainMenuView**

Create `SketchDrive/SketchDrive/UI/MainMenuView.swift`:
```swift
import SwiftUI

struct MainMenuView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 40) {
            Text("SketchDrive")
                .font(.system(size: 64, weight: .bold, design: .rounded))
                .foregroundStyle(.blue)

            Text("Draw it. Drive it.")
                .font(.title2)
                .foregroundStyle(.secondary)

            VStack(spacing: 20) {
                Button {
                    appState.navigate(to: .missionList)
                } label: {
                    Label("Play", systemImage: "flag.checkered")
                        .font(.title)
                        .frame(maxWidth: 300)
                        .padding()
                        .background(.blue)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }

                Button {
                    appState.navigate(to: .garage)
                } label: {
                    Label("Garage", systemImage: "car.fill")
                        .font(.title)
                        .frame(maxWidth: 300)
                        .padding()
                        .background(.orange)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }
            }
        }
        .padding()
    }
}
```

- [ ] **Step 3: Implement MissionListView**

Create `SketchDrive/SketchDrive/UI/MissionListView.swift`:
```swift
import SwiftUI

struct MissionListView: View {
    @EnvironmentObject var appState: AppState
    @EnvironmentObject var missionManager: MissionManager

    var body: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 280))], spacing: 20) {
                ForEach(missionManager.missions) { mission in
                    let unlocked = missionManager.isUnlocked(missionId: mission.id)
                    let stars = missionManager.results[mission.id] ?? 0

                    Button {
                        if unlocked {
                            appState.navigate(to: .missionBriefing(mission))
                        }
                    } label: {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(mission.title)
                                    .font(.title2.bold())
                                Spacer()
                                if !unlocked {
                                    Image(systemName: "lock.fill")
                                        .foregroundStyle(.gray)
                                }
                            }
                            Text(mission.description)
                                .font(.body)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)

                            HStack {
                                ForEach(0..<3) { i in
                                    Image(systemName: i < stars ? "star.fill" : "star")
                                        .foregroundStyle(.yellow)
                                }
                                Spacer()
                                Text(mission.photoAngle == .side ? "Side view" : "Top view")
                                    .font(.caption)
                                    .padding(6)
                                    .background(.blue.opacity(0.1))
                                    .clipShape(Capsule())
                            }
                        }
                        .padding()
                        .background(unlocked ? Color(.systemBackground) : Color(.systemGray5))
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .shadow(radius: unlocked ? 4 : 0)
                    }
                    .disabled(!unlocked)
                }
            }
            .padding()
        }
        .navigationTitle("Missions")
    }
}
```

- [ ] **Step 4: Implement MissionBriefingView**

Create `SketchDrive/SketchDrive/UI/MissionBriefingView.swift`:
```swift
import SwiftUI

struct MissionBriefingView: View {
    let mission: Mission
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 30) {
            Text(mission.title)
                .font(.largeTitle.bold())

            Text(mission.description)
                .font(.title3)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)

            // Photo instruction
            VStack(spacing: 12) {
                Image(systemName: mission.photoAngle == .side ? "iphone.landscape.radiowaves.left.and.right" : "iphone.radiowaves.left.and.right")
                    .font(.system(size: 60))
                    .foregroundStyle(.blue)

                Text(mission.photoAngle == .side
                     ? "Draw a car and photograph it from the SIDE"
                     : "Draw a car and photograph it from ABOVE")
                    .font(.title3)
                    .multilineTextAlignment(.center)
            }
            .padding()
            .background(.blue.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 16))

            Button {
                appState.navigate(to: .camera(mission))
            } label: {
                Label("Take Photo", systemImage: "camera.fill")
                    .font(.title2)
                    .padding()
                    .frame(maxWidth: 300)
                    .background(.blue)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
            }
        }
        .padding()
    }
}
```

- [ ] **Step 5: Implement CameraView**

Create `SketchDrive/SketchDrive/UI/CameraView.swift`:
```swift
import SwiftUI
import AVFoundation

struct CameraView: View {
    let mission: Mission
    @EnvironmentObject var appState: AppState
    @StateObject private var camera = CameraManager()

    var body: some View {
        ZStack {
            // Camera preview
            CameraPreviewRepresentable(camera: camera)
                .ignoresSafeArea()

            VStack {
                Spacer()

                // Capture button
                Button {
                    camera.capturePhoto()
                } label: {
                    Circle()
                        .fill(.white)
                        .frame(width: 80, height: 80)
                        .overlay(Circle().stroke(.gray, lineWidth: 4))
                }
                .padding(.bottom, 40)
            }
        }
        .onAppear {
            camera.requestPermission()
            camera.startSession()
        }
        .onDisappear {
            camera.stopSession()
        }
        .onChange(of: camera.capturedImage) { _, image in
            if let image {
                appState.navigate(to: .vehicleResult(mission: mission, image: image))
            }
        }
    }
}

/// UIViewRepresentable wrapper for AVCaptureVideoPreviewLayer.
struct CameraPreviewRepresentable: UIViewRepresentable {
    let camera: CameraManager

    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        let layer = camera.previewLayer
        layer.frame = view.bounds
        view.layer.addSublayer(layer)
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        if let layer = uiView.layer.sublayers?.first as? AVCaptureVideoPreviewLayer {
            layer.frame = uiView.bounds
        }
    }
}
```

- [ ] **Step 6: Implement VehicleResultView**

Create `SketchDrive/SketchDrive/UI/VehicleResultView.swift`:
```swift
import SwiftUI

struct VehicleResultView: View {
    let mission: Mission
    let image: UIImage
    @EnvironmentObject var appState: AppState
    @Environment(\.modelContext) var modelContext

    @State private var vehicleProperties: VehicleProperties?
    @State private var croppedTexture: UIImage?
    @State private var vehicleName = ""
    @State private var isAnalyzing = true
    @State private var error: String?

    var body: some View {
        VStack(spacing: 20) {
            if isAnalyzing {
                ProgressView("Analyzing your vehicle...")
                    .font(.title2)
            } else if let error {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 60))
                        .foregroundStyle(.orange)
                    Text(error)
                        .font(.title3)
                    Button("Try Again") {
                        appState.pop()
                    }
                    .buttonStyle(.borderedProminent)
                }
            } else if let props = vehicleProperties, let texture = croppedTexture {
                // Vehicle preview
                Image(uiImage: texture)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 200)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .shadow(radius: 4)

                // Name input
                TextField("Name your vehicle", text: $vehicleName)
                    .font(.title2)
                    .textFieldStyle(.roundedBorder)
                    .frame(maxWidth: 300)

                // Properties
                VStack(alignment: .leading, spacing: 8) {
                    propertyRow("Weight", value: props.weightCategory.rawValue, icon: "scalemass")
                    propertyRow("Aerodynamics", value: props.aeroCategory.rawValue, icon: "wind")
                    propertyRow("Stability", value: String(format: "%.0f%%", props.stability * 100), icon: "arrow.left.and.right")
                }
                .padding()
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 12))

                // Race button
                Button {
                    saveToGarage(props: props, texture: texture)
                    appState.navigate(to: .game(mission: mission, properties: props, texture: texture))
                } label: {
                    Label("Race!", systemImage: "flag.checkered")
                        .font(.title2)
                        .padding()
                        .frame(maxWidth: 300)
                        .background(.green)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }
            }
        }
        .padding()
        .task {
            await analyzeImage()
        }
    }

    private func propertyRow(_ label: String, value: String, icon: String) -> some View {
        HStack {
            Image(systemName: icon)
                .frame(width: 30)
            Text(label)
            Spacer()
            Text(value)
                .bold()
        }
    }

    private func analyzeImage() async {
        do {
            let result = try await ContourExtractor.extract(from: image)
            let props = VehicleAnalyzer.analyze(contour: result.contour)
            await MainActor.run {
                self.vehicleProperties = props
                self.croppedTexture = result.texture
                self.isAnalyzing = false
            }
        } catch {
            await MainActor.run {
                self.error = "Could not find a vehicle in the photo. Make sure to draw on white paper with a dark pen."
                self.isAnalyzing = false
            }
        }
    }

    private func saveToGarage(props: VehicleProperties, texture: UIImage) {
        let name = vehicleName.isEmpty ? "Vehicle \(Date().formatted(.dateTime.hour().minute()))" : vehicleName
        let stored = StoredVehicle(
            name: name,
            photoData: texture.pngData() ?? Data(),
            mass: Double(props.mass),
            dragCoefficient: Double(props.dragCoefficient),
            frontalArea: Double(props.frontalArea),
            cogX: Double(props.centerOfGravity.x),
            cogY: Double(props.centerOfGravity.y),
            stability: Double(props.stability)
        )
        let store = VehicleStore(context: modelContext)
        store.save(vehicle: stored)
    }
}
```

- [ ] **Step 7: Implement GameContainerView**

Create `SketchDrive/SketchDrive/UI/GameContainerView.swift`:
```swift
import SwiftUI
import SpriteKit

struct GameContainerView: View {
    let mission: Mission
    let vehicleProperties: VehicleProperties
    let vehicleTexture: UIImage
    @EnvironmentObject var appState: AppState
    @EnvironmentObject var missionManager: MissionManager

    @State private var scene: SKScene?

    var body: some View {
        Group {
            if let scene {
                SpriteView(scene: scene)
                    .ignoresSafeArea()
            } else {
                ProgressView("Loading track...")
            }
        }
        .onAppear {
            setupScene()
        }
        .navigationBarBackButtonHidden()
    }

    private func setupScene() {
        // Load track definition
        guard let trackDef = loadTrack(id: mission.trackId) else { return }

        let skTexture = SKTexture(image: vehicleTexture)
        let vehicleNode = VehicleNode(
            texture: skTexture,
            properties: vehicleProperties,
            difficulty: .playful
        )

        let onFinish: (TimeInterval) -> Void = { time in
            let stars = MissionManager.calculateStars(
                time: time,
                thresholds: mission.starThresholds
            )
            missionManager.recordResult(missionId: mission.id, stars: stars)
            DispatchQueue.main.async {
                appState.navigate(to: .raceResult(mission: mission, time: time, stars: stars))
            }
        }

        let screenSize = CGSize(width: 1194, height: 834) // iPad Pro landscape

        switch trackDef.type {
        case .sideView:
            let sideScene = SideViewScene(size: screenSize)
            sideScene.scaleMode = .aspectFill
            sideScene.vehicle = vehicleNode
            sideScene.trackDefinition = trackDef
            sideScene.onFinish = onFinish
            scene = sideScene

        case .topDown:
            let topScene = TopDownScene(size: screenSize)
            topScene.scaleMode = .aspectFill
            topScene.vehicle = vehicleNode
            topScene.trackDefinition = trackDef
            topScene.onFinish = onFinish
            scene = topScene
        }
    }

    private func loadTrack(id: String) -> TrackDefinition? {
        guard let url = Bundle.main.url(forResource: "track_\(id)", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(TrackDefinition.self, from: data)
    }
}
```

- [ ] **Step 8: Implement RaceResultView**

Create `SketchDrive/SketchDrive/UI/RaceResultView.swift`:
```swift
import SwiftUI

struct RaceResultView: View {
    let mission: Mission
    let time: TimeInterval
    let stars: Int
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack(spacing: 30) {
            Text(stars > 0 ? "Great job!" : "Try again!")
                .font(.largeTitle.bold())

            // Stars
            HStack(spacing: 12) {
                ForEach(0..<3) { i in
                    Image(systemName: i < stars ? "star.fill" : "star")
                        .font(.system(size: 50))
                        .foregroundStyle(i < stars ? .yellow : .gray)
                }
            }

            // Time
            Text(String(format: "Time: %.1f seconds", time))
                .font(.title2)

            // Feedback
            Text(feedbackMessage)
                .font(.title3)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 40)
                .foregroundStyle(.secondary)

            HStack(spacing: 20) {
                Button {
                    // Go back to briefing to retry
                    appState.popToRoot()
                    appState.navigate(to: .missionList)
                    appState.navigate(to: .missionBriefing(mission))
                } label: {
                    Label("Retry", systemImage: "arrow.counterclockwise")
                        .font(.title3)
                        .padding()
                        .frame(maxWidth: 200)
                        .background(.orange)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }

                Button {
                    appState.popToRoot()
                    appState.navigate(to: .missionList)
                } label: {
                    Label("Missions", systemImage: "list.bullet")
                        .font(.title3)
                        .padding()
                        .frame(maxWidth: 200)
                        .background(.blue)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }
            }
        }
        .padding()
        .navigationBarBackButtonHidden()
    }

    private var feedbackMessage: String {
        switch stars {
        case 0: return "Your car didn't quite make it. Try drawing a different shape!"
        case 1: return "You finished! Can you make a faster car?"
        case 2: return "Nice driving! A more streamlined car might get you 3 stars."
        case 3: return "Perfect run! Your car was a great match for this track!"
        default: return ""
        }
    }
}
```

- [ ] **Step 9: Implement GarageView**

Create `SketchDrive/SketchDrive/UI/GarageView.swift`:
```swift
import SwiftUI
import SwiftData

struct GarageView: View {
    @Query(sort: \StoredVehicle.createdAt, order: .reverse) var vehicles: [StoredVehicle]
    @Environment(\.modelContext) var modelContext

    var body: some View {
        Group {
            if vehicles.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "car.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.gray)
                    Text("No vehicles yet")
                        .font(.title2)
                        .foregroundStyle(.secondary)
                    Text("Complete a mission to add your first car!")
                        .foregroundStyle(.tertiary)
                }
            } else {
                ScrollView {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 200))], spacing: 16) {
                        ForEach(vehicles) { vehicle in
                            vehicleCard(vehicle)
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationTitle("Garage")
    }

    private func vehicleCard(_ vehicle: StoredVehicle) -> some View {
        VStack(spacing: 8) {
            if let uiImage = UIImage(data: vehicle.photoData) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFit()
                    .frame(height: 120)
                    .background(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            Text(vehicle.name)
                .font(.headline)

            HStack(spacing: 4) {
                Label(String(format: "%.0fkg", vehicle.mass), systemImage: "scalemass")
                Spacer()
                Label(String(format: "Cd %.2f", vehicle.dragCoefficient), systemImage: "wind")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(radius: 2)
    }
}
```

- [ ] **Step 10: Update SketchDriveApp with navigation**

Modify `SketchDrive/SketchDrive/App/SketchDriveApp.swift`:
```swift
import SwiftUI
import SwiftData

@main
struct SketchDriveApp: App {
    @StateObject private var appState = AppState()
    @StateObject private var missionManager = MissionManager()

    var body: some Scene {
        WindowGroup {
            NavigationStack(path: $appState.path) {
                MainMenuView()
                    .navigationDestination(for: AppScreen.self) { screen in
                        switch screen {
                        case .mainMenu:
                            MainMenuView()
                        case .missionList:
                            MissionListView()
                        case .missionBriefing(let mission):
                            MissionBriefingView(mission: mission)
                        case .camera(let mission):
                            CameraView(mission: mission)
                        case .vehicleResult(let mission, let image):
                            VehicleResultView(mission: mission, image: image)
                        case .game(let mission, let props, let texture):
                            GameContainerView(mission: mission, vehicleProperties: props, vehicleTexture: texture)
                        case .raceResult(let mission, let time, let stars):
                            RaceResultView(mission: mission, time: time, stars: stars)
                        case .garage:
                            GarageView()
                        }
                    }
            }
            .environmentObject(appState)
            .environmentObject(missionManager)
            .onAppear {
                missionManager.loadMissions()
            }
        }
        .modelContainer(for: StoredVehicle.self)
    }
}
```

- [ ] **Step 11: Build and verify**

```bash
xcodebuild -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' build 2>&1 | tail -5
```
Expected: `** BUILD SUCCEEDED **`

- [ ] **Step 12: Commit**

```bash
git add SketchDrive/App/ SketchDrive/UI/
git commit -m "feat: add full SwiftUI navigation flow — menu, missions, camera, game, results, garage"
```

---

### Task 15: Integration Test on Device

**Files:** None new — manual verification

- [ ] **Step 1: Run all unit tests**

```bash
xcodebuild test -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' 2>&1 | grep -E '(Test Suite|Tests|PASS|FAIL)' | tail -20
```
Expected: All tests pass

- [ ] **Step 2: Run on iPad simulator**

```bash
xcodebuild -scheme SketchDrive -destination 'platform=iOS Simulator,name=iPad Pro 13-inch (M4)' build
open -a Simulator
xcrun simctl boot "iPad Pro 13-inch (M4)" 2>/dev/null
xcrun simctl install booted build/Build/Products/Debug-iphonesimulator/SketchDrive.app
xcrun simctl launch booted com.sketchdrive.SketchDrive
```

Verify:
- Main menu shows with Play and Garage buttons
- Mission list shows 3 missions (first unlocked, others locked)
- Tapping first mission shows briefing with photo instruction
- Camera opens (will be blank in simulator — test on device for real photos)
- Garage is empty initially

- [ ] **Step 3: Test with a sample image on device**

On a real iPad:
1. Draw a simple car shape on white paper
2. Open mission 1, take a photo from the side
3. Verify contour extraction works — vehicle shape is visible
4. Verify properties display (weight, aero, stability)
5. Name the vehicle, tap Race
6. Verify side-view scene loads with terrain
7. Verify gas/brake controls work
8. Drive to finish line, verify star result appears
9. Check garage — vehicle should be saved

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: SketchDrive MVP complete — photo-to-vehicle pipeline, 2 track types, 3 missions, garage"
```
