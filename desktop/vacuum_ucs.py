"""UCS (Uniform-Cost Search) cho bài ROBOT HÚT BỤI: MỘT TỆP, chạy độc lập (không cần thư mục nào khác).

Chạy:
    pip install pygame
    python vacuum_ucs.py                 mở cửa sổ trực quan hóa từng dòng code
    python vacuum_ucs.py --console       chỉ chạy phần LOGIC và in lời giải ra màn hình (không cần pygame)

Tệp chia làm hai phần, ngăn cách bằng một dòng kẻ lớn. Phần 1 không dùng pygame; phần 2 chỉ vẽ.

  PHẦN 1  LOGIC (thuật toán, bài toán, điều khiển), không dùng pygame
      1.1  Thuật toán UCS               Node, Problem, PriorityQueue, child_node, solution, find_in_frontier, UCS
      1.2  Bài toán robot hút bụi       trạng thái đầu / đích, actions, result, chi phí mỗi bước, bài mẫu
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
# 1.2  BÀI TOÁN ROBOT HÚT BỤI
# ------------------------------------------------------------------------------------------------------
# Robot hút bụi trong ngôi nhà 2 đến 6 phòng xếp thành hàng A, B, C... Trạng thái: phần tử đầu là phòng robot đang đứng,
# sau đó là tình trạng từng phòng. 'D' = bẩn (dirty), 'C' = sạch (clean).
#     ("A", "D", "D")          2 phòng: robot ở A, phòng A bẩn, phòng B bẩn
#     ("B", "C", "D", "D")     3 phòng: robot ở B, A sạch, B bẩn, C bẩn
# Hành động: Suck (hút bụi, tốn 1), Left / Right (sang phòng bên cạnh, tốn 2).

INITIAL_STATE = ("A", "D", "D")
GOAL_STATE = ("B", "C", "C")

# Các bài mẫu hiện trên giao diện: (nhãn, trạng thái đầu, trạng thái đích).
PRESETS = [
    ("2 phòng", INITIAL_STATE, GOAL_STATE),
    ("3 phòng", ("A", "D", "D", "D"), ("C", "C", "C", "C")),
    ("4 phòng", ("B", "D", "C", "D", "D"), ("D", "C", "C", "C", "C")),
    ("6 phòng", ("C", "D", "D", "C", "D", "D", "D"), ("F", "C", "C", "C", "C", "C", "C")),
]
DEFAULT_PRESET = 0      # bài mẫu được mở sẵn khi vào app (đếm từ 0)
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


def chi_so_phong(vi_tri):
    """Phòng 'A' nằm ở ô 1 của trạng thái, 'B' ở ô 2, 'C' ở ô 3, ..."""
    return ord(vi_tri) - ord("A") + 1


def ten_phong(k):
    """Ngược lại với chi_so_phong: ô 1 -> 'A', ô 2 -> 'B', ..."""
    return chr(ord("A") + k - 1)


def actions_vacuum(state):
    return ["Suck", "Left", "Right"]


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


def step_cost_vacuum(state, action):
    if action == "Suck":
        return 1
    return 2


def make_problem(initial_state=INITIAL_STATE, goal_state=GOAL_STATE):
    return Problem(tuple(initial_state), tuple(goal_state), actions_vacuum, result_vacuum, step_cost_vacuum)


# ---------- tiện ích cho giao diện (không thuộc thuật toán) ----------

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


def random_start(current_goal=None):
    """Bài ngẫu nhiên: đổi cả số phòng, đích và trạng thái đầu (tham số current_goal không dùng tới)."""
    goal = random_goal()
    return scramble(goal), goal



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


class VacuumSession(UCSSession):
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
        print("[" + ", ".join(path[i]) + "]")
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
# 2.4  HÌNH VẼ RIÊNG CỦA ROBOT HÚT BỤI: ngôi nhà, robot và thẻ trạng thái
# ------------------------------------------------------------------------------------------------------
ROOM_TYPES = ["living", "kitchen", "bedroom", "bath", "study", "hall"]
ROOM_NAMES = {"living": "Phòng khách", "kitchen": "Bếp", "bedroom": "Phòng ngủ", "bath": "Phòng tắm",
              "study": "Làm việc", "hall": "Hành lang", "storage": "Kho"}
SCENE = pygame.Rect(524, 92, 864, 340)         # vùng ngôi nhà trên màn hình


ISO = {"TW": 100.0, "TH": 50.0, "OX": 0.0, "OY": 0.0, "ZK": 1.0}


def P(r, c, z=0.0):
    return (ISO["OX"] + (c - r) * ISO["TW"] / 2, ISO["OY"] + (c + r) * ISO["TH"] / 2 - z * ISO["ZK"])


def poly(s, pts3, col, edge=None, w=1):
    pts = [P(*p) for p in pts3]
    G.polygon(s, col, pts)
    if edge:
        G.polygon(s, edge, pts, w)


def box(s, r0, c0, r1, c1, z0, z1, col, edge=True):
    ec = shade(col, 0.45) if edge else None
    poly(s, [(r1, c0, z0), (r1, c1, z0), (r1, c1, z1), (r1, c0, z1)], shade(col, 0.78), ec)
    poly(s, [(r0, c1, z0), (r1, c1, z0), (r1, c1, z1), (r0, c1, z1)], shade(col, 0.58), ec)
    poly(s, [(r0, c0, z1), (r0, c1, z1), (r1, c1, z1), (r1, c0, z1)], col, ec)


def flat(s, r0, c0, r1, c1, z, col, edge=None):
    poly(s, [(r0, c0, z), (r0, c1, z), (r1, c1, z), (r1, c0, z)], col, edge)


def cylinder(s, r, c, rad, z0, z1, col, n=28):
    bot = [P(r + rad * math.cos(2 * math.pi * k / n), c + rad * math.sin(2 * math.pi * k / n), z0) for k in range(n)]
    top = [P(r + rad * math.cos(2 * math.pi * k / n), c + rad * math.sin(2 * math.pi * k / n), z1) for k in range(n)]
    for i in range(n):
        j = (i + 1) % n
        a = 2 * math.pi * (i + 0.5) / n
        if math.cos(a) + math.sin(a) > -0.3:
            k = 0.55 + 0.45 * max(0.0, 0.6 * math.cos(a) - 0.4 * math.sin(a) + 0.4)
            G.polygon(s, shade(col, k), [bot[i], bot[j], top[j], top[i]])
    G.polygon(s, col, top)
    G.polygon(s, shade(col, 0.5), top, 1)


def draw_robot(s, rc, cc, th, spin, rad, led):
    zk = ISO["ZK"]
    h = 16
    ct, st = math.cos(th), math.sin(th)

    def loc(u, v, z=0.0):
        return P(rc + u * ct - v * st, cc + u * st + v * ct, z)

    n = 40
    sh = [P(rc + rad * 1.1 * math.cos(2 * math.pi * k / 32) + 0.05, cc + rad * 1.1 * math.sin(2 * math.pi * k / 32) + 0.05)
          for k in range(32)]
    alpha_poly(s, sh, (0, 0, 0, 80))
    bu, bv = rad * 0.62, rad * 0.58
    hx, hy = loc(bu, bv, 2)
    for k in range(3):
        a = math.radians(spin + k * 120)
        e = P(rc + bu * ct - bv * st + 0.2 * math.cos(a), cc + bu * st + bv * ct + 0.2 * math.sin(a), 2)
        G.line(s, (214, 214, 220), (hx, hy), e, 3 * zk + 1)
    cylinder(s, rc, cc, rad, 0, h, (40, 40, 46), n)
    ring = [P(rc + rad * math.cos(2 * math.pi * k / n), cc + rad * math.sin(2 * math.pi * k / n), h) for k in range(n)]
    G.polygon(s, (32, 32, 36), ring)
    G.polygon(s, (86, 86, 96), ring, 3 * zk + 1)
    inner = [P(rc + rad * 0.88 * math.cos(2 * math.pi * k / n), cc + rad * 0.88 * math.sin(2 * math.pi * k / n), h) for k in range(n)]
    G.polygon(s, (22, 22, 26), inner)
    gl = [P(rc + rad * 0.72 * math.cos(a), cc + rad * 0.72 * math.sin(a), h) for a in [3.3 + k * 0.05 for k in range(22)]]
    G.lines(s, (96, 96, 108), False, gl, 3 * zk + 1)
    for v in (-0.12, 0.12):
        x, y = loc(rad * 0.62, v * rad * 1.6, h)
        G.ellipse(s, (70, 70, 78), (x - 6 * zk, y - 3 * zk, 12 * zk, 7 * zk))
    tr = rad * 0.4
    for k in range(n):
        j = (k + 1) % n
        a = 2 * math.pi * (k + 0.5) / n
        if math.cos(a) + math.sin(a) > -0.3:
            b = [P(rc + tr * math.cos(2 * math.pi * q / n), cc + tr * math.sin(2 * math.pi * q / n), z)
                 for q, z in ((k, h), (j, h), (j, h + 10), (k, h + 10))]
            G.polygon(s, (14, 14, 18), b)
    topc = [P(rc + tr * math.cos(2 * math.pi * q / n), cc + tr * math.sin(2 * math.pi * q / n), h + 10) for q in range(n)]
    G.polygon(s, (36, 36, 42), topc)
    G.polygon(s, (92, 92, 102), topc, 2)
    z = rad * 0.13
    zp = [loc(-z, -z, h + 10), loc(-z, z, h + 10), loc(z, -z, h + 10), loc(z, z, h + 10)]
    G.lines(s, (176, 176, 184), False, zp, 2)
    if led:
        x, y = loc(rad * 0.3, 0, h + 10)
        G.circle(s, (90, 230, 150), (x, y), 4 * zk + 1)


class Scene:
    def __init__(self):
        self.cfg(2)

    def cfg(self, n):
        self.n = n
        self.rows = 1 if n <= 3 else 2
        self.cols = n if n <= 3 else (n + 1) // 2
        self.RS = 2.0
        tot = (self.rows + self.cols) * self.RS
        tw_ = max(44.0, min(150.0, 1100 / tot, (SCENE.h - 44) / (0.62 + tot / 4)))
        ISO["TW"], ISO["TH"], ISO["ZK"] = tw_, tw_ / 2, tw_ / 150
        self.wall_h = 100
        total_h = self.wall_h * ISO["ZK"] + tot * ISO["TH"] / 2 + 18
        cx = SCENE.x + 282
        ISO["OX"] = cx - (self.cols - self.rows) * self.RS * tw_ / 4
        ISO["OY"] = SCENE.y + 26 + (SCENE.h - 26 - total_h) / 2 + self.wall_h * ISO["ZK"] + 4
        self.objs = None
        self.bg = None

    def cell_of(self, i):
        if self.rows == 1:
            return (0, i)
        if i < self.cols:
            return (0, i)
        return (1, 2 * self.cols - 1 - i)

    def index_of(self, gr, gc):
        for i in range(self.n):
            if self.cell_of(i) == (gr, gc):
                return i
        return None

    def room_type(self, gr, gc):
        i = self.index_of(gr, gc)
        return "storage" if i is None else ROOM_TYPES[i % len(ROOM_TYPES)]

    def origin(self, gr, gc):
        return gr * self.RS, gc * self.RS

    def center(self, i):
        gr, gc = self.cell_of(i)
        return gr * self.RS + self.RS / 2, gc * self.RS + self.RS / 2

    def pos_at(self, f):
        f = max(0.0, min(self.n - 1.0, f))
        i = min(int(f), self.n - 2) if self.n > 1 else 0
        t = f - i
        a, b = self.center(i), self.center(min(i + 1, self.n - 1))
        return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t

    def floor(self, s, gr, gc, rnd):
        r0, c0 = self.origin(gr, gc)
        t = self.room_type(gr, gc)
        RS = self.RS
        pts = [(r0, c0, 0), (r0, c0 + RS, 0), (r0 + RS, c0 + RS, 0), (r0 + RS, c0, 0)]
        if t in ("living", "study", "hall"):
            base = {"living": (190, 140, 90), "study": (204, 164, 114), "hall": (150, 108, 72)}[t]
            poly(s, pts, base)
            dark = shade(base, 0.82)
            for k in range(1, 8):
                f = k / 4
                G.line(s, dark, P(r0 + f, c0), P(r0 + f, c0 + RS), 1)
                off = 0.5 + 0.7 * ((k + gr + gc) % 2)
                G.line(s, dark, P(r0 + f, c0 + off), P(r0 + f - 0.25, c0 + off), 1)
        elif t == "kitchen":
            for i in range(4):
                for j in range(4):
                    col = (236, 230, 218) if (i + j) % 2 == 0 else (186, 186, 182)
                    poly(s, [(r0 + i / 2, c0 + j / 2, 0), (r0 + i / 2, c0 + j / 2 + .5, 0),
                             (r0 + i / 2 + .5, c0 + j / 2 + .5, 0), (r0 + i / 2 + .5, c0 + j / 2, 0)], col)
        elif t == "bedroom":
            poly(s, pts, (152, 174, 198))
            for _ in range(60):
                G.circle(s, rnd.choice([(138, 160, 186), (166, 186, 208)]), P(r0 + rnd.random() * RS, c0 + rnd.random() * RS), 2)
        elif t == "bath":
            poly(s, pts, (158, 212, 222))
            for k in range(1, 6):
                G.line(s, (112, 170, 184), P(r0 + k / 3, c0), P(r0 + k / 3, c0 + RS), 1)
                G.line(s, (112, 170, 184), P(r0, c0 + k / 3), P(r0 + RS, c0 + k / 3), 1)
        else:
            poly(s, pts, (150, 150, 152))
            for k in range(1, 4):
                G.line(s, (126, 126, 130), P(r0 + k / 2, c0), P(r0 + k / 2, c0 + RS), 1)
        G.polygon(s, (0, 0, 0), [P(*p) for p in pts], 1)

    def build_bg(self, canvas):
        rnd = random.Random(5)
        s = canvas
        s.fill(BG)
        G.rect(s, PANEL, SCENE, border_radius=14)
        clip = s.get_clip()
        setclip(s, SCENE)
        G.rect(s, (68, 128, 62), SCENE)
        for x in range(SCENE.x, SCENE.right, 56):
            if ((x - SCENE.x) // 56) % 2 == 0:
                G.rect(s, (74, 138, 66), (x, SCENE.y, 56, SCENE.h))
        for _ in range(900):
            x, y = rnd.uniform(SCENE.x, SCENE.right), rnd.uniform(SCENE.y, SCENE.bottom)
            g = rnd.choice([(52, 104, 50), (88, 156, 76), (60, 118, 56)])
            G.line(s, g, (x, y), (x + rnd.randint(-2, 2), y - rnd.randint(3, 7)), 1)
        R, C, RS = self.rows, self.cols, self.RS
        ground = [P(-0.6, -0.6), P(-0.6, C * RS + 0.6), P(R * RS + 0.6, C * RS + 0.6), P(R * RS + 0.6, -0.6)]
        G.polygon(s, (126, 100, 70), ground)
        G.polygon(s, (92, 70, 48), ground, 2)
        SL = 14
        poly(s, [(R * RS, 0, 0), (R * RS, C * RS, 0), (R * RS, C * RS, -SL), (R * RS, 0, -SL)], (176, 170, 158), (90, 84, 74))
        poly(s, [(0, C * RS, 0), (R * RS, C * RS, 0), (R * RS, C * RS, -SL), (0, C * RS, -SL)], (136, 130, 120), (90, 84, 74))
        for gr in range(R):
            for gc in range(C):
                self.floor(s, gr, gc, rnd)
        for tx, ty, sc in [(SCENE.x + 44, SCENE.y + 215, 0.8), (SCENE.x + 540, SCENE.y + 250, 0.7), (SCENE.x + 70, SCENE.y + 120, 0.6)]:
            G.ellipse(s, (30, 80, 30), (tx - 24 * sc, ty - 6 * sc, 48 * sc, 14 * sc))
            G.rect(s, (96, 66, 42), (tx - 5 * sc, ty - 44 * sc, 10 * sc, 48 * sc))
            for dx, dy, rad in [(0, -80, 28), (-18, -62, 22), (18, -62, 22), (0, -58, 24), (-9, -92, 18)]:
                G.circle(s, rnd.choice([(40, 108, 52), (48, 120, 58)]), (tx + dx * sc, ty + dy * sc), rad * sc)
        s.set_clip(clip)
        self.bg = s

    def build_objs(self):
        zk = ISO["ZK"]
        objs = []
        R, C, RS = self.rows, self.cols, self.RS
        wall_c = (238, 230, 214)
        wh = self.wall_h

        def back(s):
            box(s, -0.14, -0.14, R * RS, 0, 0, wh, wall_c)
            box(s, -0.14, -0.14, 0, C * RS, 0, wh, wall_c)
            for gc in range(C):
                a, b = gc * RS + 0.5, gc * RS + RS - 0.5
                poly(s, [(0, a, 44), (0, b, 44), (0, b, 84), (0, a, 84)], (170, 215, 240), (255, 255, 255), 2)
            for gr in range(R):
                a, b = gr * RS + 0.5, gr * RS + RS - 0.5
                poly(s, [(a, 0, 44), (b, 0, 44), (b, 0, 84), (a, 0, 84)], (170, 215, 240), (255, 255, 255), 2)
        objs.append((-9, back))

        T, door = 0.04, 0.9
        g = (RS - door) / 2
        ph = 52
        for gr in range(R):
            for gc in range(C):
                a = self.index_of(gr, gc)
                if gc + 1 < C:
                    b = self.index_of(gr, gc + 1)
                    has = a is not None and b is not None and abs(a - b) == 1
                    r0, c0 = self.origin(gr, gc)
                    x = c0 + RS
                    segs = [(r0, r0 + g), (r0 + RS - g, r0 + RS)] if has else [(r0, r0 + RS)]
                    for u, v in segs:
                        objs.append(((u + v) / 2 + x, lambda s, u=u, v=v, x=x: box(s, u, x - T, v, x + T, 0, ph, wall_c)))
                if gr + 1 < R:
                    b = self.index_of(gr + 1, gc)
                    has = a is not None and b is not None and abs(a - b) == 1
                    r0, c0 = self.origin(gr, gc)
                    y = r0 + RS
                    segs = [(c0, c0 + g), (c0 + RS - g, c0 + RS)] if has else [(c0, c0 + RS)]
                    for u, v in segs:
                        objs.append(((u + v) / 2 + y, lambda s, u=u, v=v, y=y: box(s, y - T, u, y + T, v, 0, ph, wall_c)))

        for gr in range(R):
            for gc in range(C):
                t = self.room_type(gr, gc)
                r0, c0 = self.origin(gr, gc)

                def sr(u0, u1, gr=gr, r0=r0):
                    if gr == 0:
                        return r0 + 0.05 + u0, r0 + 0.05 + u1
                    return r0 + RS - 0.05 - u1, r0 + RS - 0.05 - u0

                def dep(u0, u1, v0, v1, sr=sr, c0=c0):
                    ra, rb = sr(u0, u1)
                    return (ra + rb) / 2 + c0 + (v0 + v1) / 2

                if t == "living":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        flat(s, r0 + 0.7, c0 + 0.5, r0 + 1.3, c0 + 1.5, 0.5, (160, 62, 62), (240, 214, 170))
                        ra, rb = sr(0, 0.18)
                        box(s, ra, c0 + 0.2, rb, c0 + 1.5, 0, 44, (138, 78, 62))
                        ra, rb = sr(0.18, 0.46)
                        box(s, ra, c0 + 0.2, rb, c0 + 1.5, 0, 24, (150, 88, 70))
                    objs.append((dep(0, 0.46, 0.2, 1.5), f))
                elif t == "kitchen":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.38)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.85, 0, 36, (196, 196, 202))
                        ra2, rb2 = sr(0.06, 0.32)
                        flat(s, ra2, c0 + 0.25, rb2, c0 + 0.8, 36, (140, 170, 190), (96, 120, 136))
                        for u, v in [(0.1, 1.2), (0.1, 1.5), (0.26, 1.2), (0.26, 1.5)]:
                            rr = sr(u, u)[0]
                            x, y = P(rr, c0 + v, 36)
                            G.ellipse(s, (40, 40, 44), (x - 8 * zk - 1, y - 4 * zk - 1, 16 * zk + 2, 8 * zk + 2))
                    objs.append((dep(0, 0.38, 0.15, 1.85), f))
                elif t == "bedroom":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.5)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.55, 0, 14, (150, 110, 80))
                        ra, rb = sr(0.03, 0.47)
                        box(s, ra, c0 + 0.19, rb, c0 + 1.51, 14, 26, (238, 238, 244))
                        box(s, ra, c0 + 0.23, rb, c0 + 0.5, 26, 33, (252, 252, 254))
                        flat(s, ra, c0 + 0.7, rb, c0 + 1.5, 26.5, (84, 118, 170), (58, 86, 130))
                    objs.append((dep(0, 0.5, 0.15, 1.55), f))
                elif t == "bath":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.46)
                        box(s, ra, c0 + 0.15, rb, c0 + 1.45, 0, 24, (248, 248, 250))
                        ra2, rb2 = sr(0.07, 0.39)
                        flat(s, ra2, c0 + 0.25, rb2, c0 + 1.35, 24, (120, 190, 226), (170, 176, 184))
                        ra, rb = sr(0, 0.3)
                        box(s, ra, c0 + 1.55, rb, c0 + 1.85, 0, 30, (246, 246, 248))
                    objs.append((dep(0, 0.46, 0.15, 1.85), f))
                elif t == "study":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.42)
                        box(s, ra, c0 + 0.3, rb, c0 + 1.7, 0, 32, (126, 86, 54))
                        ra2, rb2 = sr(0.08, 0.3)
                        box(s, ra2, c0 + 0.85, rb2, c0 + 1.25, 32, 35, (150, 152, 160))
                        box(s, sr(0.04, 0.08)[0], c0 + 0.85, sr(0.04, 0.08)[1], c0 + 1.25, 35, 56, (60, 64, 74))
                    objs.append((dep(0, 0.42, 0.3, 1.7), f))
                elif t == "hall":
                    def f(s, r0=r0, c0=c0, sr=sr):
                        flat(s, r0 + 0.8, c0 + 0.3, r0 + 1.2, c0 + 1.7, 0.5, (86, 120, 100), (214, 196, 150))
                        pr = sr(0.25, 0.25)[0]
                        cylinder(s, pr, c0 + 0.3, 0.13, 0, 18, (160, 100, 60))
                        for dr, dc, h in [(0, 0, 40), (-.07, .05, 30), (.07, -.05, 32)]:
                            x, y = P(pr + dr, c0 + 0.3 + dc, h)
                            G.circle(s, (46, 128, 60), (x, y), 12 * zk + 2)
                    objs.append((dep(0.1, 0.4, 0.3, 0.3), f))
                else:
                    def f(s, r0=r0, c0=c0, sr=sr):
                        ra, rb = sr(0, 0.45)
                        box(s, ra, c0 + 0.2, rb, c0 + 0.8, 0, 30, (170, 130, 80))
                        box(s, ra, c0 + 1.0, rb, c0 + 1.5, 0, 22, (150, 110, 70))
                    objs.append((dep(0, 0.45, 0.2, 1.5), f))
        objs.sort(key=lambda t: t[0])
        self.objs = objs


DIRTY = (150, 108, 66)
CLEAN = (80, 184, 116)

_MINI = register_cache({})


def mini_state(state, w, h):
    pw, ph = max(8, round(w * SC)), max(8, round(h * SC))
    key = (state, pw, ph)
    if key in _MINI:
        return _MINI[key]
    s = pygame.Surface((pw, ph), pygame.SRCALPHA)
    pygame.draw.rect(s, (26, 33, 52), (0, 0, pw, ph), border_radius=max(4, ph // 6))
    n = len(state) - 1
    pad, gap = max(3, pw // 20), max(1, pw // 60)
    sw = (pw - 2 * pad - (n - 1) * gap) / n
    sh, top = ph * 0.46, ph * 0.12
    rr = max(2, ph // 12)
    for i in range(n):
        x = pad + i * (sw + gap)
        dirty = state[1 + i] == "D"
        rect = pygame.Rect(round(x), round(top), round(sw), round(sh))
        pygame.draw.rect(s, DIRTY if dirty else CLEAN, rect, border_radius=rr)
        if dirty:
            for dx, dy in ((0.3, 0.35), (0.65, 0.5), (0.42, 0.75)):
                pygame.draw.circle(s, (60, 44, 30), (x + sw * dx, top + sh * dy), max(1, sh * 0.09))
        else:
            pygame.draw.lines(s, (230, 255, 236), False, [(x + sw * 0.28, top + sh * 0.5), (x + sw * 0.45, top + sh * 0.72),
                                                          (x + sw * 0.74, top + sh * 0.28)], max(1, ph // 20))
    cx, cy = pad + room_index(state) * (sw + gap) + sw / 2, top + sh / 2
    rad = min(sw, sh) * 0.38
    pygame.draw.circle(s, (18, 18, 22), (cx, cy), rad)
    pygame.draw.circle(s, (96, 96, 108), (cx, cy), rad, max(1, ph // 24))
    pygame.draw.circle(s, ORANGE, (cx, cy), max(1, rad * 0.32))
    f = pfont("consolas", max(8, int(ph * 0.25)), True)
    t = f.render(state[0] + " " + "".join(state[1:]), True, (190, 200, 222))
    s.blit(t, t.get_rect(midbottom=(pw // 2, ph - max(1, ph // 14))))
    _MINI[key] = s
    return s


def blit_state(dst, state, cx, cy, w, h, scale=1.0, alpha=1.0):
    """Vẽ thẻ nhỏ `state` kích thước w x h tâm (cx, cy). Trả về Rect đã vẽ."""
    img = mini_state(state, w, h)
    owned = False
    if abs(scale - 1) > 0.02:
        img = pygame.transform.smoothscale(img, (max(2, int(img.get_width() * scale)), max(2, int(img.get_height() * scale))))
        owned = True
    if alpha < 0.98:
        if not owned:
            img = img.copy()
        img.set_alpha(int(255 * max(0, alpha)))
    dst.blit(img, img.get_rect(center=(round(cx * SC), round(cy * SC))))
    k = scale if owned else 1.0
    return pygame.Rect(round(cx - w * k / 2), round(cy - h * k / 2), round(w * k), round(h * k))


class BigCard:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.n = 0                  # số phòng đang vẽ
        self.rx = None              # vị trí ngang của robot (trượt mượt)
        self.dirt = []              # mức bẩn của từng phòng, 0..1 (đổi màu mượt)
        self.alpha = 1.0

    def reset(self):
        self.n, self.rx = 0, None

    def layout(self, n):
        r = self.rect
        sq = min(40, (r.w - 20 - (n - 1) * 6) / n)
        total = n * sq + (n - 1) * 6
        return sq, r.x + (r.w - total) / 2

    def update(self, state, dt, on):
        if state is None:
            return
        n = len(state) - 1
        if n != self.n:
            self.n, self.rx, self.dirt = n, None, [1.0 if v == "D" else 0.0 for v in state[1:]]
        sq, x0 = self.layout(n)
        tx = x0 + room_index(state) * (sq + 6) + sq / 2
        self.rx = tx if self.rx is None else sm(self.rx, tx, 12, dt)
        for i in range(n):
            self.dirt[i] = sm(self.dirt[i], 1.0 if state[1 + i] == "D" else 0.0, 12, dt)
        self.alpha = sm(self.alpha, 1.0 if on else 0.22, 9, dt)

    def draw(self, s, label, border, state):
        r, a = self.rect, self.alpha

        def fd(c):
            return mix(PANEL, c, a)

        G.rect(s, fd((24, 30, 48)), r, border_radius=12)
        G.rect(s, fd(border), r, 2, border_radius=12)
        text(s, label, font("segoeui", 12, True), fd(border), (r.x + 10, r.y + 4))
        if state is None or not self.dirt:
            return
        n = len(state) - 1
        sq, x0 = self.layout(n)
        top = r.y + 20
        for i in range(n):
            x = x0 + i * (sq + 6)
            G.rect(s, fd(mix(CLEAN, DIRTY, self.dirt[i])), (x, top, sq, 30), border_radius=7)
            if self.dirt[i] > 0.5:
                for dx, dy in ((0.28, 0.35), (0.6, 0.55), (0.42, 0.72)):
                    G.circle(s, fd((60, 44, 30)), (x + sq * dx, top + 30 * dy), 2.6)
            else:
                G.lines(s, fd((230, 255, 236)), False, [(x + sq * 0.3, top + 15), (x + sq * 0.45, top + 22), (x + sq * 0.72, top + 8)], 2.5)
            text(s, letter(i), font("segoeui", 12, True), fd(MUTED), (x + sq / 2, top + 33), "midtop")
        cx = self.rx
        G.circle(s, fd((18, 18, 22)), (cx, top + 15), 11)
        G.circle(s, fd((96, 96, 108)), (cx, top + 15), 11, 2)
        G.circle(s, fd(ORANGE), (cx, top + 15), 3.5)


# ------------------------------------------------------------------------------------------------------
# 2.5  MÀN HÌNH ROBOT HÚT BỤI VÀ HỘP THOẠI TỰ ĐẶT
# ------------------------------------------------------------------------------------------------------
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
        rp = px_rect(SCENE)
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
    """Hộp thoại "Tự đặt": vẽ và nhận chuột. Việc đổi số phòng, chọn bụi, áp dụng do VacuumEditor (mục 1.4) làm."""
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


# ------------------------------------------------------------------------------------------------------
# 2.6  CHẠY
# ------------------------------------------------------------------------------------------------------


def main():
    enable_dpi_awareness()
    VacuumScreen().run()


if __name__ == "__main__":
    main()

