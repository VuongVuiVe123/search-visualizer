"use strict";

/* View của bài robot hút bụi nhiều phòng: CHỈ VẼ ngôi nhà isometric, robot trụ,
   thẻ trạng thái [phòng robot đứng, các phòng], hộp thoại tự đặt.
   Trạng thái đầu, đích, bài mẫu và luật chơi khai báo ở problems/vacuum.py (Python),
   tệp này đọc chúng qua View.problem (nạp lúc khởi động trong engine.js). */

const DIRTY = [150, 108, 66], CLEAN = [80, 184, 116];
const ROOM_TYPES = ["living", "kitchen", "bedroom", "bath", "study", "hall"];
const letter = i => String.fromCharCode(65 + i);
const roomIndex = state => state[0].charCodeAt(0) - 65;   // "A" -> 0, "B" -> 1, ... (để vẽ)
const makeState = (pos, dirt) => [letter(pos), ...dirt.map(d => (d ? "D" : "C"))];
const makeGoal = (n, pos) => [letter(pos), ...Array(n).fill("C")];
const SCENE = { x: 524, y: 92, w: 864, h: 340 };
const INFO = { x: 1100, y: 100, w: 280, h: 324 };
const MOD = { x: 320, y: 210, w: 760, h: 520 };

/* ---------------- Phép chiếu isometric và các khối vẽ ---------------- */
const ISO = { TW: 100, TH: 50, OX: 0, OY: 0, ZK: 1 };
const P = (r, c, z = 0) => [ISO.OX + (c - r) * ISO.TW / 2, ISO.OY + (c + r) * ISO.TH / 2 - z * ISO.ZK];
function path(pts) { ctx.beginPath(); pts.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.closePath(); }
function polyPts(pts, fill, stroke, lw = 1) {
  path(pts);
  if (fill) { ctx.fillStyle = css(fill); ctx.fill(); }
  if (stroke) { ctx.strokeStyle = css(stroke); ctx.lineWidth = lw; ctx.stroke(); }
}
function poly(pts3, fill, stroke, lw = 1) { polyPts(pts3.map(p => P(...p)), fill, stroke, lw); }
function box(r0, c0, r1, c1, z0, z1, col, edge = true) {
  const ec = edge ? shade(col, 0.45) : null;
  poly([[r1, c0, z0], [r1, c1, z0], [r1, c1, z1], [r1, c0, z1]], shade(col, 0.78), ec);
  poly([[r0, c1, z0], [r1, c1, z0], [r1, c1, z1], [r0, c1, z1]], shade(col, 0.58), ec);
  poly([[r0, c0, z1], [r0, c1, z1], [r1, c1, z1], [r1, c0, z1]], col, ec);
}
function flat(r0, c0, r1, c1, z, col, edge) { poly([[r0, c0, z], [r0, c1, z], [r1, c1, z], [r1, c0, z]], col, edge); }
function ring(r, c, rad, z, n = 32) { const a = []; for (let k = 0; k < n; k++) a.push(P(r + rad * Math.cos(2 * Math.PI * k / n), c + rad * Math.sin(2 * Math.PI * k / n), z)); return a; }
function cylinder(r, c, rad, z0, z1, col, n = 28) {
  const bot = ring(r, c, rad, z0, n), top = ring(r, c, rad, z1, n);
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n, a = 2 * Math.PI * (i + 0.5) / n;
    if (Math.cos(a) + Math.sin(a) > -0.3) {
      const k = 0.55 + 0.45 * Math.max(0, 0.6 * Math.cos(a) - 0.4 * Math.sin(a) + 0.4);
      polyPts([bot[i], bot[j], top[j], top[i]], shade(col, k));
    }
  }
  polyPts(top, col, shade(col, 0.5), 1);
}
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

function drawRobot(rc, cc, th, spin, rad, led) {
  const zk = ISO.ZK, h = 16, ct = Math.cos(th), st = Math.sin(th), n = 40;
  const loc = (u, v, z = 0) => P(rc + u * ct - v * st, cc + u * st + v * ct, z);
  ctx.globalAlpha = 0.31; polyPts(ring(rc + 0.05, cc + 0.05, rad * 1.1, 0, 32), [0, 0, 0]); ctx.globalAlpha = 1;
  const bu = rad * 0.62, bv = rad * 0.58, [hx, hy] = loc(bu, bv, 2);
  for (let k = 0; k < 3; k++) {
    const a = spin * Math.PI / 180 + k * 2 * Math.PI / 3;
    const e = P(rc + bu * ct - bv * st + 0.2 * Math.cos(a), cc + bu * st + bv * ct + 0.2 * Math.sin(a), 2);
    line(hx, hy, e[0], e[1], "rgb(214,214,220)", 3 * zk + 1);
  }
  cylinder(rc, cc, rad, 0, h, [40, 40, 46], n);
  polyPts(ring(rc, cc, rad, h, n), [32, 32, 36], [86, 86, 96], 3 * zk + 1);
  polyPts(ring(rc, cc, rad * 0.88, h, n), [22, 22, 26]);
  const gl = []; for (let k = 0; k < 22; k++) { const a = 3.3 + k * 0.05; gl.push(P(rc + rad * 0.72 * Math.cos(a), cc + rad * 0.72 * Math.sin(a), h)); }
  ctx.beginPath(); gl.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.strokeStyle = "rgb(96,96,108)"; ctx.lineWidth = 3 * zk + 1; ctx.stroke();
  for (const v of [-0.12, 0.12]) {
    const [x, y] = loc(rad * 0.62, v * rad * 1.6, h);
    ctx.beginPath(); ctx.ellipse(x, y, 6 * zk, 3.5 * zk, 0, 0, 7); ctx.fillStyle = "rgb(70,70,78)"; ctx.fill();
  }
  const tr = rad * 0.4, tb = ring(rc, cc, tr, h, n), tt = ring(rc, cc, tr, h + 10, n);
  for (let k = 0; k < n; k++) {
    const j = (k + 1) % n, a = 2 * Math.PI * (k + 0.5) / n;
    if (Math.cos(a) + Math.sin(a) > -0.3) polyPts([tb[k], tb[j], tt[j], tt[k]], [14, 14, 18]);
  }
  polyPts(tt, [36, 36, 42], [92, 92, 102], 2);
  const z = rad * 0.13, zp = [loc(-z, -z, h + 10), loc(-z, z, h + 10), loc(z, -z, h + 10), loc(z, z, h + 10)];
  ctx.beginPath(); zp.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.strokeStyle = "rgb(176,176,184)"; ctx.lineWidth = 2; ctx.stroke();
  if (led) { const [x, y] = loc(rad * 0.3, 0, h + 10); circle(x, y, 4 * zk + 1, "rgb(90,230,150)"); }
}

