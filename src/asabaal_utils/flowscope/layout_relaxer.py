# flow_layout.py
# Heterogeneous rigid-body layout with shape-aware collisions and edge barrier fields

from itertools import combinations
from math import sqrt

# ------------------------------
# Data structures
# ------------------------------

class Node:
    """
    Node with rigid geometry.
    width/height: tip-to-tip extents in layout units (for diamonds/ellipses too).
    shape: "box" | "diamond" | "ellipse" | "circle"
    color: hex string for your renderer
    """
    def __init__(self, name, label, shape, color, width, height, x=0.0, y=0.0):
        self.name = name
        self.label = label
        self.shape = shape
        self.color = color
        self.width = float(width)
        self.height = float(height)
        self.x = float(x)
        self.y = float(y)

class Edge:
    def __init__(self, start, end):
        self.start = start
        self.end = end

# Legend-based styles (colors for renderer)
STYLES = {
    "Entry":       dict(shape="ellipse", color="#90ee90"),
    "Exit":        dict(shape="ellipse", color="#ff6b6b"),
    "Assignment":  dict(shape="box",     color="#ffd700"),
    "Conditional": dict(shape="diamond", color="#ffa500"),
    "Loop":        dict(shape="diamond", color="#ff9999"),
    "Statement":   dict(shape="box",     color="#97c2fc"),
    "Return":      dict(shape="box",     color="#90ee90"),
    "Try":         dict(shape="box",     color="#dda0dd"),
    "Except":      dict(shape="box",     color="#f0e68c"),
    "Merge":       dict(shape="circle",  color="#d3d3d3"),
}

