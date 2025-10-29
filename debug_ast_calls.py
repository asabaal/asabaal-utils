#!/usr/bin/env python3
"""Debug script to test AST parsing of generator.py specifically."""

import ast
import sys
from pathlib import Path

def debug_ast_calls():
    # Read the generator file
    generator_path = Path("src/asabaal_utils/agents/spec_coder/generator.py")
    if not generator_path.exists():
        print(f"ERROR: {generator_path} not found!")
        return
    
    content = generator_path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    
    # Find imports
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    
    print(f"Imported modules: {imported_modules}")
    
    # Find generate_from_spec function and analyze its calls
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "generate_from_spec":
            print(f"\nFound function: {node.name} at line {node.lineno}")
            
            # Find all calls within this function
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_name = extract_called_name_debug(child, imported_modules, "generator")
                    if call_name:
                        calls.append((call_name, child.lineno))
            
            print(f"Found {len(calls)} calls:")
            for call_name, line in calls:
                print(f"  Line {line}: {call_name}")
            
            break

def extract_called_name_debug(call_node, imported_modules, current_module):
    """Debug version of _extract_called_name that shows what's happening."""
    print(f"\nAnalyzing call at line {call_node.lineno}: {ast.dump(call_node.func)}")
    
    if isinstance(call_node.func, ast.Name):
        # This is a bare function call like foo()
        func_name = call_node.func.id
        print(f"  Bare call: {func_name}")
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
        
        print(f"  Parts: {parts}")
        
        if isinstance(node, ast.Name):
            parts.append(node.id)
            full_name = ".".join(reversed(parts))
            print(f"  Full name: {full_name}")
            
            # Capture self.method() and self._method() calls (internal methods) FIRST
            # Only capture direct self.method() calls, not self.attribute.method()
            if len(parts) == 2 and parts[-1] == 'self':
                method_name = parts[0]
                # Return with current module prefix
                full_method_name = f"{current_module}.{method_name}"
                print(f"  Self method: {full_method_name}")
                return full_method_name
            
            # Capture self.attribute.method() calls as cross-module calls
            elif len(parts) >= 3 and parts[-1] == 'self':
                # This is like self.spec_parser.parse_file
                # Treat as cross-module call to attribute.method
                method_name = parts[0]
                attribute_name = parts[1]
                cross_module_call = f"{attribute_name}.{method_name}"
                print(f"  Self attribute method: {cross_module_call}")
                return cross_module_call
            
            # Capture module.function calls where module is imported
            elif len(parts) == 2:
                module_name, func_name = parts[1], parts[0]
                print(f"  Module function: {module_name}.{func_name}")
                # Only capture if module is explicitly imported
                if module_name in imported_modules:
                    return full_name
                else:
                    print(f"    Module {module_name} not in imported modules: {imported_modules}")
            
            # Exclude other method calls and longer chains
            return None
    
    return None

if __name__ == "__main__":
    debug_ast_calls()