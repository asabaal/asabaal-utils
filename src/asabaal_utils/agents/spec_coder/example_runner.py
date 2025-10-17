#!/usr/bin/env python3
"""
Spec-Coder Agent Interactive Example Runner

This script demonstrates the complete spec-coder pipeline by generating
all files locally for inspection and learning.
"""

import os
import sys
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import IntegrationOrchestrator

# Configuration
OUTPUT_DIR = Path("example_output")
SPEC_FILE = OUTPUT_DIR / "spec.yml"

def create_example_spec():
    """Create the example OpenSpec specification."""
    spec_content = {
        'spec_id': 'example-001',
        'title': 'Example: Multiply by 2 Function',
        'version': '1.0.0',
        'description': 'A simple example that demonstrates the spec-coder pipeline by implementing a function that multiplies integers by 2.',
        'requirements': [
            {
                'id': 'req-001',
                'title': 'Basic Multiply Function',
                'description': 'Implement a function that takes an integer and returns the same integer multiplied by 2. This is the ONLY function that should be implemented.',
                'validation': [
                    {
                        'type': 'unit',
                        'file': 'test_basic_function.py',
                        'target': 'test_basic_function'
                    }
                ]
            }
        ],
        'interfaces': [
            {
                'name': 'SimpleInterface',
                'methods': [
                    {
                        'name': 'basic_function',
                        'description': 'Multiplies the input integer by 2 and returns the result. This is the ONLY function in this module.',
                        'parameters': [
                            {
                                'name': 'x',
                                'type': 'int',
                                'description': 'The integer to multiply by 2'
                            }
                        ],
                        'returns': {
                            'type': 'int',
                            'description': 'The input integer multiplied by 2'
                        }
                    }
                ]
            }
        ]
    }
    
    with open(SPEC_FILE, 'w') as f:
        yaml.dump(spec_content, f, default_flow_style=False, indent=2)
    
    print(f"✅ Created specification: {SPEC_FILE}")
    return SPEC_FILE

def setup_output_directory():
    """Setup the output directory and clean previous runs."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✅ Created output directory: {OUTPUT_DIR}")

def run_pipeline():
    """Run the complete spec-coder pipeline."""
    print("\n🚀 Starting Spec-Coder Pipeline Example")
    print("=" * 50)
    
    # Initialize the orchestrator
    orchestrator = IntegrationOrchestrator(base_dir=OUTPUT_DIR)
    
    # Run the full pipeline
    output_dir = OUTPUT_DIR / "pipeline_output"
    success = orchestrator.run_full_pipeline(
        spec_file=SPEC_FILE, 
        output_dir=output_dir
    )
    
    if success:
        print("✅ Pipeline completed successfully!")
        return output_dir
    else:
        print("❌ Pipeline failed!")
        return None

def organize_output_files(final_output_dir):
    """Organize the generated files for easy inspection."""
    print("\n📁 Organizing output files...")
    
    # Create organized structure
    stage1_dir = OUTPUT_DIR / "stage1_scaffold"
    stage2_dir = OUTPUT_DIR / "stage2_analysis" 
    stage3_dir = OUTPUT_DIR / "stage3_alignment"
    stage4_dir = OUTPUT_DIR / "stage4_generation"
    
    for dir_path in [stage1_dir, stage2_dir, stage3_dir, stage4_dir]:
        dir_path.mkdir(exist_ok=True)
    
    # Move files to appropriate directories
    if final_output_dir and final_output_dir.exists():
        # Stage 1: Scaffold files
        scaffold_dir = final_output_dir / "scaffolds"
        if scaffold_dir.exists():
            shutil.move(str(scaffold_dir), str(stage1_dir))
        
        # Stage 2: Analysis files  
        reports_dir = final_output_dir / "reports"
        if reports_dir.exists():
            stage2_files = list(reports_dir.glob("stage2_*"))
            for file in stage2_files:
                if file.is_file():
                    shutil.move(str(file), str(stage2_dir / file.name))
        
        # Stage 3: Alignment files
        if reports_dir.exists():
            alignment_file = reports_dir / "behavioral_alignment_report.json"
            if alignment_file.exists():
                shutil.move(str(alignment_file), str(stage3_dir))
        
        # Stage 4: Generation files
        prompts_dir = OUTPUT_DIR / "prompts"
        if prompts_dir.exists():
            shutil.move(str(prompts_dir), str(stage4_dir / "prompts"))
        
        # Move remaining reports to stage4
        if reports_dir.exists():
            stage4_reports_dir = stage4_dir / "reports"
            stage4_reports_dir.mkdir(parents=True, exist_ok=True)
            for file in reports_dir.iterdir():
                if file.is_file():
                    shutil.move(str(file), str(stage4_reports_dir / file.name))
        
        # Move generated source code
        src_dir = final_output_dir / "src"
        if src_dir.exists():
            shutil.move(str(src_dir), str(stage4_dir / "src"))

def create_summary():
    """Create a summary of what was generated."""
    summary = f"""# Spec-Coder Pipeline Example Summary