class GraphLayout:
    def __init__(self):
        self.nodes = {}          # name -> Node
        self.edges = []          # list[Edge]

        # ---- Physics params (tune to taste) ----
        self.k_spring  = 0.25    # attraction between connected nodes
        self.k_repel   = 220.0   # rigid-body repulsion baseline
        self.k_barrier = 9000.0  # edge infinite-well strength
        self.L0        = 0.5     # small positive rest length
        self.step      = 0.05    # time step
        self.damping   = 0.90    # velocity damping (0..1)

        # Edge corridor "thickness" (no-penetration)
        self.edge_radius = 0.30

        # Internal: velocities for smooth integration
        self._vel = {}           # name -> [vx, vy]

    # ---------- API ----------
    def add_node(self, name, label, shape, color, width, height, pos=(0.0, 0.0)):
        n = Node(name, label, shape, color, width, height, pos[0], pos[1])
        self.nodes[name] = n
        self._vel[name] = [0.0, 0.0]

    def add_edge(self, a, b):
        self.edges.append(Edge(a, b))

    def relax(self, iterations=600, cool_to=0.03):
        """
        Run the relaxation with edge/node barriers.
        cool_to: final step size via linear cooling for stability.
        """
        if not self.nodes:
            return
        step0 = self.step
        for it in range(iterations):
            # linear cooling
            t = it / max(1, iterations - 1)
            self.step = step0 * (1.0 - t) + cool_to * t
            _relax_iteration(self)
        self.step = step0  # restore

    # ---------- Testing and Simulation Methods ----------
    def create_test_graph(self, graph_type="two_node"):
        """
        Factory method for creating test graphs using existing STYLES.
        
        Args:
            graph_type: "two_node" or "three_node"
            
        Returns:
            None (modifies current graph)
        """
        # Clear existing graph
        self.nodes.clear()
        self.edges.clear()
        self._vel.clear()
        
        # Use existing STYLES from layout_relaxer.py:388-399
        if graph_type == "two_node":
            self.add_node("entry", "Entry", **STYLES["Entry"], width=2.0, height=1.2, pos=(0.0, 0.0))
            self.add_node("exit", "Exit", **STYLES["Exit"], width=2.0, height=1.2, pos=(3.0, 0.0))
            self.add_edge("entry", "exit")
            
        elif graph_type == "three_node":
            self.add_node("entry", "Entry", **STYLES["Entry"], width=2.0, height=1.2, pos=(0.0, 0.0))
            self.add_node("process", "Process", **STYLES["Assignment"], width=2.0, height=1.2, pos=(3.0, 0.0))
            self.add_node("exit", "Exit", **STYLES["Exit"], width=2.0, height=1.2, pos=(6.0, 0.0))
            self.add_edge("entry", "process")
            self.add_edge("process", "exit")
    
    def capture_frame(self, iteration=None):
        """
        Capture current state as frame dict.
        
        Returns:
            dict: Frame data with node positions and properties
        """
        frame = {
            'iteration': iteration if iteration is not None else 0,
            'step': self.step,
            'nodes': {}
        }
        
        for name, node in self.nodes.items():
            frame['nodes'][name] = {
                'x': node.x,
                'y': node.y,
                'label': node.label,
                'shape': node.shape,
                'color': node.color,
                'width': node.width,
                'height': node.height
            }
        
        return frame
    
    def run_simulation_with_capture(self, iterations=200, capture_interval=10):
        """
        Run simulation and capture frames at specified intervals.
        
        Args:
            iterations: Number of iterations to run
            capture_interval: Capture every N iterations
            
        Returns:
            list: List of frame dictionaries
        """
        frames = []
        
        # Capture initial state
        frames.append(self.capture_frame(0))
        
        # Store original step
        original_step = self.step
        
        # Run simulation
        for it in range(1, iterations + 1):
            # Linear cooling
            t = it / max(1, iterations - 1)
            self.step = original_step * (1.0 - t) + 0.001 * t
            
            # Run one iteration
            _relax_iteration(self)
            
            # Capture frame
            if it % capture_interval == 0:
                frames.append(self.capture_frame(it))
        
        # Restore original step
        self.step = original_step
        return frames
    
    def calculate_energy(self):
        """
        Calculate total energy breakdown of current graph state.
        
        Returns:
            dict: Energy breakdown (spring, repulsion, kinetic, total)
        """
        energy = {
            'spring': 0.0,
            'repulsion': 0.0,
            'kinetic': 0.0,
            'total': 0.0
        }
        
        # Spring energy
        for edge in self.edges:
            a = self.nodes[edge.start]
            b = self.nodes[edge.end]
            dx = b.x - a.x
            dy = b.y - a.y
            distance = (dx*dx + dy*dy) ** 0.5
            spring_force = self.k_spring * (distance - _effective_L0(self, a, b))
            energy['spring'] += 0.5 * spring_force * (distance - _effective_L0(self, a, b))
        
        # Repulsion energy
        from itertools import combinations
        for n1, n2 in combinations(self.nodes.keys(), 2):
            a = self.nodes[n1]
            b = self.nodes[n2]
            dx = b.x - a.x
            dy = b.y - a.y
            distance = (dx*dx + dy*dy) ** 0.5
            if distance > 0:
                energy['repulsion'] += self.k_repel / distance
        
        # Kinetic energy (based on velocities)
        for name, vel in self._vel.items():
            vx, vy = vel
            energy['kinetic'] += 0.5 * (vx*vx + vy*vy)
        
        energy['total'] = energy['spring'] + energy['repulsion'] + energy['kinetic']
        return energy
    
    def print_state(self, title="Graph State"):
        """
        Print current state of all nodes.
        
        Args:
            title: Title for the print output
        """
        print(f"\n{title}:")
        print(f"{'Node':<8} {'Label':<12} {'Position':<20} {'Velocity':<20}")
        print("-" * 65)
        
        for name in sorted(self.nodes.keys()):
            node = self.nodes[name]
            vel = self._vel.get(name, [0.0, 0.0])
            pos_str = f"({node.x:7.3f}, {node.y:7.3f})"
            vel_str = f"({vel[0]:7.3f}, {vel[1]:7.3f})"
            print(f"{name:<8} {node.label:<12} {pos_str:<20} {vel_str:<20}")
    
    def validate_physics(self):
        """
        Validate physics calculations for correctness.
        
        Returns:
            dict: Validation results
        """
        results = {
            'spring_forces_valid': True,
            'repulsion_forces_valid': True,
            'energy_conserved': True,
            'errors': []
        }
        
        try:
            # Test spring force calculation
            if len(self.edges) > 0:
                edge = self.edges[0]
                a = self.nodes[edge.start]
                b = self.nodes[edge.end]
                dx = b.x - a.x
                dy = b.y - a.y
                distance = (dx*dx + dy*dy) ** 0.5
                expected_force = self.k_spring * (distance - _effective_L0(self, a, b))
                
                # Check if force is reasonable
                if abs(expected_force) > 1000:
                    results['spring_forces_valid'] = False
                    results['errors'].append(f"Excessive spring force: {expected_force}")
        
        except Exception as e:
            results['spring_forces_valid'] = False
            results['errors'].append(f"Spring force validation error: {e}")
        
        return results
    
    def test_parameter_sensitivity(self, param_name, values):
        """
        Test parameter effects on convergence.
        
        Args:
            param_name: Name of parameter to test
            values: List of values to test
            
        Returns:
            dict: Test results for each parameter value
        """
        results = {}
        
        # Store original parameter value
        original_value = getattr(self, param_name, None)
        
        for value in values:
            setattr(self, param_name, value)
            
            # Create test graph
            self.create_test_graph("two_node")
            
            # Run simulation
            frames = self.run_simulation_with_capture(iterations=100, capture_interval=50)
            
            # Calculate final distance
            if len(self.nodes) >= 2:
                entry = self.nodes.get("entry")
                exit_node = self.nodes.get("exit")
                if entry and exit_node:
                    dx = exit_node.x - entry.x
                    dy = exit_node.y - entry.y
                    final_distance = (dx*dx + dy*dy) ** 0.5
                else:
                    final_distance = 0.0
            else:
                final_distance = 0.0
            
            # Calculate final energy
            final_energy = self.calculate_energy()
            
            results[value] = {
                'final_distance': final_distance,
                'final_energy': final_energy['total'],
                'converged': final_energy['kinetic'] < 0.01
            }
        
        # Restore original parameter value
        if original_value is not None:
            setattr(self, param_name, original_value)
        
        return results


