"""UCS (Uniform-Cost Search) cho bài 8-PUZZLE: MỘT TỆP, chạy độc lập (không cần thư mục nào khác).

Chạy:
    pip install pygame
    python 8puzzle_ucs.py                 mở cửa sổ trực quan hóa từng dòng code
    python 8puzzle_ucs.py --console       chỉ chạy phần LOGIC và in lời giải ra màn hình (không cần pygame)

Tệp chia làm hai phần, ngăn cách bằng một dòng kẻ lớn. Phần 1 không dùng pygame; phần 2 chỉ vẽ.

  PHẦN 1  LOGIC (thuật toán, bài toán, điều khiển), không dùng pygame
      1.1  Thuật toán UCS               Node, Problem, PriorityQueue, child_node, solution, find_in_frontier, UCS
      1.2  Bài toán 8-puzzle             trạng thái đầu / đích, actions, result, chi phí mỗi bước, bài mẫu
      1.3  Ghi lại từng dòng của UCS    Recorder: chạy chính hàm UCS, ghi một "sự kiện" sau mỗi dòng
      1.4  Phát lại và phiên làm việc   Player, SolutionReplay, UCSSession, hộp thoại "Tự đặt" (mô hình)
  PHẦN 2  GIAO DIỆN (pygame), chỉ vẽ và nhận phím / chuột, gọi sang phần 1 để làm việc
      2.1  Bảng màu    2.2  Bộ vẽ nhỏ    2.3  Khung màn hình chung    2.4  Hình vẽ riêng    2.5  Màn hình và hộp thoại    2.6  main

Phím tắt: Space phát / dừng · Phải / Trái tiếp / lùi một dòng · N nhảy tới nút kế · R về đầu · Lên / Xuống đổi tốc độ
          G bài ngẫu nhiên · T tự đặt · V chạy lời giải · 1-9 chọn bài mẫu · F11 toàn màn hình · Esc thoát
"""
import ctypes
import inspect
import math
import random
import re
import sys

if sys.version_info < (3, 8):
    raise SystemExit("Cần Python 3.8 trở lên (máy này đang là " + sys.version.split()[0] + ").")


def _stop(message):
    """Báo lỗi bằng tiếng Việt và giữ cửa sổ lại (khi bấm đúp để chạy), thay vì in một đống traceback."""
    print("\n" + message + "\n")
    try:
        input("Bấm Enter để đóng...")
    except EOFError:
        pass
    raise SystemExit(1)


# ======================================================================================================
# PHẦN 1  LOGIC (không dùng pygame)
# ======================================================================================================

# ------------------------------------------------------------------------------------------------------
# 1.1  THUẬT TOÁN UCS
# ------------------------------------------------------------------------------------------------------
# UCS luôn mở nút có chi phí g NHỎ NHẤT trước. Khác BFS / DFS ở hai chỗ:
#   - kiểm tra đích khi LẤY nút ra khỏi frontier (không phải lúc sinh nút con) nên lời giải tìm được có tổng chi phí nhỏ nhất;
#   - gặp lại một trạng thái đang chờ trong frontier bằng đường RẺ HƠN thì thay nút cũ bằng nút mới.


class Node:
    def __init__(self, state, parent=None, action=None, path_cost=0):
        self.state = state              # trạng thái mà nút này đại diện
        self.parent = parent            # nút cha (None nếu là nút gốc)
        self.action = action            # hành động đã làm để đi từ cha tới nút này
        self.path_cost = path_cost      # chi phí g: tổng chi phí từ nút gốc tới nút này


class Problem:
    def __init__(self, initial_state, goal_condition, actions, result, step_cost):
        self.initial_state = initial_state      # trạng thái ban đầu
        self.goal_condition = goal_condition    # trạng thái đích
        self.actions = actions                  # actions(state)            -> danh sách hành động làm được
        self.result = result                    # result(state, action)     -> trạng thái mới sau hành động
        self.step_cost = step_cost              # step_cost(state, action)  -> chi phí của một bước đi


def is_goal(problem, state):
    return state == problem.goal_condition


# Hàng đợi ưu tiên: các nút luôn xếp theo chi phí g tăng dần; push chèn đúng chỗ, pop lấy nút g nhỏ nhất ở đầu.
def PriorityQueue():
    return []


def push(queue, node):
    i = 0
    while i < len(queue) and queue[i].path_cost <= node.path_cost:
        i += 1
    queue.insert(i, node)


def is_empty(queue):
    return len(queue) == 0


def pop(queue):
    if is_empty(queue):
        return None
    node = queue[0]
    del queue[0]
    return node


def child_node(problem, parent, action):
    """Sinh nút con: áp dụng hành động lên trạng thái nút cha, cộng thêm chi phí của bước đi."""
    new_state = problem.result(parent.state, action)
    new_path_cost = parent.path_cost + problem.step_cost(parent.state, action)
    return Node(state=new_state, parent=parent, action=action, path_cost=new_path_cost)


def solution(node):
    """Lần ngược từ nút đích về nút gốc, trả về danh sách trạng thái từ đầu tới đích."""
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    path.reverse()
    return path


