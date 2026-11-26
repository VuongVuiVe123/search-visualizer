"""Khung chung của BFS và DFS (graph search). Khác nhau duy nhất: lấy nút ở đầu hay ở đỉnh."""


def run(rec, dfs):
    pb = rec.problem
    init = rec.init
    ds = "ngăn xếp" if dfs else "hàng đợi"
    rec.emit(1, "node = Node(initial_state): tạo nút gốc từ trạng thái đầu.", 0.9)
    if pb.is_goal(init):
        rec.emit(2, "is_goal(node.state) đúng ngay → trả về lời giải rỗng.", 0.8)
        rec.emit(3, "return solution(node)", 0.8, "done")
        return
    rec.emit(2, "is_goal(problem, node.state)? Chưa phải đích → tiếp tục.", 0.6)
    rec.emit(4, "frontier = Stack(): tạo ngăn xếp LIFO rỗng." if dfs else "frontier = Queue(): tạo hàng đợi FIFO rỗng.", 0.5)
    root = rec.add_node(init, None, None)
    rec.frontier.append(root)
    rec.node_eid = None
    rec.emit(5, "push(frontier, node): đặt nút gốc lên ĐỈNH ngăn xếp." if dfs else "enqueue(frontier, node): bỏ nút gốc vào CUỐI hàng đợi.", 0.9)
    rec.emit(6, "explored = []: tập các trạng thái đã mở, ban đầu rỗng.", 0.5)
    while rec.frontier:
        rec.reset_view()
        rec.emit(7, f"while not is_empty(frontier): {ds} còn {len(rec.frontier)} nút → lặp.", 0.4)
        eid = rec.frontier.pop(-1 if dfs else 0)
        nd = rec.nodes[eid]
        rec.node_state, rec.node_eid, rec.node_depth = nd["state"], eid, nd["depth"]
        rec.emit(8, "pop(frontier): lấy nút ở ĐỈNH ngăn xếp (vào sau, ra trước)." if dfs else "dequeue(frontier): lấy nút ở ĐẦU hàng đợi (vào trước, ra trước).", 0.9)
        rec.explored.append(eid)
        rec.emit(9, "explored.append(node.state): đánh dấu trạng thái này đã được mở.", 0.7)
        acts = pb.actions(nd["state"])
        for a in (list(reversed(acts)) if dfs else acts):
            rec.reset_view()
            rec.act = a
            rec.emit(10, f"for action in {'reversed(' if dfs else ''}problem.actions(...){')' if dfs else ''}: thử hành động «{a}».", 0.5)
            rec.ckey += 1
            cs = pb.result(nd["state"], a)
            rec.child = (cs, eid, rec.ckey)
            rec.emit(11, f"child_node(problem, node, «{a}»): {pb.describe(a)}.", 1.0)
            rec.gate[1] = False
            rec.emit(12, f"in_frontier = False: giả sử nút con chưa có trong {ds}.", 0.35)
            hit = [f for f in rec.frontier if rec.nodes[f]["state"] == cs]
            rec.scan_match = hit[0] if hit else None
            rec.emit(13, f"for n in frontier: so sánh nút con với từng nút đang chờ trong {ds}.",
                     0.5 + min(len(rec.frontier), 24) * 0.035, "scan")
            in_frontier = False
            if hit:
                rec.match = hit[0]
                rec.emit(14, "n.state == child.state: TRÙNG với một nút đang chờ!", 0.6)
                in_frontier = True
                rec.gate[1] = True
                rec.emit(15, "in_frontier = True", 0.4)
            in_explored = any(rec.nodes[e]["state"] == cs for e in rec.explored)
            rec.gate[0] = in_explored
            ok = (not in_explored) and not in_frontier
            rec.verdict = "ok" if ok else "dup"
            if ok:
                why = f"chưa mở và chưa có trong {ds} → nút MỚI, xét tiếp."
            elif in_explored:
                why = "trạng thái này đã nằm trong explored → BỎ."
            else:
                why = "trạng thái này đang chờ trong frontier → BỎ."
            rec.emit(16, "if child.state not in explored and not in_frontier: " + why, 1.0, "check")
            if not ok:
                continue
            if pb.is_goal(cs):
                gid = rec.add_node(cs, eid, a)
                rec.verdict = "goal"
                rec.child_eid = gid
                rec.emit(17, "is_goal(problem, child.state): ĐÚNG, đã tới trạng thái đích!", 0.9)
                rec.path, acts_ = rec.chain(gid)
                if dfs and len(acts_) > 12:
                    lst = " → ".join(acts_[:10]) + f" → … ({len(acts_)} bước, DFS không đảm bảo ngắn nhất)"
                else:
                    lst = " → ".join(acts_)
                rec.emit(18, f"return solution(child): lời giải {len(acts_)} bước: " + lst, 2.0, "done")
                return
            rec.emit(17, "is_goal(problem, child.state)? Chưa phải đích.", 0.5)
            cid = rec.add_node(cs, eid, a)
            rec.frontier.append(cid)
            rec.child_eid = cid
            rec.verdict = "queued"
            rec.emit(19, "push(frontier, child): nút con lên ĐỈNH ngăn xếp, đồng thời thêm vào bảng." if dfs else "enqueue(frontier, child): nút con vào CUỐI hàng đợi, đồng thời thêm vào bảng.", 0.95)
    rec.reset_view()
    rec.emit(20, f"return None: {ds} cạn, không có lời giải.", 1.0, "done")


def quick(problem, init, goal, dfs, limit):
    """(độ dài lời giải, số nút phải mở) theo cách đếm của notebook; None nếu vượt giới hạn."""
    if init == goal:
        return 0, 0
    if dfs:
        fr, parent, ex, frs, opened = [init], {init: None}, set(), {init}, 0
        while fr:
            st = fr.pop()
            frs.discard(st)
            ex.add(st)
            opened += 1
            if opened > limit:
                return None
            for a in reversed(problem.actions(st)):
                c = problem.result(st, a)
                if c in ex or c in frs:
                    continue
                parent[c] = st
                if c == goal:
                    n, x = 0, c
                    while parent[x] is not None:
                        x, n = parent[x], n + 1
                    return n, opened
                fr.append(c)
                frs.add(c)
        return None
    from collections import deque
    fr, seen, opened = deque([(init, 0)]), {init}, 0
    while fr:
        st, d = fr.popleft()
        opened += 1
        if opened > limit:
            return None
        for a in problem.actions(st):
            c = problem.result(st, a)
            if c in seen:
                continue
            if c == goal:
                return d + 1, opened
            seen.add(c)
            fr.append((c, d + 1))
    return None
