"""Tìm kiếm chi phí đều (Uniform-Cost Search).

Frontier là hàng đợi ưu tiên theo chi phí g: luôn mở nút có g nhỏ nhất trước.
Khác BFS / DFS ở 2 chỗ:
  - kiểm tra đích khi LẤY nút ra khỏi frontier (không phải khi sinh nút con),
    nhờ vậy lời giải tìm được có tổng chi phí nhỏ nhất;
  - nếu gặp lại một trạng thái đang chờ trong frontier bằng đường RẺ HƠN,
    thay nút cũ bằng nút mới.
Hàm UCS bên dưới chính là hàm giao diện chạy và hiển thị từng dòng.
"""
from core.node import Node, child_node, solution
from core.priority_queue import PriorityQueue, is_empty, pop, push
from core.problem import is_goal


def find_in_frontier(frontier, state):
    """Tìm nút đang chờ trong frontier có cùng trạng thái; không có thì trả về None."""
    for n in frontier:
        if n.state == state:
            return n
    return None


def UCS(problem):
    node = Node(problem.initial_state, path_cost=0)
    frontier = PriorityQueue()
    push(frontier, node)
    explored = []
    while not is_empty(frontier):
        node = pop(frontier)
        if is_goal(problem, node.state):
            return solution(node)
        explored.append(node.state)
        for action in problem.actions(node.state):
            child = child_node(problem, node, action)
            old = find_in_frontier(frontier, child.state)
            if child.state not in explored and old is None:
                push(frontier, child)
            elif old is not None and old.path_cost > child.path_cost:
                frontier.remove(old)
                push(frontier, child)
    return None
