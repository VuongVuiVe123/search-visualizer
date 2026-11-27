"""Bài toán 8-puzzle: bàn 3x3, 8 ô số và 1 ô trống (số 0).
Trượt ô trống để về trạng thái đích.

Trạng thái là bàn cờ 3x3, mỗi hàng một bộ số:
    ((1, 2, 3),
     (4, 0, 6),      <- 0 là ô trống
     (7, 5, 8))
Dùng tuple (không sửa được) thay vì list để giao diện có thể dùng trạng thái làm khóa
khi lưu hình đã vẽ.
"""
import random

from core.problem import Problem

# =====================================================================
# 1. TRẠNG THÁI BAN ĐẦU / ĐÍCH / BÀI MẪU
# =====================================================================

INITIAL_STATE = ((1, 2, 3),
                 (4, 0, 6),
                 (7, 5, 8))

GOAL_STATE = ((1, 2, 3),
              (4, 5, 6),
              (7, 8, 0))

# Các bài mẫu hiện trên giao diện (nút "Bài mẫu"): (nhãn, trạng thái đầu).
# Mỗi thuật toán có bộ riêng vì DFS đi rất sâu, bài nhỏ với BFS có thể rất dài với DFS.
PRESETS = {
    "bfs": [
        ("2 bước", INITIAL_STATE),
        ("4 bước", ((1, 5, 2), (4, 0, 3), (7, 8, 6))),
        ("6 bước", ((0, 2, 3), (1, 8, 5), (4, 7, 6))),
    ],
    "dfs": [
        ("34 bước", ((4, 1, 3), (2, 5, 6), (0, 7, 8))),
        ("292 bước", ((2, 3, 0), (1, 4, 6), (7, 5, 8))),
        ("320 bước", INITIAL_STATE),
    ],
    "ucs": [                                    # đặt tên theo tổng chi phí g của lời giải rẻ nhất
        ("chi phí 3", INITIAL_STATE),
        ("chi phí 5", ((1, 5, 2), (4, 0, 3), (7, 8, 6))),
        ("chi phí 8", ((0, 2, 3), (1, 8, 5), (4, 7, 6))),
    ],
}
DEFAULT_PRESET = 1   # bài mẫu được mở sẵn khi vào trang (đếm từ 0)


# =====================================================================
# 2. HÀNH ĐỘNG: ô trống có thể đi Lên / Xuống / Trái / Phải (nếu không chạm mép)
# =====================================================================

def find_blank(state):
    """Tìm vị trí (hàng i, cột j) của ô trống."""
    for i in range(3):
        for j in range(3):
            if state[i][j] == 0:
                return i, j


def actions_8puzzle(state):
    i, j = find_blank(state)
    moves = []
    if i > 0:
        moves.append("Lên")
    if i < 2:
        moves.append("Xuống")
    if j > 0:
        moves.append("Trái")
    if j < 2:
        moves.append("Phải")
    return moves


# =====================================================================
# 3. KẾT QUẢ HÀNH ĐỘNG: đổi chỗ ô trống với ô bên cạnh theo hướng đi
# =====================================================================

def result_8puzzle(state, action):
    i, j = find_blank(state)
    if action == "Lên":
        new_i, new_j = i - 1, j
    elif action == "Xuống":
        new_i, new_j = i + 1, j
    elif action == "Trái":
        new_i, new_j = i, j - 1
    elif action == "Phải":
        new_i, new_j = i, j + 1

    board = []
    for row in state:
        board.append(list(row))       # chép từng hàng để không sửa trạng thái cũ

    temp = board[i][j]
    board[i][j] = board[new_i][new_j]
    board[new_i][new_j] = temp
    return tuple(tuple(row) for row in board)


# =====================================================================
# 4. CHI PHÍ MỖI BƯỚC (UCS dùng): ô trống đi Lên / Xuống tốn 1, đi Trái / Phải tốn 2
# =====================================================================

def step_cost_8puzzle(state, action):
    if action == "Lên" or action == "Xuống":
        return 1
    return 2


# =====================================================================
# 5. TẠO PROBLEM: Problem(initial, goal, actions_8puzzle, result_8puzzle, step_cost_8puzzle)
# =====================================================================

def make_problem(initial_state=INITIAL_STATE, goal_state=GOAL_STATE):
    initial_state = tuple(tuple(row) for row in initial_state)
    goal_state = tuple(tuple(row) for row in goal_state)
    return Problem(initial_state, goal_state, actions_8puzzle, result_8puzzle, step_cost_8puzzle)


# =====================================================================
# 6. TIỆN ÍCH CHO GIAO DIỆN (không thuộc thuật toán)
# =====================================================================

def _inversions(state):
    t = [v for row in state for v in row if v]
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t)) if t[i] > t[j])


def solvable(initial_state, goal_state):
    """Bàn 3x3: giải được khi hai trạng thái có cùng tính chẵn lẻ của số cặp nghịch thế."""
    return _inversions(initial_state) % 2 == _inversions(goal_state) % 2


def random_goal():
    return GOAL_STATE


def scramble(goal_state):
    """Xáo ngẫu nhiên vài nước từ đích (nên luôn giải được)."""
    s, prev = tuple(tuple(row) for row in goal_state), None
    for _ in range(random.randint(6, 9)):
        opts = [o for o in (result_8puzzle(s, a) for a in actions_8puzzle(s)) if o != prev]
        prev, s = s, random.choice(opts)
    return s


def describe_action(action):
    """Câu mô tả ngắn hành động, dùng trong lời thuyết minh dòng child_node."""
    return "trượt ô trống để sinh nút con"
