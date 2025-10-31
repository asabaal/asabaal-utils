#!/usr/bin/env python3
"""
Debug physics to find divergence issue
"""

from layout_relaxer import GraphLayout

def test_simple_spring():
    """Test simple two-node spring system"""
    G = GraphLayout()
    
    # Conservative parameters - much smaller repulsion
    G.k_spring = 0.1
    G.k_repel = 0.5  # MUCH SMALLER
    G.k_barrier = 10.0  # MUCH SMALLER
    G.L0 = 1.0
    G.step = 0.01
    G.damping = 0.9
    G.edge_radius = 0.3
    
    # Two nodes connected by spring
    G.add_node("a", "A", "box", "#ff0000", width=1.0, height=1.0, pos=(0.0, 0.0))
    G.add_node("b", "B", "box", "#0000ff", width=1.0, height=1.0, pos=(3.0, 0.0))
    G.add_edge("a", "b")
    
    print("Initial positions:")
    print(f"A: ({G.nodes['a'].x:.3f}, {G.nodes['a'].y:.3f})")
    print(f"B: ({G.nodes['b'].x:.3f}, {G.nodes['b'].y:.3f})")
    print(f"Distance: {((G.nodes['b'].x - G.nodes['a'].x)**2 + (G.nodes['b'].y - G.nodes['a'].y)**2)**0.5:.3f}")
    print(f"L0: {G.L0}")
    
    # Run a few iterations manually
    from layout_relaxer import _relax_iteration
    for i in range(10):
        _relax_iteration(G)
        
        if i % 2 == 0:
            d = ((G.nodes['b'].x - G.nodes['a'].x)**2 + (G.nodes['b'].y - G.nodes['a'].y)**2)**0.5
            # Debug spring force
            from layout_relaxer import _dist_dxdy, _effective_L0
            dd, dx, dy = _dist_dxdy(G.nodes['a'].x, G.nodes['a'].y, G.nodes['b'].x, G.nodes['b'].y)
            delta = dd - _effective_L0(G, G.nodes['a'], G.nodes['b'])
            spring_force = G.k_spring * delta
            fx = (dx / dd) * spring_force
            print(f"Iter {i}: d={dd:.3f}, delta={delta:.3f}, spring_force={spring_force:.3f}, fx={fx:.3f}")
            print(f"  A=({G.nodes['a'].x:.3f}, {G.nodes['a'].y:.3f}), B=({G.nodes['b'].x:.3f}, {G.nodes['b'].y:.3f})")

if __name__ == "__main__":
    test_simple_spring()