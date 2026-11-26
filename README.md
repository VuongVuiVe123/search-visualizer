# Search Visualizer

Trực quan hóa thuật toán tìm kiếm (BFS, DFS) trên hai bài toán: **8-puzzle** và **robot hút bụi nhiều phòng**.
Mỗi dòng code đang chạy sáng lên và hiện đúng thứ nó làm trên hình (frontier, explored, bảng node).

Thuật toán viết gọn trong `core/` (`Node`, `child_node`, `solution`, `Stack`/`push`/`pop`, `Problem`, `DFS(problem)`);
giao diện chạy **chính hàm đó** và ghi lại từng dòng, không có bản viết lại riêng cho giao diện.

## Cấu trúc: 4 tầng, mỗi tầng một việc

```
core/                    ① THUẬT TOÁN (không có giao diện)
  node.py                Node, child_node, solution
  problem.py             Problem, is_goal
  data_structures.py     Stack / push / pop (DFS), Queue / enqueue / dequeue (BFS), is_empty
  algorithms/
    dfs.py               def DFS(problem)
    bfs.py               def BFS(problem)
    __init__.py          ALGORITHMS = danh sách thuật toán

problems/                ② BÀI TOÁN
  puzzle8.py             trạng thái đầu / đích / bài mẫu, find_blank, actions_8puzzle, result_8puzzle
  vacuum.py              trạng thái đầu / đích / bài mẫu, actions_vacuum, result_vacuum, chi_so_phong
  __init__.py            PROBLEMS = danh sách bài toán

tracing/                 ③ CẦU NỐI thuật toán ↔ giao diện (không chứa thuật toán)
  tracer.py              chạy hàm DFS/BFS thật, ghi lại từng dòng code + frontier / explored
  narration.py           lời thuyết minh tiếng Việt cho từng dòng code
  algorithm_info.py      tên, màu, giới hạn số nút của từng thuật toán
  stats.py               đếm nhanh số bước / số nút, tạo bài ngẫu nhiên
  api.py                 cổng JSON cho giao diện web

web/                     ④ GIAO DIỆN WEB (chỉ vẽ)
  shared/engine.js       khung chung: code sáng dòng, bảng node, frontier, explored, nút điều khiển
  puzzle8/               trang + view.js (vẽ bàn cờ 3x3)
  vacuum/                trang + view.js (vẽ ngôi nhà isometric)
  manifest.json          danh sách tệp Python trình duyệt cần nạp
desktop/                 ④ GIAO DIỆN PYGAME (chỉ vẽ, dùng lại core/ problems/ tracing/)

index.html               trang chủ (GitHub Pages cần tệp này ở thư mục gốc)
run_console.py           chạy thuật toán trong cửa sổ dòng lệnh, không giao diện
```

Quy tắc: tầng sau chỉ được dùng tầng trước. `core/` không biết gì về giao diện; `web/` và `desktop/` không chứa thuật toán.

## Tra nhanh: chức năng nào nằm ở đâu

| Cần tìm | Mở tệp | Tìm tên |
|---|---|---|
| Hàm DFS / BFS | `core/algorithms/dfs.py`, `bfs.py` | `def DFS`, `def BFS` |
| Lớp Node, sinh nút con, lần ngược lời giải | `core/node.py` | `Node`, `child_node`, `solution` |
| Ngăn xếp / hàng đợi | `core/data_structures.py` | `Stack`, `push`, `pop`, `Queue`, `enqueue`, `dequeue` |
| Lớp Problem, kiểm tra đích | `core/problem.py` | `Problem`, `is_goal` |
| **Trạng thái đầu / đích của 8-puzzle** | `problems/puzzle8.py` | `INITIAL_STATE`, `GOAL_STATE` |
| Các bài mẫu 8-puzzle (nút "Bài mẫu") | `problems/puzzle8.py` | `PRESETS` |
| Hành động / kết quả hành động 8-puzzle | `problems/puzzle8.py` | `find_blank`, `actions_8puzzle`, `result_8puzzle` |
| Kiểm tra 8-puzzle giải được không | `problems/puzzle8.py` | `solvable` |
| **Trạng thái đầu / đích robot hút bụi** | `problems/vacuum.py` | `INITIAL_STATE`, `GOAL_STATE` |
| Hành động / kết quả robot hút bụi | `problems/vacuum.py` | `actions_vacuum`, `result_vacuum`, `chi_so_phong` |
| Tạo `Problem(...)` cho từng bài | `problems/<bài>.py` | `make_problem` |
| Lời giải thích hiện dưới khung code | `tracing/narration.py` | `caption` |
| Tên, màu, giới hạn số nút của thuật toán | `tracing/algorithm_info.py` | `ALGORITHM_INFO` |
| Cách giao diện biết dòng nào đang chạy | `tracing/tracer.py` | `Recording` |
| Vẽ bàn cờ 8-puzzle | `web/puzzle8/view.js`, `desktop/8puzzle_pygame.py` | `BigBoard`, `drawMiniBoard` |
| Vẽ ngôi nhà, robot | `web/vacuum/view.js`, `desktop/vacuum_pygame.py` | `Scene`, `drawRobot` |

## Chạy thử

Không cần giao diện:

```
python run_console.py                # DFS, robot hút bụi
python run_console.py bfs puzzle8    # BFS, 8-puzzle
```

Bản web: chạy máy chủ ở thư mục gốc (không mở trực tiếp tệp), rồi mở <http://localhost:8000>:

```
python -m http.server 8000
```

Bản pygame (cần `pip install pygame`):

```
python desktop/8puzzle_pygame.py
python desktop/vacuum_pygame.py
```

## Thêm thuật toán mới (vd. UCS, IDS)

1. Tạo `core/algorithms/<ten>.py` có hàm `<TEN>(problem)` viết cùng kiểu với `dfs.py`, thêm vào `ALGORITHMS`
   trong `core/algorithms/__init__.py` và vào `web/manifest.json`.
2. Thêm thông tin hiển thị vào `ALGORITHM_INFO` trong `tracing/algorithm_info.py`.
3. Nếu thuật toán có dòng code kiểu mới, thêm mẫu nhận dạng vào `ROLES` và câu thuyết minh vào `caption()` trong `tracing/narration.py`.

Giao diện web tự có thêm thẻ chọn thuật toán, áp dụng cho mọi bài toán; đoạn code hiển thị lấy thẳng từ tệp Python.

## Thêm bài toán mới

1. Tạo `problems/<ten>.py` theo bố cục của `vacuum.py` (`INITIAL_STATE`, `GOAL_STATE`, `PRESETS`, `DEFAULT_PRESET`,
   `actions_<ten>`, `result_<ten>`, `make_problem`, `solvable`, `random_goal`, `scramble`, `describe_action`),
   thêm vào `PROBLEMS` trong `problems/__init__.py` và vào `web/manifest.json`.
2. Tạo `web/<ten>/` gồm `index.html` và `view.js` (xem `web/puzzle8/view.js` làm mẫu), rồi thêm một thẻ ở `index.html` gốc.

## Đưa lên GitHub Pages

Settings → Pages → Deploy from a branch → `main`, thư mục `/ (root)`.
Các link: `/` (trang chủ), `/web/puzzle8/`, `/web/vacuum/`. Mọi đường dẫn đều là đường dẫn tương đối.
