"""Bản desktop (pygame) CHỈ CHO UCS: một app 8-puzzle và một app robot hút bụi.

Mỗi app tách làm hai phần để dễ đọc:

    logic.py   LOGIC: bài toán, bài mẫu, kiểm tra bài tự đặt, con trỏ phát lại, chạy lời giải.
               Không import pygame, chạy được và test được mà không cần màn hình.
    ui.py      GIAO DIỆN: chỉ vẽ và nhận phím / chuột, gọi sang logic để làm việc.

Thuật toán UCS nằm ở core/algorithms/ucs.py, bài toán ở problems/, ghi từng bước ở tracing/ (dùng chung cả bản web).

    common/    phần dùng chung của hai app (logic: playback.py, session.py · giao diện: theme.py, kit.py, screen.py)
    puzzle8/   app 8-puzzle   → python desktop/ucs/puzzle8/ui.py
    vacuum/    app robot hút bụi → python desktop/ucs/vacuum/ui.py
"""
