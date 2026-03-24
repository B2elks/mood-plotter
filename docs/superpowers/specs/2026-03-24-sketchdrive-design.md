# SketchDrive — Design Specification

## Overview

**SketchDrive** is an iPad game for children (ages 3–12) where creativity happens in the real world and the iPad brings it to life. Children draw or build cars, photograph them, and the app extracts the shape to create a playable vehicle with physics properties derived from its form. The same analog-first philosophy applies to tracks — children can draw tracks on paper, photograph them, and race their cars on them.

**Core principle:** Everything creative happens in reality — drawing, building, crafting. The iPad is the tool that animates and simulates.

**Tech stack:** Swift, SpriteKit, Vision framework, Core Image, Core ML, SwiftUI, SwiftData, AVFoundation.

**Target:** iPad (iOS 17+). Offline-first with optional online enhancements.

---

## 1. Core Game Loop

1. **Mission screen** — A mechanic guide character presents a challenge ("We need a car that can make it up this steep hill!")
2. **Track preview** — The child sees the track and its challenges (side-view or top-down)
3. **Photo instruction** — "Draw a car and photograph it from the side!" (angle depends on track type)
4. **Camera** — The child photographs their creation against a light background
5. **Vehicle analysis** — The app extracts the contour, calculates properties (weight, aerodynamics, center of gravity), and shows the result
6. **Driving** — Manual controls (gas/brake/steer) or auto-drive to see how the car performs
7. **Result** — Star rating, feedback ("Your car had great speed but tipped over in the curve — the center of gravity was too high"), suggestion to iterate

---

## 2. Image Analysis & Vehicle Creation

