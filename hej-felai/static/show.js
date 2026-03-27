(function() {
  const W = () => window.innerWidth;
  const H = () => window.innerHeight;
  const PADDING = 100;
  const SMALL_SIZE = 55;
  const LARGE_SIZE = 110;
  const DRIFT_RANGE = 60;
  const DRIFT_SPEED = 0.008;
  const MIN_DIST = 90;
  const FEATURE_INTERVAL = 5000;
  const POLL_INTERVAL = 5000;
  const SETTINGS_POLL = 30000;

  let bubbles = [];
  let knownIds = new Set();
  let featured = new Set();
  let container = document.getElementById('container');
  let emptyMsg = document.getElementById('empty-msg');
  let counterEl = document.getElementById('counter');

  function randomPos() {
    return {
      x: PADDING + Math.random() * (W() - PADDING * 2),
      y: PADDING + Math.random() * (H() - PADDING * 2)
    };
  }

  function createBubble(person) {
    const pos = randomPos();
    const el = document.createElement('div');
    el.className = 'bubble';

    const photoStyle = person.photo_filename
      ? `background-image:url(/uploads/${person.photo_filename})`
      : `background:linear-gradient(135deg, #5b8def44, #5b8def22)`;

    el.innerHTML = `
      <div class="photo" style="width:${SMALL_SIZE}px;height:${SMALL_SIZE}px;${photoStyle}"></div>
      <div class="info">
        <div class="name">${esc(person.name)}</div>
        <div class="role">${esc(person.role)}</div>
      </div>
    `;
    el.style.left = pos.x + 'px';
    el.style.top = pos.y + 'px';
    el.style.transform = 'translate(-50%, -50%)';
    el.style.opacity = '0';
    container.appendChild(el);

    requestAnimationFrame(() => { el.style.opacity = '1'; });

    const b = {
      id: person.id,
      el: el,
      x: pos.x,
      y: pos.y,
      tx: pos.x,
      ty: pos.y
    };
    newDriftTarget(b);
    bubbles.push(b);
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function newDriftTarget(b) {
    let nx = b.x + (Math.random() - 0.5) * DRIFT_RANGE * 2;
    let ny = b.y + (Math.random() - 0.5) * DRIFT_RANGE * 2;
    nx = Math.max(PADDING, Math.min(W() - PADDING, nx));
    ny = Math.max(PADDING, Math.min(H() - PADDING, ny));
    b.tx = nx;
    b.ty = ny;
  }

  function drift() {
    bubbles.forEach(b => {
      const dx = b.tx - b.x;
      const dy = b.ty - b.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 5) { newDriftTarget(b); return; }
      b.x += dx * DRIFT_SPEED;
      b.y += dy * DRIFT_SPEED;
      b.el.style.left = b.x + 'px';
      b.el.style.top = b.y + 'px';
    });
    resolveOverlaps();
    requestAnimationFrame(drift);
  }

  function resolveOverlaps() {
    for (let i = 0; i < bubbles.length; i++) {
      for (let j = i + 1; j < bubbles.length; j++) {
        const dx = bubbles[j].x - bubbles[i].x;
        const dy = bubbles[j].y - bubbles[i].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MIN_DIST && dist > 0) {
          const push = (MIN_DIST - dist) / 2 * 0.05;
          const nx = dx / dist;
          const ny = dy / dist;
          bubbles[i].x -= nx * push;
          bubbles[i].y -= ny * push;
          bubbles[j].x += nx * push;
          bubbles[j].y += ny * push;
        }
      }
    }
  }

  function updateFeatured() {
    if (bubbles.length === 0) return;
    const prev = new Set(featured);
    featured.clear();

    while (featured.size < Math.min(2, bubbles.length)) {
      const idx = Math.floor(Math.random() * bubbles.length);
      if (!prev.has(idx) || bubbles.length <= 2) {
        featured.add(idx);
      }
    }

    bubbles.forEach((b, i) => {
      const photo = b.el.querySelector('.photo');
      if (featured.has(i)) {
        b.el.classList.add('featured');
        photo.style.width = LARGE_SIZE + 'px';
        photo.style.height = LARGE_SIZE + 'px';
      } else {
        b.el.classList.remove('featured');
        photo.style.width = SMALL_SIZE + 'px';
        photo.style.height = SMALL_SIZE + 'px';
      }
    });
  }

  async function pollCheckins() {
    try {
      const resp = await fetch('/api/checkins');
      const people = await resp.json();

      const serverIds = new Set(people.map(p => p.id));
      if (bubbles.length > 0 && people.length === 0) {
        bubbles.forEach(b => b.el.remove());
        bubbles = [];
        knownIds.clear();
        featured.clear();
        emptyMsg.style.display = 'block';
        counterEl.textContent = '';
        return;
      }

      bubbles = bubbles.filter(b => {
        if (!serverIds.has(b.id)) {
          b.el.remove();
          knownIds.delete(b.id);
          return false;
        }
        return true;
      });

      people.forEach(p => {
        if (!knownIds.has(p.id)) {
          knownIds.add(p.id);
          createBubble(p);
        }
      });

      if (bubbles.length > 0) {
        emptyMsg.style.display = 'none';
        counterEl.textContent = bubbles.length + ' deltagare';
      }
    } catch (e) {}
  }

  async function pollSettings() {
    try {
      const resp = await fetch('/api/settings');
      const s = await resp.json();
      document.body.style.background = s.bg_color || '#0a0a1a';
      if (s.bg_image) {
        document.body.style.backgroundImage = `url('${s.bg_image}')`;
        document.body.style.backgroundSize = 'cover';
        document.body.style.backgroundPosition = 'center';
      } else {
        document.body.style.backgroundImage = 'none';
      }
      document.getElementById('event-title').textContent = s.event_title || '';
    } catch (e) {}
  }

  pollCheckins();
  requestAnimationFrame(drift);
  setInterval(pollCheckins, POLL_INTERVAL);
  setInterval(updateFeatured, FEATURE_INTERVAL);
  setInterval(pollSettings, SETTINGS_POLL);
  setTimeout(updateFeatured, 1000);
})();
