# flowscope/layout_calculator.py
# Function-level layout engine for FlowScope
# Vertical position = "how far into the function"
# Merge nodes align with their originating conditionals
# Loop-backs exit on opposite side of loop nodes

from collections import defaultdict, deque

VERTICAL_GAP = 110
HORIZONTAL_GAP = 160
INDENT = 120
NODE_WIDTHS = {
    "entry": 140, "exit": 140, "return": 160,
    "conditional": 180, "loop": 200, "merge": 150,
    "assignment": 180, "statement": 180,
    "block_start": 140, "loop_exit": 140
}
NODE_HEIGHT = 60
PORT_OFFSET = 0.48
CURVE_PAD = 80


# -----------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------
def _node_size(ntype: str):
    return NODE_WIDTHS.get(ntype, 160), NODE_HEIGHT


def _edge_label(e):
    return (e.get("label") or "").strip().lower()


def _set_ports(n):
    ntype = n["type"]

    def side_pos(side):
        if side == "top":    return {"side": "top", "offset": 0.5}
        if side == "bottom": return {"side": "bottom", "offset": 0.5}
        if side == "left":   return {"side": "left", "offset": PORT_OFFSET}
        if side == "right":  return {"side": "right", "offset": PORT_OFFSET}
        return {"side": "bottom", "offset": 0.5}

    if ntype == "loop":
        n["ports"] = {
            "in_entry": side_pos("left"),
            "out_body": side_pos("bottom"),
            "in_back":  side_pos("right"),
            "out_exit": side_pos("bottom")
        }
    elif ntype == "conditional":
        n["ports"] = {
            "in":    side_pos("top"),
            "true":  side_pos("left"),
            "false": side_pos("right")
        }
    elif ntype == "merge":
        n["ports"] = {
            "in_left":  side_pos("left"),
            "in_right": side_pos("right"),
            "out":      side_pos("bottom")
        }
    else:
        n["ports"] = {"in": side_pos("top"), "out": side_pos("bottom")}


def _index_graph(graph):
    nodes = {n["id"]: dict(n) for n in graph["nodes"]}
    for n in nodes.values():
        _set_ports(n)
        n["level"] = None
        n["branch"] = 0
        n["x"] = n["y"] = 0
    out_edges = defaultdict(list)
    in_edges = defaultdict(list)
    for e in graph["edges"]:
        out_edges[e["from"]].append(e)
        in_edges[e["to"]].append(e)
    return nodes, out_edges, in_edges


def _find_entry_exit(nodes):
    entry = None
    exits = []
    for n in nodes.values():
        if n["type"] == "entry":
            entry = n
        if n["type"] == "exit":
            exits.append(n)
    return entry, exits


# -----------------------------------------------------------
# Loop detection and longest-path layering
# -----------------------------------------------------------
def _is_loop_edge(e, nodes):
    lbl = _edge_label(e)
    if any(k in lbl for k in ["continue", "next iteration", "loop back"]):
        return True
    dst = nodes[e["to"]]
    if dst["type"] == "loop" and "done" not in lbl and "exit" not in lbl:
        return True
    return False


