"""Đóng gói bài nộp: tạo một thư mục (và tệp .zip) TỰ CHỨA ĐỦ, giáo viên giải nén là chạy được.

    python desktop/ucs/make_submission.py                  → dist/bai_nop_ucs/ và dist/bai_nop_ucs.zip
    python desktop/ucs/make_submission.py --name TEN_BAI   → dist/TEN_BAI/ và dist/TEN_BAI.zip
    python desktop/ucs/make_submission.py --no-test        → bỏ bước tự chạy thử

Vì sao cần: hai app UCS đọc thuật toán từ core/, bài toán từ problems/, bộ ghi từng dòng từ tracing/ (dùng chung với bản web).
Lệnh này gom đúng những thư mục cần thiết thành MỘT thư mục, không sửa một dòng code nào, nên thuật toán vẫn chỉ có một bản.

Bên trong bài nộp: core/ problems/ tracing/ desktop/ucs/, README.txt, requirements.txt, chay_8puzzle.py, chay_vacuum.py.
Không có: web/, index.html, hai app pygame cũ, tracing/api.py (cổng riêng của bản web), chính tệp này.
"""
import argparse
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COPY_DIRS = ("core", "problems", "tracing")
SKIP_NAMES = {"__pycache__"}
SKIP_FILES = {os.path.join("tracing", "api.py"), os.path.join("desktop", "ucs", "make_submission.py")}

README = """BÀI NỘP: THUẬT TOÁN UCS (Uniform-Cost Search) - 8-PUZZLE VÀ ROBOT HÚT BỤI
==========================================================================

CÁCH CHẠY
---------
1. Cần Python 3.8 trở lên và thư viện pygame:

       pip install pygame

2. Mở cửa sổ dòng lệnh TRONG thư mục này rồi chạy một trong hai lệnh:

       python chay_8puzzle.py      (8-puzzle)
       python chay_vacuum.py       (robot hút bụi)

   (hoặc mở thẳng desktop/ucs/puzzle8/ui.py, desktop/ucs/vacuum/ui.py trong IDE rồi bấm Run)

App chạy local, không cần internet. Mỗi dòng code của hàm UCS chạy tới đâu thì sáng lên tới đó,
bên cạnh là hàng đợi ưu tiên (FRONTIER), các nút đã mở (EXPLORED) và bảng các nút theo độ sâu.

CHI PHÍ MỖI BƯỚC
----------------
    8-puzzle      : ô trống đi Lên / Xuống tốn 1, đi Trái / Phải tốn 2
    Robot hút bụi : Suck tốn 1, Left / Right tốn 2

PHÍM TẮT
--------
    Space  phát / dừng            Phải / Trái  tiếp / lùi một dòng     N  nhảy tới nút kế (dòng pop)
    R      về đầu                 Lên / Xuống  tăng / giảm tốc độ       G  bài ngẫu nhiên
    T      tự đặt trạng thái      V            chạy lời giải            1-9  chọn bài mẫu
    F11    toàn màn hình          Esc          thoát

TÌM CÁI GÌ Ở ĐÂU
-----------------
    Hàm UCS, tìm nút trùng trong frontier ........ core/algorithms/ucs.py
    Node (có path_cost = g), child_node, solution . core/node.py
    Problem (có step_cost) ....................... core/problem.py
    Hàng đợi ưu tiên (push chèn theo g, pop) ..... core/priority_queue.py
    Trạng thái đầu / đích / bài mẫu 8-puzzle ..... problems/puzzle8.py   (INITIAL_STATE, GOAL_STATE, PRESETS)
    actions / result / chi phí 8-puzzle .......... problems/puzzle8.py   (actions_8puzzle, result_8puzzle, step_cost_8puzzle)
    Trạng thái đầu / đích / bài mẫu robot ........ problems/vacuum.py
    actions / result / chi phí robot ............. problems/vacuum.py    (actions_vacuum, result_vacuum, step_cost_vacuum)
    Ghi lại từng dòng code đang chạy ............. tracing/tracer.py

GIAO DIỆN: LOGIC TÁCH RIÊNG KHỎI VẼ
-----------------------------------
    desktop/ucs/common/playback.py, session.py ... LOGIC (không dùng pygame): phát lại, tải bài, kiểm tra bài tự đặt
    desktop/ucs/puzzle8/logic.py, vacuum/logic.py  LOGIC của từng bài: phiên chạy, hộp thoại "Tự đặt"
    desktop/ucs/common/screen.py, kit.py, theme.py  GIAO DIỆN dùng chung: chỉ vẽ và nhận phím / chuột
    desktop/ucs/puzzle8/ui.py, boards.py ......... GIAO DIỆN 8-puzzle
    desktop/ucs/vacuum/ui.py, scene.py, cards.py .. GIAO DIỆN robot hút bụi
"""

LAUNCHER = '''"""Chạy app UCS {title}.   Cách chạy:   python {file}"""
from desktop.ucs.{pkg}.ui import main

main()
'''

