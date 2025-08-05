#!/usr/bin/env python3
"""
Stage 8: File-Level Merge Readiness Assessment

This stage performs detailed file-level analysis to determine merge readiness,
business impact, risk assessment, and code element analysis for each file.
Saves structured outputs that Stage 9 (HTML generation) can quickly read.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

class FileAssessmentGenerator:
    def __init__(self, target_repo_path: str = None, output_dir: str = None):
        # Use current working directory as target repo if not specified
        self.target_repo = Path(target_repo_path) if target_repo_path else Path.cwd()
        
        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.target_repo / "pr_analysis_output"
        
        self.output_dir.mkdir(exist_ok=True)
        
        self.debug_dir = self.output_dir / "debug_outputs" / "stage8_file_assessment"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.prompt_data_dir = self.output_dir / "prompt_data"
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_stage7_results(self) -> Dict[str, Any]:
        """Load Stage 7 detailed analysis results"""
        print("📊 Loading Stage 7 detailed analysis results...")
        
        stage7_file = self.output_dir / "detailed_analysis_results.json"
        if stage7_file.exists():
            with open(stage7_file, 'r') as f:
                stage7_data = json.load(f)
                file_count = stage7_data.get('analysis_summary', {}).get('total_files_analyzed', 0)
                print(f"✅ Loaded Stage 7 results: {file_count} files analyzed")
                return stage7_data
        else:
            print("⚠️  Stage 7 results not found - cannot perform file assessment")
            return {}
    
    def create_file_assessment_prompt(self, stage7_data: Dict[str, Any]) -> str:
        """Create prompt for comprehensive file-level assessment"""
        
        data_file = self.prompt_data_dir / "file_assessment_data.json"
        
        # Save Stage 7 data for the agent to read
        with open(data_file, 'w') as f:
            json.dump(stage7_data, f, indent=2)
        
        file_analyses = stage7_data.get('file_analyses', [])
        file_count = len(file_analyses)
        
        prompt = f"""You are a senior software architect performing comprehensive file-level merge readiness assessment.

DATA: Read all Stage 7 analysis data from {data_file}

TASK: Enhance the existing file analysis with detailed merge readiness assessment.

INPUT DATA: {file_count} files with basic analysis from Stage 7
Each file currently has: file_path, merge_readiness, overall_assessment, feedback, code_elements

REQUIREMENTS:
1. For EACH file, provide enhanced assessment:
   - Confirm or refine merge_readiness: "ready" | "conditional" | "not_ready"
   - Detailed business_impact_score (1-10)
   - Technical_risk_score (1-10) 
   - Specific feedback for conditional/not_ready files
   - Code quality assessment
   - Dependencies and potential conflicts

2. Generate summary statistics:
   - Total files: {file_count}
   - Ready files count
   - Conditional files count  
   - Not ready files count
   - Overall merge confidence (0-1)

3. Create priority recommendations for non-ready files

