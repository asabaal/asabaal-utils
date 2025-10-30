"""
function_flow_builder.py
Enhanced intra-function control flow graph builder for FlowScope.

Features:
- try/except/else/finally blocks
- full comprehension expansion with depth limit
- correct no-else merging
- RETURNS ONLY EDGE TO THE EXIT NODE
"""

import ast
import uuid

MAX_COMP_DEPTH = 2


def new_id():
    return f"n_{uuid.uuid4().hex[:6]}"


def code_of(node):
    try:
        import astor
        return astor.to_source(node).strip()
    except Exception:
        try:
            import astunparse
            return astunparse.unparse(node).strip()
        except Exception:
            return getattr(node, "name", str(node))


class Node:
    def __init__(self, label, ntype, line=None):
        self.id = new_id()
        self.label = label
        self.type = ntype
        self.line = line

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "line": self.line,
        }


class FunctionFlow:
    def __init__(self, func_name, source_code=None):
        self.func_name = func_name
        self.source_code = source_code
        self.nodes = []
        self.edges = []

    def add_edge(self, src, dst, label=None):
        if src and dst:
            self.edges.append({"from": src.id, "to": dst.id, "label": label})

    def add_node(self, node):
        self.nodes.append(node)
        return node

    def to_json(self):
        result = {
            "function": self.func_name,
            "type": "function_flow",
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": self.edges,
        }
        if self.source_code:
            result["source_code"] = self.source_code
        return result