def find_in_frontier(frontier, state):
    """Tìm nút đang chờ trong frontier có cùng trạng thái; không có thì trả về None."""
    for n in frontier:
        if n.state == state:
            return n
    return None


# Hàm dưới đây chính là hàm giao diện chạy và hiển thị từng dòng: sửa ở đây thì giao diện đổi theo.
def UCS(problem):
    node = Node(problem.initial_state, path_cost=0)
    frontier = PriorityQueue()
    push(frontier, node)
    explored = []
    while not is_empty(frontier):
        node = pop(frontier)
        if is_goal(problem, node.state):
            return solution(node)
        explored.append(node.state)
        for action in problem.actions(node.state):
            child = child_node(problem, node, action)
            old = find_in_frontier(frontier, child.state)
            if child.state not in explored and old is None:
                push(frontier, child)
            elif old is not None and old.path_cost > child.path_cost:
                frontier.remove(old)
                push(frontier, child)
    return None


# ------------------------------------------------------------------------------------------------------
# 1.2  BÀI TOÁN 8-PUZZLE
# ------------------------------------------------------------------------------------------------------
# Bàn 3x3, 8 ô số và 1 ô trống (số 0). Trượt ô trống để về trạng thái đích. Mỗi bước ô trống đi một trong 4 hướng:
# Lên / Xuống tốn 1, Trái / Phải tốn 2 (đó là chi phí mà UCS cộng dồn thành g).
# Trạng thái là bàn cờ 3x3 viết bằng tuple (không sửa được) để giao diện dùng làm khóa khi lưu hình đã vẽ.

INITIAL_STATE = ((1, 2, 3),
                 (4, 0, 6),
                 (7, 5, 8))

GOAL_STATE = ((1, 2, 3),
              (4, 5, 6),
              (7, 8, 0))

# Các bài mẫu hiện trên giao diện (nút "Bài mẫu"): (nhãn, trạng thái đầu, trạng thái đích). Tên theo tổng chi phí g của lời giải rẻ nhất.
PRESETS = [
    ("chi phí 3", INITIAL_STATE, GOAL_STATE),
    ("chi phí 5", ((1, 5, 2), (4, 0, 3), (7, 8, 6)), GOAL_STATE),
    ("chi phí 8", ((0, 2, 3), (1, 8, 5), (4, 7, 6)), GOAL_STATE),
]
DEFAULT_PRESET = 1      # bài mẫu được mở sẵn khi vào app (đếm từ 0)


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


def step_cost_8puzzle(state, action):
    if action == "Lên" or action == "Xuống":
        return 1
    return 2


def make_problem(initial_state=INITIAL_STATE, goal_state=GOAL_STATE):
    initial_state = tuple(tuple(row) for row in initial_state)
    goal_state = tuple(tuple(row) for row in goal_state)
    return Problem(initial_state, goal_state, actions_8puzzle, result_8puzzle, step_cost_8puzzle)


# ---------- tiện ích cho giao diện (không thuộc thuật toán) ----------

def _inversions(state):
    t = [v for row in state for v in row if v]
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t)) if t[i] > t[j])


def solvable(initial_state, goal_state):
    """Bàn 3x3: giải được khi hai trạng thái có cùng tính chẵn lẻ của số cặp nghịch thế."""
    return _inversions(initial_state) % 2 == _inversions(goal_state) % 2


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


def random_start(current_goal=None):
    """Bài ngẫu nhiên: giữ nguyên đích đang dùng, xáo ngẫu nhiên trạng thái đầu bằng vài nước đi từ đích."""
    goal = current_goal or GOAL_STATE
    return scramble(goal), goal


def flat(state):
    """Bàn 3x3 ((1, 2, 3), ...) -> 9 ô (1, 2, 3, ...)."""
    return tuple(v for row in state for v in row)


def grid(cells):
    """9 ô -> bàn 3x3."""
    cells = tuple(cells)
    return (cells[0:3], cells[3:6], cells[6:9])


# ------------------------------------------------------------------------------------------------------
# 1.3  GHI LẠI TỪNG DÒNG CỦA UCS (cầu nối giữa thuật toán và giao diện)
# ------------------------------------------------------------------------------------------------------
# Giao diện cần biết: dòng nào của UCS đang chạy, frontier và explored lúc đó ra sao, nút nào đang xét, nút con là gì...
# Cách làm: chạy ĐÚNG hàm UCS ở mục 1.1 dưới sys.settrace. Mỗi khi UCS chạy xong một dòng, Recorder nhìn các biến của nó
# (node, child, old, frontier, explored) rồi ghi lại một "sự kiện". Giao diện chỉ việc phát lại danh sách sự kiện này,
# nên hàm UCS không bị chen thêm dòng nào của giao diện, và dòng sáng trên màn hình chính là dòng code thật đang chạy.

UCS_INFO = dict(name="UCS", full="Uniform-Cost Search", l1="Chi phí đều", l2="hàng đợi ưu tiên",
                limit=600,      # số nút tối đa được mở trước khi coi bài là quá lớn để trình chiếu
                gates=("child.state in explored ?", "old is not None ?"))      # nhãn hai đèn kiểm tra trên màn hình

