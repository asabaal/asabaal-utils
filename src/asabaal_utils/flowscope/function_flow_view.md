# FlowScope Function-Level Flow View Specification

## Overview

This document defines the architecture and behavior of the **Function-Level Flow View** for the FlowScope visualization system. This feature enables detailed visualization of code flow within an individual function, complementing the existing global function call graph.

---

## 1. Purpose

The Function-Level Flow View extends FlowScope from inter-function analysis (current global graph) to intra-function analysis. It visualizes the logical and control flow within a single function, providing insights into branching, looping, assignments, and returns.

**Primary goals:**

* Help developers understand control paths inside a given function.
* Support debugging, optimization, and learning workflows.
* Maintain seamless integration with the existing FlowScope UI/UX and color legend.

---

## 2. Conceptual Model

Each function is decomposed into an internal graph where nodes represent logical operations or control blocks, and edges represent control flow transitions.

### Node Types

| Type        | Description                            | Default Color |
| ----------- | -------------------------------------- | ------------- |
| Entry       | Start of the function                  | Green         |
| Assignment  | Variable initialization or computation | Yellow        |
| Conditional | Branching logic (if / elif / else)     | Orange        |
| Loop        | Iterative constructs (for / while)     | Blue          |
| Action      | Function calls or side effects         | Yellow        |
| Return      | Function exit with return value        | Green         |
| Exit        | Logical end of execution               | Gray          |

### Edge Types

* **Sequential:** Default next-line execution.
* **Conditional True/False:** Paths depending on branch outcome.
* **Loop Back:** Repeated iteration edge.
* **Exit:** Function termination.

---

## 3. Example

### Function Source

```python
def validate_function(data):
    errors = []
    for item in data:
        if not validate_item(item):
            errors.append(item)
        elif is_outdated(item):
            refresh_item(item)
    summary = summarize(errors)
    if summary:
        log_summary(summary)
    return len(errors) == 0
```

### Graph Representation

```json
{
  "function": "validate_function",
  "type": "function_flow",
  "nodes": [
    {"id": "A", "label": "Start", "type": "entry", "color": "green"},
    {"id": "B", "label": "errors = []", "type": "assign", "color": "yellow"},
    {"id": "C", "label": "for item in data", "type": "loop", "color": "blue"},
    {"id": "D", "label": "if not validate_item(item)", "type": "conditional", "color": "orange"},
    {"id": "E", "label": "errors.append(item)", "type": "action", "color": "yellow"},
    {"id": "F", "label": "elif is_outdated(item)", "type": "conditional", "color": "orange"},
    {"id": "G", "label": "refresh_item(item)", "type": "action", "color": "yellow"},
    {"id": "H", "label": "summary = summarize(errors)", "type": "assign", "color": "yellow"},
    {"id": "I", "label": "if summary", "type": "conditional", "color": "orange"},
    {"id": "J", "label": "log_summary(summary)", "type": "action", "color": "yellow"},
    {"id": "K", "label": "return len(errors) == 0", "type": "return", "color": "green"},
    {"id": "⊥", "label": "End", "type": "exit", "color": "grey"}
  ],
  "edges": [
    ["A", "B"], ["B", "C"], ["C", "D"],
    ["D", "E"], ["D", "F"],
    ["F", "G"], ["E", "C"], ["G", "C"],
    ["C", "H"], ["H", "I"],
    ["I", "J"], ["I", "K"],
    ["J", "K"], ["K", "⊥"]
  ]
}
```

---

## 4. Integration Strategy

### 4.1. UI Interaction

* In the Global Function Explorer, each function node gains a **click event**.
* Clicking opens a sub-panel or overlay that renders the Function-Level Flow View.
* The subgraph uses the same color scheme and layout engine (e.g., D3/Vis.js/Cytoscape).

### 4.2. Data Source

* The flow graph is generated dynamically via AST parsing of the selected function.
* Parsed data is transformed into the JSON format above.

### 4.3. Rendering Pipeline

1. User clicks a node in the global view.
2. FlowScope calls `generate_function_flow(module, function_name)`.
3. That function:

   * Parses the source code with Python's `ast` module.
   * Constructs nodes and edges based on control flow.
   * Returns a JSON structure for rendering.
4. The UI renders the result in a collapsible or pop-up panel.

### 4.4. Optional Enhancements

* Variable dependency highlighting.
* Hover-over tooltips for code snippets.
* Line number mapping and code preview integration.
* Step-through execution simulation.

---

## 5. Implementation Outline (Prompt for Coding Agent)

> **Prompt Title:** Implement Function-Level Flow View in FlowScope

**Objective:** Extend FlowScope by adding intra-function visualization for code flow.

**Tasks:**

1. Create a new module `function_flow.py` that:

   * Parses a given function using Python's `ast`.
   * Constructs a control flow graph (CFG) JSON as defined above.
2. Add an API endpoint or callable method to FlowScope backend:

   ```python
   def generate_function_flow(module_path: str, function_name: str) -> dict:
       """Return a structured JSON representation of internal function flow."""
   ```
3. Integrate with the frontend renderer:

   * On node click, fetch and render the function flow graph.
   * Maintain color consistency and use the same legend.
4. Add toggle options in the UI to expand/collapse the view.
5. Ensure compatibility with the existing renderer and search bar.

---

## 6. Future Extensions

* Integrate performance profiling overlays.
* Allow diff comparison between versions of the same function.
* Add AI-based summaries of code paths (e.g., logic intent or side effects).
* Enable export of the flow graph to DOT or GraphML.

---

## 7. Summary

This layer adds micro-level observability to FlowScope, allowing the same system that maps the *interconnectedness of code* to also explain *the flow within each function*. It bridges static structure and dynamic understanding, making FlowScope a complete tool for reasoning about software behavior.

