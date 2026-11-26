"""Thông tin hiển thị của từng thuật toán (tên, màu, nhãn...). Không phải thuật toán.

Thêm thuật toán mới: thêm một mục ở đây với cùng khóa như trong core/algorithms/__init__.py.
    frontier   "stack" (LIFO) hoặc "queue" (FIFO): để giao diện vẽ frontier đúng chiều
    optimal    thuật toán có đảm bảo lời giải ngắn nhất không
    limit      số nút tối đa được mở trước khi coi bài là quá lớn để trình chiếu
"""

ALGORITHM_INFO = {
    "bfs": dict(name="BFS", full="Breadth-First Search", l1="Chiều rộng", l2="hàng đợi FIFO",
                color=(86, 214, 230), limit=450, frontier="queue", optimal=True),
    "dfs": dict(name="DFS", full="Depth-First Search", l1="Chiều sâu", l2="ngăn xếp LIFO",
                color=(255, 126, 170), limit=600, frontier="stack", optimal=False),
}
