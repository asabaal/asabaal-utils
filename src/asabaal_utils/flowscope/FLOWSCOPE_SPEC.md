# FlowScope — Function-Level Code Flow and Drift Analysis Tool

## 🎯 Purpose

FlowScope is a **standalone subsystem** that analyzes Python codebases to generate and compare **function-level call graphs**.  
Its goals are to:
1. Map how code flows between functions and modules.
2. Track how that flow changes over time (code drift).
3. Provide static and dynamic visualizations to assist with debugging and educational understanding.

Although FlowScope can live anywhere, in your setup it will reside **inside your existing repository** (e.g. under `src/asabaal_utils/agents/flowscope/`).  
It will operate independently — it does **not** depend on SpecCoder or any other package code.

---

## 🧩 System Overview

**Core modules:**
```
flowscope/
├── __init__.py
├── scanner.py          # AST parsing & static call extraction
├── graph.py            # Graph assembly & utilities
├── snapshot.py         # Save/load graph snapshots
├── drift.py            # Compare graph versions
├── visualize.py        # Static + interactive graph output
└── cli.py              # Command-line interface
```

**Key data structures:**
- `nx.DiGraph`: Directed graph representing function-level flow.
- JSON snapshots: persistent versions of graphs for later comparison.

---

## ⚙️ Functional Specification

### 1. Static Scanner (`scanner.py`)
Parses `.py` files and extracts function-level relationships.

```python
import ast
from pathlib import Path
import networkx as nx

def scan_directory(path: Path) -> nx.DiGraph:
    """Scan directory recursively and build call graph."""
    graph = nx.DiGraph()
    for file in path.rglob("*.py"):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        current_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = f"{file.stem}.{node.name}"
                graph.add_node(func_name, file=str(file))
                current_func = func_name
            elif isinstance(node, ast.Call) and current_func:
                if isinstance(node.func, ast.Name):
                    called = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    called = node.func.attr
                else:
                    called = "unknown"
                graph.add_edge(current_func, called)
    return graph
```

---

### 2. Snapshot System (`snapshot.py`)
Handles graph saving and loading.

```python
import json

def save_graph(graph, path):
    data = {"nodes": list(graph.nodes), "edges": list(graph.edges)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_graph(path):
    import networkx as nx
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    g = nx.DiGraph()
    g.add_nodes_from(data["nodes"])
    g.add_edges_from([tuple(e) for e in data["edges"]])
    return g
```

---

### 3. Drift Analyzer (`drift.py`)
Compares two graph snapshots and reports differences.

```python
def compare_graphs(old, new):
    added_nodes = set(new.nodes) - set(old.nodes)
    removed_nodes = set(old.nodes) - set(new.nodes)
    added_edges = set(new.edges) - set(old.edges)
    removed_edges = set(old.edges) - set(new.edges)
    return {
        "added_nodes": list(added_nodes),
        "removed_nodes": list(removed_nodes),
        "added_edges": list(added_edges),
        "removed_edges": list(removed_edges),
    }
```

---

### 4. Visualizer (`visualize.py`)
Provides static and interactive graph rendering.

```python
from pyvis.network import Network

def visualize(graph, output="flow_graph.html"):
    net = Network(directed=True, notebook=False)
    for n in graph.nodes:
        net.add_node(n, label=n)
    for a, b in graph.edges:
        net.add_edge(a, b)
    net.show(output)
```

---

### 5. CLI (`cli.py`)
Minimal command-line entrypoint for convenience.

```python
import argparse
from pathlib import Path
from .scanner import scan_directory
from .snapshot import save_graph, load_graph
from .drift import compare_graphs
from .visualize import visualize

def main():
    parser = argparse.ArgumentParser(description="FlowScope CLI")
    sub = parser.add_subparsers(dest="cmd")

    scan = sub.add_parser("scan")
    scan.add_argument("path")
    scan.add_argument("--output", default="flow_graph.json")

    cmp = sub.add_parser("compare")
    cmp.add_argument("old")
    cmp.add_argument("new")

    vis = sub.add_parser("visualize")
    vis.add_argument("graph")
    vis.add_argument("--output", default="flow_graph.html")

    args = parser.parse_args()
    if args.cmd == "scan":
        g = scan_directory(Path(args.path))
        save_graph(g, args.output)
        print(f"Saved graph to {args.output}")
    elif args.cmd == "compare":
        from .snapshot import load_graph
        diff = compare_graphs(load_graph(args.old), load_graph(args.new))
        print(diff)
    elif args.cmd == "visualize":
        from .snapshot import load_graph
        g = load_graph(args.graph)
        visualize(g, args.output)
        print(f"Saved HTML graph to {args.output}")

if __name__ == "__main__":
    main()
```

---

## 🧪 Example Reference Cases

Create a test directory structure:

```
flowscope_examples/
├── example_v1/
│   └── math_ops.py
├── example_v2/
│   └── math_ops.py
```

### example_v1/math_ops.py
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def calculator(a, b):
    return add(a, b)
```

### example_v2/math_ops.py
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def calculator(a, b):
    return multiply(a, b)
```

### Test commands
```bash
flowscope scan flowscope_examples/example_v1 --output v1.json
flowscope scan flowscope_examples/example_v2 --output v2.json
flowscope compare v1.json v2.json
flowscope visualize v2.json --output v2_graph.html
```

Expected diff:
```json
{
  "added_nodes": ["math_ops.multiply"],
  "removed_nodes": [],
  "added_edges": [["calculator", "multiply"]],
  "removed_edges": [["calculator", "add"]]
}
```

---

## 🧠 Implementation Notes

- **Dependencies:** `networkx`, `pyvis`
- **Compatibility:** Python 3.9+
- **Performance:** Scales easily to thousands of functions per scan.
- **Security:** Static analysis only; no code execution required.
- **Extensibility:** Future dynamic mode can log actual runtime flows.

---

## 📈 Future Extensions

| Feature | Description |
|----------|--------------|
| Runtime tracing | Use `sys.settrace` to validate live flow edges |
| Function metadata | Add docstring summaries to graph nodes |
| Weighted edges | Track call frequency or complexity |
| Module-level graph diff | Compare architecture drift visually |
| Web dashboard | Aggregate drift over time and show trends |

---

## ✅ Acceptance Criteria

- Scans any valid Python project recursively.
- Outputs a reproducible JSON call graph.
- Compares graphs to identify added/removed functions and connections.
- Provides CLI and programmatic API.
- Supports visualization with `pyvis`.

---

**Author:** Internal SpecCoder Utility Design  
**Project:** FlowScope — Code Flow and Drift Analysis  
**Version:** 1.0 Specification
