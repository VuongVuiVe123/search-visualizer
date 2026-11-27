"""Chạy hàm thuật toán thật (vd. DFS trong core/algorithms/dfs.py) và ghi lại từng dòng code đang chạy.

Cách làm: dùng sys.settrace của Python. Mỗi khi hàm thuật toán chạy xong một dòng, ta xem các
biến của nó (node, child, frontier, explored, in_frontier, ...) và ghi lại thành một "sự kiện".
Giao diện chỉ việc phát lại danh sách sự kiện này: tô sáng dòng code, vẽ frontier, explored, ...

Nhờ vậy thuật toán chỉ có MỘT bản duy nhất (trong core/), không phải viết lại cho giao diện.
"""
import inspect
import re
import sys

from core.algorithms import ALGORITHMS
from core.problem import is_goal
from problems import PROBLEMS
from tracing import narration
from tracing.algorithm_info import ALGORITHM_INFO

KIND = {"return_root": "done", "return_child": "done", "return_none": "done", "return_take": "done",
        "scan": "scan", "find_old": "scan", "check": "check", "check_old": "check"}
SCAN_ROLES = ("scan", "compare", "flag_true")


def algorithm_code(algo_key):
    """Mã nguồn của hàm thuật toán (để hiển thị) và số dòng đầu tiên của nó trong tệp."""
    lines, first = inspect.getsourcelines(ALGORITHMS[algo_key])
    return [ln.rstrip("\n") for ln in lines], first


def take_line(algo_key):
    """Chỉ số dòng lấy nút ra khỏi frontier (pop / dequeue): nút "Node kế" trên giao diện nhảy tới dòng này."""
    code, _ = algorithm_code(algo_key)
    return code_roles(code).index("take")


def code_roles(code):
    """Vai trò của từng dòng code. Dòng kiểm tra đích / trả lời giải nằm SAU dòng lấy nút ra (UCS)
    thì đổi thành goal_take / return_take để phân biệt với kiểm tra nút gốc (BFS, DFS)."""
    roles, seen_take = [], False
    for ln in code:
        r = narration.role_of(ln)
        if r == "take":
            seen_take = True
        elif seen_take and r == "goal_root":
            r = "goal_take"
        elif seen_take and r == "return_root":
            r = "return_take"
        roles.append(r)
    return roles


