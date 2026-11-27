"""LOGIC của app UCS 8-puzzle (không dùng pygame).

    flat / grid        đổi qua lại giữa bàn 3x3 ((1,2,3),...) và 9 ô (1,2,3,...)
    Puzzle8Session     phiên chạy UCS trên 8-puzzle (bài toán nằm ở problems/puzzle8.py)
    Puzzle8Editor      mô hình của hộp thoại "Tự đặt": đổi chỗ ô, xáo, đích chuẩn, kiểm tra, áp dụng
"""
from desktop.ucs.common.session import UCSSession
from problems import puzzle8
from tracing.stats import random_initial


def flat(state):
    """Bàn 3x3 ((1, 2, 3), ...) -> 9 ô (1, 2, 3, ...)."""
    return tuple(v for row in state for v in row)


def grid(cells):
    """9 ô -> bàn 3x3."""
    cells = tuple(cells)
    return (cells[0:3], cells[3:6], cells[6:9])


class Puzzle8Session(UCSSession):
    PROBLEM = puzzle8
    PROBLEM_ID = "puzzle8"
    UNSOLVABLE_MSG = "Không giải được: hai bàn cờ khác tính chẵn lẻ. Hãy đổi chỗ thêm một cặp ô."


class Puzzle8Editor:
    """Hộp thoại tự đặt trạng thái đầu và đích. Hai bàn cờ được giữ dưới dạng 9 ô để dễ bấm đổi chỗ."""

    def __init__(self, session):
        self.session = session
        self.init = list(flat(session.init))
        self.goal = list(flat(session.goal))
        self.selected = None            # (bàn nào, ô nào) đang chọn, hoặc None
        self.check = None
        self.recheck()

    def boards(self):
        return {"init": self.init, "goal": self.goal}

    def click_cell(self, which, i):
        """Bấm một ô: chọn ô đó; bấm ô thứ hai cùng bàn thì đổi chỗ; bấm lại ô đang chọn thì bỏ chọn."""
        sel = self.selected
        if sel is None or sel[0] != which:
            self.selected = (which, i)
        elif sel[1] == i:
            self.selected = None
        else:
            cells = self.boards()[which]
            cells[sel[1]], cells[i] = cells[i], cells[sel[1]]
            self.selected = None
            self.recheck()

    def use_standard_goal(self):
        self.goal = list(flat(puzzle8.GOAL_STATE))
        self.selected = None
        self.recheck()

    def shuffle(self):
        init, _ = random_initial("puzzle8", "ucs", grid(self.goal))
        self.init = list(flat(init))
        self.selected = None
        self.recheck()

    def recheck(self):
        self.check = self.session.check(grid(self.init), grid(self.goal))

    @property
    def ok(self):
        return self.check.ok

    def apply(self):
        """Trả về (trạng thái đầu, đích) để nạp, hoặc None nếu bài chưa dùng được."""
        if not self.ok:
            return None
        return grid(self.init), grid(self.goal)