Generated: {datetime.now().isoformat()}

## Input Specification
- File: `spec.yml`
- Content: OpenSpec specification for a function that multiplies integers by 2

## Generated Files

### Stage 1: Scaffold ({len(list((OUTPUT_DIR / "stage1_scaffold").rglob("*"))) if (OUTPUT_DIR / "stage1_scaffold").exists() else 0} files)
- Documentation: `stage1_scaffold/docs/e2e_001.md`
- Tests: `stage1_scaffold/tests/test_basic_function.py`
- CI/CD: `stage1_scaffold/.github/workflows/ci.yml`
- Scripts: `stage1_scaffold/scripts/validate.sh`
- Dependencies: `stage1_scaffold/requirements.txt`

### Stage 2: Analysis ({len(list((OUTPUT_DIR / "stage2_analysis").rglob("*"))) if (OUTPUT_DIR / "stage2_analysis").exists() else 0} files)
- Test behavior analysis: `stage2_analysis/test_summaries.json`

### Stage 3: Alignment ({len(list((OUTPUT_DIR / "stage3_alignment").rglob("*"))) if (OUTPUT_DIR / "stage3_alignment").exists() else 0} files)
- Alignment report: `stage3_alignment/behavioral_alignment_report.json`

### Stage 4: Generation ({len(list((OUTPUT_DIR / "stage4_generation").rglob("*"))) if (OUTPUT_DIR / "stage4_generation").exists() else 0} files)
- Prompts: `stage4_generation/prompts/` (9 prompt files)
- Source code: `stage4_generation/src/`
- Reports: `stage4_generation/reports/`

## Key Files to Examine

1. **Input Specification**: `spec.yml`
2. **Generated Tests**: `stage1_scaffold/tests/test_basic_function.py`
3. **Test Analysis**: `stage2_analysis/test_summaries.json`
4. **Alignment Report**: `stage3_alignment/behavioral_alignment_report.json`
5. **Generated Prompts**: `stage4_generation/prompts/*.prompt`
6. **Final Implementation**: `stage4_generation/src/`

## What This Demonstrates

- How OpenSpec specifications are processed
- Test generation from specifications
- Behavioral analysis and alignment
- Prompt generation for code implementation
- Complete pipeline integration

## Next Steps

Examine each file to understand how the spec-coder agent transforms a specification into working code.
"""
    
    with open(OUTPUT_DIR / "pipeline_summary.md", 'w') as f:
        f.write(summary)
    
    print(f"✅ Created summary: {OUTPUT_DIR / 'pipeline_summary.md'}")

def print_final_instructions():
    """Print instructions for examining the output."""
    print("\n" + "=" * 60)
    print("🎉 Example completed successfully!")
    print("=" * 60)
    print(f"\n📂 All files generated in: {OUTPUT_DIR.absolute()}")
    print("\n📋 Key files to examine:")
    print(f"   • Specification: {SPEC_FILE}")
    print(f"   • Generated tests: {OUTPUT_DIR / 'stage1_scaffold/tests/test_basic_function.py'}")
    print(f"   • Prompts: {OUTPUT_DIR / 'stage4_generation/prompts/'}")
    print(f"   • Summary: {OUTPUT_DIR / 'pipeline_summary.md'}")
    print("\n🔍 Example commands:")
    print(f"   cat {SPEC_FILE}")
    print(f"   cat {OUTPUT_DIR / 'stage1_scaffold/tests/test_basic_function.py'}")
    print(f"   ls {OUTPUT_DIR / 'stage4_generation/prompts/'}")
    print(f"   cat {OUTPUT_DIR / 'pipeline_summary.md'}")

def main():
    """Main example runner."""
    print("🧩 Spec-Coder Agent Interactive Example")
    print("This will generate all pipeline files locally for inspection.\n")
    
    try:
        # Setup
        setup_output_directory()
        spec_file = create_example_spec()
        
        # Run pipeline
        final_output = run_pipeline()
        
        if final_output:
            # Organize results
            organize_output_files(final_output)
            create_summary()
            print_final_instructions()
        else:
            print("❌ Pipeline failed. Check the logs above.")
            return 1
            
    except Exception as e:
        print(f"❌ Error running example: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())