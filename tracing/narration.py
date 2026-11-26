"""Lời thuyết minh tiếng Việt cho từng dòng code của thuật toán.

Mỗi dòng code của thuật toán được nhận ra bằng nội dung của nó (ROLES bên dưới),
ví dụ dòng "node = pop(frontier)" có vai trò "take". Nhờ vậy BFS, DFS, và các thuật toán
sau này viết cùng kiểu đều dùng chung bộ lời thuyết minh này.

Thêm thuật toán có dòng code kiểu mới: thêm mẫu vào ROLES và một câu vào caption().
"""
import re

# (vai trò, mẫu nhận dạng nội dung dòng code). Xét lần lượt từ trên xuống.
ROLES = [
    ("make_root",   r"^node = Node\(problem\.initial_state\)$"),
    ("goal_root",   r"^if is_goal\(problem, node\.state\):$"),
    ("return_root", r"^return solution\(node\)$"),
    ("new_frontier", r"^frontier = \w+\(\)$"),
    ("add_root",    r"^\w+\(frontier, node\)$"),
    ("new_explored", r"^explored = \[\]$"),
    ("loop",        r"^while not is_empty\(frontier\):$"),
    ("take",        r"^node = \w+\(frontier\)$"),
    ("mark",        r"^explored\.append\(node\.state\)$"),
    ("for_action",  r"^for action in .*:$"),
    ("make_child",  r"^child = child_node\(problem, node, action\)$"),
    ("flag_false",  r"^in_frontier = False$"),
    ("scan",        r"^for n in frontier:$"),
    ("compare",     r"^if n\.state == child\.state:$"),
    ("flag_true",   r"^in_frontier = True$"),
    ("check",       r"^if child\.state not in explored and not in_frontier:$"),
    ("goal_child",  r"^if is_goal\(problem, child\.state\):$"),
    ("return_child", r"^return solution\(child\)$"),
    ("add_child",   r"^\w+\(frontier, child\)$"),
    ("return_none", r"^return None$"),
]


def role_of(code_line):
    text = code_line.strip()
    for role, pattern in ROLES:
        if re.match(pattern, text):
            return role
    return None


# Thời gian (giây, ở tốc độ x1) mỗi loại dòng được giữ trên màn hình.
DURATION = {
    "make_root": 0.9, "goal_root": 0.6, "return_root": 0.8, "new_frontier": 0.5, "add_root": 0.9,
    "new_explored": 0.5, "loop": 0.4, "take": 0.9, "mark": 0.7, "for_action": 0.5, "make_child": 1.0,
    "flag_false": 0.35, "compare": 0.6, "flag_true": 0.4, "check": 1.0, "goal_child": 0.5,
    "return_child": 2.0, "add_child": 0.95, "return_none": 1.0,
}


def duration(role, c):
    if role == "goal_root" and c["is_goal"]:
        return 0.8
    if role == "goal_child" and c["is_goal"]:
        return 0.9
    if role == "scan":
        return 0.5 + min(c["frontier_len"], 24) * 0.035
    return DURATION[role]


def caption(role, c):
    """c: thông tin lúc dòng vừa chạy xong (xem Tracer._context trong tracer.py)."""
    stack = c["frontier_kind"] == "stack"
    ds = "ngăn xếp" if stack else "hàng đợi"
    call = c["call"]        # tên hàm trên dòng đó, vd "push", "enqueue", "Stack"

    if role == "make_root":
        return "node = Node(initial_state): tạo nút gốc từ trạng thái đầu."
    if role == "goal_root":
        if c["is_goal"]:
            return "is_goal(node.state) đúng ngay → trả về lời giải rỗng."
        return "is_goal(problem, node.state)? Chưa phải đích → tiếp tục."
    if role == "return_root":
        return "return solution(node)"
    if role == "new_frontier":
        return f"frontier = {call}(): tạo {ds} {'LIFO' if stack else 'FIFO'} rỗng."
    if role == "add_root":
        where = "lên ĐỈNH ngăn xếp" if stack else "vào CUỐI hàng đợi"
        verb = "đặt" if stack else "bỏ"
        return f"{call}(frontier, node): {verb} nút gốc {where}."
    if role == "new_explored":
        return "explored = []: tập các trạng thái đã mở, ban đầu rỗng."
    if role == "loop":
        return f"while not is_empty(frontier): {ds} còn {c['frontier_len']} nút → lặp."
    if role == "take":
        if stack:
            return f"{call}(frontier): lấy nút ở ĐỈNH ngăn xếp (vào sau, ra trước)."
        return f"{call}(frontier): lấy nút ở ĐẦU hàng đợi (vào trước, ra trước)."
    if role == "mark":
        return "explored.append(node.state): đánh dấu trạng thái này đã được mở."
    if role == "for_action":
        rev = "reversed(" in c["line"]
        loop = "reversed(problem.actions(...))" if rev else "problem.actions(...)"
        return f"for action in {loop}: thử hành động «{c['action']}»."
    if role == "make_child":
        return f"child_node(problem, node, «{c['action']}»): {c['describe']}."
    if role == "flag_false":
        return f"in_frontier = False: giả sử nút con chưa có trong {ds}."
    if role == "scan":
        return f"for n in frontier: so sánh nút con với từng nút đang chờ trong {ds}."
    if role == "compare":
        return "n.state == child.state: TRÙNG với một nút đang chờ!"
    if role == "flag_true":
        return "in_frontier = True"
    if role == "check":
        head = "if child.state not in explored and not in_frontier: "
        if c["in_explored"]:
            return head + "trạng thái này đã nằm trong explored → BỎ."
        if c["in_frontier"]:
            return head + "trạng thái này đang chờ trong frontier → BỎ."
        return head + f"chưa mở và chưa có trong {ds} → nút MỚI, xét tiếp."
    if role == "goal_child":
        if c["is_goal"]:
            return "is_goal(problem, child.state): ĐÚNG, đã tới trạng thái đích!"
        return "is_goal(problem, child.state)? Chưa phải đích."
    if role == "return_child":
        acts = c["solution"]
        if not c["optimal"] and len(acts) > 12:
            lst = " → ".join(acts[:10]) + f" → … ({len(acts)} bước, {c['algo_name']} không đảm bảo ngắn nhất)"
        else:
            lst = " → ".join(acts)
        return f"return solution(child): lời giải {len(acts)} bước: " + lst
    if role == "add_child":
        if stack:
            return f"{call}(frontier, child): nút con lên ĐỈNH ngăn xếp, đồng thời thêm vào bảng."
        return f"{call}(frontier, child): nút con vào CUỐI hàng đợi, đồng thời thêm vào bảng."
    if role == "return_none":
        return f"return None: {ds} cạn, không có lời giải."
    return c["line"].strip()
