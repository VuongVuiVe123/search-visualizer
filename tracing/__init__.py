"""TRACING: cầu nối giữa thuật toán (core/) và giao diện (web/, desktop/).

    tracer.py          chạy hàm thuật toán thật (vd. DFS trong core/algorithms/dfs.py),
                       ghi lại từng dòng code đang chạy cùng frontier / explored / node / child
    narration.py       lời thuyết minh tiếng Việt cho từng loại dòng code
    algorithm_info.py  thông tin hiển thị của thuật toán: tên, màu, giới hạn số nút
    stats.py           chạy nhanh không ghi (đếm số bước, số nút) và tạo bài ngẫu nhiên
    api.py             cổng JSON để giao diện web (JavaScript) gọi vào Python

Thư mục này KHÔNG chứa thuật toán. Thuật toán chỉ nằm trong core/.
"""
