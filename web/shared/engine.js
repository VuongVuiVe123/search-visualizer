"use strict";

/* ============================================================================
   Engine dùng chung: canvas sắc nét, cầu nối Python (Pyodide), bộ phát sự kiện
   và các khung chung (code sáng dòng, bảng node, frontier, explored, điều khiển).
   Mỗi bài toán chỉ cần viết một "view" (xem web/puzzle8/view.js, web/vacuum/view.js).

   Tệp này CHỈ VẼ. Thuật toán nằm ở core/, bài toán (trạng thái đầu, đích, bài mẫu)
   nằm ở problems/, việc ghi lại từng bước nằm ở tracing/ (đều là Python).
   ============================================================================ */

let W = 1400, H = 900;
const SANS = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif';
const MONO = 'Consolas, "SF Mono", Menlo, "DejaVu Sans Mono", monospace';
const COL = {
  bg: [13, 17, 27], panel: [20, 26, 40], panelL: [34, 43, 64], text: [228, 234, 246], muted: [126, 140, 166],
  cyan: [86, 214, 230], blue: [100, 156, 255], orange: [255, 170, 70], red: [255, 98, 112], green: [104, 224, 150], gold: [255, 214, 90],
};
const SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16];

const css = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const mixc = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const shade = (c, k) => c.map(v => Math.max(0, Math.min(255, v * k)));
const sm = (v, t, k, dt) => v + (t - v) * (1 - Math.exp(-k * dt));
const inRect = (m, r) => m.x >= r.x && m.x < r.x + r.w && m.y >= r.y && m.y < r.y + r.h;
const sk = s => s.join(",");

let cv, ctx, scale = 1, offX = 0, offY = 0, dpr = 1;
const mouse = { x: -1, y: -1 };
const CACHE = new Map();

function resize() {
  dpr = window.devicePixelRatio || 1;
  const w = window.innerWidth, h = window.innerHeight;
  cv.style.width = w + "px"; cv.style.height = h + "px";
  cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
  scale = Math.min(w / W, h / H);
  offX = (w - W * scale) / 2; offY = (h - H * scale) / 2;
  CACHE.clear();
  if (E.view && E.view.onResize) E.view.onResize();
}

