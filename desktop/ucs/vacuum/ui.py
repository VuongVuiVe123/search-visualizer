"""GIAO DIỆN app UCS robot hút bụi: chỉ vẽ và nhận phím / chuột.

Chạy:   python desktop/ucs/vacuum/ui.py

Mọi việc "làm gì" nằm ở logic.py (VacuumSession, VacuumEditor). Tệp này gọi sang đó rồi vẽ kết quả.
Phần khung chung (đầu trang, khung code, bảng node, FRONTIER, EXPLORED, nút điều khiển) ở common/screen.py.
Hình vẽ riêng: scene.py (ngôi nhà, robot), cards.py (thẻ trạng thái). Tệp này ghép chúng lại và thêm
chuyển động của robot, khung "nút đang xét", hộp thoại tự đặt.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from desktop.ucs.common.preflight import check_environment  # noqa: E402

check_environment()         # báo lỗi tiếng Việt nếu thiếu pygame hoặc thiếu thư mục, trước khi nạp pygame

import pygame  # noqa: E402

from desktop.ucs.common import kit  # noqa: E402
from desktop.ucs.common.kit import Button, G, alpha_poly, font, panel, setclip, shade, sm, text  # noqa: E402
from desktop.ucs.common.screen import VERDICT_COLOR, VERDICT_COMPACT, Layout, Metrics, UCSScreen  # noqa: E402
from desktop.ucs.common.theme import ACCENT, GOLD, GREEN, INK_ON_ACCENT, MUTED, ORANGE, PANEL_L, TEXT  # noqa: E402
from desktop.ucs.vacuum.cards import CLEAN, DIRTY, BigCard, blit_state  # noqa: E402
from desktop.ucs.vacuum.logic import VacuumEditor, VacuumSession, letter, room_index  # noqa: E402
from desktop.ucs.vacuum.scene import ISO, SCENE, Scene, P, draw_robot  # noqa: E402

ACTION_LABEL = {"Suck": "↓ Suck (hút bụi)", "Left": "← Left", "Right": "Right →"}


class VacuumScreen(UCSScreen):
    CAPTION = "Robot hút bụi nhiều phòng - UCS"
    TABLE_TITLE = "bảng NODE theo độ sâu  (mỗi thẻ = một trạng thái [vị trí robot, các phòng])"
    VERDICT_STYLE = VERDICT_COMPACT
    LAYOUT = Layout(W=1400, H=940, code=pygame.Rect(12, 92, 500, 580), tab=pygame.Rect(524, 444, 864, 228),
                    side=pygame.Rect(1100, 100, 280, 324), q_y=684, e_y=792, bar_y=872, btn_y=886,
                    preset_x=640, preset_w=82, preset_step=90, tools=(92, 112, 150), replay_stop="Dừng robot",
                    line_h=21, code_size=13, preset_label=False)

    def __init__(self):
        side = self.LAYOUT.side
        self.scene = Scene()
        self.node_card = BigCard((side.x + 12, side.y + 28, side.w - 24, 64))
        self.child_card = BigCard((side.x + 12, side.y + 130, side.w - 24, 64))
        self.child_cache = None             # trạng thái nút con gần nhất (để thẻ child không trống khi chưa có nút con)
        self.s_pos, self.s_dirt, self.s_theta, self.spin = 0.0, [], 0.0, 0.0    # chuyển động của robot và bụi trong nhà
        self.sucking, self.particles = False, []
        super().__init__(VacuumSession())

    @property
    def n(self):
        return self.session.rooms

    @property
    def SUBTITLE(self):
        return f"Robot hút bụi · {self.n} phòng"

    # ---------- phần riêng: kích thước thẻ, vị trí, hình vẽ ----------
    def build_metrics(self):
        L, w = self.LAYOUT, max(76, 16 * self.n + 16)                # thẻ rộng ra khi nhiều phòng
        room = L.W - 24 - L.q_x - 40
        return Metrics(cell=(w, 50, 8, 6), q=(w, 50, w + 10, max(4, int(room // (w + 10)))), e=(w - 6, 46, w, max(4, int(room // w))))

    def draw_card(self, s, state, cx, cy, w, h, scale, alpha):
        return blit_state(s, state, cx, cy, w, h, scale, alpha)

    def anchors(self):
        return {"child": self.child_card.rect.center, "node": self.node_card.rect.center}

    def draw_goal(self, s, x):
        text(s, "Đích", font("segoeui", 14, True), GREEN, (x - 8, 30), "midright")
        text(s, f"robot ở {self.session.goal[0]}, sạch hết", font("segoeui", 13), TEXT, (x - 8, 50), "midright")

    def on_loaded(self):
        if self.scene.n != self.n:
            self.scene.cfg(self.n)
        self.node_card.reset()
        self.child_card.reset()
        self.child_cache = None
        init = self.session.init
        self.s_pos = float(room_index(init))
        self.s_dirt = [1.0 if v == "D" else 0.0 for v in init[1:]]
        self.s_theta, self.spin, self.particles = 0.0, 0.0, []

    def on_rescale(self):
        self.scene.bg = None

    # ---------- chuyển động của robot ----------
    def update_stage(self, dt, ev):
        replay = self.session.replay
        self.update_scene(replay.state if replay else ev["node_state"], dt)
        self.node_card.update(ev["node_state"], dt, True)
        ch = ev["child"]
        if ch:
            self.child_cache = ch[0]
        self.child_card.update(self.child_state(ev), dt, bool(ch))

    def child_state(self, ev):
        return ev["child"][0] if ev["child"] else (self.child_cache or ev["node_state"])

    def update_scene(self, state, dt):
        """Robot trượt sang phòng của `state`, quay mặt theo hướng đi, hút bụi ở phòng vừa sạch."""
        sc = self.scene
        target = float(room_index(state))
        old = self.s_pos
        self.s_pos = sm(self.s_pos, target, 5, dt)
        a, b = sc.pos_at(old), sc.pos_at(self.s_pos)
        dr, dc = b[0] - a[0], b[1] - a[1]
        if math.hypot(dr, dc) > 0.004:
            diff = (math.atan2(dc, dr) - self.s_theta + math.pi) % (2 * math.pi) - math.pi
            self.s_theta += diff * min(1.0, dt * 10)
        sucking = False
        for i in range(self.n):
            tv = 1.0 if state[1 + i] == "D" else 0.0
            if tv == 0.0 and self.s_dirt[i] > 0.04 and abs(self.s_pos - i) < 0.6:
                sucking = True
            self.s_dirt[i] = sm(self.s_dirt[i], tv, 4, dt)
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

    # ---------- ngôi nhà ----------
    def draw_stage(self, s, ev, p):
        sc, n = self.scene, self.n
        if sc.bg is None:
            sc.build_bg(pygame.Surface(s.get_size()))
        if sc.objs is None:
            sc.build_objs()
        rp = kit.px_rect(SCENE)
        s.blit(sc.bg, rp.topleft, rp)
        clip = s.get_clip()
        setclip(s, SCENE)
        for i in range(n):                                              # phòng sạch: sàn sáng lên
            gr, gc = sc.cell_of(i)
            r0, c0 = sc.origin(gr, gc)
            cl = 1 - self.s_dirt[i]
            if cl > 0.02:
                alpha_poly(s, [P(r0, c0), P(r0, c0 + sc.RS), P(r0 + sc.RS, c0 + sc.RS), P(r0 + sc.RS, c0)], (255, 255, 255, int(46 * cl)))
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260)
        for i in range(n):                                              # phòng bẩn: vệt bụi và vòng vàng nhấp nháy
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
        drawn = False
        for depth, fn in sc.objs:                                       # đồ đạc và robot xếp theo độ sâu để che nhau đúng
            if not drawn and depth >= rd:
                draw_robot(s, rc, cc, self.s_theta, self.spin, 0.44, self.sucking)
                drawn = True
            fn(s)
        if not drawn:
            draw_robot(s, rc, cc, self.s_theta, self.spin, 0.44, self.sucking)
        for i in range(n):                                              # nhãn phòng A, B, C...
            gr, gc = sc.cell_of(i)
            r0, c0 = sc.origin(gr, gc)
            x, y = P(r0 + sc.RS - 0.28, c0 + 0.36)
            on = abs(self.s_pos - i) < 0.5
            r = pygame.Rect(x - 13, y - 10, 26, 20)
            G.rect(s, ACCENT if on else (30, 38, 58), r, border_radius=6)
            text(s, letter(i), font("segoeui", 14, True), INK_ON_ACCENT if on else TEXT, r.center, "center")
        for pr, pc, z, age in self.particles:                           # hạt bụi bị hút vào robot
            x0, y0 = P(pr, pc, z)
            x1, y1 = P(rc, cc, 18)
            t = age / 0.45
            G.circle(s, (170, 162, 152), (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t), 3)
        replay = self.session.replay
        if ev["child"] and not replay:                                  # mũi tên báo robot sắp đi đâu
            self.draw_intent(s, ev)
        s.set_clip(clip)
        G.rect(s, PANEL_L, SCENE, 1, border_radius=14)
        text(s, "ngôi nhà (mỗi phòng là một ô của bài toán)", font("segoeui", 14, True), GOLD, (SCENE.x + 14, SCENE.y + 8))
        if replay:
            chip = pygame.Rect(SCENE.x + 12, SCENE.bottom - 40, 330, 28)
            G.rect(s, (10, 30, 20), chip, border_radius=14)
            G.rect(s, GREEN, chip, 2, border_radius=14)
            text(s, f"Robot chạy lời giải: bước {replay.k}/{replay.n} · {replay.action or 'bắt đầu'}", font("segoeui", 14, True),
                 GREEN, chip.center, "center")

    def draw_intent(self, s, ev):
        """Đường nét đứt từ phòng hiện tại tới phòng nút con (hoặc vòng tròn nếu đứng yên) kèm tên hành động."""
        sc = self.scene
        a_idx, b_idx = room_index(ev["node_state"]), room_index(ev["child"][0])
        if a_idx != b_idx:
            a, b = sc.center(a_idx), sc.center(b_idx)
            for k in range(9):
                t0 = k / 9
                t1 = t0 + 0.05
                G.line(s, ACCENT, P(a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, 2),
                       P(a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1, 2), 4)
            hx, hy = P(b[0], b[1], 2)
            G.circle(s, ACCENT, (hx, hy), 7)
        else:
            rc2, cc2 = sc.center(a_idx)
            ring = [P(rc2 + 0.9 * math.cos(a), cc2 + 0.9 * math.sin(a), 2) for a in [2 * math.pi * k / 30 for k in range(30)]]
            G.polygon(s, ACCENT, ring, 3)
        tx, ty = P(*sc.center(b_idx), 70)
        chip = pygame.Rect(tx - 44, ty - 14, 88, 26)
        G.rect(s, shade(ACCENT, 0.3), chip, border_radius=13)
        G.rect(s, ACCENT, chip, 2, border_radius=13)
        text(s, ev["act"], font("segoeui", 14, True), ACCENT, chip.center, "center")

    # ---------- khung bên phải: nút đang xét ----------
    def draw_side(self, s, ev, p):
        r, nc, cc = self.LAYOUT.side, self.node_card, self.child_card
        panel(s, r, "nút đang xét", ORANGE)
        text(s, f"g = {ev['node_cost']}", font("segoeui", 12), GOLD, (r.right - 14, r.y + 12), "topright")
        nc.draw(s, "node", ORANGE, ev["node_state"])
        if ev["act"]:                                                   # hành động đang thử
            chip = pygame.Rect(0, 0, 160, 22)
            chip.midtop = (r.centerx, nc.rect.bottom + 6)
            G.rect(s, shade(ACCENT, 0.3), chip, border_radius=11)
            G.rect(s, ACCENT, chip, 2, border_radius=11)
            text(s, ACTION_LABEL[ev["act"]], font("segoeui", 14, True), ACCENT, chip.center, "center")
        border = VERDICT_COLOR[ev["verdict"]]
        cc.draw(s, "child", border, self.child_state(ev))
        if ev["child"]:
            text(s, f"g = {ev['child'][3]}", font("segoeui", 12, True), GOLD, (cc.rect.right - 10, cc.rect.y + 4), "topright")
        if ev["verdict"] == "dup" and ev["child"]:
            self.flash_duplicate(s, cc.rect, p)
        self.draw_verdict(s, r, cc.rect.bottom + 8, ev, p)

    def open_editor(self):
        self.dialog = VacuumDialog(self)


class VacuumDialog:
    """Hộp thoại "Tự đặt": vẽ và nhận chuột. Việc đổi số phòng, chọn bụi, áp dụng do VacuumEditor (logic.py) làm."""
    MOD = pygame.Rect(320, 210, 760, 520)

    def __init__(self, screen):
        self.screen = screen
        self.editor = VacuumEditor(screen.session)
        M = self.MOD
        self.buttons = [
            Button((M.x + 40, M.y + 72, 40, 36), "−", "minus"),
            Button((M.x + 200, M.y + 72, 40, 36), "+", "plus"),
            Button((M.right - 40 - 230, M.bottom - 62, 110, 42), "Hủy", "cancel"),
            Button((M.right - 40 - 112, M.bottom - 62, 112, 42), "Áp dụng", "apply"),
        ]

    def column(self, i):
        w = (self.MOD.w - 80) / self.editor.n
        return self.MOD.x + 40 + i * w, w

    def rects(self, i):
        """Ba ô của phòng i: chọn nơi robot bắt đầu, bật/tắt bụi, chọn phòng đích."""
        x, w = self.column(i)
        M = self.MOD
        return (pygame.Rect(x + 6, M.y + 150, w - 12, 34), pygame.Rect(x + 6, M.y + 224, w - 12, 84),
                pygame.Rect(x + 6, M.y + 350, w - 12, 34))

    def press(self, key):
        ed = self.editor
        if key == "cancel":
            self.screen.dialog = None
        elif key == "minus":
            ed.change_rooms(-1)
        elif key == "plus":
            ed.change_rooms(+1)
        elif key == "apply":
            self.screen.dialog = None
            self.screen.apply_custom(*ed.apply())

    def handle_event(self, e, m):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.press("cancel")
            elif e.key == pygame.K_RETURN:
                self.press("apply")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.buttons:
                if b.rect.collidepoint(m):
                    self.press(b.key)
                    return
            for i in range(self.editor.n):
                start, dirt, goal = self.rects(i)
                if start.collidepoint(m):
                    self.editor.set_start(i)
                if dirt.collidepoint(m):
                    self.editor.toggle_dirt(i)
                if goal.collidepoint(m):
                    self.editor.set_goal(i)

    def draw(self, s, mouse):
        ed, M = self.editor, self.MOD
        veil = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        veil.fill((4, 6, 12, 195))
        s.blit(veil, (0, 0))
        G.rect(s, (22, 29, 46), M, border_radius=18)
        G.rect(s, ACCENT, M, 2, border_radius=18)
        text(s, "Tự đặt phòng, bụi, robot và đích", font("segoeui", 22, True), TEXT, (M.x + 40, M.y + 16))
        text(s, "Số phòng", font("segoeui", 14, True), MUTED, (M.x + 40, M.y + 52))
        text(s, str(ed.n), font("segoeui", 26, True), ACCENT, (M.x + 160, M.y + 90), "center")
        text(s, "Bấm vào ô để chọn. Hàng giữa: bấm để bật / tắt bụi.", font("segoeui", 14), MUTED, (M.x + 280, M.y + 82))
        for label, y in (("Robot bắt đầu ở phòng", M.y + 128), ("Phòng nào đang bẩn (D)?", M.y + 196),
                         ("Đích: robot phải dừng ở phòng", M.y + 330)):
            text(s, label, font("segoeui", 15, True), TEXT, (M.x + 40, y))
        for i in range(ed.n):
            start, dirt, goal = self.rects(i)
            on = ed.pos == i
            G.rect(s, ORANGE if on else PANEL_L, start, border_radius=8)
            text(s, f"Phòng {letter(i)}", font("segoeui", 14, True), (20, 20, 26) if on else TEXT, start.center, "center")
            G.rect(s, DIRTY if ed.dirt[i] else CLEAN, dirt, border_radius=10)
            if ed.dirt[i]:
                for dx, dy in ((0.25, 0.3), (0.6, 0.5), (0.4, 0.75), (0.75, 0.25)):
                    G.circle(s, (60, 44, 30), (dirt.x + dirt.w * dx, dirt.y + dirt.h * dy), 5)
            text(s, f"{letter(i)}: " + ("D (bẩn)" if ed.dirt[i] else "C (sạch)"), font("segoeui", 14, True), (255, 255, 255),
                 (dirt.centerx, dirt.bottom - 6), "midbottom")
            if on:
                G.circle(s, (18, 18, 22), (dirt.centerx, dirt.y + 28), 15)
                G.circle(s, ORANGE, (dirt.centerx, dirt.y + 28), 5)
            at_goal = ed.goal_pos == i
            G.rect(s, GREEN if at_goal else PANEL_L, goal, border_radius=8)
            text(s, f"Phòng {letter(i)}", font("segoeui", 14, True), (10, 30, 20) if at_goal else TEXT, goal.center, "center")
        text(s, ed.state_space_text(), font("segoeui", 14), MUTED, (M.x + 40, M.y + 410))
        for b in self.buttons:
            b.active = b.key == "apply"
            b.draw(s, mouse)


def main():
    kit.enable_dpi_awareness()
    VacuumScreen().run()


if __name__ == "__main__":
    main()
