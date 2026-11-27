"""LOGIC của app UCS robot hút bụi (không dùng pygame).

Trạng thái: ("B", "C", "D", "D") = robot ở phòng B, phòng A sạch (C), phòng B bẩn (D), phòng C bẩn.

    letter / room_index   đổi giữa số thứ tự phòng (0, 1, ...) và chữ phòng ("A", "B", ...)
    make_state / make_goal
    VacuumSession         phiên chạy UCS trên robot hút bụi (bài toán nằm ở problems/vacuum.py)
    VacuumEditor          mô hình của hộp thoại "Tự đặt": số phòng, robot ở đâu, phòng nào bẩn, đích
"""
from desktop.ucs.common.session import UCSSession
from problems import vacuum

MIN_ROOMS, MAX_ROOMS = 2, 6


def letter(i):
    return chr(65 + i)


def room_index(state):
    """Phòng robot đang đứng, dạng số: 'A' -> 0, 'B' -> 1, ..."""
    return ord(state[0]) - ord("A")


def make_state(pos, dirt):
    """pos: số thứ tự phòng robot đứng; dirt: danh sách True/False (phòng có bẩn không)."""
    return (letter(pos),) + tuple("D" if d else "C" for d in dirt)


def make_goal(n, pos):
    """Đích: robot dừng ở phòng pos, cả n phòng đều sạch."""
    return (letter(pos),) + ("C",) * n


class VacuumSession(UCSSession):
    PROBLEM = vacuum
    PROBLEM_ID = "vacuum"
    RANDOM_KEEPS_GOAL = False
    REPLAY_STEP = 1.2
    REPLAY_MAX_SPEED = 3.0
    REPLAY_HOLD = 1.4

    @property
    def rooms(self):
        return len(self.init) - 1


class VacuumEditor:
    def __init__(self, session):
        self.n = session.rooms
        self.pos = room_index(session.init)             # robot bắt đầu ở phòng nào
        self.dirt = [v == "D" for v in session.init[1:]]
        self.goal_pos = room_index(session.goal)        # đích: robot phải dừng ở phòng nào

    def change_rooms(self, delta):
        old = self.n
        n = max(MIN_ROOMS, min(MAX_ROOMS, old + delta))
        if n == old:
            return
        self.dirt = self.dirt[:n] + [True] * max(0, n - len(self.dirt))     # phòng thêm vào thì cho bẩn
        self.pos = min(self.pos, n - 1)
        self.goal_pos = min(self.goal_pos, n - 1) if self.goal_pos < old - 1 else n - 1   # đích ở phòng cuối thì bám theo
        self.n = n

    def set_start(self, i):
        self.pos = i

    def toggle_dirt(self, i):
        self.dirt[i] = not self.dirt[i]

    def set_goal(self, i):
        self.goal_pos = i

    def state_space_text(self):
        n = self.n
        return (f"Không gian trạng thái: {n} × 2^{n} = {n * 2 ** n} trạng thái. "
                f"Đích: robot ở phòng {letter(self.goal_pos)}, mọi phòng sạch (C).")

    def apply(self):
        return make_state(self.pos, self.dirt), make_goal(self.n, self.goal_pos)
