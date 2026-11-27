"""PROBLEMS: mỗi bài toán một tệp. Thêm bài toán mới: tạo tệp mới rồi thêm vào PROBLEMS.

Mỗi tệp bài toán có cùng bố cục:
    1. Trạng thái ban đầu / đích / bài mẫu   (INITIAL_STATE, GOAL_STATE, PRESETS)
    2. actions_<tên>(state)                     các hành động làm được
    3. result_<tên>(state, action)              trạng thái sau khi làm hành động
    4. step_cost_<tên>(state, action)           chi phí một bước đi (UCS dùng)
    5. make_problem(initial, goal)              ghép lại thành Problem(...)
    6. Tiện ích cho giao diện                   solvable, scramble, random_goal, describe_action
"""
from . import puzzle8, vacuum

PROBLEMS = {"puzzle8": puzzle8, "vacuum": vacuum}
