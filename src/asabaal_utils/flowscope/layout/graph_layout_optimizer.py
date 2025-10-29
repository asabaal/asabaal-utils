"""
graph_layout_optimizer.py
------------------------------------
Plug-and-play layout optimizer for functional flow graphs.

Designed for small to mid-sized codebase graphs (≈ up to a few hundred nodes).
Performs:
1. Chain contraction (optional)
2. Base layout (or accepts existing node positions)
3. Simulated annealing refinement to reduce crossings
4. Chain expansion and return of optimized coordinates

Usage (single call):

    from graph_layout_optimizer import optimize_graph_layout

    new_pos = optimize_graph_layout(G, initial_pos=my_existing_pos)

Your visualizer can then use `new_pos` as the default layout.

Dependencies: networkx, matplotlib, numpy
"""

import math
import random
import networkx as nx
import numpy as np


# ------------------------------------------------------------
# 1. Chain Contraction / Expansion
# ------------------------------------------------------------

def contract_chains(G):
    """Collapse linear 1-in-1-out nodes into meta-edges."""
    H = G.copy()
    chains = []
    for n in list(H.nodes()):
        if n not in H:
            continue
        preds = list(H.predecessors(n)) if H.is_directed() else list(H.neighbors(n))
        succs = list(H.successors(n)) if H.is_directed() else list(H.neighbors(n))
        if len(preds) == 1 and len(succs) == 1 and preds[0] != succs[0]:
            p, s = preds[0], succs[0]
            if not H.has_edge(p, s):
                H.add_edge(p, s)
            H.remove_node(n)
            chains.append((p, n, s))
    return H, chains


def expand_chains(pos, chains):
    """Reinsert previously collapsed nodes midway between their endpoints."""
    for (p, n, s) in chains:
        if p in pos and s in pos:
            x1, y1 = pos[p]
            x2, y2 = pos[s]
            pos[n] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return pos


# ------------------------------------------------------------
# 2. Base Layout
# ------------------------------------------------------------

def base_layout(G, seed=42, iterations=200):
    """Force-directed initial layout (spring)."""
    return nx.spring_layout(G, seed=seed, iterations=iterations, dim=2)


# ------------------------------------------------------------
# 3. Crossing Counting Utilities
# ------------------------------------------------------------

def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segments_cross(p1, p2, p3, p4):
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)


def count_crossings(pos, edges):
    """Naive O(E²) crossing counter (fine for ≤ few hundred edges)."""
    crossings = 0
    edge_list = list(edges)
    for i in range(len(edge_list)):
        (a, b) = edge_list[i]
        for j in range(i + 1, len(edge_list)):
            (c, d) = edge_list[j]
            if len({a, b, c, d}) < 4:
                continue
            if segments_cross(pos[a], pos[b], pos[c], pos[d]):
                crossings += 1
    return crossings


# ------------------------------------------------------------
# 4. Simulated Annealing Refinement
# ------------------------------------------------------------

def anneal_layout(G, pos, steps=2000, temp_start=1.0, temp_end=0.001):
    """Refine layout via simulated annealing to minimize edge crossings."""
    edges = list(G.edges())
    best_pos = dict(pos)
    best_cost = count_crossings(best_pos, edges)
    current_pos = dict(pos)
    current_cost = best_cost

    for step in range(steps):
        temp = temp_start * (temp_end / temp_start) ** (step / steps)
        node = random.choice(list(G.nodes()))
        x, y = current_pos[node]
        dx, dy = (random.random() - 0.5) * temp, (random.random() - 0.5) * temp
        new_pos = dict(current_pos)
        new_pos[node] = (x + dx, y + dy)
        new_cost = count_crossings(new_pos, edges)
        delta = new_cost - current_cost

        if delta < 0 or math.exp(-delta / max(temp, 1e-9)) > random.random():
            current_pos, current_cost = new_pos, new_cost
            if new_cost < best_cost:
                best_pos, best_cost = new_pos, new_cost

    return best_pos


# ------------------------------------------------------------
# 5. Main Entry Point
# ------------------------------------------------------------

def optimize_graph_layout(
    G,
    initial_pos=None,
    contract=True,
    anneal_steps=2000,
    seed=42,
    return_crossings=False,
):
    """
    Perform full layout optimization.

    Args:
        G: networkx.Graph or DiGraph
        initial_pos: optional {node: (x, y)} dict. If None, use spring layout.
        contract: bool — collapse and re-expand linear chains.
        anneal_steps: int — number of annealing iterations.
        seed: int — reproducibility seed.
        return_crossings: bool — also return crossing count.

    Returns:
        pos: {node: (x, y)} optimized coordinates
        (optional) crossing_count
    """
    # 1. Contract
    if contract:
        G_reduced, chains = contract_chains(G)
    else:
        G_reduced, chains = G, []

    # 2. Base layout
    pos0 = dict(initial_pos) if initial_pos else base_layout(G_reduced, seed=seed)

    # 3. Anneal
    pos_opt = anneal_layout(G_reduced, pos0, steps=anneal_steps)

    # 4. Expand
    final_pos = expand_chains(pos_opt, chains)

    if return_crossings:
        cost = count_crossings(final_pos, list(G.edges()))
        return final_pos, cost
    return final_pos


# ------------------------------------------------------------
# 6. Simple Visualization Helper (optional)
# ------------------------------------------------------------

def quick_plot(G, pos, figsize=(10, 8), node_size=30, **kwargs):
    import matplotlib.pyplot as plt
    plt.figure(figsize=figsize)
    nx.draw(G, pos, node_size=node_size, width=0.4, with_labels=False, **kwargs)
    plt.show()


# ------------------------------------------------------------
# 7. CLI Example (safe for coding-agent tests)
# ------------------------------------------------------------

if __name__ == "__main__":
    print("Creating example graph...")
    G = nx.gn_graph(40, seed=1, create_using=nx.DiGraph)
    pos, cost = optimize_graph_layout(G, return_crossings=True)
    print(f"Final crossings: {cost}")
    quick_plot(G, pos)

