"""Chạy thuật toán ngay trong cửa sổ dòng lệnh, không cần giao diện (giống notebook trên lớp).

    python run_console.py                  DFS, robot hút bụi (giống notebook vacuum_DFS.ipynb)
    python run_console.py bfs              BFS, robot hút bụi
    python run_console.py dfs puzzle8      DFS, 8-puzzle

Trạng thái đầu / đích lấy từ INITIAL_STATE / GOAL_STATE trong problems/<tên bài>.py.
"""
import sys

from core.algorithms import ALGORITHMS
from problems import PROBLEMS


def print_state(state):
    print("[" + ", ".join(str(v) for v in state) + "]")
    print()


def main(algo="dfs", problem_id="vacuum"):
    pmod = PROBLEMS[problem_id]
    problem = pmod.make_problem(pmod.INITIAL_STATE, pmod.GOAL_STATE)
    path = ALGORITHMS[algo](problem)
    if path is None:
        print("Không tìm thấy lời giải")
    else:
        for i in range(len(path)):
            print("Bước", i)
            print_state(path[i])
        print("Số bước:", len(path) - 1)


if __name__ == "__main__":
    main(*sys.argv[1:])
