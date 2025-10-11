#!/usr/bin/env python3
"""
Stage 7: Detailed File-Level Analysis (Version 2)
Refactored to use the Agentic Batch Processing Toolkit

This version provides the same interface as the original but leverages the 
generalized batch processing framework for better maintainability and consistency.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import the generalized toolkit
from ..agentic_toolkit import create_detailed_analysis_processor, BatchProcessingConfig


class DetailedAnalysisEngine:
    """
    Detailed file-level analysis engine using the Agentic Batch Processing Toolkit.
    
    Maintains the same interface as the original implementation but uses the
    generalized framework internally for better consistency and maintainability.
    """
    
    def __init__(self, repo_path: str, output_dir: Optional[str] = None, debug_mode: bool = False, max_files: Optional[int] = None, config: Optional[Dict[str, Any]] = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else self.repo_path / "pr_analysis_output"
        self.debug_mode = debug_mode
        self.max_files = max_files
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Package directory for templates
        self.package_dir = Path(__file__).parent
        
        # Create batch processor using the toolkit
        self.batch_processor = create_detailed_analysis_processor(
            repo_path=str(self.repo_path),
            output_dir=str(self.output_dir),
            instructions_path=str(self.package_dir / "detailed_analysis_instructions.txt"),
            output_format_path=str(self.package_dir / "detailed_analysis_output_format.json"),
            batch_size=12,
            max_files=max_files,
            debug_mode=debug_mode,
            backend_config=config
        )
    
    def load_analysis_context(self) -> Dict[str, Any]:
        """Load all previous analysis data for detailed review"""
        if self.debug_mode:
            print("🔍 Loading previous analysis data...")
        context = {}
        
        # Load Stage 1: File classifications and content
        stage1_files = self.output_dir / "debug_outputs" / "stage1"
        context_file = stage1_files / "final_analysis_context.json"
        
        if context_file.exists():
            if self.debug_mode:
                print(f"✅ Found Stage 1 context: {context_file}")
            with open(context_file, 'r') as f:
                context = json.load(f)
                if self.debug_mode:
                    print(f"   Files classified: {len(context.get('file_classifications', {}))}")
                    print(f"   Files with content: {len(context.get('file_contents', {}))}")
        else:
            if self.debug_mode:
                print(f"❌ Stage 1 context not found: {context_file}")
            
        # Load Stage 6: Combined analysis results
        stage6_files = self.output_dir / "debug_outputs" / "stage6"
        complete_analysis_file = stage6_files / "complete_pr_analysis.json"
        
        if complete_analysis_file.exists():
            if self.debug_mode:
                print(f"✅ Found Stage 6 results: {complete_analysis_file}")
            with open(complete_analysis_file, 'r') as f:
                stage6_data = json.load(f)
                context['previous_analysis'] = stage6_data
        else:
            if self.debug_mode:
                print(f"❌ Stage 6 results not found: {complete_analysis_file}")
                
        return context
    
    def generate_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Generate human-readable summary of detailed analysis"""
        
        # Handle both expected and actual response formats
        metadata = analysis_data.get('analysis_summary', {})
        file_analyses = analysis_data.get('file_analyses', [])
        
        total_files = metadata.get('total_files_analyzed', len(file_analyses))
        
        report = f"""DETAILED FILE-LEVEL ANALYSIS SUMMARY
{'=' * 50}

OVERALL RESULTS:
- Total files analyzed: {total_files}
- Analysis timestamp: {metadata.get('analysis_timestamp', 'Unknown')}
- Overall merge readiness: {metadata.get('overall_merge_readiness', 'Unknown').upper()}

"""

        # Count files by status
        ready_count = len([f for f in file_analyses if f.get('merge_readiness') == 'ready'])
        conditional_count = len([f for f in file_analyses if f.get('merge_readiness') == 'conditional'])
        not_ready_count = len([f for f in file_analyses if f.get('merge_readiness') == 'not_ready'])
        
        report += f"""FILE STATUS BREAKDOWN:
- Ready for merge: {ready_count}
- Conditional: {conditional_count}  
- Not ready: {not_ready_count}

"""

        # Files needing attention
        conditional_files = [f for f in file_analyses if f.get('merge_readiness') == 'conditional']
        not_ready_files = [f for f in file_analyses if f.get('merge_readiness') == 'not_ready']
        
        if conditional_files:
            report += f"\nCONDITIONAL FILES ({len(conditional_files)}):\n"
            for file_data in conditional_files:
                report += f"- {file_data.get('file_path', 'Unknown')}: {file_data.get('feedback', 'No specific feedback')}\n"
                
        if not_ready_files:
            report += f"\nNOT READY FILES ({len(not_ready_files)}):\n"
            for file_data in not_ready_files:
                report += f"- {file_data.get('file_path', 'Unknown')}: {file_data.get('feedback', 'No specific feedback')}\n"
                
        # Overall recommendations
        recommendations = analysis_data.get('recommendations', [])
        if recommendations:
            report += f"\nRECOMMENDATIONS:\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
                
        return report
    
    def run_detailed_analysis(self) -> bool:
        """Execute complete detailed file-level analysis using the batch processing toolkit"""
        
        print("=" * 80)
        print("🔍 STAGE 7: DETAILED FILE-LEVEL ANALYSIS")
        print("=" * 80)
        
        try:
            # Step 1: Load context and get file list
            analysis_context = self.load_analysis_context()
            files_array = analysis_context.get('files', [])
            
            # Apply file count filter if specified
            if self.max_files and len(files_array) > self.max_files:
                files_array = files_array[:self.max_files]
                if self.debug_mode:
                    print(f"🔢 File count filter applied: Processing {self.max_files} files (of {len(analysis_context.get('files', []))} total)")
            
            total_files = len(files_array)
            print(f"📊 Processing {total_files} files using generalized batch processing toolkit")
            
            # Step 2: Process all files using the batch processor
            result = self.batch_processor.process_all(
                items=files_array,
                previous_analyses=analysis_context.get('previous_analysis', {})
            )
            
            if result.success:
                # Load the results from the batch processor
                if self.batch_processor.results_file.exists():
                    with open(self.batch_processor.results_file, 'r') as f:
                        final_analysis = json.load(f)
                    
                    # Save results in the format expected by other stages
                    analysis_file = self.output_dir / "detailed_analysis_results.json"
                    with open(analysis_file, 'w') as f:
                        json.dump(final_analysis, f, indent=2)
                    
                    # Generate and save summary
                    summary = self.generate_analysis_summary(final_analysis)
                    summary_file = self.output_dir / "detailed_analysis_summary.txt"
                    with open(summary_file, 'w') as f:
                        f.write(summary)
                    
                    print(f"✅ STAGE 7 DETAILED ANALYSIS: SUCCESS")
                    print(f"📊 Analyzed {result.processed_count} of {result.total_count} files")
                    print(f"📊 Generated detailed analysis: {analysis_file}")
                    
                    if self.debug_mode:
                        self.create_test_summary(True, f"Analyzed {result.processed_count}/{result.total_count} files successfully")
                    
                    return True
                else:
                    raise Exception("Batch processor results file not found")
            else:
                error_msg = result.error_message or "Unknown error"
                print(f"❌ STAGE 7 DETAILED ANALYSIS: FAILED - {error_msg}")
                if self.debug_mode:
                    self.create_test_summary(False, error_msg)
                return False
                
        except Exception as e:
            print(f"❌ STAGE 7 DETAILED ANALYSIS: FAILED - {e}")
            if self.debug_mode:
                self.create_test_summary(False, str(e))
            return False
    
    def create_test_summary(self, success: bool, message: str):
        """Create test summary for this stage (debug mode only)"""
        if not self.debug_mode:
            return
            
        debug_dir = self.output_dir / "debug_outputs" / "stage7"
        debug_dir.mkdir(parents=True, exist_ok=True)
            
        summary = {
            "stage": "7_detailed_analysis",
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "output_files": [
                str(self.output_dir / "detailed_analysis_results.json"),
                str(self.output_dir / "detailed_analysis_summary.txt")
            ],
            "toolkit_version": "generalized_v2"
        }
        
        summary_file = debug_dir / "stage7_test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """Main execution for Stage 7"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python stage7_detailed_analysis_v2.py <repo_path> [output_dir]")
        sys.exit(1)
        
    repo_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    analyzer = DetailedAnalysisEngine(repo_path, output_dir, debug_mode=True)
    success = analyzer.run_detailed_analysis()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()