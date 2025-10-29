#!/usr/bin/env python3
"""Debug the exact scanner logic step by step."""

import ast
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import _extract_called_name, _is_external_function

def debug_scanner_logic():
    # Read and parse the generator file
    generator_path = Path("src/asabaal_utils/agents/spec_coder/generator.py")
    content = generator_path.read_text(encoding="utf-8")
    tree = ast.parse(content)
    
    current_module = "generator"
    current_func = None
    
    # Extract imports
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    
    local_modules = {current_module}
    
    print(f"Imported modules: {imported_modules}")
    print(f"Local modules: {local_modules}")
    
    # Walk through the AST and simulate the scanner logic
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "generate_from_spec":
            current_func = f"{current_module}.{node.name}"
            print(f"\nCurrent function: {current_func}")
            
            # Look for calls within this function
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    called_name = _extract_called_name(child, imported_modules, current_module)
                    if called_name:
                        print(f"\n  Found call: {called_name}")
                        
                        is_external = _is_external_function(called_name, local_modules)
                        print(f"    Is external: {is_external}")
                        
                        if not is_external:
                            print(f"    Would add edge: {current_func} -> {called_name}")
                            
                            # Check cross-module logic
                            if "." in called_name:
                                target_module = called_name.split(".")[0]
                                is_cross_module = (target_module != current_module and target_module in imported_modules)
                                print(f"    Cross-module check: {target_module} != {current_module} and {target_module} in {imported_modules} = {is_cross_module}")
                        else:
                            print(f"    Skipping (external function)")

if __name__ == "__main__":
    debug_scanner_logic()