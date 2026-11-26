"""Tìm kiếm theo chiều sâu (Depth-First Search).

Hàm DFS bên dưới chính là hàm giao diện chạy và hiển thị từng dòng,
nên sửa ở đây thì giao diện đổi theo.
"""
from core.data_structures import Stack, is_empty, pop, push
from core.node import Node, child_node, solution
from core.problem import is_goal


def DFS(problem):
    node = Node(problem.initial_state)
    if is_goal(problem, node.state):
        return solution(node)
    frontier = Stack()
    push(frontier, node)
    explored = []
    while not is_empty(frontier):
        node = pop(frontier)
        explored.append(node.state)
        for action in reversed(problem.actions(node.state)):
            child = child_node(problem, node, action)
            in_frontier = False
            for n in frontier:
                if n.state == child.state:
                    in_frontier = True
            if child.state not in explored and not in_frontier:
                if is_goal(problem, child.state):
                    return solution(child)
                push(frontier, child)
    return None
