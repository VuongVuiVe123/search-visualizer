import ctypes
import math
import os
import re
import sys

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pygame

W, H = 1400, 900

BG = (13, 17, 27)
PANEL = (20, 26, 40)
PANEL_L = (34, 43, 64)
TEXT = (228, 234, 246)
MUTED = (126, 140, 166)
CYAN = (86, 214, 230)
BLUE = (100, 156, 255)
ORANGE = (255, 170, 70)
RED = (255, 98, 112)
GREEN = (104, 224, 150)
GOLD = (255, 214, 90)
TILE_COL = {1: (239, 122, 122), 2: (240, 170, 110), 3: (240, 214, 110), 4: (150, 215, 120),
            5: (100, 210, 190), 6: (100, 170, 240), 7: (150, 130, 240), 8: (210, 130, 220)}

ACC_NOW = (86, 214, 230)
TOKEN = re.compile(r"(?P<kw>\b(?:def|if|for|while|not|in|return|and)\b)|(?P<fn>\b[A-Za-z_]\w*(?=\())|"
                   r"(?P<lit>\b(?:False|True|None)\b)")


# =====================================================================
# Lấy thuật toán, bài toán và bộ ghi từ các thư mục chung của dự án.
# Tệp này CHỈ VẼ, không tự viết lại thuật toán:
#   core/algorithms/   BFS, DFS
#   problems/puzzle8.py  trạng thái đầu, đích, bài mẫu, actions, result
#   tracing/           ghi lại từng dòng code đang chạy để vẽ
# =====================================================================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from problems import puzzle8  # noqa: E402
from tracing.algorithm_info import ALGORITHM_INFO  # noqa: E402
from tracing.stats import quick, random_initial  # noqa: E402
from tracing.tracer import Recording, algorithm_code, take_line  # noqa: E402

GOAL = puzzle8.GOAL_STATE
PRESETS = puzzle8.PRESETS["bfs"]            # mỗi thuật toán có bộ bài mẫu riêng: puzzle8.PRESETS[<thuật toán>]
CODE_BY = {k: algorithm_code(k)[0] for k in ALGORITHM_INFO}
ALGO_COL = {k: v["color"] for k, v in ALGORITHM_INFO.items()}
ALGO_INFO = {k: (v["name"], v["l1"], v["l2"], v["full"]) for k, v in ALGORITHM_INFO.items()}
LIMIT = {k: v["limit"] for k, v in ALGORITHM_INFO.items()}
solvable = puzzle8.solvable


def flat(state):
    """Bàn 3x3 ((1, 2, 3), ...) -> 9 ô (1, 2, 3, ...) để vẽ."""
    return tuple(v for row in state for v in row)


def grid(cells):
    """Ngược lại với flat: 9 ô -> bàn 3x3."""
    cells = tuple(cells)
    return (cells[0:3], cells[3:6], cells[6:9])


def quick_stats(init, goal, algo="bfs"):
    """(số bước, số nút đã mở) hoặc None nếu bài quá lớn để trình chiếu."""
    return quick(algo, puzzle8.make_problem(init, goal))


def Rec(init, goal, algo):
    """Chạy thuật toán thật và ghi lại từng dòng (xem tracing/tracer.py)."""
    return Recording(algo, "puzzle8", puzzle8.make_problem(init, goal))


def sm(v, t, k, dt):
    return v + (t - v) * (1 - math.exp(-k * dt))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


SC = 1.0


def _p(a):
    return (a[0] * SC, a[1] * SC)


def _r(r):
    x, y, w, h = r
    return pygame.Rect(round(x * SC), round(y * SC), max(1, round(w * SC)), max(1, round(h * SC)))


def _w(w):
    return 0 if w == 0 else max(1, round(w * SC))


class _G:

    def rect(self, s, c, r, w=0, border_radius=0):
        pygame.draw.rect(s, c, _r(r), _w(w), border_radius=round(border_radius * SC))

    def line(self, s, c, a, b, w=1):
        pygame.draw.line(s, c, _p(a), _p(b), _w(w) or 1)

    def lines(self, s, c, closed, pts, w=1):
        pygame.draw.lines(s, c, closed, [_p(q) for q in pts], _w(w) or 1)

    def circle(self, s, c, center, radius, w=0):
        pygame.draw.circle(s, c, _p(center), max(1, round(radius * SC)), _w(w))

    def polygon(self, s, c, pts, w=0):
        pygame.draw.polygon(s, c, [_p(q) for q in pts], _w(w))


G = _G()
FONTS = {}


def font(name, size, bold=False):
    px = max(6, round(size * SC))
    key = (name, px, bold)
    if key not in FONTS:
        FONTS[key] = pygame.font.SysFont(name, px, bold=bold)
    return FONTS[key]


def pfont(name, px, bold=False):
    key = (name, px, bold)
    if key not in FONTS:
        FONTS[key] = pygame.font.SysFont(name, px, bold=bold)
    return FONTS[key]


def tw(f, s):
    return f.size(s)[0] / SC


MINI = {}


