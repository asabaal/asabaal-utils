#!/usr/bin/env python3
"""Debug the scanner error."""

import ast
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asabaal_utils.flowscope.scanner import _extract_called_name

def debug_extract_called_name():
    # Test the function with some sample AST nodes
    code = """
    self.spec_parser.parse_file(spec_path)
    self._generate_source_code(spec, output_dir)
    """
    tree = ast.parse(code)
    
    imported_modules = {'spec_parser', 'ollama_client'}
    current_module = 'generator'
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            print(f"Analyzing call: {ast.dump(node)}")
            try:
                called_name = _extract_called_name(node, imported_modules, current_module)
                print(f"Result: {called_name}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    debug_extract_called_name()