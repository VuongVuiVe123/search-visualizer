"use strict";

/* View của bài 8-puzzle: CHỈ VẼ bàn cờ 3x3 trượt ô, thẻ trạng thái, hộp thoại tự đặt.
   Trạng thái đầu, đích và các bài mẫu khai báo ở problems/puzzle8.py (Python),
   tệp này đọc chúng qua View.problem (nạp lúc khởi động trong engine.js).
   Trạng thái từ Python là bàn 3x3 [[1,2,3],[4,0,6],[7,5,8]]; để vẽ thì trải phẳng thành 9 ô. */

const flat = state => state.flat();                                  // [[1,2,3],...] -> [1,2,3,...]
const grid = a => [a.slice(0, 3), a.slice(3, 6), a.slice(6, 9)];      // ngược lại
const TILE = { 1: [239, 122, 122], 2: [240, 170, 110], 3: [240, 214, 110], 4: [150, 215, 120], 5: [100, 210, 190], 6: [100, 170, 240], 7: [150, 130, 240], 8: [210, 130, 220] };

class BigBoard {
  constructor(x, y, size = 132) {
    this.x = x; this.y = y; this.size = size; this.ts = Math.floor((size - 16) / 3) - 2;
    this.state = null; this.pos = {}; this.alpha = 1;
  }
  slot(i) { const r = Math.floor(i / 3), c = i % 3, st = this.ts + 4; return [8 + c * st, 8 + r * st]; }
  setState(state, from) {
    state = flat(state);
    this.state = state;
    if (from) for (const v in from.pos) this.pos[v] = from.pos[v].slice();
    state.forEach((v, i) => { if (v && !this.pos[v]) this.pos[v] = this.slot(i); });
  }
  update(dt) {
    if (!this.state) return;
    this.state.forEach((v, i) => {
      if (!v) return;
      const [tx, ty] = this.slot(i), p = this.pos[v];
      p[0] = sm(p[0], tx, 10, dt); p[1] = sm(p[1], ty, 10, dt);
    });
  }
  get cx() { return this.x + this.size / 2; }
  get cy() { return this.y + this.size / 2; }
  draw(border, alpha = 1) {
    ctx.save(); ctx.globalAlpha = alpha; ctx.translate(this.x, this.y);
    fillRR(0, 0, this.size, this.size, 12, "rgb(24,30,48)");
    for (let i = 0; i < 9; i++) { const [sx, sy] = this.slot(i); fillRR(sx, sy, this.ts, this.ts, 8, "rgb(14,18,30)"); }
    if (this.state) {
      this.state.forEach((v, i) => {
        if (!v) return;
        const [px, py] = this.pos[v], [tx, ty] = this.slot(i);
        const mv = Math.min(1, Math.hypot(px - tx, py - ty) / 20);
        if (mv > 0.05) fillRR(px + 2, py + 5, this.ts, this.ts, 8, "rgba(0,0,0,0.35)");
        fillRR(px, py - 2 * mv, this.ts, this.ts, 8, css(TILE[v]));
        T(String(v), px + this.ts / 2, py + this.ts / 2 - 2 * mv, { s: 26, b: 1, c: [26, 26, 40], a: "center", v: "middle" });
      });
    }
    strokeRR(0, 0, this.size, this.size, 12, css(border), 3);
    ctx.restore();
  }
}

function drawMiniBoard(g, pw, ph, state) {
  const rad = (x, y, w, h, r) => { g.beginPath(); g.roundRect ? g.roundRect(x, y, w, h, r) : g.rect(x, y, w, h); };
  g.fillStyle = "rgb(26,33,52)"; rad(0, 0, pw, pw, Math.max(4, pw / 7)); g.fill();
  const pad = Math.max(2, pw / 12), gap = Math.max(1, pw / 26), ts = (pw - 2 * pad - 2 * gap) / 3;
  g.textAlign = "center"; g.textBaseline = "middle"; g.font = `bold ${Math.max(8, ts * 0.78)}px ${SANS}`;
  flat(state).forEach((v, i) => {
    const r = Math.floor(i / 3), c = i % 3, x = pad + c * (ts + gap), y = pad + r * (ts + gap);
    g.fillStyle = v ? css(TILE[v]) : "rgb(12,16,26)"; rad(x, y, ts, ts, 3); g.fill();
    if (v) { g.fillStyle = "rgb(26,26,40)"; g.fillText(String(v), x + ts / 2, y + ts / 2 + ts * 0.04); }
  });
}

