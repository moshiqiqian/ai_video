const cv = document.getElementById('c');
const g = cv.getContext('2d');
const W = 1920, H = 1080;

/* ---------- style: swiss grid, one typeface, one red ---------- */
const C = { page: '#EAE9E5', ink: '#111111', red: '#E30613', mute: '#77766F', grid: '#D6D5D0', paper: '#F6F5F1' };
const F = '"Microsoft YaHei", "Noto Sans SC", sans-serif';

/* ---------- lines (filled from lines.json at runtime) ---------- */
let LINES = [];
export const DUR = 22;

/* ---------- deterministic helpers ---------- */
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const easeOut = p => 1 - Math.pow(1 - clamp(p), 3);
const easeInOut = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const snap = (t, a, d) => easeOut((t - a) / d);

/* ---------- drawing ---------- */
function grid(alpha = 1) {
  g.save();
  g.globalAlpha = alpha;
  g.strokeStyle = C.grid;
  g.lineWidth = 1;
  for (let i = 0; i <= 12; i++) {
    const x = 96 + i * 146;
    g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke();
  }
  for (let j = 0; j <= 7; j++) {
    const y = 84 + j * 146;
    g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke();
  }
  g.restore();
}

function label(text, x, y, color = C.mute) {
  g.save();
  g.fillStyle = color;
  g.font = `500 20px ${F}`;
  g.letterSpacing = '4px';
  g.fillText(text, x, y);
  g.restore();
}

function reveal(text, x, y, size, p, color = C.ink, weight = 800) {
  if (p <= 0) return;
  const w = g.measureText(text).width;
  g.save();
  g.beginPath();
  g.rect(x - 4, y - size * 1.05, w + 8, size * 1.32);
  g.clip();
  g.fillStyle = color;
  g.font = `${weight} ${size}px ${F}`;
  g.letterSpacing = '0px';
  g.fillText(text, x, y + (1 - easeOut(p)) * size * 1.15);
  g.restore();
}

function frameNumber(t) {
  const f = Math.floor(t * 24);
  return String(f).padStart(5, '0');
}

/* ---------- scenes ---------- */
function scene1(t, a, b) {
  const p = seg(t, a, b);
  grid(clamp(1 - p * 1.4, 0, 1) * .9);
  label('01 / 输入', 96, 120);
  label('A FILM MADE IN CODE', 1400, 120);

  g.save();
  g.fillStyle = C.red;
  g.fillRect(96, 196, 56, 56);
  g.restore();

  g.font = `800 168px ${F}`;
  const w1 = g.measureText('文字').width;
  reveal('文字', 150, 420, 168, snap(t, a + .15, .5));
  reveal('电影', 150, 610, 168, snap(t, a + .38, .5), C.ink);

  const bar = easeOut(seg(t, a + .55, b - .2));
  g.save();
  g.fillStyle = C.red;
  g.fillRect(150, 680, 320 * bar, 14);
  g.restore();

  label('FROM SCRIPT TO PICTURE', 150, 760);
}

function scene2(t, a, b) {
  const p = seg(t, a, b);
  grid(.35);
  label('02 / 渲染', 96, 120);
  label('FRAME BY FRAME', 1400, 120);

  const n = Math.round(lerp(0, 24, easeOut(seg(t, a + .1, a + 1.5))));
  g.save();
  g.fillStyle = C.red;
  g.font = `800 420px ${F}`;
  g.letterSpacing = '-14px';
  g.fillText(String(n), 96, 640);
  g.restore();

  g.save();
  g.fillStyle = C.ink;
  g.font = `500 34px ${F}`;
  g.fillText('帧 / 秒', 800, 600);
  g.restore();

  g.save();
  g.fillStyle = C.ink;
  g.font = `800 96px ${F}`;
  const w = g.measureText('没有一帧是拍出来的').width;
  g.beginPath(); g.rect(96, 760, w + 20, 120); g.clip();
  g.fillText('没有一帧是拍出来的', 96, 850 + (1 - easeOut(seg(t, a + .5, a + 1.0))) * 110);
  g.restore();

  // a ruler of ticks, one per frame
  g.save();
  g.strokeStyle = C.ink; g.lineWidth = 2;
  for (let i = 0; i < 24; i++) {
    const x = 96 + i * 66;
    const h = (i / 24) <= seg(t, a + .2, a + 1.6) ? 42 : 16;
    g.globalAlpha = .9;
    g.beginPath(); g.moveTo(x, 930); g.lineTo(x, 930 - h); g.stroke();
  }
  g.restore();
}

