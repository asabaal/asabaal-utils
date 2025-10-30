# flowscope/layout_calculator.py
# Layered (Sugiyama-style) layout with crossing reduction for FlowScope function graphs.

from collections import defaultdict, deque
import itertools

VERTICAL_GAP   = 120
HORIZONTAL_GAP = 170
DUMMY_WIDTH    = 1   # virtual
NODE_HEIGHT    = 60
CURVE_PAD      = 70
PORT_OFFSET    = 0.48
LANE_PAD       = 20
GUTTER_PAD     = 140

NODE_WIDTHS = {
    "entry": 140, "exit": 140, "return": 160,
    "conditional": 180, "loop": 200, "merge": 150,
    "assignment": 180, "statement": 180, "block_start": 140,
    "loop_exit": 140, "try": 180, "except": 170,
    "yield": 160, "comprehension_entry": 170,
    "complex_comprehension_violation": 210, "_dummy": DUMMY_WIDTH
}

def _w(t): return NODE_WIDTHS.get(t, 160)
def _lbl(e): return (e.get("label") or "").lower().strip()

def _set_ports(n):
    def p(side, off=0.5): return {"side": side, "offset": off}
    t = n["type"]
    if t == "loop":
        n["ports"] = {"in_entry": p("left", PORT_OFFSET), "out_body": p("bottom"),
                      "in_back": p("right", PORT_OFFSET), "out_exit": p("bottom")}
    elif t == "conditional":
        n["ports"] = {"in": p("top"), "true": p("left", PORT_OFFSET), "false": p("right", PORT_OFFSET)}
    elif t == "merge":
        n["ports"] = {"in_left": p("left", PORT_OFFSET), "in_right": p("right", PORT_OFFSET), "out": p("bottom")}
    elif t == "try":
        n["ports"] = {"in": p("top"), "out_try": p("bottom"), "out_finally": p("bottom"), "out_handler": p("right", PORT_OFFSET)}
    else:
        n["ports"] = {"in": p("top"), "out": p("bottom")}

def _index(graph):
    nodes = {n["id"]: dict(n) for n in graph["nodes"]}
    for n in nodes.values():
        _set_ports(n)
        n["level"] = None
        n["x"] = n["y"] = 0
    out_e = defaultdict(list); in_e = defaultdict(list)
    for e in graph["edges"]:
        out_e[e["from"]].append(e); in_e[e["to"]].append(e)
    return nodes, out_e, in_e

def _find_entry_exit(nodes):
    entry = None; exits = []
    for n in nodes.values():
        if n["type"] == "entry": entry = n
        if n["type"] == "exit":  exits.append(n)
    return entry, exits

# ---- classify edges used for the forward DAG ----
def _is_loop_back(e, nodes):
    if any(k in _lbl(e) for k in ("loop back", "next iteration", "continue")): return True
    dst = nodes[e["to"]]; src = nodes[e["from"]]
    return dst["type"] == "loop" and "done" not in _lbl(e)

def _is_return(e, nodes):
    return nodes[e["from"]]["type"] == "return" or nodes[e["to"]]["type"] == "exit"

def _is_exception(e, nodes):
    a = nodes[e["from"]]["type"]; b = nodes[e["to"]]["type"]
    if a in ("try","except") or b in ("try","except"): return True
    return any(k in _lbl(e) for k in ("except","finally"))

def _is_break(e, nodes): return "break" in _lbl(e)

def _forward_edges(edges, nodes):
    f = []
    for e in edges:
        if _is_loop_back(e, nodes): continue
        if _is_return(e, nodes):    continue
        if _is_exception(e, nodes): continue
        if _is_break(e, nodes):     continue
        f.append(e)
    return f

# ---- longest-path levels on forward DAG ----
def _levels_longest_path(nodes, edges, entry):
    if not entry: return
    fwd = _forward_edges(edges, nodes)
    out = defaultdict(list); indeg = defaultdict(int)
    ids = list(nodes.keys())
    for e in fwd:
        u,v = e["from"], e["to"]
        out[u].append(v); indeg[v] += 1
    indeg[entry["id"]] = 0
    q = deque([nid for nid in ids if indeg.get(nid,0) == 0])
    topo = []; seen=set()
    while q:
        u=q.popleft()
        if u in seen: continue
        seen.add(u); topo.append(u)
        for v in out.get(u, []):
            indeg[v]-=1
            if indeg[v] <= 0: q.append(v)
    for nid in ids:
        if nid not in seen: topo.append(nid)

    for n in nodes.values(): n["level"] = float("-inf")
    nodes[entry["id"]]["level"] = 0
    for u in topo:
        lu = nodes[u]["level"]
        if lu == float("-inf"): lu=0; nodes[u]["level"]=0
        for v in out.get(u, []):
            nodes[v]["level"] = max(nodes[v]["level"], lu+1)
    used = sorted({n["level"] for n in nodes.values()})
    remap={lv:i for i,lv in enumerate(used)}
    for n in nodes.values(): n["level"] = remap[n["level"]]