def _assign_levels_longest_path(nodes, out_edges, entry):
    """
    Assign vertical levels based on the longest path from the entry node
    (loop-back edges are excluded). This reflects how far into the function
    each node occurs.
    """
    if not entry:
        return

    # Build forward DAG (ignore loop-backs)
    fwd_out = defaultdict(list)
    indeg = defaultdict(int)
    for u_id, edges in out_edges.items():
        for e in edges:
            if _is_loop_edge(e, nodes):
                continue
            v_id = e["to"]
            fwd_out[u_id].append(v_id)
            indeg[v_id] += 1

    # Initialize queue with nodes having indegree 0
    q = deque([entry["id"]])
    indeg[entry["id"]] = 0
    topo = []
    seen = set()
    while q:
        nid = q.popleft()
        if nid in seen:
            continue
        seen.add(nid)
        topo.append(nid)
        for v in fwd_out.get(nid, []):
            indeg[v] -= 1
            if indeg[v] <= 0:
                q.append(v)
    for nid in nodes:
        if nid not in seen:
            topo.append(nid)

    # Longest path levels
    for n in nodes.values():
        n["level"] = float("-inf")
    nodes[entry["id"]]["level"] = 0

    for u in topo:
        u_lvl = nodes[u]["level"]
        if u_lvl == float("-inf"):
            u_lvl = 0
            nodes[u]["level"] = 0
        for v in fwd_out.get(u, []):
            nodes[v]["level"] = max(nodes[v]["level"], u_lvl + 1)

    # Normalize
    used = sorted({n["level"] for n in nodes.values()})
    remap = {lv: i for i, lv in enumerate(used)}
    for n in nodes.values():
        n["level"] = remap[n["level"]]


# -----------------------------------------------------------
# Branches (horizontal lanes)
# -----------------------------------------------------------
def _assign_branches(nodes, out_edges):
    def spread_from(cond_id, side):
        frontier = deque()
        seen = set()
        for e in out_edges.get(cond_id, []):
            lbl = _edge_label(e)
            if side == "left" and lbl.startswith("true"):
                frontier.append(e["to"])
            if side == "right" and lbl.startswith("false"):
                frontier.append(e["to"])
        while frontier:
            nid = frontier.popleft()
            if nid in seen:
                continue
            seen.add(nid)
            nodes[nid]["branch"] += -1 if side == "left" else 1
            if nodes[nid]["type"] in ("merge", "loop"):
                continue
            for e in out_edges.get(nid, []):
                if _is_loop_edge(e, nodes):
                    continue
                frontier.append(e["to"])

    for n in nodes.values():
        if n["branch"] is None:
            n["branch"] = 0
    for n in nodes.values():
        if n["type"] == "conditional":
            spread_from(n["id"], "left")
            spread_from(n["id"], "right")

    # indent loop bodies
    for n in nodes.values():
        if n["type"] == "loop":
            body_targets = []
            for e in out_edges.get(n["id"], []):
                lbl = _edge_label(e)
                if lbl.startswith("iterate") or lbl.startswith("true") or lbl == "":
                    body_targets.append(e["to"])
            stack, seen = list(body_targets), set()
            while stack:
                nid = stack.pop()
                if nid in seen:
                    continue
                seen.add(nid)
                nodes[nid]["branch"] += 1
                if nodes[nid]["type"] in ("loop_exit", "merge", "loop"):
                    continue
                for e in out_edges.get(nid, []):
                    if _is_loop_edge(e, nodes):
                        continue
                    stack.append(e["to"])


# -----------------------------------------------------------
# Placement (x/y coordinates)
# -----------------------------------------------------------
def _place(nodes, out_edges):
    by_level = defaultdict(list)
    for n in nodes.values():
        by_level[n["level"]].append(n)

    # 1. Build merge->conditional alignment map
    merge_align = {}
    for cond in nodes.values():
        if cond["type"] == "conditional":
            visited = set()
            stack = [cond["id"]]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.add(nid)
                for e in out_edges.get(nid, []):
                    tgt = e["to"]
                    tgt_node = nodes[tgt]
                    if tgt_node["type"] == "merge":
                        merge_align[tgt] = cond["id"]
                    elif tgt_node["type"] not in ("conditional", "merge", "loop"):
                        stack.append(tgt)

    # 2. Sort nodes within each level
    for lvl, arr in by_level.items():
        arr.sort(key=lambda n: (n["branch"], n["type"], n["id"]))

    # 3. Assign x-coordinates by branch lanes
    for lvl, arr in by_level.items():
        lane_groups = defaultdict(list)
        for n in arr:
            lane_groups[n["branch"]].append(n)
        for branch, lane_nodes in lane_groups.items():
            for i, n in enumerate(lane_nodes):
                w, _ = _node_size(n["type"])
                n["x"] = branch * HORIZONTAL_GAP + i * (w + 24)

    # 4. Align merges with their originating conditionals
    for merge_id, cond_id in merge_align.items():
        if cond_id in nodes and merge_id in nodes:
            nodes[merge_id]["x"] = nodes[cond_id]["x"]

    # 5. Assign y by level
    for n in nodes.values():
        n["y"] = n["level"] * VERTICAL_GAP


