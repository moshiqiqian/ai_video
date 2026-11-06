const cv = document.getElementById('c');
const g = cv.getContext('2d');
const W = 1920, H = 1080;
const DUR = 48;

const C = {
  page: '#EAE9E5', paper: '#F7F6F2', ink: '#111111', red: '#E30613',
  mute: '#77766F', faint: '#C9C8C3', line: '#D6D5D0',
};
const F = '"Microsoft YaHei", "Noto Sans SC", "PingFang SC", sans-serif';

const NODES = [
  { cn: '立项', en: 'BRIEF' },
  { cn: '文案', en: 'SCRIPT' },
  { cn: '分镜', en: 'STORYBOARD' },
  { cn: '配音', en: 'VOICE' },
  { cn: '混音', en: 'MIX' },
  { cn: '渲染', en: 'RENDER' },
];

const SC = {
  intro: [0.0, 4.8],
  flow: [4.8, 10.2],
  brief: [10.2, 15.0],
  script: [15.0, 19.8],
  story: [19.8, 24.6],
  voice: [24.6, 29.4],
  mix: [29.4, 34.2],
  render: [34.2, 39.0],
  revise: [39.0, 44.0],
  end: [44.0, 48.0],
};

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const easeOut = p => 1 - Math.pow(1 - clamp(p), 3);
const easeInOut = p => { p = clamp(p); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const seg = (t, a, b) => clamp((t - a) / (b - a));
const snap = (t, a, d) => easeOut((t - a) / d);

function txt(s, x, y, size, weight = 500, color = C.ink) {
  g.fillStyle = color;
  g.font = `${weight} ${size}px ${F}`;
  g.fillText(s, x, y);
}

function label(s, x, y, size = 20, color = C.mute, spacing = '4px') {
  g.save();
  g.fillStyle = color;
  g.font = `500 ${size}px ${F}`;
  g.letterSpacing = spacing;
  g.fillText(s, x, y);
  g.restore();
}

function reveal(s, x, y, size, p, color = C.ink, weight = 800) {
  if (p <= 0) return;
  g.save();
  g.font = `${weight} ${size}px ${F}`;
  const w = g.measureText(s).width;
  g.beginPath(); g.rect(x - 4, y - size * 1.06, w + 8, size * 1.34); g.clip();
  g.fillStyle = color;
  g.fillText(s, x, y + (1 - easeOut(p)) * size * 1.2);
  g.restore();
}

function hline(x1, x2, y, p, color = C.ink, width = 3) {
  if (p <= 0) return;
  g.save();
  g.strokeStyle = color; g.lineWidth = width;
  g.beginPath(); g.moveTo(x1, y); g.lineTo(lerp(x1, x2, easeOut(p)), y); g.stroke();
  g.restore();
}

function grid(alpha = 1) {
  g.save();
  g.globalAlpha = alpha;
  g.strokeStyle = C.line; g.lineWidth = 1;
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

/* ---------- flowchart ---------- */
function flowGeom(y, h) {
  const m = 120, gap = 24, w = (1680 - gap * 5) / 6;
  return { x: i => m + i * (w + gap), w, y, h, gap };
}

function drawFlow(t, a, active, compact = false) {
  const y = compact ? 96 : 380;
  const h = compact ? 78 : 150;
  const nameSize = compact ? 24 : 40;
  const enSize = compact ? 11 : 15;
  const Gf = flowGeom(y, h);
  const appear = compact ? 1 : seg(t, a + .1, a + 1.1);
  const conn = compact ? 1 : easeInOut(seg(t, a + .25, a + 1.7));

  // connectors
  g.save();
  g.strokeStyle = compact ? C.faint : C.ink;
  g.lineWidth = compact ? 2 : 3;
  g.globalAlpha = .55;
  for (let i = 0; i < 5; i++) {
    const x1 = Gf.x(i) + Gf.w, x2 = Gf.x(i + 1);
    const q = clamp(conn * 5 - i);
    if (q <= 0) continue;
    g.beginPath(); g.moveTo(x1, y + h / 2); g.lineTo(lerp(x1, x2, q), y + h / 2); g.stroke();
  }
  g.restore();

  // nodes
  for (let i = 0; i < 6; i++) {
    const q = compact ? 1 : easeOut(clamp((appear - i * .08) / .5));
    if (q <= 0) continue;
    const x = Gf.x(i);
    const on = i === active;
    g.save();
    g.globalAlpha = q;
    g.translate(0, (1 - q) * 18);
    g.fillStyle = on ? C.red : (compact ? C.paper : C.paper);
    g.strokeStyle = on ? C.red : C.ink;
    g.lineWidth = compact ? 2 : 3;
    g.fillRect(x, y, Gf.w, h);
    g.strokeRect(x, y, Gf.w, h);

    if (on) {
      g.fillStyle = C.paper;
    } else {
      g.fillStyle = C.mute;
    }
    g.font = `500 ${enSize + 2}px ${F}`;
    g.letterSpacing = '2px';
    g.fillText(String(i + 1).padStart(2, '0'), x + (compact ? 12 : 20), y + (compact ? 20 : 32));

    g.fillStyle = on ? C.paper : C.ink;
    g.font = `800 ${nameSize}px ${F}`;
    g.letterSpacing = '0px';
    g.fillText(NODES[i].cn, x + (compact ? 12 : 20), y + (compact ? 54 : 96));

    g.fillStyle = on ? 'rgba(255,255,255,.72)' : C.mute;
    g.font = `500 ${enSize}px ${F}`;
    g.letterSpacing = '3px';
    g.fillText(NODES[i].en, x + (compact ? 12 : 20), y + (compact ? 70 : 126));
    g.restore();
  }

  // travelling pulse on the overview
  if (!compact) {
    const q = ((t - a) * .42) % 1;
    const total = Gf.x(5) + Gf.w - Gf.x(0);
    const px = Gf.x(0) + total * easeInOut(q);
    g.save();
    g.fillStyle = C.red;
    g.beginPath(); g.arc(px, y + h / 2, 9, 0, Math.PI * 2); g.fill();
    g.restore();
  }
}

/* ---------- detail panels ---------- */
function panelHead(num, cn, en, t, a) {
  reveal(String(num).padStart(2, '0'), 96, 292, 28, snap(t, a + .05, .3), C.red, 800);
  reveal(cn, 96, 392, 72, snap(t, a + .1, .45));
  label(en, 100, 438, 18, C.mute, '6px');
}

function detailBrief(t, a) {
  panelHead(1, '立项', 'STYLE · DURATION · LANGUAGE', t, a);
  const items = [
    ['风格', 'SWISS GRID'],
    ['时长', '48 秒'],
    ['语言', '中文'],
  ];
  items.forEach(([k, v], i) => {
    const q = easeOut(seg(t, a + .45 + i * .18, a + .85 + i * .18));
    const y = 560 + i * 120;
    g.save();
    g.globalAlpha = q;
    g.strokeStyle = C.ink; g.lineWidth = 2;
    g.beginPath(); g.moveTo(96, y); g.lineTo(lerp(96, 1720, q), y); g.stroke();
    g.restore();
    label(k, 96, y + 58, 24, C.mute, '8px');
    reveal(v, 420, y + 72, 56, snap(t, a + .55 + i * .18, .4), C.ink, 800);
  });
}

function detailScript(t, a) {
  panelHead(2, '文案', 'LINES · TIMECODES', t, a);
  const rows = LINES.slice(0, 3).map(l => [
    l.id.toUpperCase(), l.t0.toFixed(2), l.text,
  ]);
  rows.forEach(([id, tm, s], i) => {
    const q = snap(t, a + .35 + i * .2, .4);
    const y = 560 + i * 108;
    label(id, 96, y, 22, C.red, '0px');
    label(tm, 190, y, 22, C.mute, '0px');
    reveal(s, 360, y + 4, 42, q, C.ink, 600);
    g.save(); g.font = `600 42px ${F}`;
    const w = g.measureText(s).width;
    g.restore();
    hline(96, 360 + w, y + 30, snap(t, a + .5 + i * .2, .5), C.faint, 2);
  });
  label('每一句都有自己的时间，字幕不用猜。', 96, 900, 24, C.mute, '2px');
}

function detailStory(t, a) {
  panelHead(3, '分镜', 'SHOTS · DURATIONS', t, a);
  const shots = [SC.brief, SC.script, SC.story, SC.voice].map((s, i) =>
    [`S${i + 1}`, `${(s[1] - s[0]).toFixed(1)}s`]);
  const fw = 380, fh = 214;
  shots.forEach(([id, d], i) => {
    const q = easeOut(seg(t, a + .35 + i * .12, a + .75 + i * .12));
    const x = 96 + i * (fw + 32);
    const y = 540;
    g.save();
    g.globalAlpha = q;
    g.fillStyle = i === 1 ? C.red : C.paper;
    g.strokeStyle = i === 1 ? C.red : C.ink;
    g.lineWidth = 3;
    g.fillRect(x, y, fw, fh);
    g.strokeRect(x, y, fw, fh);
    g.fillStyle = i === 1 ? C.paper : C.ink;
    g.font = `800 54px ${F}`;
    g.fillText(id, x + 24, y + 84);
    g.font = `500 22px ${F}`;
    g.fillStyle = i === 1 ? 'rgba(255,255,255,.8)' : C.mute;
    g.fillText(d, x + 26, y + 120);
    // mini layout lines
    g.strokeStyle = i === 1 ? 'rgba(255,255,255,.5)' : C.faint;
    g.lineWidth = 2;
    for (let k = 0; k < 3; k++) {
      g.beginPath(); g.moveTo(x + 26, y + 150 + k * 18); g.lineTo(x + 26 + (k === 0 ? 180 : 120), y + 150 + k * 18); g.stroke();
    }
    g.restore();
  });
  label('每个镜头都有起点、终点和时长。', 96, 860, 24, C.mute, '2px');
}

function detailVoice(t, a) {
  panelHead(4, '配音', 'PER-LINE WAV · CAPTIONS', t, a);
  const rows = LINES.slice(0, 4).map(l =>
    [l.id, `${(l.t1 - l.t0 - 0.55).toFixed(2)}s`]);
  rows.forEach(([id, d], i) => {
    const q = easeOut(seg(t, a + .3 + i * .13, a + .6 + i * .13));
    const y = 540 + i * 78;
    g.save();
    g.globalAlpha = q;
    g.fillStyle = C.paper; g.strokeStyle = C.ink; g.lineWidth = 2;
    g.fillRect(96, y, 520, 58);
    g.strokeRect(96, y, 520, 58);
    g.fillStyle = C.ink; g.font = `600 26px ${F}`;
    g.fillText(`${id}.wav`, 116, y + 38);
    g.fillStyle = C.red; g.font = `700 24px ${F}`;
    g.fillText(d, 520, y + 38);
    g.restore();
  });

  // waveform
  const baseY = 780;
  const n = 56;
  for (let i = 0; i < n; i++) {
    const amp = (0.25 + 0.75 * Math.abs(Math.sin(i * .55 + t * 3.2))) * (0.6 + 0.4 * Math.sin(i * .17 + 1.2));
    const h = 10 + 120 * amp * easeOut(seg(t, a + .45, a + .9));
    const x = 700 + i * 19;
    g.save();
    g.fillStyle = i % 9 === 0 ? C.red : C.ink;
    g.fillRect(x, baseY - h / 2, 9, h);
    g.restore();
  }
  label('一句一个文件，起点和时长都是明确的数字。', 96, 900, 24, C.mute, '2px');
}

function detailMix(t, a) {
  panelHead(5, '混音', 'VOICE · MUSIC · SFX', t, a);
  const layers = [
    ['旁白', .9, C.ink],
    ['配乐', .55, C.red],
    ['音效', .35, C.mute],
  ];
  layers.forEach(([name, lvl, color], i) => {
    const y = 560 + i * 90;
    const q = easeOut(seg(t, a + .35 + i * .12, a + .75 + i * .12));
    label(name, 96, y + 8, 22, C.mute, '2px');
    g.save();
    g.fillStyle = C.paper;
    g.fillRect(210, y - 20, 1180 * q, 44);
    g.fillStyle = color;
    g.fillRect(210, y - 20, 1180 * q * lvl, 44);
    g.restore();
    g.save();
    g.fillStyle = C.ink; g.font = `600 20px ${F}`;
    g.fillText(`${Math.round(lvl * 100)}%`, 1410, y + 8);
    g.restore();
  });

  // meter
  const q = easeOut(seg(t, a + .9, a + 1.5));
  g.save();
  g.strokeStyle = C.ink; g.lineWidth = 2;
  g.strokeRect(96, 830, 520, 64);
  g.fillStyle = C.red;
  g.fillRect(100, 834, 512 * q * .94, 56);
  g.fillStyle = C.ink; g.font = `600 22px ${F}`;
  g.fillText('−14 LUFS', 96, 936);
  g.restore();
  label('同一条时间轴，画面停在哪儿，声音就在哪儿。', 700, 936, 24, C.mute, '2px');
}

function detailRender(t, a) {
  panelHead(6, '渲染', 'FRAMES · DETERMINISTIC', t, a);
  const p = easeInOut(seg(t, a + .3, a + 2.2));
  const n = Math.round(lerp(0, 1152, p));
  g.save();
  g.fillStyle = C.red;
  g.font = `800 240px ${F}`;
  g.letterSpacing = '-8px';
  g.fillText(String(n).padStart(4, '0'), 96, 760);
  g.restore();
  label('帧', 700, 720, 28, C.mute, '4px');

  // progress
  g.save();
  g.fillStyle = C.paper;
  g.fillRect(96, 810, 1180, 26);
  g.fillStyle = C.ink;
  g.fillRect(96, 810, 1180 * p, 26);
  g.restore();

  // frame strip
  for (let i = 0; i < 26; i++) {
    const on = i / 26 < p;
    const x = 1340 + (i % 13) * 42;
    const y = 470 + Math.floor(i / 13) * 56;
    g.save();
    g.fillStyle = on ? C.ink : C.paper;
    g.strokeStyle = C.faint; g.lineWidth = 1;
    g.fillRect(x, y, 34, 42);
    g.strokeRect(x, y, 34, 42);
    g.restore();
  }
  label('每一帧都是算出来的，不依赖上一帧。', 96, 900, 24, C.mute, '2px');
}

function sceneRevise(t, a) {
  drawFlow(t, a, -1, false);
  reveal('改一行', 96, 720, 82, snap(t, a + .25, .45));
  reveal('重出一版', 96, 830, 82, snap(t, a + .55, .45), C.red);

  // feedback loop: render -> brief
  const Gf = flowGeom(380, 150);
  const x6 = Gf.x(5) + Gf.w / 2, x1 = Gf.x(0) + Gf.w / 2;
  const y0 = 380 + 150, yb = y0 + 74;
  const q = easeInOut(seg(t, a + .3, a + 1.5));
  g.save();
  g.strokeStyle = C.red; g.lineWidth = 3;
  g.beginPath(); g.moveTo(x6, y0); g.lineTo(x6, yb); g.stroke();
  g.beginPath(); g.moveTo(x6, yb); g.lineTo(lerp(x6, x1, q), yb); g.stroke();
  if (q >= .999) {
    g.beginPath(); g.moveTo(x1, yb); g.lineTo(x1, y0 + 20); g.stroke();
    g.beginPath();
    g.moveTo(x1, y0 + 20); g.lineTo(x1 - 12, y0 + 42); g.moveTo(x1, y0 + 20); g.lineTo(x1 + 12, y0 + 42);
    g.stroke();
  } else {
    g.beginPath();
    g.moveTo(lerp(x6, x1, q), yb); g.lineTo(lerp(x6, x1, q) - 22, yb - 10);
    g.moveTo(lerp(x6, x1, q), yb); g.lineTo(lerp(x6, x1, q) - 22, yb + 10);
    g.stroke();
  }
  g.restore();
  label('STALE', x6 - 90, yb - 16, 18, C.red, '4px');
  label('上游改了，下游自动标记过期，不用凭记忆重跑。', 96, 940, 24, C.mute, '2px');
}

function sceneEnd(t, a) {
  grid(clamp(1 - seg(t, a, a + .8)) * .7);
  const big = '六步，一条片子。';
  g.save();
  g.font = `800 128px ${F}`;
  const w = g.measureText(big).width;
  reveal(big, (W - w) / 2, 470, 128, snap(t, a + .2, .6));
  g.restore();

  hline((W - 260) / 2, (W + 260) / 2, 530, snap(t, a + .5, .6), C.red, 6);

  const sub = '本地 · 确定 · 可回退';
  g.save();
  g.font = `500 34px ${F}`;
  const sw = g.measureText(sub).width;
  g.globalAlpha = easeOut(seg(t, a + .9, a + 1.4));
  g.fillStyle = C.mute;
  g.fillText(sub, (W - sw) / 2, 620);
  g.restore();

  const q = easeOut(seg(t, a + 1.5, a + 1.75));
  if (q > 0) {
    g.save();
    g.globalAlpha = q;
    g.translate(1480, 850);
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
let LINES = [];
function subtitle(t) {
  const L = LINES.find(l => t >= l.t0 && t <= l.t1);
  if (!L) return;
  g.save();
  g.globalAlpha = clamp(seg(t, L.t0, L.t0 + .2) * seg(t, L.t1 + .01, L.t1 - .15));
  g.fillStyle = C.red;
  g.fillRect(96, 1002, 14, 14);
  g.fillStyle = C.ink;
  g.font = `500 38px ${F}`;
  g.fillText(L.text, 128, 1022);
  g.restore();
}

/* ---------- master ---------- */
window.render = t => {
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalAlpha = 1;
  g.fillStyle = C.page;
  g.fillRect(0, 0, W, H);

  // meta
  label('AI-v / SIX STAGES', 96, 52, 18, C.mute, '5px');
  g.save();
  g.fillStyle = C.mute; g.font = `500 18px ${F}`; g.textAlign = 'right';
  g.fillText(`T ${t.toFixed(2)}`, 1824, 52);
  g.restore();

  const [ia, ib] = SC.intro;
  if (t < ib) {
    grid(clamp(1 - seg(t, ia, ia + 3.4)) * .9);
    reveal('一条视频', 96, 430, 132, snap(t, ia + .2, .55));
    reveal('六步', 96, 570, 132, snap(t, ia + .45, .55), C.red);
    label('FROM ONE SENTENCE TO A FINISHED FILM', 100, 640, 20, C.mute, '5px');
    const q = easeOut(seg(t, ia + .9, ia + 1.6));
    g.save(); g.fillStyle = C.ink; g.fillRect(96, 700, 440 * q, 12); g.restore();
  } else if (t < SC.flow[1]) {
    const [a, b] = SC.flow;
    drawFlow(t, a, -1, false);
    label('每一步都有产物，也都能单独重跑。', 96, 700, 26, C.mute, '2px');
  } else if (t < SC.brief[1]) {
    drawFlow(t, SC.brief[0], 0, true);
    detailBrief(t, SC.brief[0]);
  } else if (t < SC.script[1]) {
    drawFlow(t, SC.script[0], 1, true);
    detailScript(t, SC.script[0]);
  } else if (t < SC.story[1]) {
    drawFlow(t, SC.story[0], 2, true);
    detailStory(t, SC.story[0]);
  } else if (t < SC.voice[1]) {
    drawFlow(t, SC.voice[0], 3, true);
    detailVoice(t, SC.voice[0]);
  } else if (t < SC.mix[1]) {
    drawFlow(t, SC.mix[0], 4, true);
    detailMix(t, SC.mix[0]);
  } else if (t < SC.render[1]) {
    drawFlow(t, SC.render[0], 5, true);
    detailRender(t, SC.render[0]);
  } else if (t < SC.revise[1]) {
    sceneRevise(t, SC.revise[0]);
  } else {
    sceneEnd(t, SC.end[0]);
  }

  subtitle(t);
};

window.TEXTS = t => {
  const L = LINES.find(l => t >= l.t0 && t <= l.t1);
  return L ? [{ id: L.id, text: L.text, x0: 96, y0: 990, x1: 1824, y1: 1040 }] : [];
};

window.DUR = DUR;
window.EV = [
  { t: 4.8, type: 'cut' }, { t: 10.2, type: 'cut' }, { t: 15.0, type: 'cut' },
  { t: 19.8, type: 'cut' }, { t: 24.6, type: 'cut' }, { t: 29.4, type: 'cut' },
  { t: 34.2, type: 'cut' }, { t: 39.0, type: 'cut' }, { t: 44.0, type: 'cut' },
];

try {
  LINES = await (await fetch('./lines.json')).json();
} catch (e) {
  LINES = [];
}
window.READY = true;
