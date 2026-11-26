import ctypes
import math
import random
import re
from collections import deque

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pygame

W, H = 1400, 940

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
DIRTY = (150, 108, 66)
CLEAN = (80, 184, 116)
ALGO_COL = {"bfs": (86, 214, 230), "dfs": (255, 126, 170)}
ALGO_INFO = {"bfs": ("BFS", "Chiều rộng", "hàng đợi FIFO", "Breadth-First Search"),
             "dfs": ("DFS", "Chiều sâu", "ngăn xếp LIFO", "Depth-First Search")}
ACC_NOW = (86, 214, 230)

CODE = [
    "def BFS(problem):",
    "    node = Node(problem.initial_state)",
    "    if is_goal(problem, node.state):",
    "        return solution(node)",
    "    frontier = Queue()",
    "    enqueue(frontier, node)",
    "    explored = []",
    "    while not is_empty(frontier):",
    "        node = dequeue(frontier)",
    "        explored.append(node.state)",
    "        for action in problem.actions(node.state):",
    "            child = child_node(problem, node, action)",
    "            in_frontier = False",
    "            for n in frontier:",
    "                if n.state == child.state:",
    "                    in_frontier = True",
    "            if child.state not in explored and not in_frontier:",
    "                if is_goal(problem, child.state):",
    "                    return solution(child)",
    "                enqueue(frontier, child)",
    "    return None",
]
CODE_DFS = [l.replace("BFS", "DFS").replace("Queue()", "Stack()").replace("enqueue", "push")
            .replace("dequeue", "pop").replace("for action in problem.actions(node.state):",
                                               "for action in reversed(problem.actions(node.state)):")
            for l in CODE]
CODE_BY = {"bfs": CODE, "dfs": CODE_DFS}
TOKEN = re.compile(r"(?P<kw>\b(?:def|if|for|while|not|in|return|and)\b)|(?P<fn>\b[A-Za-z_]\w*(?=\())|"
                   r"(?P<lit>\b(?:False|True|None)\b)")

ROOM_TYPES = ["living", "kitchen", "bedroom", "bath", "study", "hall"]
ROOM_NAMES = {"living": "Phòng khách", "kitchen": "Bếp", "bedroom": "Phòng ngủ", "bath": "Phòng tắm",
              "study": "Làm việc", "hall": "Hành lang", "storage": "Kho"}
ACT_VI = {"Suck": "hút bụi phòng hiện tại → phòng đó thành C",
          "Left": "robot sang phòng bên trái",
          "Right": "robot sang phòng bên phải"}


def letter(i):
    return chr(65 + i)


def actions(state):
    return ["Suck", "Left", "Right"]


def result(state, a):
    n = len(state) - 1
    pos, st = state[0], list(state[1:])
    if a == "Suck":
        st[pos] = "C"
    elif a == "Left":
        pos = max(0, pos - 1)
    elif a == "Right":
        pos = min(n - 1, pos + 1)
    return (pos,) + tuple(st)


def make_state(pos, dirt):
    return (pos,) + tuple("D" if d else "C" for d in dirt)


def make_goal(n, pos):
    return (pos,) + ("C",) * n


class Rec:
    def __init__(self, init, goal, algo):
        self.init, self.goal, self.algo = init, goal, algo
        self.nodes = []
        self.events = []
        self.frontier, self.explored = [], []
        self.reset_view()
        self.node_state, self.node_eid, self.node_depth = init, None, 0
        self.tn = 0
        self.ckey = 0
        self.path = ()
        self.solution = []
        self.work()

    def reset_view(self):
        self.act = None
        self.child = None
        self.child_eid = None
        self.gate = [None, None]
        self.verdict = None
        self.match = None
        self.scan_match = None

    def emit(self, line, cap, dur, kind="n"):
        self.events.append(dict(
            line=line, cap=cap, dur=dur, kind=kind, act=self.act, child=self.child, child_eid=self.child_eid,
            frontier=tuple(self.frontier), explored=tuple(self.explored), tn=self.tn,
            gate=tuple(self.gate), verdict=self.verdict, match=self.match, scan_match=self.scan_match,
            node_state=self.node_state, node_eid=self.node_eid, node_depth=self.node_depth, path=self.path))

    def add_node(self, state, parent, action):
        depth = 0 if parent is None else self.nodes[parent]["depth"] + 1
        self.nodes.append(dict(state=state, parent=parent, action=action, depth=depth))
        self.tn = len(self.nodes)
        return len(self.nodes) - 1

    def chain(self, eid):
        out, acts = [], []
        while eid is not None:
            out.append(eid)
            acts.append(self.nodes[eid]["action"])
            eid = self.nodes[eid]["parent"]
        return tuple(reversed(out)), [a for a in reversed(acts) if a]

    def work(self):
        init = self.init
        dfs = self.algo == "dfs"
        ds = "ngăn xếp" if dfs else "hàng đợi"
        self.emit(1, "node = Node(initial_state): tạo nút gốc từ trạng thái đầu.", 0.9)
        if init == self.goal:
            self.emit(2, "is_goal(node.state) đúng ngay → trả về lời giải rỗng.", 0.8)
            self.emit(3, "return solution(node)", 0.8, "done")
            return
        self.emit(2, "is_goal(problem, node.state)? Chưa phải đích → tiếp tục.", 0.6)
        self.emit(4, "frontier = Stack(): tạo ngăn xếp LIFO rỗng." if dfs else "frontier = Queue(): tạo hàng đợi FIFO rỗng.", 0.5)
        root = self.add_node(init, None, None)
        self.frontier.append(root)
        self.node_eid = None
        self.emit(5, "push(frontier, node): đặt nút gốc lên ĐỈNH ngăn xếp." if dfs else "enqueue(frontier, node): bỏ nút gốc vào CUỐI hàng đợi.", 0.9)
        self.emit(6, "explored = []: tập các trạng thái đã mở, ban đầu rỗng.", 0.5)
        while self.frontier:
            self.reset_view()
            self.emit(7, f"while not is_empty(frontier): {ds} còn {len(self.frontier)} nút → lặp.", 0.4)
            eid = self.frontier.pop(-1 if dfs else 0)
            nd = self.nodes[eid]
            self.node_state, self.node_eid, self.node_depth = nd["state"], eid, nd["depth"]
            self.emit(8, "pop(frontier): lấy nút ở ĐỈNH ngăn xếp (vào sau, ra trước)." if dfs else "dequeue(frontier): lấy nút ở ĐẦU hàng đợi (vào trước, ra trước).", 0.9)
            self.explored.append(eid)
            self.emit(9, "explored.append(node.state): đánh dấu trạng thái này đã được mở.", 0.7)
            for a in (list(reversed(actions(nd["state"]))) if dfs else actions(nd["state"])):
                self.reset_view()
                self.act = a
                self.emit(10, f"for action in {'reversed(' if dfs else ''}problem.actions(...){')' if dfs else ''}: thử hành động «{a}».", 0.5)
                self.ckey += 1
                cs = result(nd["state"], a)
                self.child = (cs, eid, self.ckey)
                self.emit(11, f"child_node(problem, node, «{a}»): {ACT_VI[a]}.", 1.0)
                self.gate[1] = False
                self.emit(12, f"in_frontier = False: giả sử nút con chưa có trong {ds}.", 0.35)
                hit = [f for f in self.frontier if self.nodes[f]["state"] == cs]
                self.scan_match = hit[0] if hit else None
                self.emit(13, f"for n in frontier: so sánh nút con với từng nút đang chờ trong {ds}.",
                          0.5 + min(len(self.frontier), 24) * 0.035, "scan")
                in_frontier = False
                if hit:
                    self.match = hit[0]
                    self.emit(14, "n.state == child.state: TRÙNG với một nút đang chờ!", 0.6)
                    in_frontier = True
                    self.gate[1] = True
                    self.emit(15, "in_frontier = True", 0.4)
                in_explored = any(self.nodes[e]["state"] == cs for e in self.explored)
                self.gate[0] = in_explored
                ok = (not in_explored) and not in_frontier
                self.verdict = "ok" if ok else "dup"
                if ok:
                    why = f"chưa mở và chưa có trong {ds} → nút MỚI, xét tiếp."
                elif in_explored:
                    why = "trạng thái này đã nằm trong explored → BỎ."
                else:
                    why = "trạng thái này đang chờ trong frontier → BỎ."
                self.emit(16, "if child.state not in explored and not in_frontier: " + why, 1.0, "check")
                if not ok:
                    continue
                if cs == self.goal:
                    gid = self.add_node(cs, eid, a)
                    self.verdict = "goal"
                    self.child_eid = gid
                    self.emit(17, "is_goal(problem, child.state): ĐÚNG, đã tới trạng thái đích!", 0.9)
                    self.path, acts = self.chain(gid)
                    self.solution = acts
                    if dfs and len(acts) > 12:
                        lst = " → ".join(acts[:10]) + f" → … ({len(acts)} bước, DFS không đảm bảo ngắn nhất)"
                    else:
                        lst = " → ".join(acts)
                    self.emit(18, f"return solution(child): lời giải {len(acts)} bước: " + lst, 2.0, "done")
                    return
                self.emit(17, "is_goal(problem, child.state)? Chưa phải đích.", 0.5)
                cid = self.add_node(cs, eid, a)
                self.frontier.append(cid)
                self.child_eid = cid
                self.verdict = "queued"
                self.emit(19, "push(frontier, child): nút con lên ĐỈNH ngăn xếp, đồng thời thêm vào bảng." if dfs else "enqueue(frontier, child): nút con vào CUỐI hàng đợi, đồng thời thêm vào bảng.", 0.95)
        self.reset_view()
        self.emit(20, f"return None: {ds} cạn, không có lời giải.", 1.0, "done")


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

    def ellipse(self, s, c, r, w=0):
        pygame.draw.ellipse(s, c, _r(r), _w(w))


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


