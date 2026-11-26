"""Tìm kiếm theo chiều rộng (Breadth-First Search).

Giống hệt DFS, chỉ khác frontier là hàng đợi (Queue) thay vì ngăn xếp (Stack),
và duyệt hành động theo thứ tự xuôi.
Hàm BFS bên dưới chính là hàm giao diện chạy và hiển thị từng dòng.
"""
from core.data_structures import Queue, dequeue, enqueue, is_empty
from core.node import Node, child_node, solution
from core.problem import is_goal


def BFS(problem):
    node = Node(problem.initial_state)
    if is_goal(problem, node.state):
        return solution(node)
    frontier = Queue()
    enqueue(frontier, node)
    explored = []
    while not is_empty(frontier):
        node = dequeue(frontier)
        explored.append(node.state)
        for action in problem.actions(node.state):
            child = child_node(problem, node, action)
            in_frontier = False
            for n in frontier:
                if n.state == child.state:
                    in_frontier = True
            if child.state not in explored and not in_frontier:
                if is_goal(problem, child.state):
                    return solution(child)
                enqueue(frontier, child)
    return None
