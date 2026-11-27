# Search Visualizer

Trực quan hóa thuật toán tìm kiếm (BFS, DFS, UCS) trên hai bài toán: **8-puzzle** và **robot hút bụi nhiều phòng**.
Mỗi dòng code đang chạy sáng lên và hiện đúng thứ nó làm trên hình (frontier, explored, bảng node).

Thuật toán viết gọn trong `core/` (`Node`, `child_node`, `solution`, `Stack`/`push`/`pop`, `Problem`, `DFS(problem)`);
giao diện chạy **chính hàm đó** và ghi lại từng dòng, không có bản viết lại riêng cho giao diện.

## Cấu trúc: 4 tầng, mỗi tầng một việc

```
core/                    ① THUẬT TOÁN (không có giao diện)
  node.py                Node (có path_cost = chi phí g), child_node, solution
  problem.py             Problem (có step_cost), is_goal
  data_structures.py     Stack / push / pop (DFS), Queue / enqueue / dequeue (BFS), is_empty
  priority_queue.py      PriorityQueue / push / pop theo chi phí g (UCS)
  algorithms/
    dfs.py               def DFS(problem)
    bfs.py               def BFS(problem)
    ucs.py               def UCS(problem), find_in_frontier
    __init__.py          ALGORITHMS = danh sách thuật toán

problems/                ② BÀI TOÁN
  puzzle8.py             trạng thái đầu / đích / bài mẫu, find_blank, actions_8puzzle, result_8puzzle, step_cost_8puzzle
  vacuum.py              trạng thái đầu / đích / bài mẫu, actions_vacuum, result_vacuum, chi_so_phong, step_cost_vacuum
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
  ucs/                   bản CHỈ CHO UCS, mỗi app tách LOGIC và GIAO DIỆN (xem mục "Bản desktop UCS" bên dưới)
  8puzzle_pygame.py      bản đủ BFS / DFS / UCS (một tệp, vừa vẽ vừa điều khiển)
  vacuum_pygame.py       như trên, cho robot hút bụi

index.html               trang chủ (GitHub Pages cần tệp này ở thư mục gốc)
run_console.py           chạy thuật toán trong cửa sổ dòng lệnh, không giao diện
```

Quy tắc: tầng sau chỉ được dùng tầng trước. `core/` không biết gì về giao diện; `web/` và `desktop/` không chứa thuật toán.

## Tra nhanh: chức năng nào nằm ở đâu

