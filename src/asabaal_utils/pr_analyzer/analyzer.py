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
    FileAssessmentGenerator,
    Stage9HTMLGenerator,
    FeedbackUpdateSystem
)

# Import both versions of DetailedAnalysisEngine for migration
try:
    from .stage7_detailed_analysis_v2 import DetailedAnalysisEngine as DetailedAnalysisEngineV2
    TOOLKIT_VERSION_AVAILABLE = True
except ImportError:
    TOOLKIT_VERSION_AVAILABLE = False

from .stage7_detailed_analysis import DetailedAnalysisEngine as DetailedAnalysisEngineV1


class UnifiedPRAnalyzer:
    """Unified PR analyzer that runs all stages and saves outputs locally"""
    
    def __init__(self, repo_path: str, debug_mode: bool = False, max_files: int = None):
        self.repo_path = Path(repo_path).resolve()
        self.analyzer_dir = Path(__file__).parent
        self.output_dir = self.repo_path / "pr_analysis_output"
        self.output_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode
        self.max_files = max_files
        
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
    
    def run_stage7_detailed_analysis(self) -> bool:
        """Run Stage 7: Detailed file-level analysis"""
        print("🔄 Stage 7: Detailed File-Level Analysis")
        
        try:
            # Use the new toolkit-based version if available, otherwise fall back to V1
            if TOOLKIT_VERSION_AVAILABLE:
                if self.debug_mode:
                    print("🔧 Using generalized batch processing toolkit (V2)")
                stage7 = DetailedAnalysisEngineV2(str(self.repo_path), str(self.output_dir), self.debug_mode, self.max_files)
            else:
                if self.debug_mode:
                    print("🔧 Using legacy implementation (V1)")
                stage7 = DetailedAnalysisEngineV1(str(self.repo_path), str(self.output_dir), self.debug_mode, self.max_files)
            
            result = stage7.run_detailed_analysis()
            
            if result:
                print("✅ Stage 7: SUCCESS")
                # Analysis results are saved to main output directory
                analysis_file = self.output_dir / "detailed_analysis_results.json"
                if analysis_file.exists():
                    print(f"📊 Detailed Analysis Generated: {analysis_file}")
                if self.debug_mode:
                    print(f"🐛 Debug outputs saved to: {self.output_dir}/debug_outputs/stage7")
                return True
            else:
                print("❌ Stage 7: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 7: ERROR - {e}")
            return False
    
    def run_stage8_file_assessment(self) -> bool:
        """Run Stage 8: File-Level Merge Readiness Assessment"""
        print("🔄 Stage 8: File Assessment")
        
        try:
            stage8 = FileAssessmentGenerator(str(self.repo_path), str(self.output_dir))
            result = stage8.run_stage8_file_assessment()
            
            if result:
                print("✅ Stage 8: SUCCESS")
                print("📊 File assessment completed - results saved for Stage 9")
                return True
            else:
                print("❌ Stage 8: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 8: FAILED with error: {e}")
            return False
    
    def run_stage9_html_generation(self) -> bool:
        """Run Stage 9: HTML report generation"""
        print("🔄 Stage 9: HTML Report Generation")
        
        try:
            stage9 = Stage9HTMLGenerator(str(self.repo_path), str(self.output_dir))
            result = stage9.run_stage9_html_generation()
            
            if result:
                print("✅ Stage 9: SUCCESS")
                # HTML report is already generated in the correct location
                html_file = self.output_dir / "pr_analysis_interactive.html"
                if html_file.exists():
                    print(f"📊 HTML Report Generated: {html_file}")
                    print(f"🔗 Open in browser: file://{html_file.absolute()}")
                return True
            else:
                print("❌ Stage 9: FAILED")
                return False
                
        except Exception as e:
            print(f"❌ Stage 9: ERROR - {e}")
            return False
    
    def analyze_pr(self, from_branch: str = "main", to_branch: str = None, start_stage: int = 1, end_stage: int = 9) -> bool:
        """Run complete PR analysis pipeline with optional stage range"""
        
        print("=" * 80)
        print("🚀 PR ANALYZER - UNIFIED PIPELINE")
        print("=" * 80)
        print(f"📂 Repository: {self.repo_path}")
        print(f"🔀 Analyzing: {from_branch} → {to_branch or 'current branch'}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🎯 Running stages: {start_stage} → {end_stage}")
        print()
        
        start_time = time.time()
        
        # Define all stages with their numbers
        all_stages = [
            (1, "Stage 1: Context Preparation", lambda: self.run_stage1_context_prep(from_branch, to_branch)),
            (2, "Stage 2: Agent Prompts", self.run_stage2_agent_prompts),
            (3, "Stage 3: Agent Communication", self.run_stage3_agent_communication),
            (4, "Stage 4: Response Parsing", self.run_stage4_response_parsing),
            (5, "Stage 5: Issue Extraction", self.run_stage5_issue_extraction),
            (6, "Stage 6: Filtering & Combination", self.run_stage6_filtering_combination),
            (7, "Stage 7: Detailed Analysis", self.run_stage7_detailed_analysis),
            (8, "Stage 8: File Assessment", self.run_stage8_file_assessment),
            (9, "Stage 9: HTML Generation", self.run_stage9_html_generation)
        ]
        
        # Filter stages by range
        stages = [(name, func) for num, name, func in all_stages if start_stage <= num <= end_stage]
        
        failed_stages = []
        
        for stage_name, stage_func in stages:
            print(f"🔄 Running {stage_name}...")
            success = stage_func()
            if not success:
                failed_stages.append(stage_name)
                print(f"❌ {stage_name} FAILED - Stopping pipeline execution")
                print(f"💡 Fix the error above and run the analyzer again")
                return False
            print(f"✅ {stage_name} completed successfully")
            print()
        
        elapsed_time = time.time() - start_time
        print("=" * 80)
        
        if not failed_stages:
            if start_stage == end_stage:
                print(f"✅ STAGE {start_stage} COMPLETED SUCCESSFULLY!")
            elif start_stage == 1 and end_stage == 9:
                print("✅ ALL STAGES COMPLETED SUCCESSFULLY!")
            else:
                print(f"✅ STAGES {start_stage}-{end_stage} COMPLETED SUCCESSFULLY!")
            print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
            
            # Only show reports if the stages that generate them were run
            reports_shown = []
            
            # HTML report is generated by Stage 9
            if end_stage >= 9:
                html_report = self.output_dir / "pr_analysis_interactive.html"
                if html_report.exists():
                    print(f"📊 Interactive HTML Report: {html_report}")
                    print(f"🔗 Open in browser: file://{html_report.absolute()}")
                    reports_shown.append("HTML")
            
            # File assessment results are generated by Stage 8
            elif end_stage >= 8:
                assessment_file = self.output_dir / "file_assessment_results.json"
                if assessment_file.exists():
                    print(f"📊 File Assessment Results: {assessment_file}")
                    print(f"➡️  Run Stage 9 to generate HTML report from these results")
                    reports_shown.append("File Assessment")
            
            # Markdown report is generated by Stage 6 - only show if we actually ran Stage 6
            if start_stage <= 6 and end_stage >= 6:
                markdown_report = self.output_dir / "debug_outputs" / "stage6" / "PR_ANALYSIS_REPORT.md"
                if markdown_report.exists():
                    print(f"📄 Markdown Report: {markdown_report}")
                    reports_shown.append("Markdown")
            
            # Stage 7 detailed analysis - only show if we actually ran Stage 7
            if start_stage <= 7 and end_stage >= 7:
                detailed_report = self.output_dir / "detailed_analysis_results.json"
                if detailed_report.exists():
                    print(f"🔍 Detailed Analysis: {detailed_report}")
                    reports_shown.append("Detailed Analysis")
            
            if not reports_shown:
                print("📋 No final reports generated (stages run did not include report generation)")
            
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
                from .path_utils import find_repo_root
                repo_root = find_repo_root()
                source_debug = repo_root / "pr_analyzer" / "debug_outputs" / "stage8_feedback"
                target_debug = self.output_dir / "debug_outputs" / "stage8_feedback"
                if source_debug.exists():
                    shutil.copytree(source_debug, target_debug, dirs_exist_ok=True)
                
                # Re-run HTML generation with updated data
                if self.run_stage8_html_generation():
                    print("✅ HTML report updated with feedback!")
                
                return True
            else:
                print("❌ Feedback update failed")
                return False
                
        except Exception as e:
            print(f"❌ Error updating analysis: {e}")
            return False