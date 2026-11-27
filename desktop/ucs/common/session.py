"""LOGIC (không dùng pygame): một phiên chạy UCS trên một bài toán.

Phiên giữ mọi thứ không thuộc về việc vẽ:
    - bài toán đang chạy (trạng thái đầu, đích) và các bài mẫu
    - bản ghi từng dòng của UCS (tracing/tracer.py: Recording)
    - con trỏ phát lại (playback.Player) và chạy lời giải (playback.SolutionReplay)
    - kiểm tra một bài tự đặt có giải được và có vừa sức trình chiếu không

Mỗi bài toán kế thừa lớp này và chỉ khai báo bài toán nào (PROBLEM), vài thông số. Xem puzzle8/logic.py, vacuum/logic.py.
"""
from desktop.ucs.common.playback import Player, SolutionReplay
from tracing.algorithm_info import ALGORITHM_INFO
from tracing.stats import quick, random_initial
from tracing.tracer import Recording, algorithm_code, take_line


class Check:
    """Kết quả kiểm tra một bài: ok (được dùng không), level ("ok" / "warn" / "error"), msg (câu báo cho người dùng)."""

    def __init__(self, ok, level, msg):
        self.ok, self.level, self.msg = ok, level, msg


class UCSSession:
    ALGO = "ucs"
    PROBLEM = None                  # module bài toán, vd. problems/puzzle8.py
    PROBLEM_ID = ""                 # khóa trong problems.PROBLEMS
    RANDOM_KEEPS_GOAL = True        # bấm "Ngẫu nhiên": giữ nguyên đích (8-puzzle) hay đổi cả đích (robot hút bụi)
    UNSOLVABLE_MSG = "Bài này không có lời giải."
    REPLAY_STEP = 0.8               # mỗi trạng thái của lời giải hiện bao nhiêu giây
    REPLAY_MAX_SPEED = 8.0
    REPLAY_HOLD = 1.6               # đứng ở đích thêm bao lâu rồi tự tắt

    def __init__(self):
        self.info = ALGORITHM_INFO[self.ALGO]               # tên, màu, giới hạn số nút, nhãn hai đèn kiểm tra
        self.code = algorithm_code(self.ALGO)[0]            # mã nguồn thật của hàm UCS để hiển thị
        self.node_line = take_line(self.ALGO)               # dòng pop(frontier)
        self.presets = self._load_presets()                 # [(nhãn, trạng thái đầu, trạng thái đích), ...]
        self.preset = -1                                    # đang dùng bài mẫu số mấy (-1: bài ngẫu nhiên / tự đặt)
        self.notice = None                                  # câu cần báo cho người dùng (giao diện lấy ra bằng pop_notice)
        self.player = None
        self.replay = None
        self.load_preset(min(self.PROBLEM.DEFAULT_PRESET, len(self.presets) - 1))

    # ---------- bài toán và bài mẫu ----------
    def _load_presets(self):
        raw = self.PROBLEM.PRESETS
        if isinstance(raw, dict):
            raw = raw.get(self.ALGO) or next(iter(raw.values()))
        return [(p[0], p[1], p[2] if len(p) > 2 else self.PROBLEM.GOAL_STATE) for p in raw]

    def load(self, init, goal):
        """Nạp một bài mới: tạo Problem, chạy UCS và ghi lại từng dòng."""
        speed_i = self.player.speed_i if self.player else 2
        self.problem = self.PROBLEM.make_problem(init, goal)
        self.init, self.goal = self.problem.initial_state, self.problem.goal_condition
        self.rec = Recording(self.ALGO, self.PROBLEM_ID, self.problem)
        self.player = Player(self.rec.events, self.node_line)
        self.player.speed_i = speed_i
        self.replay = None

    def load_preset(self, i):
        _, init, goal = self.presets[i]
        self.preset = i
        self.load(init, goal)

    def load_random(self):
        goal = self.goal if self.RANDOM_KEEPS_GOAL else None
        init, goal = random_initial(self.PROBLEM_ID, self.ALGO, goal)
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
        if not self.PROBLEM.solvable(init, goal):
            return Check(False, "error", self.UNSOLVABLE_MSG)
        name = self.info["name"]
        st = quick(self.ALGO, self.PROBLEM.make_problem(init, goal))
        if st is None:
            return Check(False, "warn", f"Giải được nhưng quá lớn: {name} phải mở hơn {self.info['limit']} nút, "
                                        "khó theo dõi. Hãy đặt gần đích hơn.")
        if st[0] == 0:
            return Check(True, "ok", "Trạng thái đầu đã bằng đích: 0 bước.")
        return Check(True, "ok", f"{name} tìm được lời giải {st[0]} bước, mở {st[1]} nút.")