### Contour Extraction (offline, Vision framework)
- Child photographs their drawing/creation against a light background
- `VNDetectContoursRequest` extracts the vehicle contour
- The contour becomes a `CGPath` → converted to `SKPhysicsBody`
- The original photo is cropped along the contour and used as texture (the child's drawing lives!)

### Property Calculation (offline, from contour)
- **Aerodynamics (Cd)** — calculated from how streamlined the contour is: ratio of the contour's perimeter to an ideal streamlined shape. Flat/smooth = low drag.
- **Frontal area (A)** — height × width in the direction of travel. Used for drag force calculation.
- **Weight (mass)** — estimated from total contour area. Larger car = heavier.
- **Center of gravity** — calculated as centroid of the contour. High center = tip-prone.
- **Stability** — width-to-height ratio. Wide and low = stable. Narrow and tall = unstable.
- **Wheel placement** — the app detects the lowest points (side-view) or symmetrical rounded shapes (top-down) as wheels.

### Engineer Mode (older children)
- Displays calculated values: Cd value, weight in kg, marked center of gravity
- Real-time force arrows during driving (air resistance, friction, gravity)
- G-force display, speedometer

### Online Bonus (optional, with internet)
- Send photo for more sophisticated classification (sports car, truck, bus, etc.)
- Richer feedback and tips

---

## 3. Track Design & Perspectives

### Two Track Types

**Side-view tracks:**
- Car drives left → right through a 2D terrain profile
- Terrain with hills, valleys, slopes, jumps, tunnels
- Gravity plays a major role — center of gravity and weight determine hill climbing and jump landing
- Controls: Gas (right), Brake (left), + tilt via gyroscope or buttons

**Top-down tracks:**
- Classic racing track seen from above
- Curves, straights, narrow passages
- Aerodynamics and turning radius play a major role
- Controls: Gas, Brake, Steer left/right

### Pre-built Tracks
- ~15–20 tracks with increasing difficulty
- Each track tied to a mission from the guide character
- Built-in elements: ramps, tunnels, gravel sections, ice, steep hills, narrow passages

### Custom Tracks (photograph paper)
- Child draws a track with colored pens, photographs it
- Vision framework interprets lines as track contour
- **Color coding:**
  - Black/pencil = road
  - Red = boost/turbo
  - Blue = slippery/ice
  - Green = ramp/jump
  - Orange = gravel/slow
- Core Image filters identify colors and map to track properties
- In-app instructions show which color = what

---

## 4. Physics Engine

### Base Physics (all ages)
- SpriteKit's built-in physics (`SKPhysicsWorld`) as foundation
- Each vehicle gets properties mapped from contour analysis:
  - `mass` — from contour area
  - `friction` — based on vehicle type (wide wheels = more grip)
  - `linearDamping` — air resistance from frontal area
  - `restitution` — how much the car bounces

### Aerodynamics Model
- Drag force: `F = 0.5 * Cd * A * v²`
- `Cd` (drag coefficient) — calculated from contour streamlining
- `A` (frontal area) — vehicle height × width in travel direction
- At high speed the difference is significant: an F1 car maintains speed, a truck loses it

### Vehicle Dynamics
- **Top speed** — lighter car + good aerodynamics = higher top speed
- **Acceleration** — force/mass, heavier car = slower acceleration
- **Braking** — affected by weight and friction
- **Cornering (top-down)** — center of gravity and width determine max speed in curves
- **Hill climbing (side-view)** — force vs weight × slope, heavy car can get stuck
- **Jumping (side-view)** — light car flies further but lands harder relative to size

### Difficulty Scaling
- **Playful mode:** Physics are forgiving. All cars complete tracks, but better shape = better result (more stars).
- **Realistic mode:** Physics bite. Wrong car can actually get stuck on a hill or tip over in a curve.
- **Engineer mode:** Real-time display of force arrows, speedometer, Cd value, G-forces. Learn physics through play.

---

## 5. Mission System & Progression

### Guide Character
- A mechanic character (gender-neutral, colorful, friendly) that drives the story
- Gives missions, tips, and feedback after each run
- Adapts language to age group (simpler/harder vocabulary)

### Mission Structure
Each mission introduces a new concept or challenge:
1. "Draw a car!" — basic intro, simple flat track
2. "This hill is steep — we need a strong car!" — teaches weight vs power
3. "A narrow tunnel — your car must be small enough!" — teaches size
4. "Race track! Build the fastest car you can!" — aerodynamics
5. "Icy road — we need grip!" — friction
6. ...continuing with combinations of concepts

### Progression
- ~5 tracks per "chapter", each chapter has a theme (power, aerodynamics, grip, etc.)
- 1–3 stars per track based on time/performance
- New chapters unlock with stars
- **"Draw your own track"** unlocks after chapter 2 (~track 10) — child understands the basics by then
- **Engineer mode** unlocks after chapter 3 — for those who want to go deeper

### Garage
- All cars saved with photo, name (child names them), and properties
- Can be reused on any track
- Compare cars side by side — "why was this one faster?"

### Feedback Loop
- After each run: short analysis ("Your car had great speed but tipped in the curve — center of gravity was too high")
- Suggestion: "Try drawing a lower car next time!"
- Encourages iteration — draw, test, improve

---

## 6. Technical Architecture

### Project Structure
```
SketchDrive/
├── App/                    # App entry, navigation
├── Camera/                 # AVFoundation camera handling
├── Vision/                 # Contour detection, color analysis
│   ├── ContourExtractor    # VNDetectContoursRequest → CGPath
│   ├── ColorAnalyzer       # Core Image color detection for tracks
│   └── VehicleAnalyzer     # Calculate properties from contour
├── Physics/                # Physics models
│   ├── AerodynamicsModel   # Cd, air resistance
│   ├── VehiclePhysics      # Mass, friction, center of gravity
│   └── DifficultyScaler    # Scale physics per difficulty level
├── Game/                   # SpriteKit scenes
│   ├── SideViewScene       # Side-view tracks
│   ├── TopDownScene        # Top-down tracks
│   ├── VehicleNode         # Vehicle sprite with physics body
│   ├── TrackBuilder        # Builds tracks from data/photos
│   └── AutoPilot           # AI steering for auto-drive
├── Missions/               # Mission system
│   ├── MissionManager      # Progression, unlocking
│   ├── MissionData         # JSON-defined missions
│   └── GuideCharacter      # Mechanic, dialogues
├── Garage/                 # Saved vehicles
│   ├── VehicleStore        # Persistence (SwiftData)
│   └── VehicleCard         # UI for vehicle cards
├── UI/                     # SwiftUI views
│   ├── MainMenu
│   ├── MissionView
│   ├── CameraView
│   ├── VehicleResultView
│   ├── GarageView
│   └── EngineerOverlay     # Engineer mode HUD
├── Audio/                  # Sound effects, music
└── Resources/
    ├── Tracks/             # Pre-built tracks (JSON)
    └── Missions/           # Mission data (JSON)
```

### Key Technologies
| Function | Framework |
|---|---|
| Game engine & physics | SpriteKit |
| UI & navigation | SwiftUI |
| Camera | AVFoundation |
| Contour detection | Vision |
| Color analysis | Core Image |
| Local ML (bonus) | Core ML |
| Persistence | SwiftData |
| Audio | AVAudioEngine |

### Data Flow — Photo to Playable Vehicle
```
Camera → UIImage
  → Vision: VNDetectContoursRequest → [VNContour]
    → Select largest contour → CGPath
      → VehicleAnalyzer: calculate area, centroid, frontal area, Cd
        → VehiclePhysics object (mass, drag, friction, centerOfGravity)
          → VehicleNode: SKSpriteNode with cropped texture + SKPhysicsBody from CGPath
```

### Data Flow — Photo to Playable Track
```
Camera → UIImage
  → Vision: contour detection → track lines
  → Core Image: color analysis → boost/ice/ramp zones
    → TrackBuilder: generate SKNodes with correct physics properties
      → SideViewScene or TopDownScene depending on contour layout
```

### Offline/Online Strategy
- All core functions offline via Vision + Core Image
- Optional online: Core ML model can be downloaded for better vehicle classification
- No data leaves the device without parental approval

---

## 7. Design for Future Expansion

The architecture is designed so these can be added later without restructuring:

- **Multiplayer** — VehicleNode and track data are already serializable; sharing via Game Center or local network is additive
- **New track types** — the Scene protocol pattern allows adding new perspectives (e.g., isometric) without modifying existing code
- **More analog objects** — the Vision pipeline is generic; trees, buildings, ramps can all be photographed and brought into the game
- **Android port** — while native Swift, the physics models and mission data (JSON) are portable

---

## 8. MVP Scope

For the first buildable version:

**In:**
- Camera capture + contour extraction
- Vehicle property calculation from contour
- 1 side-view track (simple hills)
- 1 top-down track (simple oval with curves)
- Manual driving controls
- Basic physics (mass, drag, friction)
- 3 introductory missions
- Vehicle garage (save/load)
- Playful difficulty mode

**Out (later):**
- Custom track photography
- Color-coded track elements
- Auto-pilot AI
- Engineer mode
- Full mission progression (all chapters)
- Guide character with dialogue
- Realistic difficulty mode
- Online features
- Audio/music