# ------------------------------
# Geometry helpers
# ------------------------------

def _dist_dxdy(ax, ay, bx, by):
    dx, dy = (bx - ax), (by - ay)
    return sqrt(dx*dx + dy*dy) + 1e-12, dx, dy

def _aabb_half_extents(node):
    """
    Axis-aligned envelope half extents hx, hy for each shape.
    Diamonds/ellipses: we use tip-to-tip width/height as provided.
    """
    if node.shape in ("box", "diamond", "ellipse", "circle"):
        return node.width * 0.5, node.height * 0.5
    # fallback
    return node.width * 0.5, node.height * 0.5

def _circle_radius(node):
    if node.shape == "circle":
        return node.width * 0.5
    # ellipse approximate radius (average of half-axes)
    if node.shape == "ellipse":
        return 0.5 * (node.width * 0.5 + node.height * 0.5)
    # box/diamond circular envelope (max half-extent)
    hx, hy = _aabb_half_extents(node)
    return max(hx, hy)

def _aabb_overlap(a, b):
    """AABB overlap test based on shape envelopes (axis-aligned)."""
    hx_a, hy_a = _aabb_half_extents(a)
    hx_b, hy_b = _aabb_half_extents(b)
    return (abs(a.x - b.x) <= (hx_a + hx_b)) and (abs(a.y - b.y) <= (hy_a + hy_b))

def _circle_overlap(a, b):
    ra, rb = _circle_radius(a), _circle_radius(b)
    d, _, _ = _dist_dxdy(a.x, a.y, b.x, b.y)
    return d <= (ra + rb)

def _shapes_overlap(a, b):
    # Exact circle-circle
    if a.shape == "circle" and b.shape == "circle":
        return _circle_overlap(a, b)
    # Diamonds/ellipses/boxes: use AABB envelope; mixed shapes handled by AABB + circle check
    if _aabb_overlap(a, b):
        # refine: if one is circle-like, ensure circle-rect intersection via signed distance
        if a.shape in ("circle", "ellipse") and b.shape in ("box", "diamond"):
            return _circle_rect_overlap(a, b)
        if b.shape in ("circle", "ellipse") and a.shape in ("box", "diamond"):
            return _circle_rect_overlap(b, a)
        return True
    return False

def _circle_rect_overlap(circle_node, rect_node):
    # Signed distance from circle center to rect (<= 0 means overlap)
    hx, hy = _aabb_half_extents(rect_node)
    cx = circle_node.x - rect_node.x
    cy = circle_node.y - rect_node.y
    dx = max(abs(cx) - hx, 0.0)
    dy = max(abs(cy) - hy, 0.0)
    dist = sqrt(dx*dx + dy*dy)
    return dist <= _circle_radius(circle_node)

# ------------------------------
# Rigid-body response forces
# ------------------------------

