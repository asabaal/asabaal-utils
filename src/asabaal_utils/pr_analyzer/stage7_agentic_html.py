#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

class AgenticHTMLReportGenerator:
    def __init__(self, target_repo_path: str = None, output_dir: str = None):
        # Use current working directory as target repo if not specified
        self.target_repo = Path(target_repo_path) if target_repo_path else Path.cwd()
        
        # Set analyzer root to local output directory if provided, otherwise package directory
        if output_dir:
            self.analyzer_root = Path(output_dir)
            self.output_dir = Path(output_dir)
        else:
            self.analyzer_root = Path(__file__).parent.parent.parent.parent.parent / "pr_analyzer"
            self.output_dir = self.target_repo / "pr_analysis_output"
        
        self.output_dir.mkdir(exist_ok=True)
        
        self.debug_dir = self.output_dir / "debug_outputs" / "stage7_agentic"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.prompt_data_dir = self.output_dir / "prompt_data"
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_analysis_data(self) -> Dict[str, Any]:
        """Load all analysis data from previous stages"""
        print("📊 Loading comprehensive analysis data...")
        
        analysis_data = {}
        
        # Load Stage 1: Context and file analysis
        stage1_files = self.analyzer_root / "debug_outputs" / "stage1"
        if (stage1_files / "file_analysis_results.json").exists():
            with open(stage1_files / "file_analysis_results.json", 'r') as f:
                analysis_data['file_analysis'] = json.load(f)
                
        # Load Stage 3: Agent responses with detailed findings
        stage3_files = self.analyzer_root / "debug_outputs" / "stage3"
        analysis_data['agent_responses'] = {}
        
        response_files = [
            'duplicate_detection_full_response.txt',
            'merge_readiness_full_response.txt', 
            'pattern_analysis_full_response.txt',
            'quality_assessment_full_response.txt',
            'security_review_full_response.txt'
        ]
        
        for response_file in response_files:
            file_path = stage3_files / response_file
            if file_path.exists():
                with open(file_path, 'r') as f:
                    agent_name = response_file.replace('_full_response.txt', '')
                    analysis_data['agent_responses'][agent_name] = f.read()
        
        # Load Stage 6: Final combined results from MAIN output directory
        complete_analysis_file = self.analyzer_root / "complete_pr_analysis.json"
        if complete_analysis_file.exists():
            with open(complete_analysis_file, 'r') as f:
                analysis_data['complete_analysis'] = json.load(f)
                
        # Load markdown report for reference from MAIN output directory
        markdown_file = self.analyzer_root / "PR_ANALYSIS_REPORT.md"
        if markdown_file.exists():
            with open(markdown_file, 'r') as f:
                analysis_data['markdown_report'] = f.read()
        
        print(f"✅ Loaded analysis data with {len(analysis_data)} sections")
        return analysis_data
    
    def create_html_generation_prompt(self) -> str:
        """Create HTML generation prompt with file references"""
        
        instructions_file = self.prompt_data_dir / "html_generation_instructions.txt"
        
        prompt = f"""You are a senior UX engineer creating an interactive HTML dashboard.
Read detailed instructions from {instructions_file} and generate the HTML report.
Return ONLY complete HTML code."""

        return prompt
    
    def call_html_generation_agent(self, prompt: str) -> str:
        """Call Claude agent to generate HTML report"""
        print("🤖 Calling HTML generation agent...")
        
        # Save prompt to file for debugging
        prompt_file = self.debug_dir / "html_generation_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        print(f"💾 Saved prompt to {prompt_file}")
        
        # Check for OAuth token
        oauth_token = os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')
        if not oauth_token:
            raise Exception("CLAUDE_CODE_OAUTH_TOKEN not available - run 'claude setup-token'")
        
        try:
            # Call Claude agent with our established pattern
            cmd = ['claude', '-p', prompt]
            print(f"🔄 Running: claude -p <prompt> (prompt length: {len(prompt):,} chars)")
            
            result = subprocess.run(
                cmd,
                env={**os.environ, 'CLAUDE_CODE_OAUTH_TOKEN': oauth_token},
                capture_output=True,
                text=True,
                timeout=None  # No timeout
            )
            
            if result.returncode != 0:
                error_msg = f"Agent call failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout}"
                raise Exception(error_msg)
            
            response = result.stdout.strip()
            
            # Save full response for debugging
            response_file = self.debug_dir / "html_generation_full_response.txt"
            with open(response_file, 'w') as f:
                f.write(response)
            print(f"💾 Saved full response to {response_file}")
            print(f"✅ HTML generation agent completed ({len(response):,} chars)")
            
            return response
            
        except Exception as e:
            print(f"❌ Error calling HTML generation agent: {e}")
            raise
    
    def save_html_report(self, html_content: str) -> Path:
        """Save generated HTML report"""
        
        # Extract just the HTML if there's extra text
        html_start = html_content.find('<!DOCTYPE html>')
        if html_start == -1:
            html_start = html_content.find('<html>')
        if html_start > 0:
            html_content = html_content[html_start:]
            
        html_end = html_content.rfind('</html>') + 7
        if html_end < len(html_content):
            html_content = html_content[:html_end]
        
        # Save to target repository output directory
        html_file = self.output_dir / "pr_analysis_interactive.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        file_size = html_file.stat().st_size
        print(f"💾 Saved interactive HTML report: {html_file} ({file_size:,} bytes)")
        
        return html_file
    
    def run_stage7_agentic_html_test(self):
        """Run complete Stage 7 agentic HTML generation test"""
        print("=" * 80)
        print("🚀 STAGE 7: AGENTIC HTML REPORT GENERATION")
        print("🔧 DEBUG: Stage 7 is definitely being called!")
        print("=" * 80)
        
        try:
            # Step 1: Load all analysis data
            analysis_data = self.load_analysis_data()
            
            # Step 2: Create HTML generation prompt
            prompt = self.create_html_generation_prompt()
            print(f"📝 Created HTML generation prompt ({len(prompt):,} chars)")
            
            # Step 3: Call HTML generation agent
            html_response = self.call_html_generation_agent(prompt)
            print(f"✅ HTML generation agent completed ({len(html_response):,} chars)")
            
            # Step 4: Save HTML report
            html_file = self.save_html_report(html_response)
            
            # Step 5: Validation
            if html_file.exists() and html_file.stat().st_size > 10000:  # At least 10KB
                print("✅ STAGE 7 AGENTIC HTML: SUCCESS")
                print(f"📊 Generated comprehensive interactive HTML report: {html_file}")
                print(f"🔗 Open in browser: file://{html_file.absolute()}")
                return True
            else:
                print("❌ STAGE 7 AGENTIC HTML: FAILED - HTML file too small or missing")
                return False
                
        except Exception as e:
            print(f"❌ STAGE 7 AGENTIC HTML: FAILED with error: {e}")
            return False

def main():
    generator = AgenticHTMLReportGenerator()
    success = generator.run_stage7_agentic_html_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()