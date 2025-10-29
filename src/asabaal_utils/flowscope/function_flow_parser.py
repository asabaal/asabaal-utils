"""
Function Flow Parser for intra-function analysis.

This module parses individual functions to extract control flow information,
including assignments, conditionals, loops, and return statements.
"""

import ast
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ControlFlowNode:
    """Represents a node in the control flow graph."""
    id: str
    type: str  # 'entry', 'assignment', 'conditional', 'loop', 'return', 'exit'
    label: str
    line: int
    condition: Optional[str] = None
    targets: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.targets is None:
            self.targets = []


@dataclass
class FunctionFlow:
    """Represents the control flow within a single function."""
    function_name: str
    module: str
    file_path: str
    entry_point: ControlFlowNode
    exit_point: ControlFlowNode
    nodes: List[ControlFlowNode]
    edges: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'function_name': self.function_name,
            'module': self.module,
            'file_path': self.file_path,
            'entry_point': {
                'id': self.entry_point.id,
                'type': self.entry_point.type,
                'label': self.entry_point.label,
                'line': self.entry_point.line
            },
            'exit_point': {
                'id': self.exit_point.id,
                'type': self.exit_point.type,
                'label': self.exit_point.label,
                'line': self.exit_point.line
            },
            'nodes': [
                {
                    'id': node.id,
                    'type': node.type,
                    'label': node.label,
                    'line': node.line,
                    'condition': node.condition,
                    'targets': node.targets
                }
                for node in self.nodes
            ],
            'edges': self.edges
        }


