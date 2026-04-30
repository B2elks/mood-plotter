# Wobble Drawing Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file HTML drawing tool where freehand strokes and shapes wobble gently on the canvas, giving them a "breathing" feel.

**Architecture:** One self-contained `index.html` with inline `<style>` and `<script>`. Canvas 2D rendering. A `requestAnimationFrame` loop redraws every object each frame, applying a `sin(time * speed + phase)` wobble offset. Each object gets a random `phase` at creation so they breathe out of sync.

**Tech Stack:** HTML5 Canvas 2D, vanilla JavaScript, plain CSS. No frameworks, no build, no dependencies.

**Testing approach:** This is a visual playground tool with no JS test runner. Each task ends with a manual browser verification step describing what to look for.

---

### Task 1: Project skeleton — HTML, CSS, layout

**Files:**
- Create: `wobble/index.html`

- [ ] **Step 1: Create the directory and file with skeleton**

Create `wobble/index.html` with the full skeleton:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Wobble</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; overflow: hidden; background: #1a1a1a; }
  body { display: flex; font-family: system-ui, sans-serif; }

  #toolbar {
    width: 64px;
    background: #2a2a2a;
    border-right: 1px solid #444;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 0;
    gap: 8px;
  }

  .tool-btn {
    width: 44px;
    height: 44px;
    border: 2px solid transparent;
    border-radius: 8px;
    background: #3a3a3a;
    color: #eee;
    font-size: 20px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .tool-btn:hover { background: #4a4a4a; }
  .tool-btn.active { border-color: #6cf; background: #2a4a5a; }

  #color { width: 44px; height: 44px; border: none; border-radius: 8px; cursor: pointer; background: none; }
  #width { width: 44px; }
  .spacer { flex: 1; }

  #canvas { flex: 1; display: block; cursor: crosshair; background: #111; }
</style>
</head>
<body>
  <div id="toolbar">
    <button class="tool-btn active" data-tool="pen" title="Penna">✏</button>
    <button class="tool-btn" data-tool="circle" title="Cirkel">○</button>
    <button class="tool-btn" data-tool="square" title="Kvadrat">□</button>
    <button class="tool-btn" data-tool="triangle" title="Triangel">△</button>
    <input type="range" id="width" min="1" max="20" value="3" title="Linjebredd">
    <input type="color" id="color" value="#66ccff" title="Färg">
    <div class="spacer"></div>
    <button class="tool-btn" id="clear" title="Rensa allt">🗑</button>
  </div>
  <canvas id="canvas"></canvas>

<script>
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
  }
  window.addEventListener('resize', resize);
  resize();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify in browser**

Open `wobble/index.html` in a browser.
Expected:
- Dark background fills window
- Narrow toolbar on the left with 4 tool buttons (pen highlighted), a width slider, color picker, and a trash button at the bottom
- Black canvas fills the rest
- No console errors

- [ ] **Step 3: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): add HTML skeleton with toolbar and canvas"
```

---

### Task 2: Tool selection state

**Files:**
- Modify: `wobble/index.html` (extend `<script>`)

- [ ] **Step 1: Add state and tool-button handler**

Append to the `<script>` block (before the closing `</script>`):

```js
const state = {
  tool: 'pen',
  color: document.getElementById('color').value,
  width: parseInt(document.getElementById('width').value, 10),
};

document.querySelectorAll('.tool-btn[data-tool]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tool-btn[data-tool]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.tool = btn.dataset.tool;
  });
});

document.getElementById('color').addEventListener('input', e => {
  state.color = e.target.value;
});

document.getElementById('width').addEventListener('input', e => {
  state.width = parseInt(e.target.value, 10);
});
```

- [ ] **Step 2: Verify in browser**

Reload the page.
Expected:
- Clicking a tool button highlights it (cyan border) and de-highlights others
- Changing color picker updates `state.color` (verify by typing `state.color` in DevTools console)
- Changing width slider updates `state.width`

- [ ] **Step 3: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): wire tool selection, color, and width state"
```

---

### Task 3: Freehand drawing (no wobble yet)

**Files:**
- Modify: `wobble/index.html` (extend `<script>`)

- [ ] **Step 1: Add objects array, mouse handlers, and static render**

Append to the `<script>` block:

