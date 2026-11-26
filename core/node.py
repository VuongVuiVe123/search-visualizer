"""Nút của cây tìm kiếm."""


class Node:
    def __init__(self, state, parent=None, action=None):
        self.state = state      # trạng thái mà nút này đại diện
        self.parent = parent    # nút cha (None nếu là nút gốc)
        self.action = action    # hành động đã làm để đi từ cha tới nút này


def child_node(problem, parent, action):
    """Sinh nút con: áp dụng hành động lên trạng thái của nút cha."""
    new_state = problem.result(parent.state, action)
    return Node(state=new_state, parent=parent, action=action)


def solution(node):
    """Lần ngược từ nút đích về nút gốc, trả về danh sách trạng thái từ đầu tới đích."""
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    path.reverse()
    return path
