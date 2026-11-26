"""Đăng ký các thuật toán. Thêm thuật toán mới: tạo tệp mới trong thư mục này rồi thêm vào REGISTRY."""
from . import bfs, dfs

REGISTRY = {"bfs": bfs, "dfs": dfs}