function scene3(t, a, b) {
  const p = seg(t, a, b);
  grid(.35);
  label('03 / 一条时间轴', 96, 120);
  label('ONE TIMELINE', 1400, 120);

  const cols = [
    { name: '文字', note: 'script' },
    { name: '图表', note: 'data' },
    { name: '声音', note: 'voice' },
  ];
  const baseY = 900;
  const startX = 96;

  cols.forEach((c, i) => {
    const q = easeOut(seg(t, a + .15 + i * .16, a + .65 + i * .16));
    const x = startX + i * 580;
    const h = 420 * (0.5 + i * 0.22);
    g.save();
    g.fillStyle = i === 1 ? C.red : C.ink;
    g.globalAlpha = .92;
    g.fillRect(x, baseY - h * q, 300, h * q);
    g.restore();

    g.save();
    g.fillStyle = C.paper;
    g.font = `800 68px ${F}`;
    g.fillText(c.name, x + 26, baseY - 34);
    g.restore();

    label(c.note.toUpperCase(), x, baseY + 52);

    g.save();
    g.strokeStyle = C.ink; g.lineWidth = 2; g.globalAlpha = .35;
    g.beginPath(); g.moveTo(x, baseY + 18); g.lineTo(x + 300, baseY + 18); g.stroke();
    g.restore();
  });

  // a red dot travelling across the baseline
  const dx = lerp(startX, startX + 2 * 580 + 300, easeInOut(seg(t, a + .8, b - .2)));
  g.save();
  g.fillStyle = C.red;
  g.beginPath(); g.arc(dx, baseY + 18, 14, 0, Math.PI * 2); g.fill();
  g.restore();
}

function scene4(t, a, b) {
  grid(.25);
  label('04 / 输出', 96, 120);
  label('END FRAME', 1400, 120);

  g.save();
  g.font = `800 150px ${F}`;
  const w = g.measureText('代码即画面').width;
  reveal('代码即画面', (W - w) / 2, 470, 150, snap(t, a + .2, .6));
  g.restore();

  const bar = easeOut(seg(t, a + .6, a + 1.4));
  g.save();
  g.fillStyle = C.red;
  g.fillRect((W - 300 * bar) / 2, 560, 300 * bar, 12);
  g.restore();

  g.save();
  g.fillStyle = C.mute;
  g.font = `500 30px ${F}`;
  const sub = 'HTML · CANVAS · TIMELINE';
  const sw = g.measureText(sub).width;
  g.fillText(sub, (W - sw) / 2, 660);
  g.restore();

  // seal
  const q = easeOut(seg(t, a + 1.0, a + 1.25));
  if (q > 0) {
    g.save();
    g.globalAlpha = q;
    g.translate(1480, 820);
    g.rotate(-0.06);
    g.scale(lerp(1.6, 1, q), lerp(1.6, 1, q));
    g.fillStyle = C.red;
    g.fillRect(-62, -62, 124, 124);
    g.fillStyle = C.paper;
    g.font = `800 64px ${F}`;
    g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('作', 0, 4);
    g.restore();
  }
}

/* ---------- subtitles ---------- */
function subtitles(t) {
  const L = LINES.find(l => t >= l.t0 && t <= l.t1);
  if (!L) return;
  const p = seg(t, L.t0, L.t0 + .22) * seg(t, L.t1 + .01, L.t1 - .15);
  g.save();
  g.globalAlpha = clamp(p);
  g.fillStyle = C.red;
  g.fillRect(96, 1006, 14, 14);
  g.fillStyle = C.ink;
  g.font = `500 38px ${F}`;
  g.fillText(L.text, 128, 1024);
  g.restore();
}

/* ---------- master ---------- */
window.render = t => {
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1;
  g.fillStyle = C.page;
  g.fillRect(0, 0, W, H);

  const S = [
    [0.0, 5.6, scene1],
    [5.6, 11.2, scene2],
    [11.2, 17.4, scene3],
    [17.4, DUR, scene4],
  ];
  for (const [a, b, fn] of S) {
    if (t >= a && t < b + 0.001) fn(t, a, b);
  }

  // running meta
  g.save();
  g.fillStyle = C.mute;
  g.font = `500 20px ${F}`;
  g.textAlign = 'right';
  g.fillText(`T ${t.toFixed(2)}  F ${frameNumber(t)}`, 1824, 1050);
  g.restore();

  subtitles(t);
};

window.TEXTS = t => {
  const L = LINES.find(l => t >= l.t0 && t <= l.t1);
  return L ? [{ id: L.id, text: L.text, x0: 96, y0: 990, x1: 1824, y1: 1040 }] : [];
};

window.DUR = DUR;
window.EV = [
  { t: 0.2, type: 'cut' },
  { t: 5.6, type: 'cut' },
  { t: 11.2, type: 'cut' },
  { t: 17.4, type: 'cut' },
];

/* ---------- load lines, then ready ---------- */
try {
  const res = await fetch('./lines.json');
  LINES = await res.json();
} catch (e) {
  LINES = [];
}
window.READY = true;
