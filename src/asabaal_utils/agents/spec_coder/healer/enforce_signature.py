#!/usr/bin/env python3
"""
Signature Enforcer - Ensures functions match canonical signatures
Simplified version using string manipulation instead of AST
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SignatureEnforcer:
    """Enforces canonical signatures on generated functions."""
    
    def __init__(self, healer_dir: Path, catalog_path: str = "logic_catalog/functional_catalog.yaml"):
        self.healer_dir = Path(healer_dir)
        # Resolve catalog path relative to healer directory parent (generator directory)
        if not Path(catalog_path).is_absolute():
            catalog_path = str(self.healer_dir.parent / catalog_path)
        self.catalog_path = Path(catalog_path)
        self.catalog = self.load_catalog()
    
    def load_catalog(self) -> Dict:
        """Load the functional logic catalog."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")
        
        with open(self.catalog_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_canonical_signature(self, function_name: str) -> Optional[str]:
        """Get the canonical signature for a function from the catalog."""
        functions = self.catalog.get('functions', {})
        function_info = functions.get(function_name, {})
        
        if not function_info:
            return None
        
        # Build signature from catalog info
        params = function_info.get('parameters', [])
        param_strs = []
        
        for param in params:
            param_name = param.get('name', 'param')
            param_type = param.get('type', 'Any')
            default = param.get('default', None)
            
            if default is not None:
                param_strs.append(f"{param_name}: {param_type} = {default}")
            else:
                param_strs.append(f"{param_name}: {param_type}")
        
        signature = f"{function_name}({', '.join(param_strs)})"
        return signature
    
    def parse_signature(self, signature: str) -> Tuple[str, List[Dict]]:
        """Parse a signature string into name and parameters."""
        if '(' not in signature:
            return signature, []
        
        name_part = signature.split('(')[0].strip()
        params_part = signature.split('(')[1].rstrip(')').strip()
        
        params = []
        if params_part:
            for param_str in params_part.split(','):
                param_str = param_str.strip()
                if ':' in param_str:
                    param_name = param_str.split(':')[0].strip()
                    param_type = param_str.split(':', 1)[1].strip()
                    if '=' in param_type:
                        param_type = param_type.split('=')[0].strip()
                        default = param_str.split('=')[1].strip()
                    else:
                        default = None
                    params.append({
                        'name': param_name,
                        'type': param_type,
                        'default': default
                    })
                else:
                    params.append({
                        'name': param_str,
                        'type': 'Any',
                        'default': None
                    })
        
        return name_part, params
    
    def enforce_signature(self, py_src: str, function_name: str) -> str:
        """Rewrite a Python function to match its canonical signature using string manipulation."""
        # Get canonical signature
        canonical_sig = self.get_canonical_signature(function_name)
        if not canonical_sig:
            print(f"⚠️  No canonical signature found for {function_name}")
            return py_src
        
        # Parse the canonical signature to add smoke-safe defaults
        name, params = self.parse_signature(canonical_sig)
        
        # Add smoke-safe defaults to all parameters
        param_strs = []
        for param in params:
            param_name = param['name']
            param_type = param['type']
            
            # Add smoke-safe defaults based on type
            if param_type == 'int':
                default = '0'
            elif param_type == 'float':
                default = '0.0'
            elif param_type == 'str':
                default = '""'
            elif param_type == 'list':
                default = '[]'
            elif param_type == 'bool':
                default = 'False'
            else:
                default = 'None'
            
            param_strs.append(f"{param_name}: {param_type} = {default}")
        
        # Build new signature with defaults
        new_sig = f"{function_name}({', '.join(param_strs)})"
        
        # Split into lines
        lines = py_src.split('\n')
        
        # Find the function definition line
        func_line_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f'def {function_name}('):
                func_line_idx = i
                break
        
        if func_line_idx is None:
            print(f"⚠️  Function {function_name} not found in source")
            return py_src
        
        # Get the indentation of the original function
        original_line = lines[func_line_idx]
        indent = len(original_line) - len(original_line.lstrip())
        
        # Replace the signature line
        new_signature = ' ' * indent + f'def {new_sig}:'
        lines[func_line_idx] = new_signature
        
        return '\n'.join(lines)
    
    def add_smoke_safe_defaults(self, py_src: str, function_name: str) -> str:
        """Add smoke-safe defaults to function parameters."""
        # This is handled by the signature enforcement
        return py_src
    
    def add_impl_wrapper(self, py_src: str, function_name: str) -> str:
        """Add a private _impl() wrapper for strict validation."""
        # For now, skip the complex wrapper implementation
        return py_src


def main():
    """Test signature enforcement on a sample function."""
    from pathlib import Path
    enforcer = SignatureEnforcer(Path(__file__).parent)
    
    # Test with a sample function
    sample_code = '''def export_as_midi(such, lists, are, invalid):
    """Test function."""
    pass
'''
    
    print("Original code:")
    print(sample_code)
    
    enforced_code = enforcer.enforce_signature(sample_code, "export_as_midi")
    
    print("\nEnforced code:")
    print(enforced_code)


if __name__ == "__main__":
    main()