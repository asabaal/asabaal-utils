#!/usr/bin/env python3
"""
Generate Prompts - Create per-function prompt templates for AI code generation
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def load_functional_catalog(catalog_file: Path) -> Dict[str, Any]:
    """Load functional catalog from YAML file."""
    with open(catalog_file, 'r') as f:
        return yaml.safe_load(f)

def generate_function_prompt(function_name: str, function_data: Dict[str, Any]) -> str:
    """Generate a comprehensive prompt for a single function."""
    
    # Extract function information
    category = function_data.get('category', 'utility')
    description = function_data.get('description', '')
    behaviors = function_data.get('behaviors', [])
    parameters = function_data.get('parameters', [])
    return_type = function_data.get('return_type', 'Any')
    validation_rules = function_data.get('validation_rules', [])
    error_conditions = function_data.get('error_conditions', [])
    
    # Build parameter signature
    param_signature_parts = []
    for param in parameters:
        param_name = param['name']
        param_type = param['type']
        default_val = param.get('default')
        
        if default_val is not None:
            param_signature_parts.append(f"{param_name}: {param_type} = {default_val}")
        else:
            param_signature_parts.append(f"{param_name}: {param_type}")
    
    param_signature = ", ".join(param_signature_parts)
    
    # Build the prompt
    prompt = f"""# Function Implementation Request: {function_name}

## Overview
Generate a Python function `{function_name}` that implements the following specification.

## Function Signature
```python
def {function_name}({param_signature}) -> {return_type}:
    \"\"\"
    {description}
    \"\"\"
    # Implementation here
```

## Category
{category}

## Behavioral Requirements
{chr(10).join(f"- {behavior}" for behavior in behaviors) if behaviors else "- No specific behaviors defined"}

## Parameters
"""
    
    # Add parameter details
    if parameters:
        for param in parameters:
            param_name = param['name']
            param_type = param['type']
            param_desc = param.get('description', '')
            default_val = param.get('default')
            
            prompt += f"- `{param_name}` ({param_type})"
            if default_val is not None:
                prompt += f" (default: {default_val})"
            if param_desc:
                prompt += f": {param_desc}"
            prompt += "\n"
    else:
        prompt += "- No parameters\n"
    
    prompt += f"""
## Return Type
The function must return a value of type `{return_type}`.

## Validation Rules
{chr(10).join(f"- {rule}" for rule in validation_rules) if validation_rules else "- No specific validation rules defined"}

## Error Conditions
{chr(10).join(f"- {condition}" for condition in error_conditions) if error_conditions else "- No specific error conditions defined"}

## Implementation Guidelines

1. **Code Quality**: Write clean, readable, and well-documented code
2. **Error Handling**: Implement appropriate error handling for edge cases
3. **Type Safety**: Ensure type hints are correct and consistent
4. **Performance**: Consider performance implications for large inputs
5. **Testing**: The implementation should pass all associated test cases

## Test Coverage Context
This function has the following test coverage:
- Test files: {', '.join(function_data.get('test_coverage', {}).get('file_paths', []))}
- Test names: {', '.join(function_data.get('test_coverage', {}).get('test_names', []))}
- Average alignment score: {function_data.get('test_coverage', {}).get('average_alignment_score', 0):.2f}

## Additional Notes
- Focus on implementing the core functionality as specified
- Ensure the function handles edge cases gracefully
- Follow Python best practices and conventions
- The implementation should be self-contained and not depend on external state

Generate only the function implementation without additional explanations or test code.
"""
    
    return prompt

def generate_metadata_summary(catalog: Dict[str, Any]) -> str:
    """Generate a metadata summary for the prompts collection."""
    metadata = catalog.get('metadata', {})
    
    summary = f"""# Functional Logic Prompts Collection

## Overview
This directory contains AI prompt templates for implementing functions based on test analysis and behavioral alignment.

## Generation Details
- **Generated**: {datetime.now().isoformat()}
- **Catalog Version**: {metadata.get('catalog_version', 'unknown')}
- **Total Functions**: {metadata.get('total_functions', 0)}
- **Categories**: {', '.join(metadata.get('categories', {}).keys())}

## Categories Breakdown
"""
    
    categories = metadata.get('categories', {})
    for category, functions in categories.items():
        summary += f"- **{category}**: {len(functions)} functions\n"
    
    summary += f"""