# ---- dummy nodes for long edges (Sugiyama) ----
def _insert_dummies(graph):
    nodes = {n["id"]: n for n in graph["nodes"]}
    edges = []
    next_id = itertools.count(1_000_000)  # dummy id space
    for e in graph["edges"]:
        u = nodes[e["from"]]; v = nodes[e["to"]]
        if u["level"] + 1 >= v["level"]:
            edges.append(e); continue
        # split across levels
        prev = u
        for lv in range(u["level"]+1, v["level"]):
            did = f"d{next(next_id)}"
            dn = {"id": did, "type": "_dummy", "label": "", "level": lv, "x":0, "y":0}
            dn["ports"] = {"in":{"side":"top","offset":0.5},"out":{"side":"bottom","offset":0.5}}
            nodes[did] = dn
            edges.append({"from": prev["id"], "to": did, "label": e.get("label")})
            prev = dn
        edges.append({"from": prev["id"], "to": v["id"], "label": e.get("label")})
    return {"nodes": list(nodes.values()), "edges": edges}

# ---- merge alignment: merge x follows its conditional ----
def _merge_alignment(nodes, out_edges):
    mapping = {}
    for n in nodes.values():
        if n["type"] != "conditional": continue
        seen=set(); stack=[n["id"]]
        while stack:
            u=stack.pop()
            if u in seen: continue
            seen.add(u)
            for e in out_edges.get(u, []):
                t=e["to"]; typ=nodes[t]["type"]
                if typ == "merge": mapping[t]=n["id"]
                elif typ not in ("conditional","merge","loop"): stack.append(t)
    return mapping

# ---- crossing reduction between adjacent ranks ----
def _order_by_barycenter(levels, edges_by_src, edges_by_dst):
    # initial order = declaration order
    # iterative down and up sweeps
    def neighbors_up(nid):   return [e["from"] for e in edges_by_dst.get(nid, [])]
    def neighbors_down(nid): return [e["to"]   for e in edges_by_src.get(nid, [])]

    def sweep(direction="down"):
        rng = range(1, len(levels)) if direction=="down" else range(len(levels)-2, -1, -1)
        for i in rng:
            upper = levels[i-1] if direction=="down" else levels[i+1]
            cur   = levels[i]
            pos = {nid: idx for idx, nid in enumerate(upper)}
            bary = []
            for nid in cur:
                neigh = neighbors_up(nid) if direction=="down" else neighbors_down(nid)
                if neigh:
                    b = sum(pos.get(p, 0) for p in neigh) / len(neigh)
                else:
                    b = cur.index(nid)
                bary.append((b, nid))
            bary.sort(key=lambda x: (x[0], x[1]))
            levels[i] = [nid for _, nid in bary]

    # run 2 full passes
    sweep("down"); sweep("up"); sweep("down")
    return levels

# ---- placement ----
def _place(nodes, edges, entry, exits):
    # build adjacency for ordering
    edges_by_src = defaultdict(list); edges_by_dst = defaultdict(list)
    for e in edges:
        edges_by_src[e["from"]].append(e)
        edges_by_dst[e["to"]].append(e)

    # compute level lists
    by_lv = defaultdict(list)
    for n in nodes.values():
        by_lv[n["level"]].append(n["id"])
    max_lv = max(by_lv) if by_lv else 0
    levels = [by_lv[i] for i in range(max_lv+1)]

    # merge-align constraints (pin merge index to its cond index)
    id2 = {n["id"]: n for n in nodes.values()}
    out_map = defaultdict(list)
    for e in edges: out_map[e["from"]].append(e)
    align = _merge_alignment(id2, out_map)

    # crossing reduction with barycenter
    levels = _order_by_barycenter(levels, edges_by_src, edges_by_dst)

    # fix merge alignment by local swap to conditional column
    for mid, cid in align.items():
        # find their ranks
        for r, arr in enumerate(levels):
            if cid in arr:
                cond_rank, cond_idx = r, arr.index(cid)
                break
        for r2, arr2 in enumerate(levels):
            if mid in arr2:
                merge_rank, merge_idx = r2, arr2.index(mid)
                break
        if merge_rank != cond_rank and merge_idx != cond_idx:
            # reinsert merge at cond column index position for its rank
            arr2 = levels[merge_rank]
            arr2.remove(mid)
            insert_at = min(cond_idx, len(arr2))
            arr2.insert(insert_at, mid)

    # x,y assignment by rank order
    x_pos = {}
    for r, arr in enumerate(levels):
        for j, nid in enumerate(arr):
            n = id2[nid]
            n["x"] = j * HORIZONTAL_GAP
            n["y"] = r * VERTICAL_GAP
            x_pos[nid] = n["x"]

    # force exit at bottom rank + 1
    if nodes and exits:
        deepest = max(n["level"] for n in nodes.values())
        for ex in exits:
            ex["level"] = deepest + 1
            ex["y"] = ex["level"] * VERTICAL_GAP
            # put exit under the main spine column (entry column index)
            ex["x"] = id2[entry["id"]]["x"] if entry else 0

    # compute gutter x
    max_x = max(n["x"] for n in nodes.values()) if nodes else 0
    gutters = {
        "return": max_x + GUTTER_PAD * 2,
        "loop":   max_x + GUTTER_PAD,
        "break":  max_x + GUTTER_PAD * 1.5,
        "except": -GUTTER_PAD * 2
    }
    return gutters

