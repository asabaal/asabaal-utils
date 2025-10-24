#!/usr/bin/env python3
"""
Build Logic Catalog - Build YAML catalog from aggregated behaviors
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

def load_aggregated_behaviors(aggregated_file: Path) -> Dict[str, Any]:
    """Load aggregated behaviors from JSON file."""
    with open(aggregated_file, 'r') as f:
        return json.load(f)

def normalize_function_name(func_name: str) -> str:
    """Normalize function name to snake_case."""
    # Convert camelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', func_name)
    snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    # Remove common prefixes and clean up
    prefixes_to_remove = ['test_', 'mock_', 'fake_']
    for prefix in prefixes_to_remove:
        if snake_case.startswith(prefix):
            snake_case = snake_case[len(prefix):]
    
    # Remove any remaining test-related suffixes
    suffixes_to_remove = ['_test', '_mock', '_fake']
    for suffix in suffixes_to_remove:
        if snake_case.endswith(suffix):
            snake_case = snake_case[:-len(suffix)]
    
    return snake_case

def infer_return_type(behaviors: List[str], validation_rules: List[str]) -> str:
    """infer return type from behaviors and validation rules."""
    all_text = ' '.join(behaviors + validation_rules).lower()
    
    # Look for return type patterns
    if any(word in all_text for word in ['return bool', 'returns bool', 'should return true', 'should return false']):
        return 'bool'
    elif any(word in all_text for word in ['return list', 'returns list', 'should return list']):
        return 'list'
    elif any(word in all_text for word in ['return dict', 'returns dict', 'should return dict']):
        return 'dict'
    elif any(word in all_text for word in ['return str', 'returns str', 'should return string']):
        return 'str'
    elif any(word in all_text for word in ['return int', 'returns int', 'should return int']):
        return 'int'
    elif any(word in all_text for word in ['return float', 'returns float', 'should return float']):
        return 'float'
    elif any(word in all_text for word in ['return bytes', 'returns bytes', 'should return bytes']):
        return 'bytes'
    elif any(word in all_text for word in ['midi file', 'midi data', 'bytes data']):
        return 'bytes'
    else:
        return 'Any'

def extract_parameter_info(parameters: List[str], behaviors: List[str]) -> List[Dict[str, Any]]:
    """Extract detailed parameter information."""
    param_info = []
    
    # Common parameter patterns and their types
    param_patterns = {
        'tempo': {'type': 'int', 'default': None, 'description': 'Tempo in BPM'},
        'bpm': {'type': 'int', 'default': None, 'description': 'Beats per minute'},
        'time_signature': {'type': 'str', 'default': None, 'description': 'Time signature (e.g., "4/4")'},
        'pattern': {'type': 'list', 'default': None, 'description': 'Rhythm pattern'},
        'duration': {'type': 'float', 'default': None, 'description': 'Duration in seconds'},
        'length': {'type': 'int', 'default': None, 'description': 'Length in beats or measures'},
        'velocity': {'type': 'int', 'default': None, 'description': 'Note velocity (0-127)'},
        'accent_pattern': {'type': 'list', 'default': None, 'description': 'Accent pattern'},
        'pulse_count': {'type': 'int', 'default': None, 'description': 'Number of pulses'},
        'resolution': {'type': 'int', 'default': None, 'description': 'Resolution (PPQ)'},
        'ticks': {'type': 'int', 'default': None, 'description': 'Number of ticks'},
        'measures': {'type': 'int', 'default': None, 'description': 'Number of measures'},
        'beats': {'type': 'int', 'default': None, 'description': 'Number of beats'},
        'divisions': {'type': 'int', 'default': None, 'description': 'Number of divisions'},
    }
    
    for param in parameters:
        param_name = normalize_function_name(param)
        
        # Check if we have predefined info
        if param_name in param_patterns:
            info = param_patterns[param_name].copy()
            info['name'] = param_name
        else:
            # Try to infer type from context
            all_text = ' '.join(behaviors).lower()
            if any(word in all_text for word in [f'{param} list', f'{param} array']):
                param_type = 'list'
            elif any(word in all_text for word in [f'{param} string', f'{param} str']):
                param_type = 'str'
            elif any(word in all_text for word in [f'{param} int', f'{param} integer']):
                param_type = 'int'
            elif any(word in all_text for word in [f'{param} float', f'{param} decimal']):
                param_type = 'float'
            elif any(word in all_text for word in [f'{param} bool', f'{param} boolean']):
                param_type = 'bool'
            else:
                param_type = 'Any'
            
            info = {
                'name': param_name,
                'type': param_type,
                'default': None,
                'description': f'Parameter {param_name}'
            }
        
        param_info.append(info)
    
    return param_info

def categorize_function(func_name: str, behaviors: List[str]) -> str:
    """Categorize function based on name and behaviors."""
    name_lower = func_name.lower()
    behaviors_text = ' '.join(behaviors).lower()
    
    if any(word in name_lower or word in behaviors_text for word in ['export', 'save', 'write']):
        return 'export'
    elif any(word in name_lower or word in behaviors_text for word in ['import', 'load', 'read']):
        return 'import'
    elif any(word in name_lower or word in behaviors_text for word in ['validate', 'check', 'verify']):
        return 'validation'
    elif any(word in name_lower or word in behaviors_text for word in ['create', 'generate', 'build']):
        return 'creation'
    elif any(word in name_lower or word in behaviors_text for word in ['convert', 'transform']):
        return 'conversion'
    elif any(word in name_lower or word in behaviors_text for word in ['calculate', 'compute']):
        return 'calculation'
    else:
        return 'utility'

def extract_error_conditions(behaviors: List[str], validation_rules: List[str]) -> List[str]:
    """Extract error conditions from behaviors and validation rules."""
    error_conditions = []
    all_text = ' '.join(behaviors + validation_rules).lower()
    
    # Look for error patterns
    error_patterns = [
        'should raise',
        'should throw',
        'should error',
        'should fail',
        'invalid',
        'error when',
        'exception when',
        'must be',
        'cannot be',
        'should not'
    ]
    
    for rule in validation_rules:
        rule_lower = rule.lower()
        if any(pattern in rule_lower for pattern in error_patterns):
            error_conditions.append(rule)
    
    return error_conditions

def build_function_entry(function_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a single function entry for the catalog."""
    func_name = function_data['function_name']
    normalized_name = normalize_function_name(func_name)
    
    # Extract and clean behaviors
    behaviors = [b.strip() for b in function_data['behaviors'] if b.strip()]
    
    # Build parameter info
    parameters = extract_parameter_info(function_data['parameters'], behaviors)
    
    # Infer return type
    return_type = infer_return_type(behaviors, function_data['validation_rules'])
    
    # Categorize function
    category = categorize_function(func_name, behaviors)
    
    # Extract error conditions
    error_conditions = extract_error_conditions(behaviors, function_data['validation_rules'])
    
    # Build the entry
    entry = {
        'name': normalized_name,
        'original_name': func_name,
        'category': category,
        'description': behaviors[0] if behaviors else f"Function {normalized_name}",
        'behaviors': behaviors,
        'parameters': parameters,
        'return_type': return_type,
        'validation_rules': function_data['validation_rules'],
        'error_conditions': error_conditions,
        'test_coverage': {
            'test_names': function_data['test_names'],
            'file_paths': function_data['file_paths'],
            'sources': function_data['sources'],
            'average_alignment_score': function_data.get('average_alignment_score', 0)
        },
        'metadata': {
            'total_behaviors': len(behaviors),
            'total_validation_rules': len(function_data['validation_rules']),
            'has_specified_tests': 'specified' in function_data['sources'],
            'has_additional_tests': 'additional' in function_data['sources']
        }
    }
    
    return entry