## Usage
Each `.prompt` file contains a complete specification for implementing a single function. The prompts are designed to be used with AI code generation systems to produce implementations that will pass the analyzed test cases.

## Source Data
These prompts were generated from:
- Test analysis and behavioral extraction
- OpenSpec specification alignment
- Aggregated validation rules and error conditions

## Quality Assurance
- All prompts include comprehensive behavioral requirements
- Validation rules ensure proper error handling
- Test coverage context guides implementation decisions
"""
    
    return summary

def save_prompt(function_name: str, prompt: str, prompts_dir: Path):
    """Save a single prompt to file."""
    prompt_file = prompts_dir / f"{function_name}.prompt"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    print(f"Generated prompt: {prompt_file}")

def save_metadata_summary(summary: str, prompts_dir: Path):
    """Save metadata summary to README file."""
    readme_file = prompts_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(summary)
    print(f"Generated metadata summary: {readme_file}")

def generate_prompts_index(catalog: Dict[str, Any], prompts_dir: Path):
    """Generate an index file listing all available prompts."""
    functions = catalog.get('functions', {})
    
    index_content = "# Function Prompts Index\n\n"
    index_content += "This file lists all available function prompts organized by category.\n\n"
    
    # Group functions by category
    categories = {}
    for func_name, func_data in functions.items():
        category = func_data.get('category', 'utility')
        if category not in categories:
            categories[category] = []
        categories[category].append((func_name, func_data))
    
    # Generate index by category
    for category, func_list in categories.items():
        index_content += f"## {category.title()}\n\n"
        
        for func_name, func_data in func_list:
            description = func_data.get('description', '')
            test_count = len(func_data.get('test_coverage', {}).get('test_names', []))
            alignment_score = func_data.get('test_coverage', {}).get('average_alignment_score', 0)
            
            index_content += f"- [{func_name}.prompt]({func_name}.prompt)"
            if description:
                index_content += f" - {description}"
            index_content += f" (Tests: {test_count}, Alignment: {alignment_score:.2f})\n"
        
        index_content += "\n"
    
    # Save index
    index_file = prompts_dir / "INDEX.md"
    with open(index_file, 'w') as f:
        f.write(index_content)
    print(f"Generated prompts index: {index_file}")

def main():
    """Main prompt generation process."""
    import os
    
    print(f"DEBUG: Current working directory: {Path.cwd()}")
    print(f"DEBUG: Current directory contents: {list(Path.cwd().iterdir())}")
    
    # Use BASE_DIR environment variable if set, otherwise use current directory
    base_dir = Path(os.environ.get('BASE_DIR', Path.cwd()))
    catalog_file = base_dir / "logic_catalog" / "functional_catalog.yaml"
    prompts_dir = base_dir / "prompts"
    
    print(f"DEBUG: Looking for catalog at: {catalog_file.absolute()}")
    print(f"DEBUG: Catalog exists: {catalog_file.exists()}")
    print(f"DEBUG: Prompts dir: {prompts_dir.absolute()}")
    print(f"DEBUG: Prompts dir exists: {prompts_dir.exists()}")
    if prompts_dir.exists():
        print(f"DEBUG: Prompts dir contents: {list(prompts_dir.iterdir())}")
    
    print("=== Generating Function Prompts ===")
    
    if not catalog_file.exists():
        print(f"Functional catalog not found: {catalog_file}")
        print("Please run build_logic_catalog.py first.")
        return
    
    # Create prompts directory
    prompts_dir.mkdir(exist_ok=True)
    
    # Load functional catalog
    catalog = load_functional_catalog(catalog_file)
    functions = catalog.get('functions', {})
    total_functions = len(functions)
    
    print(f"Loaded catalog with {total_functions} functions")
    
    # Generate prompts for each function
    generated_count = 0
    for func_name, func_data in functions.items():
        try:
            prompt = generate_function_prompt(func_name, func_data)
            save_prompt(func_name, prompt, prompts_dir)
            generated_count += 1
        except Exception as e:
            print(f"Error generating prompt for {func_name}: {e}")
    
    # Generate metadata summary
    summary = generate_metadata_summary(catalog)
    save_metadata_summary(summary, prompts_dir)
    
    # Generate prompts index
    generate_prompts_index(catalog, prompts_dir)
    
    print(f"\n=== Prompt Generation Complete ===")
    print(f"Generated {generated_count} prompts out of {total_functions} functions")
    print(f"Prompts saved to: {prompts_dir}")

if __name__ == "__main__":
    main()