OUTPUT FORMAT: Return valid JSON with this exact structure:
{{
  "assessment_summary": {{
    "total_files": {file_count},
    "ready_files": 0,
    "conditional_files": 0,
    "not_ready_files": 0,
    "overall_confidence": 0.0,
    "assessment_timestamp": "2025-01-01T00:00:00Z"
  }},
  "file_assessments": [
    {{
      "file_path": "path/to/file.ext",
      "merge_readiness": "ready|conditional|not_ready",
      "business_impact_score": 5,
      "technical_risk_score": 3,
      "overall_assessment": {{
        "purpose": "File purpose description",
        "business_impact": "Impact description", 
        "risk_assessment": "Risk description"
      }},
      "detailed_feedback": "Specific feedback for improvement",
      "code_elements": {{
        "classes": ["ClassName1", "ClassName2"],
        "functions": ["function1", "function2"]
      }},
      "recommendations": ["Recommendation 1", "Recommendation 2"]
    }}
  ],
  "priority_actions": [
    {{
      "priority": "high|medium|low",
      "description": "Action description",
      "affected_files": ["file1.py", "file2.js"],
      "estimated_effort": "1-2 hours"
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON response. No explanations or markdown formatting."""
        
        return prompt
    
    def call_assessment_agent(self, prompt: str) -> str:
        """Call Claude agent for file assessment"""
        print("🤖 Calling file assessment agent...")
        
        # Save prompt for debugging
        prompt_file = self.debug_dir / "file_assessment_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        print(f"💾 Saved prompt to {prompt_file}")
        
        # Check for OAuth token
        oauth_token = os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')
        if not oauth_token:
            raise Exception("CLAUDE_CODE_OAUTH_TOKEN not available - run 'claude setup-token'")
        
        try:
            # Call Claude agent
            cmd = ['claude', '-p', prompt]
            print(f"🔄 Running file assessment agent (prompt length: {len(prompt):,} chars)")
            
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
                    error_msg += f"\\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\\nSTDOUT: {result.stdout}"
                raise Exception(error_msg)
            
            response = result.stdout.strip()
            
            # Save full response for debugging
            response_file = self.debug_dir / "file_assessment_full_response.txt"
            with open(response_file, 'w') as f:
                f.write(response)
            print(f"💾 Saved full response to {response_file}")
            print(f"✅ File assessment agent completed ({len(response):,} chars)")
            
            return response
            
        except Exception as e:
            print(f"❌ Error calling file assessment agent: {e}")
            raise
    
    def save_assessment_results(self, comprehensive_data: Dict[str, Any]) -> Path:
        """Save comprehensive file assessment results for Stage 9 to read"""
        
        try:
            # Save main results file with comprehensive data
            results_file = self.output_dir / "file_assessment_results.json"
            with open(results_file, 'w') as f:
                json.dump(comprehensive_data, f, indent=2)
            
            # Generate summary from comprehensive data
            file_assessments = comprehensive_data.get('file_assessments', [])
            ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'ready')
            conditional_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'conditional')
            not_ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'not_ready')
            total_count = len(file_assessments)
            
            # Save summary for quick access
            summary_file = self.output_dir / "file_assessment_summary.txt"
            with open(summary_file, 'w') as f:
                f.write(f"Stage 8: File-Level Merge Readiness Assessment\\n")
                f.write(f"=" * 50 + "\\n")
                f.write(f"Total Files: {total_count}\\n")
                f.write(f"Ready Files: {ready_count}\\n")
                f.write(f"Conditional Files: {conditional_count}\\n")
                f.write(f"Not Ready Files: {not_ready_count}\\n")
                f.write(f"Overall Confidence: {ready_count/total_count:.2f}\\n")
                f.write(f"Assessment Time: {comprehensive_data.get('assessment_timestamp', 'Unknown')}\\n")
            
            file_size = results_file.stat().st_size
            print(f"💾 Saved comprehensive file assessment results: {results_file} ({file_size:,} bytes)")
            print(f"📊 Assessment summary: {total_count} files analyzed")
            
            return results_file
            
        except Exception as e:
            print(f"❌ Error saving comprehensive assessment results: {e}")
            raise
    
    def create_comprehensive_assessment(self, stage7_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive assessment by enhancing Stage 7 data with detailed scoring"""
        
        file_analyses = stage7_data.get('file_analyses', [])
        enhanced_assessments = []
        
        for file_analysis in file_analyses:
            # Enhance each file with detailed assessment scores
            enhanced_file = {
                "file_path": file_analysis.get('file_path', ''),
                "merge_readiness": file_analysis.get('merge_readiness', 'unknown'),
                "business_impact_score": self._calculate_business_impact_score(file_analysis),
                "technical_risk_score": self._calculate_technical_risk_score(file_analysis),
                "overall_assessment": file_analysis.get('overall_assessment', {}),
                "detailed_feedback": file_analysis.get('feedback', ''),
                "code_elements": file_analysis.get('code_elements', {"classes": [], "functions": []}),
                "recommendations": self._generate_recommendations(file_analysis)
            }
            enhanced_assessments.append(enhanced_file)
        
        # Generate summary statistics
        ready_count = sum(1 for f in enhanced_assessments if f['merge_readiness'] == 'ready')
        conditional_count = sum(1 for f in enhanced_assessments if f['merge_readiness'] == 'conditional')
        not_ready_count = sum(1 for f in enhanced_assessments if f['merge_readiness'] == 'not_ready')
        total_count = len(enhanced_assessments)
        
        comprehensive_data = {
            "assessment_summary": {
                "total_files": total_count,
                "ready_files": ready_count,
                "conditional_files": conditional_count,
                "not_ready_files": not_ready_count,
                "overall_confidence": ready_count / total_count if total_count > 0 else 0.0,
                "assessment_timestamp": "2025-01-04T00:00:00Z"
            },
            "file_assessments": enhanced_assessments,
            "priority_actions": self._generate_priority_actions(enhanced_assessments)
        }
        
        return comprehensive_data
    
    def _calculate_business_impact_score(self, file_analysis: Dict[str, Any]) -> int:
        """Calculate business impact score based on file analysis"""
        file_path = file_analysis.get('file_path', '').lower()
        merge_readiness = file_analysis.get('merge_readiness', '')
        
        # High impact files
        if any(pattern in file_path for pattern in ['index.html', 'main.', 'app.', 'contact', 'supabase']):
            return 9 if merge_readiness == 'ready' else 8
        # Medium impact files  
        elif any(pattern in file_path for pattern in ['.html', '.js', '.css', 'blog']):
            return 7 if merge_readiness == 'ready' else 6
        # Lower impact files
        else:
            return 5 if merge_readiness == 'ready' else 4
    
    def _calculate_technical_risk_score(self, file_analysis: Dict[str, Any]) -> int:
        """Calculate technical risk score based on file analysis"""
        merge_readiness = file_analysis.get('merge_readiness', '')
        file_path = file_analysis.get('file_path', '').lower()
        
        if merge_readiness == 'not_ready':
            return 8 if 'template' in file_path or 'placeholder' in file_path else 7
        elif merge_readiness == 'conditional':
            return 6 if any(pattern in file_path for pattern in ['.js', 'forms', 'client']) else 5
        else:  # ready
            return 3 if '.svg' in file_path and 'large' in file_path else 2
    
    def _generate_recommendations(self, file_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on file analysis"""
        recommendations = []
        file_path = file_analysis.get('file_path', '').lower()
        merge_readiness = file_analysis.get('merge_readiness', '')
        detailed_feedback = file_analysis.get('feedback', '')
        
        if merge_readiness == 'not_ready':
            # Check for specific issues mentioned in detailed feedback
            if 'placeholder' in detailed_feedback.lower() or 'template' in detailed_feedback.lower():
                recommendations.extend(["Complete template content", "Remove placeholder text", "Add actual content"])
            elif 'draft' in detailed_feedback.lower():
                recommendations.extend(["Complete draft content", "Review and publish when ready"])
            elif 'missing' in detailed_feedback.lower() or 'incomplete' in detailed_feedback.lower():
                recommendations.extend(["Complete missing content", "Review file completeness"])
            elif 'error' in detailed_feedback.lower() or 'issue' in detailed_feedback.lower():
                recommendations.extend(["Fix identified issues", "Review and test changes"])
            else:
                # Generic not_ready recommendations
                recommendations.extend(["Address issues mentioned in feedback", "Review before merge"])
                
            # File-type specific recommendations for not_ready files
            if '.svg' in file_path:
                recommendations.append("Optimize file size if needed")
            elif '.json' in file_path and 'config' in file_path:
                recommendations.append("Validate JSON structure")
            elif '.js' in file_path:
                recommendations.append("Test functionality")
                
        elif merge_readiness == 'conditional':
            # Conditional files need specific conditions met
            if 'form' in file_path or 'client' in file_path:
                recommendations.extend(["Add input validation", "Implement rate limiting"])
            elif 'config' in file_path:
                recommendations.extend(["Review configuration values", "Test in staging environment"])
            elif 'script' in file_path or '.js' in file_path:
                recommendations.extend(["Add error handling", "Test edge cases"])
            else:
                recommendations.extend(["Review conditions mentioned in feedback", "Test thoroughly before merge"])
                
        elif merge_readiness == 'ready':
            recommendations.append("File is ready for merge")
        else:
            # Unknown status
            recommendations.append("Review file status and requirements")
        
        return recommendations
    
    def _generate_priority_actions(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate priority actions based on assessments"""
        not_ready_files = [f for f in assessments if f['merge_readiness'] == 'not_ready']
        conditional_files = [f for f in assessments if f['merge_readiness'] == 'conditional']
        
        actions = []
        
        if not_ready_files:
            template_files = [f['file_path'] for f in not_ready_files if 'template' in f['file_path']]
            if template_files:
                actions.append({
                    "priority": "high",
                    "description": "Complete or remove template files with placeholder content",
                    "affected_files": template_files,
                    "estimated_effort": "2-4 hours"
                })
        
        if conditional_files:
            js_files = [f['file_path'] for f in conditional_files if f['file_path'].endswith('.js')]
            if js_files:
                actions.append({
                    "priority": "medium", 
                    "description": "Enhance security and validation for JavaScript files",
                    "affected_files": js_files,
                    "estimated_effort": "3-5 hours"
                })
        
        return actions
    
    def run_stage8_file_assessment(self):
        """Run complete Stage 8 file-level assessment"""
        print("=" * 80)
        print("🚀 STAGE 8: FILE-LEVEL MERGE READINESS ASSESSMENT")
        print("=" * 80)
        
        try:
            # Step 1: Load Stage 7 results
            stage7_data = self.load_stage7_results()
            if not stage7_data:
                print("❌ STAGE 8: FAILED - No Stage 7 data available")
                return False
            
            # Step 2: Create comprehensive assessment from Stage 7 data
            print(f"🔄 Enhancing {len(stage7_data.get('file_analyses', []))} files with detailed assessment scores...")
            comprehensive_data = self.create_comprehensive_assessment(stage7_data)
            
            # Step 3: Save comprehensive results for Stage 9
            results_file = self.save_assessment_results(comprehensive_data)
            
            # Step 4: Validation
            if results_file.exists() and results_file.stat().st_size > 10000:
                print("✅ STAGE 8: SUCCESS")
                print(f"📊 Comprehensive file assessment results saved: {results_file}")
                print(f"➡️  Stage 9 can now read these results for HTML generation")
                return True
            else:
                print("❌ STAGE 8: FAILED - Results file too small or missing")
                return False
                
        except Exception as e:
            print(f"❌ STAGE 8: FAILED with error: {e}")
            return False

def main():
    generator = FileAssessmentGenerator()
    success = generator.run_stage8_file_assessment()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()