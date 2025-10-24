#!/usr/bin/env python3
"""
Run fresh PR analysis for backend comparison
"""

import sys
import os
from pathlib import Path

# Add asabaal-utils to path
sys.path.insert(0, str(Path(__file__).parent / "asabaal-utils" / "src"))

def run_fresh_analysis():
    """Run a fresh analysis with current OpenRouter backend"""
    
    target_repo = "/home/asabaal/repos/multisensory-experience-website"
    output_dir = Path(target_repo) / "pr_analysis_output_openrouter_comparison"
    
    print("🔄 Running fresh PR analysis for backend comparison...")
    print(f"Target: {target_repo}")
    print(f"Output: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Import and run the analyzer
    try:
        from asabaal_utils.pr_analyzer.stages import ContextPreparer
        
        # Stage 1: Context Preparation
        print("📋 Stage 1: Preparing analysis context...")
        context_preparer = ContextPreparer(str(target_repo), str(output_dir))
        success = context_preparer.run_context_preparation()
        
        if success:
            print("✅ Context preparation completed")
            print(f"📁 Analysis context saved to: {output_dir}/debug_outputs/stage1/")
            return True
        else:
            print("❌ Context preparation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False

if __name__ == "__main__":
    success = run_fresh_analysis()
    sys.exit(0 if success else 1)