# Mỗi dòng code của UCS được nhận ra bằng nội dung của nó (không dựa vào số dòng), nên chèn thêm dòng vẫn chạy được.
UCS_LINE_ROLES = [
    ("make_root", r"^node = Node\(problem\.initial_state, path_cost=0\)$"),
    ("new_frontier", r"^frontier = \w+\(\)$"),
    ("add_root", r"^\w+\(frontier, node\)$"),
    ("new_explored", r"^explored = \[\]$"),
    ("loop", r"^while not is_empty\(frontier\):$"),
    ("take", r"^node = \w+\(frontier\)$"),
    ("goal_take", r"^if is_goal\(problem, node\.state\):$"),
    ("return_take", r"^return solution\(node\)$"),
    ("mark", r"^explored\.append\(node\.state\)$"),
    ("for_action", r"^for action in problem\.actions\(node\.state\):$"),
    ("make_child", r"^child = child_node\(problem, node, action\)$"),
    ("find_old", r"^old = find_in_frontier\(frontier, child\.state\)$"),
    ("check_old", r"^if child\.state not in explored and old is None:$"),
    ("add_child", r"^\w+\(frontier, child\)$"),
    ("better", r"^elif old is not None and old\.path_cost > child\.path_cost:$"),
    ("replace", r"^frontier\.remove\(old\)$"),
    ("return_none", r"^return None$"),
]


def role_of(line):
    text = line.strip()
    for role, pattern in UCS_LINE_ROLES:
        if re.match(pattern, text):
            return role
    return None


_lines, UCS_FIRST_LINE = inspect.getsourcelines(UCS)
UCS_CODE = [ln.rstrip("\n") for ln in _lines]                  # mã nguồn thật của hàm UCS, để hiển thị
UCS_ROLES = [role_of(ln) for ln in UCS_CODE]
UCS_NODE_LINE = UCS_ROLES.index("take")                        # dòng pop(frontier): nút "Node kế" nhảy tới đó

# Thời gian (giây, ở tốc độ x1) mỗi loại dòng được giữ trên màn hình.
DURATION = {"make_root": 0.9, "new_frontier": 0.5, "add_root": 0.9, "new_explored": 0.5, "loop": 0.4, "take": 0.9,
            "goal_take": 0.6, "return_take": 2.0, "mark": 0.7, "for_action": 0.5, "make_child": 1.0, "check_old": 1.0,
            "add_child": 0.95, "better": 1.0, "replace": 0.8, "return_none": 1.0}


def duration(role, c):
    if role == "goal_take" and c["is_goal"]:
        return 0.9
    if role == "find_old":
        return 0.5 + min(c["frontier_len"], 24) * 0.035
    return DURATION.get(role, 0.6)          # dòng code lạ (vd. thêm print để thử): vẫn hiện 0.6 giây


def caption(role, c):
    """Câu giải thích hiện dưới khung code. c: thông tin lúc dòng vừa chạy xong."""
    call = c["call"]                        # tên hàm trên dòng đó, vd "push", "pop", "PriorityQueue"
    if role == "make_root":
        return "node = Node(initial_state, path_cost=0): tạo nút gốc, chi phí g = 0."
    if role == "new_frontier":
        return f"frontier = {call}(): tạo hàng đợi ưu tiên rỗng (nút có g nhỏ nhất luôn đứng đầu)."
    if role == "add_root":
        return f"{call}(frontier, node): đưa nút gốc (g = 0) vào hàng đợi ưu tiên."
    if role == "new_explored":
        return "explored = []: tập các trạng thái đã mở, ban đầu rỗng."
    if role == "loop":
        return f"while not is_empty(frontier): hàng đợi ưu tiên còn {c['frontier_len']} nút → lặp."
    if role == "take":
        return f"{call}(frontier): lấy nút ở ĐẦU hàng đợi ưu tiên, tức nút có chi phí NHỎ NHẤT (g = {c['node_cost']})."
    if role == "goal_take":
        if c["is_goal"]:
            return "is_goal(problem, node.state): ĐÚNG! UCS kiểm tra đích khi LẤY nút ra, nên đây là đường rẻ nhất."
        return "is_goal(problem, node.state)? Chưa phải đích → mở rộng nút này."
    if role == "return_take":
        acts = c["solution"]
        lst = " → ".join(acts) if len(acts) <= 12 else " → ".join(acts[:10]) + " → …"
        return f"return solution(node): lời giải {len(acts)} bước, tổng chi phí g = {c['node_cost']}: " + lst
    if role == "mark":
        return "explored.append(node.state): đánh dấu trạng thái này đã được mở."
    if role == "for_action":
        return f"for action in problem.actions(...): thử hành động «{c['action']}»."
    if role == "make_child":
        return (f"child_node(problem, node, «{c['action']}»): {c['describe']}; "
                f"g = {c['node_cost']} + {c['child_cost'] - c['node_cost']} = {c['child_cost']}.")
    if role == "find_old":
        if c["old_cost"] is None:
            return "old = find_in_frontier(...): trạng thái này KHÔNG có trong frontier → old = None."
        return f"old = find_in_frontier(...): trạng thái này ĐANG chờ trong frontier với g = {c['old_cost']}."
    if role == "check_old":
        head = "if child.state not in explored and old is None: "
        if c["in_explored"]:
            return head + "trạng thái này đã nằm trong explored → BỎ."
        if c["old_cost"] is not None:
            return head + "đã có trong frontier → sang dòng elif so sánh chi phí."
        return head + "chưa mở, chưa có trong frontier → nút MỚI, đưa vào hàng đợi."
    if role == "better":
        head = "elif old is not None and old.path_cost > child.path_cost: "
        if c["old_cost"] is None:
            return head + "không có nút cũ để so → BỎ nút con."
        if c["old_cost"] > c["child_cost"]:
            return head + f"g cũ {c['old_cost']} > g mới {c['child_cost']} → đường mới RẺ HƠN, thay nút cũ."
        return head + f"g cũ {c['old_cost']} ≤ g mới {c['child_cost']} → giữ nút cũ, BỎ nút con."
    if role == "replace":
        return f"frontier.remove(old): xóa nút cũ (g = {c['old_cost']}) khỏi hàng đợi."
    if role == "add_child":
        return f"{call}(frontier, child): chèn nút con (g = {c['child_cost']}) vào hàng đợi theo thứ tự g tăng dần."
    if role == "return_none":
        return "return None: hàng đợi ưu tiên cạn, không có lời giải."
    return c["line"].strip()


