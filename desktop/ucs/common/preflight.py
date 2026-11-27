"""Kiểm tra môi trường trước khi mở app (chỉ dùng thư viện chuẩn, chạy được cả khi chưa cài pygame).

Thay vì để Python in một đống lỗi khó hiểu, app báo bằng tiếng Việt: thiếu gì và phải làm gì.
Hay gặp nhất khi nộp bài: máy giáo viên chưa cài pygame, hoặc chỉ nhận được thư mục desktop mà thiếu core / problems / tracing.
"""
import importlib.util
import os
import sys

REQUIRED_DIRS = ("core", "problems", "tracing")         # nằm cạnh thư mục desktop
MIN_PYTHON = (3, 8)


def _stop(message):
    print("\n" + message + "\n")
    try:
        input("Bấm Enter để đóng...")                     # giữ cửa sổ lại khi bấm đúp để chạy
    except EOFError:
        pass
    raise SystemExit(1)


def project_root():
    """Thư mục chứa core/, problems/, tracing/, desktop/ (đi lên từ tệp này: common → ucs → desktop → gốc)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def check_environment():
    if sys.version_info < MIN_PYTHON:
        _stop(f"Cần Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} trở lên (máy này đang là {sys.version.split()[0]}).")
    root = project_root()
    missing = [d for d in REQUIRED_DIRS if not os.path.isdir(os.path.join(root, d))]
    if missing:
        _stop("Thiếu thư mục: " + ", ".join(m + "/" for m in missing) + f"\n(đang tìm trong {root})\n"
              "App cần cả bộ core/, problems/, tracing/, desktop/ nằm chung một thư mục.\n"
              "Hãy giải nén đủ bài nộp, không chỉ lấy riêng thư mục desktop.")
    if importlib.util.find_spec("pygame") is None:
        _stop("Chưa cài thư viện pygame. Mở cửa sổ dòng lệnh và chạy:\n\n    pip install pygame\n\n"
              "(nếu báo không có pip: python -m pip install pygame), rồi chạy lại app.")