# ---- ports & routing ----
def _choose_ports(e, nodes):
    s = nodes[e["from"]]; d = nodes[e["to"]]; lbl = _lbl(e)
    fp, tp = e.get("from_port"), e.get("to_port")
    if s["type"] == "conditional":
        if lbl.startswith("true"): fp = fp or "true"
        elif lbl.startswith("false"): fp = fp or "false"
        else: fp = fp or "out"
    elif s["type"] == "loop":
        if lbl.startswith(("iterate","true")) or lbl == "": fp = fp or "out_body"
        elif any(k in lbl for k in ("done","false","break","complete")): fp = fp or "out_exit"
        else: fp = fp or "out_body"
    elif s["type"] == "try":
        fp = fp or ("out_finally" if "finally" in lbl else "out_try")
    else:
        fp = fp or "out"
    if d["type"] == "loop":
        tp = tp or ("in_back" if _is_loop_back(e, nodes) else "in_entry")
    elif d["type"] == "merge":
        tp = tp or ("in_left" if d["x"] >= s["x"] else "in_right")
    else:
        tp = tp or "in"
    e["from_port"], e["to_port"] = fp, tp

def _route(edges, nodes, gutters):
    laid=[]
    for e in edges:
        ed=dict(e)
        _choose_ports(ed, nodes)
        s = nodes[ed["from"]]; d = nodes[ed["to"]]
        # special edges to gutters
        if _is_return(ed, nodes):
            bx = gutters["return"]
            ed["style"]={"type":"orthogonal","dashed":True}
            ed["control_points"]=[{"x": bx, "y": s["y"]}, {"x": bx, "y": d["y"]-CURVE_PAD}]
            laid.append(ed); continue
        if _is_loop_back(ed, nodes):
            bx = gutters["loop"]
            ed["style"]={"type":"bezier","curved":True,"dashed":True}
            ed["control_points"]=[{"x": max(bx, s["x"], d["x"]), "y": (s["y"]+d["y"])/2}]
            laid.append(ed); continue
        if _is_break(ed, nodes):
            bx = gutters["break"]
            ed["style"]={"type":"bezier","curved":True,"dashed":True}
            ed["control_points"]=[{"x": max(bx, s["x"]), "y": s["y"]-CURVE_PAD}]
            laid.append(ed); continue
        if _is_exception(ed, nodes):
            bx = gutters["except"]
            ed["style"]={"type":"bezier","curved":True,"dashed":True}
            ed["control_points"]=[{"x": min(bx, s["x"]), "y": (s["y"]+d["y"])/2}]
            laid.append(ed); continue
        # forward default
        if d["y"] > s["y"]:
            ed["style"]={"type":"straight"}; ed["control_points"]=[]
        else:
            ed["style"]={"type":"bezier","curved":True}
            ed["control_points"]=[{"x": s["x"], "y": min(s["y"], d["y"]) - CURVE_PAD*0.6}]
        laid.append(ed)
    return laid

# -------------------- Public API --------------------
def compute_layout(graph: dict) -> dict:
    # 0) index
    nodes, out_e, in_e = _index(graph)
    entry, exits = _find_entry_exit(nodes)

    # 1) levels (how far into the function)
    _levels_longest_path(nodes, graph["edges"], entry)

    # 2) create dummy nodes to split long edges
    with_dummies = _insert_dummies({"nodes": list(nodes.values()), "edges": graph["edges"]})
    nodes = {n["id"]: n for n in with_dummies["nodes"]}

    # 3) place with crossing reduction + merge alignment
    out_map = defaultdict(list)
    for e in with_dummies["edges"]: out_map[e["from"]].append(e)
    gutters = _place(nodes, with_dummies["edges"], entry, exits)

    # 4) y/x already set; route edges
    laid_edges = _route(with_dummies["edges"], nodes, gutters)

    # 5) clean (optional: hide dummy nodes from renderer, but keep for routing)
    final_nodes = []
    for n in nodes.values():
        if n["type"] == "_dummy": continue   # comment this if renderer needs them
        final_nodes.append(n)

    return {
        **graph,
        "nodes": final_nodes,
        "edges": laid_edges,
        "layout": {
            "vertical_gap": VERTICAL_GAP,
            "horizontal_gap": HORIZONTAL_GAP,
            "node_heights": NODE_HEIGHT,
            "node_widths": NODE_WIDTHS,
            "gutters": gutters
        }
    }

