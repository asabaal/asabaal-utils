import ast
import sys
import pkgutil
from pathlib import Path
import networkx as nx
from typing import Set, Optional, List


def _is_external_function(func_name: str, local_modules: Set[str]) -> bool:
    """Check if a function is from external library/standard library.
    
    Args:
        func_name: Full function name (e.g., "module.function" or "function")
        local_modules: Set of local module names
        
    Returns:
        True if function is external, False if it's local
    """
    # Split function name to get module part
    parts = func_name.split('.')
    
    # If no module part, it's likely a built-in or method call - exclude it
    if len(parts) == 1:
        return True
    
    module_name = parts[0]
    
    # Check if it's a local module
    if module_name in local_modules:
        return False
    
    # Check if it's a standard library module
    stdlib_modules = {
        'ast', 'sys', 'os', 'pathlib', 'json', 'csv', 'xml', 're', 'math',
        'datetime', 'time', 'random', 'collections', 'itertools', 'functools',
        'operator', 'typing', 'dataclasses', 'enum', 'contextlib', 'io',
        'logging', 'unittest', 'argparse', 'configparser', 'hashlib', 'hmac',
        'secrets', 'uuid', 'base64', 'urllib', 'http', 'email', 'mimetypes',
        'socket', 'ssl', 'asyncio', 'threading', 'multiprocessing',
        'subprocess', 'shutil', 'tempfile', 'glob', 'fnmatch', 'pickle',
        'sqlite3', 'decimal', 'fractions', 'statistics', 'string', 'textwrap',
        'unicodedata', 'codecs', 'struct', 'array', 'bisect', 'heapq',
        'weakref', 'copy', 'pprint', 'reprlib', 'numbers', 'inspect',
        'importlib', 'pkgutil', 'warnings', 'traceback', 'types', 'gc'
    }
    
    if module_name in stdlib_modules:
        return True
    
    # Check if it's an installed package (basic check)
    try:
        import importlib
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


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
    local_modules = set()
    module_imports = {}  # Track imports per module
    
    # First pass: collect all local module names and imports
    for file in path.rglob("*.py"):
        if any(pattern in str(file) for pattern in exclude_patterns):
            continue
        local_modules.add(file.stem)
        
        # Extract imports for this module
        try:
            content = file.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            imported_modules = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module)
            
            module_imports[file.stem] = imported_modules
        except (SyntaxError, UnicodeDecodeError):
            module_imports[file.stem] = set()
    
    # Second pass: build graph with filtering and cross-module detection
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
        imported_modules = module_imports.get(current_module, set())
        
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
                called_name = _extract_called_name(node, imported_modules)
                if called_name and not _is_external_function(called_name, local_modules):
                    # Check if this is a cross-module call
                    if "." in called_name:
                        target_module = called_name.split(".")[0]
                        if target_module != current_module and target_module in local_modules:
                            # This is a cross-module call within the codebase
                            if called_name not in graph.nodes():
                                graph.add_node(
                                    called_name, 
                                    cross_module=True,
                                    target_module=target_module,
                                    source_module=current_module
                                )
                            else:
                                # Update existing node with cross-module info
                                graph.nodes[called_name]['cross_module'] = True
                                graph.nodes[called_name]['target_module'] = target_module
                                graph.nodes[called_name]['source_module'] = current_module
                    
                    graph.add_edge(current_func, called_name)
    
    return graph


def _extract_called_name(call_node: ast.Call, imported_modules: Set[str]) -> Optional[str]:
    """Extract name of called function from an AST Call node.
    
    Only captures module-level function calls that are explicitly imported.
    """
    if isinstance(call_node.func, ast.Name):
        # This is a bare function call like foo()
        # Only capture if it's a user-defined function (not built-in)
        func_name = call_node.func.id
        # Skip built-ins and common functions
        built_ins = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'any', 'all', 'sum',
            'max', 'min', 'sorted', 'reversed', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'delattr', 'callable', 'type', 'isinstance', 'issubclass',
            'open', 'input', 'eval', 'exec', 'compile', 'globals', 'locals',
            'vars', 'dir', 'help', 'repr', 'ascii', 'format', 'vars'
        }
        if func_name not in built_ins:
            return func_name
        return None
        
    elif isinstance(call_node.func, ast.Attribute):
        # Handle method calls like obj.method() or module.function()
        parts = []
        node = call_node.func
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        
        if isinstance(node, ast.Name):
            parts.append(node.id)
            full_name = ".".join(reversed(parts))
            
            # Only capture module.function calls where module is imported
            # and it's exactly 2 parts (module.function)
            if len(parts) == 2:
                module_name, func_name = parts[1], parts[0]
                # Only capture if module is explicitly imported
                if module_name in imported_modules:
                    return full_name
            
            # Exclude method calls and longer chains
            return None
    
    return None


def scan_file(file_path: Path) -> nx.DiGraph:
    """Scan a single Python file and build call graph.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        NetworkX DiGraph representing function call relationships in file
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
    
    # Extract imports to know what modules are available
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    
    # For single file, assume only this module is local
    local_modules = {current_module}
    
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
            called_name = _extract_called_name(node, imported_modules)
            if called_name and not _is_external_function(called_name, local_modules):
                # Check if this is a cross-module call
                if "." in called_name:
                    target_module = called_name.split(".")[0]
                    if target_module != current_module and target_module in imported_modules:
                        # This is a cross-module call
                        if called_name not in graph.nodes():
                            graph.add_node(
                                called_name, 
                                cross_module=True,
                                target_module=target_module,
                                source_module=current_module
                            )
                        else:
                            # Update existing node with cross-module info
                            graph.nodes[called_name]['cross_module'] = True
                            graph.nodes[called_name]['target_module'] = target_module
                            graph.nodes[called_name]['source_module'] = current_module
                
                graph.add_edge(current_func, called_name)
    
    return graph