class Recorder:
    """Ghi lại một lần chạy UCS.

    events    danh sách sự kiện, mỗi sự kiện ứng với một dòng code vừa chạy
    nodes     bảng các nút đã sinh và được giữ lại: state, parent (chỉ số nút cha), action, depth, cost (chi phí g)
    path      chỉ số các nút trên đường đi lời giải (từ gốc tới đích)
    solution  danh sách hành động của lời giải
    """
    KIND = {"return_take": "done", "return_none": "done", "find_old": "scan", "check_old": "check"}

    def __init__(self, problem):
        self.problem = problem
        self.init, self.goal = problem.initial_state, problem.goal_condition
        self.nodes, self.events = [], []
        self.solution, self.path = [], ()
        self._eid, self._keep = {}, []                      # id(Node) -> chỉ số trong bảng nút
        self.frontier, self.explored = [], []
        self.node_state, self.node_eid, self.node_depth = self.init, None, 0
        self.ckey = 0
        self.reset_view()
        self._run()

    # ---------- trạng thái phụ cho phần hình ----------
    def reset_view(self):
        self.act = None
        self.child = None
        self.child_eid = None
        self.gate = [None, None]        # [đã có trong explored?, đã có trong frontier?]  (hai đèn trên màn hình)
        self.verdict = None             # ok / dup / goal / queued / replace
        self.match = None
        self.scan_match = None

    def add_node(self, node):
        parent = None if node.parent is None else self._eid[id(node.parent)]
        depth = 0 if parent is None else self.nodes[parent]["depth"] + 1
        self.nodes.append(dict(state=node.state, parent=parent, action=node.action, depth=depth, cost=node.path_cost))
        eid = len(self.nodes) - 1
        self._eid[id(node)] = eid
        self._keep.append(node)
        return eid

    def chain(self, eid):
        out = []
        while eid is not None:
            out.append(eid)
            eid = self.nodes[eid]["parent"]
        out.reverse()
        return tuple(out), [self.nodes[e]["action"] for e in out[1:]]

    def emit(self, idx, role, extra):
        line = UCS_CODE[idx]
        m = re.search(r"(\w+)\(", line)
        node_cost = 0 if self.node_eid is None else self.nodes[self.node_eid]["cost"]
        c = dict(line=line, call=m.group(1) if m else "", frontier_len=len(self.frontier), action=self.act,
                 solution=self.solution, is_goal=False, in_explored=False, node_cost=node_cost,
                 child_cost=None if self.child is None else self.child[3], old_cost=None)
        c.update(extra)
        self.events.append(dict(
            line=idx, cap=caption(role, c), dur=duration(role, c), kind=self.KIND.get(role, "n"),
            act=self.act, child=self.child, child_eid=self.child_eid,
            frontier=tuple(self.frontier), explored=tuple(self.explored), tn=len(self.nodes),
            gate=tuple(self.gate), verdict=self.verdict, match=self.match, scan_match=self.scan_match,
            node_state=self.node_state, node_eid=self.node_eid, node_depth=self.node_depth,
            node_cost=node_cost, path=self.path))

    # ---------- chạy UCS dưới sys.settrace ----------
    def _run(self):
        target = UCS.__code__
        pending = [None, None]          # dòng vừa bắt đầu chạy: [chỉ số dòng, vai trò]

        def local(frame, event, arg):
            if event == "line":
                idx = frame.f_lineno - UCS_FIRST_LINE
                role = UCS_ROLES[idx]
                if pending[0] is not None:                  # dòng trước đó vừa chạy xong
                    self._finish(pending[0], pending[1], role, frame.f_locals)
                pending[0], pending[1] = idx, role
            elif event == "return" and pending[0] is not None:
                self._finish(pending[0], pending[1], None, frame.f_locals)
                pending[0] = None
            return local

        def on_call(frame, event, arg):
            return local if frame.f_code is target else None

        old = sys.gettrace()
        sys.settrace(on_call)
        try:
            UCS(self.problem)
        finally:
            sys.settrace(old)

    def _sync_frontier(self, L):
        if "frontier" in L:
            self.frontier = [self._eid[id(n)] for n in L["frontier"]]

    def _finish(self, idx, role, next_role, L):
        """Dòng `idx` vừa chạy xong; L là các biến của hàm UCS lúc này."""
        if role == "add_root":
            self.add_node(L["node"])
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "loop":
            if next_role == "return_none":                  # frontier rỗng: thoát vòng lặp
                return
            self.reset_view()
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "take":
            eid = self._eid[id(L["node"])]
            self.node_state, self.node_eid, self.node_depth = L["node"].state, eid, self.nodes[eid]["depth"]
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "goal_take":
            goal = is_goal(self.problem, L["node"].state)
            if goal:
                self.verdict = "goal"
            self.emit(idx, role, {"is_goal": goal})
            if goal:
                self.path, self.solution = self.chain(self._eid[id(L["node"])])
        elif role == "mark":
            self.explored.append(self._eid[id(L["node"])])
            self.emit(idx, role, {})
        elif role == "for_action":
            if next_role != "make_child":                   # hết hành động: thoát vòng for
                return
            self.reset_view()
            self.act = L["action"]
            self.emit(idx, role, {})
        elif role == "make_child":
            self.ckey += 1
            self.child = (L["child"].state, self._eid[id(L["node"])], self.ckey, L["child"].path_cost)
            self.emit(idx, role, {"describe": describe_action(L["action"])})
        elif role == "find_old":
            old = L["old"]
            self.scan_match = self.match = None if old is None else self._eid[id(old)]
            self.gate[1] = old is not None
            self.emit(idx, role, {"old_cost": None if old is None else old.path_cost})
        elif role == "check_old":
            old = L["old"]
            in_explored = L["child"].state in L["explored"]
            self.gate[0] = in_explored
            if in_explored:
                self.verdict = "dup"
            elif old is None:
                self.verdict = "ok"
            self.emit(idx, role, {"in_explored": in_explored, "old_cost": None if old is None else old.path_cost})
        elif role == "better":
            old = L["old"]
            better = old is not None and old.path_cost > L["child"].path_cost
            self.verdict = "replace" if better else "dup"
            self.emit(idx, role, {"old_cost": None if old is None else old.path_cost})
        elif role == "replace":
            self._sync_frontier(L)
            self.emit(idx, role, {"old_cost": L["old"].path_cost})
        elif role == "add_child":
            self.child_eid = self.add_node(L["child"])
            self._sync_frontier(L)
            self.verdict = "queued"
            self.emit(idx, role, {})
        elif role == "return_none":
            self.reset_view()
            self.emit(idx, role, {})
        else:
            self.emit(idx, role, {})                        # make_root, new_frontier, new_explored, return_take, dòng lạ