function rr(x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}
function fillRR(x, y, w, h, r, fill) { rr(x, y, w, h, r); ctx.fillStyle = fill; ctx.fill(); }
function strokeRR(x, y, w, h, r, stroke, lw = 1) { rr(x, y, w, h, r); ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
function circle(x, y, r, fill) { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill(); }
function line(x1, y1, x2, y2, stroke, lw = 1) { ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
function T(s, x, y, o = {}) {
  ctx.font = `${o.b ? "bold " : ""}${o.s || 14}px ${o.f === "m" ? MONO : SANS}`;
  ctx.fillStyle = css(o.c || COL.text, o.al === undefined ? 1 : Math.max(0, o.al));
  ctx.textAlign = o.a || "left"; ctx.textBaseline = o.v || "top";
  ctx.fillText(s, x, y);
}
function tw(s, size, bold, mono) { ctx.font = `${bold ? "bold " : ""}${size}px ${mono ? MONO : SANS}`; return ctx.measureText(s).width; }
function wrapText(s, size, width) {
  const words = s.split(" "), lines = []; let cur = "";
  for (const w of words) {
    const t = (cur + " " + w).trim();
    if (tw(t, size) <= width) cur = t; else { lines.push(cur); cur = w; }
  }
  lines.push(cur); return lines;
}
function panel(r, title, accent) {
  fillRR(r.x, r.y, r.w, r.h, 14, css(COL.panel));
  strokeRR(r.x, r.y, r.w, r.h, 14, css(COL.panelL), 1);
  if (title) T(title, r.x + 14, r.y + 10, { s: 15, b: 1, c: accent || COL.cyan });
}

/* Vẽ một lần vào canvas ẩn (ở độ phân giải thật) rồi dùng lại: dùng cho các thẻ trạng thái nhỏ. */
function drawCached(key, w, h, fn, cx, cy, sc = 1, al = 1) {
  const pw = Math.max(8, Math.round(w * scale * dpr)), ph = Math.max(8, Math.round(h * scale * dpr));
  const k = key + "|" + pw + "x" + ph;
  let c = CACHE.get(k);
  if (!c) { c = document.createElement("canvas"); c.width = pw; c.height = ph; fn(c.getContext("2d"), pw, ph); CACHE.set(k, c); }
  const dw = w * sc, dh = h * sc;
  ctx.globalAlpha = Math.max(0, Math.min(1, al));
  ctx.drawImage(c, cx - dw / 2, cy - dh / 2, dw, dh);
  ctx.globalAlpha = 1;
  return { x: cx - dw / 2, y: cy - dh / 2, w: dw, h: dh };
}

/* ---------------- Cầu nối Python ----------------
   base: đường dẫn tới thư mục gốc của dự án (nơi có core/, problems/, tracing/).
   Danh sách tệp Python cần nạp nằm ở web/manifest.json. */
const PY = {};
async function loadPython(base, setStatus) {
  if (typeof loadPyodide !== "function") throw new Error("không tải được Pyodide từ mạng (kiểm tra kết nối internet)");
  setStatus("Đang tải Python (Pyodide)…");
  const py = await loadPyodide();
  setStatus("Đang nạp mã Python…");
  const files = await (await fetch(base + "web/manifest.json")).json();
  py.FS.mkdirTree("/py");
  for (const f of files) {
    const dir = f.includes("/") ? f.slice(0, f.lastIndexOf("/")) : "";
    if (dir) py.FS.mkdirTree("/py/" + dir);
    py.FS.writeFile("/py/" + f, await (await fetch(base + f)).text());
  }
  py.runPython("import sys\nsys.path.insert(0, '/py')");
  const api = py.pyimport("tracing.api");
  PY.algos = () => JSON.parse(api.algos_json(""));
  PY.problem = pid => JSON.parse(api.problem_json(JSON.stringify(pid)));
  PY.record = (pid, algo, init, goal) => JSON.parse(api.record_json(JSON.stringify([pid, algo, init, goal])));
  PY.quick = (pid, algo, init, goal) => JSON.parse(api.quick_json(JSON.stringify([pid, algo, init, goal])));
  PY.solvable = (pid, init, goal) => JSON.parse(api.solvable_json(JSON.stringify([pid, init, goal])));
  PY.random = (pid, algo, goal = null) => JSON.parse(api.random_json(JSON.stringify([pid, algo, goal])));
}

class Rec {
  constructor(pid, algo, init, goal) {
    const d = PY.record(pid, algo, init, goal);
    this.init = init; this.goal = goal; this.algo = algo;
    this.events = d.events; this.solution = d.solution; this.nodes = d.nodes;
    for (const n of this.nodes) n.key = sk(n.state);
  }
}

/* ---------------- Engine ---------------- */
const CODE_TOKEN = /\b(def|if|for|while|not|in|return|and)\b|\b[A-Za-z_]\w*(?=\()|\b(False|True|None)\b/g;
function tokenize(ln) {
  const lead = ln.length - ln.trimStart().length;
  ln = " ".repeat(Math.floor(lead / 2)) + ln.trimStart();
  const segs = []; let pos = 0, m;
  CODE_TOKEN.lastIndex = 0;
  while ((m = CODE_TOKEN.exec(ln))) {
    if (m.index > pos) segs.push([ln.slice(pos, m.index), [214, 222, 240]]);
    const col = m[1] ? [255, 130, 170] : m[2] ? [255, 190, 110] : [110, 200, 255];
    segs.push([m[0], col]); pos = m.index + m[0].length;
  }
  if (pos < ln.length) segs.push([ln.slice(pos), [214, 222, 240]]);
  return segs;
}

const E = {
  view: null, algos: {}, keys: [], algo: "bfs", preset: 0, speedI: 2, acc: [86, 214, 230], swX: 0,
  toast: ["", 0], capText: "", capAge: 0, barY: 0, buttons: [], swRects: {},

  async start(view) {
    this.view = view;
    cv = document.getElementById("c"); ctx = cv.getContext("2d");
    W = view.layout.W; H = view.layout.H;
    resize();
    const st = document.getElementById("status");
    try {
      await loadPython(view.pythonBase, t => { st.textContent = t; });
      this.algos = PY.algos(); this.keys = Object.keys(this.algos);
      view.problem = PY.problem(view.id);
      this.algo = this.keys[0]; this.acc = this.algos[this.algo].color.slice();
      this.layoutSwitch(); this.swX = this.swRects[this.algo].x;
      this.barY = view.layout.code.y + 36;
      const p = view.presets(this.algo)[view.problem.defaultPreset || 0];
      this.preset = view.problem.defaultPreset || 0;
      this.load(p[1], p[2]);
      st.style.display = "none";
      let last = performance.now();
      const frame = now => {
        const dt = Math.min(0.05, (now - last) / 1000); last = now;
        this.update(dt); this.draw();
        requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
    } catch (e) { st.textContent = "Không khởi động được: " + e.message; console.error(e); }
  },

  layoutSwitch() {
    const n = this.keys.length, cw = (440 - (n - 1) * 8) / n;
    this.keys.forEach((k, i) => { this.swRects[k] = { x: 462 + i * (cw + 8), y: 16, w: cw, h: 52 }; });
  },

  get presets() { return this.view.presets(this.algo); },
  get isStack() { return this.algos[this.algo].frontier === "stack"; },
  get ev() { return this.events[this.evI]; },
  speed() { return SPEEDS[this.speedI]; },
  seek(i) { this.evI = Math.max(0, Math.min(this.events.length - 1, i)); this.evT = 0; this.one = false; },
  quick(init, goal, algo) { return PY.quick(this.view.id, algo || this.algo, init, goal); },

  load(init, goal) {
    this.goal = goal;
    this.rec = new Rec(this.view.id, this.algo, init, goal);
    this.events = this.rec.events;
    this.evI = 0; this.evT = 0; this.playing = false; this.one = false;
    this.animTab = new Map(); this.animQ = new Map(); this.animE = new Map();
    this.scroll = 0; this.lamps = [[70, 80, 100], [70, 80, 100]];
    this.bannerKey = null; this.bannerAge = 1; this.layoutTn = -1;
    this.view.onLoad(this);
  },

  setAlgo(a) {
    if (a === this.algo) return;
    const init = this.rec.init, goal = this.goal;
    this.playing = false; this.algo = a;
    if (this.quick(init, goal, a)) this.load(init, goal);
    else {
      const p = this.presets[Math.min(1, this.presets.length - 1)];
      this.preset = Math.min(1, this.presets.length - 1); this.load(p[1], p[2]);
      this.toast = [`Bài đang đặt quá lớn với ${this.algos[a].name} (phải mở hơn ${this.algos[a].limit} nút) → chuyển sang bài mẫu.`, 3.5];
    }
  },

  press(key) {
    const last = this.events.length - 1;
    if (key === "play") { if (this.evI >= last) this.seek(0); this.playing = !this.playing; this.view.onPlayToggle && this.view.onPlayToggle(this); }
    else if (key === "next") { this.playing = false; if (this.evI < last) { this.evI++; this.evT = 0; this.one = true; } }
    else if (key === "back") { this.playing = false; this.seek(this.evI - 1); }
    else if (key === "node") {
      let j = this.evI + 1; while (j < last && this.events[j].line !== this.algos[this.algo].takeLine) j++;
      this.evI = Math.min(j, last); this.evT = 0; this.one = true;
    }
    else if (key === "reset") { this.playing = false; this.seek(0); }
    else if (key === "slow") this.speedI = Math.max(0, this.speedI - 1);
    else if (key === "fast") this.speedI = Math.min(SPEEDS.length - 1, this.speedI + 1);
    else if (key.startsWith("alg_")) this.setAlgo(key.slice(4));
    else if (/^p\d$/.test(key)) { const p = this.presets[+key[1]]; if (p) { this.preset = +key[1]; this.load(p[1], p[2]); } }
    else if (key === "rand") { const [i, g] = this.view.randomPuzzle(this); this.preset = -1; this.load(i, g); }
    else if (key === "edit") this.view.editor.open(this);
    else this.view.press && this.view.press(key, this);
  },

  buildButtons() {
    const L = this.view.layout, y = L.btnY, b = []; let bx = 12;
    for (const [w, label, key] of [[80, "Về đầu", "reset"], [70, "Lùi", "back"], [96, this.playing ? "Dừng" : "Phát", "play"],
    [70, "Tiếp", "next"], [100, "Node kế", "node"], [38, "−", "slow"], [38, "+", "fast"]]) {
      b.push({ x: bx, y, w, h: 40, label, key, active: key === "play" && this.playing }); bx += w + 8;
      if (key === "slow") { this.speedX = bx - 8 + 6; bx += 56; }
    }
    bx = L.presetX; this.presetLabelX = bx - 8;
    this.presets.forEach((p, i) => { b.push({ x: bx, y, w: 78, h: 40, label: p[0], key: "p" + i, active: this.preset === i }); bx += 84; });
    b.push({ x: bx, y, w: 96, h: 40, label: "Tự đặt", key: "edit" }); bx += 104;
    b.push({ x: bx, y, w: 116, h: 40, label: "Ngẫu nhiên", key: "rand" }); bx += 124;
    for (const x of (this.view.extraButtons ? this.view.extraButtons(this) : [])) { b.push({ x: bx, y, h: 40, ...x }); bx += x.w + 8; }
    this.buttons = b;
  },

  computeLayout(tn) {
    const L = this.view.layout, nodes = this.rec.nodes, gap = L.cell.gap, cw = L.cell.w, ch = L.cell.h;
    const cols = Math.max(1, Math.floor((L.tab.w - 28 + gap) / (cw + gap))), by = new Map();
    for (let e = 0; e < tn; e++) { const d = nodes[e].depth; if (!by.has(d)) by.set(d, []); by.get(d).push(e); }
    const pos = new Map(), heads = []; let y = 0;
    for (const d of [...by.keys()].sort((a, b) => a - b)) {
      const arr = by.get(d); heads.push([d, y, arr.length]); y += 24;
      arr.forEach((e, k) => pos.set(e, [14 + (k % cols) * (cw + gap), y + Math.floor(k / cols) * (ch + gap)]));
      y += (Math.floor((arr.length - 1) / cols) + 1) * (ch + gap) + 6;
    }
    return [pos, heads, y];
  },

  update(dt) {
    const last = this.events.length - 1, L = this.view.layout;
    this.toast[1] = Math.max(0, this.toast[1] - dt);
    const tgt = this.algos[this.algo].color;
    this.acc = this.acc.map((v, i) => sm(v, tgt[i], 9, dt));
    this.swX = sm(this.swX, this.swRects[this.algo].x, 14, dt);
    if (this.playing || this.one) {
      this.evT += dt * this.speed();
      while (this.evT >= this.ev.dur) {
        if (this.evI >= last) { this.evT = this.ev.dur; this.playing = this.one = false; break; }
        if (this.one) { this.evT = this.ev.dur; this.one = false; break; }
        this.evT -= this.ev.dur; this.evI++;
      }
    }
    const ev = this.ev;
    this.barY = sm(this.barY, L.code.y + 36 + ev.line * L.lh, 30, dt);
    for (let k = 0; k < 2; k++) {
      const g = ev.gate[k], t = g === null ? [84, 96, 120] : g ? COL.red : COL.green;
      this.lamps[k] = this.lamps[k].map((v, j) => sm(v, t[j], 12, dt));
    }
    const key = ev.verdict + "|" + (ev.child ? ev.child.key : "");
    if (key !== this.bannerKey) { this.bannerKey = key; this.bannerAge = 0; }
    this.bannerAge += dt;
    if (ev.cap !== this.capText) { this.capText = ev.cap; this.capAge = 0; }
    this.capAge += dt;
    this.view.update(dt, ev, this);
    this.updateTable(dt); this.updateQueue(dt); this.updateExplored(dt);
    this.buildButtons();
  },

  updateTable(dt) {
    const L = this.view.layout, ev = this.ev, tn = ev.tn, cw = L.cell.w, ch = L.cell.h;
    if (tn !== this.layoutTn) { [this.tpos, this.theads, this.ttotal] = this.computeLayout(tn); this.layoutTn = tn; }
    const viewH = L.tab.h - 48;
    let focus = ev.nodeEid !== null ? ev.nodeEid : (tn ? tn - 1 : null);
    if (ev.childEid !== null && ev.childEid < tn) focus = ev.childEid;
    if (focus !== null && this.tpos.has(focus)) {
      const t = this.tpos.get(focus)[1] - viewH * 0.4;
      this.scroll = sm(this.scroll, Math.max(0, Math.min(t, Math.max(0, this.ttotal - viewH))), 5, dt);
    }
    const cb = this.view.anchors(this).child;
    for (const e of [...this.animTab.keys()]) if (e >= tn) this.animTab.delete(e);
    for (const [e, [x, y]] of this.tpos) {
      let a = this.animTab.get(e);
      if (!a) { a = [cb[0] - L.tab.x - cw / 2, cb[1] - L.tab.y - 36 + this.scroll - ch / 2, 0.35, 0]; this.animTab.set(e, a); }
      a[0] = sm(a[0], x, 7, dt); a[1] = sm(a[1], y, 7, dt); a[2] = sm(a[2], 1, 7, dt); a[3] = sm(a[3], 1, 9, dt);
    }
  },
  updateQueue(dt) {
    const L = this.view.layout, ev = this.ev, fr = ev.frontier, an = this.view.anchors(this), cb = an.child, nb = an.node;
    for (const e of [...this.animQ.keys()]) if (e >= ev.tn) this.animQ.delete(e);
    const offset = this.isStack ? Math.max(0, fr.length - L.qmax) : 0;
    const inF = new Set(fr);
    fr.forEach((e, i) => {
      let a = this.animQ.get(e);
      if (!a) { a = [cb[0], cb[1], 0.4, 0, false]; this.animQ.set(e, a); }
      a[4] = false;
      const idx = i - offset, show = idx >= 0 && idx < L.qmax;
      a[0] = sm(a[0], L.qx + idx * L.qp + L.qcard.w / 2, 8, dt); a[1] = sm(a[1], L.qy + 60, 8, dt);
      a[2] = sm(a[2], 1, 8, dt); a[3] = sm(a[3], show ? 1 : 0, 8, dt);
    });
    for (const [e, a] of [...this.animQ]) {
      if (!inF.has(e)) {
        a[4] = true; a[0] = sm(a[0], nb[0], 7, dt); a[1] = sm(a[1], nb[1], 7, dt);
        a[2] = sm(a[2], 0.7, 7, dt); a[3] = sm(a[3], 0, 9, dt);
        if (a[3] < 0.03) this.animQ.delete(e);
      }
    }
  },
  updateExplored(dt) {
    const L = this.view.layout, ev = this.ev, ex = ev.explored, nb = this.view.anchors(this).node;
    const start = Math.max(0, ex.length - L.emax), has = new Set(ex);
    for (const e of [...this.animE.keys()]) if (!has.has(e)) this.animE.delete(e);
    ex.forEach((e, i) => {
      let a = this.animE.get(e);
      if (!a) { a = [nb[0], nb[1], 0.5, 0]; this.animE.set(e, a); }
      const idx = i - start;
      a[0] = sm(a[0], L.qx + idx * L.estep + L.estep / 2, 8, dt); a[1] = sm(a[1], L.ey + 36, 8, dt);
      a[2] = sm(a[2], 1, 8, dt); a[3] = sm(a[3], idx >= 0 ? 1 : 0, 8, dt);
    });
  },

  draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = "#080a10"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.setTransform(dpr * scale, 0, 0, dpr * scale, dpr * offX, dpr * offY);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.clip();
    ctx.fillStyle = css(COL.bg); ctx.fillRect(0, 0, W, H);
    const ev = this.ev, p = ev.dur ? Math.min(1, this.evT / ev.dur) : 1;
    this.sets = { fr: new Set(ev.frontier), ex: new Set(ev.explored), path: new Set(ev.path) };
    this.drawCode(ev); this.drawTable(ev, p);
    this.view.drawMain(ev, p, this);
    this.drawQueue(ev, p); this.drawExplored(ev); this.drawControls(); this.drawHeader(ev);
    if (this.toast[1] > 0) {
      const L = this.view.layout, a = Math.min(1, this.toast[1] / 0.5), x = L.tab.x + 12, w = L.tab.w - 24, y = L.tab.y + L.tab.h - 46;
      fillRR(x, y, w, 34, 17, "rgb(60,40,18)"); strokeRR(x, y, w, 34, 17, css(COL.orange), 2);
      T(wrapText(this.toast[0], 13, w - 28)[0], x + w / 2, y + 17, { s: 13, c: COL.orange, a: "center", v: "middle", al: a });
    }
    if (this.view.editor.active) this.view.editor.draw(this);
    ctx.restore();
  },

  drawHeader(ev) {
    const acc = this.acc, al = this.algos[this.algo];
    T(al.full, 16, 8, { s: 28, b: 1, c: acc });
    T(this.view.subtitle(this), 18, 50, { s: 15, c: COL.muted });
    const chips = [["Đã mở", ev.explored.length, COL.orange], ["Frontier", ev.frontier.length, COL.blue], ["Nút sinh ra", ev.tn, COL.cyan], ["Độ sâu", ev.nodeDepth, COL.gold]];
    let x = W - 16;
    for (const [name, val, col] of chips.slice().reverse()) {
      const w = Math.max(tw(name, 13), 36) + 26;
      fillRR(x - w, 12, w, 52, 10, css(COL.panel)); strokeRR(x - w, 12, w, 52, 10, css(shade(col, 0.55)), 1);
      T(name, x - w / 2, 18, { s: 13, c: COL.muted, a: "center" }); T(String(val), x - w / 2, 34, { s: 22, b: 1, c: col, a: "center" });
      x -= w + 8;
    }
    this.view.drawGoal(x - 8, this);
    fillRR(458, 10, 448, 64, 18, "rgb(16,21,34)"); strokeRR(458, 10, 448, 64, 18, css(COL.panelL), 1);
    const r0 = this.swRects[this.algo];
    fillRR(this.swX - 4, 12, r0.w + 8, 60, 18, css(shade(acc, 0.35))); fillRR(this.swX, 16, r0.w, 52, 14, css(acc));
    for (const k of this.keys) {
      const r = this.swRects[k], on = k === this.algo, a = this.algos[k];
      const c = on ? [10, 22, 30] : inRect(mouse, r) ? COL.text : COL.muted;
      T(a.name, r.x + 18, r.y + 26, { s: 26, b: 1, c, v: "middle" });
      T(a.l1, r.x + 90, r.y + 17, { s: 13, b: 1, c, v: "middle" }); T(a.l2, r.x + 90, r.y + 35, { s: 12, c, v: "middle" });
    }
  },

  drawCode(ev) {
    const L = this.view.layout, r = L.code, acc = this.acc, al = this.algos[this.algo];
    panel(r, `mã nguồn  ${al.name}(problem)`, acc);
    strokeRR(r.x, r.y, r.w, r.h, 14, css(shade(acc, 0.6)), 2);
    fillRR(r.x + 8, this.barY, r.w - 16, L.lh, 6, "rgb(24,32,52)");
    fillRR(r.x + 8, this.barY, r.w - 16, L.lh, 6, css(acc, 0.16));
    fillRR(r.x + 8, this.barY, 4, L.lh, 2, css(acc));
    al.code.forEach((ln, i) => {
      const y = r.y + 36 + i * L.lh, act = i === ev.line;
      T(String(i + 1), r.x + 34, y + 3, { s: 13, f: "m", c: act ? acc : [70, 82, 110], a: "right" });
      let x = r.x + 46;
      for (const [s, c] of tokenize(ln)) {
        T(s, x, y + 3, { s: 14, f: "m", c: act ? c : shade(c, 0.5) });
        x += tw(s, 14, false, true);
      }
    });
    T(`dòng ${ev.line + 1} · sự kiện ${this.evI + 1}/${this.events.length}`, r.x + r.w - 14, r.y + 12, { s: 13, c: COL.muted, a: "right" });
    const cx = r.x + 10, cy = r.y + r.h - 72, cw = r.w - 20;
    fillRR(cx, cy, cw, 62, 10, "rgb(14,20,34)"); strokeRR(cx, cy, cw, 62, 10, css(COL.panelL), 1);
    const a = Math.min(1, this.capAge / 0.25);
    wrapText(this.capText, 15, cw - 24).slice(0, 3).forEach((l, k) => T(l, cx + 12, cy + 7 + k * 17, { s: 15, al: a }));
  },

  cellStyle(eid, ev, pulse) {
    if (this.sets.path.has(eid)) return [COL.gold, 3, 1];
    if (eid === ev.nodeEid) return [mixc(COL.orange, [255, 240, 200], pulse * 0.6), 3, 1];
    if (this.sets.ex.has(eid)) return [[70, 82, 112], 1, 0.55];
    if (this.sets.fr.has(eid)) return [COL.blue, 2, 1];
    return [[70, 82, 112], 1, 1];
  },

  drawTable(ev, p) {
    const L = this.view.layout, TAB = L.tab, cw = L.cell.w, ch = L.cell.h, V = this.view;
    panel(TAB, V.tableTitle, COL.gold);
    const vx = TAB.x + 6, vy = TAB.y + 36, vw = TAB.w - 12, vh = TAB.h - 44, oy = vy - this.scroll;
    ctx.save(); ctx.beginPath(); ctx.rect(vx, vy, vw, vh); ctx.clip();
    for (const [d, y, n] of this.theads) {
      const yy = oy + y;
      if (yy > vy - 30 && yy < vy + vh) {
        T(`Độ sâu ${d}`, TAB.x + 18, yy + 2, { s: 14, b: 1, c: COL.gold }); T(`${n} nút`, TAB.x + TAB.w - 22, yy + 3, { s: 13, c: COL.muted, a: "right" });
        line(TAB.x + 14, yy + 21, TAB.x + TAB.w - 14, yy + 21, css(COL.panelL));
      }
    }
    const nodes = this.rec.nodes, pulse = 0.5 + 0.5 * Math.sin(performance.now() / 220);
    const order = [...this.animTab.keys()].sort((a, b) => (a === ev.nodeEid) - (b === ev.nodeEid) || this.sets.path.has(a) - this.sets.path.has(b) || a - b);
    for (const e of order) {
      const [x, y, sc, al] = this.animTab.get(e), cx = TAB.x + x + cw / 2, cy = oy + y + ch / 2;
      if (cy < vy - ch || cy > vy + vh + ch) continue;
      let [col, bw, dim] = this.cellStyle(e, ev, pulse);
      const r = V.drawCard(nodes[e].state, cx, cy, cw, ch, sc, al * (0.5 + 0.5 * dim));
      if (e === ev.nodeEid) strokeRR(r.x - 5, r.y - 5, r.w + 10, r.h + 10, 10, css(shade(COL.orange, 0.45)), 2);
      if (e === ev.match) col = COL.red;
      strokeRR(r.x - 1, r.y - 1, r.w + 2, r.h + 2, 8, css(col), bw);
    }
    const ne = ev.nodeEid;
    if (ne !== null && this.animTab.has(ne) && this.animTab.has(nodes[ne].parent)) {
      const a = this.animTab.get(ne), b = this.animTab.get(nodes[ne].parent);
      line(TAB.x + a[0] + cw / 2, oy + a[1] + ch / 2, TAB.x + b[0] + cw / 2, oy + b[1] + ch / 2, css(shade(COL.orange, 0.7)), 2);
    }
    if (ev.path.length) {
      const pts = ev.path.filter(e => this.animTab.has(e)).map(e => [TAB.x + this.animTab.get(e)[0] + cw / 2, oy + this.animTab.get(e)[1] + ch / 2]);
      if (pts.length > 1) {
        const t = ev.kind === "done" ? Math.min(1, p * 1.3) : 1, n = Math.max(1, Math.floor(t * (pts.length - 1)));
        ctx.beginPath(); pts.slice(0, n + 1).forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]));
        ctx.strokeStyle = css(COL.gold); ctx.lineWidth = 4; ctx.stroke();
        pts.slice(0, n + 1).forEach(q => circle(q[0], q[1], 5, css(COL.gold)));
      }
    }
    ctx.restore();
    if (this.ttotal > vh) {
      const th = Math.max(30, vh * vh / this.ttotal), ty = vy + (vh - th) * (this.scroll / Math.max(1, this.ttotal - vh));
      fillRR(TAB.x + TAB.w - 8, ty, 4, th, 2, css(COL.panelL));
    }
  },

  /* Hai đèn kiểm tra + biểu ngữ kết luận, dùng chung cho mọi bài toán. */
  drawVerdict(r, y, ev, o = {}) {
    const rowH = o.rowH || 28, lampR = o.lampR || 8, fs = o.fs || 13, bw = o.bw || 260, bh = o.bh || 34, bdy = o.bdy || 62;
    ["child.state in explored ?", "in_frontier ?"].forEach((label, k) => {
      const yy = y + k * rowH, col = this.lamps[k];
      circle(r.x + 26, yy + rowH / 2 - 3, lampR + 3, css(shade(col, 0.4))); circle(r.x + 26, yy + rowH / 2 - 3, lampR, css(col));
      T(label, r.x + 46, yy + 3, { s: fs, f: "m" });
      const g = ev.gate[k];
      T(g === null ? "?" : g ? "CÓ" : "KHÔNG", r.x + r.w - 18, yy + 1, { s: fs + 2, b: 1, c: col, a: "right" });
    });
    const vb = ev.verdict;
    if (vb) {
      const msg = { ok: "Nút mới → xét tiếp", dup: "Trùng → BỎ", goal: "ĐÍCH!", queued: this.isStack ? "Vào ngăn xếp" : "Vào hàng đợi" }[vb];
      const col = { ok: COL.green, dup: COL.red, goal: COL.gold, queued: COL.green }[vb];
      const e = 1 - Math.pow(1 - Math.min(1, this.bannerAge / 0.3), 3), w = bw * (0.6 + 0.4 * e), cx = r.x + r.w / 2, yy = y + bdy;
      fillRR(cx - w / 2, yy, w, bh, bh / 2, css(shade(col, 0.28))); strokeRR(cx - w / 2, yy, w, bh, bh / 2, css(col), 2);
      T(msg, cx, yy + bh / 2, { s: bh > 30 ? 17 : 15, b: 1, c: col, a: "center", v: "middle", al: e });
    }
  },

  drawQueue(ev, p) {
    const L = this.view.layout, qy = L.qy, acc = this.acc, dfs = this.isStack, QX = L.qx, QP = L.qp, QMAX = L.qmax, cw = L.qcard.w, ch = L.qcard.h;
    const rect = { x: 12, y: qy, w: W - 24, h: 100 };
    panel(rect); strokeRR(rect.x, rect.y, rect.w, rect.h, 14, css(shade(acc, 0.6)), 2);
    T("FRONTIER", 26, qy + 18, { s: 15, b: 1, c: acc }); T(dfs ? "ngăn xếp LIFO" : "hàng đợi FIFO", 26, qy + 40, { s: 13, c: COL.muted });
    T(`${ev.frontier.length} nút`, 26, qy + 62, { s: 13, c: COL.muted });
    const bx = QX - 8, by = qy + 28, bw = QMAX * QP + 2, bh = 64;
    fillRR(bx, by, bw, bh, 10, "rgb(14,20,34)");
    const hidden = dfs ? Math.max(0, ev.frontier.length - QMAX) : 0;
    if (dfs) {
      T("ĐÁY" + (hidden ? `  (+${hidden} nút ẩn)` : ""), bx + 4, qy + 8, { s: 12, b: 1, c: COL.muted });
      T("ĐỈNH  (push / pop)", bx + bw - 4, qy + 8, { s: 12, b: 1, c: COL.green, a: "right" });
    } else {
      T("HEAD  (dequeue)", bx + 4, qy + 8, { s: 12, b: 1, c: COL.green });
      T("TAIL  (enqueue)", bx + bw - 4, qy + 8, { s: 12, b: 1, c: COL.orange, a: "right" });
    }
    ctx.save(); ctx.beginPath(); ctx.rect(bx + 2, by - 4, bw - 4, bh + 8); ctx.clip();
    const nodes = this.rec.nodes;
    for (const [e, a] of [...this.animQ].sort((u, v) => u[1][4] - v[1][4])) {
      const r = this.view.drawCard(nodes[e].state, a[0], a[1], cw, ch, a[2], a[3]);
      if (!a[4]) strokeRR(r.x - 1, r.y - 1, r.w + 2, r.h + 2, 8, css(e === ev.match ? COL.red : COL.blue), e === ev.match ? 3 : 2);
    }
    if (ev.kind === "scan" && ev.frontier.length) {
      const fr = ev.frontier, lim = ev.scanMatch !== null && fr.includes(ev.scanMatch) ? fr.indexOf(ev.scanMatch) : fr.length - 1;
      let ci = lim ? Math.min(lim, Math.floor(Math.min(1, p * 1.15) * lim + 0.5)) : 0;
      ci -= hidden;
      if (ci >= 0 && ci < QMAX) {
        const cx = QX + ci * QP + cw / 2, hit = ev.scanMatch !== null && ci + hidden === lim && p > 0.6, col = hit ? COL.red : COL.cyan;
        strokeRR(cx - cw / 2 - 4, qy + 28, cw + 8, 64, 10, css(col), 3);
        ctx.beginPath(); ctx.moveTo(cx - 7, qy + 21); ctx.lineTo(cx + 7, qy + 21); ctx.lineTo(cx, qy + 30); ctx.fillStyle = css(col); ctx.fill();
      }
    }
    ctx.restore();
    const extra = dfs ? 0 : ev.frontier.length - QMAX;
    if (extra > 0) T(`+${extra}`, bx + bw + 4, qy + 48, { s: 15, b: 1, c: COL.muted });
  },

  drawExplored(ev) {
    const L = this.view.layout, ey = L.ey, rect = { x: 12, y: ey, w: W - 24, h: 72 };
    panel(rect);
    T("EXPLORED", 26, ey + 10, { s: 15, b: 1, c: COL.orange }); T("đã mở", 26, ey + 31, { s: 13, c: COL.muted });
    T(`${ev.explored.length} nút`, 26, ey + 49, { s: 13, c: COL.muted });
    ctx.save(); ctx.beginPath(); ctx.rect(L.qx - 8, ey + 4, W - L.qx - 12, 64); ctx.clip();
    const nodes = this.rec.nodes;
    for (const [e, a] of this.animE) {
      const r = this.view.drawCard(nodes[e].state, a[0], a[1], L.ecard.w, L.ecard.h, a[2], a[3] * 0.9);
      strokeRR(r.x, r.y, r.w, r.h, 6, "rgb(70,82,112)", 1);
    }
    ctx.restore();
  },

  drawControls() {
    const L = this.view.layout, acc = this.acc, last = this.events.length - 1, by = L.barY;
    fillRR(12, by, W - 24, 6, 3, css(COL.panelL));
    const frac = (this.evI + Math.min(1, this.evT / this.ev.dur)) / Math.max(1, last + 1);
    fillRR(12, by, Math.max(6, (W - 24) * frac), 6, 3, css(acc));
    for (const b of this.buttons) {
      const hot = inRect(mouse, b);
      fillRR(b.x, b.y, b.w, b.h, 10, b.active ? css(acc) : hot ? "rgb(52,64,92)" : css(COL.panelL));
      T(b.label, b.x + b.w / 2, b.y + b.h / 2, { s: b.label.length > 11 ? 14 : 16, b: 1, c: b.active ? [10, 22, 30] : COL.text, a: "center", v: "middle" });
    }
    T(`x${SPEEDS[this.speedI]}`, this.speedX, L.btnY + 20, { s: 17, b: 1, c: acc, v: "middle" });
    T("Bài mẫu:", this.presetLabelX, L.btnY + 20, { s: 14, c: COL.muted, a: "right", v: "middle" });
  },

  pointerDown(m) {
    const V = this.view, L = V.layout;
    if (V.editor.active) { V.editor.click(m, this); return; }
    for (const b of this.buttons) if (inRect(m, b)) { this.press(b.key); return; }
    for (const k of this.keys) if (inRect(m, this.swRects[k])) { this.press("alg_" + k); return; }
    if (m.y >= L.barY - 6 && m.y <= L.barY + 10 && m.x >= 12 && m.x <= W - 12) this.seek(Math.floor((m.x - 12) / (W - 24) * this.events.length));
    else if (V.pointerDown) V.pointerDown(m, this);
  },
  keyDown(e) {
    const V = this.view;
    if (V.editor.active) { V.editor.key(e, this); return; }
    const k = e.key, map = Object.assign({ " ": "play", ArrowRight: "next", ArrowLeft: "back", n: "node", r: "reset", ArrowUp: "fast", ArrowDown: "slow", g: "rand", t: "edit", 1: "p0", 2: "p1", 3: "p2", 4: "p3" }, V.keys || {});
    this.keys.forEach(a => { map[this.algos[a].name[0].toLowerCase()] = "alg_" + a; });
    if (map[k]) { e.preventDefault(); this.press(map[k]); }
  },
};

function pointer(e) { mouse.x = (e.clientX - offX) / scale; mouse.y = (e.clientY - offY) / scale; return mouse; }
window.addEventListener("pointermove", e => { if (e.target && e.target.id === "c") pointer(e); });
window.addEventListener("pointerdown", e => { if (e.target && e.target.id === "c" && E.view && E.events) E.pointerDown(pointer(e)); });
window.addEventListener("keydown", e => { if (E.view && E.events) E.keyDown(e); });
window.addEventListener("resize", () => { if (cv) resize(); });
