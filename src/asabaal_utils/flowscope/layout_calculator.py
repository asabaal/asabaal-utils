# flowscope/region_layout_calculator.py
# Region-aware function-flow layout for FlowScope.
# Goals:
#  - Vertical levels = "how far into the function" (longest-path on forward DAG)
#  - Forward edges straight, split–merge axis preserved
#  - Loop-back / return / break / exception edges routed in side gutters ("buses")
#  - Ports on nodes for clean anchors

from collections import defaultdict, deque

# ------------------- Tunables -------------------
VERTICAL_GAP     = 120
HORIZONTAL_GAP   = 200
LANE_NODE_SPACER = 24

NODE_HEIGHT = 60
NODE_WIDTHS = {
    "entry": 140, "exit": 140, "return": 160,
    "conditional": 180, "loop": 200, "merge": 150,
    "assignment": 180, "statement": 180,
    "block_start": 140, "loop_exit": 140,
    "try": 180, "except": 170, "yield": 160,
    "comprehension_entry": 170,
    "complex_comprehension_violation": 210,
}

# gutter columns (computed later; these are just paddings)
GUTTER_PAD       = 120
CURVE_PAD        = 80
PORT_OFFSET      = 0.48
# ------------------------------------------------


# ----------------- Utilities --------------------
def _w(ntype: str) -> int:
    return NODE_WIDTHS.get(ntype, 160)


def _label(e) -> str:
    return (e.get("label") or "").strip().lower()


def _set_ports(n):
    """Attach logical ports per node type (renderer maps side+offset to xy)."""
    def p(side, offset=0.5):
        return {"side": side, "offset": offset}
    t = n["type"]
    if t == "loop":
        n["ports"] = {
            "in_entry": p("left", PORT_OFFSET),
            "out_body": p("bottom"),
            "in_back":  p("right", PORT_OFFSET),
            "out_exit": p("bottom"),
        }
    elif t == "conditional":
        n["ports"] = {"in": p("top"), "true": p("left", PORT_OFFSET), "false": p("right", PORT_OFFSET)}
    elif t == "merge":
        n["ports"] = {"in_left": p("left", PORT_OFFSET), "in_right": p("right", PORT_OFFSET), "out": p("bottom")}
    elif t == "try":
        n["ports"] = {"in": p("top"), "out_try": p("bottom"), "out_finally": p("bottom"), "out_handler": p("right", PORT_OFFSET)}
    elif t in ("except", "loop_exit"):
        n["ports"] = {"in": p("top"), "out": p("bottom")}
    else:
        n["ports"] = {"in": p("top"), "out": p("bottom")}


def _index_graph(graph):
    nodes = {n["id"]: dict(n) for n in graph["nodes"]}
    for n in nodes.values():
        _set_ports(n)
        n["level"]  = None
        n["branch"] = 0
        n["x"] = n["y"] = 0
    out_edges = defaultdict(list)
    in_edges  = defaultdict(list)
    for e in graph["edges"]:
        out_edges[e["from"]].append(e)
        in_edges[e["to"]].append(e)
    return nodes, out_edges, in_edges


def _find_entry_exits(nodes):
    entry = None
    exits = []
    for n in nodes.values():
        if n["type"] == "entry":
            entry = n
        if n["type"] == "exit":
            exits.append(n)
    return entry, exits


def _is_loop_back(e, nodes):
    lbl = _label(e)
    if any(k in lbl for k in ("continue", "loop back", "next iteration")):
        return True
    dst = nodes[e["to"]]
    src = nodes[e["from"]]
    # target loop header (common back-edge shape)
    if dst["type"] == "loop" and "done" not in lbl and "exit" not in lbl and src["id"] != dst["id"]:
        return True
    return False


def _is_break(e, nodes):
    return "break" in _label(e)


