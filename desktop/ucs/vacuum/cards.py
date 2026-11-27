"""GIAO DIỆN robot hút bụi: vẽ thẻ trạng thái (chỉ vẽ, không có logic).

Thẻ trạng thái ("B", "C", "D", "D") là một dải các ô phòng: nền xanh = sạch (dấu ✓), nâu = bẩn, chấm tròn = robot.

    blit_state   vẽ một thẻ nhỏ (trong bảng node, FRONTIER, EXPLORED)
    BigCard      thẻ lớn ở khung "nút đang xét": phòng đổi màu mượt, robot trượt sang phòng mới
"""
import pygame

from desktop.ucs.common import kit
from desktop.ucs.common.kit import G, font, mix, pfont, sm, text
from desktop.ucs.common.theme import MUTED, ORANGE, PANEL
from desktop.ucs.vacuum.logic import letter, room_index

DIRTY = (150, 108, 66)
CLEAN = (80, 184, 116)

_MINI = kit.register_cache({})


def mini_state(state, w, h):
    pw, ph = max(8, round(w * kit.SC)), max(8, round(h * kit.SC))
    key = (state, pw, ph)
    if key in _MINI:
        return _MINI[key]
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
    cx, cy = pad + room_index(state) * (sw + gap) + sw / 2, top + sh / 2
    rad = min(sw, sh) * 0.38
    pygame.draw.circle(s, (18, 18, 22), (cx, cy), rad)
    pygame.draw.circle(s, (96, 96, 108), (cx, cy), rad, max(1, ph // 24))
    pygame.draw.circle(s, ORANGE, (cx, cy), max(1, rad * 0.32))
    f = pfont("consolas", max(8, int(ph * 0.25)), True)
    t = f.render(state[0] + " " + "".join(state[1:]), True, (190, 200, 222))
    s.blit(t, t.get_rect(midbottom=(pw // 2, ph - max(1, ph // 14))))
    _MINI[key] = s
    return s


def blit_state(dst, state, cx, cy, w, h, scale=1.0, alpha=1.0):
    """Vẽ thẻ nhỏ `state` kích thước w x h tâm (cx, cy). Trả về Rect đã vẽ."""
    img = mini_state(state, w, h)
    owned = False
    if abs(scale - 1) > 0.02:
        img = pygame.transform.smoothscale(img, (max(2, int(img.get_width() * scale)), max(2, int(img.get_height() * scale))))
        owned = True
    if alpha < 0.98:
        if not owned:
            img = img.copy()
        img.set_alpha(int(255 * max(0, alpha)))
    dst.blit(img, img.get_rect(center=(round(cx * kit.SC), round(cy * kit.SC))))
    k = scale if owned else 1.0
    return pygame.Rect(round(cx - w * k / 2), round(cy - h * k / 2), round(w * k), round(h * k))


class BigCard:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.n = 0                  # số phòng đang vẽ
        self.rx = None              # vị trí ngang của robot (trượt mượt)
        self.dirt = []              # mức bẩn của từng phòng, 0..1 (đổi màu mượt)
        self.alpha = 1.0

    def reset(self):
        self.n, self.rx = 0, None

    def layout(self, n):
        r = self.rect
        sq = min(40, (r.w - 20 - (n - 1) * 6) / n)
        total = n * sq + (n - 1) * 6
        return sq, r.x + (r.w - total) / 2

    def update(self, state, dt, on):
        if state is None:
            return
        n = len(state) - 1
        if n != self.n:
            self.n, self.rx, self.dirt = n, None, [1.0 if v == "D" else 0.0 for v in state[1:]]
        sq, x0 = self.layout(n)
        tx = x0 + room_index(state) * (sq + 6) + sq / 2
        self.rx = tx if self.rx is None else sm(self.rx, tx, 12, dt)
        for i in range(n):
            self.dirt[i] = sm(self.dirt[i], 1.0 if state[1 + i] == "D" else 0.0, 12, dt)
        self.alpha = sm(self.alpha, 1.0 if on else 0.22, 9, dt)

    def draw(self, s, label, border, state):
        r, a = self.rect, self.alpha

        def fd(c):
            return mix(PANEL, c, a)

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
            G.rect(s, fd(mix(CLEAN, DIRTY, self.dirt[i])), (x, top, sq, 30), border_radius=7)
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
