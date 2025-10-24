#!/usr/bin/env python3
"""
Aggregate Behaviors - Extract and merge behaviors from alignment reports
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def load_alignment_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    """Load all alignment reports from the reports directory."""
    reports = []
    
    # Look for JSON alignment reports
    for report_file in reports_dir.glob("*_alignment_report.json"):
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
                reports.append(report)
                print(f"Loaded: {report_file.name}")
        except Exception as e:
            print(f"Error loading {report_file}: {e}")
    
    return reports

def extract_behaviors_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract behaviors from a single alignment report."""
    behaviors = []
    
    # Extract from requirement coverage (specified tests)
    requirement_coverage = report.get('requirement_coverage', {})
    
    for req_id, req_data in requirement_coverage.items():
        tests = req_data.get('tests', [])
        
        for test_data in tests:
            # Extract function name from test name
            test_name = test_data.get('test_name', '')
            function_name = extract_function_name_from_test(test_name)
            
            behavior = {
                'test_name': test_name,
                'source': 'specified',
                'file_path': test_data.get('test_file', ''),
                'function_name': function_name,
                'implied_behavior': test_data.get('implied_behavior', ''),
                'alignment_score': test_data.get('confidence', 0),
                'alignment_details': f"Alignment type: {test_data.get('alignment_type', '')}",
                'validation_rules': extract_validation_rules(test_data.get('implied_behavior', '')),
                'parameters': extract_parameters(test_data.get('implied_behavior', ''))
            }
            behaviors.append(behavior)
    
    # Extract from additional tests
    additional_tests = report.get('additional_tests', [])
    
    for test_data in additional_tests:
        # Extract function name from test name
        test_name = test_data.get('test_name', '')
        function_name = extract_function_name_from_test(test_name)
        
        behavior = {
            'test_name': test_name,
            'source': 'additional',
            'file_path': test_data.get('test_file', ''),
            'function_name': function_name,
            'implied_behavior': test_data.get('implied_behavior', ''),
            'alignment_score': 0,  # Additional tests don't have alignment scores
            'alignment_details': test_data.get('match_reason', 'Additional test not specified in OpenSpec'),
            'validation_rules': extract_validation_rules(test_data.get('implied_behavior', '')),
            'parameters': extract_parameters(test_data.get('implied_behavior', ''))
        }
        behaviors.append(behavior)
    
    return behaviors

def extract_function_name_from_test(test_name: str) -> str:
    """Extract function name from test name."""
    # Handle edge case of just "test"
    if test_name == 'test' or not test_name:
        return ''
    
    # Handle case where test_ is at the end (add_function_test)
    if test_name.endswith('_test'):
        name_part = test_name[:-5]  # Remove '_test'
    # Remove test_ prefix and convert to function name
    elif test_name.startswith('test_'):
        name_part = test_name[5:]  # Remove 'test_'
    else:
        name_part = test_name
    
    # Handle common test patterns:
    # test_functionName_scenario -> functionName
    # test_function_happy_path -> function  
    # test_function_edge_cases -> function
    # test_apply_accent_pattern_happy_path -> apply_accent_pattern
    
    # Split by common separators
    parts = name_part.split('_')
    
    # Remove common test suffixes
    suffixes_to_remove = ['happy', 'path', 'edge', 'cases', 'invalid', 'inputs', 'type', 'safety']
    filtered_parts = []
    
    for part in parts:
        if part.lower() not in suffixes_to_remove:
            filtered_parts.append(part)
    
    # Rejoin and normalize
    if filtered_parts:
        function_name = '_'.join(filtered_parts)
    else:
        function_name = name_part
    
    # Handle camelCase to snake_case
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', function_name)
    snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    # Clean up common prefixes
    prefixes_to_remove = ['generate_', 'apply_', 'export_']
    for prefix in prefixes_to_remove:
        if snake_case.startswith(prefix):
            return snake_case  # Keep the meaningful part
    
    return snake_case

def extract_validation_rules(behavior_text: str) -> List[str]:
    """Extract validation rules from behavior text."""
    rules = []
    
    # Look for validation patterns
    validation_keywords = [
        'should', 'must', 'expect', 'assert', 'validate', 'check',
        'verify', 'ensure', 'require', 'throw', 'raise', 'return'
    ]
    
    sentences = behavior_text.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if any(keyword in sentence.lower() for keyword in validation_keywords):
            rules.append(sentence)
    
    return rules