def _is_exception_edge(e, nodes):
    lbl = _label(e)
    a = nodes[e["from"]]["type"]
    b = nodes[e["to"]]["type"]
    if a in ("try", "except") or b in ("try", "except"):
        return True
    if any(k in lbl for k in ("except", "finally")):
        return True
    return False


def _is_return_edge(e, nodes):
    a = nodes[e["from"]]["type"]
    b = nodes[e["to"]]["type"]
    return a == "return" or b == "exit"


def _forward_edge_filter(edges, nodes):
    """Remove loop backs, breaks, returns, exceptions for DAG leveling."""
    fwd = []
    for e in edges:
        if _is_loop_back(e, nodes):         continue
        if _is_break(e, nodes):             continue
        if _is_exception_edge(e, nodes):    continue
        if _is_return_edge(e, nodes):       continue
        fwd.append(e)
    return fwd
# ------------------------------------------------


# --------------- Level Assignment ----------------
def _assign_levels_longest_path(nodes, edges, entry):
    """Longest-path layering on forward DAG."""
    if not entry:
        return
    fwd = _forward_edge_filter(edges, nodes)
    out = defaultdict(list)
    indeg = defaultdict(int)
    ids = list(nodes.keys())

    for e in fwd:
        u, v = e["from"], e["to"]
        out[u].append(v)
        indeg[v] += 1
    indeg[entry["id"]] = 0

    q = deque([nid for nid in ids if indeg.get(nid, 0) == 0])
    topo, seen = [], set()
    while q:
        nid = q.popleft()
        if nid in seen: continue
        seen.add(nid)
        topo.append(nid)
        for v in out.get(nid, []):
            indeg[v] -= 1
            if indeg[v] <= 0:
                q.append(v)
    for nid in ids:
        if nid not in seen:
            topo.append(nid)

    for n in nodes.values():
        n["level"] = float("-inf")
    nodes[entry["id"]]["level"] = 0

    for u in topo:
        lu = nodes[u]["level"]
        if lu == float("-inf"):
            lu = 0
            nodes[u]["level"] = 0
        for v in out.get(u, []):
            nodes[v]["level"] = max(nodes[v]["level"], lu + 1)

    used = sorted({n["level"] for n in nodes.values()})
    remap = {lv: i for i, lv in enumerate(used)}
    for n in nodes.values():
        n["level"] = remap[n["level"]]
# -------------------------------------------------


# --------------- Branch Lanes --------------------
def _assign_branches(nodes, out_edges):
    """True goes left, False right; loop bodies indented right."""
    def spread_from(cond_id, side):
        frontier = deque()
        seen = set()
        for e in out_edges.get(cond_id, []):
            lbl = _label(e)
            if side == "left"  and lbl.startswith("true"):  frontier.append(e["to"])
            if side == "right" and lbl.startswith("false"): frontier.append(e["to"])
        while frontier:
            nid = frontier.popleft()
            if nid in seen: continue
            seen.add(nid)
            nodes[nid]["branch"] += (-1 if side == "left" else 1)
            if nodes[nid]["type"] in ("merge", "loop"):  # stop at merge or nested loop header
                continue
            for e in out_edges.get(nid, []):
                if _is_loop_back(e, nodes): continue
                frontier.append(e["to"])

    for n in nodes.values():
        n["branch"] = n.get("branch", 0)

    for n in nodes.values():
        if n["type"] == "conditional":
            spread_from(n["id"], "left")
            spread_from(n["id"], "right")

    # indent loop bodies to the right
    for n in nodes.values():
        if n["type"] == "loop":
            body_targets = []
            for e in out_edges.get(n["id"], []):
                if _label(e).startswith(("iterate","true")) or _label(e) == "":
                    body_targets.append(e["to"])
            stack, seen = list(body_targets), set()
            while stack:
                nid = stack.pop()
                if nid in seen: continue
                seen.add(nid)
                nodes[nid]["branch"] = nodes[nid]["branch"] + 1
                if nodes[nid]["type"] in ("loop", "merge", "loop_exit"):
                    continue
                for e in out_edges.get(nid, []):
                    if _is_loop_back(e, nodes): continue
                    stack.append(e["to"])
