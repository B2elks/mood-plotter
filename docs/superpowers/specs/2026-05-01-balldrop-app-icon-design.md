# BallDrop — App-ikon (logo)

**Datum:** 2026-05-01
**Projekt:** `/Users/b2/Documents/Proj/LLM/BallDrop`

## Mål

Skapa en app-ikon (1024×1024 PNG) för BallDrop iOS-appen. Ikonen ska visa spelets karaktär (bollar som faller från en spawn-punkt) i samma färgvärld som spelet. Genereras programmatiskt via ett Swift-skript så att designen är reproducerbar och kan tweakas senare.

## Funktionella krav

### Canvas

- 1024×1024 px, kvadratisk PNG (sRGB, ingen alpha-kanal — App Store-krav).
- Inget hörnradius eller maskning — iOS appliterar masken automatiskt.

### Bakgrund

- Vertikal `CGGradient` från sky-blue till mint:
  - Top: `(0.53, 0.81, 0.92)` (matchar `LinearGradient`-toppen i `ContentView`).
  - Bottom: `(0.60, 0.85, 0.78)` (matchar `LinearGradient`-botten).

### Spawn-point (centrerad horisontellt, ~25 % från toppen)

- Position: `(512, 1024 - 256)` = `(512, 768)` i CoreGraphics-koordinater (origin nederst-vänster).
- Vit cirkel, radie 80 px, fyllning vit `alpha 0.6`, stroke vit, lineWidth 4.
- Liten "pil" under cirkeln: två linjer som möts vid `y = -84` lokalt (relativt cirkelns centrum), löper till `(±12, -68)`. Stroke vit, lineWidth 4, lineCap round. (Skalad version av spelets SpawnPoint-pil.)

### Fyra fallande bollar

- Position: under spawn-punkten, lätt böjd bana som svänger åt vänster och tillbaka, så det ser ut som rörelse.
- Storlek: 30, 40, 50, 60 px radie (största närmast botten — perspektiv/snabbhet effekt).
- Färger (4 av spelets 5 boll-färger, hoppar över gult som syns dåligt mot ljus bakgrund):
  - Boll 1 (närmast spawn-punkten, minst): rosa `(1.0, 0.42, 0.54)`.
  - Boll 2: orange `(1.0, 0.70, 0.28)`.
  - Boll 3: grön `(0.53, 0.84, 0.55)`.
  - Boll 4 (längst ner, störst): lila `(0.70, 0.53, 0.87)`.
- Varje boll: vit stroke, lineWidth 6.

**Exakta CoreGraphics-koordinater (origin nederst-vänster, y växer uppåt):**

| Boll | Radie | Position (x, y) |
|------|-------|-----------------|
| 1    | 30    | (512, 600)      |
| 2    | 40    | (480, 460)      |
| 3    | 50    | (520, 290)      |
| 4    | 60    | (496, 110)      |

(Värdena ger en mjuk S-form. Justera om visuellt nödvändigt.)

## Arkitektur

**Ny fil:** `BallDrop/scripts/GenerateAppIcon.swift` — Swift-skript med shebang `#!/usr/bin/env swift` som använder Foundation + CoreGraphics + ImageIO. Inga externa beroenden. Kan köras med `swift BallDrop/scripts/GenerateAppIcon.swift` eller direkt om markerad körbar.

Skriptet:
1. Skapar en `CGContext` 1024×1024 sRGB.
2. Ritar gradient.
3. Ritar spawn-point-cirkel + pil.
4. Ritar de fyra färgade bollarna.
5. Sparar som PNG via `CGImageDestination` till `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Icon-1024.png`.

**Uppdaterad fil:** `BallDrop/BallDrop/iOS/Assets.xcassets/AppIcon.appiconset/Contents.json` — lägg till `"filename": "Icon-1024.png"` på den enda image-entryn.

## Edge cases

- **Skriptet körs med PNG redan på plats:** överskriver. OK för v1.
- **Skriptet körs med olika Swift-toolchain:** CoreGraphics och ImageIO finns på alla macOS-versioner som projektet stödjer (14+). Inget att hantera.
- **Ikonens utseende vid små storlekar (60×60 i Spotlight):** spawn-punkten + fyra bollar bör fortfarande vara läsbara. Om det blir för rörigt kan vi reducera till 3 bollar i v2.

## Testning

Manuell verifiering:

1. Kör skriptet: `swift BallDrop/scripts/GenerateAppIcon.swift`
2. Verifiera att `Icon-1024.png` skapats och har storlek 1024×1024 (`sips -g pixelWidth -g pixelHeight`).
3. Öppna PNG-filen och kontrollera visuell kvalitet — gradient, spawn-point, fyra bollar i fallmönster.
4. Bygg iOS-target i Xcode → ikon syns på Home Screen vid installation/simulator.

## Out of scope (v1)

- Mindre ikonstorlekar (Xcode genererar automatiskt från 1024×1024 marketing-ikonen).
- Mörkt läge / tinted variant (Xcode 15+ stödjer detta men låter sig vänta).
- Mac-app-ikon (separat ärende, inte denna spec).
- Animerad logo / launch screen-art.
- Vector-källfil (SVG/PDF) — vi har skriptet som källa.