def extract_parameters(behavior_text: str) -> List[str]:
    """Extract parameter references from behavior text."""
    parameters = []
    
    # Look for parameter patterns
    import re
    
    # Pattern for words that might be parameters (often followed by specific values)
    param_patterns = [
        r'\b(\w+)\s*=\s*["\']?\w+["\']?',  # param = value
        r'\b(\w+)\s+of\s+\w+',             # param of type
        r'\b(\w+)\s+as\s+\w+',             # param as type
        r'with\s+(\w+)',                   # with param
        r'using\s+(\w+)',                  # using param
    ]
    
    for pattern in param_patterns:
        matches = re.findall(pattern, behavior_text, re.IGNORECASE)
        parameters.extend(matches)
    
    # Remove duplicates and common non-parameter words
    exclude_words = {'test', 'should', 'must', 'expect', 'assert', 'value', 'result', 'error'}
    parameters = list(set(p for p in parameters if p.lower() not in exclude_words))
    
    return parameters

def merge_behaviors(behaviors_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merge behaviors from multiple reports, deduplicating by function name."""
    
    # Group by function name
    function_groups = defaultdict(list)
    
    for behaviors in behaviors_list:
        for behavior in behaviors:
            func_name = behavior.get('function_name', 'unknown')
            if func_name and func_name != 'unknown':
                function_groups[func_name].append(behavior)
    
    # Merge behaviors for each function
    merged_behaviors = []
    
    for func_name, func_behaviors in function_groups.items():
        merged = {
            'function_name': func_name,
            'test_name': func_behaviors[0].get('test_name', ''),  # Keep first test name for compatibility
            'file_paths': list(set(b.get('file_path') for b in func_behaviors if b.get('file_path'))),
            'test_names': [b.get('test_name') for b in func_behaviors],
            'sources': list(set(b.get('source') for b in func_behaviors)),
            'behaviors': [b.get('implied_behavior', '') for b in func_behaviors if b.get('implied_behavior')],
            'validation_rules': [],
            'parameters': [],
            'alignment_scores': [b.get('alignment_score', 0) for b in func_behaviors if b.get('alignment_score') is not None and b.get('alignment_score') > 0],
            'average_alignment_score': 0
        }
        
        # Collect all validation rules
        all_rules = []
        for behavior in func_behaviors:
            all_rules.extend(behavior.get('validation_rules', []))
        merged['validation_rules'] = list(set(all_rules))  # Deduplicate
        
        # Collect all parameters
        all_params = []
        for behavior in func_behaviors:
            all_params.extend(behavior.get('parameters', []))
        merged['parameters'] = list(set(all_params))  # Deduplicate
        
        # Calculate average alignment score
        scores = merged['alignment_scores']
        if scores:
            merged['average_alignment_score'] = sum(scores) / len(scores)
        
        merged_behaviors.append(merged)
    
    return merged_behaviors

def save_aggregated_behaviors(behaviors: List[Dict[str, Any]], output_file: Path):
    """Save aggregated behaviors to JSON file."""
    # Add metadata
    output_data = {
        'metadata': {
            'total_functions': len(behaviors),
            'total_behaviors': sum(len(b['behaviors']) for b in behaviors),
            'functions_with_specified_tests': len([b for b in behaviors if 'specified' in b['sources']]),
            'functions_with_additional_tests': len([b for b in behaviors if 'additional' in b['sources']])
        },
        'functions': behaviors
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved aggregated behaviors to: {output_file}")
    print(f"Total functions: {output_data['metadata']['total_functions']}")
    print(f"Total behaviors: {output_data['metadata']['total_behaviors']}")

def main():
    """Main aggregation process."""
    import os
    
    # Use BASE_DIR environment variable if set, otherwise use current directory
    base_dir = Path(os.environ.get('BASE_DIR', Path.cwd()))
    reports_dir = Path(os.environ.get('REPORTS_DIR', base_dir / "reports"))
    output_dir = Path(os.environ.get('OUTPUT_DIR', base_dir / "logic_catalog"))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=== Aggregating Behaviors from Alignment Reports ===")
    
    # Load all alignment reports
    reports = load_alignment_reports(reports_dir)
    print(f"Found {len(reports)} alignment reports")
    
    if not reports:
        print("No alignment reports found. Please run the alignment analysis first.")
        return
    
    # Extract behaviors from each report
    all_behaviors = []
    for report in reports:
        behaviors = extract_behaviors_from_report(report)
        all_behaviors.append(behaviors)
        print(f"Extracted {len(behaviors)} behaviors from report")
    
    # Merge behaviors by function
    merged_behaviors = merge_behaviors(all_behaviors)
    print(f"Merged into {len(merged_behaviors)} unique functions")
    
    # Save aggregated behaviors
    output_file = output_dir / "aggregated_behaviors.json"
    save_aggregated_behaviors(merged_behaviors, output_file)
    
    print("\n=== Aggregation Complete ===")

if __name__ == "__main__":
    main()