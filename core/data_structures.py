"""Cấu trúc dữ liệu cho frontier.

    Stack (ngăn xếp, LIFO: vào sau ra trước)  -> dùng cho DFS
    Queue (hàng đợi, FIFO: vào trước ra trước) -> dùng cho BFS
"""


# ---------------- Stack: dùng cho DFS ----------------

def Stack():
    return []


def push(stack, node):
    """Đặt nút lên ĐỈNH ngăn xếp (cuối danh sách)."""
    stack.append(node)


def pop(stack):
    """Lấy nút ở ĐỈNH ngăn xếp ra."""
    if is_empty(stack):
        return None
    node = stack[-1]
    del stack[-1]
    return node


# ---------------- Queue: dùng cho BFS ----------------

def Queue():
    return []


def enqueue(queue, node):
    """Thêm nút vào CUỐI hàng đợi."""
    queue.append(node)


def dequeue(queue):
    """Lấy nút ở ĐẦU hàng đợi ra."""
    if is_empty(queue):
        return None
    node = queue[0]
    del queue[0]
    return node


# ---------------- Dùng chung ----------------

def is_empty(frontier):
    return len(frontier) == 0
