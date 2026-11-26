from . import graph_search

NAME = "DFS"
FULL = "Depth-First Search"
L1, L2 = "Chiều sâu", "ngăn xếp LIFO"
COLOR = (255, 126, 170)
LIMIT = 600

CODE = [
    "def DFS(problem):",
    "    node = Node(problem.initial_state)",
    "    if is_goal(problem, node.state):",
    "        return solution(node)",
    "    frontier = Stack()",
    "    push(frontier, node)",
    "    explored = []",
    "    while not is_empty(frontier):",
    "        node = pop(frontier)",
    "        explored.append(node.state)",
    "        for action in reversed(problem.actions(node.state)):",
    "            child = child_node(problem, node, action)",
    "            in_frontier = False",
    "            for n in frontier:",
    "                if n.state == child.state:",
    "                    in_frontier = True",
    "            if child.state not in explored and not in_frontier:",
    "                if is_goal(problem, child.state):",
    "                    return solution(child)",
    "                push(frontier, child)",
    "    return None",
]


def run(rec):
    graph_search.run(rec, dfs=True)


def quick(problem, init, goal, limit=None):
    return graph_search.quick(problem, init, goal, True, limit or LIMIT)
