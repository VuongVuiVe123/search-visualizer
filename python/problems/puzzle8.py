import random

from framework import Problem

ID = "puzzle8"
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)


class Puzzle8(Problem):
    id = ID

    def actions(self, s):
        i = s.index(0)
        r, c = divmod(i, 3)
        out = []
        if r > 0:
            out.append("Lên")
        if r < 2:
            out.append("Xuống")
        if c > 0:
            out.append("Trái")
        if c < 2:
            out.append("Phải")
        return out

    def result(self, s, a):
        i = s.index(0)
        r, c = divmod(i, 3)
        dr, dc = {"Lên": (-1, 0), "Xuống": (1, 0), "Trái": (0, -1), "Phải": (0, 1)}[a]
        j = (r + dr) * 3 + (c + dc)
        l = list(s)
        l[i], l[j] = l[j], l[i]
        return tuple(l)

    def describe(self, a):
        return "trượt ô trống để sinh nút con"


def make(init, goal):
    return Puzzle8(tuple(init), tuple(goal))


def _inversions(s):
    t = [v for v in s if v]
    return sum(1 for i in range(len(t)) for j in range(i + 1, len(t)) if t[i] > t[j])


def solvable(init, goal):
    """Bàn 3x3 (cạnh lẻ): giải được khi hai hoán vị cùng tính chẵn lẻ số nghịch thế."""
    return _inversions(init) % 2 == _inversions(goal) % 2


def scramble(goal):
    pb = Puzzle8(goal, goal)
    s, prev = goal, None
    for _ in range(random.randint(6, 9)):
        opts = [o for o in (pb.result(s, a) for a in pb.actions(s)) if o != prev]
        prev, s = s, random.choice(opts)
    return s