/* ---------------- Cảnh ngôi nhà ---------------- */
class Scene {
  constructor() { this.cfg(2); }
  cfg(n) {
    this.n = n; this.rows = n <= 3 ? 1 : 2; this.cols = n <= 3 ? n : Math.ceil(n / 2); this.RS = 2;
    const tot = (this.rows + this.cols) * this.RS;
    const tw_ = Math.max(44, Math.min(150, 1100 / tot, (SCENE.h - 44) / (0.62 + tot / 4)));
    ISO.TW = tw_; ISO.TH = tw_ / 2; ISO.ZK = tw_ / 150; this.wallH = 100;
    const totalH = this.wallH * ISO.ZK + tot * ISO.TH / 2 + 18;
    ISO.OX = SCENE.x + 282 - (this.cols - this.rows) * this.RS * tw_ / 4;
    ISO.OY = SCENE.y + 26 + (SCENE.h - 26 - totalH) / 2 + this.wallH * ISO.ZK + 4;
    this.objs = null; this.bg = null; this.bgKey = "";
  }
  cellOf(i) { return this.rows === 1 ? [0, i] : i < this.cols ? [0, i] : [1, 2 * this.cols - 1 - i]; }
  indexOf(gr, gc) { for (let i = 0; i < this.n; i++) { const c = this.cellOf(i); if (c[0] === gr && c[1] === gc) return i; } return null; }
  roomType(gr, gc) { const i = this.indexOf(gr, gc); return i === null ? "storage" : ROOM_TYPES[i % ROOM_TYPES.length]; }
  origin(gr, gc) { return [gr * this.RS, gc * this.RS]; }
  center(i) { const [gr, gc] = this.cellOf(i); return [gr * this.RS + this.RS / 2, gc * this.RS + this.RS / 2]; }
  posAt(f) {
    f = Math.max(0, Math.min(this.n - 1, f));
    const i = Math.min(Math.floor(f), this.n - 2), t = f - i, a = this.center(i), b = this.center(Math.min(i + 1, this.n - 1));
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  }