class _TooBig(Exception):
    pass


def quick(problem, limit=UCS_INFO["limit"]):
    """(số bước của lời giải, số nút đã mở); None nếu không có lời giải hoặc phải mở quá `limit` nút.
    Chạy chính hàm UCS nhưng không ghi từng dòng; đếm số nút đã mở bằng số lần UCS gọi problem.actions(...)."""
    opened = 0

    def counting_actions(state):
        nonlocal opened
        opened += 1
        if opened > limit:
            raise _TooBig
        return problem.actions(state)

    counted = Problem(problem.initial_state, problem.goal_condition, counting_actions, problem.result, problem.step_cost)
    try:
        path = UCS(counted)
    except _TooBig:
        return None
    return None if path is None else (len(path) - 1, opened)


def random_initial(current_goal=None, tries=120):
    """Bài ngẫu nhiên: xáo trạng thái đầu tới khi UCS giải được trong giới hạn số nút. Trả về (trạng thái đầu, đích)."""
    for _ in range(tries):
        init, goal = random_start(current_goal)
        if quick(make_problem(init, goal)) is not None:
            break
    return init, goal


# ------------------------------------------------------------------------------------------------------
# 1.4  PHÁT LẠI VÀ PHIÊN LÀM VIỆC
# ------------------------------------------------------------------------------------------------------
# Player quản lý "đang xem sự kiện số mấy" như một trình phát video. SolutionReplay đi lần lượt qua các trạng thái của lời giải.
# UCSSession gom mọi thứ không thuộc về việc vẽ: bài đang chạy, bản ghi UCS, con trỏ phát lại, kiểm tra bài tự đặt.

SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16]


