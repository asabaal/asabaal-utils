import ast
import sys
import pkgutil
import fnmatch
import json
from pathlib import Path
import networkx as nx
from typing import Set, Optional, List, Dict

# Function flow analysis imports
# These will be imported when needed to avoid circular dependencies


def _should_exclude_file(file_path: Path, exclude_patterns: Set[str]) -> bool:
    """Check if a file should be excluded based on patterns.
    
    Args:
        file_path: Path to the file
        exclude_patterns: Set of patterns to exclude
        
    Returns:
        True if file should be excluded, False otherwise
    """
    # Convert to relative path for pattern matching
    path_str = str(file_path)
    
    # Check each pattern
    for pattern in exclude_patterns:
        # Use fnmatch for glob-style pattern matching
        if fnmatch.fnmatch(path_str, f"*{pattern}*"):
            return True
        # Also check individual path components
        for part in file_path.parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    
    return False


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


def scan_directory(path: Path, exclude_patterns: Optional[Set[str]] = None, 
                   analyze_functions: bool = False, output_dir: Optional[Path] = None) -> nx.DiGraph:
    """Scan directory recursively and build call graph.
    
    Args:
        path: Directory path to scan
        exclude_patterns: Set of directory/file patterns to exclude
        analyze_functions: Whether to perform intra-function flow analysis
        output_dir: Directory to save function flow analysis results
        
    Returns:
        NetworkX DiGraph representing function call relationships
    """
    if exclude_patterns is None:
        exclude_patterns = {"__pycache__", ".git", ".venv", "venv", "node_modules", "flowscope_analysis"}
    
    graph = nx.DiGraph()
    local_modules = set()
    module_imports = {}  # Track imports per module
    
    # First pass: collect all local module names and imports
    for file in path.rglob("*.py"):
        if _should_exclude_file(file, exclude_patterns):
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
        if _should_exclude_file(file, exclude_patterns):
            continue
            
        try:
            content = file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError):
            continue

        current_module = file.stem
        imported_modules = module_imports.get(current_module, set())
        
        # Build function registry for this module
        registry = _build_function_registry(tree, current_module, imported_modules)
        
        # First pass: find all function definitions in this file
        function_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_nodes.append(node)
        
        # Process each function separately to avoid scope confusion
        for func_node in function_nodes:
            if isinstance(func_node, ast.FunctionDef):
                func_name = f"{current_module}.{func_node.name}"
                graph.add_node(func_name, file=str(file), line=func_node.lineno)
            else:  # AsyncFunctionDef
                func_name = f"{current_module}.{func_node.name}"
                graph.add_node(func_name, file=str(file), line=func_node.lineno, async_func=True)
            
            # Look for calls only within this function
            for node in ast.walk(func_node):
                if isinstance(node, ast.Call):
                    called_name = _extract_called_name(node, registry)
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
                        
                        graph.add_edge(func_name, called_name, line=node.lineno)
    
    # Perform function flow analysis if requested
    if analyze_functions:
        if output_dir is None:
            output_dir = Path.cwd()
        # If output_dir is a file path, use its parent for function flows
        elif output_dir.is_file():
            output_dir = output_dir.parent
        _analyze_function_flows(path, exclude_patterns, output_dir)
    
    return graph