class Recording:
    """Ghi lại một lần chạy thuật toán.

    events    danh sách sự kiện, mỗi sự kiện ứng với một dòng code vừa chạy
    nodes     bảng các nút đã sinh và được giữ lại: state, parent (chỉ số nút cha), action, depth, cost (chi phí g)
    path      chỉ số các nút trên đường đi lời giải (từ gốc tới đích)
    solution  danh sách hành động của lời giải
    """

    def __init__(self, algo_key, problem_id, problem):
        self.algo_key, self.problem_id, self.problem = algo_key, problem_id, problem
        self.algorithm = ALGORITHMS[algo_key]
        self.info = ALGORITHM_INFO[algo_key]
        self.code, self.first_line = algorithm_code(algo_key)
        self.roles = code_roles(self.code)
        self.line_of = {}
        for i, r in enumerate(self.roles):
            self.line_of.setdefault(r, i)

        self.init, self.goal = problem.initial_state, problem.goal_condition
        self.nodes, self.events = [], []
        self.solution, self.path = [], ()
        self._eid, self._keep = {}, []      # id(Node) -> chỉ số trong bảng nút
        self.frontier, self.explored = [], []
        self.node_state, self.node_eid, self.node_depth = self.init, None, 0
        self.ckey = 0
        self.reset_view()
        self._run()

    # ---------------- trạng thái phụ cho phần hình ----------------

    def reset_view(self):
        self.act = None
        self.child = None
        self.child_eid = None
        self.gate = [None, None]     # [đã có trong explored?, đã có trong frontier?]
        self.verdict = None          # ok / dup / goal / queued
        self.match = None
        self.scan_match = None

    def add_node(self, node):
        parent = None if node.parent is None else self._eid[id(node.parent)]
        depth = 0 if parent is None else self.nodes[parent]["depth"] + 1
        self.nodes.append(dict(state=node.state, parent=parent, action=node.action, depth=depth,
                               cost=getattr(node, "path_cost", 0)))
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
        line = self.code[idx]
        m = re.search(r"(\w+)\(", line)
        node_cost = 0 if self.node_eid is None else self.nodes[self.node_eid]["cost"]
        c = dict(line=line, call=m.group(1) if m else "", frontier_kind=self.info["frontier"],
                 optimal=self.info["optimal"], algo_name=self.info["name"], frontier_len=len(self.frontier),
                 action=self.act, solution=self.solution, is_goal=False, in_explored=False, in_frontier=False,
                 node_cost=node_cost, child_cost=None if self.child is None else self.child[3], old_cost=None)
        c.update(extra)
        self.events.append(dict(
            line=idx, cap=narration.caption(role, c), dur=narration.duration(role, c), kind=KIND.get(role, "n"),
            act=self.act, child=self.child, child_eid=self.child_eid,
            frontier=tuple(self.frontier), explored=tuple(self.explored), tn=len(self.nodes),
            gate=tuple(self.gate), verdict=self.verdict, match=self.match, scan_match=self.scan_match,
            node_state=self.node_state, node_eid=self.node_eid, node_depth=self.node_depth,
            node_cost=node_cost, path=self.path))

    # ---------------- chạy thuật toán dưới sys.settrace ----------------

    def _run(self):
        target, first, roles = self.algorithm.__code__, self.first_line, self.roles
        pending = [None, None]           # dòng vừa bắt đầu chạy: [chỉ số, vai trò]
        scan = {"on": False, "hit": None, "flag": False}

        def local(frame, event, arg):
            if event == "line":
                idx = frame.f_lineno - first
                role = roles[idx]
                if scan["on"] and role in SCAN_ROLES:
                    if role == "flag_true":       # vòng "for n in frontier" quét rất nhiều lần: gộp lại
                        scan["flag"] = True
                    return local
                if scan["on"]:
                    self._end_scan(scan)
                if pending[0] is not None:
                    self._finish(pending[0], pending[1], role, frame.f_locals)
                pending[0], pending[1] = idx, role
                if role == "scan":
                    self._start_scan(scan, frame.f_locals)
            elif event == "return" and pending[0] is not None:
                self._finish(pending[0], pending[1], None, frame.f_locals)
                pending[0] = None
            return local

        def on_call(frame, event, arg):
            return local if frame.f_code is target else None

        old = sys.gettrace()
        sys.settrace(on_call)
        try:
            self.algorithm(self.problem)
        finally:
            sys.settrace(old)

    def _start_scan(self, scan, L):
        child = L["child"]
        hit = next((n for n in L["frontier"] if n.state == child.state), None)
        scan.update(on=True, flag=False, hit=None if hit is None else self._eid[id(hit)])
        self.scan_match = scan["hit"]
        self.emit(self.line_of["scan"], "scan", {})

    def _end_scan(self, scan):
        scan["on"] = False
        if scan["flag"]:
            self.match = scan["hit"]
            self.emit(self.line_of["compare"], "compare", {})
            self.gate[1] = True
            self.emit(self.line_of["flag_true"], "flag_true", {})

    def _sync_frontier(self, L):
        if "frontier" in L:
            self.frontier = [self._eid[id(n)] for n in L["frontier"]]

    def _finish(self, idx, role, next_role, L):
        """Dòng `idx` vừa chạy xong; L là các biến của hàm thuật toán lúc này."""
        if role == "scan":
            return                                   # đã ghi ở _start_scan / _end_scan
        if role == "goal_root":
            self.emit(idx, role, {"is_goal": is_goal(self.problem, L["node"].state)})
        elif role == "add_root":
            self.add_node(L["node"])
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "loop":
            if next_role == "return_none":           # frontier rỗng: thoát vòng lặp
                return
            self.reset_view()
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "take":
            eid = self._eid[id(L["node"])]
            self.node_state, self.node_eid, self.node_depth = L["node"].state, eid, self.nodes[eid]["depth"]
            self._sync_frontier(L)
            self.emit(idx, role, {})
        elif role == "mark":
            self.explored.append(self._eid[id(L["node"])])
            self.emit(idx, role, {})
        elif role == "for_action":
            if next_role != "make_child":            # hết hành động: thoát vòng for
                return
            self.reset_view()
            self.act = L["action"]
            self.emit(idx, role, {})
        elif role == "make_child":
            self.ckey += 1
            self.child = (L["child"].state, self._eid[id(L["node"])], self.ckey, L["child"].path_cost)
            pmod = PROBLEMS[self.problem_id]
            self.emit(idx, role, {"describe": pmod.describe_action(L["action"])})
        elif role == "flag_false":
            self.gate[1] = False
            self.emit(idx, role, {})
        elif role == "check":
            in_explored = L["child"].state in L["explored"]
            self.gate[0] = in_explored
            ok = not in_explored and not L["in_frontier"]
            self.verdict = "ok" if ok else "dup"
            self.emit(idx, role, {"in_explored": in_explored, "in_frontier": L["in_frontier"]})
        elif role == "goal_child":
            goal = is_goal(self.problem, L["child"].state)
            if goal:
                self.child_eid = self.add_node(L["child"])
                self.verdict = "goal"
            self.emit(idx, role, {"is_goal": goal})
            if goal:
                self.path, self.solution = self.chain(self.child_eid)
        elif role == "add_child":
            self.child_eid = self.add_node(L["child"])
            self._sync_frontier(L)
            self.verdict = "queued"
            self.emit(idx, role, {})
        elif role == "return_none":
            self.reset_view()
            self.emit(idx, role, {})
        # ----- các dòng riêng của UCS (hàng đợi ưu tiên theo chi phí g) -----
        elif role == "goal_take":
            goal = is_goal(self.problem, L["node"].state)
            if goal:
                self.verdict = "goal"
            self.emit(idx, role, {"is_goal": goal})
            if goal:
                self.path, self.solution = self.chain(self._eid[id(L["node"])])
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
        else:
            self.emit(idx, role, {})
