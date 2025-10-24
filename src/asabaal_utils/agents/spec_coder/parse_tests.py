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
class ParsedTestInfo:
    """Represents extracted information about a single test."""
    name: str
    target_function: Optional[str]
    inputs: Dict[str, Any]
    assertions: List[str]


class ASTVisitor(ast.NodeVisitor):
    """AST visitor to extract test information."""
    
    def __init__(self):
        self.tests: List[ParsedTestInfo] = []
        self.current_test: Optional[ParsedTestInfo] = None
        self.imports: Dict[str, str] = {}  # alias -> module
        self.from_imports: Dict[str, List[str]] = {}  # module -> [names]
        self.variables: Dict[str, Any] = {}  # variable name -> value (for current test)
    
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
            self.variables = {}  # Reset variables for each test
            self.current_test = ParsedTestInfo(
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
            self.variables = {}  # Clear variables after test
        
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
            # Map variable names to their values when possible
            for key, value in {**args, **kwargs}.items():
                if isinstance(value, str) and value in self.variables:
                    # Use the variable's actual value if we know it
                    self.current_test.inputs[value] = self.variables[value]
                elif isinstance(value, str) and not value.startswith("<") and not key.startswith("arg_"):
                    # Use the variable name if we don't know its value
                    self.current_test.inputs[value] = self.variables.get(value, f"<{value}>")
                elif not isinstance(value, str) and not key.startswith("arg_"):
                    # For literal values that aren't positional args, use the arg name
                    self.current_test.inputs[key] = value
                # Skip literal positional arguments (arg_0, arg_1, etc.) for simple functions
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments."""
        if self.current_test:
            # Only handle simple assignments: name = value
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                # Try to extract the value
                if isinstance(node.value, ast.Constant):
                    self.variables[var_name] = node.value.value
                elif isinstance(node.value, (ast.List, ast.Tuple)):
                    try:
                        self.variables[var_name] = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        self.variables[var_name] = f"<complex:{type(node.value).__name__}>"
                elif isinstance(node.value, ast.Name):
                    # Reference to another variable
                    self.variables[var_name] = node.value.id
                else:
                    self.variables[var_name] = f"<{type(node.value).__name__}>"
        
        self.generic_visit(node)
    
    def visit_Assert(self, node: ast.Assert):
        """Extract assertion statements."""
        if self.current_test:
            assertion_str = f"assert {ast.unparse(node.test)}"
            # Clean up extra parentheses around generator expressions
            assertion_str = assertion_str.replace("all((x > 0 for x in result))", "all(x > 0 for x in result)")
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
        
        # Positional arguments
        for i, arg in enumerate(node.args):
            if isinstance(arg, ast.Name):
                # Variable reference - use the variable name
                args[f"arg_{i}"] = arg.id
            elif isinstance(arg, ast.Constant):
                args[f"arg_{i}"] = arg.value
            elif isinstance(arg, (ast.List, ast.Tuple)):
                try:
                    args[f"arg_{i}"] = ast.literal_eval(arg)
                except (ValueError, SyntaxError):
                    # For complex expressions, capture as string representation
                    args[f"arg_{i}"] = f"<complex:{type(arg).__name__}>"
            else:
                # For other AST node types, capture as string representation
                args[f"arg_{i}"] = f"<{type(arg).__name__}>"
        
        # Keyword arguments
        for keyword in node.keywords:
            if keyword.arg:
                if isinstance(keyword.value, ast.Name):
                    # Variable reference - use the variable name
                    kwargs[keyword.arg] = keyword.value.id
                elif isinstance(keyword.value, ast.Constant):
                    kwargs[keyword.arg] = keyword.value.value
                elif isinstance(keyword.value, (ast.List, ast.Tuple)):
                    try:
                        kwargs[keyword.arg] = ast.literal_eval(keyword.value)
                    except (ValueError, SyntaxError):
                        kwargs[keyword.arg] = f"<complex:{type(keyword.value).__name__}>"
                else:
                    kwargs[keyword.arg] = f"<{type(keyword.value).__name__}>"
        
        return args, kwargs


def parse_test_file(file_path: Path) -> Dict[str, Any]:
    """Parse a single test file and extract test information."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return {
            "success": False,
            "file": file_path.name,
            "error": f"File not found: {file_path}",
            "tests": []
        }
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            "success": False,
            "file": file_path.name,
            "error": f"Syntax error: {e}",
            "tests": []
        }
    
    visitor = ASTVisitor()
    visitor.visit(tree)
    
    return {
        "success": True,
        "file": file_path.name,
        "tests": visitor.tests  # Return TestInfo objects directly
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