| Cần tìm | Mở tệp | Tìm tên |
|---|---|---|
| Hàm DFS / BFS / UCS | `core/algorithms/dfs.py`, `bfs.py`, `ucs.py` | `def DFS`, `def BFS`, `def UCS` |
| Lớp Node, sinh nút con, lần ngược lời giải | `core/node.py` | `Node`, `child_node`, `solution` |
| Ngăn xếp / hàng đợi | `core/data_structures.py` | `Stack`, `push`, `pop`, `Queue`, `enqueue`, `dequeue` |
| Hàng đợi ưu tiên (UCS) | `core/priority_queue.py` | `PriorityQueue`, `push`, `pop` |
| Chi phí g của một nút | `core/node.py` | `path_cost` trong `Node`, cách tính trong `child_node` |
| Lớp Problem, kiểm tra đích | `core/problem.py` | `Problem`, `is_goal` |
| **Trạng thái đầu / đích của 8-puzzle** | `problems/puzzle8.py` | `INITIAL_STATE`, `GOAL_STATE` |
| Các bài mẫu 8-puzzle (nút "Bài mẫu") | `problems/puzzle8.py` | `PRESETS` |
| Hành động / kết quả hành động 8-puzzle | `problems/puzzle8.py` | `find_blank`, `actions_8puzzle`, `result_8puzzle` |
| Chi phí mỗi bước 8-puzzle (Lên/Xuống 1, Trái/Phải 2) | `problems/puzzle8.py` | `step_cost_8puzzle` |
| Kiểm tra 8-puzzle giải được không | `problems/puzzle8.py` | `solvable` |
| **Trạng thái đầu / đích robot hút bụi** | `problems/vacuum.py` | `INITIAL_STATE`, `GOAL_STATE` |
| Hành động / kết quả robot hút bụi | `problems/vacuum.py` | `actions_vacuum`, `result_vacuum`, `chi_so_phong` |
| Chi phí mỗi bước robot (hút 1, trái/phải 2) | `problems/vacuum.py` | `step_cost_vacuum` |
| Tạo `Problem(...)` cho từng bài | `problems/<bài>.py` | `make_problem` |
| Lời giải thích hiện dưới khung code | `tracing/narration.py` | `caption` |
| Tên, màu, giới hạn số nút của thuật toán | `tracing/algorithm_info.py` | `ALGORITHM_INFO` |
| Cách giao diện biết dòng nào đang chạy | `tracing/tracer.py` | `Recording` |
| Vẽ bàn cờ 8-puzzle | `web/puzzle8/view.js`, `desktop/ucs/puzzle8/boards.py` | `BigBoard`, `drawMiniBoard` / `blit_board` |
| Vẽ ngôi nhà, robot | `web/vacuum/view.js`, `desktop/ucs/vacuum/scene.py` | `Scene`, `drawRobot` / `draw_robot` |
| Bản desktop UCS: tải bài, bài mẫu, kiểm tra bài tự đặt, chạy lời giải | `desktop/ucs/common/session.py` | `UCSSession` |
| Bản desktop UCS: nút Phát / Tiếp / Lùi / tốc độ | `desktop/ucs/common/playback.py` | `Player`, `SolutionReplay` |
| Bản desktop UCS: hộp thoại "Tự đặt" (xử lý) | `desktop/ucs/puzzle8/logic.py`, `desktop/ucs/vacuum/logic.py` | `Puzzle8Editor`, `VacuumEditor` |
| Bản desktop UCS: khung chung (đầu trang, bảng node, FRONTIER, ...) | `desktop/ucs/common/screen.py` | `UCSScreen` |

## Chạy thử

Không cần giao diện:

```
python run_console.py                # DFS, robot hút bụi
python run_console.py bfs puzzle8    # BFS, 8-puzzle
python run_console.py ucs puzzle8    # UCS, 8-puzzle (in thêm chi phí g)
```

Phím tắt trong app: B / D / U chọn BFS / DFS / UCS.

Bản web: chạy máy chủ ở thư mục gốc (không mở trực tiếp tệp), rồi mở <http://localhost:8000>:

```
python -m http.server 8000
```

Bản pygame (cần `pip install pygame`):

```
python desktop/ucs/puzzle8/ui.py     # 8-puzzle, chỉ UCS
python desktop/ucs/vacuum/ui.py      # robot hút bụi, chỉ UCS
python desktop/8puzzle_pygame.py     # bản đủ BFS / DFS / UCS
python desktop/vacuum_pygame.py
```

## Nộp bài bản desktop UCS

`desktop/ucs/` đọc thuật toán từ `core/`, bài toán từ `problems/`, bộ ghi từ `tracing/` (dùng chung với bản web),
nên **không nộp riêng thư mục `desktop/`**. Hãy đóng gói bằng một lệnh:

```
python desktop/ucs/make_submission.py
```

Lệnh này tạo `dist/bai_nop_ucs/` và `dist/bai_nop_ucs.zip` (khoảng 60 KB) gồm đúng những thư mục cần thiết, không sửa một dòng code nào,
rồi tự chạy thử bản vừa lắp trong một tiến trình sạch trước khi nén. Đặt tên khác bằng `--name TEN_BAI`.