def mini_surface(state, size):
    ps = max(6, round(size * SC))
    key = (state, ps)
    if key in MINI:
        return MINI[key]
    s = pygame.Surface((ps, ps), pygame.SRCALPHA)
    pygame.draw.rect(s, (26, 33, 52), (0, 0, ps, ps), border_radius=max(4, ps // 7))
    pad, gap = max(2, ps // 12), max(1, ps // 26)
    ts = (ps - 2 * pad - 2 * gap) // 3
    f = pfont("segoeui", max(8, int(ts * 0.78)), True)
    for i, v in enumerate(flat(state)):
        r, c = divmod(i, 3)
        rect = pygame.Rect(pad + c * (ts + gap), pad + r * (ts + gap), ts, ts)
        if v == 0:
            pygame.draw.rect(s, (12, 16, 26), rect, border_radius=3)
        else:
            pygame.draw.rect(s, TILE_COL[v], rect, border_radius=3)
            t = f.render(str(v), True, (26, 26, 40))
            s.blit(t, t.get_rect(center=rect.center))
    MINI[key] = s
    return s


def blit_mini(dst, state, cx, cy, size, scale=1.0, alpha=1.0):
    img = mini_surface(state, size)
    owned = False
    if abs(scale - 1) > 0.02:
        n = max(2, int(img.get_width() * scale))
        img = pygame.transform.smoothscale(img, (n, n))
        owned = True
    if alpha < 0.98:
        if not owned:
            img = img.copy()
        img.set_alpha(int(255 * max(0, alpha)))
    dst.blit(img, img.get_rect(center=(round(cx * SC), round(cy * SC))))
    half = size * (scale if owned else 1.0) / 2
    return pygame.Rect(round(cx - half), round(cy - half), round(half * 2), round(half * 2))


def text(dst, s, f, col, pos, anchor="topleft", alpha=1.0):
    t = f.render(s, True, col)
    if alpha < 0.98:
        t.set_alpha(int(255 * max(0, alpha)))
    r = t.get_rect(**{anchor: (round(pos[0] * SC), round(pos[1] * SC))})
    dst.blit(t, r)


def wrap(s, f, width):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.size(t)[0] <= width * SC:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def setclip(dst, rect):
    dst.set_clip(_r(rect))


def panel(dst, rect, title=None, accent=CYAN):
    G.rect(dst, PANEL, rect, border_radius=14)
    G.rect(dst, PANEL_L, rect, 1, border_radius=14)
    if title:
        text(dst, title, font("segoeui", 15, True), accent, (rect.x + 14, rect.y + 10))


class Button:
    def __init__(self, rect, label, key):
        self.rect, self.label, self.key = pygame.Rect(rect), label, key
        self.active = False

    def draw(self, dst, mouse):
        hot = self.rect.collidepoint(mouse)
        col = ACC_NOW if self.active else ((52, 64, 92) if hot else PANEL_L)
        G.rect(dst, col, self.rect, border_radius=10)
        t = font("segoeui", 16, True).render(self.label, True, (10, 22, 30) if self.active else TEXT)
        dst.blit(t, t.get_rect(center=(round(self.rect.centerx * SC), round(self.rect.centery * SC))))


class BigBoard:

    def __init__(self, x, y, size=132):
        self.x, self.y, self.size = x, y, size
        self.ts = (size - 8 * 2) // 3 - 2
        self.state = None
        self.pos = {}
        self.alpha = 1.0

    def slot(self, i):
        r, c = divmod(i, 3)
        step = self.ts + 4
        return 8 + c * step, 8 + r * step

    def set_state(self, state, copy_from=None):
        state = flat(state)
        self.state = state
        if copy_from is not None:
            for v, p in copy_from.pos.items():
                self.pos[v] = list(p)
        for i, v in enumerate(state):
            if v and v not in self.pos:
                self.pos[v] = list(self.slot(i))

    def update(self, dt):
        if not self.state:
            return
        for i, v in enumerate(self.state):
            if v:
                tx, ty = self.slot(i)
                p = self.pos[v]
                p[0], p[1] = sm(p[0], tx, 10, dt), sm(p[1], ty, 10, dt)

    def draw(self, dst, border, alpha=1.0):
        s = pygame.Surface((round(self.size * SC), round(self.size * SC)), pygame.SRCALPHA)
        G.rect(s, (24, 30, 48), (0, 0, self.size, self.size), border_radius=12)
        for i in range(9):
            sx, sy = self.slot(i)
            G.rect(s, (14, 18, 30), (sx, sy, self.ts, self.ts), border_radius=8)
        if self.state:
            f = font("segoeui", 26, True)
            for i, v in enumerate(self.state):
                if not v:
                    continue
                px, py = self.pos[v]
                tx, ty = self.slot(i)
                moving = min(1.0, math.hypot(px - tx, py - ty) / 20)
                if moving > 0.05:
                    G.rect(s, (0, 0, 0, 90), (px + 2, py + 5, self.ts, self.ts), border_radius=8)
                G.rect(s, TILE_COL[v], (px, py - 2 * moving, self.ts, self.ts), border_radius=8)
                t = f.render(str(v), True, (26, 26, 40))
                s.blit(t, t.get_rect(center=(round((px + self.ts / 2) * SC), round((py + self.ts / 2 - 2 * moving) * SC))))
        G.rect(s, border, (0, 0, self.size, self.size), 3, border_radius=12)
        if alpha < 0.98:
            s.set_alpha(int(255 * alpha))
        dst.blit(s, (round(self.x * SC), round(self.y * SC)))

    @property
    def center(self):
        return (self.x + self.size / 2, self.y + self.size / 2)


CODE_X, CODE_Y, CODE_W, CODE_H = 12, 92, 528, 540
TAB = pygame.Rect(552, 92, 468, 540)
RIGHT = pygame.Rect(1032, 92, 356, 540)
CELL, GAPC = 50, 6
LH = 20
Q_Y, E_Y = 644, 752
SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16]


class App:
    def __init__(self):
        pygame.init()
        info = pygame.display.get_desktop_sizes()[0]
        sc = 0.82 * min((info[0] - 40) / W, (info[1] - 110) / H)
        self.win = pygame.display.set_mode((int(W * sc), int(H * sc)), pygame.RESIZABLE)
        pygame.display.set_caption("BFS 8-puzzle - trực quan hóa từng dòng code")
        self.canvas = None
        self.fullscreen, self.win_size = False, self.win.get_size()
        self.clock = pygame.time.Clock()
        self.speed_i = 2
        self.preset = 1
        self.algo = "bfs"
        self.toast = ("", 0.0)
        self.apply_scale()
        self.node_board = BigBoard(RIGHT.centerx - 66, RIGHT.y + 56)
        self.child_board = BigBoard(RIGHT.centerx - 66, RIGHT.y + 56 + 132 + 68)
        bx = 12
        self.buttons = []
        for w, label, key in [(80, "Về đầu", "reset"), (70, "Lùi", "back"), (96, "Phát", "play"),
                              (70, "Tiếp", "next"), (100, "Node kế", "node"),
                              (38, "−", "slow"), (38, "+", "fast")]:
            self.buttons.append(Button((bx, 846, w, 40), label, key))
            bx += w + 8
            if key == "slow":
                bx += 56
        self.speed_x = [b for b in self.buttons if b.key == "slow"][0].rect.right + 6
        bx = 690
        for i, (lab, _) in enumerate(PRESETS):
            self.buttons.append(Button((bx, 846, 84, 40), lab, f"p{i}"))
            bx += 92
        self.buttons.append(Button((bx, 846, 104, 40), "Tự đặt", "edit"))
        self.buttons.append(Button((bx + 112, 846, 128, 40), "Ngẫu nhiên", "rand"))
        self.buttons.append(Button((bx + 248, 846, 140, 40), "Chạy lời giải", "replay"))
        self.replay = None
        self.layout_switch(472)
        self.acc = list(ALGO_COL[self.algo])
        self.sw_x = float(self.algo_rects[self.algo].x)
        self.cap_text, self.cap_age = "", 0.0
        self.editing = False
        self.goal = GOAL
        self.load(self.presets[self.preset][1])

    def apply_scale(self):
        global SC
        ww, wh = self.win.get_size()
        sc = max(0.3, min(ww / W, wh / H))
        if self.canvas is not None and abs(sc - SC) < 0.003 and self.canvas.get_size() == (round(W * SC), round(H * SC)):
            return
        SC = sc
        self.canvas = pygame.Surface((round(W * SC), round(H * SC)))
        MINI.clear()
        self.build_code()

    def build_code(self):
        self.lines = []
        f = self.code_font(14, CODE_W - 60)
        for line in CODE_BY[self.algo]:
            lead = len(line) - len(line.lstrip())
            line = " " * (lead // 2) + line.lstrip()
            segs, pos = [], 0
            for m in TOKEN.finditer(line):
                if m.start() > pos:
                    segs.append((line[pos:m.start()], (214, 222, 240)))
                col = {"kw": (255, 130, 170), "fn": (110, 200, 255), "lit": (255, 190, 110)}[m.lastgroup]
                segs.append((m.group(), col))
                pos = m.end()
            if pos < len(line):
                segs.append((line[pos:], (214, 222, 240)))
            bright = pygame.Surface((round((CODE_W - 60) * SC), round(24 * SC)), pygame.SRCALPHA)
            dim = pygame.Surface((round((CODE_W - 60) * SC), round(24 * SC)), pygame.SRCALPHA)
            x = 0
            for s, col in segs:
                bright.blit(f.render(s, True, col), (x, round(2 * SC)))
                dim.blit(f.render(s, True, shade(col, 0.5)), (x, round(2 * SC)))
                x += f.size(s)[0]
            self.lines.append((bright, dim))
        self.bar_y = getattr(self, 'bar_y', CODE_Y + 36.0)

    @property
    def presets(self):
        return puzzle8.PRESETS.get(self.algo, PRESETS)

    # ---------- dùng chung cho mọi thuật toán (BFS, DFS, UCS, ...) ----------
    def layout_switch(self, x0_wide):
        """Công tắc chọn thuật toán: 2 thẻ thì rộng, từ 3 thẻ trở lên thì thu gọn chữ."""
        keys = list(ALGORITHM_INFO)
        n, wide = len(keys), len(keys) <= 2
        x0, total = (x0_wide, 436) if wide else (x0_wide - 42, 478)
        cw = (total - (n - 1) * 8) // n
        self.algo_rects = {k: pygame.Rect(x0 + i * (cw + 8), 16, cw, 52) for i, k in enumerate(keys)}
        self.sw_style = dict(x0=x0, total=total, name_x=18 if wide else 12, name_s=26 if wide else 22,
                             lx=90 if wide else 64, l2_s=12 if wide else 11)

    def info(self):
        return ALGORITHM_INFO[self.algo]

    def code_font(self, size, avail):
        """Cỡ chữ khung code: thu nhỏ dần (tối thiểu 10) nếu dòng dài nhất không vừa khung."""
        shown = [" " * ((len(ln) - len(ln.lstrip())) // 2) + ln.lstrip() for ln in CODE_BY[self.algo]]
        while size > 10 and max(tw(font("consolas", size), ln) for ln in shown) > avail:
            size -= 1
        return font("consolas", size)

    def cost_badge(self, s, r, g):
        """Huy hiệu nhỏ ghi chi phí g ở góc trên bên phải một thẻ (chỉ với thuật toán có chi phí, vd. UCS)."""
        if not self.info()["cost"] or g is None:
            return
        f = font("segoeui", 11, True)
        w = max(17, tw(f, str(g)) + 9)
        box = pygame.Rect(round(r.right - w + 5), round(r.y - 7), round(w), 15)
        G.rect(s, tuple(int(v) for v in self.acc), box, border_radius=7)
        text(s, str(g), f, (16, 14, 30), box.center, "center")

    def queued_msg(self):
        kind = self.info()["frontier"]
        return {"stack": "Vào ngăn xếp", "priority": "Vào hàng đợi ưu tiên"}.get(kind, "Vào hàng đợi")


    def load(self, init, goal=GOAL):
        self.replay = None
        self.goal = goal
        self.rec = Rec(init, goal, self.algo)
        self.events = self.rec.events
        self.ev_i, self.ev_t = 0, 0.0
        self.playing, self.one = False, False
        self.anim_tab, self.anim_q, self.anim_e = {}, {}, {}
        self.scroll = 0.0
        self.lamps = [[70, 80, 100], [70, 80, 100]]
        self.banner_key, self.banner_age = None, 1.0
        self.last_child_key = None
        self.node_board.state, self.node_board.pos = None, {}
        self.child_board.state, self.child_board.pos = None, {}
        self.child_board.alpha = 0.0
        self.layout_tn = -1
        self.sync_boards(snap=True)

    @property
    def ev(self):
        return self.events[self.ev_i]

    def speed(self):
        return SPEEDS[self.speed_i]

    def seek(self, i):
        self.ev_i = max(0, min(len(self.events) - 1, i))
        self.ev_t = 0.0
        self.one = False

    def press(self, key):
        last = len(self.events) - 1
        if key == "play":
            if self.ev_i >= last:
                self.seek(0)
            self.playing = not self.playing
        elif key == "next":
            self.playing = False
            if self.ev_i < last:
                self.ev_i += 1
                self.ev_t, self.one = 0.0, True
        elif key == "back":
            self.playing = False
            self.seek(self.ev_i - 1)
        elif key == "node":
            j = self.ev_i + 1
            while j < last and self.events[j]["line"] != take_line(self.algo):
                j += 1
            self.ev_i, self.ev_t, self.one = min(j, last), 0.0, True
        elif key == "reset":
            self.playing = False
            self.seek(0)
        elif key == "slow":
            self.speed_i = max(0, self.speed_i - 1)
        elif key == "fast":
            self.speed_i = min(len(SPEEDS) - 1, self.speed_i + 1)
        elif key.startswith("alg_") and key[4:] in ALGORITHM_INFO:
            self.set_algo(key[4:])
        elif key.startswith("p"):
            self.preset = int(key[1:])
            self.load(self.presets[self.preset][1])
        elif key == "rand":
            s, _ = random_initial("puzzle8", self.algo, self.goal)
            self.preset = -1
            self.load(s, self.goal)
        elif key == "edit":
            self.open_editor()
        elif key == "replay":
            self.start_replay()

    def start_replay(self):
        """Chạy lời giải: bàn cờ lớn trượt lần lượt từng nước từ trạng thái đầu tới đích."""
        if self.replay:
            self.replay = None
            return
        if not self.rec.solution:
            self.toast = ("Chưa có lời giải để chạy.", 3.0)
            return
        self.playing = False
        self.seek(len(self.events) - 1)
        self.replay = dict(states=[self.rec.nodes[e]["state"] for e in self.rec.path], t=0.0, step=0.8, k=-1)

    def update_replay(self, dt):
        rp, nb = self.replay, self.node_board
        last = len(rp["states"]) - 1
        rp["t"] += dt * min(8.0, max(1.0, self.speed()))
        k = min(last, int(rp["t"] / rp["step"]))
        if k != rp["k"]:
            if rp["k"] < 0:
                nb.state, nb.pos = None, {}
                nb.set_state(rp["states"][0])
                for i, v in enumerate(nb.state):
                    if v:
                        nb.pos[v] = list(nb.slot(i))
            else:
                nb.set_state(rp["states"][k])
            rp["k"] = k
        if k >= last and rp["t"] > last * rp["step"] + 1.6:
            self.replay = None

    def set_algo(self, algo):
        if algo == self.algo:
            return
        init, goal = self.rec.init, self.goal
        self.playing = False
        self.algo = algo
        pygame.display.set_caption(f"{algo.upper()} 8-puzzle - trực quan hóa từng dòng code")
        self.build_code()
        if quick_stats(init, goal, algo) is not None:
            self.load(init, goal)
        else:
            self.preset = 1
            self.load(self.presets[1][1])
            self.toast = (f"Bài đang đặt quá lớn với {algo.upper()} (phải mở hơn {LIMIT[algo]} nút) → chuyển sang bài mẫu.", 3.5)

    MOD = pygame.Rect(350, 170, 700, 500)
    ED_CELL, ED_GAP = 70, 6

    def ed_cell(self, which, i):
        size = 3 * self.ED_CELL + 2 * self.ED_GAP
        bx = self.MOD.x + 56 if which == "init" else self.MOD.right - 56 - size
        r, c = divmod(i, 3)
        return pygame.Rect(bx + c * (self.ED_CELL + self.ED_GAP), self.MOD.y + 96 + r * (self.ED_CELL + self.ED_GAP),
                           self.ED_CELL, self.ED_CELL)

    def open_editor(self):
        self.replay = None
        self.playing = False
        self.editing = True
        self.ed = dict(init=list(flat(self.rec.init)), goal=list(flat(self.goal)), sel=None)
        mx, my = self.MOD.x, self.MOD.y
        self.ed_buttons = [
            Button((mx + 56, my + 330, 222, 36), "Xáo ngẫu nhiên", "ed_shuffle"),
            Button((self.MOD.right - 56 - 222, my + 330, 222, 36), "Đích chuẩn 1-8", "ed_std"),
            Button((self.MOD.right - 56 - 230, my + self.MOD.h - 58, 110, 40), "Hủy", "ed_cancel"),
            Button((self.MOD.right - 56 - 112, my + self.MOD.h - 58, 112, 40), "Áp dụng", "ed_apply"),
        ]
        self.ed_check()

    def ed_check(self):
        init, goal = grid(self.ed["init"]), grid(self.ed["goal"])
        if not solvable(init, goal):
            self.ed.update(ok=False, col=RED, msg="Không giải được: hai bàn cờ khác tính chẵn lẻ. Hãy đổi chỗ thêm một cặp ô.")
            return
        st = quick_stats(init, goal, self.algo)
        nm = self.algo.upper()
        if st is None:
            self.ed.update(ok=False, col=ORANGE,
                           msg=f"Giải được nhưng quá lớn: {nm} phải mở hơn {LIMIT[self.algo]} nút, khó theo dõi. Hãy đặt gần đích hơn.")
        elif st[0] == 0:
            self.ed.update(ok=True, col=GREEN, msg="Trạng thái đầu đã bằng đích: 0 bước.")
        else:
            tail = "" if self.info()["optimal"] else " (không chắc ngắn nhất)"
            self.ed.update(ok=True, col=GREEN, msg=f"{nm} tìm được lời giải {st[0]} bước{tail}, mở {st[1]} nút.")

    def editor_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.editing = False
            elif e.key == pygame.K_RETURN and self.ed["ok"]:
                self.press_ed("ed_apply")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            m = self.to_canvas(e.pos)
            for b in self.ed_buttons:
                if b.rect.collidepoint(m):
                    self.press_ed(b.key)
                    return
            for which in ("init", "goal"):
                for i in range(9):
                    if self.ed_cell(which, i).collidepoint(m):
                        sel = self.ed["sel"]
                        if sel is None or sel[0] != which:
                            self.ed["sel"] = (which, i)
                        elif sel[1] == i:
                            self.ed["sel"] = None
                        else:
                            a = self.ed[which]
                            a[sel[1]], a[i] = a[i], a[sel[1]]
                            self.ed["sel"] = None
                            self.ed_check()
                        return
            if not self.MOD.collidepoint(m):
                self.ed["sel"] = None

    def press_ed(self, key):
        if key == "ed_cancel":
            self.editing = False
        elif key == "ed_apply":
            if self.ed["ok"]:
                self.editing = False
                self.preset = -1
                self.load(grid(self.ed["init"]), grid(self.ed["goal"]))
        elif key == "ed_std":
            self.ed["goal"] = list(flat(GOAL))
            self.ed["sel"] = None
            self.ed_check()
        elif key == "ed_shuffle":
            st, _ = random_initial("puzzle8", self.algo, grid(self.ed["goal"]))
            self.ed["init"] = list(flat(st))
            self.ed["sel"] = None
            self.ed_check()

    def draw_editor(self, s):
        veil = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        veil.fill((4, 6, 12, 190))
        s.blit(veil, (0, 0))
        M = self.MOD
        G.rect(s, (22, 29, 46), M, border_radius=18)
        G.rect(s, CYAN, M, 2, border_radius=18)
        text(s, "Tự đặt trạng thái", font("segoeui", 22, True), TEXT, (M.x + 28, M.y + 18))
        text(s, "Bấm một ô rồi bấm ô thứ hai (cùng bàn cờ) để đổi chỗ hai ô.", font("segoeui", 14), MUTED,
             (M.x + 28, M.y + 52))
        for which, title, col in (("init", "Trạng thái đầu", ORANGE), ("goal", "Trạng thái đích", GREEN)):
            c0 = self.ed_cell(which, 0)
            text(s, title, font("segoeui", 16, True), col, (c0.x, c0.y - 36))
            size = 3 * self.ED_CELL + 2 * self.ED_GAP
            G.rect(s, (14, 18, 30), (c0.x - 8, c0.y - 8, size + 16, size + 16), border_radius=12)
            for i, v in enumerate(self.ed[which]):
                r = self.ed_cell(which, i)
                if v:
                    G.rect(s, TILE_COL[v], r, border_radius=10)
                    text(s, str(v), font("segoeui", 30, True), (26, 26, 40), r.center, "center")
                else:
                    G.rect(s, (30, 38, 58), r, border_radius=10)
                    text(s, "trống", font("segoeui", 13), MUTED, r.center, "center")
                if self.ed["sel"] == (which, i):
                    G.rect(s, CYAN, r.inflate(4, 4), 4, border_radius=12)
        mid = (M.centerx, M.y + 96 + 111)
        text(s, "→", font("segoeui", 40, True), MUTED, mid, "center")
        msg_col = self.ed["col"]
        box = pygame.Rect(M.x + 56, M.y + 386, M.w - 112, 40)
        G.rect(s, shade(msg_col, 0.22), box, border_radius=10)
        G.rect(s, msg_col, box, 2, border_radius=10)
        lines = wrap(self.ed["msg"], font("segoeui", 15), box.w - 24)
        for k, line in enumerate(lines[:2]):
            text(s, line, font("segoeui", 15), msg_col, (box.x + 12, box.y + 4 + k * 17))
        mouse = self.mouse
        for b in self.ed_buttons:
            b.active = b.key == "ed_apply" and self.ed["ok"]
            b.draw(s, mouse)

    def update(self, dt):
        last = len(self.events) - 1
        self.toast = (self.toast[0], max(0.0, self.toast[1] - dt))
        tgt = ALGO_COL[self.algo]
        self.acc = [sm(self.acc[i], tgt[i], 9, dt) for i in range(3)]
        global ACC_NOW
        ACC_NOW = tuple(int(v) for v in self.acc)
        self.sw_x = sm(self.sw_x, self.algo_rects[self.algo].x, 14, dt)
        if self.playing or self.one:
            self.ev_t += dt * self.speed()
            while self.ev_t >= self.ev["dur"]:
                if self.ev_i >= last:
                    self.ev_t = self.ev["dur"]
                    self.playing = self.one = False
                    break
                if self.one:
                    self.ev_t = self.ev["dur"]
                    self.one = False
                    break
                self.ev_t -= self.ev["dur"]
                self.ev_i += 1
        if self.replay:
            self.update_replay(dt)
        else:
            self.sync_boards()
        self.node_board.update(dt)
        self.child_board.update(dt)
        ev = self.ev
        self.child_board.alpha = sm(self.child_board.alpha, 1.0 if ev["child"] else 0.18, 8, dt)
        self.bar_y = sm(self.bar_y, CODE_Y + 36 + ev["line"] * LH, 30, dt)
        for k in range(2):
            g = ev["gate"][k]
            tgt = (84, 96, 120) if g is None else (RED if g else GREEN)
            self.lamps[k] = [sm(self.lamps[k][j], tgt[j], 12, dt) for j in range(3)]
        key = (ev["verdict"], ev["child"][2] if ev["child"] else None)
        if key != self.banner_key:
            self.banner_key, self.banner_age = key, 0.0
        self.banner_age += dt
        if ev["cap"] != self.cap_text:
            self.cap_text, self.cap_age = ev["cap"], 0.0
        self.cap_age += dt
        self.update_table(dt)
        self.update_queue(dt)
        self.update_explored(dt)

    def sync_boards(self, snap=False):
        ev = self.ev
        if self.node_board.state != flat(ev["node_state"]):
            self.node_board.set_state(ev["node_state"])
        ch = ev["child"]
        ck = ch[2] if ch else None
        if ch and ck != self.last_child_key:
            self.child_board.state, self.child_board.pos = None, {}
            self.child_board.set_state(ch[0], copy_from=self.node_board)
        self.last_child_key = ck
        if snap:
            for b in (self.node_board, self.child_board):
                if b.state:
                    for i, v in enumerate(b.state):
                        if v:
                            b.pos[v] = list(b.slot(i))

    def compute_layout(self, tn):
        nodes = self.rec.nodes
        cols = max(1, int((TAB.w - 28 + GAPC) // (CELL + GAPC)))
        by = {}
        for eid in range(tn):
            by.setdefault(nodes[eid]["depth"], []).append(eid)
        pos, heads, y = {}, [], 0
        for d in sorted(by):
            heads.append((d, y, len(by[d])))
            y += 24
            for k, eid in enumerate(by[d]):
                pos[eid] = (14 + (k % cols) * (CELL + GAPC), y + (k // cols) * (CELL + GAPC))
            y += ((len(by[d]) - 1) // cols + 1) * (CELL + GAPC) + 8
        return pos, heads, y

    def update_table(self, dt):
        ev = self.ev
        tn = ev["tn"]
        if tn != self.layout_tn:
            self.tpos, self.theads, self.ttotal = self.compute_layout(tn)
            self.layout_tn = tn
        view_h = TAB.h - 48
        focus = ev["node_eid"] if ev["node_eid"] is not None else (tn - 1 if tn else None)
        if ev["child_eid"] is not None and ev["child_eid"] < tn:
            focus = ev["child_eid"]
        if focus is not None and focus in self.tpos:
            tgt = self.tpos[focus][1] - view_h * 0.4
            self.scroll = sm(self.scroll, max(0, min(tgt, max(0, self.ttotal - view_h))), 5, dt)
        cb = self.child_board.center
        for eid in list(self.anim_tab):
            if eid >= tn:
                del self.anim_tab[eid]
        for eid, (x, y) in self.tpos.items():
            a = self.anim_tab.get(eid)
            if a is None:
                sx, sy = cb[0] - TAB.x, cb[1] - TAB.y - 36 + self.scroll
                a = self.anim_tab[eid] = [sx - CELL / 2, sy - CELL / 2, 0.35, 0.0]
            a[0], a[1] = sm(a[0], x, 7, dt), sm(a[1], y, 7, dt)
            a[2], a[3] = sm(a[2], 1.0, 7, dt), sm(a[3], 1.0, 9, dt)

    QX, QP, QMAX = 150, 60, 20

    def update_queue(self, dt):
        ev = self.ev
        fr = ev["frontier"]
        cb = self.child_board.center
        nb = self.node_board.center
        for eid in list(self.anim_q):
            if eid >= ev["tn"]:
                del self.anim_q[eid]
        offset = max(0, len(fr) - self.QMAX) if self.algo == "dfs" else 0
        for i, eid in enumerate(fr):
            a = self.anim_q.get(eid)
            if a is None:
                a = self.anim_q[eid] = [cb[0], cb[1], 0.4, 0.0, False]
            a[4] = False
            idx = i - offset
            show = 0 <= idx < self.QMAX
            a[0] = sm(a[0], self.QX + idx * self.QP + 25, 8, dt)
            a[1] = sm(a[1], Q_Y + 60, 8, dt)
            a[2] = sm(a[2], 1.0, 8, dt)
            a[3] = sm(a[3], 1.0 if show else 0.0, 8, dt)
        gone = []
        for eid, a in self.anim_q.items():
            if eid not in fr:
                a[4] = True
                a[0], a[1] = sm(a[0], nb[0], 7, dt), sm(a[1], nb[1], 7, dt)
                a[2], a[3] = sm(a[2], 0.7, 7, dt), sm(a[3], 0.0, 9, dt)
                if a[3] < 0.03:
                    gone.append(eid)
        for eid in gone:
            del self.anim_q[eid]

    def update_explored(self, dt):
        ev = self.ev
        ex = ev["explored"]
        nb = self.node_board.center
        start = max(0, len(ex) - 20)
        for eid in list(self.anim_e):
            if eid not in ex:
                del self.anim_e[eid]
        for i, eid in enumerate(ex):
            a = self.anim_e.get(eid)
            if a is None:
                a = self.anim_e[eid] = [nb[0], nb[1], 0.5, 0.0]
            idx = i - start
            a[0] = sm(a[0], 150 + idx * 58 + 27, 8, dt)
            a[1] = sm(a[1], E_Y + 36, 8, dt)
            a[2] = sm(a[2], 1.0, 8, dt)
            a[3] = sm(a[3], 1.0 if idx >= 0 else 0.0, 8, dt)

    def draw(self):
        s = self.canvas
        s.fill(BG)
        ev = self.ev
        p = min(1.0, self.ev_t / ev["dur"]) if ev["dur"] else 1.0
        self.draw_header(s, ev)
        self.draw_code(s, ev)
        self.draw_table(s, ev, p)
        self.draw_right(s, ev, p)
        self.draw_queue(s, ev, p)
        self.draw_explored(s, ev)
        self.draw_controls(s)
        if self.toast[1] > 0:
            a = min(1.0, self.toast[1] / 0.5)
            r = pygame.Rect(0, 0, TAB.w - 24, 34)
            r.midbottom = (TAB.centerx, TAB.bottom - 12)
            G.rect(s, (60, 40, 18), r, border_radius=17)
            G.rect(s, ORANGE, r, 2, border_radius=17)
            for k, line in enumerate(wrap(self.toast[0], font("segoeui", 13), TAB.w - 44)[:1]):
                text(s, line, font("segoeui", 13), ORANGE, r.center, "center", alpha=a)
        if self.editing:
            self.draw_editor(s)

    def draw_header(self, s, ev):
        acc = tuple(int(v) for v in self.acc)
        text(s, ALGO_INFO[self.algo][3], font("segoeui", 28, True), acc, (16, 10))
        text(s, "8-puzzle · từng dòng code sáng lên trên hình",
             font("segoeui", 15), MUTED, (18, 50))
        chips = [("Đã mở", len(ev["explored"]), ORANGE), ("Frontier", len(ev["frontier"]), BLUE),
                 ("Nút sinh ra", ev["tn"], CYAN),
                 ("Chi phí g", ev["node_cost"], GOLD) if self.info()["cost"] else ("Độ sâu", ev["node_depth"], GOLD)]
        x = W - 16
        for name, val, col in reversed(chips):
            f1, f2 = font("segoeui", 13), font("segoeui", 22, True)
            w = max(tw(f1, name), 36) + 26
            r = pygame.Rect(x - w, 12, w, 52)
            G.rect(s, PANEL, r, border_radius=10)
            G.rect(s, shade(col, 0.55), r, 1, border_radius=10)
            text(s, name, f1, MUTED, (r.centerx, r.y + 6), "midtop")
            text(s, str(val), f2, col, (r.centerx, r.y + 22), "midtop")
            x = r.x - 8
        text(s, "Đích", font("segoeui", 14, True), GREEN, (x - 66, 38), "midright")
        blit_mini(s, self.goal, x - 34, 38, 46)
        self.draw_switch(s)

    def draw_switch(self, s):
        st = self.sw_style
        cont = pygame.Rect(st["x0"] - 6, 10, st["total"] + 12, 64)
        G.rect(s, (16, 21, 34), cont, border_radius=18)
        G.rect(s, PANEL_L, cont, 1, border_radius=18)
        acc = tuple(int(v) for v in self.acc)
        pill = pygame.Rect(round(self.sw_x), 16, self.algo_rects[self.algo].w, 52)
        G.rect(s, shade(acc, 0.35), pill.inflate(8, 8), border_radius=18)
        G.rect(s, acc, pill, border_radius=14)
        for key, r in self.algo_rects.items():
            name, l1, l2, _ = ALGO_INFO[key]
            on = key == self.algo
            col = (10, 22, 30) if on else (TEXT if r.collidepoint(self.mouse) else MUTED)
            text(s, name, font("segoeui", st["name_s"], True), col, (r.x + st["name_x"], r.centery), "midleft")
            text(s, l1, font("segoeui", 13, True), col, (r.x + st["lx"], r.centery - 9), "midleft")
            text(s, l2, font("segoeui", st["l2_s"]), col, (r.x + st["lx"], r.centery + 9), "midleft")

    def draw_code(self, s, ev):
        rect = pygame.Rect(CODE_X, CODE_Y, CODE_W, CODE_H)
        acc = tuple(int(v) for v in self.acc)
        panel(s, rect, f"mã nguồn  {self.algo.upper()}(problem)", acc)
        G.rect(s, shade(acc, 0.6), rect, 2, border_radius=14)
        top = CODE_Y + 36
        G.rect(s, (24, 32, 52), (CODE_X + 8, self.bar_y, CODE_W - 16, LH), border_radius=6)
        glow = pygame.Surface((round((CODE_W - 16) * SC), round(LH * SC)), pygame.SRCALPHA)
        glow.fill((*acc, 40))
        s.blit(glow, (round((CODE_X + 8) * SC), round(self.bar_y * SC)))
        G.rect(s, acc, (CODE_X + 8, self.bar_y, 4, LH), border_radius=2)
        f = font("consolas", 13)
        for i, (bright, dim) in enumerate(self.lines):
            y = top + i * LH - 3
            act = i == ev["line"]
            text(s, str(i + 1), f, acc if act else (70, 82, 110), (CODE_X + 34, y + 4), "topright")
            s.blit(bright if act else dim, (round((CODE_X + 46) * SC), round(y * SC)))
        cap = pygame.Rect(CODE_X + 10, CODE_Y + CODE_H - 72, CODE_W - 20, 62)
        G.rect(s, (14, 20, 34), cap, border_radius=10)
        G.rect(s, PANEL_L, cap, 1, border_radius=10)
        a = min(1.0, self.cap_age / 0.25)
        fc = font("segoeui", 15)
        for k, line in enumerate(wrap(self.cap_text, fc, cap.w - 24)[:3]):
            text(s, line, fc, TEXT, (cap.x + 12, cap.y + 6 + k * 17), alpha=a)

    def status_style(self, eid, ev, fr, ex):
        if ev["path"] and eid in ev["path"]:
            return GOLD, 3, 1.0
        if eid == ev["node_eid"]:
            return ORANGE, 3, 1.0
        if eid in ex:
            return (70, 82, 112), 1, 0.55
        if eid in fr:
            return BLUE, 2, 1.0
        return (70, 82, 112), 1, 1.0

    def draw_table(self, s, ev, p):
        panel(s, TAB, "bảng trạng thái theo độ sâu  (mỗi ô = một nút)", GOLD)
        view = pygame.Rect(TAB.x + 6, TAB.y + 36, TAB.w - 12, TAB.h - 44)
        clip = s.get_clip()
        setclip(s, view)
        oy = TAB.y + 36 - self.scroll
        fr, ex = set(ev["frontier"]), set(ev["explored"])
        for d, y, n in self.theads:
            yy = oy + y
            if view.y - 30 < yy < view.bottom:
                text(s, f"Độ sâu {d}", font("segoeui", 14, True), GOLD, (TAB.x + 18, yy + 2))
                text(s, f"{n} nút", font("segoeui", 13), MUTED, (TAB.right - 22, yy + 3), "topright")
                G.line(s, PANEL_L, (TAB.x + 14, yy + 21), (TAB.right - 14, yy + 21))
        nodes = self.rec.nodes
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 220)
        order = sorted(self.anim_tab, key=lambda e: (e == ev["node_eid"], e in ev["path"]))
        for eid in order:
            x, y, sc, al = self.anim_tab[eid]
            cx, cy = TAB.x + x + CELL / 2, oy + y + CELL / 2
            if cy < view.y - CELL or cy > view.bottom + CELL:
                continue
            col, bw, dim = self.status_style(eid, ev, fr, ex)
            r = blit_mini(s, nodes[eid]["state"], cx, cy, CELL, sc, al * (0.5 + 0.5 * dim))
            if eid == ev["node_eid"]:
                col = mix(ORANGE, (255, 240, 200), pulse * 0.6)
                G.rect(s, shade(ORANGE, 0.45), r.inflate(10, 10), 2, border_radius=10)
            if eid == ev["match"]:
                col = RED
            G.rect(s, col, r.inflate(2, 2), bw, border_radius=8)
            self.cost_badge(s, r, nodes[eid].get("cost"))
        ne = ev["node_eid"]
        if ne is not None and ne in self.anim_tab and nodes[ne]["parent"] in self.anim_tab:
            a, b = self.anim_tab[ne], self.anim_tab[nodes[ne]["parent"]]
            G.line(s, shade(ORANGE, 0.7), (TAB.x + a[0] + CELL / 2, oy + a[1] + CELL / 2),
                             (TAB.x + b[0] + CELL / 2, oy + b[1] + CELL / 2), 2)
        if ev["path"]:
            pts = [(TAB.x + self.anim_tab[e][0] + CELL / 2, oy + self.anim_tab[e][1] + CELL / 2)
                   for e in ev["path"] if e in self.anim_tab]
            if len(pts) > 1:
                t = min(1.0, p * 1.3 if ev["kind"] == "done" else 1.0)
                n = max(1, int(t * (len(pts) - 1)))
                G.lines(s, GOLD, False, pts[:n + 1], 4)
                for q in pts[:n + 1]:
                    G.circle(s, GOLD, q, 5)
        s.set_clip(clip)
        if self.ttotal > view.h:
            th = max(30, view.h * view.h / self.ttotal)
            ty = view.y + (view.h - th) * (self.scroll / max(1, self.ttotal - view.h))
            G.rect(s, PANEL_L, (TAB.right - 8, ty, 4, th), border_radius=2)

    def draw_replay(self, s):
        rp, nb, sol = self.replay, self.node_board, self.rec.solution
        k, n = max(0, rp["k"]), len(rp["states"]) - 1
        glyphs = {"Lên": "↑", "Xuống": "↓", "Trái": "←", "Phải": "→"}
        panel(s, RIGHT, "chạy lời giải", GOLD)
        text(s, "ĐÃ TỚI ĐÍCH" if k == n else f"bước {k} / {n}", font("segoeui", 15, True), GOLD,
             (RIGHT.centerx, nb.y - 20), "midtop")
        nb.draw(s, GREEN if k == n else GOLD)
        act = sol[k - 1] if k >= 1 else None
        r = pygame.Rect(0, 0, 148, 30)
        r.midtop = (RIGHT.centerx, nb.y + nb.size + 12)
        G.rect(s, shade(GOLD, 0.3), r, border_radius=15)
        G.rect(s, GOLD, r, 2, border_radius=15)
        text(s, f"{glyphs[act]}  {act}" if act else "trạng thái đầu", font("segoeui", 18, True), GOLD, r.center, "center")
        by, bw = r.bottom + 22, RIGHT.w - 48
        G.rect(s, PANEL_L, (RIGHT.x + 24, by, bw, 8), border_radius=4)
        G.rect(s, GOLD, (RIGHT.x + 24, by, max(8, bw * k / max(1, n)), 8), border_radius=4)
        text(s, "các nước tiếp theo", font("segoeui", 13, True), MUTED, (RIGHT.x + 24, by + 22))
        nxt = "  ".join(glyphs[a] for a in sol[k:k + 12]) or "—"
        text(s, nxt, font("segoeui", 18, True), TEXT, (RIGHT.x + 24, by + 44))
        text(s, f"Lời giải {n} bước · bấm \"Dừng\" hoặc phím V để thoát", font("segoeui", 12), MUTED,
             (RIGHT.centerx, RIGHT.bottom - 28), "midtop")

    def draw_right(self, s, ev, p):
        if self.replay:
            self.draw_replay(s)
            return
        panel(s, RIGHT, "nút đang xét", ORANGE)
        nb, cb = self.node_board, self.child_board
        text(s, "node", font("segoeui", 15, True), ORANGE, (nb.x - 2, nb.y - 20))
        if self.info()["cost"]:
            text(s, f"g = {ev['node_cost']}", font("segoeui", 14), GOLD, (nb.x + nb.size + 2, nb.y - 19), "topright")
        else:
            text(s, f"độ sâu {ev['node_depth']}", font("segoeui", 14), MUTED, (nb.x + nb.size + 2, nb.y - 19), "topright")
        nb.draw(s, ORANGE if ev["node_eid"] is not None or ev["line"] >= 1 else PANEL_L)
        ay = nb.y + nb.size + 8
        if ev["act"]:
            glyph = {"Lên": "↑", "Xuống": "↓", "Trái": "←", "Phải": "→"}[ev["act"]]
            pop = min(1.0, self.banner_age / 0.25)
            r = pygame.Rect(0, 0, 148, 30)
            r.midtop = (RIGHT.centerx, ay + 4)
            G.rect(s, (32, 42, 66), r, border_radius=15)
            G.rect(s, CYAN, r, 2, border_radius=15)
            text(s, f"{glyph}  {ev['act']}", font("segoeui", 18, True), CYAN, r.center, "center")
        vb = ev["verdict"]
        border = {None: CYAN, "ok": GREEN, "dup": RED, "goal": GOLD, "queued": GREEN, "replace": GOLD}[vb]
        text(s, "child", font("segoeui", 15, True), border, (cb.x - 2, cb.y - 20))
        if self.info()["cost"] and ev["child"]:
            text(s, f"g = {ev['child'][3]}", font("segoeui", 14), GOLD, (cb.x + cb.size + 2, cb.y - 19), "topright")
        cb.draw(s, border, cb.alpha)
        if vb == "dup" and ev["child"]:
            flash = pygame.Surface((round(cb.size * SC), round(cb.size * SC)), pygame.SRCALPHA)
            flash.fill((255, 98, 112, int(70 * (0.5 + 0.5 * math.sin(p * 12)))))
            s.blit(flash, (round(cb.x * SC), round(cb.y * SC)))
        gy = cb.y + cb.size + 12
        for k, label in enumerate(self.info()["gates"]):
            y = gy + k * 28
            col = tuple(int(v) for v in self.lamps[k])
            G.circle(s, shade(col, 0.4), (RIGHT.x + 26, y + 11), 11)
            G.circle(s, col, (RIGHT.x + 26, y + 11), 8)
            text(s, label, font("consolas", 13), TEXT, (RIGHT.x + 46, y + 3))
            g = ev["gate"][k]
            tag = "?" if g is None else ("CÓ" if g else "KHÔNG")
            text(s, tag, font("segoeui", 15, True), col, (RIGHT.right - 18, y + 1), "topright")
        msg = {None: "", "ok": "Nút mới → xét tiếp", "dup": "Trùng → BỎ", "goal": "ĐÍCH!",
               "queued": self.queued_msg(), "replace": "Rẻ hơn → thay nút cũ"}[vb]
        if vb:
            col = {"ok": GREEN, "dup": RED, "goal": GOLD, "queued": GREEN, "replace": GOLD}[vb]
            pop = min(1.0, self.banner_age / 0.3)
            ease = 1 - (1 - pop) ** 3
            r = pygame.Rect(0, 0, int(260 * (0.6 + 0.4 * ease)), 34)
            r.midtop = (RIGHT.centerx, gy + 62)
            G.rect(s, shade(col, 0.28), r, border_radius=17)
            G.rect(s, col, r, 2, border_radius=17)
            text(s, msg, font("segoeui", 17, True), col, r.center, "center", alpha=ease)

    def draw_queue(self, s, ev, p):
        rect = pygame.Rect(12, Q_Y, W - 24, 100)
        acc = tuple(int(v) for v in self.acc)
        panel(s, rect)
        G.rect(s, shade(acc, 0.6), rect, 2, border_radius=14)
        dfs = self.algo == "dfs"
        text(s, "FRONTIER", font("segoeui", 15, True), acc, (26, Q_Y + 18))
        prio = self.info()["frontier"] == "priority"
        text(s, "ngăn xếp LIFO" if dfs else ("ưu tiên theo g" if prio else "hàng đợi FIFO"), font("segoeui", 13), MUTED, (26, Q_Y + 40))
        text(s, f"{len(ev['frontier'])} nút", font("segoeui", 13), MUTED, (26, Q_Y + 62))
        belt = pygame.Rect(self.QX - 8, Q_Y + 28, self.QMAX * self.QP + 2, 64)
        G.rect(s, (14, 20, 34), belt, border_radius=10)
        off = (pygame.time.get_ticks() / 60) % 16 if self.playing else 0
        for x in range(int(belt.x + 8 - off), belt.right - 8, 16):
            if x > belt.x + 4:
                G.line(s, (26, 34, 54), (x, belt.bottom - 5), (x + 8, belt.bottom - 5), 2)
        hidden = max(0, len(ev["frontier"]) - self.QMAX) if dfs else 0
        if dfs:
            text(s, "ĐÁY" + (f"  (+{hidden} nút ẩn)" if hidden else ""), font("segoeui", 12, True), MUTED, (belt.x + 4, Q_Y + 8), "topleft")
            text(s, "ĐỈNH  (push / pop)", font("segoeui", 12, True), GREEN, (belt.right - 4, Q_Y + 8), "topright")
        else:
            text(s, "ĐẦU: g nhỏ nhất  (pop)" if prio else "HEAD  (dequeue)", font("segoeui", 12, True), GREEN, (belt.x + 4, Q_Y + 8), "topleft")
            text(s, "g lớn nhất  (push chèn theo g)" if prio else "TAIL  (enqueue)", font("segoeui", 12, True), ORANGE, (belt.right - 4, Q_Y + 8), "topright")
        clip = s.get_clip()
        setclip(s, belt.inflate(-4, 8))
        nodes = self.rec.nodes
        match, tick = ev["match"], pygame.time.get_ticks()
        for eid, (x, y, sc, al, gone) in sorted(self.anim_q.items(), key=lambda t: t[1][4]):
            r = blit_mini(s, nodes[eid]["state"], x, y, 46, sc, al)
            if not gone:
                col = RED if eid == match else BLUE
                G.rect(s, col, r.inflate(2, 2), 2 if eid != match else 3, border_radius=8)
                self.cost_badge(s, r, nodes[eid].get("cost"))
        if ev["kind"] == "scan" and ev["frontier"]:
            fr = ev["frontier"]
            lim = fr.index(ev["scan_match"]) if ev["scan_match"] in fr else len(fr) - 1
            ci = min(lim, int(min(1.0, p * 1.15) * lim + 0.5)) if lim else 0
            ci -= hidden
            if 0 <= ci < self.QMAX:
                cx = self.QX + ci * self.QP + 25
                hit = ev["scan_match"] is not None and ci + hidden == lim and p > 0.6
                col = RED if hit else CYAN
                G.rect(s, col, (cx - 29, Q_Y + 28, 58, 64), 3, border_radius=10)
                G.polygon(s, col, [(cx - 7, Q_Y + 21), (cx + 7, Q_Y + 21), (cx, Q_Y + 30)])
        s.set_clip(clip)
        extra = 0 if dfs else len(ev["frontier"]) - self.QMAX
        if extra > 0:
            text(s, f"+{extra}", font("segoeui", 15, True), MUTED, (belt.right + 4, Q_Y + 48), "topleft")

    def draw_explored(self, s, ev):
        rect = pygame.Rect(12, E_Y, W - 24, 72)
        panel(s, rect)
        text(s, "EXPLORED", font("segoeui", 15, True), ORANGE, (26, E_Y + 10))
        text(s, "đã mở", font("segoeui", 13), MUTED, (26, E_Y + 31))
        text(s, f"{len(ev['explored'])} nút", font("segoeui", 13), MUTED, (26, E_Y + 49))
        clip = s.get_clip()
        setclip(s, pygame.Rect(self.QX - 8, E_Y + 4, W - self.QX - 12, 64))
        nodes = self.rec.nodes
        for eid, (x, y, sc, al) in self.anim_e.items():
            r = blit_mini(s, nodes[eid]["state"], x, y, 52, sc, al * 0.9)
            G.rect(s, (70, 82, 112), r, 1, border_radius=6)
        s.set_clip(clip)

    def draw_controls(self, s):
        last = len(self.events) - 1
        bar = pygame.Rect(12, 832, W - 24, 6)
        G.rect(s, PANEL_L, bar, border_radius=3)
        frac = (self.ev_i + min(1.0, self.ev_t / self.ev["dur"])) / max(1, last + 1)
        G.rect(s, tuple(int(v) for v in self.acc), (bar.x, bar.y, max(6, bar.w * frac), bar.h), border_radius=3)
        self.bar_rect = bar
        mouse = self.mouse
        for b in self.buttons:
            b.active = (b.key == "play" and self.playing) or (b.key == f"p{self.preset}") or (b.key == "alg_" + self.algo) \
                or (b.key == "replay" and bool(self.replay))
            if b.key == "replay":
                b.label = "Dừng" if self.replay else "Chạy lời giải"
            if b.key.startswith("p") and b.key[1:].isdigit():
                b.label = self.presets[int(b.key[1:])][0]
            if b.key == "play":
                b.label = "Dừng" if self.playing else "Phát"
            b.draw(s, mouse)
        text(s, f"x{SPEEDS[self.speed_i]:g}", font("segoeui", 17, True), CYAN, (self.speed_x + 6, 866), "midleft")
        pre = [b for b in self.buttons if b.key == "p0"][0]
        text(s, "Bài mẫu:", font("segoeui", 14), MUTED, (pre.rect.x - 8, 866), "midright")
        text(s, f"dòng {self.ev['line'] + 1}  ·  sự kiện {self.ev_i + 1}/{last + 1}", font("segoeui", 13), MUTED,
             (CODE_X + CODE_W - 14, CODE_Y + 12), "topright")

    def to_canvas(self, pos):
        ww, wh = self.win.get_size()
        sc = min(ww / W, wh / H)
        ox, oy = (ww - W * sc) / 2, (wh - H * sc) / 2
        return ((pos[0] - ox) / sc, (pos[1] - oy) / sc)

    def run(self):
        self.mouse = (0, 0)
        while True:
            dt = min(0.05, self.clock.tick(60) / 1000)
            self.win = pygame.display.get_surface()
            self.mouse = self.to_canvas(pygame.mouse.get_pos())
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not self.editing):
                    pygame.quit()
                    return
                if self.editing:
                    self.editor_event(e)
                    continue
                if e.type == pygame.KEYDOWN:
                    k = e.key
                    if k == pygame.K_SPACE: self.press("play")
                    elif k == pygame.K_RIGHT: self.press("next")
                    elif k == pygame.K_LEFT: self.press("back")
                    elif k == pygame.K_n: self.press("node")
                    elif k == pygame.K_r: self.press("reset")
                    elif k == pygame.K_UP: self.press("fast")
                    elif k == pygame.K_DOWN: self.press("slow")
                    elif k == pygame.K_g: self.press("rand")
                    elif k == pygame.K_F11:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            self.win = pygame.display.set_mode(self.win_size, pygame.RESIZABLE)
                    elif k == pygame.K_t: self.press("edit")
                    elif k == pygame.K_v: self.press("replay")
                    elif k == pygame.K_b: self.press("alg_bfs")
                    elif k == pygame.K_d: self.press("alg_dfs")
                    elif k == pygame.K_u: self.press("alg_ucs")
                    elif pygame.K_1 <= k <= pygame.K_3: self.press(f"p{k - pygame.K_1}")
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    m = self.to_canvas(e.pos)
                    hit = False
                    for b in self.buttons:
                        if b.rect.collidepoint(m):
                            self.press(b.key)
                            hit = True
                    for k, r in self.algo_rects.items():
                        if r.collidepoint(m):
                            self.press("alg_" + k)
                            hit = True
                    if not hit and 826 <= m[1] <= 842 and 12 <= m[0] <= W - 12:
                        self.seek(int((m[0] - 12) / (W - 24) * len(self.events)))
            self.apply_scale()
            self.update(dt)
            self.draw()
            self.win.fill((8, 10, 16))
            ww, wh = self.win.get_size()
            cw, ch = self.canvas.get_size()
            self.win.blit(self.canvas, ((ww - cw) // 2, (wh - ch) // 2))
            pygame.display.flip()


if __name__ == "__main__":
    App().run()
