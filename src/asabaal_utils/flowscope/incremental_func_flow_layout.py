from itertools import combinations
from statistics import mean

class Node:
    def __init__(self, name):
        self.name = name
        self.x = 0
        self.y = 0

class Edge:
    def __init__(self, start, end):
        self.start = start
        self.end = end

class GraphLayout:
    def __init__(self):
        self.nodes = {}          # name -> Node
        self.edges = []          # list of Edge
        self.vertical_gap = 1.5  # vertical spacing
        self.horizontal_gap = 2  # horizontal spacing
        self.min_spacing = 1.0   # collision buffer
        self.grid_size = 0.5     # for final rounding
        self.adj = {}            # adjacency list

    # --- structural helpers ---
    def add_node(self, name, pos):
        node = Node(name)
        node.x, node.y = pos
        self.nodes[name] = node

    def add_edge(self, start, end):
        self.edges.append(Edge(start, end))
        self.adj.setdefault(start, []).append(end)
        self.adj.setdefault(end, [])

    def get_parents(self, node):
        return [s for s, e in [(edge.start, edge.end) for edge in self.edges] if e == node]

    def get_edges_near(self, node_name):
        return [e for e in self.edges if e.start == node_name or e.end == node_name]

# ---------------------------------------------------------------------

def layout_graph(function_ast):
    layout = GraphLayout()
    ordered_nodes = topological_order(function_ast)

    for node in ordered_nodes:
        add_node_to_layout(node, layout)
        fix_crossings(layout, node)

    smooth_edges(layout)
    align_to_grid(layout)
    return layout

# ---------------------------------------------------------------------

def add_node_to_layout(node, layout):
    parents = layout.get_parents(node)

    if not parents:
        pos = (0, 0)  # entry node
    else:
        avg_x = mean([layout.nodes[p].x for p in parents])
        max_y = max([layout.nodes[p].y for p in parents])
        pos = (avg_x, max_y + layout.vertical_gap)

    pos = avoid_overlap(pos, layout)
    layout.add_node(node, pos)

    for parent in parents:
        layout.add_edge(parent, node)

# ---------------------------------------------------------------------

def fix_crossings(layout, new_node):
    crossings = find_crossings(layout, new_node)
    for e1, e2 in crossings:
        if new_node in (e1.start, e1.end):
            shift_node(layout, new_node)
        else:
            shift_node(layout, e2.end)
        fix_crossings(layout, new_node)  # recursive cleanup

# ---------------------------------------------------------------------

def avoid_overlap(pos, layout):
    for node in layout.nodes.values():
        if distance((node.x, node.y), pos) < layout.min_spacing:
            pos = (pos[0] + layout.horizontal_gap, pos[1])
    return pos

def shift_node(layout, node_name, dx=None):
    dx = dx or layout.horizontal_gap
    layout.nodes[node_name].x += dx

def distance(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5

# ---------------------------------------------------------------------

def find_crossings(layout, node_name):
    """Check if any new edge from this node crosses others."""
    new_edges = layout.get_edges_near(node_name)
    crossings = []
    for e1, e2 in combinations(layout.edges, 2):
        if edges_cross(layout, e1, e2):
            crossings.append((e1, e2))
    return crossings

def edges_cross(layout, e1, e2):
    """Detect line segment intersection."""
    a1, a2 = layout.nodes[e1.start], layout.nodes[e1.end]
    b1, b2 = layout.nodes[e2.start], layout.nodes[e2.end]
    return segments_intersect((a1.x, a1.y), (a2.x, a2.y), (b1.x, b1.y), (b2.x, b2.y))

def segments_intersect(p1, p2, p3, p4):
    def ccw(a,b,c): return (c[1]-a[1])*(b[0]-a[0]) > (b[1]-a[1])*(c[0]-a[0])
    return ccw(p1,p3,p4) != ccw(p2,p3,p4) and ccw(p1,p2,p3) != ccw(p1,p2,p4)

# ---------------------------------------------------------------------

def smooth_edges(layout):
    # placeholder for optional curve smoothing later
    pass

def align_to_grid(layout):
    def round_to_grid(v, g): return round(v / g) * g
    for node in layout.nodes.values():
        node.x = round_to_grid(node.x, layout.grid_size)
        node.y = round_to_grid(node.y, layout.grid_size)

# ---------------------------------------------------------------------

def topological_order(function_ast):
    """
    For now, just simulate a sequential order of function statements.
    In practice, this will derive from the AST structure.
    """
    return [n for n in function_ast]

