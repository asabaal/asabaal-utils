#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class FeedbackUpdateSystem:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.debug_dir = self.project_root / "debug_outputs" / "stage8_feedback"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_data_dir = self.project_root / "prompt_data"
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
        
    def create_feedback_instructions(self, user_feedback: str, feedback_files: list = None) -> str:
        """Create instructions file for feedback update agent"""
        
        instructions = f"""TASK: Update PR analysis report based on user feedback

USER FEEDBACK:
{user_feedback}

ADDITIONAL FILES PROVIDED:
{', '.join(feedback_files) if feedback_files else 'None'}

EXISTING ANALYSIS DATA TO READ:
- debug_outputs/stage6/PR_ANALYSIS_REPORT.md (current report)
- debug_outputs/stage6/complete_pr_analysis.json (structured data)
- debug_outputs/stage3/duplicate_detection_full_response.txt (agent findings)
- debug_outputs/stage3/merge_readiness_full_response.txt (agent findings)

REQUIREMENTS:
- Incorporate user feedback into analysis
- Update recommendations based on feedback
- Preserve existing valid findings
- Generate updated markdown report
- Update structured JSON data

OUTPUT: 
1. Updated PR_ANALYSIS_REPORT.md
2. Updated complete_pr_analysis.json
"""
        
        # Save instructions file
        instructions_file = self.prompt_data_dir / "feedback_update_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
            
        return str(instructions_file)
    
    def create_feedback_update_prompt(self, instructions_file: str) -> str:
        """Create prompt for feedback update agent"""
        
        prompt = f"""You are a senior technical analyst updating PR analysis based on user feedback.
Read instructions from {instructions_file} and update the analysis accordingly.
Generate updated markdown report and JSON data."""

        return prompt
    
    def call_feedback_update_agent(self, prompt: str) -> str:
        """Call Claude agent to update analysis based on feedback"""
        print("🤖 Calling feedback update agent...")
        
        # Save prompt to file for debugging
        prompt_file = self.debug_dir / "feedback_update_prompt.txt"
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
            response_file = self.debug_dir / "feedback_update_full_response.txt"
            with open(response_file, 'w') as f:
                f.write(response)
            print(f"💾 Saved full response to {response_file}")
            print(f"✅ Feedback update agent completed ({len(response):,} chars)")
            
            return response
            
        except Exception as e:
            print(f"❌ Error calling feedback update agent: {e}")
            raise
    
    def process_feedback_update(self, user_feedback: str, feedback_files: list = None) -> bool:
        """Process user feedback and update analysis"""
        print("=" * 80)
        print("🔄 STAGE 8: FEEDBACK UPDATE SYSTEM")
        print("=" * 80)
        
        try:
            # Step 1: Create feedback instructions
            instructions_file = self.create_feedback_instructions(user_feedback, feedback_files)
            print(f"📝 Created feedback instructions: {instructions_file}")
            
            # Step 2: Create update prompt
            prompt = self.create_feedback_update_prompt(instructions_file)
            print(f"📝 Created update prompt ({len(prompt):,} chars)")
            
            # Step 3: Call feedback update agent
            update_response = self.call_feedback_update_agent(prompt)
            
            # Step 4: Validation
            if len(update_response) > 100:  # Basic validation
                print("✅ STAGE 8 FEEDBACK UPDATE: SUCCESS")
                print(f"📊 Generated feedback-based analysis update")
                return True
            else:
                print("❌ STAGE 8 FEEDBACK UPDATE: FAILED - Response too short")
                return False
                
        except Exception as e:
            print(f"❌ STAGE 8 FEEDBACK UPDATE: FAILED with error: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_stage8_feedback_updates.py '<user_feedback>' [additional_files...]")
        print("Example: python test_stage8_feedback_updates.py 'The duplicate analysis missed some config files'")
        sys.exit(1)
    
    user_feedback = sys.argv[1]
    feedback_files = sys.argv[2:] if len(sys.argv) > 2 else None
    
    system = FeedbackUpdateSystem()
    success = system.process_feedback_update(user_feedback, feedback_files)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()