  floor(gr, gc, rnd) {
    const [r0, c0] = this.origin(gr, gc), t = this.roomType(gr, gc), RS = this.RS;
    const pts = [[r0, c0, 0], [r0, c0 + RS, 0], [r0 + RS, c0 + RS, 0], [r0 + RS, c0, 0]];
    if (t === "living" || t === "study" || t === "hall") {
      const base = { living: [190, 140, 90], study: [204, 164, 114], hall: [150, 108, 72] }[t], dark = css(shade(base, 0.82));
      poly(pts, base);
      for (let k = 1; k < 8; k++) {
        const f = k / 4, off = 0.5 + 0.7 * ((k + gr + gc) % 2);
        let a = P(r0 + f, c0), b = P(r0 + f, c0 + RS); line(a[0], a[1], b[0], b[1], dark, 1);
        a = P(r0 + f, c0 + off); b = P(r0 + f - 0.25, c0 + off); line(a[0], a[1], b[0], b[1], dark, 1);
      }
    } else if (t === "kitchen") {
      for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
        poly([[r0 + i / 2, c0 + j / 2, 0], [r0 + i / 2, c0 + j / 2 + .5, 0], [r0 + i / 2 + .5, c0 + j / 2 + .5, 0], [r0 + i / 2 + .5, c0 + j / 2, 0]], (i + j) % 2 === 0 ? [236, 230, 218] : [186, 186, 182]);
      }
    } else if (t === "bedroom") {
      poly(pts, [152, 174, 198]);
      for (let k = 0; k < 60; k++) { const q = P(r0 + rnd() * RS, c0 + rnd() * RS); circle(q[0], q[1], 2, rnd() < 0.5 ? "rgb(138,160,186)" : "rgb(166,186,208)"); }
    } else if (t === "bath") {
      poly(pts, [158, 212, 222]);
      for (let k = 1; k < 6; k++) {
        let a = P(r0 + k / 3, c0), b = P(r0 + k / 3, c0 + RS); line(a[0], a[1], b[0], b[1], "rgb(112,170,184)", 1);
        a = P(r0, c0 + k / 3); b = P(r0 + RS, c0 + k / 3); line(a[0], a[1], b[0], b[1], "rgb(112,170,184)", 1);
      }
    } else {
      poly(pts, [150, 150, 152]);
      for (let k = 1; k < 4; k++) { const a = P(r0 + k / 2, c0), b = P(r0 + k / 2, c0 + RS); line(a[0], a[1], b[0], b[1], "rgb(126,126,130)", 1); }
    }
    poly(pts, null, [0, 0, 0], 1);
  }

  ensureBg() {
    const pw = Math.round(SCENE.w * scale * dpr), ph = Math.round(SCENE.h * scale * dpr), key = `${pw}x${ph}|${this.n}`;
    if (this.bg && this.bgKey === key) return;
    const c = document.createElement("canvas"); c.width = pw; c.height = ph;
    const saved = ctx; ctx = c.getContext("2d");
    ctx.setTransform(dpr * scale, 0, 0, dpr * scale, -SCENE.x * dpr * scale, -SCENE.y * dpr * scale);
    this.paintBg();
    ctx = saved; this.bg = c; this.bgKey = key;
  }
  paintBg() {
    const rnd = rng(5), R = this.rows, C = this.cols, RS = this.RS;
    fillRR(SCENE.x, SCENE.y, SCENE.w, SCENE.h, 14, "rgb(68,128,62)");
    ctx.save(); rr(SCENE.x, SCENE.y, SCENE.w, SCENE.h, 14); ctx.clip();
    for (let x = SCENE.x; x < SCENE.x + SCENE.w; x += 56) if (((x - SCENE.x) / 56 | 0) % 2 === 0) { ctx.fillStyle = "rgb(74,138,66)"; ctx.fillRect(x, SCENE.y, 56, SCENE.h); }
    const greens = ["rgb(52,104,50)", "rgb(88,156,76)", "rgb(60,118,56)"];
    for (let k = 0; k < 900; k++) {
      const x = SCENE.x + rnd() * SCENE.w, y = SCENE.y + rnd() * SCENE.h;
      line(x, y, x + (rnd() * 4 - 2) | 0, y - 3 - rnd() * 4, greens[(rnd() * 3) | 0], 1);
    }
    polyPts([P(-0.6, -0.6), P(-0.6, C * RS + 0.6), P(R * RS + 0.6, C * RS + 0.6), P(R * RS + 0.6, -0.6)], [126, 100, 70], [92, 70, 48], 2);
    const SL = 14;
    poly([[R * RS, 0, 0], [R * RS, C * RS, 0], [R * RS, C * RS, -SL], [R * RS, 0, -SL]], [176, 170, 158], [90, 84, 74]);
    poly([[0, C * RS, 0], [R * RS, C * RS, 0], [R * RS, C * RS, -SL], [0, C * RS, -SL]], [136, 130, 120], [90, 84, 74]);
    for (let gr = 0; gr < R; gr++) for (let gc = 0; gc < C; gc++) this.floor(gr, gc, rnd);
    for (const [tx, ty, sc] of [[SCENE.x + 44, SCENE.y + 215, 0.8], [SCENE.x + 540, SCENE.y + 250, 0.7], [SCENE.x + 70, SCENE.y + 120, 0.6]]) {
      ctx.beginPath(); ctx.ellipse(tx, ty + 2, 24 * sc, 7 * sc, 0, 0, 7); ctx.fillStyle = "rgb(30,80,30)"; ctx.fill();
      ctx.fillStyle = "rgb(96,66,42)"; ctx.fillRect(tx - 5 * sc, ty - 44 * sc, 10 * sc, 48 * sc);
      for (const [dx, dy, rad] of [[0, -80, 28], [-18, -62, 22], [18, -62, 22], [0, -58, 24], [-9, -92, 18]]) circle(tx + dx * sc, ty + dy * sc, rad * sc, rnd() < 0.5 ? "rgb(40,108,52)" : "rgb(48,120,58)");
    }
    ctx.restore();
  }

  buildObjs() {
    const zk = ISO.ZK, objs = [], R = this.rows, C = this.cols, RS = this.RS, wallC = [238, 230, 214], wh = this.wallH;
    objs.push([-9, () => {
      box(-0.14, -0.14, R * RS, 0, 0, wh, wallC);
      box(-0.14, -0.14, 0, C * RS, 0, wh, wallC);
      for (let gc = 0; gc < C; gc++) { const a = gc * RS + 0.5, b = gc * RS + RS - 0.5; poly([[0, a, 44], [0, b, 44], [0, b, 84], [0, a, 84]], [170, 215, 240], [255, 255, 255], 2); }
      for (let gr = 0; gr < R; gr++) { const a = gr * RS + 0.5, b = gr * RS + RS - 0.5; poly([[a, 0, 44], [b, 0, 44], [b, 0, 84], [a, 0, 84]], [170, 215, 240], [255, 255, 255], 2); }
    }]);
    const T0 = 0.04, door = 0.9, g = (RS - door) / 2, ph = 52;
    for (let gr = 0; gr < R; gr++) for (let gc = 0; gc < C; gc++) {
      const a = this.indexOf(gr, gc), [r0, c0] = this.origin(gr, gc);
      if (gc + 1 < C) {
        const b = this.indexOf(gr, gc + 1), has = a !== null && b !== null && Math.abs(a - b) === 1, x = c0 + RS;
        for (const [u, v] of has ? [[r0, r0 + g], [r0 + RS - g, r0 + RS]] : [[r0, r0 + RS]]) objs.push([(u + v) / 2 + x, () => box(u, x - T0, v, x + T0, 0, ph, wallC)]);
      }
      if (gr + 1 < R) {
        const b = this.indexOf(gr + 1, gc), has = a !== null && b !== null && Math.abs(a - b) === 1, y = r0 + RS;
        for (const [u, v] of has ? [[c0, c0 + g], [c0 + RS - g, c0 + RS]] : [[c0, c0 + RS]]) objs.push([(u + v) / 2 + y, () => box(y - T0, u, y + T0, v, 0, ph, wallC)]);
      }
    }
    for (let gr = 0; gr < R; gr++) for (let gc = 0; gc < C; gc++) {
      const t = this.roomType(gr, gc), [r0, c0] = this.origin(gr, gc);
      const sr = (u0, u1) => gr === 0 ? [r0 + 0.05 + u0, r0 + 0.05 + u1] : [r0 + RS - 0.05 - u1, r0 + RS - 0.05 - u0];
      const dep = (u0, u1, v0, v1) => { const [ra, rb] = sr(u0, u1); return (ra + rb) / 2 + c0 + (v0 + v1) / 2; };
      if (t === "living") objs.push([dep(0, 0.46, 0.2, 1.5), () => {
        flat(r0 + 0.7, c0 + 0.5, r0 + 1.3, c0 + 1.5, 0.5, [160, 62, 62], [240, 214, 170]);
        let [ra, rb] = sr(0, 0.18); box(ra, c0 + 0.2, rb, c0 + 1.5, 0, 44, [138, 78, 62]);
        [ra, rb] = sr(0.18, 0.46); box(ra, c0 + 0.2, rb, c0 + 1.5, 0, 24, [150, 88, 70]);
      }]);
      else if (t === "kitchen") objs.push([dep(0, 0.38, 0.15, 1.85), () => {
        let [ra, rb] = sr(0, 0.38); box(ra, c0 + 0.15, rb, c0 + 1.85, 0, 36, [196, 196, 202]);
        [ra, rb] = sr(0.06, 0.32); flat(ra, c0 + 0.25, rb, c0 + 0.8, 36, [140, 170, 190], [96, 120, 136]);
        for (const [u, v] of [[0.1, 1.2], [0.1, 1.5], [0.26, 1.2], [0.26, 1.5]]) {
          const [x, y] = P(sr(u, u)[0], c0 + v, 36); ctx.beginPath(); ctx.ellipse(x, y, 8 * zk + 1, 4 * zk + 1, 0, 0, 7); ctx.fillStyle = "rgb(40,40,44)"; ctx.fill();
        }
      }]);
      else if (t === "bedroom") objs.push([dep(0, 0.5, 0.15, 1.55), () => {
        let [ra, rb] = sr(0, 0.5); box(ra, c0 + 0.15, rb, c0 + 1.55, 0, 14, [150, 110, 80]);
        [ra, rb] = sr(0.03, 0.47);
        box(ra, c0 + 0.19, rb, c0 + 1.51, 14, 26, [238, 238, 244]);
        box(ra, c0 + 0.23, rb, c0 + 0.5, 26, 33, [252, 252, 254]);
        flat(ra, c0 + 0.7, rb, c0 + 1.5, 26.5, [84, 118, 170], [58, 86, 130]);
      }]);
      else if (t === "bath") objs.push([dep(0, 0.46, 0.15, 1.85), () => {
        let [ra, rb] = sr(0, 0.46); box(ra, c0 + 0.15, rb, c0 + 1.45, 0, 24, [248, 248, 250]);
        [ra, rb] = sr(0.07, 0.39); flat(ra, c0 + 0.25, rb, c0 + 1.35, 24, [120, 190, 226], [170, 176, 184]);
        [ra, rb] = sr(0, 0.3); box(ra, c0 + 1.55, rb, c0 + 1.85, 0, 30, [246, 246, 248]);
      }]);
      else if (t === "study") objs.push([dep(0, 0.42, 0.3, 1.7), () => {
        let [ra, rb] = sr(0, 0.42); box(ra, c0 + 0.3, rb, c0 + 1.7, 0, 32, [126, 86, 54]);
        [ra, rb] = sr(0.08, 0.3); box(ra, c0 + 0.85, rb, c0 + 1.25, 32, 35, [150, 152, 160]);
        [ra, rb] = sr(0.04, 0.08); box(ra, c0 + 0.85, rb, c0 + 1.25, 35, 56, [60, 64, 74]);
      }]);
      else if (t === "hall") objs.push([dep(0.1, 0.4, 0.3, 0.3), () => {
        flat(r0 + 0.8, c0 + 0.3, r0 + 1.2, c0 + 1.7, 0.5, [86, 120, 100], [214, 196, 150]);
        const pr = sr(0.25, 0.25)[0];
        cylinder(pr, c0 + 0.3, 0.13, 0, 18, [160, 100, 60]);
        for (const [dr, dc, h] of [[0, 0, 40], [-.07, .05, 30], [.07, -.05, 32]]) { const [x, y] = P(pr + dr, c0 + 0.3 + dc, h); circle(x, y, 12 * zk + 2, "rgb(46,128,60)"); }
      }]);
      else objs.push([dep(0, 0.45, 0.2, 1.5), () => {
        const [ra, rb] = sr(0, 0.45);
        box(ra, c0 + 0.2, rb, c0 + 0.8, 0, 30, [170, 130, 80]); box(ra, c0 + 1.0, rb, c0 + 1.5, 0, 22, [150, 110, 70]);
      }]);
    }
    objs.sort((a, b) => a[0] - b[0]);
    this.objs = objs;
  }
}