def text(dst, s, f, col, pos, anchor="topleft", alpha=1.0):
    t = f.render(s, True, col)
    if alpha < 0.98:
        t.set_alpha(int(255 * max(0, alpha)))
    dst.blit(t, t.get_rect(**{anchor: (round(pos[0] * SC), round(pos[1] * SC))}))


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


def alpha_poly(dst, pts, rgba):
    pp = [_p(q) for q in pts]
    xs, ys = [q[0] for q in pp], [q[1] for q in pp]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    w, h = int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4
    tmp = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, rgba, [(q[0] - x0, q[1] - y0) for q in pp])
    dst.blit(tmp, (x0, y0))


class Button:
    def __init__(self, rect, label, key):
        self.rect, self.label, self.key = pygame.Rect(rect), label, key
        self.active = False

    def draw(self, dst, mouse, fs=16):
        hot = self.rect.collidepoint(mouse)
        col = ACC_NOW if self.active else ((52, 64, 92) if hot else PANEL_L)
        G.rect(dst, col, self.rect, border_radius=10)
        t = font("segoeui", fs, True).render(self.label, True, (10, 22, 30) if self.active else TEXT)
        dst.blit(t, t.get_rect(center=(round(self.rect.centerx * SC), round(self.rect.centery * SC))))


CODE_R = pygame.Rect(12, 92, 500, 580)
SCENE = pygame.Rect(524, 92, 864, 340)
INFO = pygame.Rect(1100, 100, 280, 324)
TAB = pygame.Rect(524, 444, 864, 228)
Q_Y, E_Y = 684, 792
LH = 21
SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16]
QX = 150

ISO = {"TW": 100.0, "TH": 50.0, "OX": 0.0, "OY": 0.0, "ZK": 1.0}


def P(r, c, z=0.0):
    return (ISO["OX"] + (c - r) * ISO["TW"] / 2, ISO["OY"] + (c + r) * ISO["TH"] / 2 - z * ISO["ZK"])


def poly(s, pts3, col, edge=None, w=1):
    pts = [P(*p) for p in pts3]
    G.polygon(s, col, pts)
    if edge:
        G.polygon(s, edge, pts, w)


def box(s, r0, c0, r1, c1, z0, z1, col, edge=True):
    ec = shade(col, 0.45) if edge else None
    poly(s, [(r1, c0, z0), (r1, c1, z0), (r1, c1, z1), (r1, c0, z1)], shade(col, 0.78), ec)
    poly(s, [(r0, c1, z0), (r1, c1, z0), (r1, c1, z1), (r0, c1, z1)], shade(col, 0.58), ec)
    poly(s, [(r0, c0, z1), (r0, c1, z1), (r1, c1, z1), (r1, c0, z1)], col, ec)


def flat(s, r0, c0, r1, c1, z, col, edge=None):
    poly(s, [(r0, c0, z), (r0, c1, z), (r1, c1, z), (r1, c0, z)], col, edge)


def cylinder(s, r, c, rad, z0, z1, col, n=28):
    bot = [P(r + rad * math.cos(2 * math.pi * k / n), c + rad * math.sin(2 * math.pi * k / n), z0) for k in range(n)]
    top = [P(r + rad * math.cos(2 * math.pi * k / n), c + rad * math.sin(2 * math.pi * k / n), z1) for k in range(n)]
    for i in range(n):
        j = (i + 1) % n
        a = 2 * math.pi * (i + 0.5) / n
        if math.cos(a) + math.sin(a) > -0.3:
            k = 0.55 + 0.45 * max(0.0, 0.6 * math.cos(a) - 0.4 * math.sin(a) + 0.4)
            G.polygon(s, shade(col, k), [bot[i], bot[j], top[j], top[i]])
    G.polygon(s, col, top)
    G.polygon(s, shade(col, 0.5), top, 1)


def draw_robot(s, rc, cc, th, spin, rad, led):
    zk = ISO["ZK"]
    h = 16
    ct, st = math.cos(th), math.sin(th)

    def loc(u, v, z=0.0):
        return P(rc + u * ct - v * st, cc + u * st + v * ct, z)

    n = 40
    sh = [P(rc + rad * 1.1 * math.cos(2 * math.pi * k / 32) + 0.05, cc + rad * 1.1 * math.sin(2 * math.pi * k / 32) + 0.05)
          for k in range(32)]
    alpha_poly(s, sh, (0, 0, 0, 80))
    bu, bv = rad * 0.62, rad * 0.58
    hx, hy = loc(bu, bv, 2)
    for k in range(3):
        a = math.radians(spin + k * 120)
        e = P(rc + bu * ct - bv * st + 0.2 * math.cos(a), cc + bu * st + bv * ct + 0.2 * math.sin(a), 2)
        G.line(s, (214, 214, 220), (hx, hy), e, 3 * zk + 1)
    cylinder(s, rc, cc, rad, 0, h, (40, 40, 46), n)
    ring = [P(rc + rad * math.cos(2 * math.pi * k / n), cc + rad * math.sin(2 * math.pi * k / n), h) for k in range(n)]
    G.polygon(s, (32, 32, 36), ring)
    G.polygon(s, (86, 86, 96), ring, 3 * zk + 1)
    inner = [P(rc + rad * 0.88 * math.cos(2 * math.pi * k / n), cc + rad * 0.88 * math.sin(2 * math.pi * k / n), h) for k in range(n)]
    G.polygon(s, (22, 22, 26), inner)
    gl = [P(rc + rad * 0.72 * math.cos(a), cc + rad * 0.72 * math.sin(a), h) for a in [3.3 + k * 0.05 for k in range(22)]]
    G.lines(s, (96, 96, 108), False, gl, 3 * zk + 1)
    for v in (-0.12, 0.12):
        x, y = loc(rad * 0.62, v * rad * 1.6, h)
        G.ellipse(s, (70, 70, 78), (x - 6 * zk, y - 3 * zk, 12 * zk, 7 * zk))
    tr = rad * 0.4
    for k in range(n):
        j = (k + 1) % n
        a = 2 * math.pi * (k + 0.5) / n
        if math.cos(a) + math.sin(a) > -0.3:
            b = [P(rc + tr * math.cos(2 * math.pi * q / n), cc + tr * math.sin(2 * math.pi * q / n), z)
                 for q, z in ((k, h), (j, h), (j, h + 10), (k, h + 10))]
            G.polygon(s, (14, 14, 18), b)
    topc = [P(rc + tr * math.cos(2 * math.pi * q / n), cc + tr * math.sin(2 * math.pi * q / n), h + 10) for q in range(n)]
    G.polygon(s, (36, 36, 42), topc)
    G.polygon(s, (92, 92, 102), topc, 2)
    z = rad * 0.13
    zp = [loc(-z, -z, h + 10), loc(-z, z, h + 10), loc(z, -z, h + 10), loc(z, z, h + 10)]
    G.lines(s, (176, 176, 184), False, zp, 2)
    if led:
        x, y = loc(rad * 0.3, 0, h + 10)
        G.circle(s, (90, 230, 150), (x, y), 4 * zk + 1)


