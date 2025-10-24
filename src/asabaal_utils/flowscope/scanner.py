import ast
from pathlib import Path
import networkx as nx
from typing import Set, Optional


def scan_directory(path: Path, exclude_patterns: Optional[Set[str]] = None) -> nx.DiGraph:
    """Scan directory recursively and build call graph.
    
    Args:
        path: Directory path to scan
        exclude_patterns: Set of directory/file patterns to exclude
        
    Returns:
        NetworkX DiGraph representing function call relationships
    """
    if exclude_patterns is None:
        exclude_patterns = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
    
    graph = nx.DiGraph()
    
    for file in path.rglob("*.py"):
        # Skip excluded patterns
        if any(pattern in str(file) for pattern in exclude_patterns):
            continue
            
        try:
            content = file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        current_func = None
        current_module = file.stem
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = f"{current_module}.{node.name}"
                graph.add_node(func_name, file=str(file), line=node.lineno)
                current_func = func_name
                
            elif isinstance(node, ast.AsyncFunctionDef):
                func_name = f"{current_module}.{node.name}"
                graph.add_node(func_name, file=str(file), line=node.lineno, async_func=True)
                current_func = func_name
                
            elif isinstance(node, ast.Call) and current_func:
                called_name = _extract_called_name(node)
                if called_name:
                    graph.add_edge(current_func, called_name)
    
    return graph


def _extract_called_name(call_node: ast.Call) -> Optional[str]:
    """Extract the name of the called function from an AST Call node."""
    if isinstance(call_node.func, ast.Name):
        return call_node.func.id
    elif isinstance(call_node.func, ast.Attribute):
        # Handle method calls like obj.method() or module.function()
        parts = []
        node = call_node.func
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def scan_file(file_path: Path) -> nx.DiGraph:
    """Scan a single Python file and build call graph.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        NetworkX DiGraph representing function call relationships in the file
    """
    if not file_path.suffix == ".py":
        raise ValueError("File must be a Python file (.py)")
    
    graph = nx.DiGraph()
    
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to parse {file_path}: {e}")

    current_func = None
    current_module = file_path.stem
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = f"{current_module}.{node.name}"
            graph.add_node(func_name, file=str(file_path), line=node.lineno)
            current_func = func_name
            
        elif isinstance(node, ast.AsyncFunctionDef):
            func_name = f"{current_module}.{node.name}"
            graph.add_node(func_name, file=str(file_path), line=node.lineno, async_func=True)
            current_func = func_name
            
        elif isinstance(node, ast.Call) and current_func:
            called_name = _extract_called_name(node)
            if called_name:
                graph.add_edge(current_func, called_name)
    
    return graph