# -------------------------------------------------


# ------------- Merge Alignment Map ---------------
def _merge_alignment(nodes, out_edges):
    """Map merge node id -> originating conditional id."""
    mapping = {}
    for cond in nodes.values():
        if cond["type"] != "conditional":
            continue
        visited = set()
        stack = [cond["id"]]
        while stack:
            nid = stack.pop()
            if nid in visited: continue
            visited.add(nid)
            for e in out_edges.get(nid, []):
                tgt = e["to"]
                tnode = nodes[tgt]
                if tnode["type"] == "merge":
                    mapping[tgt] = cond["id"]
                elif tnode["type"] not in ("conditional", "merge", "loop"):
                    stack.append(tgt)
    return mapping
# -------------------------------------------------


# ------------------ Placement --------------------
def _place(nodes, out_edges):
    by_level = defaultdict(list)
    for n in nodes.values():
        by_level[n["level"]].append(n)

    # Sort inside levels: branch lane first, then type/id for stability
    for lvl, arr in by_level.items():
        arr.sort(key=lambda n: (n["branch"], n["type"], n["id"]))

    # Initial lane-based x placement
    for lvl, arr in by_level.items():
        lanes = defaultdict(list)
        for n in arr:
            lanes[n["branch"]].append(n)
        for br, lane_nodes in lanes.items():
            for i, n in enumerate(lane_nodes):
                n["x"] = br * HORIZONTAL_GAP + i * (_w(n["type"]) + LANE_NODE_SPACER)

    # Align merge x to conditional x
    align = _merge_alignment(nodes, out_edges)
    for mid, cid in align.items():
        if cid in nodes and mid in nodes:
            nodes[mid]["x"] = nodes[cid]["x"]

    # y by level
    for n in nodes.values():
        n["y"] = n["level"] * VERTICAL_GAP

    # Compute gutter x positions (based on used lane span)
    if nodes:
        min_lane = min(n["branch"] for n in nodes.values())
        max_lane = max(n["branch"] for n in nodes.values())
        main_right = max_lane * HORIZONTAL_GAP + GUTTER_PAD
    else:
        main_right = GUTTER_PAD

    gutters = {
        "loop_back":  main_right + 1 * GUTTER_PAD,
        "break_bus":  main_right + 2 * GUTTER_PAD,
        "return_bus": main_right + 3 * GUTTER_PAD,
        "except_bus": min_lane * HORIZONTAL_GAP - 2 * GUTTER_PAD,  # left side
    }
    return gutters
# -------------------------------------------------


# ---------------- Edge Routing -------------------
def _choose_ports(edge, nodes):
    src = nodes[edge["from"]]
    dst = nodes[edge["to"]]
    lbl = _label(edge)
    from_port = edge.get("from_port")
    to_port   = edge.get("to_port")

    if src["type"] == "conditional":
        if lbl.startswith("true"):
            from_port = from_port or "true"
        elif lbl.startswith("false"):
            from_port = from_port or "false"
        else:
            from_port = from_port or "out"
    elif src["type"] == "loop":
        if lbl.startswith(("iterate","true")) or lbl == "":
            from_port = from_port or "out_body"
        elif any(k in lbl for k in ("done","false","complete","break")):
            from_port = from_port or "out_exit"
        else:
            from_port = from_port or "out_body"
    elif src["type"] == "try":
        if "finally" in lbl:
            from_port = from_port or "out_finally"
        else:
            from_port = from_port or "out_try"
    elif src["type"] == "return":
        from_port = from_port or "out"
    else:
        from_port = from_port or "out"

    if dst["type"] == "loop":
        if _is_loop_back(edge, nodes):
            to_port = to_port or "in_back"
        else:
            to_port = to_port or "in_entry"
    elif dst["type"] == "merge":
        to_port = to_port or ("in_left" if dst["x"] >= src["x"] else "in_right")
    else:
        to_port = to_port or "in"

    edge["from_port"] = from_port
    edge["to_port"]   = to_port


