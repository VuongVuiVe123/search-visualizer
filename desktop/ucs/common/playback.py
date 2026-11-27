"""LOGIC (không dùng pygame): con trỏ phát lại danh sách sự kiện và chạy lời giải.

Thuật toán UCS chạy xong một lần và ghi thành danh sách sự kiện (tracing/tracer.py).
Hai lớp dưới đây chỉ quản lý "đang xem sự kiện số mấy", giống một trình phát video:

    Player           phát / dừng / tiếp / lùi / về đầu / nhảy tới nút kế / đổi tốc độ
    SolutionReplay   sau khi tìm xong, đi lần lượt qua các trạng thái của lời giải từ đầu tới đích
"""

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
