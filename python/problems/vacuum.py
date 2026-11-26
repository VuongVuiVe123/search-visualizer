import random

from framework import Problem

ID = "vacuum"

ACT_VI = {
    "Suck": "hút bụi phòng hiện tại → phòng đó thành C",
    "Left": "robot sang phòng bên trái",
    "Right": "robot sang phòng bên phải",
}


class Vacuum(Problem):
    """Trạng thái: (vị trí robot, trạng thái từng phòng) với 'D' = bẩn, 'C' = sạch."""

    id = ID

    def actions(self, s):
        return ["Suck", "Left", "Right"]

    def result(self, s, a):
        n = len(s) - 1
        pos, st = s[0], list(s[1:])
        if a == "Suck":
            st[pos] = "C"
        elif a == "Left":
            pos = max(0, pos - 1)
        elif a == "Right":
            pos = min(n - 1, pos + 1)
        return (pos,) + tuple(st)

    def describe(self, a):
        return ACT_VI[a]


def make(init, goal):
    return Vacuum(tuple(init), tuple(goal))


def solvable(init, goal):
    return len(init) == len(goal)


def scramble(goal):
    n = len(goal) - 1
    dirt = [random.random() < 0.6 for _ in range(n)]
    if not any(dirt):
        dirt[random.randrange(n)] = True
    return (random.randrange(n),) + tuple("D" if d else "C" for d in dirt)