def _route_edges(edges, nodes, gutters):
    laid = []
    for e in edges:
        edge = dict(e)
        _choose_ports(edge, nodes)
        src = nodes[edge["from"]]
        dst = nodes[edge["to"]]

        # classify
        if _is_return_edge(edge, nodes):
            # route to return bus, then straight to exit bottom
            bus_x = gutters["return_bus"]
            mx = [{"x": max(src["x"], bus_x) + CURVE_PAD, "y": src["y"]}]
            my = [{"x": bus_x, "y": dst["y"] - CURVE_PAD}]
            edge["style"] = {"type": "orthogonal", "dashed": True}
            edge["control_points"] = mx + my
            laid.append(edge)
            continue

        if _is_loop_back(edge, nodes):
            bus_x = gutters["loop_back"]
            cp = [{"x": max(src["x"], dst["x"], bus_x), "y": (src["y"] + dst["y"]) / 2}]
            edge["style"] = {"type": "bezier", "curved": True, "dashed": True}
            edge["control_points"] = cp
            laid.append(edge)
            continue

        if _is_break(edge, nodes):
            bus_x = gutters["break_bus"]
            cp = [{"x": max(src["x"], bus_x), "y": src["y"] - CURVE_PAD}]
            edge["style"] = {"type": "bezier", "curved": True, "dashed": True}
            edge["control_points"] = cp
            laid.append(edge)
            continue

        if _is_exception_edge(edge, nodes):
            bus_x = gutters["except_bus"]
            cp = [{"x": min(src["x"], bus_x), "y": (src["y"] + dst["y"]) / 2}]
            edge["style"] = {"type": "bezier", "curved": True, "dashed": True}
            edge["control_points"] = cp
            laid.append(edge)
            continue

        # forward (default)
        if dst["y"] > src["y"]:
            edge["style"] = {"type": "straight"}
            edge["control_points"] = []
        else:
            # slight upward curve if any
            edge["style"] = {"type": "bezier", "curved": True}
            edge["control_points"] = [{"x": src["x"], "y": min(src["y"], dst["y"]) - CURVE_PAD * 0.5}]
        laid.append(edge)
    return laid
# -------------------------------------------------


# -------------------- API ------------------------
def compute_layout(graph: dict) -> dict:
    """
    Input:  graph with "nodes":[{id,type,label,...}], "edges":[{from,to,label?...}]
    Output: same graph augmented with:
        node.x, node.y, node.ports
        edge.from_port, edge.to_port, edge.style, edge.control_points
        layout.gutters for renderer reference
    """
    nodes, out_edges, in_edges = _index_graph(graph)
    entry, exits = _find_entry_exits(nodes)

    # 1) Levels reflect "how far into the function"
    _assign_levels_longest_path(nodes, graph["edges"], entry)

    # 2) Exit forced to bottom
    if nodes:
        deepest = max(n["level"] for n in nodes.values())
        for ex in exits:
            ex["level"] = deepest + 1

    # 3) Lanes + placement
    _assign_branches(nodes, out_edges)
    gutters = _place(nodes, out_edges)

    # 4) Route edges w/ gutters
    laid_edges = _route_edges(graph["edges"], nodes, gutters)

    return {
        **graph,
        "nodes": list(nodes.values()),
        "edges": laid_edges,
        "layout": {
            "vertical_gap": VERTICAL_GAP,
            "horizontal_gap": HORIZONTAL_GAP,
            "node_heights": NODE_HEIGHT,
            "node_widths": NODE_WIDTHS,
            "gutters": gutters,
        }
    }