/* Thẻ lớn trong khung thông tin: ô phòng sạch/bẩn và chấm robot trượt mượt. */
class BigCard {
  constructor(rect) { this.rect = rect; this.n = 0; this.rx = null; this.dirt = []; this.alpha = 1; }
  layout(n) { const sq = Math.min(40, (this.rect.w - 20 - (n - 1) * 6) / n), total = n * sq + (n - 1) * 6; return [sq, this.rect.x + (this.rect.w - total) / 2]; }
  update(state, dt, on) {
    if (!state) return;
    const n = state.length - 1;
    if (n !== this.n) { this.n = n; this.rx = null; this.dirt = state.slice(1).map(v => v === "D" ? 1 : 0); }
    const [sq, x0] = this.layout(n), tx = x0 + roomIndex(state) * (sq + 6) + sq / 2;
    this.rx = this.rx === null ? tx : sm(this.rx, tx, 12, dt);
    for (let i = 0; i < n; i++) this.dirt[i] = sm(this.dirt[i], state[1 + i] === "D" ? 1 : 0, 12, dt);
    this.alpha = sm(this.alpha, on ? 1 : 0.22, 9, dt);
  }
  draw(label, border, state) {
    const r = this.rect, a = this.alpha, fd = c => css(mixc(COL.panel, c, a));
    fillRR(r.x, r.y, r.w, r.h, 12, fd([24, 30, 48])); strokeRR(r.x, r.y, r.w, r.h, 12, fd(border), 2);
    T(label, r.x + 10, r.y + 4, { s: 12, b: 1, c: mixc(COL.panel, border, a) });
    if (!state || !this.dirt.length) return;
    const n = state.length - 1, [sq, x0] = this.layout(n), top = r.y + 20;
    for (let i = 0; i < n; i++) {
      const x = x0 + i * (sq + 6), d = this.dirt[i];
      fillRR(x, top, sq, 30, 7, fd(mixc(CLEAN, DIRTY, d)));
      if (d > 0.5) for (const [dx, dy] of [[0.28, 0.35], [0.6, 0.55], [0.42, 0.72]]) circle(x + sq * dx, top + 30 * dy, 2.6, fd([60, 44, 30]));
      else { ctx.beginPath(); ctx.moveTo(x + sq * 0.3, top + 15); ctx.lineTo(x + sq * 0.45, top + 22); ctx.lineTo(x + sq * 0.72, top + 8); ctx.strokeStyle = fd([230, 255, 236]); ctx.lineWidth = 2.5; ctx.stroke(); }
      T(letter(i), x + sq / 2, top + 33, { s: 12, b: 1, c: mixc(COL.panel, COL.muted, a), a: "center" });
    }
    circle(this.rx, top + 15, 11, fd([18, 18, 22]));
    ctx.beginPath(); ctx.arc(this.rx, top + 15, 11, 0, 7); ctx.strokeStyle = fd([96, 96, 108]); ctx.lineWidth = 2; ctx.stroke();
    circle(this.rx, top + 15, 3.5, fd(COL.orange));
  }
}

