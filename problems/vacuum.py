"""Bài toán robot hút bụi nhiều phòng (2 đến 6 phòng).

Trạng thái: phần tử đầu là phòng robot đang đứng, sau đó là tình trạng từng phòng.
    ("A", "D", "D")          2 phòng: robot ở A, phòng A bẩn, phòng B bẩn
    ("B", "C", "D", "D")     3 phòng: robot ở B, A sạch, B bẩn, C bẩn
'D' = bẩn (dirty), 'C' = sạch (clean). Các phòng xếp thành hàng A, B, C, ... từ trái sang phải.
"""
import random

from core.problem import Problem

# =====================================================================
# 1. TRẠNG THÁI BAN ĐẦU / ĐÍCH / BÀI MẪU
# =====================================================================

INITIAL_STATE = ("A", "D", "D")
GOAL_STATE = ("B", "C", "C")

# Các bài mẫu hiện trên giao diện: (nhãn, trạng thái đầu, trạng thái đích).
PRESETS = [
    ("2 phòng", INITIAL_STATE, GOAL_STATE),
    ("3 phòng", ("A", "D", "D", "D"), ("C", "C", "C", "C")),
    ("4 phòng", ("B", "D", "C", "D", "D"), ("D", "C", "C", "C", "C")),
    ("6 phòng", ("C", "D", "D", "C", "D", "D", "D"), ("F", "C", "C", "C", "C", "C", "C")),
]
DEFAULT_PRESET = 0


# =====================================================================
# 2. HÀNH ĐỘNG
# =====================================================================

def actions_vacuum(state):
    return ["Suck", "Left", "Right"]


# =====================================================================
# 3. KẾT QUẢ HÀNH ĐỘNG
# =====================================================================

def chi_so_phong(vi_tri):
    """Phòng 'A' nằm ở ô 1 của trạng thái, 'B' ở ô 2, 'C' ở ô 3, ..."""
    return ord(vi_tri) - ord("A") + 1


def ten_phong(k):
    """Ngược lại với chi_so_phong: ô 1 -> 'A', ô 2 -> 'B', ..."""
    return chr(ord("A") + k - 1)


def result_vacuum(state, action):
    new_state = list(state)
    so_phong = len(state) - 1
    k = chi_so_phong(state[0])
    if action == "Suck":
        new_state[k] = "C"
    elif action == "Left":
        if k > 1:                       # phòng ngoài cùng bên trái thì đứng yên
            new_state[0] = ten_phong(k - 1)
    elif action == "Right":
        if k < so_phong:                # phòng ngoài cùng bên phải thì đứng yên
            new_state[0] = ten_phong(k + 1)
    return tuple(new_state)


# =====================================================================
# 4. CHI PHÍ MỖI BƯỚC (UCS dùng): hút bụi tốn 1, sang trái / phải tốn 2
# =====================================================================

def step_cost_vacuum(state, action):
    if action == "Suck":
        return 1
    return 2


# =====================================================================
# 5. TẠO PROBLEM: Problem(initial, goal, actions_vacuum, result_vacuum, step_cost_vacuum)
# =====================================================================

def make_problem(initial_state=INITIAL_STATE, goal_state=GOAL_STATE):
    return Problem(tuple(initial_state), tuple(goal_state), actions_vacuum, result_vacuum, step_cost_vacuum)


# =====================================================================
# 6. TIỆN ÍCH CHO GIAO DIỆN (không thuộc thuật toán)
# =====================================================================

def solvable(initial_state, goal_state):
    return len(initial_state) == len(goal_state)


def random_goal():
    """Đích ngẫu nhiên: 2 đến 6 phòng, tất cả sạch, robot dừng ở một phòng bất kỳ."""
    n = random.randint(2, 6)
    return (ten_phong(random.randint(1, n)),) + ("C",) * n


def scramble(goal_state):
    """Trạng thái đầu ngẫu nhiên cùng số phòng với đích: mỗi phòng bẩn với xác suất 60%."""
    n = len(goal_state) - 1
    dirt = [random.random() < 0.6 for _ in range(n)]
    if not any(dirt):
        dirt[random.randrange(n)] = True
    return (ten_phong(random.randint(1, n)),) + tuple("D" if d else "C" for d in dirt)


MO_TA = {
    "Suck": "hút bụi phòng hiện tại → phòng đó thành C",
    "Left": "robot sang phòng bên trái",
    "Right": "robot sang phòng bên phải",
}


def describe_action(action):
    """Câu mô tả ngắn hành động, dùng trong lời thuyết minh dòng child_node."""
    return MO_TA[action]