```js
const objects = [];
let activeStroke = null;

function canvasPos(e) {
  const r = canvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
}

canvas.addEventListener('mousedown', e => {
  const p = canvasPos(e);
  if (state.tool === 'pen') {
    activeStroke = {
      type: 'pen',
      points: [p],
      color: state.color,
      width: state.width,
      phase: Math.random() * Math.PI * 2,
    };
    objects.push(activeStroke);
  }
});

canvas.addEventListener('mousemove', e => {
  if (!activeStroke) return;
  const p = canvasPos(e);
  const last = activeStroke.points[activeStroke.points.length - 1];
  if (Math.hypot(p.x - last.x, p.y - last.y) > 2) {
    activeStroke.points.push(p);
  }
});

window.addEventListener('mouseup', () => { activeStroke = null; });

function drawStroke(obj) {
  if (obj.points.length < 2) return;
  ctx.strokeStyle = obj.color;
  ctx.lineWidth = obj.width;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(obj.points[0].x, obj.points[0].y);
  for (let i = 1; i < obj.points.length; i++) {
    ctx.lineTo(obj.points[i].x, obj.points[i].y);
  }
  ctx.stroke();
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const obj of objects) {
    if (obj.type === 'pen') drawStroke(obj);
  }
  requestAnimationFrame(render);
}
render();
```

- [ ] **Step 2: Verify in browser**

Reload the page.
Expected:
- Drag the mouse on the canvas → a smooth line follows the cursor in the chosen color and width
- Lift mouse, draw again → second stroke appears
- Change color and draw again → new stroke uses the new color, old strokes keep theirs
- No console errors

- [ ] **Step 3: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): freehand pen drawing with render loop"
```

---

### Task 4: Wobble effect on freehand strokes

**Files:**
- Modify: `wobble/index.html` — replace the `drawStroke` function

- [ ] **Step 1: Add wobble constants and replace drawStroke**

Find the current `drawStroke` function and replace it with:

```js
const WOBBLE_SPEED = 1.5;       // rad/sec
const WOBBLE_AMP = 2;           // px for stroke points

function drawStroke(obj, t) {
  if (obj.points.length < 2) return;
  ctx.strokeStyle = obj.color;
  ctx.lineWidth = obj.width;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  for (let i = 0; i < obj.points.length; i++) {
    const p = obj.points[i];
    const ph = obj.phase + i * 0.15;
    const dx = Math.sin(t * WOBBLE_SPEED + ph) * WOBBLE_AMP;
    const dy = Math.cos(t * WOBBLE_SPEED * 1.3 + ph) * WOBBLE_AMP;
    if (i === 0) ctx.moveTo(p.x + dx, p.y + dy);
    else ctx.lineTo(p.x + dx, p.y + dy);
  }
  ctx.stroke();
}
```

Also replace the `render` function so it passes `t`:

```js
function render() {
  const t = performance.now() / 1000;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const obj of objects) {
    if (obj.type === 'pen') drawStroke(obj, t);
  }
  requestAnimationFrame(render);
}
```

- [ ] **Step 2: Verify in browser**

Reload and draw a stroke.
Expected:
- The stroke wobbles softly — points jiggle ~2 px in x and y
- Different parts of one stroke wobble at slightly different times (the `i * 0.15` per-point offset makes it crawl along the stroke)
- Drawing two strokes shows them wobbling out of sync (different `phase`)
- Motion looks gentle, not jittery — if it feels nervous, lower `WOBBLE_AMP` or `WOBBLE_SPEED`

- [ ] **Step 3: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): add breathing wobble to freehand strokes"
```

---

### Task 5: Shapes — circle, square, triangle

**Files:**
- Modify: `wobble/index.html` — extend mousedown handler and add shape renderers

- [ ] **Step 1: Place shapes on click**

Find the `canvas.addEventListener('mousedown', ...)` handler and replace it with:

```js
canvas.addEventListener('mousedown', e => {
  const p = canvasPos(e);
  if (state.tool === 'pen') {
    activeStroke = {
      type: 'pen',
      points: [p],
      color: state.color,
      width: state.width,
      phase: Math.random() * Math.PI * 2,
    };
    objects.push(activeStroke);
  } else {
    objects.push({
      type: state.tool,
      x: p.x,
      y: p.y,
      size: 60,
      color: state.color,
      phase: Math.random() * Math.PI * 2,
    });
  }
});
```

- [ ] **Step 2: Add shape constants and renderer**

Append after the existing `WOBBLE_*` constants:

