"""Chạy nhanh thuật toán (không ghi từng dòng) để đếm số bước và số nút phải mở,
và tạo bài ngẫu nhiên vừa sức trình chiếu. Vẫn dùng đúng hàm trong core/algorithms/.
"""
from core.algorithms import ALGORITHMS
from core.problem import Problem
from problems import PROBLEMS
from tracing.algorithm_info import ALGORITHM_INFO


class _TooBig(Exception):
    pass


def quick(algo_key, problem, limit=None):
    """(số bước của lời giải, số nút đã mở); None nếu không có lời giải hoặc phải mở quá `limit` nút.

    Đếm số nút đã mở bằng cách đếm số lần thuật toán gọi problem.actions(...) (mỗi nút mở gọi đúng 1 lần).
    """
    limit = limit or ALGORITHM_INFO[algo_key]["limit"]
    opened = 0

    def counting_actions(state):
        nonlocal opened
        opened += 1
        if opened > limit:
            raise _TooBig
        return problem.actions(state)

    counted = Problem(problem.initial_state, problem.goal_condition, counting_actions, problem.result)
    try:
        path = ALGORITHMS[algo_key](counted)
    except _TooBig:
        return None
    if path is None:
        return None
    return len(path) - 1, opened


def random_initial(problem_id, algo_key, goal_state=None, tries=120):
    """Xáo trạng thái đầu ngẫu nhiên tới khi thuật toán giải được trong giới hạn số nút."""
    pmod = PROBLEMS[problem_id]
    goal_state = tuple(goal_state) if goal_state is not None else pmod.random_goal()
    s = goal_state
    for _ in range(tries):
        s = pmod.scramble(goal_state)
        if quick(algo_key, pmod.make_problem(s, goal_state)) is not None:
            break
    return s, goal_state