def build_catalog(aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the complete functional catalog."""
    functions = aggregated_data['functions']
    
    # Build function entries
    function_entries = []
    for func_data in functions:
        entry = build_function_entry(func_data)
        function_entries.append(entry)
    
    # Group functions by category
    categories = defaultdict(list)
    for entry in function_entries:
        categories[entry['category']].append(entry['name'])
    
    # Build catalog structure
    catalog = {
        'metadata': {
            'catalog_version': '1.0.0',
            'generated_at': '2025-10-14',
            'total_functions': len(function_entries),
            'categories': dict(categories),
            'source_metadata': aggregated_data['metadata']
        },
        'functions': {entry['name']: entry for entry in function_entries}
    }
    
    return catalog

def save_catalog(catalog: Dict[str, Any], output_file: Path):
    """Save catalog to YAML file."""
    with open(output_file, 'w') as f:
        yaml.dump(catalog, f, default_flow_style=False, indent=2, sort_keys=False)
    
    print(f"Saved functional catalog to: {output_file}")
    print(f"Total functions: {catalog['metadata']['total_functions']}")
    print(f"Categories: {list(catalog['metadata']['categories'].keys())}")

def main():
    """Main catalog building process."""
    import os
    
    # Use BASE_DIR environment variable if set, otherwise use current directory
    base_dir = Path(os.environ.get('BASE_DIR', Path.cwd()))
    logic_catalog_dir = Path(os.environ.get('OUTPUT_DIR', base_dir / "logic_catalog"))
    logic_catalog_dir.mkdir(parents=True, exist_ok=True)
    
    aggregated_file = logic_catalog_dir / "aggregated_behaviors.json"
    output_file = logic_catalog_dir / "functional_catalog.yaml"
    
    print("=== Building Functional Logic Catalog ===")
    
    if not aggregated_file.exists():
        print(f"Aggregated behaviors file not found: {aggregated_file}")
        print("Please run aggregate_behaviors.py first.")
        return
    
    # Load aggregated behaviors
    aggregated_data = load_aggregated_behaviors(aggregated_file)
    print(f"Loaded aggregated behaviors for {aggregated_data['metadata']['total_functions']} functions")
    
    # Build catalog
    catalog = build_catalog(aggregated_data)
    print(f"Built catalog with {catalog['metadata']['total_functions']} functions")
    
    # Save catalog
    save_catalog(catalog, output_file)
    
    print("\n=== Catalog Building Complete ===")

if __name__ == "__main__":
    main()