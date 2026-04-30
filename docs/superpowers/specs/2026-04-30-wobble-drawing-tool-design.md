# Wobble — ritverktyg med liv-effekt

## Översikt

Ett litet webbverktyg där man ritar frihandsstreck och former. Allt man ritar "andas" — wobblar mjukt på plats så det känns levande. Ingen sparfunktion, ingen server: en enda HTML-fil som öppnas i webbläsaren.

## Mål och avgränsningar

**Mål:**
- Snabbt att öppna och börja rita
- Tydlig liv-känsla — objekten andas asynkront, inte synkat
- Frihandsstreck och tre grundformer (cirkel, kvadrat, triangel)
- Inga beroenden, en fil

**Inte i scope:**
- Spara eller exportera (bilder, video, GIF)
- Lager, ångra/gör om, markering, redigering av befintliga objekt
- Mobil-optimering (men touch fungerar om det går lätt)
- Server, build-steg, npm-paket

## Plats och stack

- Plats: `/Users/b2/Documents/Proj/LLM/wobble/`
- En fil: `index.html` med inline `<style>` och `<script>`
- Rendering: Canvas 2D
- Animation: `requestAnimationFrame`

## UI-layout

```
┌──────────────────────────────────────────────┐
│ ┌─────┐                                      │
│ │ ✏  │                                      │
│ │ ○  │                                      │
│ │ □  │                                      │
│ │ △  │           CANVAS                     │
│ │ ─  │                                      │
│ │ 🎨 │                                      │
│ │ 🗑  │                                      │
│ └─────┘                                      │
└──────────────────────────────────────────────┘
```

Verktygsfält till vänster (smal kolumn ~64px). Canvas fyller resten. Aktivt verktyg markeras visuellt.

**Verktygsfält uppifrån och ner:**
1. Penna (frihand) — default
2. Cirkel
3. Kvadrat
4. Triangel
5. Linjebredd-slider (1–20 px)
6. Färgväljare (`<input type="color">`)
7. Rensa allt (papperskorg)

## Datamodell

Ett enda array `objects` håller allt i ritordning:

```js
// Frihandsstreck
{ type: 'pen', points: [{x,y}, ...], color, width, phase }

// Form
{ type: 'circle' | 'square' | 'triangle', x, y, size, color, phase }
```

`phase` är ett slumpat tal (0–2π) som sätts när objektet skapas. Det avgör objektets wobble-fas så att alla objekt andas i otakt.

`size` för former: standardvärde t.ex. 60 px (radie för cirkel, halv-sida för kvadrat/triangel).

## Interaktion

**Penna:**
- `mousedown` → starta nytt streck, lägg till första punkten
- `mousemove` (med musen nere) → lägg till punkt om avståndet till föregående > 2 px
- `mouseup` → avsluta strecket

**Form (cirkel/kvadrat/triangel):**
- `mousedown` på canvas → placera form där, med standardstorlek

**Färg/linjebredd:** påverkar nästa objekt som skapas, inte befintliga.

**Rensa allt:** tömmer `objects` direkt utan bekräftelse (det är en lekplats).

## Liv-effekt

Per frame i render-loopen, för varje objekt:

```js
const t = performance.now() / 1000
const wobble = Math.sin(t * SPEED + obj.phase) * AMPLITUDE
```

**Frihandsstreck:** varje punkt får en liten offset i x och y. Olika frekvenser för x och y så det inte bara är diagonal-gungning. Faseffekt per punkt baserat på punktens index så strecket "kryper" lite längs sin egen längd.

**Former:** wobblar storlek (skalfaktor 0.95–1.05) och får en liten translation (±2 px). Triangel kan dessutom rotera ±3°.

**Konstanter (utgångsvärden, justerbara):**
- `SPEED = 1.5` (rad/sek)
- `AMPLITUDE = 2` (px för punkter)
- `SCALE_AMPLITUDE = 0.05` (5% storlek)

Värden behöver kännas rätt — finjustera tills det andas mjukt utan att se nervöst ut.

## Render-pipeline

```
loop():
  ctx.clearRect(...)
  for obj in objects:
    if pen: drawWobblyPath(obj, t)
    else:   drawWobblyShape(obj, t)
  requestAnimationFrame(loop)
```

Canvas storlek sätts till `window.innerWidth - sidebarWidth` × `window.innerHeight`. Hantera `resize` genom att uppdatera canvas-storlek.

## Testning

Manuellt i webbläsare:
- Rita ett streck — det ska wobbla mjukt
- Placera flera former — de ska andas i otakt (inte synkat)
- Byt färg och linjebredd — nästa objekt får nya värden, gamla behåller sina
- Rensa allt — canvas blir tom
- Resize fönstret — canvas anpassar sig

## Filöversikt

```
wobble/
└── index.html   # allt: HTML + CSS + JS
```