SMOKE_TEST = r"""
import os, sys
sys.path.insert(0, ".")
from core.algorithms.ucs import UCS
from desktop.ucs.puzzle8.logic import Puzzle8Editor, Puzzle8Session
from desktop.ucs.vacuum.logic import VacuumEditor, VacuumSession

p = Puzzle8Session()
assert p.rec.solution and p.player.events, "8-puzzle: UCS không tìm ra lời giải"
chi_phi = lambda s: s.rec.nodes[s.rec.path[-1]]["cost"]
assert UCS(p.problem) is not None
v = VacuumSession()
assert v.rec.solution == ["Suck", "Right", "Suck"] and chi_phi(v) == 4, "robot: sai lời giải hoặc chi phí"
assert Puzzle8Editor(p).ok and VacuumEditor(v).apply()
print("  logic: 8-puzzle %d bước chi phí %d | robot %d bước chi phí %d" % (len(p.rec.solution), chi_phi(p), len(v.rec.solution), chi_phi(v)))
if "pygame" in sys.modules:
    sys.exit("logic không được nạp pygame")
try:
    import pygame
except ImportError:
    print("  giao diện: BỎ QUA (máy này chưa cài pygame)")
    raise SystemExit(0)
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.get_desktop_sizes = lambda: [(1920, 1080)]
from desktop.ucs.puzzle8.ui import Puzzle8Screen
from desktop.ucs.vacuum.ui import VacuumScreen
for cls in (Puzzle8Screen, VacuumScreen):
    app = cls()
    app.press("play")
    for _ in range(30):
        app.apply_scale(); app.update(1 / 30); app.draw()
    app.press("replay")
    for _ in range(10):
        app.apply_scale(); app.update(1 / 30); app.draw()
print("  giao diện: hai app vẽ được 40 khung hình mỗi app")
"""


def _ignore(directory, names):
    rel = os.path.relpath(directory, ROOT)
    return [n for n in names if n in SKIP_NAMES or n.endswith(".pyc") or os.path.join(rel, n) in SKIP_FILES]


def assemble(out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(os.path.join(out_dir, "desktop"))
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(ROOT, d), os.path.join(out_dir, d), ignore=_ignore)
    shutil.copy(os.path.join(ROOT, "desktop", "__init__.py"), os.path.join(out_dir, "desktop", "__init__.py"))
    shutil.copytree(os.path.join(ROOT, "desktop", "ucs"), os.path.join(out_dir, "desktop", "ucs"), ignore=_ignore)
    with open(os.path.join(out_dir, "README.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README)
    with open(os.path.join(out_dir, "requirements.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("pygame>=2.0\n")
    for pkg, title, file in (("puzzle8", "8-puzzle", "chay_8puzzle.py"), ("vacuum", "robot hút bụi", "chay_vacuum.py")):
        with open(os.path.join(out_dir, file), "w", encoding="utf-8", newline="\n") as f:
            f.write(LAUNCHER.format(pkg=pkg, title=title, file=file))


def smoke_test(out_dir):
    """Chạy thử bản vừa lắp trong một tiến trình sạch, chỉ thấy đúng thư mục bài nộp (không thấy dự án gốc)."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PYTHONDONTWRITEBYTECODE"] = "1"            # không để lại __pycache__ trong thư mục bài nộp
    r = subprocess.run([sys.executable, "-c", SMOKE_TEST], cwd=out_dir, env=env, capture_output=True, text=True, timeout=180)
    print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr.rstrip()[-1500:])
        raise SystemExit("Bản đóng gói chạy thử KHÔNG đạt, chưa nộp được.")


def make_zip(out_dir, zip_path):
    name = os.path.basename(out_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(out_dir):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, os.path.join(name, os.path.relpath(full, out_dir)))


def main():
    ap = argparse.ArgumentParser(description="Đóng gói bài nộp UCS desktop thành thư mục và tệp .zip tự chứa đủ.")
    ap.add_argument("--name", default="bai_nop_ucs", help="tên thư mục / tệp zip (mặc định: bai_nop_ucs)")
    ap.add_argument("--no-test", action="store_true", help="bỏ bước tự chạy thử")
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "dist", args.name)
    zip_path = out_dir + ".zip"
    print("1) Lắp thư mục", os.path.relpath(out_dir, ROOT))
    assemble(out_dir)
    if not args.no_test:
        print("2) Chạy thử bản vừa lắp (trong tiến trình sạch)")
        smoke_test(out_dir)
    print("3) Nén", os.path.relpath(zip_path, ROOT))
    make_zip(out_dir, zip_path)
    with zipfile.ZipFile(zip_path) as z:
        n = len(z.namelist())
    print(f"\nXong: {os.path.relpath(zip_path, ROOT)}  ({os.path.getsize(zip_path) // 1024} KB, {n} tệp)")
    print("Nộp tệp .zip này. Giáo viên giải nén, chạy:  pip install pygame  rồi  python chay_8puzzle.py")


if __name__ == "__main__":
    main()