class Scene:
    def __init__(self):
        self.cfg(2)

    def cfg(self, n):
        self.n = n
        self.rows = 1 if n <= 3 else 2
        self.cols = n if n <= 3 else (n + 1) // 2
        self.RS = 2.0
        tot = (self.rows + self.cols) * self.RS
        tw_ = max(44.0, min(150.0, 1100 / tot, (SCENE.h - 44) / (0.62 + tot / 4)))
        ISO["TW"], ISO["TH"], ISO["ZK"] = tw_, tw_ / 2, tw_ / 150
        self.wall_h = 100
        total_h = self.wall_h * ISO["ZK"] + tot * ISO["TH"] / 2 + 18
        cx = SCENE.x + 282
        ISO["OX"] = cx - (self.cols - self.rows) * self.RS * tw_ / 4
        ISO["OY"] = SCENE.y + 26 + (SCENE.h - 26 - total_h) / 2 + self.wall_h * ISO["ZK"] + 4
        self.objs = None
        self.bg = None

    def cell_of(self, i):
        if self.rows == 1:
            return (0, i)
        if i < self.cols:
            return (0, i)
        return (1, 2 * self.cols - 1 - i)

    def index_of(self, gr, gc):
        for i in range(self.n):
            if self.cell_of(i) == (gr, gc):
                return i
        return None

    def room_type(self, gr, gc):
        i = self.index_of(gr, gc)
        return "storage" if i is None else ROOM_TYPES[i % len(ROOM_TYPES)]

    def origin(self, gr, gc):
        return gr * self.RS, gc * self.RS

    def center(self, i):
        gr, gc = self.cell_of(i)
        return gr * self.RS + self.RS / 2, gc * self.RS + self.RS / 2

    def pos_at(self, f):
        f = max(0.0, min(self.n - 1.0, f))
        i = min(int(f), self.n - 2) if self.n > 1 else 0
        t = f - i
        a, b = self.center(i), self.center(min(i + 1, self.n - 1))
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t

    def floor(self, s, gr, gc, rnd):
        r0, c0 = self.origin(gr, gc)
        t = self.room_type(gr, gc)
        RS = self.RS
        pts = [(r0, c0, 0), (r0, c0 + RS, 0), (r0 + RS, c0 + RS, 0), (r0 + RS, c0, 0)]
        if t in ("living", "study", "hall"):
            base = {"living": (190, 140, 90), "study": (204, 164, 114), "hall": (150, 108, 72)}[t]
            poly(s, pts, base)
            dark = shade(base, 0.82)
            for k in range(1, 8):
                f = k / 4
                G.line(s, dark, P(r0 + f, c0), P(r0 + f, c0 + RS), 1)
                off = 0.5 + 0.7 * ((k + gr + gc) % 2)
                G.line(s, dark, P(r0 + f, c0 + off), P(r0 + f - 0.25, c0 + off), 1)
        elif t == "kitchen":
            for i in range(4):
                for j in range(4):
                    col = (236, 230, 218) if (i + j) % 2 == 0 else (186, 186, 182)
                    poly(s, [(r0 + i / 2, c0 + j / 2, 0), (r0 + i / 2, c0 + j / 2 + .5, 0),
                             (r0 + i / 2 + .5, c0 + j / 2 + .5, 0), (r0 + i / 2 + .5, c0 + j / 2, 0)], col)
        elif t == "bedroom":
            poly(s, pts, (152, 174, 198))
            for _ in range(60):
                G.circle(s, rnd.choice([(138, 160, 186), (166, 186, 208)]), P(r0 + rnd.random() * RS, c0 + rnd.random() * RS), 2)
        elif t == "bath":
            poly(s, pts, (158, 212, 222))
            for k in range(1, 6):
                G.line(s, (112, 170, 184), P(r0 + k / 3, c0), P(r0 + k / 3, c0 + RS), 1)
                G.line(s, (112, 170, 184), P(r0, c0 + k / 3), P(r0 + RS, c0 + k / 3), 1)
        else:
            poly(s, pts, (150, 150, 152))
            for k in range(1, 4):
                G.line(s, (126, 126, 130), P(r0 + k / 2, c0), P(r0 + k / 2, c0 + RS), 1)
        G.polygon(s, (0, 0, 0), [P(*p) for p in pts], 1)

    def build_bg(self, canvas):
        rnd = random.Random(5)
        s = canvas
        s.fill(BG)
        G.rect(s, PANEL, SCENE, border_radius=14)
        clip = s.get_clip()
        setclip(s, SCENE)
        G.rect(s, (68, 128, 62), SCENE)
        for x in range(SCENE.x, SCENE.right, 56):
            if ((x - SCENE.x) // 56) % 2 == 0:
                G.rect(s, (74, 138, 66), (x, SCENE.y, 56, SCENE.h))
        for _ in range(900):
            x, y = rnd.uniform(SCENE.x, SCENE.right), rnd.uniform(SCENE.y, SCENE.bottom)
            g = rnd.choice([(52, 104, 50), (88, 156, 76), (60, 118, 56)])
            G.line(s, g, (x, y), (x + rnd.randint(-2, 2), y - rnd.randint(3, 7)), 1)
        R, C, RS = self.rows, self.cols, self.RS
        ground = [P(-0.6, -0.6), P(-0.6, C * RS + 0.6), P(R * RS + 0.6, C * RS + 0.6), P(R * RS + 0.6, -0.6)]
        G.polygon(s, (126, 100, 70), ground)
        G.polygon(s, (92, 70, 48), ground, 2)
        SL = 14
        poly(s, [(R * RS, 0, 0), (R * RS, C * RS, 0), (R * RS, C * RS, -SL), (R * RS, 0, -SL)], (176, 170, 158), (90, 84, 74))
        poly(s, [(0, C * RS, 0), (R * RS, C * RS, 0), (R * RS, C * RS, -SL), (0, C * RS, -SL)], (136, 130, 120), (90, 84, 74))
        for gr in range(R):
            for gc in range(C):
                self.floor(s, gr, gc, rnd)
        for tx, ty, sc in [(SCENE.x + 44, SCENE.y + 215, 0.8), (SCENE.x + 540, SCENE.y + 250, 0.7), (SCENE.x + 70, SCENE.y + 120, 0.6)]:
            G.ellipse(s, (30, 80, 30), (tx - 24 * sc, ty - 6 * sc, 48 * sc, 14 * sc))
            G.rect(s, (96, 66, 42), (tx - 5 * sc, ty - 44 * sc, 10 * sc, 48 * sc))
            for dx, dy, rad in [(0, -80, 28), (-18, -62, 22), (18, -62, 22), (0, -58, 24), (-9, -92, 18)]:
                G.circle(s, rnd.choice([(40, 108, 52), (48, 120, 58)]), (tx + dx * sc, ty + dy * sc), rad * sc)
        s.set_clip(clip)
        self.bg = s

    def build_objs(self):
        zk = ISO["ZK"]
        objs = []
        R, C, RS = self.rows, self.cols, self.RS
        wall_c = (238, 230, 214)
        wh = self.wall_h

        def back(s):
            box(s, -0.14, -0.14, R * RS, 0, 0, wh, wall_c)
            box(s, -0.14, -0.14, 0, C * RS, 0, wh, wall_c)
            for gc in range(C):
                a, b = gc * RS + 0.5, gc * RS + RS - 0.5
                poly(s, [(0, a, 44), (0, b, 44), (0, b, 84), (0, a, 84)], (170, 215, 240), (255, 255, 255), 2)
            for gr in range(R):
                a, b = gr * RS + 0.5, gr * RS + RS - 0.5
                poly(s, [(a, 0, 44), (b, 0, 44), (b, 0, 84), (a, 0, 84)], (170, 215, 240), (255, 255, 255), 2)
        objs.append((-9, back))

        T, door = 0.04, 0.9
        g = (RS - door) / 2
        ph = 52
        for gr in range(R):
            for gc in range(C):
                a = self.index_of(gr, gc)
                if gc + 1 < C:
                    b = self.index_of(gr, gc + 1)
                    has = a is not None and b is not None and abs(a - b) == 1
                    r0, c0 = self.origin(gr, gc)
                    x = c0 + RS
                    segs = [(r0, r0 + g), (r0 + RS - g, r0 + RS)] if has else [(r0, r0 + RS)]
                    for u, v in segs:
                        objs.append(((u + v) / 2 + x, lambda s, u=u, v=v, x=x: box(s, u, x - T, v, x + T, 0, ph, wall_c)))
                if gr + 1 < R:
                    b = self.index_of(gr + 1, gc)
                    has = a is not None and b is not None and abs(a - b) == 1
                    r0, c0 = self.origin(gr, gc)
                    y = r0 + RS
                    segs = [(c0, c0 + g), (c0 + RS - g, c0 + RS)] if has else [(c0, c0 + RS)]
                    for u, v in segs:
                        objs.append(((u + v) / 2 + y, lambda s, u=u, v=v, y=y: box(s, y - T, u, y + T, v, 0, ph, wall_c)))

        for gr in range(R):
            for gc in range(C):
                t = self.room_type(gr, gc)
                r0, c0 = self.origin(gr, gc)

                def sr(u0, u1, gr=gr, r0=r0):
                    if gr == 0:
                        return r0 + 0.05 + u0, r0 + 0.05 + u1
                    return r0 + RS - 0.05 - u1, r0 + RS - 0.05 - u0

                def dep(u0, u1, v0, v1, sr=sr, c0=c0):
                    ra, rb = sr(u0, u1)
                    return (ra + rb) / 2 + c0 + (v0 + v1) / 2

                if t == "living":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        flat(s, r0 + 0.7, c0 + 0.5, r0 + 1.3, c0 + 1.5, 0.5, (160, 62, 62), (240, 214, 170))
                        ra, rb = sr(0, 0.18)
                        box(s, ra, c0 + 0.2, rb, c0 + 1.5, 0, 44, (138, 78, 62))
                        ra, rb = sr(0.18, 0.46)
                        box(s, ra, c0 + 0.2, rb, c0 + 1.5, 0, 24, (150, 88, 70))
                    objs.append((dep(0, 0.46, 0.2, 1.5), f))
                elif t == "kitchen":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.38)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.85, 0, 36, (196, 196, 202))
                        ra2, rb2 = sr(0.06, 0.32)
                        flat(s, ra2, c0 + 0.25, rb2, c0 + 0.8, 36, (140, 170, 190), (96, 120, 136))
                        for u, v in [(0.1, 1.2), (0.1, 1.5), (0.26, 1.2), (0.26, 1.5)]:
                            rr = sr(u, u)[0]
                            x, y = P(rr, c0 + v, 36)
                            G.ellipse(s, (40, 40, 44), (x - 8 * zk - 1, y - 4 * zk - 1, 16 * zk + 2, 8 * zk + 2))
                    objs.append((dep(0, 0.38, 0.15, 1.85), f))
                elif t == "bedroom":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.5)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.55, 0, 14, (150, 110, 80))
                        ra, rb = sr(0.03, 0.47)
                        box(s, ra, c0 + 0.19, rb, c0 + 1.51, 14, 26, (238, 238, 244))
                        box(s, ra, c0 + 0.23, rb, c0 + 0.5, 26, 33, (252, 252, 254))
                        flat(s, ra, c0 + 0.7, rb, c0 + 1.5, 26.5, (84, 118, 170), (58, 86, 130))
                    objs.append((dep(0, 0.5, 0.15, 1.55), f))
                elif t == "bath":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.46)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.45, 0, 24, (248, 248, 250))
                        ra2, rb2 = sr(0.07, 0.39)
                        flat(s, ra2, c0 + 0.25, rb2, c0 + 1.35, 24, (120, 190, 226), (170, 176, 184))
                        ra, rb = sr(0, 0.3)
                        box(s, ra, c0 + 1.55, rb, c0 + 1.85, 0, 30, (246, 246, 248))
                    objs.append((dep(0, 0.46, 0.15, 1.85), f))
                elif t == "study":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.42)
                        box(s, ra, c0 + 0.3, rb, c0 + 1.7, 0, 32, (126, 86, 54))
                        ra2, rb2 = sr(0.08, 0.3)
                        box(s, ra2, c0 + 0.85, rb2, c0 + 1.25, 32, 35, (150, 152, 160))
                        box(s, sr(0.04, 0.08)[0], c0 + 0.85, sr(0.04, 0.08)[1], c0 + 1.25, 35, 56, (60, 64, 74))
                    objs.append((dep(0, 0.42, 0.3, 1.7), f))
                elif t == "hall":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        flat(s, r0 + 0.8, c0 + 0.3, r0 + 1.2, c0 + 1.7, 0.5, (86, 120, 100), (214, 196, 150))
                        pr = sr(0.25, 0.25)[0]
                        cylinder(s, pr, c0 + 0.3, 0.13, 0, 18, (160, 100, 60))
                        for dr, dc, h in [(0, 0, 40), (-.07, .05, 30), (.07, -.05, 32)]:
                            x, y = P(pr + dr, c0 + 0.3 + dc, h)
                            G.circle(s, (46, 128, 60), (x, y), 12 * zk + 2)
                    objs.append((dep(0.1, 0.4, 0.3, 0.3), f))
                else:
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.45)
                        box(s, ra, c0 + 0.2, rb, c0 + 0.8, 0, 30, (170, 130, 80))
                        box(s, ra, c0 + 1.0, rb, c0 + 1.5, 0, 22, (150, 110, 70))
                    objs.append((dep(0, 0.45, 0.2, 1.5), f))
        objs.sort(key=lambda t: t[0])
        self.objs = objs


