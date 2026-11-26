class Problem:
    """Một bài toán tìm kiếm: trạng thái đầu, đích, hành động và kết quả hành động."""

    id = ""

    def __init__(self, init, goal):
        self.init, self.goal = init, goal

    def actions(self, state):
        raise NotImplementedError

    def result(self, state, action):
        raise NotImplementedError

    def is_goal(self, state):
        return state == self.goal

    def describe(self, action):
        """Mô tả ngắn hành động, dùng trong chú thích của dòng child_node."""
        return ""


class Rec:
    """Chạy một thuật toán trên một bài toán và ghi lại từng sự kiện theo từng dòng code."""

    def __init__(self, problem, algo):
        self.problem, self.algo = problem, algo
        self.init, self.goal = problem.init, problem.goal
        self.nodes = []
        self.events = []
        self.frontier, self.explored = [], []
        self.reset_view()
        self.node_state, self.node_eid, self.node_depth = self.init, None, 0
        self.tn = 0
        self.ckey = 0
        self.path = ()
        algo.run(self)

    def reset_view(self):
        self.act = None
        self.child = None
        self.child_eid = None
        self.gate = [None, None]
        self.verdict = None
        self.match = None
        self.scan_match = None

    def emit(self, line, cap, dur, kind="n"):
        self.events.append(dict(
            line=line, cap=cap, dur=dur, kind=kind, act=self.act, child=self.child, child_eid=self.child_eid,
            frontier=tuple(self.frontier), explored=tuple(self.explored), tn=self.tn,
            gate=tuple(self.gate), verdict=self.verdict, match=self.match, scan_match=self.scan_match,
            node_state=self.node_state, node_eid=self.node_eid, node_depth=self.node_depth, path=self.path))

    def add_node(self, state, parent, action):
        depth = 0 if parent is None else self.nodes[parent]["depth"] + 1
        self.nodes.append(dict(state=state, parent=parent, action=action, depth=depth))
        self.tn = len(self.nodes)
        return len(self.nodes) - 1

    def chain(self, eid):
        out, acts = [], []
        while eid is not None:
            out.append(eid)
            acts.append(self.nodes[eid]["action"])
            eid = self.nodes[eid]["parent"]
        return tuple(reversed(out)), [a for a in reversed(acts) if a]