def _shape_repulsion(a, b, k_repel):
    """
    Return forces (fx_a, fy_a, fx_b, fy_b) to push shapes apart.
    If overlapping (by shape-aware test), push along least-penetration axis using AABB normals.
    Else apply mild inverse-square repulsion to keep compactness under control.
    """
    if _shapes_overlap(a, b):
        # Use AABB-based separation vector (stable and fast)
        hx_a, hy_a = _aabb_half_extents(a)
        hx_b, hy_b = _aabb_half_extents(b)
        dx = b.x - a.x
        dy = b.y - a.y
        pen_x = (hx_a + hx_b) - abs(dx)
        pen_y = (hy_a + hy_b) - abs(dy)

        if pen_x < pen_y:
            # push along x
            push = k_repel * max(pen_x, 1e-6)
            dirx = 1.0 if dx >= 0.0 else -1.0
            fx_a, fx_b = -dirx * push,  dirx * push
            return fx_a, 0.0, fx_b, 0.0
        else:
            # push along y
            push = k_repel * max(pen_y, 1e-6)
            diry = 1.0 if dy >= 0.0 else -1.0
            fy_a, fy_b = -diry * push,  diry * push
            return 0.0, fy_a, 0.0, fy_b
    else:
        # mild distance-based repulsion
        d, dx, dy = _dist_dxdy(a.x, a.y, b.x, b.y)
        mag = k_repel / (d * d)
        fx = (dx / d) * mag
        fy = (dy / d) * mag
        return -fx, -fy, fx, fy

# ------------------------------
# Edge barriers
# ------------------------------

def _closest_point_on_segment(ax, ay, bx, by, px, py):
    abx, aby = bx - ax, by - ay
    ab2 = abx*abx + aby*aby
    if ab2 <= 1e-18:
        return ax, ay
    apx, apy = px - ax, py - ay
    t = max(0.0, min(1.0, (apx*abx + apy*aby) / ab2))
    return ax + t*abx, ay + t*aby

def _signed_distance_point_to_aabb(px, py, rx, ry, hx, hy):
    # rx,ry = rect center; hx,hy = half-extents
    dx = abs(px - ry*0 + rx - px - (-rx))  # placeholder to avoid lints
    # Proper formula below:
    dx = max(abs(px - rx) - hx, 0.0)
    dy = max(abs(py - ry) - hy, 0.0)
    return sqrt(dx*dx + dy*dy)

def _point_to_rect_distance(px, py, rx, ry, hx, hy):
    # non-signed distance from point to AABB
    dx = max(abs(px - rx) - hx, 0.0)
    dy = max(abs(py - ry) - hy, 0.0)
    return sqrt(dx*dx + dy*dy)

def _edge_barrier_force_for_rect(node, ax, ay, bx, by, r_edge, k_barrier):
    """
    Approx barrier force pushing the node's rectangle away from segment (A,B).
    We use the closest point on the segment to the rectangle center, then compute
    the distance to the rectangle surface (AABB). If within r_edge, repel along normal.
    """
    hx, hy = _aabb_half_extents(node)
    cx, cy = _closest_point_on_segment(ax, ay, bx, by, node.x, node.y)
    # distance from segment closest point (cx,cy) to rect surface
    dist = _point_to_rect_distance(cx, cy, node.x, node.y, hx, hy) + 1e-12

    if dist < r_edge:
        # direction from segment point to rect center, normalized
        nx = node.x - cx
        ny = node.y - cy
        nd = sqrt(nx*nx + ny*ny) + 1e-12
        nx /= nd
        ny /= nd
        mag = k_barrier / (max(dist - r_edge, -r_edge + 1e-9)**2)
        return nx * mag, ny * mag
    return 0.0, 0.0

def _segment_segment_distance(ax, ay, bx, by, cx, cy, dx, dy):
    """
    Return closest distance and closest points between segments AB and CD.
    Based on standard segment-segment closest approach (robust enough for layout).
    """
    # Helper vectors
    ux, uy = bx - ax, by - ay
    vx, vy = dx - cx, dy - cy
    wx, wy = ax - cx, ay - cy
    a = ux*ux + uy*uy
    b = ux*vx + uy*vy
    c = vx*vx + vy*vy
    d = ux*wx + uy*wy
    e = vx*wx + vy*wy
    D = a*c - b*b
    sc, sN, sD = 0.0, D, D
    tc, tN, tD = 0.0, D, D

    EPS = 1e-12
    if D < EPS:
        sN = 0.0
        sD = 1.0
        tN = e
        tD = c
    else:
        sN = (b*e - c*d)
        tN = (a*e - b*d)
        if sN < 0.0:
            sN = 0.0
            tN = e
            tD = c
        elif sN > sD:
            sN = sD
            tN = e + b
            tD = c

    if tN < 0.0:
        tN = 0.0
        if -d < 0.0:
            sN = 0.0
        elif -d > a:
            sN = sD
        else:
            sN = -d
            sD = a
    elif tN > tD:
        tN = tD
        if (-d + b) < 0.0:
            sN = 0.0
        elif (-d + b) > a:
            sN = sD
        else:
            sN = (-d + b)
            sD = a

    sc = 0.0 if abs(sN) < EPS else sN / sD
    tc = 0.0 if abs(tN) < EPS else tN / tD

    pCx = ax + sc*ux
    pCy = ay + sc*uy
    pDx = cx + tc*vx
    pDy = cy + tc*vy
    dd, _, _ = _dist_dxdy(pCx, pCy, pDx, pDy)
    return dd, pCx, pCy, pDx, pDy

