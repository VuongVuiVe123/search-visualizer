"""GIAO DIỆN dùng chung cho cả hai app UCS (chỉ vẽ và nhận phím / chuột, không có thuật toán).

UCSScreen vẽ phần khung giống nhau của mọi bài toán:

    đầu trang        tên thuật toán, các ô số liệu (Đã mở, Frontier, Nút sinh ra, Chi phí g), đích
    khung mã nguồn   mã nguồn thật của hàm UCS, dòng đang chạy sáng lên, lời giải thích bên dưới
    bảng node        mỗi nút một thẻ, xếp theo độ sâu, góc thẻ ghi chi phí g
    FRONTIER         hàng đợi ưu tiên: thẻ nào g nhỏ nhất đứng đầu
    EXPLORED         các nút đã mở
    thanh điều khiển Phát / Tiếp / Lùi / bài mẫu / Ngẫu nhiên / Tự đặt / Chạy lời giải

Mọi việc "làm gì" nằm ở self.session (xem session.py). Lớp này chỉ gọi session rồi vẽ kết quả.

Mỗi app bài toán kế thừa UCSScreen và bổ sung phần vẽ riêng (xem phần HOOK bên dưới):
    puzzle8/ui.py    bàn cờ 3x3
    vacuum/ui.py     ngôi nhà isometric và robot
"""
import math

import pygame

from desktop.ucs.common import kit
from desktop.ucs.common.kit import Button, G, font, panel, setclip, shade, sm, text, tw, wrap
from desktop.ucs.common.theme import (ACCENT, BG, BLUE, CYAN, DIM_BORDER, GOLD, GREEN, INK_ON_ACCENT, LAMP_OFF, MUTED, ORANGE,
                                      PANEL, PANEL_L, RED, TEXT)

# ----- màu và chữ theo "phán quyết" của dòng kiểm tra nút con -----
VERDICT_COLOR = {None: CYAN, "ok": GREEN, "dup": RED, "goal": GOLD, "queued": GREEN, "replace": GOLD}
VERDICT_TEXT = {"ok": "Nút mới → xét tiếp", "dup": "Trùng → BỎ", "goal": "ĐÍCH!",
                "queued": "Vào hàng đợi ưu tiên", "replace": "Rẻ hơn → thay nút cũ"}

# ----- kiểu thẻ trong bảng node theo trạng thái của nút (xem UCSSession.node_status): (màu viền, độ dày, độ đậm) -----
NODE_STYLE = {"path": (GOLD, 3, 1.0), "current": (ORANGE, 3, 1.0), "explored": (DIM_BORDER, 1, 0.55),
              "frontier": (BLUE, 2, 1.0), "other": (DIM_BORDER, 1, 1.0)}

# ----- hai cỡ của khối "hai đèn + biểu ngữ phán quyết" -----
VERDICT_ROOMY = dict(row_h=28, lamp_o=11, lamp_i=8, label_fs=13, tag_fs=15, label_x=46, tag_dx=18, bw=260, bh=34, bdy=62, banner_fs=17)
VERDICT_COMPACT = dict(row_h=22, lamp_o=9, lamp_i=6, label_fs=12, tag_fs=13, label_x=44, tag_dx=16, bw=240, bh=28, bdy=48, banner_fs=15)


class Layout:
    """Vị trí các khung trên màn hình (toạ độ hệ thiết kế). Mỗi app tự khai báo một bộ."""

    def __init__(self, **kw):
        self.q_x = 150              # x bắt đầu của hàng thẻ trong FRONTIER và EXPLORED
        self.preset_label = True    # có ghi chữ "Bài mẫu:" bên trái hàng nút bài mẫu không (cần chỗ trống)
        self.__dict__.update(kw)


class Metrics:
    """Kích thước thẻ trong từng khung. Cố định với 8-puzzle, đổi theo số phòng với robot hút bụi."""

    def __init__(self, cell, q, e):
        self.cell_w, self.cell_h, self.cell_gap, self.section_gap = cell    # thẻ trong bảng node
        self.q_w, self.q_h, self.q_pitch, self.q_max = q                    # thẻ trong FRONTIER (rộng, cao, bước, tối đa)
        self.e_w, self.e_h, self.e_pitch, self.e_max = e                    # thẻ trong EXPLORED


