"""GIAO DIỆN: bộ công cụ vẽ nhỏ dùng chung (chỉ có pygame, không có logic thuật toán).

Mọi hàm vẽ nhận toạ độ trong "hệ thiết kế" 1400 x ~900; kit tự nhân với tỉ lệ cửa sổ SC
để chữ và nét luôn sắc khi phóng to / thu nhỏ cửa sổ.
"""
import ctypes
import math
import re

import pygame

from desktop.ucs.common.theme import ACCENT, CYAN, INK_ON_ACCENT, PANEL, PANEL_L, TEXT

SC = 1.0                # tỉ lệ cửa sổ hiện tại so với hệ thiết kế
_CACHES = []


def enable_dpi_awareness():
    """Windows: tắt co giãn tự động của hệ điều hành để chữ không bị mờ."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def register_cache(cache):
    """Đăng ký một dict lưu hình đã vẽ sẵn; kit sẽ xóa nó mỗi khi đổi tỉ lệ cửa sổ."""
    _CACHES.append(cache)
    return cache


def set_scale(value):
    global SC
    SC = value
    for cache in _CACHES:
        cache.clear()


# ---------- toán màu và chuyển động mượt ----------

def sm(v, target, k, dt):
    """Đưa v tới gần target một cách mượt (k càng lớn càng nhanh)."""
    return v + (target - v) * (1 - math.exp(-k * dt))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------- vẽ hình ----------

def _p(a):
    return (a[0] * SC, a[1] * SC)


def _r(r):
    x, y, w, h = r
    return pygame.Rect(round(x * SC), round(y * SC), max(1, round(w * SC)), max(1, round(h * SC)))


def _w(w):
    return 0 if w == 0 else max(1, round(w * SC))


def px_rect(rect):
    """Rect trong hệ thiết kế -> Rect theo pixel thật của canvas."""
    return _r(rect)


class _Draw:
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


G = _Draw()


def alpha_poly(dst, pts, rgba):
    """Đa giác nửa trong suốt."""
    pp = [_p(q) for q in pts]
    xs, ys = [q[0] for q in pp], [q[1] for q in pp]
    x0, y0 = int(min(xs)) - 2, int(min(ys)) - 2
    w, h = int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4
    tmp = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
    pygame.draw.polygon(tmp, rgba, [(q[0] - x0, q[1] - y0) for q in pp])
    dst.blit(tmp, (x0, y0))


def setclip(dst, rect):
    dst.set_clip(_r(rect))


# ---------- chữ ----------

_FONTS = {}


def font(name, size, bold=False):
    px = max(6, round(size * SC))
    return pfont(name, px, bold)


def pfont(name, px, bold=False):
    """Phông theo cỡ pixel thật (không nhân với SC)."""
    key = (name, px, bold)
    if key not in _FONTS:
        _FONTS[key] = pygame.font.SysFont(name, px, bold=bold)
    return _FONTS[key]


def tw(f, s):
    """Chiều rộng của chuỗi s, tính theo hệ thiết kế."""
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


# ---------- khung và nút ----------

def panel(dst, rect, title=None, accent=CYAN):
    G.rect(dst, PANEL, rect, border_radius=14)
    G.rect(dst, PANEL_L, rect, 1, border_radius=14)
    if title:
        text(dst, title, font("segoeui", 15, True), accent, (rect.x + 14, rect.y + 10))


class Button:
    def __init__(self, rect, label, key):
        self.rect, self.label, self.key = pygame.Rect(rect), label, key
        self.active = False
        self.font_size = 16

    def draw(self, dst, mouse):
        hot = self.rect.collidepoint(mouse)
        col = ACCENT if self.active else ((52, 64, 92) if hot else PANEL_L)
        G.rect(dst, col, self.rect, border_radius=10)
        t = font("segoeui", self.font_size, True).render(self.label, True, INK_ON_ACCENT if self.active else TEXT)
        dst.blit(t, t.get_rect(center=(round(self.rect.centerx * SC), round(self.rect.centery * SC))))


# ---------- khung mã nguồn: tô màu từ khóa ----------

_TOKEN = re.compile(r"(?P<kw>\b(?:def|if|for|while|not|in|return|and|elif|is)\b)|(?P<fn>\b[A-Za-z_]\w*(?=\())|"
                    r"(?P<lit>\b(?:False|True|None)\b)")
_TOKEN_COLOR = {"kw": (255, 130, 170), "fn": (110, 200, 255), "lit": (255, 190, 110)}
_PLAIN = (214, 222, 240)


def _halve_indent(line):
    """Dòng code hiển thị thụt lề bằng một nửa cho gọn."""
    lead = len(line) - len(line.lstrip())
    return " " * (lead // 2) + line.lstrip()


def render_code_lines(code, avail_w, size):
    """Vẽ sẵn từng dòng code thành hai hình: sáng (dòng đang chạy) và tối. Chữ tự thu nhỏ nếu dòng dài nhất không vừa."""
    shown = [_halve_indent(ln) for ln in code]
    while size > 10 and max(tw(font("consolas", size), ln) for ln in shown) > avail_w:
        size -= 1
    f = font("consolas", size)
    out = []
    for line in shown:
        segs, pos = [], 0
        for m in _TOKEN.finditer(line):
            if m.start() > pos:
                segs.append((line[pos:m.start()], _PLAIN))
            segs.append((m.group(), _TOKEN_COLOR[m.lastgroup]))
            pos = m.end()
        if pos < len(line):
            segs.append((line[pos:], _PLAIN))
        bright = pygame.Surface((round(avail_w * SC), round(24 * SC)), pygame.SRCALPHA)
        dim = pygame.Surface((round(avail_w * SC), round(24 * SC)), pygame.SRCALPHA)
        x = 0
        for s, col in segs:
            bright.blit(f.render(s, True, col), (x, round(2 * SC)))
            dim.blit(f.render(s, True, shade(col, 0.5)), (x, round(2 * SC)))
            x += f.size(s)[0]
        out.append((bright, dim))
    return out