def _analyze_function_flows(path: Path, exclude_patterns: Set[str], output_dir: Path):
    """Analyze function flows for all Python files in the directory.
    
    Args:
        path: Directory path to analyze
        exclude_patterns: Set of directory/file patterns to exclude
        output_dir: Directory to save function flow analysis results
    """
    # Import new function flow builder
    try:
        from .function_flow_builder import generate_function_flow
    except ImportError:
        print("Warning: Function flow builder not available. Skipping function flow analysis.")
        return
    
    # Create output directory for function flows JSON files
    function_flows_dir = output_dir / "function_flows"
    function_flows_dir.mkdir(parents=True, exist_ok=True)
    
    print("Analyzing function flows...")
    
    # Analyze each file
    for file in path.rglob("*.py"):
        if _should_exclude_file(file, exclude_patterns):
            continue
        
        try:
            module_name = file.stem
            source_code = file.read_text(encoding="utf-8")
            
            # Parse AST to find all functions
            import ast
            tree = ast.parse(source_code)
            
            function_flows = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    try:
                        # Generate function flow using new builder
                        function_flow = generate_function_flow(source_code, node.name)
                        function_flows[node.name] = function_flow
                    except Exception as e:
                        print(f"    Error analyzing function {node.name}: {e}")
            
            if function_flows:
                print(f"  Analyzed {len(function_flows)} functions in {module_name}")
                
                # Save module data
                module_data = {
                    'module': module_name,
                    'function_flows': function_flows
                }
                
                import json
                output_file = function_flows_dir / f"{module_name}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(module_data, f, indent=2)
                
                print(f"    Saved to {output_file}")
        
        except Exception as e:
            print(f"  Error analyzing {file}: {e}")
    
    # Generate HTML visualizations from JSON files
    try:
        from .function_flow_renderer import FunctionFlowRenderer
        print("Generating HTML visualizations...")
        renderer = FunctionFlowRenderer(output_dir)
        
        # Process all JSON files and convert to HTML
        for json_file in function_flows_dir.glob("*.json"):
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    module_data = json.load(f)
                
                module_name = module_data['module']
                function_flows = module_data['function_flows']
                
                # Render all function flows for this module
                renderer.render_module_function_flows(function_flows, module_name)
                print(f"    Generated HTML for {module_name}")
            except Exception as e:
                print(f"    Error rendering {json_file.name}: {e}")
        
        print("HTML visualizations generated.")
    except ImportError:
        print("Warning: Function flow renderer not available. Only JSON files generated.")
    except Exception as e:
        print(f"Error generating HTML visualizations: {e}")
    
    print(f"Function flow analysis complete. Results saved to {function_flows_dir}")


