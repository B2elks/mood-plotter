const WS_URL = `wss://${location.hostname}/ws`;

const questionNum = document.getElementById('question-num');
const questionText = document.getElementById('question-text');
const questionBox = document.getElementById('question-box');
const queueInfo = document.getElementById('queue-info');
const callerInfo = document.getElementById('caller-info');
const callerName = document.getElementById('caller-name');
const answerArea = document.getElementById('answer-area');
const answerText = document.getElementById('answer-text');
const resultArea = document.getElementById('result-area');
const resultIcon = document.getElementById('result-icon');
const resultText = document.getElementById('result-text');
const leaderboardEl = document.getElementById('leaderboard');
const hostSvg = document.getElementById('host');
const confettiCanvas = document.getElementById('confetti');
const ctx = confettiCanvas.getContext('2d');

let ws = null;
let confettiParticles = [];

function connect() {
  ws = new WebSocket(WS_URL);
  ws.onopen = () => console.log('Show WS connected');
  ws.onmessage = (e) => { handleEvent(JSON.parse(e.data)); };
  ws.onclose = () => {
    console.log('Show WS disconnected, reconnecting...');
    setTimeout(connect, 2000);
  };
}

function handleEvent(event) {
  switch (event.type) {
    case 'init':
      updateLeaderboard(event.leaderboard);
      queueInfo.textContent = `📞 ${event.queue_size} i kö`;
      break;
    case 'question':
      questionNum.textContent = `FRÅGA ${event.idx + 1} AV ${event.total}`;
      questionText.textContent = event.question;
      questionBox.classList.add('active');
      answerArea.style.display = 'none';
      resultArea.style.display = 'none';
      callerInfo.style.display = 'none';
      setHostState('asking');
      break;
    case 'caller_active':
      callerName.textContent = event.name + ' svarar...';
      callerInfo.style.display = '';
      setHostState('listening');
      break;
    case 'queue_update':
      queueInfo.textContent = `📞 ${event.size} i kö`;
      break;
    case 'answer':
      answerArea.style.display = '';
      answerText.textContent = event.transcript;
      break;
    case 'result':
      resultArea.style.display = '';
      resultArea.className = 'result-area ' + (event.correct ? 'correct' : 'wrong');
      resultIcon.textContent = event.correct ? '🎉' : '😢';
      resultText.textContent = event.explanation;
      if (event.correct) {
        setHostState('celebrating');
        fireConfetti();
      } else {
        setHostState('sad');
        questionBox.classList.add('shake');
        setTimeout(() => questionBox.classList.remove('shake'), 600);
      }
      break;
    case 'leaderboard':
      updateLeaderboard(event.scores);
      break;
    case 'show_state':
      if (event.state === 'idle') {
        setHostState('idle');
        questionBox.classList.remove('active');
        callerInfo.style.display = 'none';
        answerArea.style.display = 'none';
        resultArea.style.display = 'none';
      } else if (event.state === 'waiting') {
        setHostState('waiting');
      } else if (event.state === 'ended') {
        setHostState('celebrating');
      }
      break;
    case 'show_ended':
      questionNum.textContent = 'SHOWEN ÄR SLUT!';
      if (event.winner) {
        questionText.textContent = `🏆 Vinnare: ${event.winner.name} med ${event.winner.points} poäng!`;
      } else {
        questionText.textContent = 'Ingen vinnare denna gång!';
      }
      fireConfetti();
      break;
  }
}

function setHostState(state) {
  const panel = document.getElementById('character-panel');
  panel.className = 'character-panel';
  if (state === 'asking') panel.classList.add('host-talking');
  else if (state === 'celebrating') panel.classList.add('host-celebrating');
}

function updateLeaderboard(scores) {
  if (!scores || Object.keys(scores).length === 0) {
    leaderboardEl.textContent = '⭐ Väntar på deltagare...';
    return;
  }
  const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  const medals = ['🥇', '🥈', '🥉'];
  leaderboardEl.textContent = sorted.slice(0, 5).map((entry, i) =>
    `${medals[i] || '⭐'} ${entry[0]} ${entry[1]}p`
  ).join('  ·  ');
}

function fireConfetti() {
  confettiCanvas.width = window.innerWidth;
  confettiCanvas.height = window.innerHeight;
  confettiParticles = [];
  const colors = ['#ff8800', '#ffcc00', '#ff4444', '#22c55e', '#3b82f6', '#fff'];
  for (let i = 0; i < 150; i++) {
    confettiParticles.push({
      x: Math.random() * confettiCanvas.width,
      y: -20 - Math.random() * 200,
      w: 6 + Math.random() * 6,
      h: 4 + Math.random() * 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 4,
      vy: 2 + Math.random() * 4,
      rot: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 10,
    });
  }
  animateConfetti();
}

function animateConfetti() {
  ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
  let alive = false;
  for (const p of confettiParticles) {
    if (p.y > confettiCanvas.height + 20) continue;
    alive = true;
    p.x += p.vx;
    p.y += p.vy;
    p.rot += p.rotSpeed;
    p.vy += 0.05;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot * Math.PI / 180);
    ctx.fillStyle = p.color;
    ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
    ctx.restore();
  }
  if (alive) requestAnimationFrame(animateConfetti);
  else ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
}

connect();
