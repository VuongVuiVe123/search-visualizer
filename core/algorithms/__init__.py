"""Danh sách các thuật toán. Thêm thuật toán mới: tạo tệp mới trong thư mục này rồi thêm vào ALGORITHMS."""
from .bfs import BFS
from .dfs import DFS

ALGORITHMS = {"bfs": BFS, "dfs": DFS}
