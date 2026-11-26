"""Bài toán 8-puzzle: bàn 3x3, 8 ô số và 1 ô trống (số 0). Trượt ô trống để về trạng thái đích.

Trạng thái là bộ 9 số đọc theo hàng, từ trái sang phải, từ trên xuống dưới:
    (1, 2, 3,
     4, 0, 6,      <- 0 là ô trống
     7, 5, 8)
"""
import random

from core.problem import Problem

# =====================================================================
# 1. TRẠNG THÁI BAN ĐẦU / ĐÍCH / BÀI MẪU
# =====================================================================

GOAL_STATE = (1, 2, 3,
              4, 5, 6,
              7, 8, 0)

INITIAL_STATE = (1, 2, 3,
                 4, 0, 6,
                 7, 5, 8)

# Các bài mẫu hiện trên giao diện (nút "Bài mẫu"): (nhãn, trạng thái đầu).
# Mỗi thuật toán có bộ riêng vì DFS đi rất sâu, bài nhỏ với BFS có thể rất dài với DFS.
PRESETS = {
    "bfs": [
        ("2 bước", (1, 2, 3, 4, 0, 6, 7, 5, 8)),
        ("4 bước", (1, 5, 2, 4, 0, 3, 7, 8, 6)),
        ("6 bước", (0, 2, 3, 1, 8, 5, 4, 7, 6)),
    ],
    "dfs": [
        ("34 bước", (4, 1, 3, 2, 5, 6, 0, 7, 8)),
        ("Notebook", INITIAL_STATE),
        ("292 bước", (2, 3, 0, 1, 4, 6, 7, 5, 8)),
    ],
}
DEFAULT_PRESET = 1   # bài mẫu được mở sẵn khi vào trang (đếm từ 0)


# =====================================================================
# 2. HÀNH ĐỘNG: ô trống có thể đi Lên / Xuống / Trái / Phải (nếu không chạm mép)
# =====================================================================

def actions_puzzle8(state):
    i = state.index(0)          # vị trí ô trống
    hang, cot = divmod(i, 3)
    out = []
    if hang > 0:
        out.append("Lên")
    if hang < 2:
        out.append("Xuống")
    if cot > 0:
        out.append("Trái")
    if cot < 2:
        out.append("Phải")
    return out


# =====================================================================
# 3. KẾT QUẢ HÀNH ĐỘNG: đổi chỗ ô trống với ô bên cạnh theo hướng đi
# =====================================================================

HUONG = {"Lên": (-1, 0), "Xuống": (1, 0), "Trái": (0, -1), "Phải": (0, 1)}


def result_puzzle8(state, action):
    i = state.index(0)
    hang, cot = divmod(i, 3)
    dh, dc = HUONG[action]
    j = (hang + dh) * 3 + (cot + dc)    # vị trí ô sẽ đổi chỗ với ô trống
    new_state = list(state)
    new_state[i], new_state[j] = new_state[j], new_state[i]
    return tuple(new_state)


# =====================================================================
# 4. TẠO PROBLEM (giống trên lớp: Problem(initial, goal, actions, result))
# =====================================================================

def make_problem(initial_state=INITIAL_STATE, goal_state=GOAL_STATE):
    return Problem(tuple(initial_state), tuple(goal_state), actions_puzzle8, result_puzzle8)


# =====================================================================
# 5. TIỆN ÍCH CHO GIAO DIỆN (không thuộc thuật toán)
# =====================================================================

def _inversions(state):
    t = [v for v in state if v]
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t)) if t[i] > t[j])


def solvable(initial_state, goal_state):
    """Bàn 3x3: giải được khi hai trạng thái có cùng tính chẵn lẻ của số cặp nghịch thế."""
    return _inversions(initial_state) % 2 == _inversions(goal_state) % 2


def random_goal():
    return GOAL_STATE


def scramble(goal_state):
    """Xáo ngẫu nhiên vài nước từ đích (nên luôn giải được)."""
    s, prev = tuple(goal_state), None
    for _ in range(random.randint(6, 9)):
        opts = [o for o in (result_puzzle8(s, a) for a in actions_puzzle8(s)) if o != prev]
        prev, s = s, random.choice(opts)
    return s


def describe_action(action):
    """Câu mô tả ngắn hành động, dùng trong lời thuyết minh dòng child_node."""
    return "trượt ô trống để sinh nút con"