class Player:
    def __init__(self, events, node_line):
        self.events = events
        self.node_line = node_line      # dòng code "lấy nút ra khỏi frontier" (nút "Node kế" nhảy tới đó)
        self.i = 0                      # đang ở sự kiện số mấy
        self.t = 0.0                    # đã ở sự kiện này bao nhiêu giây
        self.playing = False
        self.one = False                # đang chạy đúng một sự kiện (nút "Tiếp" / "Node kế")
        self.speed_i = 2

    # ---------- thông tin hiện tại ----------
    @property
    def last(self):
        return len(self.events) - 1

    @property
    def current(self):
        return self.events[self.i]

    @property
    def progress(self):
        """0..1: đã đi được bao nhiêu phần của sự kiện hiện tại (để vẽ hiệu ứng)."""
        dur = self.current["dur"]
        return min(1.0, self.t / dur) if dur else 1.0

    @property
    def speed(self):
        return SPEEDS[self.speed_i]

    # ---------- các nút điều khiển ----------
    def seek(self, i):
        self.i = max(0, min(self.last, i))
        self.t = 0.0
        self.one = False

    def toggle_play(self):
        if self.i >= self.last:
            self.seek(0)
        self.playing = not self.playing

    def step_next(self):
        self.playing = False
        if self.i < self.last:
            self.i += 1
            self.t, self.one = 0.0, True

    def step_back(self):
        self.playing = False
        self.seek(self.i - 1)

    def next_node(self):
        """Nhảy tới lần lấy nút ra kế tiếp (dòng pop)."""
        self.playing = False
        j = self.i + 1
        while j < self.last and self.events[j]["line"] != self.node_line:
            j += 1
        self.i, self.t, self.one = min(j, self.last), 0.0, True

    def reset(self):
        self.playing = False
        self.seek(0)

    def slower(self):
        self.speed_i = max(0, self.speed_i - 1)

    def faster(self):
        self.speed_i = min(len(SPEEDS) - 1, self.speed_i + 1)

    # ---------- chạy theo thời gian ----------
    def advance(self, dt):
        if not (self.playing or self.one):
            return
        self.t += dt * self.speed
        while self.t >= self.current["dur"]:
            if self.i >= self.last:
                self.t = self.current["dur"]
                self.playing = self.one = False
                return
            if self.one:
                self.t = self.current["dur"]
                self.one = False
                return
            self.t -= self.current["dur"]
            self.i += 1


class SolutionReplay:
    """Đi qua từng trạng thái của lời giải (từ trạng thái đầu tới đích), mỗi trạng thái giữ `step` giây."""

    def __init__(self, states, actions, step, max_speed, hold):
        self.states = states            # các trạng thái trên đường đi, đầu tiên là trạng thái đầu
        self.actions = actions          # actions[k - 1] là hành động để tới trạng thái k
        self.step = step
        self.max_speed = max_speed      # trần tốc độ (để không chạy quá nhanh khi bấm "+")
        self.hold = hold                # đứng yên ở đích thêm bao lâu rồi tự kết thúc
        self.t = 0.0
        self.k = 0
        self.finished = False

    @property
    def n(self):
        """Số bước của lời giải."""
        return len(self.states) - 1

    @property
    def state(self):
        return self.states[self.k]

    @property
    def action(self):
        """Hành động vừa làm để tới trạng thái hiện tại (None nếu đang ở trạng thái đầu)."""
        return self.actions[self.k - 1] if self.k >= 1 else None

    def advance(self, dt, speed):
        self.t += dt * min(self.max_speed, max(1.0, speed))
        self.k = min(self.n, int(self.t / self.step))
        if self.k >= self.n and self.t > self.n * self.step + self.hold:
            self.finished = True


class Check:
    """Kết quả kiểm tra một bài: ok (được dùng không), level ("ok" / "warn" / "error"), msg (câu báo cho người dùng)."""

    def __init__(self, ok, level, msg):
        self.ok, self.level, self.msg = ok, level, msg


