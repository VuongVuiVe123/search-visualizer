"""Mô tả một bài toán tìm kiếm.

Mỗi bài toán (xem thư mục problems/) đưa vào:
    initial_state   trạng thái ban đầu
    goal_condition  trạng thái đích
    actions         hàm actions(state)            -> danh sách hành động làm được
    result          hàm result(state, action)     -> trạng thái mới sau hành động
    step_cost       hàm step_cost(state, action)  -> chi phí của một bước đi (UCS dùng)
                    bỏ trống thì mọi bước đều tốn 1
"""


def unit_step_cost(state, action):
    """Chi phí mặc định: bước nào cũng tốn 1."""
    return 1


class Problem:
    def __init__(self, initial_state, goal_condition, actions, result, step_cost=unit_step_cost):
        self.initial_state = initial_state
        self.goal_condition = goal_condition
        self.actions = actions
        self.result = result
        self.step_cost = step_cost


def is_goal(problem, state):
    return state == problem.goal_condition
