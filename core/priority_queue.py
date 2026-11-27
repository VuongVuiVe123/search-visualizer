"""Hàng đợi ưu tiên (Priority Queue) cho UCS.

Các nút luôn được xếp theo chi phí g (path_cost) tăng dần:
    push  chèn nút vào đúng chỗ theo g (nút cùng g thì nút vào sau đứng sau)
    pop   lấy nút ở ĐẦU hàng đợi, tức nút có g NHỎ NHẤT

Tách riêng khỏi data_structures.py vì cũng dùng tên push / pop như Stack.
"""


def PriorityQueue():
    return []


def push(queue, node):
    i = 0
    while i < len(queue) and queue[i].path_cost <= node.path_cost:
        i += 1
    queue.insert(i, node)


def is_empty(queue):
    return len(queue) == 0


def pop(queue):
    if is_empty(queue):
        return None
    node = queue[0]
    del queue[0]
    return node