class UCSScreen:
    LAYOUT = None
    CAPTION = ""
    SUBTITLE = ""
    TABLE_TITLE = ""
    VERDICT_STYLE = VERDICT_ROOMY

    # =====================================================================
    # HOOK: mỗi app bài toán ghi đè các hàm này
    # =====================================================================
    def build_metrics(self):
        """Trả về Metrics theo bài đang nạp."""
        raise NotImplementedError

    def draw_card(self, s, state, cx, cy, w, h, scale, alpha):
        """Vẽ một trạng thái thành thẻ nhỏ (dùng trong bảng node, FRONTIER, EXPLORED). Trả về Rect đã vẽ."""
        raise NotImplementedError

    def anchors(self):
        """Hai điểm mà thẻ bay tới / bay ra: {"child": (x, y), "node": (x, y)}."""
        raise NotImplementedError

    def draw_goal(self, s, x):
        """Vẽ đích ở đầu trang, bên trái ô số liệu đầu tiên (x là mép trái của dải ô số liệu)."""
        raise NotImplementedError

    def draw_side(self, s, ev, p):
        """Vẽ khung bên phải: nút đang xét, nút con, hai đèn kiểm tra."""
        raise NotImplementedError

    def draw_stage(self, s, ev, p):
        """Vẽ phần minh họa lớn (ngôi nhà của robot). 8-puzzle không dùng."""

    def update_stage(self, dt, ev):
        """Cập nhật hiệu ứng chuyển động của bàn cờ / ngôi nhà theo sự kiện hiện tại."""

    def on_loaded(self):
        """Gọi sau mỗi lần nạp bài mới."""

    def on_rescale(self):
        """Gọi khi đổi kích thước cửa sổ (xóa các hình đã vẽ sẵn)."""

    def open_editor(self):
        """Mở hộp thoại tự đặt: tạo một dialog và gán vào self.dialog."""
        raise NotImplementedError

    # =====================================================================
    # Khởi tạo
    # =====================================================================
    def __init__(self, session):
        pygame.init()
        L = self.LAYOUT
        info = pygame.display.get_desktop_sizes()[0]
        sc = 0.82 * min((info[0] - 40) / L.W, (info[1] - 110) / L.H)
        self.win = pygame.display.set_mode((int(L.W * sc), int(L.H * sc)), pygame.RESIZABLE)
        pygame.display.set_caption(self.CAPTION)
        self.session = session
        self.canvas = None
        self.fullscreen, self.win_size = False, self.win.get_size()
        self.clock = pygame.time.Clock()
        self.mouse = (0, 0)
        self.toast = ("", 0.0)
        self.dialog = None                      # hộp thoại đang mở (nếu có)
        self.cap_text, self.cap_age = "", 0.0
        self.bar_y = L.code.y + 36.0
        self.speed_x = 0
        self.buttons = self.build_buttons()
        self.apply_scale()
        self.reload_view()

    def build_buttons(self):
        L, y, buttons, bx = self.LAYOUT, self.LAYOUT.btn_y, [], 12
        for w, label, key in [(80, "Về đầu", "reset"), (70, "Lùi", "back"), (96, "Phát", "play"), (70, "Tiếp", "next"),
                              (100, "Node kế", "node"), (38, "−", "slow"), (38, "+", "fast")]:
            buttons.append(Button((bx, y, w, 40), label, key))
            bx += w + 8
            if key == "slow":
                self.speed_x = bx - 8 + 6       # chỗ ghi "x1", "x2"... giữa hai nút − và +
                bx += 56
        bx = L.preset_x
        for i, (label, _, _) in enumerate(self.session.presets):
            buttons.append(Button((bx, y, L.preset_w, 40), label, f"p{i}"))
            bx += L.preset_step
        w_edit, w_rand, w_replay = L.tools
        buttons.append(Button((bx, y, w_edit, 40), "Tự đặt", "edit"))
        buttons.append(Button((bx + w_edit + 8, y, w_rand, 40), "Ngẫu nhiên", "rand"))
        replay = Button((bx + w_edit + w_rand + 16, y, w_replay, 40), "Chạy lời giải", "replay")
        replay.font_size = 15
        buttons.append(replay)
        return buttons

    def apply_scale(self):
        L = self.LAYOUT
        ww, wh = self.win.get_size()
        sc = max(0.3, min(ww / L.W, wh / L.H))
        if self.canvas is not None and abs(sc - kit.SC) < 0.003 and self.canvas.get_size() == (round(L.W * kit.SC), round(L.H * kit.SC)):
            return
        kit.set_scale(sc)
        self.canvas = pygame.Surface((round(L.W * sc), round(L.H * sc)))
        self.code_lines = kit.render_code_lines(self.session.code, L.code.w - 60, L.code_size)
        self.on_rescale()

    def reload_view(self):
        """Gọi mỗi khi session nạp bài mới: đặt lại các hiệu ứng."""
        self.M = self.build_metrics()
        self.anim_tab, self.anim_q, self.anim_e = {}, {}, {}      # vị trí đang bay của thẻ trong 3 khung
        self.scroll = 0.0
        self.lamps = [[70, 80, 100], [70, 80, 100]]
        self.banner_key, self.banner_age = None, 1.0
        self.layout_tn = -1
        self.on_loaded()

    @property
    def ev(self):
        return self.session.ev

    # =====================================================================
    # Nhận lệnh từ nút bấm / phím
    # =====================================================================
    def press(self, key):
        ss, player = self.session, self.session.player
        if key == "play":
            ss.stop_replay()
            player.toggle_play()
        elif key == "next":
            player.step_next()
        elif key == "back":
            player.step_back()
        elif key == "node":
            player.next_node()
        elif key == "reset":
            ss.stop_replay()
            player.reset()
        elif key == "slow":
            player.slower()
        elif key == "fast":
            player.faster()
        elif key.startswith("p") and key[1:].isdigit():
            if int(key[1:]) < len(ss.presets):
                ss.load_preset(int(key[1:]))
                self.reload_view()
        elif key == "rand":
            ss.load_random()
            self.reload_view()
        elif key == "edit":
            ss.stop_replay()
            player.playing = False
            self.open_editor()
        elif key == "replay":
            ss.toggle_replay()
        self.show_notice()

    def apply_custom(self, init, goal):
        """Hộp thoại gọi khi bấm Áp dụng."""
        self.session.load_custom(init, goal)
        self.reload_view()

    def show_notice(self):
        notice = self.session.pop_notice()
        if notice:
            self.toast = (notice, 3.0)

    # =====================================================================
    # Cập nhật hiệu ứng mỗi khung hình
    # =====================================================================
    def update(self, dt):
        ss, L = self.session, self.LAYOUT
        self.toast = (self.toast[0], max(0.0, self.toast[1] - dt))
        ss.update(dt)
        ev = ss.ev
        self.update_stage(dt, ev)
        for k in range(2):                                  # hai đèn kiểm tra đổi màu mượt
            g = ev["gate"][k]
            tgt = LAMP_OFF if g is None else (RED if g else GREEN)
            self.lamps[k] = [sm(self.lamps[k][j], tgt[j], 12, dt) for j in range(3)]
        key = (ev["verdict"], ev["child"][2] if ev["child"] else None)
        if key != self.banner_key:
            self.banner_key, self.banner_age = key, 0.0
        self.banner_age += dt
        if ev["cap"] != self.cap_text:
            self.cap_text, self.cap_age = ev["cap"], 0.0
        self.cap_age += dt
        self.bar_y = sm(self.bar_y, L.code.y + 36 + ev["line"] * L.line_h, 30, dt)
        self.update_table(dt, ev)
        self.update_queue(dt, ev)
        self.update_explored(dt, ev)

    def table_layout(self, tn):
        """Xếp các nút theo độ sâu: trả về (vị trí từng nút, tiêu đề từng độ sâu, tổng chiều cao)."""
        M, nodes = self.M, self.session.rec.nodes
        cols = max(1, int((self.LAYOUT.tab.w - 28 + M.cell_gap) // (M.cell_w + M.cell_gap)))
        by_depth = {}
        for eid in range(tn):
            by_depth.setdefault(nodes[eid]["depth"], []).append(eid)
        pos, heads, y = {}, [], 0
        for d in sorted(by_depth):
            heads.append((d, y, len(by_depth[d])))
            y += 24
            for k, eid in enumerate(by_depth[d]):
                pos[eid] = (14 + (k % cols) * (M.cell_w + M.cell_gap), y + (k // cols) * (M.cell_h + M.cell_gap))
            y += ((len(by_depth[d]) - 1) // cols + 1) * (M.cell_h + M.cell_gap) + M.section_gap
        return pos, heads, y

    def update_table(self, dt, ev):
        M, tab = self.M, self.LAYOUT.tab
        tn = ev["tn"]
        if tn != self.layout_tn:
            self.tpos, self.theads, self.ttotal = self.table_layout(tn)
            self.layout_tn = tn
        view_h = tab.h - 48
        focus = ev["node_eid"] if ev["node_eid"] is not None else (tn - 1 if tn else None)
        if ev["child_eid"] is not None and ev["child_eid"] < tn:
            focus = ev["child_eid"]
        if focus is not None and focus in self.tpos:                    # cuộn bảng tới nút đang xét
            tgt = self.tpos[focus][1] - view_h * 0.4
            self.scroll = sm(self.scroll, max(0, min(tgt, max(0, self.ttotal - view_h))), 5, dt)
        cb = self.anchors()["child"]
        for eid in list(self.anim_tab):
            if eid >= tn:
                del self.anim_tab[eid]
        for eid, (x, y) in self.tpos.items():
            a = self.anim_tab.get(eid)
            if a is None:                                               # nút mới bay ra từ ô "child"
                a = self.anim_tab[eid] = [cb[0] - tab.x - M.cell_w / 2, cb[1] - tab.y - 36 + self.scroll - M.cell_h / 2, 0.35, 0.0]
            a[0], a[1] = sm(a[0], x, 7, dt), sm(a[1], y, 7, dt)
            a[2], a[3] = sm(a[2], 1.0, 7, dt), sm(a[3], 1.0, 9, dt)

    def update_queue(self, dt, ev):
        L, M = self.LAYOUT, self.M
        fr, anc = ev["frontier"], self.anchors()
        cb, nb = anc["child"], anc["node"]
        for eid in list(self.anim_q):
            if eid >= ev["tn"]:
                del self.anim_q[eid]
        for i, eid in enumerate(fr):                                    # nút đang chờ: bay tới đúng chỗ trong hàng đợi
            a = self.anim_q.get(eid)
            if a is None:
                a = self.anim_q[eid] = [cb[0], cb[1], 0.4, 0.0, False]
            a[4] = False
            a[0] = sm(a[0], L.q_x + i * M.q_pitch + M.q_w / 2, 8, dt)
            a[1] = sm(a[1], L.q_y + 60, 8, dt)
            a[2] = sm(a[2], 1.0, 8, dt)
            a[3] = sm(a[3], 1.0 if i < M.q_max else 0.0, 8, dt)
        gone = []
        for eid, a in self.anim_q.items():                              # nút rời hàng đợi: bay về ô "node" rồi mờ dần
            if eid not in fr:
                a[4] = True
                a[0], a[1] = sm(a[0], nb[0], 7, dt), sm(a[1], nb[1], 7, dt)
                a[2], a[3] = sm(a[2], 0.7, 7, dt), sm(a[3], 0.0, 9, dt)
                if a[3] < 0.03:
                    gone.append(eid)
        for eid in gone:
            del self.anim_q[eid]

    def update_explored(self, dt, ev):
        L, M = self.LAYOUT, self.M
        ex, nb = ev["explored"], self.anchors()["node"]
        start = max(0, len(ex) - M.e_max)
        for eid in list(self.anim_e):
            if eid not in ex:
                del self.anim_e[eid]
        for i, eid in enumerate(ex):
            a = self.anim_e.get(eid)
            if a is None:
                a = self.anim_e[eid] = [nb[0], nb[1], 0.5, 0.0]
            idx = i - start
            a[0] = sm(a[0], L.q_x + idx * M.e_pitch + M.e_pitch / 2, 8, dt)
            a[1] = sm(a[1], L.e_y + 36, 8, dt)
            a[2] = sm(a[2], 1.0, 8, dt)
            a[3] = sm(a[3], 1.0 if idx >= 0 else 0.0, 8, dt)

    # =====================================================================
    # Vẽ
    # =====================================================================
    def draw(self):
        s, L = self.canvas, self.LAYOUT
        s.fill(BG)
        ss = self.session
        ev, p = ss.ev, ss.player.progress
        self.draw_header(s, ev)
        self.draw_stage(s, ev, p)
        self.draw_side(s, ev, p)
        self.draw_code(s, ev)
        self.draw_table(s, ev, p)
        self.draw_queue(s, ev, p)
        self.draw_explored(s, ev)
        self.draw_controls(s)
        if self.toast[1] > 0:
            a = min(1.0, self.toast[1] / 0.5)
            r = pygame.Rect(0, 0, min(L.tab.w - 24, 520), 34)
            r.midbottom = (L.tab.centerx, L.tab.bottom - 12)
            G.rect(s, (60, 40, 18), r, border_radius=17)
            G.rect(s, ORANGE, r, 2, border_radius=17)
            text(s, wrap(self.toast[0], font("segoeui", 13), r.w - 24)[0], font("segoeui", 13), ORANGE, r.center, "center", alpha=a)
        if self.dialog:
            self.dialog.draw(s, self.mouse)

    def cost_badge(self, s, r, g):
        """Huy hiệu tròn nhỏ ghi chi phí g ở góc trên bên phải một thẻ."""
        if g is None:
            return
        f = font("segoeui", 11, True)
        w = max(17, tw(f, str(g)) + 9)
        box = pygame.Rect(round(r.right - w + 5), round(r.y - 7), round(w), 15)
        G.rect(s, ACCENT, box, border_radius=7)
        text(s, str(g), f, (16, 14, 30), box.center, "center")

    def draw_header(self, s, ev):
        L, info = self.LAYOUT, self.session.info
        text(s, info["full"], font("segoeui", 28, True), ACCENT, (16, 10))
        text(s, self.SUBTITLE, font("segoeui", 15), MUTED, (18, 50))
        chips = [("Đã mở", len(ev["explored"]), ORANGE), ("Frontier", len(ev["frontier"]), BLUE),
                 ("Nút sinh ra", ev["tn"], CYAN), ("Chi phí g", ev["node_cost"], GOLD)]
        x = L.W - 16
        for name, val, col in reversed(chips):
            f1, f2 = font("segoeui", 13), font("segoeui", 22, True)
            w = max(tw(f1, name), 36) + 26
            r = pygame.Rect(x - w, 12, w, 52)
            G.rect(s, PANEL, r, border_radius=10)
            G.rect(s, shade(col, 0.55), r, 1, border_radius=10)
            text(s, name, f1, MUTED, (r.centerx, r.y + 6), "midtop")
            text(s, str(val), f2, col, (r.centerx, r.y + 22), "midtop")
            x = r.x - 8
        self.draw_goal(s, x)
        cont = pygame.Rect(494, 10, 282, 64)                    # thẻ ghi tên thuật toán đang chạy
        G.rect(s, (16, 21, 34), cont, border_radius=18)
        G.rect(s, PANEL_L, cont, 1, border_radius=18)
        pill = pygame.Rect(500, 16, 270, 52)
        G.rect(s, shade(ACCENT, 0.35), pill.inflate(8, 8), border_radius=18)
        G.rect(s, ACCENT, pill, border_radius=14)
        text(s, info["name"], font("segoeui", 26, True), INK_ON_ACCENT, (pill.x + 18, pill.centery), "midleft")
        text(s, info["l1"], font("segoeui", 13, True), INK_ON_ACCENT, (pill.x + 90, pill.centery - 9), "midleft")
        text(s, info["l2"], font("segoeui", 12), INK_ON_ACCENT, (pill.x + 90, pill.centery + 9), "midleft")

    def draw_code(self, s, ev):
        L, rect = self.LAYOUT, self.LAYOUT.code
        panel(s, rect, f"mã nguồn  {self.session.info['name']}(problem)", ACCENT)
        G.rect(s, shade(ACCENT, 0.6), rect, 2, border_radius=14)
        top = rect.y + 36
        G.rect(s, (24, 32, 52), (rect.x + 8, self.bar_y, rect.w - 16, L.line_h), border_radius=6)     # thanh sáng ở dòng đang chạy
        glow = pygame.Surface((round((rect.w - 16) * kit.SC), round(L.line_h * kit.SC)), pygame.SRCALPHA)
        glow.fill((*ACCENT, 40))
        s.blit(glow, (round((rect.x + 8) * kit.SC), round(self.bar_y * kit.SC)))
        G.rect(s, ACCENT, (rect.x + 8, self.bar_y, 4, L.line_h), border_radius=2)
        f = font("consolas", 13)
        for i, (bright, dim) in enumerate(self.code_lines):
            y = top + i * L.line_h
            active = i == ev["line"]
            text(s, str(i + 1), f, ACCENT if active else (70, 82, 110), (rect.x + 34, y + 4), "topright")
            s.blit(bright if active else dim, (round((rect.x + 46) * kit.SC), round((y - 2) * kit.SC)))
        text(s, f"dòng {ev['line'] + 1} · sự kiện {self.session.player.i + 1}/{len(self.session.player.events)}",
             font("segoeui", 13), MUTED, (rect.right - 14, rect.y + 12), "topright")
        cap = pygame.Rect(rect.x + 10, rect.bottom - 72, rect.w - 20, 62)                             # câu giải thích dòng đang chạy
        G.rect(s, (14, 20, 34), cap, border_radius=10)
        G.rect(s, PANEL_L, cap, 1, border_radius=10)
        a = min(1.0, self.cap_age / 0.25)
        fc = font("segoeui", 15)
        for k, line in enumerate(wrap(self.cap_text, fc, cap.w - 24)[:3]):
            text(s, line, fc, TEXT, (cap.x + 12, cap.y + 7 + k * 17), alpha=a)

    def draw_table(self, s, ev, p):
        tab, M, ss = self.LAYOUT.tab, self.M, self.session
        panel(s, tab, self.TABLE_TITLE, GOLD)
        view = pygame.Rect(tab.x + 6, tab.y + 36, tab.w - 12, tab.h - 44)
        clip = s.get_clip()
        setclip(s, view)
        oy = tab.y + 36 - self.scroll
        for d, y, n in self.theads:                                     # tiêu đề từng độ sâu
            yy = oy + y
            if view.y - 30 < yy < view.bottom:
                text(s, f"Độ sâu {d}", font("segoeui", 14, True), GOLD, (tab.x + 18, yy + 2))
                text(s, f"{n} nút", font("segoeui", 13), MUTED, (tab.right - 22, yy + 3), "topright")
                G.line(s, PANEL_L, (tab.x + 14, yy + 21), (tab.right - 14, yy + 21))
        nodes = ss.rec.nodes
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 220)
        order = sorted(self.anim_tab, key=lambda e: (e == ev["node_eid"], e in ev["path"]))      # nút đang xét và đường lời giải vẽ sau cùng
        for eid in order:
            x, y, sc, al = self.anim_tab[eid]
            cx, cy = tab.x + x + M.cell_w / 2, oy + y + M.cell_h / 2
            if cy < view.y - M.cell_h or cy > view.bottom + M.cell_h:
                continue
            status = ss.node_status(eid)
            col, bw, dim = NODE_STYLE[status]
            r = self.draw_card(s, nodes[eid]["state"], cx, cy, M.cell_w, M.cell_h, sc, al * (0.5 + 0.5 * dim))
            if status == "current":
                col = kit.mix(ORANGE, (255, 240, 200), pulse * 0.6)
                G.rect(s, shade(ORANGE, 0.45), r.inflate(10, 10), 2, border_radius=10)
            if eid == ev["match"]:
                col = RED
            G.rect(s, col, r.inflate(2, 2), bw, border_radius=8)
            self.cost_badge(s, r, nodes[eid]["cost"])
        ne = ev["node_eid"]
        if ne is not None and ne in self.anim_tab and nodes[ne]["parent"] in self.anim_tab:            # nối nút đang xét với nút cha
            a, b = self.anim_tab[ne], self.anim_tab[nodes[ne]["parent"]]
            G.line(s, shade(ORANGE, 0.7), (tab.x + a[0] + M.cell_w / 2, oy + a[1] + M.cell_h / 2),
                   (tab.x + b[0] + M.cell_w / 2, oy + b[1] + M.cell_h / 2), 2)
        if ev["path"]:                                                  # đường lời giải
            pts = [(tab.x + self.anim_tab[e][0] + M.cell_w / 2, oy + self.anim_tab[e][1] + M.cell_h / 2)
                   for e in ev["path"] if e in self.anim_tab]
            if len(pts) > 1:
                t = min(1.0, p * 1.3 if ev["kind"] == "done" else 1.0)
                n = max(1, int(t * (len(pts) - 1)))
                G.lines(s, GOLD, False, pts[:n + 1], 4)
                for q in pts[:n + 1]:
                    G.circle(s, GOLD, q, 5)
        s.set_clip(clip)
        if self.ttotal > view.h:                                        # thanh cuộn
            th = max(30, view.h * view.h / self.ttotal)
            ty = view.y + (view.h - th) * (self.scroll / max(1, self.ttotal - view.h))
            G.rect(s, PANEL_L, (tab.right - 8, ty, 4, th), border_radius=2)

    def draw_queue(self, s, ev, p):
        L, M, nodes = self.LAYOUT, self.M, self.session.rec.nodes
        rect = pygame.Rect(12, L.q_y, L.W - 24, 100)
        panel(s, rect)
        G.rect(s, shade(ACCENT, 0.6), rect, 2, border_radius=14)
        text(s, "FRONTIER", font("segoeui", 15, True), ACCENT, (26, L.q_y + 18))
        text(s, "ưu tiên theo g", font("segoeui", 13), MUTED, (26, L.q_y + 40))
        text(s, f"{len(ev['frontier'])} nút", font("segoeui", 13), MUTED, (26, L.q_y + 62))
        belt = pygame.Rect(L.q_x - 8, L.q_y + 28, M.q_max * M.q_pitch + 2, 64)
        G.rect(s, (14, 20, 34), belt, border_radius=10)
        off = (pygame.time.get_ticks() / 60) % 16 if self.session.player.playing else 0              # băng chuyền chạy khi đang phát
        for x in range(int(belt.x + 8 - off), belt.right - 8, 16):
            if x > belt.x + 4:
                G.line(s, (26, 34, 54), (x, belt.bottom - 5), (x + 8, belt.bottom - 5), 2)
        text(s, "ĐẦU: g nhỏ nhất  (pop)", font("segoeui", 12, True), GREEN, (belt.x + 4, L.q_y + 8), "topleft")
        text(s, "g lớn nhất  (push chèn theo g)", font("segoeui", 12, True), ORANGE, (belt.right - 4, L.q_y + 8), "topright")
        clip = s.get_clip()
        setclip(s, belt.inflate(-4, 8))
        for eid, (x, y, sc, al, leaving) in sorted(self.anim_q.items(), key=lambda t: t[1][4]):
            r = self.draw_card(s, nodes[eid]["state"], x, y, M.q_w, M.q_h, sc, al)
            if not leaving:
                G.rect(s, RED if eid == ev["match"] else BLUE, r.inflate(2, 2), 3 if eid == ev["match"] else 2, border_radius=8)
                self.cost_badge(s, r, nodes[eid]["cost"])
        if ev["kind"] == "scan" and ev["frontier"]:                    # khung dò qua từng nút khi tìm nút trùng trong frontier
            fr = ev["frontier"]
            lim = fr.index(ev["scan_match"]) if ev["scan_match"] in fr else len(fr) - 1
            ci = min(lim, int(min(1.0, p * 1.15) * lim + 0.5)) if lim else 0
            if 0 <= ci < M.q_max:
                cx = L.q_x + ci * M.q_pitch + M.q_w / 2
                hit = ev["scan_match"] is not None and ci == lim and p > 0.6
                col = RED if hit else CYAN
                G.rect(s, col, (cx - M.q_w / 2 - 4, L.q_y + 28, M.q_w + 8, 64), 3, border_radius=10)
                G.polygon(s, col, [(cx - 7, L.q_y + 21), (cx + 7, L.q_y + 21), (cx, L.q_y + 30)])
        s.set_clip(clip)
        extra = len(ev["frontier"]) - M.q_max
        if extra > 0:
            text(s, f"+{extra}", font("segoeui", 15, True), MUTED, (belt.right + 4, L.q_y + 48))

    def draw_explored(self, s, ev):
        L, M, nodes = self.LAYOUT, self.M, self.session.rec.nodes
        rect = pygame.Rect(12, L.e_y, L.W - 24, 72)
        panel(s, rect)
        text(s, "EXPLORED", font("segoeui", 15, True), ORANGE, (26, L.e_y + 10))
        text(s, "đã mở", font("segoeui", 13), MUTED, (26, L.e_y + 31))
        text(s, f"{len(ev['explored'])} nút", font("segoeui", 13), MUTED, (26, L.e_y + 49))
        clip = s.get_clip()
        setclip(s, pygame.Rect(L.q_x - 8, L.e_y + 4, L.W - L.q_x - 12, 64))
        for eid, (x, y, sc, al) in self.anim_e.items():
            r = self.draw_card(s, nodes[eid]["state"], x, y, M.e_w, M.e_h, sc, al * 0.9)
            G.rect(s, DIM_BORDER, r, 1, border_radius=6)
        s.set_clip(clip)

    def draw_controls(self, s):
        L, ss = self.LAYOUT, self.session
        player = ss.player
        bar = pygame.Rect(12, L.bar_y, L.W - 24, 6)                     # thanh tiến độ
        G.rect(s, PANEL_L, bar, border_radius=3)
        frac = (player.i + player.progress) / max(1, player.last + 1)
        G.rect(s, ACCENT, (bar.x, bar.y, max(6, bar.w * frac), bar.h), border_radius=3)
        for b in self.buttons:
            if b.key == "play":
                b.label = "Dừng" if player.playing else "Phát"
            if b.key == "replay":
                b.label = L.replay_stop if ss.replay else "Chạy lời giải"
            b.active = ((b.key == "play" and player.playing) or b.key == f"p{ss.preset}"
                        or (b.key == "replay" and ss.replay is not None))
            b.draw(s, self.mouse)
        text(s, f"x{player.speed:g}", font("segoeui", 17, True), ACCENT, (self.speed_x + 6, L.btn_y + 20), "midleft")
        if L.preset_label:
            first = next(b for b in self.buttons if b.key == "p0")
            text(s, "Bài mẫu:", font("segoeui", 14), MUTED, (first.rect.x - 8, L.btn_y + 20), "midright")

    # ---------- khối dùng chung cho khung bên phải ----------
    def draw_verdict(self, s, area, y, ev, p):
        """Hai đèn kiểm tra (nhãn lấy từ tracing/algorithm_info.py) và biểu ngữ kết luận ("Nút mới", "Trùng → BỎ", ...)."""
        v = self.VERDICT_STYLE
        for k, label in enumerate(self.session.info["gates"]):
            yy = y + k * v["row_h"]
            col = tuple(int(c) for c in self.lamps[k])
            G.circle(s, shade(col, 0.4), (area.x + 26, yy + v["lamp_o"]), v["lamp_o"])
            G.circle(s, col, (area.x + 26, yy + v["lamp_o"]), v["lamp_i"])
            text(s, label, font("consolas", v["label_fs"]), TEXT, (area.x + v["label_x"], yy + 3))
            g = ev["gate"][k]
            text(s, "?" if g is None else ("CÓ" if g else "KHÔNG"), font("segoeui", v["tag_fs"], True), col,
                 (area.right - v["tag_dx"], yy + 1), "topright")
        vb = ev["verdict"]
        if vb:
            col = VERDICT_COLOR[vb]
            ease = 1 - (1 - min(1.0, self.banner_age / 0.3)) ** 3
            r = pygame.Rect(0, 0, int(v["bw"] * (0.6 + 0.4 * ease)), v["bh"])
            r.midtop = (area.centerx, y + v["bdy"])
            G.rect(s, shade(col, 0.28), r, border_radius=v["bh"] // 2)
            G.rect(s, col, r, 2, border_radius=v["bh"] // 2)
            text(s, VERDICT_TEXT[vb], font("segoeui", v["banner_fs"], True), col, r.center, "center", alpha=ease)

    def flash_duplicate(self, s, rect, p):
        """Nhấp nháy đỏ lên thẻ nút con khi nó bị bỏ vì trùng."""
        flash = pygame.Surface((round(rect.w * kit.SC), round(rect.h * kit.SC)), pygame.SRCALPHA)
        flash.fill((255, 98, 112, int(70 * (0.5 + 0.5 * math.sin(p * 12)))))
        s.blit(flash, (round(rect.x * kit.SC), round(rect.y * kit.SC)))

    # =====================================================================
    # Vòng lặp chính: nhận phím / chuột rồi gọi press()
    # =====================================================================
    def to_canvas(self, pos):
        L = self.LAYOUT
        ww, wh = self.win.get_size()
        sc = min(ww / L.W, wh / L.H)
        ox, oy = (ww - L.W * sc) / 2, (wh - L.H * sc) / 2
        return ((pos[0] - ox) / sc, (pos[1] - oy) / sc)

    def handle_key(self, k):
        keys = {pygame.K_SPACE: "play", pygame.K_RIGHT: "next", pygame.K_LEFT: "back", pygame.K_n: "node", pygame.K_r: "reset",
                pygame.K_UP: "fast", pygame.K_DOWN: "slow", pygame.K_g: "rand", pygame.K_t: "edit", pygame.K_v: "replay"}
        if k in keys:
            self.press(keys[k])
        elif k == pygame.K_F11:
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.win = pygame.display.set_mode(self.win_size, pygame.RESIZABLE)
        elif pygame.K_1 <= k <= pygame.K_9:
            self.press(f"p{k - pygame.K_1}")

    def handle_click(self, m):
        L = self.LAYOUT
        for b in self.buttons:
            if b.rect.collidepoint(m):
                self.press(b.key)
                return
        if L.bar_y - 6 <= m[1] <= L.bar_y + 12 and 12 <= m[0] <= L.W - 12:                    # bấm lên thanh tiến độ để tua
            self.session.stop_replay()
            self.session.player.seek(int((m[0] - 12) / (L.W - 24) * len(self.session.player.events)))

    def run(self):
        while True:
            dt = min(0.05, self.clock.tick(60) / 1000)
            self.win = pygame.display.get_surface()
            self.mouse = self.to_canvas(pygame.mouse.get_pos())
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE and not self.dialog):
                    pygame.quit()
                    return
                if self.dialog:
                    self.dialog.handle_event(e, self.to_canvas(e.pos) if hasattr(e, "pos") else None)
                    continue
                if e.type == pygame.KEYDOWN:
                    self.handle_key(e.key)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.handle_click(self.to_canvas(e.pos))
            self.apply_scale()
            self.update(dt)
            self.draw()
            self.win.fill((8, 10, 16))
            ww, wh = self.win.get_size()
            cw, ch = self.canvas.get_size()
            self.win.blit(self.canvas, ((ww - cw) // 2, (wh - ch) // 2))
            pygame.display.flip()
