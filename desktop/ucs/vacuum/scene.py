"""GIAO DIỆN robot hút bụi: vẽ ngôi nhà nhìn nghiêng (isometric) và robot hút bụi (chỉ vẽ, không có logic).

    ISO, P, poly, box, flat, cylinder   phép chiếu isometric và các khối cơ bản
    draw_robot                          robot hút bụi hình trụ (quay theo hướng đi, cánh chổi quay)
    Scene                               ngôi nhà: số phòng -> bố cục, nền, đồ đạc từng phòng, vị trí tâm mỗi phòng
"""
import math
import random

import pygame

from desktop.ucs.common.kit import G, alpha_poly, setclip, shade
from desktop.ucs.common.theme import BG, PANEL

ROOM_TYPES = ["living", "kitchen", "bedroom", "bath", "study", "hall"]
ROOM_NAMES = {"living": "Phòng khách", "kitchen": "Bếp", "bedroom": "Phòng ngủ", "bath": "Phòng tắm",
              "study": "Làm việc", "hall": "Hành lang", "storage": "Kho"}
SCENE = pygame.Rect(524, 92, 864, 340)         # vùng ngôi nhà trên màn hình


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