class FunctionFlowBuilder(ast.NodeVisitor):
    """AST traversal builder for detailed control flow."""

    def __init__(self, func_name, source_code=None):
        self.flow = FunctionFlow(func_name, source_code)
        self.prev_node = None
        self.exit_node = None  # single exit target for all returns

    # helpers
    def connect(self, node):
        if self.prev_node:
            self.flow.add_edge(self.prev_node, node)
        self.prev_node = node

    def make_node(self, label, ntype, line=None):
        node = Node(label=label, ntype=ntype, line=line)
        self.flow.add_node(node)
        return node

    # function def
    def visit_FunctionDef(self, node):
        entry = self.make_node(f"Enter {node.name}", "entry", node.lineno)
        self.prev_node = entry

        # create a dedicated exit node up front
        self.exit_node = self.make_node(f"Exit {node.name}", "exit")

        for stmt in node.body:
            self.visit(stmt)

        # connect any remaining non-returning path to exit
        if self.prev_node and self.prev_node is not self.exit_node:
            self.flow.add_edge(self.prev_node, self.exit_node)

        # finalize
        self.prev_node = self.exit_node

    # simple statements
    def visit_Assign(self, node):
        n = self.make_node(code_of(node), "assignment", node.lineno)
        self.connect(n)

    def visit_Expr(self, node):
        n = self.make_node(code_of(node), "statement", node.lineno)
        self.connect(n)

    def visit_Return(self, node):
        # create return node and connect from current chain
        ret = self.make_node(code_of(node), "return", node.lineno)
        if self.prev_node:
            self.flow.add_edge(self.prev_node, ret)
        # return must only edge to the single exit node
        if self.exit_node:
            self.flow.add_edge(ret, self.exit_node)
        # break the sequential chain after return
        self.prev_node = None

    # if/else with explicit false path to merge
    def visit_If(self, node):
        cond_node = self.make_node(f"if {code_of(node.test)}", "conditional", node.lineno)
        self.connect(cond_node)

        # True branch
        true_entry = self.make_node("Begin True Block", "block_start")
        self.flow.add_edge(cond_node, true_entry, label="True")
        self.prev_node = true_entry
        for stmt in node.body:
            self.visit(stmt)
        true_exit = self.prev_node

        # False branch
        false_exit = None
        if node.orelse:
            false_entry = self.make_node("Begin False Block", "block_start")
            self.flow.add_edge(cond_node, false_entry, label="False")
            self.prev_node = false_entry
            for stmt in node.orelse:
                self.visit(stmt)
            false_exit = self.prev_node

        # Merge
        merge_node = self.make_node("Merge after if", "merge")
        if true_exit:
            self.flow.add_edge(true_exit, merge_node)
        if false_exit:
            self.flow.add_edge(false_exit, merge_node)
        else:
            # no else means the False path goes directly to the merge
            self.flow.add_edge(cond_node, merge_node, label="False")
        self.prev_node = merge_node

    # loops
    def visit_For(self, node):
        loop_node = self.make_node(f"for {code_of(node.target)} in {code_of(node.iter)}", "loop", node.lineno)
        self.connect(loop_node)

        body_entry = self.make_node("Loop Body", "block_start")
        self.flow.add_edge(loop_node, body_entry, label="Iterate")
        self.prev_node = body_entry
        for stmt in node.body:
            self.visit(stmt)
        body_exit = self.prev_node

        # loop back
        if body_exit:
            self.flow.add_edge(body_exit, loop_node, label="next iteration")

        loop_exit = self.make_node("Exit Loop", "loop_exit")
        self.flow.add_edge(loop_node, loop_exit, label="done")
        self.prev_node = loop_exit

    def visit_While(self, node):
        cond_node = self.make_node(f"while {code_of(node.test)}", "loop", node.lineno)
        self.connect(cond_node)

        body_entry = self.make_node("While Body", "block_start")
        self.flow.add_edge(cond_node, body_entry, label="True")
        self.prev_node = body_entry
        for stmt in node.body:
            self.visit(stmt)
        body_exit = self.prev_node

        if body_exit:
            self.flow.add_edge(body_exit, cond_node, label="loop back")

        loop_exit = self.make_node("Exit While", "loop_exit")
        self.flow.add_edge(cond_node, loop_exit, label="False")
        self.prev_node = loop_exit

    # try/except/else/finally
    def visit_Try(self, node):
        try_node = self.make_node("try", "try", node.lineno)
        self.connect(try_node)

        body_entry = self.make_node("try body", "block_start")
        self.flow.add_edge(try_node, body_entry, label="try")
        self.prev_node = body_entry
        for stmt in node.body:
            self.visit(stmt)
        body_exit = self.prev_node

        handler_exits = []
        for handler in node.handlers:
            h_label = f"except {getattr(handler.type, 'id', 'Exception')}"
            except_entry = self.make_node(h_label, "except", getattr(handler, "lineno", None))
            self.flow.add_edge(try_node, except_entry, label=h_label)
            self.prev_node = except_entry
            for stmt in handler.body:
                self.visit(stmt)
            handler_exits.append(self.prev_node)

        if node.orelse:
            else_entry = self.make_node("try-else", "block_start")
            self.flow.add_edge(body_exit, else_entry, label="else")
            self.prev_node = else_entry
            for stmt in node.orelse:
                self.visit(stmt)
            body_exit = self.prev_node

        if node.finalbody:
            finally_entry = self.make_node("finally", "block_start")
            self.flow.add_edge(try_node, finally_entry, label="finally")
            self.prev_node = finally_entry
            for stmt in node.finalbody:
                self.visit(stmt)
            handler_exits.append(self.prev_node)

        merge = self.make_node("After try", "merge")
        if body_exit:
            self.flow.add_edge(body_exit, merge)
        for he in handler_exits:
            if he:
                self.flow.add_edge(he, merge)
        self.prev_node = merge

    # comprehension expansion
    def _expand_comprehension(self, node, depth=0):
        if depth > MAX_COMP_DEPTH:
            violation = self.make_node(
                f"complex comprehension (depth>{MAX_COMP_DEPTH})",
                "complex_comprehension_violation",
                getattr(node, "lineno", None),
            )
            self.connect(violation)
            return violation

        comp_entry = self.make_node("comprehension start", "comprehension_entry", getattr(node, "lineno", None))
        self.connect(comp_entry)
        prev = comp_entry

        for gen in node.generators:
            loop_label = f"for {code_of(gen.target)} in {code_of(gen.iter)}"
            loop_node = self.make_node(loop_label, "loop", getattr(gen, "lineno", None))
            self.flow.add_edge(prev, loop_node)
            prev = loop_node

            for if_cond in gen.ifs:
                cond_label = f"if {code_of(if_cond)}"
                cond_node = self.make_node(cond_label, "conditional", getattr(if_cond, "lineno", None))
                self.flow.add_edge(prev, cond_node, label="filter")
                prev = cond_node

        yield_label = None
        if isinstance(node, ast.DictComp):
            yield_label = f"yield {code_of(node.key)} : {code_of(node.value)}"
        else:
            if isinstance(node.elt, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                self._expand_comprehension(node.elt, depth + 1)
            else:
                yield_label = f"yield {code_of(node.elt)}"

        if yield_label:
            yield_node = self.make_node(yield_label, "yield", getattr(node, "lineno", None))
            self.flow.add_edge(prev, yield_node)
            prev = yield_node

        merge = self.make_node("end comprehension", "merge")
        self.flow.add_edge(prev, merge)
        self.prev_node = merge
        return merge

    def visit_ListComp(self, node):
        self._expand_comprehension(node, depth=0)

    def visit_SetComp(self, node):
        self._expand_comprehension(node, depth=0)

    def visit_DictComp(self, node):
        self._expand_comprehension(node, depth=0)

    def visit_GeneratorExp(self, node):
        self._expand_comprehension(node, depth=0)

    # fallback
    def generic_visit(self, node):
        if isinstance(node, ast.stmt):
            n = self.make_node(code_of(node), "statement", getattr(node, "lineno", None))
            self.connect(n)
        super().generic_visit(node)


def generate_function_flow(source: str, func_name: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Syntax error parsing function source: {e}")

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # Extract just this function's source code
            try:
                import astor
                function_source = astor.to_source(node).strip()
            except Exception:
                try:
                    import astunparse
                    function_source = astunparse.unparse(node).strip()
                except Exception:
                    # Fallback: get the function's lines from the full source
                    lines = source.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                    function_source = '\n'.join(lines[start_line:end_line])
            
            builder = FunctionFlowBuilder(func_name, function_source)
            builder.visit(node)
            return builder.flow.to_json()

    raise ValueError(f"Function {func_name} not found in provided source.")