Giáo viên giải nén, cài `pip install pygame`, rồi chạy `python chay_8puzzle.py` hoặc `python chay_vacuum.py`
(trong zip có `README.txt` hướng dẫn và chỉ chỗ tìm thuật toán, bài toán, giao diện). Thiếu pygame hoặc thiếu thư mục
thì app báo lỗi bằng tiếng Việt thay vì in traceback (xem `desktop/ucs/common/preflight.py`).

## Bản desktop UCS: tách logic và giao diện

```
desktop/ucs/
  make_submission.py  đóng gói bài nộp (xem mục trên)
  common/
    preflight.py    kiểm tra môi trường, báo lỗi tiếng Việt khi thiếu pygame hoặc thư mục
    playback.py     LOGIC  Player (phát / dừng / tiếp / lùi / node kế / tốc độ), SolutionReplay (chạy lời giải)
    session.py      LOGIC  UCSSession: giữ bài toán, bài mẫu, bản ghi UCS; load / random / check bài tự đặt
    theme.py        UI     bảng màu
    kit.py          UI     bộ vẽ nhỏ: chữ, khung, nút, tô màu mã nguồn
    screen.py       UI     UCSScreen: khung chung của cả hai app (đầu trang, mã nguồn, bảng node, FRONTIER, EXPLORED, nút)
  puzzle8/
    logic.py        LOGIC  Puzzle8Session, Puzzle8Editor (đổi ô, xáo, đích chuẩn, kiểm tra, áp dụng)
    boards.py       UI     vẽ bàn cờ 3x3
    ui.py           UI     Puzzle8Screen, hộp thoại; chạy được: python desktop/ucs/puzzle8/ui.py
  vacuum/
    logic.py        LOGIC  VacuumSession, VacuumEditor (số phòng, robot, bụi, đích)
    scene.py        UI     vẽ ngôi nhà isometric và robot
    cards.py        UI     vẽ thẻ trạng thái
    ui.py           UI     VacuumScreen, hộp thoại; chạy được: python desktop/ucs/vacuum/ui.py
```

Các tệp **LOGIC** không import pygame, chạy và kiểm tra được mà không cần màn hình. Các tệp **UI** chỉ vẽ và
nhận phím / chuột rồi gọi sang logic. Thuật toán UCS vẫn nằm ở `core/algorithms/ucs.py`.

## Thêm thuật toán mới (vd. IDS, A*)

1. Tạo `core/algorithms/<ten>.py` có hàm `<TEN>(problem)` viết cùng kiểu với `dfs.py`, thêm vào `ALGORITHMS`
   trong `core/algorithms/__init__.py` và vào `web/manifest.json`.
2. Thêm thông tin hiển thị vào `ALGORITHM_INFO` trong `tracing/algorithm_info.py`.
3. Nếu thuật toán có dòng code kiểu mới, thêm mẫu nhận dạng vào `ROLES` và câu thuyết minh vào `caption()` trong `tracing/narration.py`.

Giao diện web tự có thêm thẻ chọn thuật toán, áp dụng cho mọi bài toán; đoạn code hiển thị lấy thẳng từ tệp Python.

## Thêm bài toán mới

1. Tạo `problems/<ten>.py` theo bố cục của `vacuum.py` (`INITIAL_STATE`, `GOAL_STATE`, `PRESETS`, `DEFAULT_PRESET`,
   `actions_<ten>`, `result_<ten>`, `step_cost_<ten>`, `make_problem`, `solvable`, `random_goal`, `scramble`, `describe_action`),
   thêm vào `PROBLEMS` trong `problems/__init__.py` và vào `web/manifest.json`.
2. Tạo `web/<ten>/` gồm `index.html` và `view.js` (xem `web/puzzle8/view.js` làm mẫu), rồi thêm một thẻ ở `index.html` gốc.

## Đưa lên GitHub Pages

Settings → Pages → Deploy from a branch → `main`, thư mục `/ (root)`.
Các link: `/` (trang chủ), `/web/puzzle8/`, `/web/vacuum/`. Mọi đường dẫn đều là đường dẫn tương đối.
