"""
function_flow_builder.py
-----------------------------------
Structured intra-function control flow graph (CFG) builder for FlowScope.
This version avoids the flattened "every-line" chaos by preserving
logical block hierarchy (if, elif, else, loops) and building clean,
semantic flow graphs suitable for visualization.
"""

import ast
import uuid


# -----------------------------------------------------
# Utility functions
# -----------------------------------------------------

def new_id():
    """Generate a short unique node id."""
    return f"n_{uuid.uuid4().hex[:6]}"


def code_of(node):
    """Return readable source code representation of an AST node."""
    try:
        import astor
        return astor.to_source(node).strip()
    except Exception:
        try:
            import astunparse
            return astunparse.unparse(node).strip()
        except Exception:
            return getattr(node, "name", str(node))


# -----------------------------------------------------
# Node and Graph model
# -----------------------------------------------------

class Node:
    def __init__(self, label, ntype, line=None):
        self.id = new_id()
        self.label = label
        self.type = ntype
        self.line = line
        self.children = []
        self.true_branch = None
        self.false_branch = None
        self.next_node = None

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "line": self.line,
        }


class FunctionFlow:
    """Container for all nodes and edges of a single function."""

    def __init__(self, func_name):
        self.func_name = func_name
        self.nodes = []
        self.edges = []

    def add_edge(self, src, dst, label=None):
        if src and dst:
            self.edges.append({"from": src.id, "to": dst.id, "label": label})

    def add_node(self, node):
        self.nodes.append(node)
        return node

    def to_json(self):
        return {
            "function": self.func_name,
            "type": "function_flow",
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": self.edges,
        }


# -----------------------------------------------------
# CFG Builder
# -----------------------------------------------------

class FunctionFlowBuilder(ast.NodeVisitor):
    """
    Traverses a Python function's AST to build a control-flow graph (CFG)
    with semantic block awareness.
    """

    def __init__(self, func_name):
        self.flow = FunctionFlow(func_name)
        self.prev_node = None
        self.stack = []  # for nested control blocks

    def connect(self, node):
        """Connect current node to previous node sequentially."""
        if self.prev_node:
            self.flow.add_edge(self.prev_node, node)
        self.prev_node = node

    # --- Node creation helpers ---
    def make_node(self, label, ntype, line=None):
        node = Node(label=label, ntype=ntype, line=line)
        self.flow.add_node(node)
        return node

    # --- Core traversal ---
    def visit_FunctionDef(self, node):
        entry = self.make_node(f"Enter {node.name}", "entry", node.lineno)
        self.prev_node = entry

        for stmt in node.body:
            self.visit(stmt)

        exit_node = self.make_node(f"Exit {node.name}", "exit")
        self.flow.add_edge(self.prev_node, exit_node)
        self.prev_node = exit_node

    def visit_Assign(self, node):
        label = code_of(node)
        n = self.make_node(label, "assignment", node.lineno)
        self.connect(n)

    def visit_Expr(self, node):
        label = code_of(node)
        n = self.make_node(label, "statement", node.lineno)
        self.connect(n)

    def visit_Return(self, node):
        label = code_of(node)
        n = self.make_node(label, "return", node.lineno)
        self.connect(n)

    def visit_If(self, node):
        cond_label = code_of(node.test)
        cond_node = self.make_node(f"if {cond_label}", "conditional", node.lineno)
        self.connect(cond_node)

        # True branch
        true_entry = self.make_node("Begin True Block", "block_start")
        self.flow.add_edge(cond_node, true_entry, label="True")
        prev_before_if = self.prev_node
        self.prev_node = true_entry
        for stmt in node.body:
            self.visit(stmt)
        true_exit = self.prev_node

        # False branch (else/elif)
        if node.orelse:
            false_entry = self.make_node("Begin False Block", "block_start")
            self.flow.add_edge(cond_node, false_entry, label="False")
            self.prev_node = false_entry
            for stmt in node.orelse:
                self.visit(stmt)
            false_exit = self.prev_node
        else:
            false_exit = cond_node  # no else path

        # Merge point
        merge_node = self.make_node("Merge after if", "merge")
        self.flow.add_edge(true_exit, merge_node)
        if false_exit != cond_node:
            self.flow.add_edge(false_exit, merge_node)

        self.prev_node = merge_node

    def visit_For(self, node):
        loop_label = code_of(node.target) + " in " + code_of(node.iter)
        loop_node = self.make_node(f"for {loop_label}", "loop", node.lineno)
        self.connect(loop_node)

        body_entry = self.make_node("Loop Body", "block_start")
        self.flow.add_edge(loop_node, body_entry, label="Iterate")

        self.prev_node = body_entry
        for stmt in node.body:
            self.visit(stmt)
        body_exit = self.prev_node

        # connect back for next iteration
        self.flow.add_edge(body_exit, loop_node, label="next iteration")

        # loop exit
        loop_exit = self.make_node("Exit Loop", "loop_exit")
        self.flow.add_edge(loop_node, loop_exit, label="done")
        self.prev_node = loop_exit

    def visit_While(self, node):
        cond_label = code_of(node.test)
        cond_node = self.make_node(f"while {cond_label}", "loop", node.lineno)
        self.connect(cond_node)

        body_entry = self.make_node("While Body", "block_start")
        self.flow.add_edge(cond_node, body_entry, label="True")

        self.prev_node = body_entry
        for stmt in node.body:
            self.visit(stmt)
        body_exit = self.prev_node
        self.flow.add_edge(body_exit, cond_node, label="loop back")

        loop_exit = self.make_node("Exit While", "loop_exit")
        self.flow.add_edge(cond_node, loop_exit, label="False")
        self.prev_node = loop_exit

    # Default handler
    def generic_visit(self, node):
        # Handle any unhandled node types gracefully
        if isinstance(node, ast.stmt):
            label = code_of(node)
            n = self.make_node(label, "statement", getattr(node, "lineno", None))
            self.connect(n)
        super().generic_visit(node)


# -----------------------------------------------------
# Public API
# -----------------------------------------------------

def generate_function_flow(source: str, func_name: str) -> dict:
    """
    Generate a structured JSON control-flow graph for a given function source.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Syntax error parsing function source: {e}")

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            builder = FunctionFlowBuilder(func_name)
            builder.visit(node)
            return builder.flow.to_json()

    raise ValueError(f"Function {func_name} not found in provided source.")