class FunctionRegistry:
    """Registry to track all defined functions in a module for call resolution."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.functions = set()  # All function names in this module
        self.classes = {}  # Class name -> set of method names
        self.imported_modules = set()  # Imported module names
    
    def add_function(self, func_name: str, is_class_method: bool = False, class_name: Optional[str] = None):
        """Add a function to the registry."""
        if is_class_method and class_name:
            if class_name not in self.classes:
                self.classes[class_name] = set()
            self.classes[class_name].add(func_name)
        else:
            self.functions.add(func_name)
    
    def is_local_function(self, func_name: str) -> bool:
        """Check if a function is defined in this module."""
        return func_name in self.functions
    
    def is_class_method(self, func_name: str, class_name: Optional[str] = None) -> bool:
        """Check if a function is a method of a class in this module."""
        if class_name:
            return class_name in self.classes and func_name in self.classes[class_name]
        # Check if it's a method in any class
        for methods in self.classes.values():
            if func_name in methods:
                return True
        return False
    
    def get_all_function_names(self) -> Set[str]:
        """Get all function names defined in this module."""
        all_names = self.functions.copy()
        for methods in self.classes.values():
            all_names.update(methods)
        return all_names


def _build_function_registry(tree: ast.AST, module_name: str, imported_modules: Set[str]) -> FunctionRegistry:
    """Build a registry of all functions defined in this module."""
    registry = FunctionRegistry(module_name)
    registry.imported_modules = imported_modules
    
    # Track current class context
    current_class = None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            current_class = node.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_method = current_class is not None
            registry.add_function(node.name, is_method, current_class or "")
        # Reset class context when we leave the class
        elif isinstance(node, ast.ClassDef) and current_class:
            # This handles nested classes - we'll reset when we encounter the next class or function at module level
            pass
    
    return registry


def _extract_called_name(call_node: ast.Call, registry: FunctionRegistry) -> Optional[str]:
    """Extract name of called function from an AST Call node.
    
    Enhanced to capture same-module function calls through registry lookup.
    """
    if isinstance(call_node.func, ast.Name):
        # This is a bare function call like foo()
        func_name = call_node.func.id
        
        # Skip built-ins and common functions
        built_ins = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
            'range', 'enumerate', 'zip', 'map', 'filter', 'any', 'all', 'sum',
            'max', 'min', 'sorted', 'reversed', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'delattr', 'callable', 'type', 'isinstance', 'issubclass',
            'open', 'input', 'eval', 'exec', 'compile', 'globals', 'locals',
            'vars', 'dir', 'help', 'repr', 'ascii', 'format', 'vars', 'super',
            'property', 'staticmethod', 'classmethod', 'next', 'iter', 'bool'
        }
        
        if func_name in built_ins:
            return None
        
        # Check if this is a local function call
        if registry.is_local_function(func_name):
            return f"{registry.module_name}.{func_name}"
        
        # Check if this is a class method call (without self)
        if registry.is_class_method(func_name):
            return f"{registry.module_name}.{func_name}"
        
        # Not a local function, skip it
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
            
            # Handle self.method() calls
            if len(parts) >= 2 and parts[-1] == 'self':
                method_name = parts[0]
                
                # Check if this is a valid method in any class
                if registry.is_class_method(method_name):
                    full_method_name = f"{registry.module_name}.{method_name}"
                    return full_method_name
                
                # Even if not in registry, treat as local method call
                full_method_name = f"{registry.module_name}.{method_name}"
                return full_method_name
            
            # Handle self.attribute.method() calls
            elif len(parts) >= 3 and parts[-1] == 'self':
                method_name = parts[0]
                attribute_name = parts[1]
                
                # This could be self.other_class.method() - treat as cross-module call
                if attribute_name in registry.imported_modules:
                    return f"{attribute_name}.{method_name}"
                
                # Or it could be self.instance.method() where instance is of a local class
                if attribute_name in registry.classes:
                    if method_name in registry.classes[attribute_name]:
                        return f"{registry.module_name}.{method_name}"
                
                # Fallback: treat as cross-module call
                return f"{attribute_name}.{method_name}"
            
            # Handle module.function() calls
            elif len(parts) == 2:
                module_name, func_name = parts[1], parts[0]
                
                # Only capture if module is imported
                if module_name in registry.imported_modules:
                    return full_name
                
                # Check if it's a same-module call with module prefix
                if module_name == registry.module_name:
                    return f"{registry.module_name}.{func_name}"
            
            # Handle class.method() calls (direct class method calls)
            elif len(parts) == 2:
                class_name, method_name = parts[1], parts[0]
                
                # Check if this is a local class method call
                if class_name in registry.classes and method_name in registry.classes[class_name]:
                    return f"{registry.module_name}.{method_name}"
            
            # Handle longer chains like obj.attr.method() - try to resolve
            elif len(parts) >= 3:
                # Look for patterns that might indicate local function calls
                method_name = parts[0]
                
                # If the last part is a known local class, this might be a method call
                if parts[-1] in registry.classes:
                    if method_name in registry.classes[parts[-1]]:
                        return f"{registry.module_name}.{method_name}"
                
                # If the method name is a local function, capture it
                if registry.is_local_function(method_name):
                    return f"{registry.module_name}.{method_name}"
            
            # Default: exclude complex method chains
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
    
    # Build function registry for this module
    registry = _build_function_registry(tree, current_module, imported_modules)
    
    # For single file, assume only this module is local
    local_modules = {current_module}
    
    # First pass: find all function definitions
    function_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_nodes.append(node)
    
    # Process each function separately to avoid scope confusion
    for func_node in function_nodes:
        if isinstance(func_node, ast.FunctionDef):
            func_name = f"{current_module}.{func_node.name}"
            graph.add_node(func_name, file=str(file_path), line=func_node.lineno)
        else:  # AsyncFunctionDef
            func_name = f"{current_module}.{func_node.name}"
            graph.add_node(func_name, file=str(file_path), line=func_node.lineno, async_func=True)
        
        # Look for calls only within this function
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                called_name = _extract_called_name(node, registry)
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
                    
                    graph.add_edge(func_name, called_name, line=node.lineno)
    
    return graph