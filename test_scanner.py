#!/usr/bin/env python3

import ast
import sys
sys.path.insert(0, 'src')
from asabaal_utils.flowscope.scanner import _extract_called_name

# Test the extraction function
code = '''
class TestClass:
    def test_method(self):
        self._generate_source_code(spec, output_dir)
        self._generate_documentation(spec, output_dir)
'''

tree = ast.parse(code)
imported_modules = set()
current_module = "test"

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        result = _extract_called_name(node, imported_modules, current_module)
        print(f"Call result: {result}")
        # Debug the AST structure
        if isinstance(node.func, ast.Attribute):
            parts = []
            attr_node = node.func
            while isinstance(attr_node, ast.Attribute):
                parts.append(attr_node.attr)
                attr_node = attr_node.value
            if isinstance(attr_node, ast.Name):
                parts.append(attr_node.id)
            print(f"Parts: {parts}, Reversed: {list(reversed(parts))}")