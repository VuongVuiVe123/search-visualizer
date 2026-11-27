"""GIAO DIỆN 8-puzzle: vẽ bàn cờ (chỉ vẽ, không có logic).

    blit_board   vẽ một bàn cờ nhỏ (thẻ trong bảng node, FRONTIER, EXPLORED)
    BigBoard     bàn cờ lớn ở khung bên phải, ô số trượt mượt từ vị trí cũ sang vị trí mới
"""
import math

import pygame

from desktop.ucs.common import kit
from desktop.ucs.common.kit import G, font, pfont, sm
from desktop.ucs.puzzle8.logic import flat

TILE_COL = {1: (239, 122, 122), 2: (240, 170, 110), 3: (240, 214, 110), 4: (150, 215, 120),
            5: (100, 210, 190), 6: (100, 170, 240), 7: (150, 130, 240), 8: (210, 130, 220)}

_MINI = kit.register_cache({})


def mini_surface(state, size):
    ps = max(6, round(size * kit.SC))
    key = (state, ps)
    if key in _MINI:
        return _MINI[key]
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
    _MINI[key] = s
    return s


def blit_board(dst, state, cx, cy, size, scale=1.0, alpha=1.0):
    """Vẽ bàn cờ `state` (3x3) thành hình vuông cạnh `size` tâm (cx, cy). Trả về Rect đã vẽ."""
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
    dst.blit(img, img.get_rect(center=(round(cx * kit.SC), round(cy * kit.SC))))
    half = size * (scale if owned else 1.0) / 2
    return pygame.Rect(round(cx - half), round(cy - half), round(half * 2), round(half * 2))


class BigBoard:
    def __init__(self, x, y, size=132):
        self.x, self.y, self.size = x, y, size
        self.ts = (size - 8 * 2) // 3 - 2
        self.state = None           # 9 ô
        self.pos = {}               # số -> vị trí đang trượt của ô đó
        self.alpha = 1.0

    def slot(self, i):
        r, c = divmod(i, 3)
        step = self.ts + 4
        return 8 + c * step, 8 + r * step

    def set_state(self, state, copy_from=None):
        """Đổi sang bàn cờ mới; ô nào đã có vị trí thì trượt từ vị trí đó (copy_from: mượn vị trí từ bàn khác)."""
        state = flat(state)
        self.state = state
        if copy_from is not None:
            for v, p in copy_from.pos.items():
                self.pos[v] = list(p)
        for i, v in enumerate(state):
            if v and v not in self.pos:
                self.pos[v] = list(self.slot(i))

    def clear(self):
        self.state, self.pos = None, {}

    def snap(self):
        """Đặt ngay mọi ô về đúng chỗ (không trượt)."""
        if self.state:
            for i, v in enumerate(self.state):
                if v:
                    self.pos[v] = list(self.slot(i))

    def update(self, dt):
        if not self.state:
            return
        for i, v in enumerate(self.state):
            if v:
                tx, ty = self.slot(i)
                p = self.pos[v]
                p[0], p[1] = sm(p[0], tx, 10, dt), sm(p[1], ty, 10, dt)

    @property
    def center(self):
        return (self.x + self.size / 2, self.y + self.size / 2)

    def draw(self, dst, border, alpha=1.0):
        s = pygame.Surface((round(self.size * kit.SC), round(self.size * kit.SC)), pygame.SRCALPHA)
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
                moving = min(1.0, math.hypot(px - tx, py - ty) / 20)           # ô đang trượt thì nổi lên một chút
                if moving > 0.05:
                    G.rect(s, (0, 0, 0, 90), (px + 2, py + 5, self.ts, self.ts), border_radius=8)
                G.rect(s, TILE_COL[v], (px, py - 2 * moving, self.ts, self.ts), border_radius=8)
                t = f.render(str(v), True, (26, 26, 40))
                s.blit(t, t.get_rect(center=(round((px + self.ts / 2) * kit.SC), round((py + self.ts / 2 - 2 * moving) * kit.SC))))
        G.rect(s, border, (0, 0, self.size, self.size), 3, border_radius=12)
        if alpha < 0.98:
            s.set_alpha(int(255 * alpha))
        dst.blit(s, (round(self.x * kit.SC), round(self.y * kit.SC)))
