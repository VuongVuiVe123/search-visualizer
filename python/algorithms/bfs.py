from . import graph_search

NAME = "BFS"
FULL = "Breadth-First Search"
L1, L2 = "Chiều rộng", "hàng đợi FIFO"
COLOR = (86, 214, 230)
LIMIT = 450

CODE = [
    "def BFS(problem):",
    "    node = Node(problem.initial_state)",
    "    if is_goal(problem, node.state):",
    "        return solution(node)",
    "    frontier = Queue()",
    "    enqueue(frontier, node)",
    "    explored = []",
    "    while not is_empty(frontier):",
    "        node = dequeue(frontier)",
    "        explored.append(node.state)",
    "        for action in problem.actions(node.state):",
    "            child = child_node(problem, node, action)",
    "            in_frontier = False",
    "            for n in frontier:",
    "                if n.state == child.state:",
    "                    in_frontier = True",
    "            if child.state not in explored and not in_frontier:",
    "                if is_goal(problem, child.state):",
    "                    return solution(child)",
    "                enqueue(frontier, child)",
    "    return None",
]


def run(rec):
    graph_search.run(rec, dfs=False)


def quick(problem, init, goal, limit=None):
    return graph_search.quick(problem, init, goal, False, limit or LIMIT)