class UCSSession:
    UNSOLVABLE_MSG = "Bài này không có lời giải."
    REPLAY_STEP = 0.8               # mỗi trạng thái của lời giải hiện bao nhiêu giây
    REPLAY_MAX_SPEED = 8.0
    REPLAY_HOLD = 1.6               # đứng ở đích thêm bao lâu rồi tự tắt

    def __init__(self):
        self.info = UCS_INFO                        # tên, giới hạn số nút, nhãn hai đèn kiểm tra
        self.code = UCS_CODE                        # mã nguồn thật của hàm UCS để hiển thị
        self.node_line = UCS_NODE_LINE              # dòng pop(frontier)
        self.presets = PRESETS                      # [(nhãn, trạng thái đầu, trạng thái đích), ...]
        self.preset = -1                            # đang dùng bài mẫu số mấy (-1: bài ngẫu nhiên / tự đặt)
        self.notice = None                          # câu cần báo cho người dùng (giao diện lấy ra bằng pop_notice)
        self.player = None
        self.replay = None
        self.load_preset(min(DEFAULT_PRESET, len(self.presets) - 1))

    # ---------- nạp bài ----------
    def load(self, init, goal):
        """Nạp một bài mới: tạo Problem, chạy UCS và ghi lại từng dòng."""
        speed_i = self.player.speed_i if self.player else 2
        self.problem = make_problem(init, goal)
        self.init, self.goal = self.problem.initial_state, self.problem.goal_condition
        self.rec = Recorder(self.problem)
        self.player = Player(self.rec.events, self.node_line)
        self.player.speed_i = speed_i
        self.replay = None

    def load_preset(self, i):
        _, init, goal = self.presets[i]
        self.preset = i
        self.load(init, goal)

    def load_random(self):
        init, goal = random_initial(self.goal)
        self.preset = -1
        self.load(init, goal)

    def load_custom(self, init, goal):
        """Nạp bài do người dùng tự đặt."""
        self.preset = -1
        self.load(init, goal)

    # ---------- thông tin hiện tại ----------
    @property
    def ev(self):
        return self.player.current

    def node_status(self, eid):
        """Một nút trong bảng đang ở trạng thái nào: "path" (trên đường lời giải), "current" (đang xét),
        "explored" (đã mở), "frontier" (đang chờ) hay "other"."""
        ev = self.ev
        if ev["path"] and eid in ev["path"]:
            return "path"
        if eid == ev["node_eid"]:
            return "current"
        if eid in ev["explored"]:
            return "explored"
        if eid in ev["frontier"]:
            return "frontier"
        return "other"

    def pop_notice(self):
        notice, self.notice = self.notice, None
        return notice

    # ---------- chạy theo thời gian ----------
    def update(self, dt):
        self.player.advance(dt)
        if self.replay:
            self.replay.advance(dt, self.player.speed)
            if self.replay.finished:
                self.replay = None

    # ---------- chạy lời giải ----------
    def toggle_replay(self):
        if self.replay:
            self.replay = None
            return
        if not self.rec.solution:
            self.notice = "Chưa có lời giải để chạy."
            return
        self.player.playing = False
        self.player.seek(self.player.last)
        states = [self.rec.nodes[e]["state"] for e in self.rec.path]
        self.replay = SolutionReplay(states, self.rec.solution, self.REPLAY_STEP, self.REPLAY_MAX_SPEED, self.REPLAY_HOLD)

    def stop_replay(self):
        self.replay = None

    # ---------- kiểm tra một bài tự đặt ----------
    def check(self, init, goal):
        if not solvable(init, goal):
            return Check(False, "error", self.UNSOLVABLE_MSG)
        name = self.info["name"]
        st = quick(make_problem(init, goal))
        if st is None:
            return Check(False, "warn", f"Giải được nhưng quá lớn: {name} phải mở hơn {self.info['limit']} nút, "
                                        "khó theo dõi. Hãy đặt gần đích hơn.")
        if st[0] == 0:
            return Check(True, "ok", "Trạng thái đầu đã bằng đích: 0 bước.")
        return Check(True, "ok", f"{name} tìm được lời giải {st[0]} bước, mở {st[1]} nút.")


class Puzzle8Session(UCSSession):
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
        self.goal = list(flat(GOAL_STATE))
        self.selected = None
        self.recheck()

    def shuffle(self):
        init, _ = random_initial(grid(self.goal))
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


def console_demo():
    """Chạy UCS không cần giao diện và in từng bước cùng chi phí g."""
    problem = make_problem(INITIAL_STATE, GOAL_STATE)
    path = UCS(problem)
    if path is None:
        print("Không tìm thấy lời giải")
        return
    total = 0
    for i in range(len(path)):
        if i > 0:
            total += next(problem.step_cost(path[i - 1], a) for a in problem.actions(path[i - 1])
                          if problem.result(path[i - 1], a) == path[i])
        print("Bước", i, "- chi phí g =", total)
        for row in path[i]:
            print(list(row))
        print()
    print("Số bước:", len(path) - 1)
    print("Tổng chi phí:", total)


# ======================================================================================================
# Ranh giới: mọi thứ phía trên KHÔNG dùng pygame. `python <tệp> --console` dừng ngay tại đây.
# ======================================================================================================
if __name__ == "__main__" and "--console" in sys.argv:
    console_demo()
    raise SystemExit(0)


# ======================================================================================================
# PHẦN 2  GIAO DIỆN (pygame): chỉ vẽ và nhận phím / chuột. Mọi việc "làm gì" gọi sang PHẦN 1.
# ======================================================================================================
try:
    import pygame
except ImportError:
    _stop("Chưa cài thư viện pygame. Mở cửa sổ dòng lệnh và chạy:\n\n    pip install pygame\n\n"
          "(nếu báo không có pip: python -m pip install pygame), rồi chạy lại.")


# ------------------------------------------------------------------------------------------------------
# 2.1  BẢNG MÀU
# ------------------------------------------------------------------------------------------------------
BG = (13, 17, 27)
PANEL = (20, 26, 40)
PANEL_L = (34, 43, 64)
TEXT = (228, 234, 246)
MUTED = (126, 140, 166)
CYAN = (86, 214, 230)
BLUE = (100, 156, 255)
ORANGE = (255, 170, 70)
RED = (255, 98, 112)
GREEN = (104, 224, 150)
GOLD = (255, 214, 90)

ACCENT = (176, 146, 255)        # màu chủ đạo của UCS (tím)
INK_ON_ACCENT = (10, 22, 30)    # màu chữ đặt trên nền ACCENT
DIM_BORDER = (70, 82, 112)      # viền của thẻ không nổi bật
LAMP_OFF = (84, 96, 120)

LEVEL_COLOR = {"ok": GREEN, "warn": ORANGE, "error": RED}      # mức của một lời kiểm tra -> màu