class BigCard:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.n = 0
        self.rx = None
        self.dirt = []
        self.alpha = 1.0

    def layout(self, n):
        r = self.rect
        sq = min(40, (r.w - 20 - (n - 1) * 6) / n)
        total = n * sq + (n - 1) * 6
        x0 = r.x + (r.w - total) / 2
        return sq, x0

    def update(self, state, dt, on):
        if state is None:
            return
        n = len(state) - 1
        if n != self.n:
            self.n, self.rx, self.dirt = n, None, [1.0 if v == "D" else 0.0 for v in state[1:]]
        sq, x0 = self.layout(n)
        tx = x0 + state[0] * (sq + 6) + sq / 2
        self.rx = tx if self.rx is None else sm(self.rx, tx, 12, dt)
        for i in range(n):
            self.dirt[i] = sm(self.dirt[i], 1.0 if state[1 + i] == "D" else 0.0, 12, dt)
        self.alpha = sm(self.alpha, 1.0 if on else 0.22, 9, dt)

    def draw(self, s, label, border, state):
        r = self.rect
        a = self.alpha
        fd = lambda c: mix(PANEL, c, a)
        G.rect(s, fd((24, 30, 48)), r, border_radius=12)
        G.rect(s, fd(border), r, 2, border_radius=12)
        text(s, label, font("segoeui", 12, True), fd(border), (r.x + 10, r.y + 4))
        if state is None or not self.dirt:
            return
        n = len(state) - 1
        sq, x0 = self.layout(n)
        top = r.y + 20
        for i in range(n):
            x = x0 + i * (sq + 6)
            col = mix(CLEAN, DIRTY, self.dirt[i])
            G.rect(s, fd(col), (x, top, sq, 30), border_radius=7)
            if self.dirt[i] > 0.5:
                for dx, dy in ((0.28, 0.35), (0.6, 0.55), (0.42, 0.72)):
                    G.circle(s, fd((60, 44, 30)), (x + sq * dx, top + 30 * dy), 2.6)
            else:
                G.lines(s, fd((230, 255, 236)), False, [(x + sq * 0.3, top + 15), (x + sq * 0.45, top + 22), (x + sq * 0.72, top + 8)], 2.5)
            text(s, letter(i), font("segoeui", 12, True), fd(MUTED), (x + sq / 2, top + 33), "midtop")
        cx = self.rx
        G.circle(s, fd((18, 18, 22)), (cx, top + 15), 11)
        G.circle(s, fd((96, 96, 108)), (cx, top + 15), 11, 2)
        G.circle(s, fd(ORANGE), (cx, top + 15), 3.5)


MINI = {}


