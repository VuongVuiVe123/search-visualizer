"""Mô tả một bài toán tìm kiếm (giống code trên lớp).

Mỗi bài toán (xem thư mục problems/) chỉ cần đưa vào 4 thứ:
    initial_state   trạng thái ban đầu
    goal_condition  trạng thái đích
    actions         hàm actions(state)          -> danh sách hành động làm được
    result          hàm result(state, action)   -> trạng thái mới sau hành động
"""


class Problem:
    def __init__(self, initial_state, goal_condition, actions, result):
        self.initial_state = initial_state
        self.goal_condition = goal_condition
        self.actions = actions
        self.result = result


def is_goal(problem, state):
    return state == problem.goal_condition