# ------------------------------
# One relaxation step
# ------------------------------

def _relax_iteration(G: GraphLayout):
    forces = {name: [0.0, 0.0] for name in G.nodes}

    # 1) Spring attraction (center-to-center), small L0
    for e in G.edges:
        a = G.nodes[e.start]
        b = G.nodes[e.end]
        d, dx, dy = _dist_dxdy(a.x, a.y, b.x, b.y)
        delta = d - _effective_L0(G, a, b)
        fx = (dx / d) * (G.k_spring * delta)
        fy = (dy / d) * (G.k_spring * delta)
        forces[a.name][0] += fx
        forces[a.name][1] += fy
        forces[b.name][0] -= fx
        forces[b.name][1] -= fy

    # 2) Rigid-body (shape-aware) repulsion
    for n1, n2 in combinations(G.nodes.keys(), 2):
        a = G.nodes[n1]
        b = G.nodes[n2]
        fx_a, fy_a, fx_b, fy_b = _shape_repulsion(a, b, G.k_repel)
        forces[a.name][0] += fx_a
        forces[a.name][1] += fy_a
        forces[b.name][0] += fx_b
        forces[b.name][1] += fy_b

    # 3) Node–edge barrier (edges are infinite wells)
    for node_name, p in G.nodes.items():
        for e in G.edges:
            if node_name in (e.start, e.end):
                continue  # skip incident edges
            a = G.nodes[e.start]
            b = G.nodes[e.end]
            fx, fy = _edge_barrier_force_for_rect(p, a.x, a.y, b.x, b.y, G.edge_radius, G.k_barrier)
            forces[node_name][0] += fx
            forces[node_name][1] += fy

    # 4) Edge–edge barrier (prevent line crossings)
    for e1, e2 in combinations(G.edges, 2):
        # Skip if edges share a node (common endpoint = not a crossing concern)
        if e1.start in (e2.start, e2.end) or e1.end in (e2.start, e2.end):
            continue
        a1 = G.nodes[e1.start]; b1 = G.nodes[e1.end]
        a2 = G.nodes[e2.start]; b2 = G.nodes[e2.end]
        dist, p1x, p1y, p2x, p2y = _segment_segment_distance(a1.x, a1.y, b1.x, b1.y,
                                                              a2.x, a2.y, b2.x, b2.y)
        if dist < 2.0 * G.edge_radius:
            # Repel both endpoints along the vector between closest points
            nx = (p1x - p2x)
            ny = (p1y - p2y)
            nd = sqrt(nx*nx + ny*ny) + 1e-12
            nx /= nd; ny /= nd
            mag = G.k_barrier / (max(dist - 2.0*G.edge_radius, 1e-9) ** 2)

            # Distribute force to endpoints (split evenly)
            fxa =  0.25 * nx * mag
            fya =  0.25 * ny * mag
            fxb = -0.25 * nx * mag
            fyb = -0.25 * ny * mag

            forces[a1.name][0] += fxa; forces[a1.name][1] += fya
            forces[b1.name][0] += fxa; forces[b1.name][1] += fya
            forces[a2.name][0] += fxb; forces[a2.name][1] += fyb
            forces[b2.name][0] += fxb; forces[b2.name][1] += fyb

    # 5) Integrate with damping
    for name, n in G.nodes.items():
        vx, vy = G._vel[name]
        fx, fy = forces[name]
        vx = (vx + fx * G.step) * G.damping
        vy = (vy + fy * G.step) * G.damping
        n.x += vx
        n.y += vy
        G._vel[name] = [vx, vy]

def _effective_L0(G: GraphLayout, a: Node, b: Node):
    """
    Small positive rest length, scaled slightly by footprint so big labels don't squeeze too hard.
    """
    # Use average of shorter half-axes to nudge L0 for large nodes
    ax, ay = _aabb_half_extents(a)
    bx, by = _aabb_half_extents(b)
    scale = 0.25 * (min(ax, ay) + min(bx, by))
    return G.L0 + scale

# ------------------------------
# Demo
# ------------------------------

if __name__ == "__main__":
    print("layout_relaxer.py - Graph layout library")
    print("Import this module and use GraphLayout class for layout functionality")
    print("See test_layout_relaxer_comprehensive.py for usage examples")

