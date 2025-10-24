#!/usr/bin/env python3
"""
Script to run integration test with a more complex specification.

This uses the advanced string utilities spec that should force the AI
to create proper class structure with multiple methods.
"""

import argparse
import tempfile
import shutil
import yaml
from pathlib import Path
import time
import sys

from asabaal_utils.agents.spec_coder.generator import CodeGenerator


def main():
    parser = argparse.ArgumentParser(description="Run complex integration test")
    parser.add_argument(
        '--model', 
        default='qwen3-coder:latest',
        help='Model to use for generation'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for generated files'
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Running COMPLEX integration test with model: {args.model}")
    print("=" * 60)
    
    # Setup directories
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir.parent
    else:
        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / "output"
    
    try:
        # Use the complex specification
        spec_file = Path("complex_test_spec.yml")
        if not spec_file.exists():
            print(f"❌ Specification file not found: {spec_file}")
            return 1
        
        # Create config
        config = {
            'model': {
                'model': args.model,
                'temperature': 0.3,
                'max_tokens': 3000  # Increased for complex spec
            },
            'generation': {
                'overwrite': True
            }
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))
        
        print(f"📋 Using complex specification: {spec_file}")
        print(f"⚙️  Configuration: {config_file}")
        print(f"📁 Output directory: {output_dir}")
        print()
        
        # Run generation
        print("🤖 Starting AI generation with COMPLEX spec...")
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
                    content = Path(file_path).read_text()
                    
                    # Basic analysis
                    lines = content.splitlines()
                    functions = [line for line in lines if line.strip().startswith('def ')]
                    classes = [line for line in lines if line.strip().startswith('class ')]
                    docstrings = content.count('"""') + content.count("'''")
                    
                    print(f"      📊 Lines: {len(lines)}, Functions: {len(functions)}, Classes: {len(classes)}")
                    print(f"      📝 Docstring pairs: {docstrings // 2}")
                    
                    # Check for StringUtils class
                    if 'class StringUtils' in content:
                        print("      ✅ Found StringUtils class!")
                    else:
                        print("      ❌ StringUtils class not found")
                    
                    # Check for required methods
                    required_methods = [
                        '__init__',
                        'reverse_string', 
                        'capitalize_words',
                        'validate_string_format',
                        'get_string_stats',
                        'set_string',
                        'get_string'
                    ]
                    
                    found_methods = []
                    for method in required_methods:
                        if f'def {method}(' in content:
                            found_methods.append(method)
                            print(f"      ✅ Found method: {method}")
                        else:
                            print(f"      ❌ Missing method: {method}")
                    
                    print(f"      📈 Methods found: {len(found_methods)}/{len(required_methods)}")
                    
                    # Show first 15 lines of code
                    print("      📖 Code preview:")
                    for i, line in enumerate(lines[:15], 1):
                        print(f"         {i:2d}: {line}")
                    if len(lines) > 15:
                        print("         ...")
                    print()
        
        else:
            print("❌ Generation failed!")
            print(f"🚨 Errors: {result.errors}")
            if result.warnings:
                print(f"⚠️  Warnings: {result.warnings}")
            return 1
        
        print()
        print("🎉 Complex integration test completed!")
        
        # Validation summary
        source_files = [f for f in result.files_generated if f.endswith('.py')]
        if source_files:
            source_content = Path(source_files[0]).read_text()
            
            print("🔍 FINAL VALIDATION:")
            if 'class StringUtils' in source_content:
                print("   ✅ Class structure: PASS")
            else:
                print("   ❌ Class structure: FAIL")
            
            method_count = len([line for line in source_content.splitlines() 
                              if line.strip().startswith('def ') and not line.strip().startswith('def test')])
            print(f"   📊 Method count: {method_count} (expected: ~7)")
            
            if '"""' in source_content:
                print("   ✅ Documentation: PASS")
            else:
                print("   ❌ Documentation: FAIL")
            
            if 'import' in source_content:
                print("   ✅ Imports: PASS")
            else:
                print("   ❌ Imports: FAIL")
        
        return 0
        
    except Exception as e:
        print(f"💥 Error during integration test: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        if not args.output_dir:
            print(f"🧹 Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    sys.exit(main())