function drawMiniState(g, pw, ph, state) {
  const rad = (x, y, w, h, r) => { g.beginPath(); g.roundRect ? g.roundRect(x, y, w, h, r) : g.rect(x, y, w, h); };
  g.fillStyle = "rgb(26,33,52)"; rad(0, 0, pw, ph, Math.max(4, ph / 6)); g.fill();
  const n = state.length - 1, pad = Math.max(3, pw / 20), gap = Math.max(1, pw / 60), sw = (pw - 2 * pad - (n - 1) * gap) / n, sh = ph * 0.46, top = ph * 0.12;
  for (let i = 0; i < n; i++) {
    const x = pad + i * (sw + gap), dirty = state[1 + i] === "D";
    g.fillStyle = css(dirty ? DIRTY : CLEAN); rad(x, top, sw, sh, Math.max(2, ph / 12)); g.fill();
    if (dirty) { g.fillStyle = "rgb(60,44,30)"; for (const [dx, dy] of [[0.3, 0.35], [0.65, 0.5], [0.42, 0.75]]) { g.beginPath(); g.arc(x + sw * dx, top + sh * dy, Math.max(1, sh * 0.09), 0, 7); g.fill(); } }
    else { g.beginPath(); g.moveTo(x + sw * 0.28, top + sh * 0.5); g.lineTo(x + sw * 0.45, top + sh * 0.72); g.lineTo(x + sw * 0.74, top + sh * 0.28); g.strokeStyle = "rgb(230,255,236)"; g.lineWidth = Math.max(1, ph / 20); g.stroke(); }
  }
  const cx = pad + roomIndex(state) * (sw + gap) + sw / 2, cy = top + sh / 2, r = Math.min(sw, sh) * 0.38;
  g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fillStyle = "rgb(18,18,22)"; g.fill(); g.strokeStyle = "rgb(96,96,108)"; g.lineWidth = Math.max(1, ph / 24); g.stroke();
  g.beginPath(); g.arc(cx, cy, Math.max(1, r * 0.32), 0, 7); g.fillStyle = css(COL.orange); g.fill();
  g.fillStyle = "rgb(190,200,222)"; g.textAlign = "center"; g.textBaseline = "bottom"; g.font = `bold ${Math.max(8, ph * 0.25)}px ${MONO}`;
  g.fillText(state[0] + " " + state.slice(1).join(""), pw / 2, ph - Math.max(1, ph / 14));
}

