"""
Test Parser - AST Analysis Layer

Extracts structured information from Python test files using AST parsing.
Identifies test functions, target functions, inputs, and assertions.
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestInfo:
    """Represents extracted information about a single test."""
    name: str
    target_function: Optional[str]
    inputs: Dict[str, Any]
    assertions: List[str]


class TestVisitor(ast.NodeVisitor):
    """AST visitor to extract test information."""
    
    def __init__(self):
        self.tests: List[TestInfo] = []
        self.current_test: Optional[TestInfo] = None
        self.imports: Dict[str, str] = {}  # alias -> module
        self.from_imports: Dict[str, List[str]] = {}  # module -> [names]
    
    def visit_Import(self, node: ast.Import):
        """Track import statements."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from-import statements."""
        if node.module:
            module_name = node.module
            if module_name not in self.from_imports:
                self.from_imports[module_name] = []
            for alias in node.names:
                self.from_imports[module_name].append(alias.name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit test functions."""
        if node.name.startswith("test_"):
            self.current_test = TestInfo(
                name=node.name,
                target_function=None,
                inputs={},
                assertions=[]
            )
            
            # Visit function body to extract calls and assertions
            for stmt in node.body:
                self.visit(stmt)
            
            if self.current_test:
                self.tests.append(self.current_test)
                self.current_test = None
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Extract function calls and their arguments."""
        if not self.current_test:
            self.generic_visit(node)
            return
        
        # Try to identify the target function
        func_name = self._get_function_name(node)
        
        # Check if this might be the function under test
        if func_name and not func_name.startswith("assert"):
            # Heuristic: first non-assert call is likely the target
            if not self.current_test.target_function:
                self.current_test.target_function = func_name
            
            # Extract arguments
            args, kwargs = self._extract_arguments(node)
            self.current_test.inputs.update(args)
            self.current_test.inputs.update(kwargs)
        
        self.generic_visit(node)
    
    def visit_Assert(self, node: ast.Assert):
        """Extract assertion statements."""
        if self.current_test:
            assertion_str = ast.unparse(node.test)
            self.current_test.assertions.append(assertion_str)
        
        self.generic_visit(node)
    
    def _get_function_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from a call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            return node.func.attr
        return None
    
    def _extract_arguments(self, node: ast.Call) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract positional and keyword arguments from a call."""
        args = {}
        kwargs = {}
        
        # Positional arguments (just capture as literals)
        for i, arg in enumerate(node.args):
            if isinstance(arg, ast.Constant):
                args[f"arg_{i}"] = arg.value
            elif isinstance(arg, (ast.List, ast.Tuple)):
                args[f"arg_{i}"] = ast.literal_eval(arg)
        
        # Keyword arguments
        for keyword in node.keywords:
            if keyword.arg and isinstance(keyword.value, ast.Constant):
                kwargs[keyword.arg] = keyword.value.value
            elif keyword.arg and isinstance(keyword.value, (ast.List, ast.Tuple)):
                kwargs[keyword.arg] = ast.literal_eval(keyword.value)
        
        return args, kwargs


def parse_test_file(file_path: Path) -> Dict[str, Any]:
    """Parse a single test file and extract test information."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            "file": file_path.name,
            "error": f"Syntax error: {e}",
            "tests": []
        }
    
    visitor = TestVisitor()
    visitor.visit(tree)
    
    # Convert TestInfo objects to dictionaries
    tests_data = []
    for test in visitor.tests:
        test_dict = {
            "name": test.name,
            "target_function": test.target_function,
            "inputs": test.inputs,
            "assertions": test.assertions
        }
        tests_data.append(test_dict)
    
    return {
        "file": file_path.name,
        "tests": tests_data
    }


def main():
    """Command-line interface for the test parser."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python parse_tests.py <test_file_or_directory>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        # Parse single file
        result = parse_test_file(path)
        print(json.dumps(result, indent=2))
    
    elif path.is_dir():
        # Parse all Python files in directory
        results = []
        for py_file in path.glob("*.py"):
            if py_file.name.startswith("test_"):
                result = parse_test_file(py_file)
                results.append(result)
        
        print(json.dumps(results, indent=2))
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()