class FunctionFlowVisitor(ast.NodeVisitor):
    """AST visitor to extract control flow information from a function."""
    
    def __init__(self, function_name: str, module: str, file_path: str):
        self.function_name = function_name
        self.module = module
        self.file_path = file_path
        self.nodes: List[ControlFlowNode] = []
        self.edges: List[Dict[str, Any]] = []
        self.node_counter = 0
        self.current_scope: List[str] = []
        
        # Create entry and exit points
        self.entry_node = ControlFlowNode(
            id=f"node_{self.node_counter}",
            type="entry",
            label=f"Enter {function_name}",
            line=0
        )
        self.node_counter += 1
        
        self.exit_node = ControlFlowNode(
            id=f"node_{self.node_counter}",
            type="exit",
            label=f"Exit {function_name}",
            line=0
        )
        self.node_counter += 1
        
        self.last_node: Optional[ControlFlowNode] = self.entry_node
        
    def _create_node(self, node_type: str, label: str, line: int, 
                    condition: Optional[str] = None) -> ControlFlowNode:
        """Create a new control flow node."""
        node = ControlFlowNode(
            id=f"node_{self.node_counter}",
            type=node_type,
            label=label,
            line=line,
            condition=condition
        )
        self.node_counter += 1
        return node
    
    def _add_edge(self, from_node: ControlFlowNode, to_node: ControlFlowNode, 
                 label: Optional[str] = None):
        """Add an edge between two nodes."""
        edge = {
            'from': from_node.id,
            'to': to_node.id,
            'label': label
        }
        self.edges.append(edge)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statements."""
        # Create assignment node
        targets = ', '.join([ast.unparse(t) for t in node.targets])
        value = ast.unparse(node.value)
        label = f"{targets} = {value}"
        
        assign_node = self._create_node(
            "assignment", 
            label, 
            node.lineno
        )
        
        self.nodes.append(assign_node)
        if self.last_node:
            self._add_edge(self.last_node, assign_node)
        self.last_node = assign_node
        
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """Visit if statements."""
        # Create conditional node
        condition = ast.unparse(node.test)
        label = f"if {condition}"
        
        conditional_node = self._create_node(
            "conditional",
            label,
            node.lineno,
            condition=condition
        )
        
        self.nodes.append(conditional_node)
        if self.last_node:
            self._add_edge(self.last_node, conditional_node)
        
        # Save current state
        prev_last_node = self.last_node
        self.last_node = conditional_node
        
        # Process if body
        for stmt in node.body:
            self.visit(stmt)
        
        # Save end of if body
        if_end_node = self.last_node
        
        # Reset to conditional for else processing
        self.last_node = conditional_node
        
        # Process else body if exists
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt)
            else_end_node = self.last_node
            
            # Create merge node
            merge_node = self._create_node(
                "merge",
                "merge",
                node.lineno
            )
            self.nodes.append(merge_node)
            
            # Connect both branches to merge
            if if_end_node:
                self._add_edge(if_end_node, merge_node, "end if")
            if else_end_node:
                self._add_edge(else_end_node, merge_node, "end else")
            self.last_node = merge_node
        else:
            # Just continue from if body
            self.last_node = if_end_node
    
    def visit_For(self, node: ast.For):
        """Visit for loops."""
        # Create loop node
        target = ast.unparse(node.target)
        iter_ = ast.unparse(node.iter)
        label = f"for {target} in {iter_}"
        
        loop_node = self._create_node(
            "loop",
            label,
            node.lineno
        )
        
        self.nodes.append(loop_node)
        if self.last_node:
            self._add_edge(self.last_node, loop_node)
        
        # Save current state
        prev_last_node = self.last_node
        self.last_node = loop_node
        
        # Process loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Connect back to loop node (iteration)
        if self.last_node:
            self._add_edge(self.last_node, loop_node, "continue")
        
        # Create loop exit node
        loop_exit_node = self._create_node(
            "loop_exit",
            f"exit for {target}",
            node.lineno
        )
        self.nodes.append(loop_exit_node)
        self._add_edge(loop_node, loop_exit_node, "break/complete")
        self.last_node = loop_exit_node
    
    def visit_While(self, node: ast.While):
        """Visit while loops."""
        # Create loop node
        condition = ast.unparse(node.test)
        label = f"while {condition}"
        
        loop_node = self._create_node(
            "loop",
            label,
            node.lineno,
            condition=condition
        )
        
        self.nodes.append(loop_node)
        if self.last_node:
            self._add_edge(self.last_node, loop_node)
        
        # Save current state
        prev_last_node = self.last_node
        self.last_node = loop_node
        
        # Process loop body
        for stmt in node.body:
            self.visit(stmt)
        
        # Connect back to loop node (iteration)
        if self.last_node:
            self._add_edge(self.last_node, loop_node, "continue")
        
        # Create loop exit node
        loop_exit_node = self._create_node(
            "loop_exit",
            f"exit while",
            node.lineno
        )
        self.nodes.append(loop_exit_node)
        self._add_edge(loop_node, loop_exit_node, "break/complete")
        self.last_node = loop_exit_node
    
    def visit_Return(self, node: ast.Return):
        """Visit return statements."""
        # Create return node
        if node.value:
            value = ast.unparse(node.value)
            label = f"return {value}"
        else:
            label = "return"
        
        return_node = self._create_node(
            "return",
            label,
            node.lineno
        )
        
        self.nodes.append(return_node)
        if self.last_node:
            self._add_edge(self.last_node, return_node)
        self._add_edge(return_node, self.exit_node)
        
        # Reset last node since return ends flow
        self.last_node = None
    
    def visit_Try(self, node: ast.Try):
        """Visit try-except blocks."""
        # Create try node
        try_node = self._create_node(
            "try",
            "try",
            node.lineno
        )
        
        self.nodes.append(try_node)
        if self.last_node:
            self._add_edge(self.last_node, try_node)
        self.last_node = try_node
        
        # Process try body
        for stmt in node.body:
            self.visit(stmt)
        
        try_end_node = self.last_node
        
        # Process except handlers
        except_end_nodes: List[Optional[ControlFlowNode]] = []
        for handler in node.handlers:
            self.last_node = try_node
            
            # Create except node
            if handler.type:
                exc_type = ast.unparse(handler.type)
                label = f"except {exc_type}"
            else:
                label = "except"
            
            except_node = self._create_node(
                "except",
                label,
                handler.lineno
            )
            
            self.nodes.append(except_node)
            self._add_edge(try_node, except_node)
            
            # Process except body
            for stmt in handler.body:
                self.visit(stmt)
            
            except_end_nodes.append(self.last_node)
        
        # Process else body if exists
        if node.orelse:
            self.last_node = try_end_node
            for stmt in node.orelse:
                self.visit(stmt)
            else_end_node = self.last_node
        else:
            else_end_node = try_end_node
        
        # Create merge node
        merge_node = self._create_node(
            "merge",
            "merge try-except",
            node.lineno
        )
        self.nodes.append(merge_node)
        
        # Connect all paths to merge
        if else_end_node:
            self._add_edge(else_end_node, merge_node, "end try")
        for except_end in except_end_nodes:
            if except_end:
                self._add_edge(except_end, merge_node, "end except")
        
        self.last_node = merge_node
    
    def generic_visit(self, node):
        """Generic visit method for other node types."""
        # For any other statement types, just continue
        if hasattr(node, 'lineno') and hasattr(node, '__class__'):
            # Create a generic statement node
            try:
                label = ast.unparse(node) if hasattr(ast, 'unparse') else str(type(node).__name__)
                if label is None:
                    label = str(type(node).__name__)
                line_num = getattr(node, 'lineno', 0)
                stmt_node = self._create_node(
                    "statement",
                    label,
                    line_num
                )
                self.nodes.append(stmt_node)
                if self.last_node:
                    self._add_edge(self.last_node, stmt_node)
                self.last_node = stmt_node
            except:
                # Skip nodes that can't be unparsed
                pass
        
        super().generic_visit(node)


class FunctionFlowParser:
    """Main parser for extracting function-level control flow."""
    
    def __init__(self):
        self.function_flows: Dict[str, FunctionFlow] = {}
    
    def parse_function(self, source_code: str, function_name: str, 
                      module: str, file_path: str) -> Optional[FunctionFlow]:
        """Parse a single function to extract its control flow."""
        try:
            tree = ast.parse(source_code)
            
            # Find the function definition
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Extract function source
                    function_source = ast.get_source_segment(source_code, node)
                    if not function_source:
                        continue
                    
                    # Create visitor and parse
                    visitor = FunctionFlowVisitor(function_name, module, file_path)
                    visitor.visit(node)
                    
                    # Connect last node to exit if not already connected
                    if visitor.last_node and visitor.last_node != visitor.exit_node:
                        visitor._add_edge(visitor.last_node, visitor.exit_node)
                    
                    # Create function flow
                    function_flow = FunctionFlow(
                        function_name=function_name,
                        module=module,
                        file_path=file_path,
                        entry_point=visitor.entry_node,
                        exit_point=visitor.exit_node,
                        nodes=visitor.nodes,
                        edges=visitor.edges
                    )
                    
                    return function_flow
        
        except SyntaxError as e:
            print(f"Syntax error parsing {function_name}: {e}")
        except Exception as e:
            print(f"Error parsing {function_name}: {e}")
        
        return None
    
    def parse_file(self, file_path: Path, module: str) -> Dict[str, FunctionFlow]:
        """Parse all functions in a file."""
        function_flows = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Find all function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_flow = self.parse_function(
                        source_code, node.name, module, str(file_path)
                    )
                    if function_flow:
                        function_flows[node.name] = function_flow
                        # Also add to the instance's function_flows
                        self.function_flows[node.name] = function_flow
        
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
        
        return function_flows
    
    def save_to_json(self, output_path: Path):
        """Save all function flows to JSON file."""
        data = {
            'function_flows': {
                name: flow.to_dict() 
                for name, flow in self.function_flows.items()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_from_json(self, input_path: Path):
        """Load function flows from JSON file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.function_flows = {}
        for name, flow_data in data.get('function_flows', {}).items():
            # Reconstruct FunctionFlow objects
            entry_point = ControlFlowNode(**flow_data['entry_point'])
            exit_point = ControlFlowNode(**flow_data['exit_point'])
            
            nodes = [ControlFlowNode(**node_data) for node_data in flow_data['nodes']]
            
            function_flow = FunctionFlow(
                function_name=flow_data['function_name'],
                module=flow_data['module'],
                file_path=flow_data['file_path'],
                entry_point=entry_point,
                exit_point=exit_point,
                nodes=nodes,
                edges=flow_data['edges']
            )
            
            self.function_flows[name] = function_flow