const MOD = { x: 350, y: 200, w: 700, h: 500 };

const View = {
  id: "puzzle8", pythonBase: "../../", problem: null,
  layout: {
    W: 1400, H: 900, lh: 20,
    code: { x: 12, y: 92, w: 528, h: 540 }, tab: { x: 552, y: 92, w: 468, h: 540 },
    qy: 644, ey: 752, barY: 832, btnY: 846, presetX: 800,
    qx: 150, qp: 60, qmax: 20, qcard: { w: 46, h: 46 }, ecard: { w: 52, h: 52 }, estep: 58, emax: 20,
    cell: { w: 50, h: 50, gap: 6 },
  },
  tableTitle: "bảng trạng thái theo độ sâu  (mỗi ô = một nút)",
  nodeBoard: new BigBoard(1032 + 356 / 2 - 66, 92 + 56),
  childBoard: new BigBoard(1032 + 356 / 2 - 66, 92 + 56 + 132 + 68),
  lastChildKey: null,

  get goal() { return this.problem.goal.slice(); },
  presets(algo) { const ps = this.problem.presets; return ps[algo] || ps[Object.keys(ps)[0]]; },
  randomPuzzle(E) { return PY.random("puzzle8", E.algo, this.goal); },
  subtitle() { return "8-puzzle · mỗi dòng code chạy, hình tương ứng sáng lên"; },
  anchors() { return { child: [this.childBoard.cx, this.childBoard.cy], node: [this.nodeBoard.cx, this.nodeBoard.cy] }; },
  drawCard(state, cx, cy, w, h, sc, al) { return drawCached("p8:" + sk(state), w, h, (g, pw, ph) => drawMiniBoard(g, pw, ph, state), cx, cy, sc, al); },
  drawGoal(xr, E) {
    T("Đích", xr - 54, 38, { s: 14, b: 1, c: COL.green, a: "right", v: "middle" });
    this.drawCard(E.goal, xr - 26, 38, 46, 46, 1, 1);
  },

  onLoad() {
    this.nodeBoard.state = null; this.nodeBoard.pos = {};
    this.childBoard.state = null; this.childBoard.pos = {}; this.childBoard.alpha = 0;
    this.lastChildKey = null; this.syncBoards(E.ev, true);
  },
  syncBoards(ev, snap) {
    const nb = this.nodeBoard, cb = this.childBoard;
    if (!nb.state || sk(nb.state) !== sk(ev.nodeState)) nb.setState(ev.nodeState);
    const ch = ev.child, ck = ch ? ch.key : null;
    if (ch && ck !== this.lastChildKey) { cb.state = null; cb.pos = {}; cb.setState(ch.state, nb); }
    this.lastChildKey = ck;
    if (snap) for (const b of [nb, cb]) if (b.state) b.state.forEach((v, i) => { if (v) b.pos[v] = b.slot(i); });
  },
  update(dt, ev) {
    this.syncBoards(ev);
    this.nodeBoard.update(dt); this.childBoard.update(dt);
    this.childBoard.alpha = sm(this.childBoard.alpha, ev.child ? 1 : 0.18, 8, dt);
  },

  drawMain(ev, p, E) {
    const r = { x: 1032, y: 92, w: 356, h: 540 }, nb = this.nodeBoard, cb = this.childBoard, vb = ev.verdict;
    panel(r, "nút đang xét", COL.orange);
    T("node", nb.x - 2, nb.y - 20, { s: 15, b: 1, c: COL.orange });
    T(`độ sâu ${ev.nodeDepth}`, nb.x + nb.size + 2, nb.y - 19, { s: 14, c: COL.muted, a: "right" });
    nb.draw(COL.orange);
    if (ev.act) {
      const cx = r.x + r.w / 2, y = nb.y + nb.size + 12;
      fillRR(cx - 74, y, 148, 30, 15, css(shade(E.acc, 0.3))); strokeRR(cx - 74, y, 148, 30, 15, css(E.acc), 2);
      const g = { "Lên": "↑", "Xuống": "↓", "Trái": "←", "Phải": "→" }[ev.act];
      T(`${g}  ${ev.act}`, cx, y + 15, { s: 18, b: 1, c: E.acc, a: "center", v: "middle" });
    }
    const border = { null: COL.cyan, ok: COL.green, dup: COL.red, goal: COL.gold, queued: COL.green }[vb];
    T("child", cb.x - 2, cb.y - 20, { s: 15, b: 1, c: border });
    cb.draw(border, cb.alpha);
    if (vb === "dup" && ev.child) { ctx.fillStyle = `rgba(255,98,112,${0.27 * (0.5 + 0.5 * Math.sin(p * 12))})`; ctx.fillRect(cb.x, cb.y, cb.size, cb.size); }
    E.drawVerdict(r, cb.y + cb.size + 12, ev);
  },

  /* ---------- hộp thoại tự đặt trạng thái đầu / đích ---------- */
  editor: {
    active: false, ed: null,
    open(E) { this.active = true; E.playing = false; this.ed = { init: flat(E.rec.init), goal: flat(E.goal), sel: null }; this.check(E); },
    cell(which, i) {
      const size = 3 * 70 + 2 * 6, bx = which === "init" ? MOD.x + 56 : MOD.x + MOD.w - 56 - size;
      return { x: bx + (i % 3) * 76, y: MOD.y + 96 + Math.floor(i / 3) * 76, w: 70, h: 70 };
    },
    buttons() {
      return [
        { x: MOD.x + 56, y: MOD.y + 330, w: 222, h: 36, label: "Xáo ngẫu nhiên", key: "shuffle" },
        { x: MOD.x + MOD.w - 56 - 222, y: MOD.y + 330, w: 222, h: 36, label: "Đích chuẩn 1-8", key: "std" },
        { x: MOD.x + MOD.w - 56 - 230, y: MOD.y + MOD.h - 62, w: 110, h: 42, label: "Hủy", key: "cancel" },
        { x: MOD.x + MOD.w - 56 - 112, y: MOD.y + MOD.h - 62, w: 112, h: 42, label: "Áp dụng", key: "apply", primary: true },
      ];
    },
    check(E) {
      const ed = this.ed, al = E.algos[E.algo], nm = al.name;
      if (!PY.solvable("puzzle8", grid(ed.init), grid(ed.goal))) { ed.ok = false; ed.col = COL.red; ed.msg = "Không giải được: hai bàn cờ khác tính chẵn lẻ. Hãy đổi chỗ thêm một cặp ô."; return; }
      const st = E.quick(grid(ed.init), grid(ed.goal));
      if (!st) { ed.ok = false; ed.col = COL.orange; ed.msg = `Giải được nhưng quá lớn: ${nm} phải mở hơn ${al.limit} nút, khó theo dõi. Hãy đặt gần đích hơn.`; }
      else if (st[0] === 0) { ed.ok = true; ed.col = COL.green; ed.msg = "Trạng thái đầu đã bằng đích: 0 bước."; }
      else { ed.ok = true; ed.col = COL.green; ed.msg = `${nm} tìm được lời giải ${st[0]} bước, mở ${st[1]} nút.`; }
    },
    press(key, E) {
      const ed = this.ed;
      if (key === "cancel") this.active = false;
      else if (key === "apply") { if (ed.ok) { this.active = false; E.preset = -1; E.load(grid(ed.init), grid(ed.goal)); } }
      else if (key === "std") { ed.goal = flat(View.goal); ed.sel = null; this.check(E); }
      else if (key === "shuffle") { ed.init = flat(PY.random("puzzle8", E.algo, grid(ed.goal))[0]); ed.sel = null; this.check(E); }
    },
    click(m, E) {
      for (const b of this.buttons()) if (inRect(m, b)) { this.press(b.key, E); return; }
      const ed = this.ed;
      for (const which of ["init", "goal"]) {
        for (let i = 0; i < 9; i++) if (inRect(m, this.cell(which, i))) {
          const sel = ed.sel;
          if (!sel || sel[0] !== which) ed.sel = [which, i];
          else if (sel[1] === i) ed.sel = null;
          else { const a = ed[which];[a[sel[1]], a[i]] = [a[i], a[sel[1]]]; ed.sel = null; this.check(E); }
          return;
        }
      }
      if (!inRect(m, MOD)) ed.sel = null;
    },
    key(e, E) {
      if (e.key === "Escape") this.active = false;
      else if (e.key === "Enter" && this.ed.ok) this.press("apply", E);
    },
    draw(E) {
      ctx.fillStyle = "rgba(4,6,12,0.76)"; ctx.fillRect(0, 0, W, H);
      const ed = this.ed;
      fillRR(MOD.x, MOD.y, MOD.w, MOD.h, 18, "rgb(22,29,46)"); strokeRR(MOD.x, MOD.y, MOD.w, MOD.h, 18, css(E.acc), 2);
      T("Tự đặt trạng thái", MOD.x + 28, MOD.y + 18, { s: 22, b: 1 });
      T("Bấm một ô rồi bấm ô thứ hai (cùng bàn cờ) để đổi chỗ hai ô.", MOD.x + 28, MOD.y + 46, { s: 13, c: COL.muted });
      for (const [which, title, col] of [["init", "Trạng thái đầu", COL.orange], ["goal", "Trạng thái đích", COL.green]]) {
        const c0 = this.cell(which, 0);
        T(title, c0.x, c0.y - 30, { s: 16, b: 1, c: col });
        fillRR(c0.x - 8, c0.y - 8, 238, 238, 12, "rgb(14,18,30)");
        ed[which].forEach((v, i) => {
          const r = this.cell(which, i);
          if (v) { fillRR(r.x, r.y, r.w, r.h, 10, css(TILE[v])); T(String(v), r.x + 35, r.y + 35, { s: 30, b: 1, c: [26, 26, 40], a: "center", v: "middle" }); }
          else { fillRR(r.x, r.y, r.w, r.h, 10, "rgb(30,38,58)"); T("trống", r.x + 35, r.y + 35, { s: 13, c: COL.muted, a: "center", v: "middle" }); }
          if (ed.sel && ed.sel[0] === which && ed.sel[1] === i) strokeRR(r.x - 2, r.y - 2, r.w + 4, r.h + 4, 12, css(COL.cyan), 4);
        });
      }
      T("→", MOD.x + MOD.w / 2, MOD.y + 207, { s: 40, b: 1, c: COL.muted, a: "center", v: "middle" });
      fillRR(MOD.x + 56, MOD.y + 386, MOD.w - 112, 40, 10, css(shade(ed.col, 0.22))); strokeRR(MOD.x + 56, MOD.y + 386, MOD.w - 112, 40, 10, css(ed.col), 2);
      wrapText(ed.msg, 15, MOD.w - 136).slice(0, 2).forEach((l, k) => T(l, MOD.x + 68, MOD.y + 390 + k * 17, { s: 15, c: ed.col }));
      for (const b of this.buttons()) {
        const on = b.primary && ed.ok, hot = inRect(mouse, b);
        fillRR(b.x, b.y, b.w, b.h, 10, on ? css(E.acc) : hot ? "rgb(52,64,92)" : css(COL.panelL));
        T(b.label, b.x + b.w / 2, b.y + b.h / 2, { s: 16, b: 1, c: on ? [10, 22, 30] : COL.text, a: "center", v: "middle" });
      }
    },
  },
};

E.start(View);
