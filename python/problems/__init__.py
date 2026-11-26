"""Đăng ký các bài toán. Thêm bài toán mới: tạo tệp mới trong thư mục này rồi thêm vào REGISTRY."""
from . import puzzle8, vacuum

REGISTRY = {"puzzle8": puzzle8, "vacuum": vacuum}
