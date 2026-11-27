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
desktop/                 ④ GIAO DIỆN PYGAME (chạy local, dùng để nộp bài)
  8puzzle_ucs.py         UCS cho 8-puzzle: MỘT TỆP tự chứa, chia rõ PHẦN 1 LOGIC và PHẦN 2 GIAO DIỆN
  vacuum_ucs.py          UCS cho robot hút bụi: cùng cách chia
  8puzzle_pygame.py      bản BFS / DFS / UCS dùng chung core/ problems/ tracing/ (một tệp, vừa vẽ vừa điều khiển)
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
| Vẽ bàn cờ 8-puzzle | `web/puzzle8/view.js`, `desktop/8puzzle_ucs.py` (mục 2.4) | `BigBoard`, `drawMiniBoard` / `blit_board` |
| Vẽ ngôi nhà, robot | `web/vacuum/view.js`, `desktop/vacuum_ucs.py` (mục 2.4) | `Scene`, `drawRobot` / `draw_robot` |
| Bản desktop UCS: hàm UCS, Node, hàng đợi ưu tiên | `desktop/8puzzle_ucs.py` mục 1.1 | `UCS`, `Node`, `push`, `pop` |
| Bản desktop UCS: trạng thái đầu / đích / bài mẫu / chi phí | `desktop/8puzzle_ucs.py` mục 1.2 (robot: `vacuum_ucs.py`) | `INITIAL_STATE`, `PRESETS`, `step_cost_8puzzle` |
| Bản desktop UCS: ghi từng dòng code đang chạy | mục 1.3 | `Recorder` |
| Bản desktop UCS: nút Phát / Tiếp / Lùi, chạy lời giải, nạp bài, kiểm tra bài tự đặt | mục 1.4 | `Player`, `SolutionReplay`, `UCSSession`, `Puzzle8Editor` |
| Bản desktop UCS: mọi thứ để vẽ | PHẦN 2 (từ dòng kẻ "Ranh giới") | `UCSScreen`, `Puzzle8Screen`, `Puzzle8Dialog` |

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
python desktop/8puzzle_ucs.py        # 8-puzzle, chỉ UCS, một tệp tự chứa
python desktop/vacuum_ucs.py         # robot hút bụi, chỉ UCS, một tệp tự chứa
python desktop/8puzzle_ucs.py --console   # chỉ phần LOGIC, in lời giải ra màn hình, không cần pygame
python desktop/8puzzle_pygame.py     # bản BFS / DFS / UCS dùng chung core/ problems/ tracing/
python desktop/vacuum_pygame.py
```

## Nộp bài bản desktop UCS

Chỉ cần nộp **hai tệp** `desktop/8puzzle_ucs.py` và `desktop/vacuum_ucs.py`. Mỗi tệp tự chứa đủ (hàm UCS, bài toán, bộ ghi từng dòng,
giao diện), không cần `core/`, `problems/`, `tracing/` hay thư mục nào khác. Máy chạy chỉ cần Python 3.8 trở lên và `pip install pygame`.

Trong mỗi tệp, một dòng kẻ lớn ("Ranh giới") chia đôi:

```
PHẦN 1  LOGIC (không dùng pygame)
    1.1  Thuật toán UCS               Node, Problem, PriorityQueue, child_node, solution, find_in_frontier, UCS
    1.2  Bài toán                     trạng thái đầu / đích, actions, result, chi phí mỗi bước, bài mẫu
    1.3  Ghi lại từng dòng của UCS    Recorder: chạy chính hàm UCS dưới sys.settrace, ghi một "sự kiện" sau mỗi dòng
    1.4  Phát lại và phiên làm việc   Player, SolutionReplay, UCSSession, hộp thoại "Tự đặt" (mô hình)
------------------------------------  Ranh giới: phía trên không dùng pygame; --console dừng ở đây
PHẦN 2  GIAO DIỆN (pygame), chỉ vẽ và nhận phím / chuột, gọi sang phần 1 để làm việc
    2.1  Bảng màu   2.2  Bộ vẽ nhỏ   2.3  Khung màn hình chung   2.4  Hình vẽ riêng   2.5  Màn hình và hộp thoại   2.6  main
```

Hai tệp này có bản sao của hàm UCS và bài toán, nên khi sửa `core/algorithms/ucs.py` hay `problems/*.py`, bản desktop UCS không tự đổi theo
(và ngược lại). Bản web và `run_console.py` vẫn dùng `core/`, `problems/`, `tracing/`.

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