def mini_state(state, w, h):
    pw, ph = max(8, round(w * SC)), max(8, round(h * SC))
    key = (state, pw, ph)
    if key in MINI:
        return MINI[key]
    s = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(s, (26, 33, 52), (0, 0, pw, ph), border_radius=max(4, ph // 6))
    n = len(state) - 1
    pad, gap = max(3, pw // 20), max(1, pw // 60)
    sw = (pw - 2 * pad - (n - 1) * gap) / n
    sh, top = ph * 0.46, ph * 0.12
    rr = max(2, ph // 12)
    for i in range(n):
        x = pad + i * (sw + gap)
        dirty = state[1 + i] == "D"
        rect = pygame.Rect(round(x), round(top), round(sw), round(sh))
        pygame.draw.rect(s, DIRTY if dirty else CLEAN, rect, border_radius=rr)
        if dirty:
            for dx, dy in ((0.3, 0.35), (0.65, 0.5), (0.42, 0.75)):
                pygame.draw.circle(s, (60, 44, 30), (x + sw * dx, top + sh * dy), max(1, sh * 0.09))
        else:
            pygame.draw.lines(s, (230, 255, 236), False, [(x + sw * 0.28, top + sh * 0.5), (x + sw * 0.45, top + sh * 0.72),
                                                          (x + sw * 0.74, top + sh * 0.28)], max(1, ph // 20))
    cx, cy = pad + state[0] * (sw + gap) + sw / 2, top + sh / 2
    rad = min(sw, sh) * 0.38
    pygame.draw.circle(s, (18, 18, 22), (cx, cy), rad)
    pygame.draw.circle(s, (96, 96, 108), (cx, cy), rad, max(1, ph // 24))
    pygame.draw.circle(s, ORANGE, (cx, cy), max(1, rad * 0.32))
    f = pfont("consolas", max(8, int(ph * 0.25)), True)
    t = f.render(letter(state[0]) + " " + "".join(state[1:]), True, (190, 200, 222))
    s.blit(t, t.get_rect(midbottom=(pw // 2, ph - max(1, ph // 14))))
    MINI[key] = s
    return s


def blit_state(dst, state, cx, cy, w, h, scale=1.0, alpha=1.0):
    img = mini_state(state, w, h)
    owned = False
    if abs(scale - 1) > 0.02:
        img = pygame.transform.smoothscale(img, (max(2, int(img.get_width() * scale)), max(2, int(img.get_height() * scale))))
        owned = True
    if alpha < 0.98:
        if not owned:
            img = img.copy()
        img.set_alpha(int(255 * max(0, alpha)))
    dst.blit(img, img.get_rect(center=(round(cx * SC), round(cy * SC))))
    k = scale if owned else 1.0
    return pygame.Rect(round(cx - w * k / 2), round(cy - h * k / 2), round(w * k), round(h * k))


PRESETS = [
    ("2 phòng", 2, 0, "DD", 1),
    ("3 phòng", 3, 0, "DDD", 2),
    ("4 phòng", 4, 1, "DCDD", 3),
    ("6 phòng", 6, 2, "DDCDDD", 5),
]


class App:
    def __init__(self):
        pygame.init()
        info = pygame.display.get_desktop_sizes()[0]
        sc = 0.82 * min((info[0] - 40) / W, (info[1] - 110) / H)
        self.win = pygame.display.set_mode((int(W * sc), int(H * sc)), pygame.RESIZABLE)
        pygame.display.set_caption("Robot hút bụi nhiều phòng - BFS / DFS")
        self.canvas = None
        self.fullscreen, self.win_size = False, self.win.get_size()
        self.clock = pygame.time.Clock()
        self.mouse = (0, 0)
        self.speed_i = 2
        self.algo = "bfs"
        self.preset = 0
        self.toast = ("", 0.0)
        self.scene = Scene()
        self.acc = list(ALGO_COL["bfs"])
        self.algo_rects = {"bfs": pygame.Rect(464, 16, 214, 52), "dfs": pygame.Rect(686, 16, 214, 52)}
        self.sw_x = float(self.algo_rects["bfs"].x)
        self.node_card = BigCard((INFO.x + 12, INFO.y + 28, INFO.w - 24, 64))
        self.child_card = BigCard((INFO.x + 12, INFO.y + 130, INFO.w - 24, 64))
        self.editing = False
        self.replay = None
        self.cap_text, self.cap_age = "", 0.0
        self.build_buttons()
        self.apply_scale()
        self.load_preset(0)

    def build_buttons(self):
        self.buttons = []
        bx = 12
        for w, label, key in [(80, "Về đầu", "reset"), (70, "Lùi", "back"), (96, "Phát", "play"),
                              (70, "Tiếp", "next"), (100, "Node kế", "node"), (38, "−", "slow"), (38, "+", "fast")]:
            self.buttons.append(Button((bx, 886, w, 40), label, key))
            bx += w + 8
            if key == "slow":
                bx += 56
        self.speed_x = [b for b in self.buttons if b.key == "slow"][0].rect.right + 6
        bx = 640
        for i, (lab, *_r) in enumerate(PRESETS):
            self.buttons.append(Button((bx, 886, 82, 40), lab, f"p{i}"))
            bx += 90
        self.buttons.append(Button((bx, 886, 92, 40), "Tự đặt", "edit"))
        self.buttons.append(Button((bx + 100, 886, 112, 40), "Ngẫu nhiên", "rand"))
        self.buttons.append(Button((bx + 220, 886, 150, 40), "Chạy lời giải", "replay"))

    def apply_scale(self):
        global SC
        ww, wh = self.win.get_size()
        sc = max(0.3, min(ww / W, wh / H))
        if self.canvas is not None and abs(sc - SC) < 0.003 and self.canvas.get_size() == (round(W * SC), round(H * SC)):
            return
        SC = sc
        self.canvas = pygame.Surface((round(W * SC), round(H * SC)))
        MINI.clear()
        self.scene.bg = None
        self.build_code()

    def build_code(self):
        self.lines = []
        f = font("consolas", 13)
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
            bright = pygame.Surface((round((CODE_R.w - 56) * SC), round(24 * SC)), pygame.SRCALPHA)
            dim = pygame.Surface((round((CODE_R.w - 56) * SC), round(24 * SC)), pygame.SRCALPHA)
            x = 0
            for s, col in segs:
                bright.blit(f.render(s, True, col), (x, round(2 * SC)))
                dim.blit(f.render(s, True, shade(col, 0.5)), (x, round(2 * SC)))
                x += f.size(s)[0]
            self.lines.append((bright, dim))
        self.bar_y = getattr(self, "bar_y", CODE_R.y + 36.0)

    @property
    def presets(self):
        return PRESETS

    def load_preset(self, i):
        lab, n, pos, dirt, gpos = PRESETS[i]
        self.preset = i
        self.load(n, make_state(pos, [c == "D" for c in dirt]), make_goal(n, gpos))

    def load(self, n, init, goal):
        self.n, self.init, self.goal = n, init, goal
        self.card_w = max(76, 16 * n + 16)
        self.card_h = 50
        if self.scene.n != n or self.scene.bg is None:
            if self.scene.n != n:
                self.scene.cfg(n)
        self.rec = Rec(init, goal, self.algo)
        self.events = self.rec.events
        self.ev_i, self.ev_t = 0, 0.0
        self.playing, self.one = False, False
        self.anim_tab, self.anim_q, self.anim_e = {}, {}, {}
        self.scroll = 0.0
        self.lamps = [[70, 80, 100], [70, 80, 100]]
        self.banner_key, self.banner_age = None, 1.0
        self.layout_tn = -1
        self.replay = None
        self.node_card.n = self.child_card.n = 0
        self.node_card.rx = self.child_card.rx = None
        self.s_pos = float(init[0])
        self.s_dirt = [1.0 if v == "D" else 0.0 for v in init[1:]]
        self.s_theta = 0.0
        self.spin = 0.0
        self.particles = []
        self.qmax = max(4, int((W - 24 - QX - 40) // (self.card_w + 10)))
        self.qp = self.card_w + 10

    @property
    def ev(self):
        return self.events[self.ev_i]

    def speed(self):
        return SPEEDS[self.speed_i]

    def seek(self, i):
        self.ev_i = max(0, min(len(self.events) - 1, i))
        self.ev_t = 0.0
        self.one = False

    def set_algo(self, algo):
        if algo == self.algo:
            return
        self.playing = False
        self.algo = algo
        self.build_code()
        self.load(self.n, self.init, self.goal)

    def press(self, key):
        last = len(self.events) - 1
        if key == "play":
            self.replay = None
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
            while j < last and self.events[j]["line"] != 8:
                j += 1
            self.ev_i, self.ev_t, self.one = min(j, last), 0.0, True
        elif key == "reset":
            self.playing = False
            self.replay = None
            self.seek(0)
        elif key == "slow":
            self.speed_i = max(0, self.speed_i - 1)
        elif key == "fast":
            self.speed_i = min(len(SPEEDS) - 1, self.speed_i + 1)
        elif key in ("alg_bfs", "alg_dfs"):
            self.set_algo(key[4:])
        elif key.startswith("p") and key[1:].isdigit():
            self.load_preset(int(key[1:]))
        elif key == "rand":
            n = random.randint(2, 6)
            dirt = [random.random() < 0.6 for _ in range(n)]
            if not any(dirt):
                dirt[random.randrange(n)] = True
            self.preset = -1
            self.load(n, make_state(random.randrange(n), dirt), make_goal(n, random.randrange(n)))
        elif key == "edit":
            self.open_editor()
        elif key == "replay":
            self.start_replay()

    def start_replay(self):
        if not self.rec.solution:
            self.toast = ("Chưa có lời giải: hãy chạy thuật toán đến khi tìm thấy đích.", 3.0)
            return
        if self.replay:
            self.replay = None
            return
        states = [self.rec.nodes[e]["state"] for e in self.rec.path]
        self.playing = False
        self.seek(len(self.events) - 1)
        self.replay = dict(states=states, t=0.0, step=1.2)

    MOD = pygame.Rect(320, 210, 760, 520)

    def open_editor(self):
        self.playing = False
        self.replay = None
        self.editing = True
        n = self.n
        self.ed = dict(n=n, pos=self.init[0], dirt=[v == "D" for v in self.init[1:]], gpos=self.goal[0])
        mx, my = self.MOD.x, self.MOD.y
        self.ed_buttons = [
            Button((mx + 40, my + 72, 40, 36), "−", "ed_minus"),
            Button((mx + 200, my + 72, 40, 36), "+", "ed_plus"),
            Button((self.MOD.right - 40 - 230, self.MOD.bottom - 62, 110, 42), "Hủy", "ed_cancel"),
            Button((self.MOD.right - 40 - 112, self.MOD.bottom - 62, 112, 42), "Áp dụng", "ed_apply"),
        ]

    def ed_col(self, i):
        n = self.ed["n"]
        w = (self.MOD.w - 80) / n
        return self.MOD.x + 40 + i * w, w

    def editor_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.editing = False
            elif e.key == pygame.K_RETURN:
                self.press_ed("ed_apply")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            m = self.to_canvas(e.pos)
            for b in self.ed_buttons:
                if b.rect.collidepoint(m):
                    self.press_ed(b.key)
                    return
            n = self.ed["n"]
            M = self.MOD
            for i in range(n):
                x, w = self.ed_col(i)
                if pygame.Rect(x + 6, M.y + 150, w - 12, 34).collidepoint(m):
                    self.ed["pos"] = i
                if pygame.Rect(x + 6, M.y + 224, w - 12, 84).collidepoint(m):
                    self.ed["dirt"][i] = not self.ed["dirt"][i]
                if pygame.Rect(x + 6, M.y + 350, w - 12, 34).collidepoint(m):
                    self.ed["gpos"] = i

    def press_ed(self, key):
        ed = self.ed
        if key == "ed_cancel":
            self.editing = False
        elif key in ("ed_minus", "ed_plus"):
            n = max(2, min(6, ed["n"] + (1 if key == "ed_plus" else -1)))
            if n != ed["n"]:
                d = ed["dirt"][:n] + [True] * max(0, n - len(ed["dirt"]))
                ed.update(n=n, dirt=d, pos=min(ed["pos"], n - 1), gpos=min(ed["gpos"], n - 1) if ed["gpos"] < ed["n"] - 1 else n - 1)
        elif key == "ed_apply":
            self.editing = False
            self.preset = -1
            self.load(ed["n"], make_state(ed["pos"], ed["dirt"]), make_goal(ed["n"], ed["gpos"]))

    def draw_editor(self, s):
        veil = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        veil.fill((4, 6, 12, 195))
        s.blit(veil, (0, 0))
        M, ed = self.MOD, self.ed
        G.rect(s, (22, 29, 46), M, border_radius=18)
        G.rect(s, ACC_NOW, M, 2, border_radius=18)
        text(s, "Tự đặt phòng, bụi, robot và đích", font("segoeui", 22, True), TEXT, (M.x + 40, M.y + 16))
        text(s, "Số phòng", font("segoeui", 14, True), MUTED, (M.x + 40, M.y + 52))
        text(s, str(ed["n"]), font("segoeui", 26, True), ACC_NOW, (M.x + 160, M.y + 90), "center")
        text(s, "Bấm vào ô để chọn. Hàng giữa: bấm để bật / tắt bụi.", font("segoeui", 14), MUTED, (M.x + 280, M.y + 82))
        rows = [("Robot bắt đầu ở phòng", M.y + 128), ("Phòng nào đang bẩn (D)?", M.y + 196), ("Đích: robot phải dừng ở phòng", M.y + 330)]
        for lab, y in rows:
            text(s, lab, font("segoeui", 15, True), TEXT, (M.x + 40, y))
        for i in range(ed["n"]):
            x, w = self.ed_col(i)
            r1 = pygame.Rect(x + 6, M.y + 150, w - 12, 34)
            G.rect(s, ORANGE if ed["pos"] == i else PANEL_L, r1, border_radius=8)
            text(s, f"Phòng {letter(i)}", font("segoeui", 14, True), (20, 20, 26) if ed["pos"] == i else TEXT, r1.center, "center")
            r2 = pygame.Rect(x + 6, M.y + 224, w - 12, 84)
            dirty = ed["dirt"][i]
            G.rect(s, DIRTY if dirty else CLEAN, r2, border_radius=10)
            if dirty:
                for dx, dy in ((0.25, 0.3), (0.6, 0.5), (0.4, 0.75), (0.75, 0.25)):
                    G.circle(s, (60, 44, 30), (r2.x + r2.w * dx, r2.y + r2.h * dy), 5)
            text(s, f"{letter(i)}: " + ("D (bẩn)" if dirty else "C (sạch)"), font("segoeui", 14, True), (255, 255, 255),
                 (r2.centerx, r2.bottom - 6), "midbottom")
            if ed["pos"] == i:
                G.circle(s, (18, 18, 22), (r2.centerx, r2.y + 28), 15)
                G.circle(s, ORANGE, (r2.centerx, r2.y + 28), 5)
            r3 = pygame.Rect(x + 6, M.y + 350, w - 12, 34)
            G.rect(s, GREEN if ed["gpos"] == i else PANEL_L, r3, border_radius=8)
            text(s, f"Phòng {letter(i)}", font("segoeui", 14, True), (10, 30, 20) if ed["gpos"] == i else TEXT, r3.center, "center")
        n = ed["n"]
        info = f"Không gian trạng thái: {n} × 2^{n} = {n * 2 ** n} trạng thái. Đích: robot ở phòng {letter(ed['gpos'])}, mọi phòng sạch (C)."
        text(s, info, font("segoeui", 14), MUTED, (M.x + 40, M.y + 410))
        for b in self.ed_buttons:
            b.active = b.key == "ed_apply"
            b.draw(s, self.mouse)

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
        ev = self.ev
        if self.replay:
            rp = self.replay
            rp["t"] += dt * min(3.0, max(1.0, self.speed()))
            k = min(len(rp["states"]) - 1, int(rp["t"] / rp["step"]))
            scene_state = rp["states"][k]
            rp["k"] = k
            if k >= len(rp["states"]) - 1 and rp["t"] > (len(rp["states"]) - 1) * rp["step"] + 1.4:
                self.replay = None
        else:
            scene_state = ev["node_state"]
        self.update_scene(scene_state, dt)
        self.node_card.update(ev["node_state"], dt, True)
        ch = ev["child"]
        self.child_card.update(ch[0] if ch else self.child_card_state(), dt, bool(ch))
        self.child_state_cache = ch[0] if ch else getattr(self, "child_state_cache", None)
        for k in range(2):
            g = ev["gate"][k]
            t = (84, 96, 120) if g is None else (RED if g else GREEN)
            self.lamps[k] = [sm(self.lamps[k][j], t[j], 12, dt) for j in range(3)]
        key = (ev["verdict"], ch[2] if ch else None)
        if key != self.banner_key:
            self.banner_key, self.banner_age = key, 0.0
        self.banner_age += dt
        if ev["cap"] != self.cap_text:
            self.cap_text, self.cap_age = ev["cap"], 0.0
        self.cap_age += dt
        self.bar_y = sm(self.bar_y, CODE_R.y + 36 + ev["line"] * LH, 30, dt)
        self.update_table(dt)
        self.update_queue(dt)
        self.update_explored(dt)

    def child_card_state(self):
        return getattr(self, "child_state_cache", None) or self.ev["node_state"]

    def update_scene(self, state, dt):
        sc = self.scene
        target = float(state[0])
        old = self.s_pos
        self.s_pos = sm(self.s_pos, target, 5, dt)
        a, b = sc.pos_at(old), sc.pos_at(self.s_pos)
        dr, dc = b[0] - a[0], b[1] - a[1]
        if math.hypot(dr, dc) > 0.004:
            tgt = math.atan2(dc, dr)
            diff = (tgt - self.s_theta + math.pi) % (2 * math.pi) - math.pi
            self.s_theta += diff * min(1.0, dt * 10)
        sucking = False
        for i in range(self.n):
            tv = 1.0 if state[1 + i] == "D" else 0.0
            nv = sm(self.s_dirt[i], tv, 4, dt)
            if tv == 0.0 and self.s_dirt[i] > 0.04 and abs(self.s_pos - i) < 0.6:
                sucking = True
            self.s_dirt[i] = nv
        moving = abs(target - self.s_pos) > 0.05
        self.spin += dt * (720 if (sucking or moving) else 120)
        self.sucking = sucking
        if sucking and random.random() < 0.7:
            rc, cc = sc.pos_at(self.s_pos)
            self.particles.append([rc + random.uniform(-0.5, 0.5), cc + random.uniform(-0.5, 0.5), random.uniform(6, 20), 0.0])
        for p in self.particles[:]:
            p[3] += dt * 2.4
            if p[3] > 0.45:
                self.particles.remove(p)

    def compute_layout(self, tn):
        nodes = self.rec.nodes
        gap = 8
        cols = max(1, int((TAB.w - 28 + gap) // (self.card_w + gap)))
        by = {}
        for eid in range(tn):
            by.setdefault(nodes[eid]["depth"], []).append(eid)
        pos, heads, y = {}, [], 0
        for d in sorted(by):
            heads.append((d, y, len(by[d])))
            y += 24
            for k, eid in enumerate(by[d]):
                pos[eid] = (14 + (k % cols) * (self.card_w + gap), y + (k // cols) * (self.card_h + gap))
            y += ((len(by[d]) - 1) // cols + 1) * (self.card_h + gap) + 6
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
        cb = self.child_card.rect.center
        for eid in list(self.anim_tab):
            if eid >= tn:
                del self.anim_tab[eid]
        for eid, (x, y) in self.tpos.items():
            a = self.anim_tab.get(eid)
            if a is None:
                a = self.anim_tab[eid] = [cb[0] - TAB.x - self.card_w / 2, cb[1] - TAB.y - 36 + self.scroll - self.card_h / 2, 0.35, 0.0]
            a[0], a[1] = sm(a[0], x, 7, dt), sm(a[1], y, 7, dt)
            a[2], a[3] = sm(a[2], 1.0, 7, dt), sm(a[3], 1.0, 9, dt)

    def update_queue(self, dt):
        ev = self.ev
        fr = ev["frontier"]
        cb = self.child_card.rect.center
        nb = self.node_card.rect.center
        for eid in list(self.anim_q):
            if eid >= ev["tn"]:
                del self.anim_q[eid]
        offset = max(0, len(fr) - self.qmax) if self.algo == "dfs" else 0
        for i, eid in enumerate(fr):
            a = self.anim_q.get(eid)
            if a is None:
                a = self.anim_q[eid] = [cb[0], cb[1], 0.4, 0.0, False]
            a[4] = False
            idx = i - offset
            show = 0 <= idx < self.qmax
            a[0] = sm(a[0], QX + idx * self.qp + self.card_w / 2, 8, dt)
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
        nb = self.node_card.rect.center
        cap = max(4, int((W - 24 - QX - 40) // self.card_w))
        start = max(0, len(ex) - cap)
        for eid in list(self.anim_e):
            if eid not in ex:
                del self.anim_e[eid]
        for i, eid in enumerate(ex):
            a = self.anim_e.get(eid)
            if a is None:
                a = self.anim_e[eid] = [nb[0], nb[1], 0.5, 0.0]
            idx = i - start
            a[0] = sm(a[0], QX + idx * self.card_w + self.card_w / 2, 8, dt)
            a[1] = sm(a[1], E_Y + 36, 8, dt)
            a[2] = sm(a[2], 1.0, 8, dt)
            a[3] = sm(a[3], 1.0 if idx >= 0 else 0.0, 8, dt)

    def draw(self):
        s = self.canvas
        s.fill(BG)
        ev = self.ev
        p = min(1.0, self.ev_t / ev["dur"]) if ev["dur"] else 1.0
        self.draw_scene(s, ev, p)
        self.draw_info(s, ev, p)
        self.draw_code(s, ev)
        self.draw_table(s, ev, p)
        self.draw_header(s, ev)
        self.draw_queue(s, ev, p)
        self.draw_explored(s, ev)
        self.draw_controls(s)
        if self.toast[1] > 0:
            a = min(1.0, self.toast[1] / 0.5)
            r = pygame.Rect(0, 0, 520, 34)
            r.midbottom = (TAB.centerx, TAB.bottom - 12)
            G.rect(s, (60, 40, 18), r, border_radius=17)
            G.rect(s, ORANGE, r, 2, border_radius=17)
            text(s, self.toast[0], font("segoeui", 13), ORANGE, r.center, "center", alpha=a)
        if self.editing:
            self.draw_editor(s)

    def draw_header(self, s, ev):
        acc = tuple(int(v) for v in self.acc)
        text(s, ALGO_INFO[self.algo][3], font("segoeui", 28, True), acc, (16, 10))
        text(s, f"Robot hút bụi · {self.n} phòng", font("segoeui", 15), MUTED, (18, 50))
        chips = [("Đã mở", len(ev["explored"]), ORANGE), ("Frontier", len(ev["frontier"]), BLUE),
                 ("Nút sinh ra", ev["tn"], CYAN), ("Độ sâu", ev["node_depth"], GOLD)]
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
        text(s, "Đích", font("segoeui", 14, True), GREEN, (x - 8, 30), "midright")
        text(s, f"robot ở {letter(self.goal[0])}, sạch hết", font("segoeui", 13), TEXT, (x - 8, 50), "midright")
        cont = pygame.Rect(458, 10, 448, 64)
        G.rect(s, (16, 21, 34), cont, border_radius=18)
        G.rect(s, PANEL_L, cont, 1, border_radius=18)
        pill = pygame.Rect(round(self.sw_x), 16, 214, 52)
        G.rect(s, shade(acc, 0.35), pill.inflate(8, 8), border_radius=18)
        G.rect(s, acc, pill, border_radius=14)
        for key, r in self.algo_rects.items():
            name, l1, l2, _ = ALGO_INFO[key]
            on = key == self.algo
            col = (10, 22, 30) if on else (TEXT if r.collidepoint(self.mouse) else MUTED)
            text(s, name, font("segoeui", 26, True), col, (r.x + 18, r.centery), "midleft")
            text(s, l1, font("segoeui", 13, True), col, (r.x + 90, r.centery - 9), "midleft")
            text(s, l2, font("segoeui", 12), col, (r.x + 90, r.centery + 9), "midleft")

    def draw_scene(self, s, ev, p):
        sc = self.scene
        if sc.bg is None:
            surf = pygame.Surface(s.get_size())
            sc.build_bg(surf)
        if sc.objs is None:
            sc.build_objs()
        rp = _r(SCENE)
        s.blit(sc.bg, rp.topleft, rp)
        clip = s.get_clip()
        setclip(s, SCENE)
        for i in range(self.n):
            gr, gc = sc.cell_of(i)
            r0, c0 = sc.origin(gr, gc)
            cl = 1 - self.s_dirt[i]
            if cl > 0.02:
                alpha_poly(s, [P(r0, c0), P(r0, c0 + sc.RS), P(r0 + sc.RS, c0 + sc.RS), P(r0 + sc.RS, c0)], (255, 255, 255, int(46 * cl)))
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260)
        for i in range(self.n):
            d = self.s_dirt[i]
            if d < 0.03:
                continue
            rc, cc = sc.center(i)
            rnd = random.Random(i * 31 + 7)
            for _ in range(9):
                dr, dc = rnd.uniform(-0.62, 0.62), rnd.uniform(-0.62, 0.62)
                x, y = P(rc + dr * d, cc + dc * d)
                rw, rh = (6 + rnd.random() * 5) * ISO["ZK"] * 1.5 * d + 1, (4 + rnd.random() * 3) * ISO["ZK"] * 1.5 * d + 1
                G.ellipse(s, (30, 26, 24), (x - rw - 1, y - rh - 1, rw * 2 + 2, rh * 2 + 2))
                G.ellipse(s, (96, 86, 78), (x - rw, y - rh, rw * 2, rh * 2))
                G.ellipse(s, (170, 160, 148), (x - rw * .6, y - rh * .8, rw * 1.1, rh * .8))
            ring = [P(rc + 0.78 * (1 + 0.05 * pulse) * d * math.cos(a), cc + 0.78 * (1 + 0.05 * pulse) * d * math.sin(a))
                    for a in [2 * math.pi * k / 30 for k in range(30)]]
            G.polygon(s, (255, 226, 110), ring, 3)
        rc, cc = sc.pos_at(self.s_pos)
        rd = rc + cc
        rad = 0.44
        drawn = False
        for depth, fn in sc.objs:
            if not drawn and depth >= rd:
                draw_robot(s, rc, cc, self.s_theta, self.spin, rad, self.sucking)
                drawn = True
            fn(s)
        if not drawn:
            draw_robot(s, rc, cc, self.s_theta, self.spin, rad, self.sucking)
        # nhãn phòng
        for i in range(self.n):
            gr, gc = sc.cell_of(i)
            r0, c0 = sc.origin(gr, gc)
            x, y = P(r0 + sc.RS - 0.28, c0 + 0.36)
            on = abs(self.s_pos - i) < 0.5
            r = pygame.Rect(x - 13, y - 10, 26, 20)
            G.rect(s, ACC_NOW if on else (30, 38, 58), r, border_radius=6)
            text(s, letter(i), font("segoeui", 14, True), (10, 22, 30) if on else TEXT, r.center, "center")
        for pr, pc, z, age in self.particles:
            x0, y0 = P(pr, pc, z)
            x1, y1 = P(rc, cc, 18)
            t = age / 0.45
            G.circle(s, (170, 162, 152), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), 3)
        ch = ev["child"]
        if ch and not self.replay:
            a_idx, b_idx = ev["node_state"][0], ch[0][0]
            if a_idx != b_idx:
                a, b = sc.center(a_idx), sc.center(b_idx)
                for k in range(9):
                    t0 = k / 9
                    t1 = t0 + 0.05
                    G.line(s, ACC_NOW, P(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, 2),
                           P(a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1, 2), 4)
                hx, hy = P(b[0], b[1], 2)
                G.circle(s, ACC_NOW, (hx, hy), 7)
            else:
                rc2, cc2 = sc.center(a_idx)
                ring = [P(rc2 + 0.9 * math.cos(a), cc2 + 0.9 * math.sin(a), 2) for a in [2 * math.pi * k / 30 for k in range(30)]]
                G.polygon(s, ACC_NOW, ring, 3)
            tx, ty = P(*sc.center(b_idx), 70)
            chip = pygame.Rect(tx - 44, ty - 14, 88, 26)
            G.rect(s, shade(ACC_NOW, 0.3), chip, border_radius=13)
            G.rect(s, ACC_NOW, chip, 2, border_radius=13)
            text(s, ev["act"], font("segoeui", 14, True), ACC_NOW, chip.center, "center")
        s.set_clip(clip)
        G.rect(s, PANEL_L, SCENE, 1, border_radius=14)
        text(s, "ngôi nhà (mỗi phòng là một ô của bài toán)", font("segoeui", 14, True), GOLD, (SCENE.x + 14, SCENE.y + 8))
        if self.replay:
            k = self.replay.get("k", 0)
            n = len(self.replay["states"]) - 1
            act = self.rec.solution[k - 1] if k >= 1 else "bắt đầu"
            chip = pygame.Rect(SCENE.x + 12, SCENE.bottom - 40, 330, 28)
            G.rect(s, (10, 30, 20), chip, border_radius=14)
            G.rect(s, GREEN, chip, 2, border_radius=14)
            text(s, f"Robot chạy lời giải: bước {k}/{n} · {act}", font("segoeui", 14, True), GREEN, chip.center, "center")

    def draw_info(self, s, ev, p):
        r = INFO
        panel(s, r, "nút đang xét", ORANGE)
        nc, cc = self.node_card, self.child_card
        vb = ev["verdict"]
        nstate = ev["node_state"]
        text(s, f"độ sâu {ev['node_depth']}", font("segoeui", 12), MUTED, (r.right - 14, r.y + 12), "topright")
        nc.draw(s, "node", ORANGE, nstate)
        ay = nc.rect.bottom + 6
        if ev["act"]:
            chip = pygame.Rect(0, 0, 160, 22)
            chip.midtop = (r.centerx, ay)
            G.rect(s, shade(ACC_NOW, 0.3), chip, border_radius=11)
            G.rect(s, ACC_NOW, chip, 2, border_radius=11)
            text(s, {"Suck": "↓ Suck (hút bụi)", "Left": "← Left", "Right": "Right →"}[ev["act"]], font("segoeui", 14, True),
                 ACC_NOW, chip.center, "center")
        border = {None: CYAN, "ok": GREEN, "dup": RED, "goal": GOLD, "queued": GREEN}[vb]
        cstate = ev["child"][0] if ev["child"] else self.child_card_state()
        cc.draw(s, "child", border, cstate)
        if vb == "dup" and ev["child"]:
            flash = pygame.Surface((round(cc.rect.w * SC), round(cc.rect.h * SC)), pygame.SRCALPHA)
            flash.fill((255, 98, 112, int(70 * (0.5 + 0.5 * math.sin(p * 12)))))
            s.blit(flash, (round(cc.rect.x * SC), round(cc.rect.y * SC)))
        gy = cc.rect.bottom + 8
        for k, label in enumerate(("child in explored ?", "in_frontier ?")):
            y = gy + k * 22
            col = tuple(int(v) for v in self.lamps[k])
            G.circle(s, shade(col, 0.4), (r.x + 26, y + 10), 9)
            G.circle(s, col, (r.x + 26, y + 10), 6)
            text(s, label, font("consolas", 12), TEXT, (r.x + 44, y + 3))
            g = ev["gate"][k]
            text(s, "?" if g is None else ("CÓ" if g else "KHÔNG"), font("segoeui", 13, True), col, (r.right - 16, y + 2), "topright")
        msg = {None: "", "ok": "Nút mới → xét tiếp", "dup": "Trùng → BỎ", "goal": "ĐÍCH!",
               "queued": "Vào ngăn xếp" if self.algo == "dfs" else "Vào hàng đợi"}[vb]
        if vb:
            col = {"ok": GREEN, "dup": RED, "goal": GOLD, "queued": GREEN}[vb]
            ease = 1 - (1 - min(1.0, self.banner_age / 0.3)) ** 3
            b = pygame.Rect(0, 0, int(240 * (0.6 + 0.4 * ease)), 28)
            b.midtop = (r.centerx, gy + 48)
            G.rect(s, shade(col, 0.28), b, border_radius=14)
            G.rect(s, col, b, 2, border_radius=14)
            text(s, msg, font("segoeui", 15, True), col, b.center, "center", alpha=ease)

    def draw_code(self, s, ev):
        rect = CODE_R
        acc = tuple(int(v) for v in self.acc)
        panel(s, rect, f"mã nguồn  {self.algo.upper()}(problem)", acc)
        G.rect(s, shade(acc, 0.6), rect, 2, border_radius=14)
        top = rect.y + 36
        G.rect(s, (24, 32, 52), (rect.x + 8, self.bar_y, rect.w - 16, LH), border_radius=6)
        glow = pygame.Surface((round((rect.w - 16) * SC), round(LH * SC)), pygame.SRCALPHA)
        glow.fill((*acc, 40))
        s.blit(glow, (round((rect.x + 8) * SC), round(self.bar_y * SC)))
        G.rect(s, acc, (rect.x + 8, self.bar_y, 4, LH), border_radius=2)
        f = font("consolas", 13)
        for i, (bright, dim) in enumerate(self.lines):
            y = top + i * LH
            act = i == ev["line"]
            text(s, str(i + 1), f, acc if act else (70, 82, 110), (rect.x + 34, y + 4), "topright")
            s.blit(bright if act else dim, (round((rect.x + 46) * SC), round((y - 2) * SC)))
        text(s, f"dòng {ev['line'] + 1} · sự kiện {self.ev_i + 1}/{len(self.events)}", font("segoeui", 13), MUTED,
             (rect.right - 14, rect.y + 12), "topright")
        cap = pygame.Rect(rect.x + 10, rect.bottom - 72, rect.w - 20, 62)
        G.rect(s, (14, 20, 34), cap, border_radius=10)
        G.rect(s, PANEL_L, cap, 1, border_radius=10)
        a = min(1.0, self.cap_age / 0.25)
        fc = font("segoeui", 15)
        for k, line in enumerate(wrap(self.cap_text, fc, cap.w - 24)[:3]):
            text(s, line, fc, TEXT, (cap.x + 12, cap.y + 7 + k * 17), alpha=a)

    def draw_table(self, s, ev, p):
        panel(s, TAB, "bảng NODE theo độ sâu  (mỗi thẻ = một trạng thái [vị trí robot, các phòng])", GOLD)
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
            cx, cy = TAB.x + x + self.card_w / 2, oy + y + self.card_h / 2
            if cy < view.y - self.card_h or cy > view.bottom + self.card_h:
                continue
            if ev["path"] and eid in ev["path"]:
                col, bw, dim = GOLD, 3, 1.0
            elif eid == ev["node_eid"]:
                col, bw, dim = mix(ORANGE, (255, 240, 200), pulse * 0.6), 3, 1.0
            elif eid in ex:
                col, bw, dim = (70, 82, 112), 1, 0.55
            elif eid in fr:
                col, bw, dim = BLUE, 2, 1.0
            else:
                col, bw, dim = (70, 82, 112), 1, 1.0
            r = blit_state(s, nodes[eid]["state"], cx, cy, self.card_w, self.card_h, sc, al * (0.5 + 0.5 * dim))
            if eid == ev["match"]:
                col = RED
            G.rect(s, col, r.inflate(2, 2), bw, border_radius=8)
        ne = ev["node_eid"]
        if ne is not None and ne in self.anim_tab and nodes[ne]["parent"] in self.anim_tab:
            a, b = self.anim_tab[ne], self.anim_tab[nodes[ne]["parent"]]
            G.line(s, shade(ORANGE, 0.7), (TAB.x + a[0] + self.card_w / 2, oy + a[1] + self.card_h / 2),
                   (TAB.x + b[0] + self.card_w / 2, oy + b[1] + self.card_h / 2), 2)
        if ev["path"]:
            pts = [(TAB.x + self.anim_tab[e][0] + self.card_w / 2, oy + self.anim_tab[e][1] + self.card_h / 2)
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

    def draw_queue(self, s, ev, p):
        rect = pygame.Rect(12, Q_Y, W - 24, 100)
        acc = tuple(int(v) for v in self.acc)
        panel(s, rect)
        G.rect(s, shade(acc, 0.6), rect, 2, border_radius=14)
        dfs = self.algo == "dfs"
        text(s, "FRONTIER", font("segoeui", 15, True), acc, (26, Q_Y + 18))
        text(s, "ngăn xếp LIFO" if dfs else "hàng đợi FIFO", font("segoeui", 13), MUTED, (26, Q_Y + 40))
        text(s, f"{len(ev['frontier'])} nút", font("segoeui", 13), MUTED, (26, Q_Y + 62))
        belt = pygame.Rect(QX - 8, Q_Y + 28, self.qmax * self.qp + 2, 64)
        G.rect(s, (14, 20, 34), belt, border_radius=10)
        off = (pygame.time.get_ticks() / 60) % 16 if self.playing else 0
        for x in range(int(belt.x + 8 - off), belt.right - 8, 16):
            if x > belt.x + 4:
                G.line(s, (26, 34, 54), (x, belt.bottom - 5), (x + 8, belt.bottom - 5), 2)
        hidden = max(0, len(ev["frontier"]) - self.qmax) if dfs else 0
        if dfs:
            text(s, "ĐÁY" + (f"  (+{hidden} nút ẩn)" if hidden else ""), font("segoeui", 12, True), MUTED, (belt.x + 4, Q_Y + 8))
            text(s, "ĐỈNH  (push / pop)", font("segoeui", 12, True), GREEN, (belt.right - 4, Q_Y + 8), "topright")
        else:
            text(s, "HEAD  (dequeue)", font("segoeui", 12, True), GREEN, (belt.x + 4, Q_Y + 8))
            text(s, "TAIL  (enqueue)", font("segoeui", 12, True), ORANGE, (belt.right - 4, Q_Y + 8), "topright")
        clip = s.get_clip()
        setclip(s, belt.inflate(-4, 8))
        nodes = self.rec.nodes
        match = ev["match"]
        for eid, (x, y, sc, al, gone) in sorted(self.anim_q.items(), key=lambda t: t[1][4]):
            r = blit_state(s, nodes[eid]["state"], x, y, self.card_w, self.card_h, sc, al)
            if not gone:
                G.rect(s, RED if eid == match else BLUE, r.inflate(2, 2), 3 if eid == match else 2, border_radius=8)
        if ev["kind"] == "scan" and ev["frontier"]:
            fr = ev["frontier"]
            lim = fr.index(ev["scan_match"]) if ev["scan_match"] in fr else len(fr) - 1
            ci = min(lim, int(min(1.0, p * 1.15) * lim + 0.5)) if lim else 0
            ci -= hidden
            if 0 <= ci < self.qmax:
                cx = QX + ci * self.qp + self.card_w / 2
                hit = ev["scan_match"] is not None and ci + hidden == lim and p > 0.6
                col = RED if hit else CYAN
                G.rect(s, col, (cx - self.card_w / 2 - 4, Q_Y + 28, self.card_w + 8, 64), 3, border_radius=10)
                G.polygon(s, col, [(cx - 7, Q_Y + 21), (cx + 7, Q_Y + 21), (cx, Q_Y + 30)])
        s.set_clip(clip)
        extra = 0 if dfs else len(ev["frontier"]) - self.qmax
        if extra > 0:
            text(s, f"+{extra}", font("segoeui", 15, True), MUTED, (belt.right + 4, Q_Y + 48))

    def draw_explored(self, s, ev):
        rect = pygame.Rect(12, E_Y, W - 24, 72)
        panel(s, rect)
        text(s, "EXPLORED", font("segoeui", 15, True), ORANGE, (26, E_Y + 10))
        text(s, "đã mở", font("segoeui", 13), MUTED, (26, E_Y + 31))
        text(s, f"{len(ev['explored'])} nút", font("segoeui", 13), MUTED, (26, E_Y + 49))
        clip = s.get_clip()
        setclip(s, pygame.Rect(QX - 8, E_Y + 4, W - QX - 12, 64))
        nodes = self.rec.nodes
        for eid, (x, y, sc, al) in self.anim_e.items():
            r = blit_state(s, nodes[eid]["state"], x, y, self.card_w - 6, self.card_h - 4, sc, al * 0.9)
            G.rect(s, (70, 82, 112), r, 1, border_radius=6)
        s.set_clip(clip)

    def draw_controls(self, s):
        last = len(self.events) - 1
        bar = pygame.Rect(12, 872, W - 24, 6)
        G.rect(s, PANEL_L, bar, border_radius=3)
        frac = (self.ev_i + min(1.0, self.ev_t / self.ev["dur"])) / max(1, last + 1)
        G.rect(s, tuple(int(v) for v in self.acc), (bar.x, bar.y, max(6, bar.w * frac), bar.h), border_radius=3)
        for b in self.buttons:
            b.active = (b.key == "play" and self.playing) or (b.key == f"p{self.preset}") or (b.key == "replay" and bool(self.replay))
            if b.key == "play":
                b.label = "Dừng" if self.playing else "Phát"
            if b.key == "replay":
                b.label = "Dừng robot" if self.replay else "Chạy lời giải"
            b.draw(s, self.mouse, 15 if b.key == "replay" else 16)
        text(s, f"x{SPEEDS[self.speed_i]:g}", font("segoeui", 17, True), ACC_NOW, (self.speed_x + 6, 906), "midleft")

    def to_canvas(self, pos):
        ww, wh = self.win.get_size()
        sc = min(ww / W, wh / H)
        ox, oy = (ww - W * sc) / 2, (wh - H * sc) / 2
        return ((pos[0] - ox) / sc, (pos[1] - oy) / sc)

    def run(self):
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
                    elif k == pygame.K_t: self.press("edit")
                    elif k == pygame.K_v: self.press("replay")
                    elif k == pygame.K_b: self.press("alg_bfs")
                    elif k == pygame.K_d: self.press("alg_dfs")
                    elif k == pygame.K_F11:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            self.win = pygame.display.set_mode(self.win_size, pygame.RESIZABLE)
                    elif pygame.K_1 <= k <= pygame.K_4: self.press(f"p{k - pygame.K_1}")
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
                    if not hit and 866 <= m[1] <= 884 and 12 <= m[0] <= W - 12:
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