```js
const SHAPE_SCALE_AMP = 0.05;   // ±5% size
const SHAPE_TRANSLATE_AMP = 2;  // px
const SHAPE_ROTATE_AMP = 0.05;  // rad (~3°)
```

Append a new `drawShape` function:

```js
function drawShape(obj, t) {
  const ph = obj.phase;
  const scale = 1 + Math.sin(t * WOBBLE_SPEED + ph) * SHAPE_SCALE_AMP;
  const dx = Math.sin(t * WOBBLE_SPEED * 0.9 + ph) * SHAPE_TRANSLATE_AMP;
  const dy = Math.cos(t * WOBBLE_SPEED * 1.1 + ph) * SHAPE_TRANSLATE_AMP;
  const rot = Math.sin(t * WOBBLE_SPEED * 0.8 + ph) * SHAPE_ROTATE_AMP;

  const s = obj.size * scale;
  ctx.save();
  ctx.translate(obj.x + dx, obj.y + dy);
  ctx.rotate(rot);
  ctx.fillStyle = obj.color;

  if (obj.type === 'circle') {
    ctx.beginPath();
    ctx.arc(0, 0, s, 0, Math.PI * 2);
    ctx.fill();
  } else if (obj.type === 'square') {
    ctx.fillRect(-s, -s, s * 2, s * 2);
  } else if (obj.type === 'triangle') {
    ctx.beginPath();
    ctx.moveTo(0, -s);
    ctx.lineTo(s * 0.866, s * 0.5);
    ctx.lineTo(-s * 0.866, s * 0.5);
    ctx.closePath();
    ctx.fill();
  }

  ctx.restore();
}
```

- [ ] **Step 3: Update render to draw shapes**

Replace the `render` function with:

```js
function render() {
  const t = performance.now() / 1000;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const obj of objects) {
    if (obj.type === 'pen') drawStroke(obj, t);
    else drawShape(obj, t);
  }
  requestAnimationFrame(render);
}
```

- [ ] **Step 4: Verify in browser**

Reload.
Expected:
- Click circle tool, click on canvas → a circle appears, pulsing in size and drifting slightly
- Click square tool, click → a square appears, pulsing + rotating gently
- Click triangle tool, click → a triangle appears, also pulsing + rotating
- Multiple shapes breathe out of sync
- Pen still works alongside shapes

- [ ] **Step 5: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): add wobbling circle, square, and triangle shapes"
```

---

### Task 6: Clear button

**Files:**
- Modify: `wobble/index.html` — add clear handler

- [ ] **Step 1: Wire the clear button**

Append to the `<script>`:

```js
document.getElementById('clear').addEventListener('click', () => {
  objects.length = 0;
});
```

- [ ] **Step 2: Verify in browser**

Reload, draw some strokes and place some shapes, then click the trash button.
Expected:
- Canvas becomes empty immediately
- New strokes/shapes can be drawn after clearing

- [ ] **Step 3: Commit**

```bash
git add wobble/index.html
git commit -m "feat(wobble): clear-all button empties canvas"
```

---

### Task 7: Polish — tune wobble feel

**Files:**
- Modify: `wobble/index.html` — adjust constants if needed

- [ ] **Step 1: Open the file and try the app for ~30 seconds**

Reload and use the tool: draw a long curvy stroke, place several shapes, watch them breathe.

Ask yourself:
- Does the motion feel calm and alive, or nervous/buzzy?
- Are strokes wobbling enough to notice without becoming illegible?
- Do shapes pulse visibly without looking like they're shaking?

- [ ] **Step 2: Tune constants if it doesn't feel right**

If too jittery: lower `WOBBLE_AMP` (try 1.5) or `WOBBLE_SPEED` (try 1.2).
If too still: raise `WOBBLE_AMP` (try 2.5) or `SHAPE_SCALE_AMP` (try 0.07).

Make adjustments inline in the constants block. Reload and re-evaluate.

- [ ] **Step 3: Commit (only if values were changed)**

```bash
git add wobble/index.html
git commit -m "tune(wobble): adjust wobble constants for better feel"
```

If no changes were needed, skip the commit.

---

## Done

Open `wobble/index.html` in a browser and verify the full flow one last time:
- Pen draws wobbling strokes
- Three shape tools place shapes that breathe
- Color and width affect new objects, not existing ones
- Clear empties the canvas
- Window resize keeps the canvas filling the available space
