#!/usr/bin/env python3
"""
Unified PR Analyzer - Main analyzer class
"""

import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional

from .stages import (
    ContextPreparer,
    AgentPromptGenerator,
    RobustAgentCaller,
    ResponseParser,
    IssueExtractor,
    FilteringAndCombination,
    AgenticHTMLReportGenerator,
    FeedbackUpdateSystem
)


class UnifiedPRAnalyzer:
    """Unified PR analyzer that runs all stages and saves outputs locally"""
    
    def __init__(self, repo_path: str, debug_mode: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.analyzer_dir = Path(__file__).parent
        self.output_dir = self.repo_path / "pr_analysis_output"
        self.output_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode
        
        # Copy necessary files to local output directory
        self.setup_local_environment()
    
    def setup_local_environment(self):
        """Copy necessary prompt data and create local analysis environment"""
        
        # Create local prompt_data directory
        local_prompt_dir = self.output_dir / "prompt_data"
        local_prompt_dir.mkdir(exist_ok=True)
        
        # Copy prompt data files from the package
        source_prompt_dir = self.analyzer_dir / "prompt_data"
        if source_prompt_dir.exists():
            for file in source_prompt_dir.glob("*"):
                if file.is_file():
                    shutil.copy2(file, local_prompt_dir / file.name)
        
        print(f"📁 Analysis output directory: {self.output_dir}")
    
    def run_stage1_context_prep(self, from_branch: str, to_branch: str) -> bool:
        """Run Stage 1: Context preparation"""
        print("🔄 Stage 1: Context Preparation")
        
        try:
            stage1 = ContextPreparer(str(self.repo_path), str(self.output_dir))
            result = stage1.run_full_stage1_test(from_branch, to_branch)
            
            if result.success:
                print("✅ Stage 1: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage1")
                return True
            else:
                print("❌ Stage 1: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 1: ERROR - {e}")
            return False
    
    def run_stage2_agent_prompts(self) -> bool:
        """Run Stage 2: Agent prompts"""
        print("🔄 Stage 2: Agent Prompts")
        
        try:
            stage2 = AgentPromptGenerator(str(self.output_dir))
            results = stage2.run_full_stage2_test()
            
            # Check if all agent prompts succeeded
            success = all(result.generated_successfully for result in results.values())
            
            if success:
                print("✅ Stage 2: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage2")
                return True
            else:
                print("❌ Stage 2: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 2: ERROR - {e}")
            return False
    
    def run_stage3_agent_communication(self) -> bool:
        """Run Stage 3: Agent communication"""
        print("🔄 Stage 3: Agent Communication")
        
        try:
            stage3 = RobustAgentCaller(str(self.output_dir))
            results = stage3.run_full_stage3_test()
            
            if results.get('ready_for_stage4', False):
                print("✅ Stage 3: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage3")
                return True
            else:
                print("❌ Stage 3: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 3: ERROR - {e}")
            return False
    
    def run_stage4_response_parsing(self) -> bool:
        """Run Stage 4: Response parsing"""
        print("🔄 Stage 4: Response Parsing")
        
        try:
            stage4 = ResponseParser(str(self.output_dir))
            results = stage4.run_full_stage4_test()
            
            if results.get('success', False):
                print("✅ Stage 4: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage4")
                return True
            else:
                print("❌ Stage 4: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 4: ERROR - {e}")
            return False
    
    def run_stage5_issue_extraction(self) -> bool:
        """Run Stage 5: Issue extraction"""
        print("🔄 Stage 5: Issue Extraction")
        
        try:
            stage5 = IssueExtractor(str(self.output_dir))
            results = stage5.run_full_stage5_test()
            
            if results.get('success', False):
                print("✅ Stage 5: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage5")
                return True
            else:
                print("❌ Stage 5: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 5: ERROR - {e}")
            return False
    
    def run_stage6_filtering_combination(self) -> bool:
        """Run Stage 6: Filtering and combination"""
        print("🔄 Stage 6: Filtering and Combination")
        
        try:
            stage6 = FilteringAndCombination(str(self.output_dir))
            results = stage6.run_full_stage6_test()
            
            if results.get('success', False):
                print("✅ Stage 6: SUCCESS")
                # Debug outputs are now saved directly to local directory
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage6")
                return True
            else:
                print("❌ Stage 6: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 6: ERROR - {e}")
            return False
    
    def run_stage7_html_generation(self) -> bool:
        """Run Stage 7: HTML report generation"""
        print("🔄 Stage 7: HTML Report Generation")
        
        try:
            stage7 = AgenticHTMLReportGenerator(str(self.repo_path), str(self.output_dir))
            result = stage7.run_stage7_agentic_html_test()
            
            if result:
                print("✅ Stage 7: SUCCESS")
                # HTML report is already generated in the correct location
                html_file = self.output_dir / "pr_analysis_interactive.html"
                if html_file.exists():
                    print(f"📊 HTML Report Generated: {html_file}")
                    print(f"🔗 Open in browser: file://{html_file.absolute()}")
                return True
            else:
                print("❌ Stage 7: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 7: ERROR - {e}")
            return False
    
    def analyze_pr(self, from_branch: str = "main", to_branch: str = None) -> bool:
        """Run complete PR analysis pipeline"""
        
        print("=" * 80)
        print("🚀 PR ANALYZER - UNIFIED PIPELINE")
        print("=" * 80)
        print(f"📂 Repository: {self.repo_path}")
        print(f"🔀 Analyzing: {from_branch} → {to_branch or 'current branch'}")
        print(f"📁 Output directory: {self.output_dir}")
        print()
        
        start_time = time.time()
        
        # Run all stages in sequence
        stages = [
            ("Stage 1: Context Preparation", lambda: self.run_stage1_context_prep(from_branch, to_branch)),
            ("Stage 2: Agent Prompts", self.run_stage2_agent_prompts),
            ("Stage 3: Agent Communication", self.run_stage3_agent_communication),
            ("Stage 4: Response Parsing", self.run_stage4_response_parsing),
            ("Stage 5: Issue Extraction", self.run_stage5_issue_extraction),
            ("Stage 6: Filtering & Combination", self.run_stage6_filtering_combination),
            ("Stage 7: HTML Generation", self.run_stage7_html_generation)
        ]
        
        failed_stages = []
        
        for stage_name, stage_func in stages:
            success = stage_func()
            if not success:
                failed_stages.append(stage_name)
                print(f"⚠️  Continuing despite {stage_name} failure...")
            print()
        
        elapsed_time = time.time() - start_time
        print("=" * 80)
        
        if not failed_stages:
            print("✅ ALL STAGES COMPLETED SUCCESSFULLY!")
            print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
            
            # Show output files
            html_report = self.output_dir / "pr_analysis_interactive.html"
            if html_report.exists():
                print(f"📊 Interactive HTML Report: {html_report}")
                print(f"🔗 Open in browser: file://{html_report.absolute()}")
            
            markdown_report = self.output_dir / "debug_outputs" / "stage6" / "PR_ANALYSIS_REPORT.md"
            if markdown_report.exists():
                print(f"📄 Markdown Report: {markdown_report}")
            
            return True
        else:
            print(f"⚠️  COMPLETED WITH {len(failed_stages)} FAILED STAGES:")
            for stage in failed_stages:
                print(f"   • {stage}")
            print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
            return False
    
    def update_analysis_with_feedback(self, feedback: str, feedback_files: list = None) -> bool:
        """Update analysis with user feedback"""
        print("=" * 80)
        print("🔄 PR ANALYZER - FEEDBACK UPDATE")
        print("=" * 80)
        print(f"💬 User Feedback: {feedback}")
        if feedback_files:
            print(f"📎 Additional Files: {', '.join(feedback_files)}")
        print()
        
        try:
            # Run Stage 8: Feedback updates
            stage8 = FeedbackUpdateSystem()
            success = stage8.process_feedback_update(feedback, feedback_files)
            
            if success:
                print("✅ Feedback update completed successfully!")
                
                # Copy updated results to local output
                source_debug = self.analyzer_dir.parent.parent.parent.parent / "pr_analyzer" / "debug_outputs" / "stage8_feedback"
                target_debug = self.output_dir / "debug_outputs" / "stage8_feedback"
                if source_debug.exists():
                    shutil.copytree(source_debug, target_debug, dirs_exist_ok=True)
                
                # Re-run HTML generation with updated data
                if self.run_stage7_html_generation():
                    print("✅ HTML report updated with feedback!")
                
                return True
            else:
                print("❌ Feedback update failed")
                return False
                
        except Exception as e:
            print(f"❌ Error updating analysis: {e}")
            return False