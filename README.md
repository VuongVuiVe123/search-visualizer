# Search Visualizer

Trực quan hóa thuật toán tìm kiếm (BFS, DFS) trên hai bài toán: **8-puzzle** và **robot hút bụi nhiều phòng**.
Mỗi dòng code đang chạy sáng lên và hiện đúng thứ nó làm trên hình (frontier, explored, bảng node).

Thuật toán và bài toán viết bằng **Python**, chạy ngay trong trình duyệt nhờ [Pyodide](https://pyodide.org).
Giao diện vẽ bằng canvas JavaScript nên chữ và nét sắc ở mọi màn hình.

## Cấu trúc

```
index.html            trang chủ: chọn bài toán
python/               phần Python chạy trong trình duyệt
  framework.py        Problem, Rec (bộ ghi sự kiện)
  algorithms/         mỗi thuật toán một tệp (bfs.py, dfs.py) + graph_search.py dùng chung
  problems/           mỗi bài toán một tệp (puzzle8.py, vacuum.py)
  api.py              cổng giao tiếp JS <-> Python (JSON)
  manifest.json       danh sách tệp Python cần nạp
shared/engine.js      giao diện dùng chung: code sáng dòng, bảng node, frontier, explored, điều khiển
puzzle8/              trang + view.js (phần vẽ riêng của 8-puzzle)
vacuum/               trang + view.js (ngôi nhà isometric của robot hút bụi)
desktop/              bản pygame chạy trên máy (dùng để nộp bài)
```

## Chạy thử trên máy

Trang cần chạy qua máy chủ (không mở trực tiếp tệp):

```
python -m http.server 8000
```

Rồi mở <http://localhost:8000>.

## Thêm thuật toán mới

1. Tạo `python/algorithms/<ten>.py` có `NAME`, `FULL`, `L1`, `L2`, `COLOR`, `LIMIT`, `CODE` (các dòng code hiển thị),
   `run(rec)` (ghi sự kiện bằng `rec.emit(...)`) và `quick(problem, init, goal, limit)`.
2. Thêm vào `REGISTRY` trong `python/algorithms/__init__.py` và vào `python/manifest.json`.

Công tắc thuật toán trên giao diện tự có thêm thẻ mới, áp dụng cho mọi bài toán.

## Thêm bài toán mới

1. Tạo `python/problems/<ten>.py` (lớp kế thừa `Problem`, cùng `make`, `solvable`, `scramble`),
   thêm vào `REGISTRY` trong `python/problems/__init__.py` và vào `manifest.json`.
2. Tạo thư mục `<ten>/` gồm `index.html` và `view.js` (xem `puzzle8/view.js` làm mẫu), rồi thêm một thẻ ở `index.html` gốc.

## Đưa lên GitHub Pages

Settings → Pages → Deploy from a branch → `main`, thư mục `/ (root)`.
Các link: `/` (trang chủ), `/puzzle8/`, `/vacuum/`. Mọi đường dẫn đều là đường dẫn tương đối.
