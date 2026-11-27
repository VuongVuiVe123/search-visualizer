"""Chạy thuật toán ngay trong cửa sổ dòng lệnh, không cần giao diện.

    python run_console.py                  DFS, robot hút bụi
    python run_console.py bfs              BFS, robot hút bụi
    python run_console.py dfs puzzle8      DFS, 8-puzzle
    python run_console.py ucs puzzle8      UCS, 8-puzzle (in thêm chi phí g của từng bước)

Trạng thái đầu / đích lấy từ INITIAL_STATE / GOAL_STATE trong problems/<tên bài>.py.
"""
import sys

from core.algorithms import ALGORITHMS
from problems import PROBLEMS


def print_state(state):
    if isinstance(state[0], tuple):          # bàn cờ 3x3 (8-puzzle): in từng hàng
        for row in state:
            print(list(row))
    else:                                    # robot hút bụi: in trên một dòng
        print("[" + ", ".join(state) + "]")
    print()


def move_cost(problem, prev_state, state):
    """Chi phí đi từ prev_state sang state: tìm hành động nối hai trạng thái rồi hỏi step_cost."""
    for action in problem.actions(prev_state):
        if problem.result(prev_state, action) == state:
            return problem.step_cost(prev_state, action)
    return 0


def main(algo="dfs", problem_id="vacuum"):
    pmod = PROBLEMS[problem_id]
    problem = pmod.make_problem(pmod.INITIAL_STATE, pmod.GOAL_STATE)
    path = ALGORITHMS[algo](problem)
    if path is None:
        print("Không tìm thấy lời giải")
        return
    show_cost = algo == "ucs"
    total = 0
    for i in range(len(path)):
        if i > 0:
            total = total + move_cost(problem, path[i - 1], path[i])
        if show_cost:
            print("Bước", i, "- chi phí g =", total)
        else:
            print("Bước", i)
        print_state(path[i])
    print("Số bước:", len(path) - 1)
    if show_cost:
        print("Tổng chi phí:", total)


if __name__ == "__main__":
    main(*sys.argv[1:])
