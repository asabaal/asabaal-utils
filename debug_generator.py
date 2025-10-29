#!/usr/bin/env python3

import ast
import sys
from pathlib import Path
sys.path.append('src')

from asabaal_utils.flowscope.scanner import scan_file, _extract_called_name, _is_external_function

# Test scanning just the generator file
generator_file = Path('src/asabaal_utils/agents/spec_coder/generator.py')
print(f"Scanning {generator_file}")

graph = scan_file(generator_file)

# Find generate_from_spec function
target_func = 'generator.generate_from_spec'
if target_func in graph.nodes():
    print(f"\nFound {target_func}")
    print(f"Out-degree: {graph.out_degree(target_func)}")
    print(f"Outgoing edges: {list(graph.successors(target_func))}")
else:
    print(f"\n{target_func} NOT found")
    print("Functions with 'generate' in name:")
    for node in graph.nodes():
        if 'generate' in node:
            print(f"  - {node}")

# Let's also manually parse the file to see what's happening
print(f"\n=== Manual AST Analysis ===")
content = generator_file.read_text()
tree = ast.parse(content)

current_func = None
imported_modules = set()
call_count = 0

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        func_name = f"generator.{node.name}"
        if func_name == target_func:
            print(f"Found target function at line {node.lineno}")
            current_func = func_name
            # Let's walk through this function's body specifically
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_count += 1
                    called_name = _extract_called_name(child, imported_modules, 'generator')
                    if called_name:
                        is_external = _is_external_function(called_name, {'generator'})
                        print(f"  Call {call_count}: {called_name} (external: {is_external})")
                    else:
                        print(f"  Call {call_count}: NOT EXTRACTED - {ast.dump(child.func)[:80]}...")
            break
    elif current_func and isinstance(node, ast.FunctionDef) and node.name != 'generate_from_spec':
        # We've moved to next function
        break

print(f"Total calls found in generate_from_spec: {call_count}")