const View = {
  id: "vacuum", pythonBase: "../../", problem: null,
  layout: {
    W: 1400, H: 940, lh: 21,
    code: { x: 12, y: 92, w: 500, h: 580 }, tab: { x: 524, y: 444, w: 864, h: 228 },
    qy: 684, ey: 792, barY: 872, btnY: 886, presetX: 688,
    qx: 150, qp: 86, qmax: 10, qcard: { w: 76, h: 50 }, ecard: { w: 70, h: 46 }, estep: 76, emax: 10,
    cell: { w: 76, h: 50, gap: 8 },
  },
  tableTitle: "bảng NODE theo độ sâu  (mỗi thẻ = một trạng thái [vị trí robot, các phòng])",
  scene: new Scene(), nodeCard: new BigCard({ x: INFO.x + 12, y: INFO.y + 28, w: INFO.w - 24, h: 64 }),
  childCard: new BigCard({ x: INFO.x + 12, y: INFO.y + 130, w: INFO.w - 24, h: 64 }),
  replay: null, n: 2, lastChild: null,

  presets() { return this.problem.presets; },
  randomPuzzle(E) { return PY.random("vacuum", E.algo); },
  subtitle() { return `Robot hút bụi · ${this.n} phòng`; },
  anchors() { const a = this.childCard.rect, b = this.nodeCard.rect; return { child: [a.x + a.w / 2, a.y + a.h / 2], node: [b.x + b.w / 2, b.y + b.h / 2] }; },
  drawCard(state, cx, cy, w, h, sc, al) { return drawCached("vc:" + sk(state), w, h, (g, pw, ph) => drawMiniState(g, pw, ph, state), cx, cy, sc, al); },
  drawGoal(xr, E) {
    T("Đích", xr, 30, { s: 14, b: 1, c: COL.green, a: "right", v: "middle" });
    T(`robot ở ${E.goal[0]}, sạch hết`, xr, 50, { s: 13, c: COL.text, a: "right", v: "middle" });
  },
  extraButtons() { return [{ w: 140, label: this.replay ? "Dừng robot" : "Chạy lời giải", key: "replay", active: !!this.replay }]; },
  keys: { v: "replay" },
  press(key, E) { if (key === "replay") this.startReplay(E); },

  onLoad(E) {
    const n = E.rec.init.length - 1, L = this.layout;
    this.n = n; this.replay = null;
    if (this.scene.n !== n || !this.scene.objs) this.scene.cfg(n);
    const cw = Math.max(76, 16 * n + 16);
    L.cell = { w: cw, h: 50, gap: 8 }; L.qcard = { w: cw, h: 50 }; L.qp = cw + 10;
    L.qmax = Math.max(4, Math.floor((W - 24 - L.qx - 40) / (cw + 10)));
    L.ecard = { w: cw - 6, h: 46 }; L.estep = cw; L.emax = Math.max(4, Math.floor((W - 24 - L.qx - 40) / cw));
    this.nodeCard.n = this.childCard.n = 0; this.nodeCard.rx = this.childCard.rx = null;
    this.lastChild = null;
    this.sPos = roomIndex(E.rec.init); this.sDirt = E.rec.init.slice(1).map(v => v === "D" ? 1 : 0); this.sTheta = 0; this.spin = 0;
    this.sucking = false; this.particles = [];
  },

  startReplay(E) {
    if (this.replay) { this.replay = null; return; }
    if (!E.rec.solution.length) { E.toast = ["Chưa có lời giải để chạy.", 3]; return; }
    const path = E.events[E.events.length - 1].path;
    E.playing = false; E.seek(E.events.length - 1);
    this.replay = { states: path.map(e => E.rec.nodes[e].state), t: 0, step: 1.2, k: 0 };
  },

  update(dt, ev, E) {
    let state = ev.nodeState;
    if (this.replay) {
      const rp = this.replay; rp.t += dt * Math.min(3, Math.max(1, E.speed()));
      rp.k = Math.min(rp.states.length - 1, Math.floor(rp.t / rp.step)); state = rp.states[rp.k];
      if (rp.k >= rp.states.length - 1 && rp.t > (rp.states.length - 1) * rp.step + 1.4) this.replay = null;
    }
    this.updateScene(state, dt);
    this.nodeCard.update(ev.nodeState, dt, true);
    const ch = ev.child;
    if (ch) this.lastChild = ch.state;
    this.childCard.update(ch ? ch.state : (this.lastChild || ev.nodeState), dt, !!ch);
  },

  updateScene(state, dt) {
    const sc = this.scene, target = roomIndex(state), old = this.sPos;
    this.sPos = sm(this.sPos, target, 5, dt);
    const a = sc.posAt(old), b = sc.posAt(this.sPos), dr = b[0] - a[0], dc = b[1] - a[1];
    if (Math.hypot(dr, dc) > 0.004) {
      const tgt = Math.atan2(dc, dr); let diff = (tgt - this.sTheta + Math.PI) % (2 * Math.PI) - Math.PI; if (diff < -Math.PI) diff += 2 * Math.PI;
      this.sTheta += diff * Math.min(1, dt * 10);
    }
    let sucking = false;
    for (let i = 0; i < this.n; i++) {
      const tv = state[1 + i] === "D" ? 1 : 0;
      if (tv === 0 && this.sDirt[i] > 0.04 && Math.abs(this.sPos - i) < 0.6) sucking = true;
      this.sDirt[i] = sm(this.sDirt[i], tv, 4, dt);
    }
    const moving = Math.abs(target - this.sPos) > 0.05;
    this.spin += dt * (sucking || moving ? 720 : 120); this.sucking = sucking;
    if (sucking && Math.random() < 0.7) { const [rc, cc] = sc.posAt(this.sPos); this.particles.push([rc + (Math.random() - 0.5), cc + (Math.random() - 0.5), 6 + Math.random() * 14, 0]); }
    for (const p of this.particles) p[3] += dt * 2.4;
    this.particles = this.particles.filter(p => p[3] <= 0.45);
  },

  drawMain(ev, p, E) { this.drawScene(ev, E); this.drawInfo(ev, p, E); },

  drawScene(ev, E) {
    const sc = this.scene, zk = ISO.ZK;
    sc.ensureBg(); if (!sc.objs) sc.buildObjs();
    ctx.drawImage(sc.bg, SCENE.x, SCENE.y, SCENE.w, SCENE.h);
    ctx.save(); rr(SCENE.x, SCENE.y, SCENE.w, SCENE.h, 14); ctx.clip();
    for (let i = 0; i < this.n; i++) {
      const [gr, gc] = sc.cellOf(i), [r0, c0] = sc.origin(gr, gc), cl = 1 - this.sDirt[i];
      if (cl > 0.02) { ctx.globalAlpha = 0.18 * cl; polyPts([P(r0, c0), P(r0, c0 + sc.RS), P(r0 + sc.RS, c0 + sc.RS), P(r0 + sc.RS, c0)], [255, 255, 255]); ctx.globalAlpha = 1; }
    }
    const pulse = 0.5 + 0.5 * Math.sin(performance.now() / 260);
    for (let i = 0; i < this.n; i++) {
      const d = this.sDirt[i]; if (d < 0.03) continue;
      const [rc, cc] = sc.center(i), rnd = rng(i * 31 + 7);
      for (let k = 0; k < 9; k++) {
        const [x, y] = P(rc + (rnd() * 1.24 - 0.62) * d, cc + (rnd() * 1.24 - 0.62) * d);
        const rw = (6 + rnd() * 5) * zk * 1.5 * d + 1, rh = (4 + rnd() * 3) * zk * 1.5 * d + 1;
        ctx.beginPath(); ctx.ellipse(x, y, rw + 1, rh + 1, 0, 0, 7); ctx.fillStyle = "rgb(30,26,24)"; ctx.fill();
        ctx.beginPath(); ctx.ellipse(x, y, rw, rh, 0, 0, 7); ctx.fillStyle = "rgb(96,86,78)"; ctx.fill();
        ctx.beginPath(); ctx.ellipse(x - rw * 0.1, y - rh * 0.2, rw * 0.55, rh * 0.5, 0, 0, 7); ctx.fillStyle = "rgb(170,160,148)"; ctx.fill();
      }
      path(ring(rc, cc, 0.78 * (1 + 0.05 * pulse) * d, 0, 30)); ctx.strokeStyle = "rgb(255,226,110)"; ctx.lineWidth = 3; ctx.stroke();
    }
    const [rc, cc] = sc.posAt(this.sPos), rd = rc + cc;
    let drawn = false;
    for (const [depth, fn] of sc.objs) {
      if (!drawn && depth >= rd) { drawRobot(rc, cc, this.sTheta, this.spin, 0.44, this.sucking); drawn = true; }
      fn();
    }
    if (!drawn) drawRobot(rc, cc, this.sTheta, this.spin, 0.44, this.sucking);
    for (let i = 0; i < this.n; i++) {
      const [gr, gc] = sc.cellOf(i), [r0, c0] = sc.origin(gr, gc), [x, y] = P(r0 + sc.RS - 0.28, c0 + 0.36), on = Math.abs(this.sPos - i) < 0.5;
      fillRR(x - 13, y - 10, 26, 20, 6, on ? css(E.acc) : "rgb(30,38,58)");
      T(letter(i), x, y, { s: 14, b: 1, c: on ? [10, 22, 30] : COL.text, a: "center", v: "middle" });
    }
    for (const [pr, pc, z, age] of this.particles) {
      const [x0, y0] = P(pr, pc, z), [x1, y1] = P(rc, cc, 18), t = age / 0.45;
      circle(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 3, "rgb(170,162,152)");
    }
    const ch = ev.child;
    if (ch && !this.replay) {
      const ai = roomIndex(ev.nodeState), bi = roomIndex(ch.state);
      if (ai !== bi) {
        const a = sc.center(ai), b = sc.center(bi);
        for (let k = 0; k < 9; k++) {
          const t0 = k / 9, t1 = t0 + 0.05, p0 = P(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, 2), p1 = P(a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1, 2);
          line(p0[0], p0[1], p1[0], p1[1], css(E.acc), 4);
        }
        const [hx, hy] = P(b[0], b[1], 2); circle(hx, hy, 7, css(E.acc));
      } else {
        const c2 = sc.center(ai); path(ring(c2[0], c2[1], 0.9, 2, 30)); ctx.strokeStyle = css(E.acc); ctx.lineWidth = 3; ctx.stroke();
      }
      const [tx, ty] = P(...sc.center(bi), 70);
      fillRR(tx - 44, ty - 14, 88, 26, 13, css(shade(E.acc, 0.3))); strokeRR(tx - 44, ty - 14, 88, 26, 13, css(E.acc), 2);
      T(ev.act, tx, ty - 1, { s: 14, b: 1, c: E.acc, a: "center", v: "middle" });
    }
    ctx.restore();
    strokeRR(SCENE.x, SCENE.y, SCENE.w, SCENE.h, 14, css(COL.panelL), 1);
    T("ngôi nhà (mỗi phòng là một ô của bài toán)", SCENE.x + 14, SCENE.y + 8, { s: 14, b: 1, c: COL.gold });
    if (this.replay) {
      const k = this.replay.k, n = this.replay.states.length - 1, act = k >= 1 ? E.rec.solution[k - 1] : "bắt đầu", y = SCENE.y + SCENE.h - 40;
      fillRR(SCENE.x + 12, y, 330, 28, 14, "rgb(10,30,20)"); strokeRR(SCENE.x + 12, y, 330, 28, 14, css(COL.green), 2);
      T(`Robot chạy lời giải: bước ${k}/${n} · ${act}`, SCENE.x + 177, y + 14, { s: 14, b: 1, c: COL.green, a: "center", v: "middle" });
    }
  },

  drawInfo(ev, p, E) {
    const r = INFO, nc = this.nodeCard, cc = this.childCard, vb = ev.verdict;
    panel(r, "nút đang xét", COL.orange);
    T(E.hasCost ? `g = ${ev.nodeCost}` : `độ sâu ${ev.nodeDepth}`, r.x + r.w - 14, r.y + 12, { s: 12, c: E.hasCost ? COL.gold : COL.muted, a: "right" });
    nc.draw("node", COL.orange, ev.nodeState);
    if (ev.act) {
      const y = nc.rect.y + nc.rect.h + 6, cx = r.x + r.w / 2;
      fillRR(cx - 80, y, 160, 22, 11, css(shade(E.acc, 0.3))); strokeRR(cx - 80, y, 160, 22, 11, css(E.acc), 2);
      T({ Suck: "↓ Suck (hút bụi)", Left: "← Left", Right: "Right →" }[ev.act], cx, y + 11, { s: 14, b: 1, c: E.acc, a: "center", v: "middle" });
    }
    const border = { null: COL.cyan, ok: COL.green, dup: COL.red, goal: COL.gold, queued: COL.green, replace: COL.gold }[vb];
    cc.draw("child", border, ev.child ? ev.child.state : (this.lastChild || ev.nodeState));
    if (E.hasCost && ev.child) T(`g = ${ev.child.cost}`, cc.rect.x + cc.rect.w - 10, cc.rect.y + 4, { s: 12, b: 1, c: COL.gold, a: "right" });
    if (vb === "dup" && ev.child) { ctx.fillStyle = `rgba(255,98,112,${0.27 * (0.5 + 0.5 * Math.sin(p * 12))})`; ctx.fillRect(cc.rect.x, cc.rect.y, cc.rect.w, cc.rect.h); }
    E.drawVerdict(r, cc.rect.y + cc.rect.h + 8, ev, { rowH: 22, lampR: 6, fs: 11, bw: 240, bh: 28, bdy: 48 });
  },

  /* ---------- hộp thoại tự đặt phòng / bụi / robot / đích ---------- */
  editor: {
    active: false, ed: null,
    open(E) { this.active = true; E.playing = false; View.replay = null; const n = E.rec.init.length - 1; this.ed = { n, pos: roomIndex(E.rec.init), dirt: E.rec.init.slice(1).map(v => v === "D"), gpos: roomIndex(E.goal) }; },
    col(i) { const n = this.ed.n, w = (MOD.w - 80) / n; return [MOD.x + 40 + i * w, w]; },
    buttons() {
      return [
        { x: MOD.x + 40, y: MOD.y + 72, w: 40, h: 36, label: "−", key: "minus" }, { x: MOD.x + 200, y: MOD.y + 72, w: 40, h: 36, label: "+", key: "plus" },
        { x: MOD.x + MOD.w - 40 - 230, y: MOD.y + MOD.h - 62, w: 110, h: 42, label: "Hủy", key: "cancel" },
        { x: MOD.x + MOD.w - 40 - 112, y: MOD.y + MOD.h - 62, w: 112, h: 42, label: "Áp dụng", key: "apply", primary: true },
      ];
    },
    press(key, E) {
      const ed = this.ed;
      if (key === "cancel") this.active = false;
      else if (key === "minus" || key === "plus") {
        const n = Math.max(2, Math.min(6, ed.n + (key === "plus" ? 1 : -1)));
        if (n !== ed.n) { const lastGoal = ed.gpos >= ed.n - 1; ed.dirt = ed.dirt.slice(0, n); while (ed.dirt.length < n) ed.dirt.push(true); ed.pos = Math.min(ed.pos, n - 1); ed.gpos = lastGoal ? n - 1 : Math.min(ed.gpos, n - 1); ed.n = n; }
      } else if (key === "apply") { this.active = false; E.preset = -1; E.load(makeState(ed.pos, ed.dirt), makeGoal(ed.n, ed.gpos)); }
    },
    click(m, E) {
      for (const b of this.buttons()) if (inRect(m, b)) { this.press(b.key, E); return; }
      const ed = this.ed;
      for (let i = 0; i < ed.n; i++) {
        const [x, w] = this.col(i);
        if (inRect(m, { x: x + 6, y: MOD.y + 150, w: w - 12, h: 34 })) ed.pos = i;
        if (inRect(m, { x: x + 6, y: MOD.y + 224, w: w - 12, h: 84 })) ed.dirt[i] = !ed.dirt[i];
        if (inRect(m, { x: x + 6, y: MOD.y + 350, w: w - 12, h: 34 })) ed.gpos = i;
      }
    },
    key(e, E) { if (e.key === "Escape") this.active = false; else if (e.key === "Enter") this.press("apply", E); },
    draw(E) {
      ctx.fillStyle = "rgba(4,6,12,0.76)"; ctx.fillRect(0, 0, W, H);
      const ed = this.ed;
      fillRR(MOD.x, MOD.y, MOD.w, MOD.h, 18, "rgb(22,29,46)"); strokeRR(MOD.x, MOD.y, MOD.w, MOD.h, 18, css(E.acc), 2);
      T("Tự đặt phòng, bụi, robot và đích", MOD.x + 40, MOD.y + 16, { s: 22, b: 1 });
      T("Số phòng", MOD.x + 40, MOD.y + 52, { s: 14, b: 1, c: COL.muted });
      T(String(ed.n), MOD.x + 160, MOD.y + 90, { s: 26, b: 1, c: E.acc, a: "center", v: "middle" });
      T("Bấm vào ô để chọn. Hàng giữa: bấm để bật / tắt bụi.", MOD.x + 280, MOD.y + 82, { s: 14, c: COL.muted });
      for (const [lab, y] of [["Robot bắt đầu ở phòng", MOD.y + 128], ["Phòng nào đang bẩn (D)?", MOD.y + 196], ["Đích: robot phải dừng ở phòng", MOD.y + 330]]) T(lab, MOD.x + 40, y, { s: 15, b: 1 });
      for (let i = 0; i < ed.n; i++) {
        const [x, w] = this.col(i);
        const r1 = { x: x + 6, y: MOD.y + 150, w: w - 12, h: 34 };
        fillRR(r1.x, r1.y, r1.w, r1.h, 8, ed.pos === i ? css(COL.orange) : css(COL.panelL)); T(`Phòng ${letter(i)}`, r1.x + r1.w / 2, r1.y + 17, { s: 14, b: 1, c: ed.pos === i ? [20, 20, 26] : COL.text, a: "center", v: "middle" });
        const r2 = { x: x + 6, y: MOD.y + 224, w: w - 12, h: 84 }, dirty = ed.dirt[i];
        fillRR(r2.x, r2.y, r2.w, r2.h, 10, css(dirty ? DIRTY : CLEAN));
        if (dirty) for (const [dx, dy] of [[0.25, 0.3], [0.6, 0.5], [0.4, 0.75], [0.75, 0.25]]) circle(r2.x + r2.w * dx, r2.y + r2.h * dy, 5, "rgb(60,44,30)");
        T(`${letter(i)}: ` + (dirty ? "D (bẩn)" : "C (sạch)"), r2.x + r2.w / 2, r2.y + r2.h - 6, { s: 14, b: 1, c: [255, 255, 255], a: "center", v: "bottom" });
        if (ed.pos === i) { circle(r2.x + r2.w / 2, r2.y + 28, 15, "rgb(18,18,22)"); circle(r2.x + r2.w / 2, r2.y + 28, 5, css(COL.orange)); }
        const r3 = { x: x + 6, y: MOD.y + 350, w: w - 12, h: 34 };
        fillRR(r3.x, r3.y, r3.w, r3.h, 8, ed.gpos === i ? css(COL.green) : css(COL.panelL)); T(`Phòng ${letter(i)}`, r3.x + r3.w / 2, r3.y + 17, { s: 14, b: 1, c: ed.gpos === i ? [10, 30, 20] : COL.text, a: "center", v: "middle" });
      }
      T(`Không gian trạng thái: ${ed.n} × 2^${ed.n} = ${ed.n * 2 ** ed.n} trạng thái. Đích: robot ở phòng ${letter(ed.gpos)}, mọi phòng sạch (C).`, MOD.x + 40, MOD.y + 410, { s: 14, c: COL.muted });
      for (const b of this.buttons()) {
        const on = b.primary, hot = inRect(mouse, b);
        fillRR(b.x, b.y, b.w, b.h, 10, on ? css(E.acc) : hot ? "rgb(52,64,92)" : css(COL.panelL));
        T(b.label, b.x + b.w / 2, b.y + b.h / 2, { s: 16, b: 1, c: on ? [10, 22, 30] : COL.text, a: "center", v: "middle" });
      }
    },
  },
};

E.start(View);
