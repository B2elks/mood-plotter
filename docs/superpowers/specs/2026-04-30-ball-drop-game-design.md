# Bollspel — Sandbox Ball Drop

## Koncept

Native macOS-app (Swift + SpriteKit). Bollar faller från toppen med realistisk fysik och studsar mot block som spelaren placerar. Sandbox-läge — inget mål, bara lek och experiment.

## Arkitektur

- **Swift + SpriteKit** — inbyggd fysikmotor (gravitation, kollision, studs, friktion)
- **macOS-app** med ett fönster — spelplan + verktygspalett i sidopanelen
- Xcode-projekt, inga externa dependencies

## Spelplan

- Gradient-bakgrund (ljusblå → mintgrön pastell)
- Bollar spawnar från en punkt högst upp (klickbar/flyttbar)
- Botten är öppen — bollar faller ut och försvinner
- Väggar på sidorna (osynliga, bollar studsar)

## Bollar

- Runda, mjuka pastellfärger (rosa, orange, grön, lila, gul) — slumpas
- Vit border, mjuk skugga
- Realistisk fysik: gravitation, studs (restitution ~0.7), friktion, rotation
- Spawnar automatiskt var 1-2:a sekund (justerbar hastighet med slider)
- Max ~100 bollar, äldsta försvinner när max nås

## Block-placering

### Palett (vänster sida)

Färdiga former att dra ut:
- Rektangel (horisontell)
- Rektangel (vertikal)
- Diagonal (snedställd)
- Cirkel (rund bumper)
- Triangel

Dra från paletten → släpp på spelplanen. Kan roteras med scroll-wheel efter placering.

### Friritning

- Pennverktyg i paletten — rita med musen, streck blir fysik-block
- Automatisk förenkling (för många punkter → jämnas ut)

## Interaktion

- **Vänsterklick + drag** på spelplan: flytta befintligt block
- **Högerklick** på block: ta bort det
- **Scroll-wheel** på block: rotera
- **Spacebar**: pausa/starta bollflödet
- **C**: rensa alla block
- **+/-**: fler/färre bollar per sekund

## Visuell stil

- Ljus gradient-bakgrund (pastell himmelblå → mintgrön)
- Vita rundade block med mjuk skugga
- Bollar med pastellfärger och vit border
- Sidopanel: vit, rena ikoner, minimalt

## Tech stack

| Komponent | Teknologi |
|-----------|-----------|
| App | Swift, macOS native |
| Rendering | SpriteKit (SKScene, SKSpriteNode, SKShapeNode) |
| Fysik | SpriteKit Physics (SKPhysicsBody) |
| UI | SwiftUI (sidopanel) + SpriteKit (spelplan) |
| Projekt | Xcode, inga dependencies |

## Filstruktur

```
BallDrop/
├── BallDrop.xcodeproj
├── BallDrop/
│   ├── BallDropApp.swift        # App entry point
│   ├── ContentView.swift        # Main view: sidebar + SpriteKit view
│   ├── SidebarView.swift        # Tool palette (SwiftUI)
│   ├── GameScene.swift          # SpriteKit scene: physics, balls, blocks
│   ├── BallNode.swift           # Ball sprite with physics
│   ├── BlockNode.swift          # Block sprite with physics
│   ├── FreeDrawTool.swift       # Freehand drawing → physics path
│   ├── SpawnPoint.swift         # Draggable ball spawn point
│   └── Assets.xcassets          # App icon
```

## Scope — vad som INTE ingår

- Ingen poäng, mål, eller game over
- Inget ljud
- Inga levels eller progression
- Ingen multiplayer
- Ingen save/load