# ------------------------------------------------------------------------------------------------------
# 2.2  BỘ VẼ NHỎ (chữ, khung, nút, tô màu mã nguồn)
# ------------------------------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------------------------------
# 2.3  KHUNG MÀN HÌNH CHUNG
# ------------------------------------------------------------------------------------------------------
# UCSScreen vẽ phần khung giống nhau của mọi bài toán:
#   đầu trang         tên thuật toán, các ô số liệu (Đã mở, Frontier, Nút sinh ra, Chi phí g), đích
#   khung mã nguồn    mã nguồn thật của hàm UCS, dòng đang chạy sáng lên, lời giải thích bên dưới
#   bảng node         mỗi nút một thẻ, xếp theo độ sâu, góc thẻ ghi chi phí g
#   FRONTIER          hàng đợi ưu tiên: thẻ nào g nhỏ nhất đứng đầu
#   EXPLORED          các nút đã mở
#   thanh điều khiển  Phát / Tiếp / Lùi / bài mẫu / Ngẫu nhiên / Tự đặt / Chạy lời giải
# Mọi việc "làm gì" nằm ở self.session (UCSSession, phần 1.4). Lớp này chỉ gọi session rồi vẽ kết quả.
# Lớp con (mục 2.5) bổ sung phần vẽ riêng của bài toán qua các hàm "HOOK".

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
        if self.canvas is not None and abs(sc - SC) < 0.003 and self.canvas.get_size() == (round(L.W * SC), round(L.H * SC)):
            return
        set_scale(sc)
        self.canvas = pygame.Surface((round(L.W * sc), round(L.H * sc)))
        self.code_lines = render_code_lines(self.session.code, L.code.w - 60, L.code_size)
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
        glow = pygame.Surface((round((rect.w - 16) * SC), round(L.line_h * SC)), pygame.SRCALPHA)
        glow.fill((*ACCENT, 40))
        s.blit(glow, (round((rect.x + 8) * SC), round(self.bar_y * SC)))
        G.rect(s, ACCENT, (rect.x + 8, self.bar_y, 4, L.line_h), border_radius=2)
        f = font("consolas", 13)
        for i, (bright, dim) in enumerate(self.code_lines):
            y = top + i * L.line_h
            active = i == ev["line"]
            text(s, str(i + 1), f, ACCENT if active else (70, 82, 110), (rect.x + 34, y + 4), "topright")
            s.blit(bright if active else dim, (round((rect.x + 46) * SC), round((y - 2) * SC)))
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
                col = mix(ORANGE, (255, 240, 200), pulse * 0.6)
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
        """Hai đèn kiểm tra (nhãn lấy từ UCS_INFO ở mục 1.3) và biểu ngữ kết luận ("Nút mới", "Trùng → BỎ", ...)."""
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
        flash = pygame.Surface((round(rect.w * SC), round(rect.h * SC)), pygame.SRCALPHA)
        flash.fill((255, 98, 112, int(70 * (0.5 + 0.5 * math.sin(p * 12)))))
        s.blit(flash, (round(rect.x * SC), round(rect.y * SC)))

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


# ------------------------------------------------------------------------------------------------------
# 2.4  HÌNH VẼ RIÊNG CỦA 8-PUZZLE: bàn cờ
# ------------------------------------------------------------------------------------------------------
TILE_COL = {1: (239, 122, 122), 2: (240, 170, 110), 3: (240, 214, 110), 4: (150, 215, 120),
            5: (100, 210, 190), 6: (100, 170, 240), 7: (150, 130, 240), 8: (210, 130, 220)}

_MINI = register_cache({})


def mini_surface(state, size):
    ps = max(6, round(size * SC))
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
    dst.blit(img, img.get_rect(center=(round(cx * SC), round(cy * SC))))
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
        s = pygame.Surface((round(self.size * SC), round(self.size * SC)), pygame.SRCALPHA)
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
                s.blit(t, t.get_rect(center=(round((px + self.ts / 2) * SC), round((py + self.ts / 2 - 2 * moving) * SC))))
        G.rect(s, border, (0, 0, self.size, self.size), 3, border_radius=12)
        if alpha < 0.98:
            s.set_alpha(int(255 * alpha))
        dst.blit(s, (round(self.x * SC), round(self.y * SC)))


# ------------------------------------------------------------------------------------------------------
# 2.5  MÀN HÌNH 8-PUZZLE VÀ HỘP THOẠI TỰ ĐẶT
# ------------------------------------------------------------------------------------------------------
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
        self.child_board.alpha = sm(self.child_board.alpha, 1.0 if ev["child"] else 0.18, 8, dt)

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
    """Hộp thoại "Tự đặt": vẽ hai bàn cờ và nhận chuột. Việc đổi ô, kiểm tra, áp dụng do Puzzle8Editor (mục 1.4) làm."""
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


# ------------------------------------------------------------------------------------------------------
# 2.6  CHẠY
# ------------------------------------------------------------------------------------------------------


def main():
    enable_dpi_awareness()
    Puzzle8Screen().run()


if __name__ == "__main__":
    main()

