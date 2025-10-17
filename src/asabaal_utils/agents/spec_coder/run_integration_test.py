#!/usr/bin/env python3
"""
Script to run a single integration test with real AI model calls.

This script demonstrates how to test the CodeGenerator with actual AI models
instead of mocked responses. Use this to validate prompt quality and model behavior.

Usage:
    python run_integration_test.py [--model MODEL_NAME]

Requirements:
    - Ollama must be running
    - At least one model must be available (llama3.1:8b, qwen3-coder:latest, etc.)
"""

import argparse
import tempfile
import shutil
import yaml
from pathlib import Path
import time
import sys

from generator import CodeGenerator


def create_test_spec(temp_dir):
    """Create a test specification for integration testing."""
    spec_content = """
spec_id: "integration-test-001"
title: "String Utilities"
version: "1.0.0"
description: "A collection of string utility functions"
requirements:
  - id: "req-001"
    title: "String Reversal Function"
    description: "Function that reverses a string"
    validation:
      - type: "unit"
        target: "test_reverse_string"
    acceptance_criteria:
      - "Function takes a string parameter"
      - "Returns the reversed string"
      - "Handles empty strings"
      - "Handles single character strings"
  - id: "req-002"
    title: "String Capitalization Function"
    description: "Function that capitalizes the first letter of each word"
    validation:
      - type: "unit"
        target: "test_capitalize_words"
    acceptance_criteria:
      - "Function takes a string parameter"
      - "Returns capitalized string"
      - "Handles multiple spaces"
      - "Handles empty strings"
interfaces:
  - name: "StringUtils"
    methods:
      - name: "reverse_string"
        parameters:
          - name: "text"
            type: "str"
        returns:
          type: "str"
      - name: "capitalize_words"
        parameters:
          - name: "text"
            type: "str"
        returns:
          type: "str"
"""
    spec_file = temp_dir / "string_utils_spec.yml"
    spec_file.write_text(spec_content)
    return spec_file


def create_config(temp_dir, model_name):
    """Create configuration for the specified model."""
    config = {
        'model': {
            'model': model_name,
            'temperature': 0.3,
            'max_tokens': 2000
        },
        'generation': {
            'overwrite': True
        }
    }
    config_file = temp_dir / "config.yaml"
    config_file.write_text(yaml.dump(config))
    return config_file


def analyze_generated_code(file_path):
    """Analyze the quality of generated code."""
    content = Path(file_path).read_text()
    
    analysis = {
        'line_count': len(content.splitlines()),
        'function_count': len([line for line in content.splitlines() if line.strip().startswith('def ')]),
        'class_count': len([line for line in content.splitlines() if line.strip().startswith('class ')]),
        'has_docstrings': '"""' in content or "'''" in content,
        'has_imports': 'import' in content,
        'has_main_guard': '__name__' in content,
        'has_error_handling': 'try:' in content or 'except' in content,
        'has_type_hints': ':' in content and '->' in content,
    }
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description="Run integration test with real AI models")
    parser.add_argument(
        '--model', 
        default='qwen3-coder:latest',
        help='Model to use for generation (default: qwen3-coder:latest)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for generated files (default: temporary)'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Running integration test with model: {args.model}")
    print("=" * 60)
    
    # Setup temporary directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir.parent
    else:
        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / "output"
    
    try:
        # Create test files
        spec_file = create_test_spec(temp_dir)
        config_file = create_config(temp_dir, args.model)
        
        print(f"📋 Test specification: {spec_file}")
        print(f"⚙️  Configuration: {config_file}")
        print(f"📁 Output directory: {output_dir}")
        print()
        
        # Run generation
        print("🤖 Starting AI generation...")
        generator = CodeGenerator(config_path=config_file)
        
        start_time = time.time()
        result = generator.generate_from_spec(spec_file, output_dir)
        execution_time = time.time() - start_time
        
        print(f"⏱️  Generation completed in {execution_time:.2f} seconds")
        print()
        
        # Display results
        if result.success:
            print("✅ Generation successful!")
            print(f"📄 Files generated: {len(result.files_generated)}")
            
            for file_path in result.files_generated:
                print(f"   📄 {file_path}")
                
                # Analyze Python files
                if file_path.endswith('.py'):
                    analysis = analyze_generated_code(file_path)
                    print(f"      📊 Lines: {analysis['line_count']}, Functions: {analysis['function_count']}")
                    print(f"      📝 Has docstrings: {analysis['has_docstrings']}")
                    print(f"      🔧 Has imports: {analysis['has_imports']}")
                    print(f"      🛡️  Has error handling: {analysis['has_error_handling']}")
                    print(f"      📝 Has type hints: {analysis['has_type_hints']}")
                    
                    # Show first few lines of code
                    content = Path(file_path).read_text()
                    lines = content.splitlines()[:10]
                    print("      📖 Code preview:")
                    for i, line in enumerate(lines, 1):
                        print(f"         {i:2d}: {line}")
                    if len(content.splitlines()) > 10:
                        print("         ...")
                    print()
            
            # Validate requirements
            print("🔍 Validating generated code against requirements...")
            source_files = [f for f in result.files_generated if f.endswith('.py')]
            if source_files:
                source_content = Path(source_files[0]).read_text()
                
                # Check for required functions
                required_functions = ['reverse_string', 'capitalize_words']
                for func in required_functions:
                    if f"def {func}(" in source_content:
                        print(f"   ✅ Found function: {func}")
                    else:
                        print(f"   ❌ Missing function: {func}")
                
                # Check for class
                if 'class StringUtils' in source_content:
                    print("   ✅ Found class: StringUtils")
                else:
                    print("   ⚠️  Class StringUtils not found (may be using module functions)")
        
        else:
            print("❌ Generation failed!")
            print(f"🚨 Errors: {result.errors}")
            if result.warnings:
                print(f"⚠️  Warnings: {result.warnings}")
            return 1
        
        print()
        print("🎉 Integration test completed!")
        if not args.output_dir:
            print(f"📁 Temporary files will be cleaned up")
            print(f"   To keep files, run with --output-dir /path/to/save")
        
        return 0
        
    except Exception as e:
        print(f"💥 Error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup if not using custom output dir
        if not args.output_dir:
            print(f"🧹 Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())