# -----------------------------------------------------------
# Edge routing
# -----------------------------------------------------------
def _route_edge(e, nodes):
    src = nodes[e["from"]]
    dst = nodes[e["to"]]
    edge = dict(e)
    lbl = _edge_label(edge)

    # ports
    from_port = edge.get("from_port")
    to_port = edge.get("to_port")
    if src["type"] == "conditional":
        if lbl.startswith("true"):
            from_port = from_port or "true"
        elif lbl.startswith("false"):
            from_port = from_port or "false"
        else:
            from_port = from_port or "out"
    elif src["type"] == "loop":
        if lbl.startswith("iterate") or lbl.startswith("true") or lbl == "":
            from_port = from_port or "out_body"
        elif any(k in lbl for k in ["done", "false", "break", "complete"]):
            from_port = from_port or "out_exit"
        else:
            from_port = from_port or "out_body"
    else:
        from_port = from_port or "out"

    if dst["type"] == "loop":
        to_port = to_port or ("in_back" if _is_loop_edge(e, nodes) else "in_entry")
    elif dst["type"] == "merge":
        to_port = to_port or ("in_left" if dst["x"] >= src["x"] else "in_right")
    else:
        to_port = to_port or "in"

    edge["from_port"] = from_port
    edge["to_port"] = to_port

    # path style
    if _is_loop_edge(e, nodes):
        edge["style"] = {"type": "bezier", "curved": True, "dashed": True}
        ctrl_x = max(src["x"], dst["x"]) + CURVE_PAD
        ctrl_y = (src["y"] + dst["y"]) / 2 - CURVE_PAD * 0.25
        edge["control_points"] = [{"x": ctrl_x, "y": ctrl_y}]
    else:
        if dst["y"] <= src["y"]:
            edge["style"] = {"type": "bezier", "curved": True}
            ctrl_x = src["x"]
            ctrl_y = min(src["y"], dst["y"]) - CURVE_PAD * 0.5
            edge["control_points"] = [{"x": ctrl_x, "y": ctrl_y}]
        else:
            edge["style"] = {"type": "straight"}

    return edge


# -----------------------------------------------------------
# Public API
# -----------------------------------------------------------
def compute_layout(graph: dict) -> dict:
    """
    Compute layout for a function-flow graph:
    - Vertical position = how far into the function (longest-path)
    - Exit forced to bottom
    - Merge nodes aligned with originating conditionals
    - Loop-backs flow out opposite side
    """
    nodes, out_edges, in_edges = _index_graph(graph)
    entry, exits = _find_entry_exit(nodes)

    _assign_levels_longest_path(nodes, out_edges, entry)

    # Force exit nodes to bottom
    max_level = max(n["level"] for n in nodes.values()) if nodes else 0
    for ex in exits:
        ex["level"] = max_level + 1

    _assign_branches(nodes, out_edges)
    _place(nodes, out_edges)

    laid_nodes = list(nodes.values())
    laid_edges = [_route_edge(e, nodes) for e in graph["edges"]]

    return {
        **graph,
        "nodes": laid_nodes,
        "edges": laid_edges,
        "layout": {
            "vertical_gap": VERTICAL_GAP,
            "horizontal_gap": HORIZONTAL_GAP,
            "indent": INDENT,
            "node_heights": NODE_HEIGHT,
            "node_widths": NODE_WIDTHS
        }
    }

