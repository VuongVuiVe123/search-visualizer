"""Cổng giao tiếp giữa giao diện JS và Python. Mọi hàm nhận/trả chuỗi JSON."""
import json

from algorithms import REGISTRY as ALGOS
from framework import Rec
from problems import REGISTRY as PROBLEMS


def _tup(x):
    return tuple(x)


def algos_json(_arg=""):
    return json.dumps({k: {
        "name": m.NAME, "full": m.FULL, "l1": m.L1, "l2": m.L2, "color": list(m.COLOR),
        "limit": m.LIMIT, "code": m.CODE,
    } for k, m in ALGOS.items()}, ensure_ascii=False)


def record_json(arg):
    pid, algo, init, goal = json.loads(arg)
    pb = PROBLEMS[pid].make(init, goal)
    rec = Rec(pb, ALGOS[algo])
    events = []
    for e in rec.events:
        ch = e["child"]
        events.append({
            "line": e["line"], "cap": e["cap"], "dur": e["dur"], "kind": e["kind"], "act": e["act"],
            "child": None if ch is None else {"state": ch[0], "parent": ch[1], "key": ch[2]},
            "childEid": e["child_eid"], "frontier": e["frontier"], "explored": e["explored"], "tn": e["tn"],
            "gate": e["gate"], "verdict": e["verdict"], "match": e["match"], "scanMatch": e["scan_match"],
            "nodeState": e["node_state"], "nodeEid": e["node_eid"], "nodeDepth": e["node_depth"],
            "path": e["path"],
        })
    return json.dumps({
        "events": events,
        "solution": [rec.nodes[e]["action"] for e in rec.path if rec.nodes[e]["action"]],
        "nodes": [{"state": n["state"], "parent": n["parent"], "action": n["action"], "depth": n["depth"]}
                  for n in rec.nodes],
    }, separators=(",", ":"), ensure_ascii=False)


def quick_json(arg):
    pid, algo, init, goal = json.loads(arg)
    pb = PROBLEMS[pid].make(init, goal)
    return json.dumps(ALGOS[algo].quick(pb, pb.init, pb.goal))


def solvable_json(arg):
    pid, init, goal = json.loads(arg)
    return json.dumps(PROBLEMS[pid].solvable(_tup(init), _tup(goal)))


def random_json(arg):
    pid, algo, goal = json.loads(arg)
    mod = PROBLEMS[pid]
    goal = _tup(goal)
    s = goal
    for _ in range(120):
        s = mod.scramble(goal)
        if ALGOS[algo].quick(mod.make(s, goal), s, goal) is not None:
            break
    return json.dumps(s)
