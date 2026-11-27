"""GIAO DIỆN app UCS 8-puzzle: chỉ vẽ và nhận phím / chuột.

Chạy:   python desktop/ucs/puzzle8/ui.py

Mọi việc "làm gì" nằm ở logic.py (Puzzle8Session, Puzzle8Editor). Tệp này gọi sang đó rồi vẽ kết quả.
Phần khung chung (đầu trang, khung code, bảng node, FRONTIER, EXPLORED, nút điều khiển) ở common/screen.py.
Tệp này chỉ thêm phần riêng của 8-puzzle: bàn cờ lớn, khung "nút đang xét", chạy lời giải, hộp thoại tự đặt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from desktop.ucs.common.preflight import check_environment  # noqa: E402

check_environment()         # báo lỗi tiếng Việt nếu thiếu pygame hoặc thiếu thư mục, trước khi nạp pygame

import pygame  # noqa: E402

from desktop.ucs.common import kit  # noqa: E402
from desktop.ucs.common.kit import Button, G, font, panel, shade, text, wrap  # noqa: E402
from desktop.ucs.common.screen import VERDICT_COLOR, Layout, Metrics, UCSScreen  # noqa: E402
from desktop.ucs.common.theme import (ACCENT, CYAN, GOLD, GREEN, LEVEL_COLOR, MUTED, ORANGE, PANEL_L, TEXT)  # noqa: E402
from desktop.ucs.puzzle8.boards import TILE_COL, BigBoard, blit_board  # noqa: E402
from desktop.ucs.puzzle8.logic import Puzzle8Editor, Puzzle8Session, flat  # noqa: E402

GLYPH = {"Lên": "↑", "Xuống": "↓", "Trái": "←", "Phải": "→"}      # mũi tên cho từng hành động


class Puzzle8Screen(UCSScreen):
    CAPTION = "UCS 8-puzzle - trực quan hóa từng dòng code"
    SUBTITLE = "8-puzzle · từng dòng code sáng lên trên hình"
    TABLE_TITLE = "bảng trạng thái theo độ sâu  (mỗi ô = một nút)"
    LAYOUT = Layout(W=1400, H=900, code=pygame.Rect(12, 92, 528, 540), tab=pygame.Rect(552, 92, 468, 540),
                    side=pygame.Rect(1032, 92, 356, 540), q_y=644, e_y=752, bar_y=832, btn_y=846,
                    preset_x=690, preset_w=84, preset_step=92, tools=(104, 128, 140), replay_stop="Dừng",
                    line_h=20, code_size=14)

    def __init__(self):
        side = self.LAYOUT.side
        self.node_board = BigBoard(side.centerx - 66, side.y + 56)
        self.child_board = BigBoard(side.centerx - 66, side.y + 56 + 132 + 68)
        self.last_child_key = None
        self.replay_k = None                    # trạng thái của lời giải đang hiện trên bàn cờ lớn
        super().__init__(Puzzle8Session())

    # ---------- phần riêng: kích thước thẻ, vị trí, hình vẽ ----------
    def build_metrics(self):
        return Metrics(cell=(50, 50, 6, 8), q=(46, 46, 60, 20), e=(52, 52, 58, 20))

    def draw_card(self, s, state, cx, cy, w, h, scale, alpha):
        return blit_board(s, state, cx, cy, w, scale, alpha)

    def anchors(self):
        return {"child": self.child_board.center, "node": self.node_board.center}

    def draw_goal(self, s, x):
        text(s, "Đích", font("segoeui", 14, True), GREEN, (x - 66, 38), "midright")
        blit_board(s, self.session.goal, x - 34, 38, 46)

    def on_loaded(self):
        self.node_board.clear()
        self.child_board.clear()
        self.child_board.alpha = 0.0
        self.last_child_key = None
        self.replay_k = None
        self.sync_boards(snap=True)

    # ---------- chuyển động của hai bàn cờ lớn ----------
    def sync_boards(self, snap=False):
        """Đưa hai bàn cờ lớn về đúng nút đang xét / nút con của sự kiện hiện tại."""
        ev, nb, cb = self.ev, self.node_board, self.child_board
        if nb.state != flat(ev["node_state"]):
            nb.set_state(ev["node_state"])
        ch = ev["child"]
        key = ch[2] if ch else None
        if ch and key != self.last_child_key:
            cb.clear()
            cb.set_state(ch[0], copy_from=nb)
        self.last_child_key = key
        if snap:
            nb.snap()
            cb.snap()

    def sync_replay_board(self, replay):
        nb = self.node_board
        if replay.k == self.replay_k:
            return
        if self.replay_k is None:               # vừa bắt đầu chạy lời giải: đặt ngay bàn cờ về trạng thái đầu
            nb.clear()
            nb.set_state(replay.state)
            nb.snap()
        else:
            nb.set_state(replay.state)
        self.replay_k = replay.k

    def update_stage(self, dt, ev):
        replay = self.session.replay
        if replay:
            self.sync_replay_board(replay)
        else:
            self.replay_k = None
            self.sync_boards()
        self.node_board.update(dt)
        self.child_board.update(dt)
        self.child_board.alpha = kit.sm(self.child_board.alpha, 1.0 if ev["child"] else 0.18, 8, dt)

    # ---------- khung bên phải ----------
    def draw_side(self, s, ev, p):
        if self.session.replay:
            self.draw_replay(s)
            return
        side, nb, cb = self.LAYOUT.side, self.node_board, self.child_board
        panel(s, side, "nút đang xét", ORANGE)
        text(s, "node", font("segoeui", 15, True), ORANGE, (nb.x - 2, nb.y - 20))
        text(s, f"g = {ev['node_cost']}", font("segoeui", 14), GOLD, (nb.x + nb.size + 2, nb.y - 19), "topright")
        nb.draw(s, ORANGE if ev["node_eid"] is not None or ev["line"] >= 1 else PANEL_L)
        if ev["act"]:                                                   # hành động đang thử: ↑ Lên, ↓ Xuống, ...
            r = pygame.Rect(0, 0, 148, 30)
            r.midtop = (side.centerx, nb.y + nb.size + 12)
            G.rect(s, (32, 42, 66), r, border_radius=15)
            G.rect(s, CYAN, r, 2, border_radius=15)
            text(s, f"{GLYPH[ev['act']]}  {ev['act']}", font("segoeui", 18, True), CYAN, r.center, "center")
        border = VERDICT_COLOR[ev["verdict"]]
        text(s, "child", font("segoeui", 15, True), border, (cb.x - 2, cb.y - 20))
        if ev["child"]:
            text(s, f"g = {ev['child'][3]}", font("segoeui", 14), GOLD, (cb.x + cb.size + 2, cb.y - 19), "topright")
        cb.draw(s, border, cb.alpha)
        if ev["verdict"] == "dup" and ev["child"]:
            self.flash_duplicate(s, pygame.Rect(cb.x, cb.y, cb.size, cb.size), p)
        self.draw_verdict(s, side, cb.y + cb.size + 12, ev, p)

    def draw_replay(self, s):
        """Chạy lời giải: bàn cờ lớn trượt lần lượt từng nước từ trạng thái đầu tới đích."""
        side, nb, rp = self.LAYOUT.side, self.node_board, self.session.replay
        panel(s, side, "chạy lời giải", GOLD)
        text(s, "ĐÃ TỚI ĐÍCH" if rp.k == rp.n else f"bước {rp.k} / {rp.n}", font("segoeui", 15, True), GOLD,
             (side.centerx, nb.y - 20), "midtop")
        nb.draw(s, GREEN if rp.k == rp.n else GOLD)
        r = pygame.Rect(0, 0, 148, 30)
        r.midtop = (side.centerx, nb.y + nb.size + 12)
        G.rect(s, shade(GOLD, 0.3), r, border_radius=15)
        G.rect(s, GOLD, r, 2, border_radius=15)
        act = rp.action
        text(s, f"{GLYPH[act]}  {act}" if act else "trạng thái đầu", font("segoeui", 18, True), GOLD, r.center, "center")
        by, bw = r.bottom + 22, side.w - 48
        G.rect(s, PANEL_L, (side.x + 24, by, bw, 8), border_radius=4)
        G.rect(s, GOLD, (side.x + 24, by, max(8, bw * rp.k / max(1, rp.n)), 8), border_radius=4)
        text(s, "các nước tiếp theo", font("segoeui", 13, True), MUTED, (side.x + 24, by + 22))
        upcoming = "  ".join(GLYPH[a] for a in rp.actions[rp.k:rp.k + 12]) or "—"
        text(s, upcoming, font("segoeui", 18, True), TEXT, (side.x + 24, by + 44))
        text(s, f"Lời giải {rp.n} bước · bấm \"Dừng\" hoặc phím V để thoát", font("segoeui", 12), MUTED,
             (side.centerx, side.bottom - 28), "midtop")

    def open_editor(self):
        self.dialog = Puzzle8Dialog(self)


class Puzzle8Dialog:
    """Hộp thoại "Tự đặt": vẽ hai bàn cờ và nhận chuột. Việc đổi ô, kiểm tra, áp dụng do Puzzle8Editor (logic.py) làm."""
    MOD = pygame.Rect(350, 170, 700, 500)
    CELL, GAP = 70, 6

    def __init__(self, screen):
        self.screen = screen
        self.editor = Puzzle8Editor(screen.session)
        M = self.MOD
        self.buttons = [
            Button((M.x + 56, M.y + 330, 222, 36), "Xáo ngẫu nhiên", "shuffle"),
            Button((M.right - 56 - 222, M.y + 330, 222, 36), "Đích chuẩn 1-8", "standard"),
            Button((M.right - 56 - 230, M.h + M.y - 58, 110, 40), "Hủy", "cancel"),
            Button((M.right - 56 - 112, M.h + M.y - 58, 112, 40), "Áp dụng", "apply"),
        ]

    def cell_rect(self, which, i):
        size = 3 * self.CELL + 2 * self.GAP
        bx = self.MOD.x + 56 if which == "init" else self.MOD.right - 56 - size
        r, c = divmod(i, 3)
        return pygame.Rect(bx + c * (self.CELL + self.GAP), self.MOD.y + 96 + r * (self.CELL + self.GAP), self.CELL, self.CELL)

    def press(self, key):
        ed = self.editor
        if key == "cancel":
            self.screen.dialog = None
        elif key == "apply":
            result = ed.apply()
            if result:
                self.screen.dialog = None
                self.screen.apply_custom(*result)
        elif key == "standard":
            ed.use_standard_goal()
        elif key == "shuffle":
            ed.shuffle()

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
            for which in ("init", "goal"):
                for i in range(9):
                    if self.cell_rect(which, i).collidepoint(m):
                        self.editor.click_cell(which, i)
                        return
            if not self.MOD.collidepoint(m):
                self.editor.selected = None

    def draw(self, s, mouse):
        ed, M = self.editor, self.MOD
        veil = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        veil.fill((4, 6, 12, 190))
        s.blit(veil, (0, 0))
        G.rect(s, (22, 29, 46), M, border_radius=18)
        G.rect(s, ACCENT, M, 2, border_radius=18)
        text(s, "Tự đặt trạng thái", font("segoeui", 22, True), TEXT, (M.x + 28, M.y + 18))
        text(s, "Bấm một ô rồi bấm ô thứ hai (cùng bàn cờ) để đổi chỗ hai ô.", font("segoeui", 14), MUTED, (M.x + 28, M.y + 52))
        for which, title, col in (("init", "Trạng thái đầu", ORANGE), ("goal", "Trạng thái đích", GREEN)):
            c0 = self.cell_rect(which, 0)
            text(s, title, font("segoeui", 16, True), col, (c0.x, c0.y - 36))
            size = 3 * self.CELL + 2 * self.GAP
            G.rect(s, (14, 18, 30), (c0.x - 8, c0.y - 8, size + 16, size + 16), border_radius=12)
            for i, v in enumerate(ed.boards()[which]):
                r = self.cell_rect(which, i)
                if v:
                    G.rect(s, TILE_COL[v], r, border_radius=10)
                    text(s, str(v), font("segoeui", 30, True), (26, 26, 40), r.center, "center")
                else:
                    G.rect(s, (30, 38, 58), r, border_radius=10)
                    text(s, "trống", font("segoeui", 13), MUTED, r.center, "center")
                if ed.selected == (which, i):
                    G.rect(s, CYAN, r.inflate(4, 4), 4, border_radius=12)
        text(s, "→", font("segoeui", 40, True), MUTED, (M.centerx, M.y + 96 + 111), "center")
        col = LEVEL_COLOR[ed.check.level]
        box = pygame.Rect(M.x + 56, M.y + 386, M.w - 112, 40)
        G.rect(s, shade(col, 0.22), box, border_radius=10)
        G.rect(s, col, box, 2, border_radius=10)
        for k, line in enumerate(wrap(ed.check.msg, font("segoeui", 15), box.w - 24)[:2]):
            text(s, line, font("segoeui", 15), col, (box.x + 12, box.y + 4 + k * 17))
        for b in self.buttons:
            b.active = b.key == "apply" and ed.ok
            b.draw(s, mouse)


def main():
    kit.enable_dpi_awareness()
    Puzzle8Screen().run()


if __name__ == "__main__":
    main()
