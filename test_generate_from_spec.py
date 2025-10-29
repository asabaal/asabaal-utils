#!/usr/bin/env python3

import ast
import sys
sys.path.insert(0, 'src')
from asabaal_utils.flowscope.scanner import _extract_called_name

# Test the exact code from generate_from_spec
code = '''
def generate_from_spec(self, spec_path: Path, output_dir):
    source_file = self._generate_source_code(spec, output_dir)
    doc_file = self._generate_documentation(spec, output_dir)
    test_files = self._generate_tests(spec, output_dir)
    ci_files = self._generate_ci_config(spec, output_dir)
    validation_file = self._generate_validation_script(output_dir)
    requirements_file = self._generate_requirements_file(output_dir)
'''

tree = ast.parse(code)
imported_modules = set()
current_module = "generator"

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        result = _extract_called_name(node, imported_modules, current_module)
        print(f"Call: {result}")