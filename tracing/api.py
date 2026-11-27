"""Cổng giao tiếp giữa giao diện web (JavaScript, qua Pyodide) và Python. Mọi hàm nhận / trả chuỗi JSON.

Bên JavaScript gọi các hàm này trong web/shared/engine.js (đối tượng PY).
"""
import json

from core.algorithms import ALGORITHMS
from problems import PROBLEMS
from tracing.algorithm_info import ALGORITHM_INFO
from tracing.stats import quick, random_initial
from tracing.tracer import Recording, algorithm_code, take_line


def algos_json(_arg=""):
    """Danh sách thuật toán: thông tin hiển thị + mã nguồn thật của hàm (để tô sáng từng dòng)."""
    out = {}
    for key in ALGORITHMS:
        info = ALGORITHM_INFO[key]
        out[key] = {
            "name": info["name"], "full": info["full"], "l1": info["l1"], "l2": info["l2"],
            "color": list(info["color"]), "limit": info["limit"], "frontier": info["frontier"],
            "cost": info["cost"], "gates": list(info["gates"]),
            "code": algorithm_code(key)[0], "takeLine": take_line(key),
        }
    return json.dumps(out, ensure_ascii=False)


def problem_json(arg):
    """Trạng thái đầu / đích / bài mẫu của một bài toán (khai báo trong problems/<tên>.py)."""
    pmod = PROBLEMS[json.loads(arg)]
    presets = pmod.PRESETS
    if isinstance(presets, dict):
        presets = {k: [[p[0], p[1], p[2] if len(p) > 2 else pmod.GOAL_STATE] for p in v] for k, v in presets.items()}
    else:
        presets = [[p[0], p[1], p[2] if len(p) > 2 else pmod.GOAL_STATE] for p in presets]
    return json.dumps({"initial": pmod.INITIAL_STATE, "goal": pmod.GOAL_STATE, "presets": presets,
                       "defaultPreset": pmod.DEFAULT_PRESET}, ensure_ascii=False)


def record_json(arg):
    pid, algo, init, goal = json.loads(arg)
    rec = Recording(algo, pid, PROBLEMS[pid].make_problem(init, goal))
    events = []
    for e in rec.events:
        ch = e["child"]
        events.append({
            "line": e["line"], "cap": e["cap"], "dur": e["dur"], "kind": e["kind"], "act": e["act"],
            "child": None if ch is None else {"state": ch[0], "parent": ch[1], "key": ch[2], "cost": ch[3]},
            "childEid": e["child_eid"], "frontier": e["frontier"], "explored": e["explored"], "tn": e["tn"],
            "gate": e["gate"], "verdict": e["verdict"], "match": e["match"], "scanMatch": e["scan_match"],
            "nodeState": e["node_state"], "nodeEid": e["node_eid"], "nodeDepth": e["node_depth"],
            "nodeCost": e["node_cost"],
            "path": e["path"],
        })
    return json.dumps({
        "events": events,
        "solution": rec.solution,
        "nodes": rec.nodes,
    }, separators=(",", ":"), ensure_ascii=False)


def quick_json(arg):
    pid, algo, init, goal = json.loads(arg)
    return json.dumps(quick(algo, PROBLEMS[pid].make_problem(init, goal)))


def solvable_json(arg):
    pid, init, goal = json.loads(arg)
    return json.dumps(PROBLEMS[pid].solvable(tuple(init), tuple(goal)))


def random_json(arg):
    """Trả về [trạng thái đầu, trạng thái đích]; nếu không đưa đích thì bài toán tự chọn đích ngẫu nhiên."""
    pid, algo, goal = json.loads(arg)
    return json.dumps(list(random_initial(pid, algo, goal)))
