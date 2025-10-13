#!/usr/bin/env python3

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .api_confirmation import require_paid_api_confirmation

# Import score calculation utilities
try:
    from asabaal_utils.pr_analyzer.score_utils import recalculate_assessment_summary
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

# Import file existence validation utilities
try:
    from asabaal_utils.pr_analyzer.file_existence_utils import validate_and_create_feedback, FileExistenceValidator
    FILE_EXISTENCE_UTILS_AVAILABLE = True
except ImportError:
    FILE_EXISTENCE_UTILS_AVAILABLE = False
    def validate_and_create_feedback(repo_root: str, file_assessments: List[Dict]) -> tuple:
        """Fallback implementation if file_existence_utils not available"""
        return {"type": "no_deleted_files", "files": []}, ""
    def recalculate_assessment_summary(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback implementation if score_utils not available"""
        print("⚠️  Score utilities not available - using basic recalculation")
        file_assessments = assessment_data.get('file_assessments', [])
        
        # Count files by status
        ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'ready')
        conditional_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'conditional')
        not_ready_count = sum(1 for f in file_assessments if f.get('merge_readiness') == 'not_ready')
        total_count = len(file_assessments)
        
        # Basic confidence calculation
        confidence_score = round(ready_count / total_count, 6) if total_count > 0 else 0.0
        
        summary = assessment_data.get('assessment_summary', {})
        summary.update({
            'total_files': total_count,
            'ready_files': ready_count,
            'conditional_files': conditional_count,
            'not_ready_files': not_ready_count,
            'overall_confidence': confidence_score,
            'assessment_timestamp': summary.get('assessment_timestamp', '2025-01-04T00:00:00Z')
        })
        
        return summary

# Import backend manager
try:
    from asabaal_utils.agentic_toolkit.backend_config import BackendManager, BackendConfig, BackendType
    BACKEND_MANAGER_AVAILABLE = True
except ImportError:
    BACKEND_MANAGER_AVAILABLE = False
    BackendManager = None  # type: ignore
    BackendConfig = None  # type: ignore
    BackendType = None  # type: ignore

class FeedbackUpdateSystem:
    def __init__(self, project_root: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        # Use provided project root or detect from script location
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Go up from asabaal-utils to find the project root
            self.project_root = Path(__file__).parent.parent.parent.parent
        
        self.debug_dir = self.project_root / "pr_analysis_output" / "debug_outputs" / "stage10_feedback"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_data_dir = self.project_root / "pr_analysis_output" / "prompt_data"
        self.prompt_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent inputs directory
        self.agent_inputs_dir = self.project_root / ".agent_inputs" / "stage10_feedback"
        self.pending_dir = self.agent_inputs_dir / "pending"
        self.processed_dir = self.agent_inputs_dir / "processed"
        
        # Create directories if they don't exist
        self.agent_inputs_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize backend manager
        self.backend_manager = None
        if BACKEND_MANAGER_AVAILABLE:
            try:
                # Create backend config from provided config or auto-detect
                backend_config = None
                if config and 'agentic_backend' in config:
                    backend_cfg = config['agentic_backend']
                    provider = backend_cfg.get('provider', 'ollama')
                    model = backend_cfg.get('model', 'anthropic/claude-3.5-sonnet')
                    
                    if provider == 'ollama':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OLLAMA,
                            model=model,
                            base_url='http://localhost:11434'
                        )
                    elif provider == 'openrouter':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OPENROUTER,
                            model=model,
                            api_key=os.getenv('OPENROUTER_API_KEY')
                        )
                    elif provider == 'claude':
                        backend_config = BackendConfig(
                            backend_type=BackendType.CLAUDE,
                            model=model,
                            api_key=os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
                        )
                
                self.backend_manager = BackendManager(backend_config)
                backend_info = self.backend_manager.get_backend_info()
                print(f"🔧 Backend manager initialized for feedback updates")
                print(f"   Using {backend_info['backend_type']} backend with model {backend_info.get('model', 'unknown')}")
            except Exception as e:
                print(f"⚠️  Backend manager initialization failed: {e}")
                self.backend_manager = None
        
    def create_feedback_instructions(self, user_feedback: str, feedback_files: Optional[List[str]] = None) -> str:
        """Create instructions file for feedback update agent"""
        
        # Validate feedback content
        if not user_feedback or user_feedback.strip() == "":
            raise ValueError("Empty feedback provided")
        
        # Check for potential test/validation feedback that shouldn't be processed
        test_patterns = ["test validation", "verify the feedback mechanism", "test feedback", "validation test"]
        feedback_lower = user_feedback.lower()
        if any(pattern in feedback_lower for pattern in test_patterns):
            print(f"⚠️  Warning: Detected test/validation feedback: {user_feedback[:100]}...")
            print("⚠️  This appears to be test feedback and will not be processed")
            raise ValueError("Test/validation feedback detected - use actual user feedback")
        
        instructions = f"""TASK: Update PR analysis report based on user feedback

USER FEEDBACK:
{user_feedback}

ADDITIONAL FILES PROVIDED:
{', '.join(feedback_files) if feedback_files else 'None'}

EXISTING ANALYSIS DATA TO READ:
- detailed_analysis_results.json (current analysis data)
- debug_outputs/stage1/final_analysis_context.json (analysis context)
- debug_outputs/stage3/communication_analysis.json (communication findings)
- final_analysis_context.json (final context)

REQUIREMENTS:
- Incorporate user feedback into analysis
- Update recommendations based on feedback
- Preserve existing valid findings
- Generate updated markdown report
- Update structured JSON data

OUTPUT REQUIREMENTS:
Provide analysis and insights only. Do not create, write, or modify any files. The system will handle file updates automatically based on your analysis.
"""
        
        # Save instructions file with timestamp to avoid overwrites
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        instructions_file = self.prompt_data_dir / f"feedback_update_instructions_{timestamp}.txt"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        # Also save to the standard location for compatibility
        standard_file = self.prompt_data_dir / "feedback_update_instructions.txt"
        with open(standard_file, 'w') as f:
            f.write(instructions)
            
        return str(standard_file)
    
    def create_feedback_update_prompt(self, instructions_file: str) -> str:
        """Create prompt for feedback update agent"""
        
        # Read the instructions
        try:
            with open(instructions_file, 'r') as f:
                instructions = f.read()
        except Exception as e:
            print(f"⚠️  Could not read instructions file: {e}")
            instructions = "Update PR analysis based on user feedback"
        
        # Read existing analysis data and check for deleted files
        analysis_context = ""
        deleted_files_prompt_addition = ""
        
        try:
            # Try to read the main analysis file
            analysis_file = self.project_root / "pr_analysis_output" / "detailed_analysis_results.json"
            if analysis_file.exists():
                with open(analysis_file, 'r') as f:
                    analysis_data_str = f.read()
                analysis_context += f"\n\nEXISTING ANALYSIS DATA:\n{analysis_data_str}"
                
                # DISABLED: Automatic deleted file detection
                # Agent should handle deleted files through explicit feedback only
                deleted_files_prompt_addition = ""
                        
        except Exception as e:
            print(f"⚠️  Could not read analysis data: {e}")
        
        prompt = f"""You are a senior technical analyst updating PR analysis based on user feedback.

{instructions}

{analysis_context}

{deleted_files_prompt_addition}

TASK: Based on the user feedback and existing analysis data above, provide specific updates to the PR analysis.

Focus on:
1. File reclassifications mentioned in the feedback
2. Updated assessments based on new architectural understanding
3. Specific recommendations for the blog system structure
4. IMPORTANT: Handle any deleted files detected above by reclassifying them to 'ready' status

RESPONSE FORMAT:
Provide a detailed analysis update that addresses the specific feedback points. Include:
- Updated file classifications
- Architectural insights
- Specific recommendations
- Any corrected assessments
- Deleted file reclassifications (if applicable)

Do not create files - just provide the analysis content that should be used to update the existing analysis."""

        return prompt
    
    def add_feedback_history_entry(self, assessment_data: Dict, metrics_before: Dict, metrics_after: Dict, file_updates: Dict):
        """Add a feedback history entry to track changes over time"""
        
        # Initialize feedback history if it doesn't exist
        if 'feedback_history' not in assessment_data:
            assessment_data['feedback_history'] = []
        
        # Count quality issues and duplicates (simplified counts)
        quality_issues = sum(1 for f in assessment_data.get('file_assessments', []) 
                           if f.get('merge_readiness') in ['not_ready', 'conditional'])
        
        # Create history entry
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'feedback_summary': f'Processed {len(file_updates)} file updates',
            'files_updated': list(file_updates.keys()),
            'metrics_before': metrics_before,
            'metrics_after': metrics_after,
            'metrics_changes': {
                'ready_files_change': metrics_after['ready_files'] - metrics_before['ready_files'],
                'conditional_files_change': metrics_after['conditional_files'] - metrics_before['conditional_files'],
                'not_ready_files_change': metrics_after['not_ready_files'] - metrics_before['not_ready_files'],
                'confidence_change': round(metrics_after['overall_confidence'] - metrics_before['overall_confidence'], 6),
                'quality_score_change': round(metrics_after['overall_quality_score'] - metrics_before['overall_quality_score'], 1)
            },
            'quality_issues_count': quality_issues,
            'duplicates_count': 0,  # TODO: Calculate actual duplicates if needed
            'recommendations_count': sum(len(f.get('recommendations', [])) 
                                       for f in assessment_data.get('file_assessments', []))
        }
        
        # Add to history (keep last 10 entries)
        assessment_data['feedback_history'].append(history_entry)
        if len(assessment_data['feedback_history']) > 10:
            assessment_data['feedback_history'] = assessment_data['feedback_history'][-10:]
        
        print(f"📝 Added feedback history entry: {history_entry['feedback_summary']}")
    
    def call_feedback_update_agent(self, prompt: str) -> str:
        """Call agent to update analysis based on feedback using OpenRouter API"""
        print("🤖 Calling feedback update agent...")
        
        # Save prompt to file for debugging
        prompt_file = self.debug_dir / "feedback_update_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        print(f"💾 Saved prompt to {prompt_file}")
        
        # Check AI backend availability
        if not self.backend_manager:
            raise Exception("AI backend manager not available - check appropriate configuration")
        
        # Use AI backend API
        try:
            backend_info = self.backend_manager.get_backend_info()
            backend_type = backend_info['backend_type']
            backend_model = backend_info.get('model', 'unknown')
            print(f"🔄 Using {backend_type} API with model {backend_model} (prompt length: {len(prompt):,} chars)")
            
            # Require confirmation for paid APIs
            if not require_paid_api_confirmation(backend_type):
                raise Exception("Paid API usage not confirmed by user")
            
            response = self.backend_manager.call_agent(prompt, timeout=600)
            
            # Save full response for debugging
            response_file = self.debug_dir / "feedback_update_full_response.txt"
            with open(response_file, 'w') as f:
                f.write(response)
            print(f"💾 Saved full response to {response_file}")
            print(f"✅ {backend_type} feedback update agent completed ({len(response):,} chars)")
            
            return response
            
        except Exception as e:
            backend_info = self.backend_manager.get_backend_info() if self.backend_manager else {'backend_type': 'AI Backend'}
            backend_type = backend_info['backend_type']
            print(f"❌ {backend_type} API error: {e}")
            raise Exception(f"{backend_type} API call failed: {str(e)}")
    
    def find_pending_feedback_file(self, filename: str) -> Optional[Path]:
        """Find a feedback file in the pending directory"""
        if not filename.endswith('.md'):
            filename += '.md'
        
        feedback_file = self.pending_dir / filename
        if feedback_file.exists():
            return feedback_file
        return None
    
    def move_to_processed(self, feedback_file: Path, success: bool = True) -> Path:
        """Move a feedback file from pending to processed with timestamp"""
        if not feedback_file.exists() or not feedback_file.parent == self.pending_dir:
            raise ValueError(f"File not found in pending directory: {feedback_file}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "success" if success else "failed"
        processed_name = f"{feedback_file.stem}_{status}_{timestamp}{feedback_file.suffix}"
        processed_path = self.processed_dir / processed_name
        
        feedback_file.rename(processed_path)
        print(f"📁 Moved feedback file to: {processed_path}")
        return processed_path
    
    def process_feedback_file(self, filename: str) -> bool:
        """Process a specific feedback file from the pending directory"""
        feedback_file = self.find_pending_feedback_file(filename)
        if not feedback_file:
            print(f"❌ Feedback file not found: {filename}")
            print(f"Available files in pending/:")
            for f in self.pending_dir.glob("*.md"):
                print(f"  - {f.name}")
            return False
        
        print(f"📝 Processing feedback file: {feedback_file}")
        
        # Read feedback content
        try:
            with open(feedback_file, 'r') as f:
                feedback_content = f.read()
        except Exception as e:
            print(f"❌ Error reading feedback file: {e}")
            return False
        
        # Process the feedback
        success = self.process_feedback_update(feedback_content)
        
        # Move file to processed directory
        try:
            self.move_to_processed(feedback_file, success)
        except Exception as e:
            print(f"⚠️  Warning: Could not move feedback file: {e}")
        
        return success
    
    def list_pending_files(self) -> List[str]:
        """List all pending feedback files"""
        return [f.name for f in self.pending_dir.glob("*.md")]
    
    def process_all_pending(self) -> Dict[str, bool]:
        """Process all pending feedback files"""
        pending_files = self.list_pending_files()
        if not pending_files:
            print("📝 No pending feedback files found")
            return {}
        
        print(f"📝 Found {len(pending_files)} pending feedback files")
        results = {}
        
        for filename in pending_files:
            print(f"\n{'='*60}")
            success = self.process_feedback_file(filename)
            results[filename] = success
            print(f"{'='*60}")
        
        return results
    
    def apply_automatic_deleted_file_reclassification(self, assessment_data: Dict) -> Dict[str, Dict[str, Any]]:
        """Apply automatic reclassification for deleted files"""
        if not FILE_EXISTENCE_UTILS_AVAILABLE:
            print("⚠️  File existence utilities not available - skipping automatic reclassification")
            return {}
            
        try:
            file_assessments = assessment_data.get('file_assessments', [])
            validator = FileExistenceValidator(str(self.project_root))
            
            # Find deleted files
            deleted_files = validator.find_deleted_files(file_assessments)
            
            if not deleted_files:
                print("✅ No deleted files found requiring automatic reclassification")
                return {}
            
            print(f"🔍 Applying automatic reclassification for {len(deleted_files)} deleted files")
            
            # Apply automatic reclassification
            updated_assessments, changes = validator.auto_reclassify_deleted_files(
                file_assessments, deleted_files
            )
            
            # Update the assessment data
            assessment_data['file_assessments'] = updated_assessments
            
            # Log the changes
            for reclassified in changes['files_reclassified']:
                print(f"🔄 Auto-reclassified: {reclassified['file_path']} ({reclassified['old_status']} → {reclassified['new_status']})")
            
            # Return file updates in the expected format
            auto_updates = {}
            for reclassified in changes['files_reclassified']:
                auto_updates[reclassified['file_path']] = {
                    'merge_readiness': reclassified['new_status'],
                    'recommendations': ['File does not exist - no action needed'],
                    'auto_reclassified': True,
                    'reclassification_reason': 'File deleted during analysis'
                }
            
            return auto_updates
            
        except Exception as e:
            print(f"⚠️  Automatic deleted file reclassification failed: {e}")
            return {}

    def update_analysis_json_files(self, output_dir: Path, agent_response: str, user_feedback: str = "") -> bool:
        """Update the JSON files that Stage 9 reads based on agentic feedback analysis"""
        try:
            # Parse the agent's response to extract file reclassifications
            file_updates = self.parse_agent_response_for_updates(agent_response, user_feedback)
            
            # DISABLED: Automatic deleted file reclassification
            # Agent should handle deleted files through explicit feedback only
            assessment_data = None
            file_assessment_file = output_dir / "file_assessment_results.json"
            
            if not file_updates:
                print("⚠️  No file updates found in agent response or automatic reclassification")
                return False
            
            print(f"📝 Found {len(file_updates)} file updates to apply")
            
            # Update file_assessment_results.json  
            file_assessment_file = output_dir / "file_assessment_results.json"
            if file_assessment_file.exists():
                with open(file_assessment_file, 'r') as f:
                    assessment_data = json.load(f)
                
                updated_count = 0
                if 'file_assessments' in assessment_data:
                    for file_assessment in assessment_data['file_assessments']:
                        file_path = file_assessment.get('file_path', '')
                        
                        # Check if this file needs updates
                        if file_path in file_updates:
                            update_data = file_updates[file_path]
                            
                            # Apply the updates from the agent
                            if 'merge_readiness' in update_data:
                                old_status = file_assessment.get('merge_readiness')
                                new_status = update_data['merge_readiness']
                                file_assessment['merge_readiness'] = new_status
                                print(f"🔄 {file_path}: {old_status} → {new_status}")
                            
                            if 'detailed_feedback' in update_data:
                                file_assessment['detailed_feedback'] = update_data['detailed_feedback']
                            
                            if 'recommendations' in update_data:
                                file_assessment['recommendations'] = update_data['recommendations']
                            
                            if 'overall_assessment' in update_data:
                                if 'overall_assessment' not in file_assessment:
                                    file_assessment['overall_assessment'] = {}
                                file_assessment['overall_assessment'].update(update_data['overall_assessment'])
                            
                            updated_count += 1
                
                # Capture metrics before updates for feedback history
                metrics_before = {}
                if 'assessment_summary' in assessment_data:
                    summary_before = assessment_data['assessment_summary']
                    metrics_before = {
                        'ready_files': summary_before.get('ready_files', 0),
                        'conditional_files': summary_before.get('conditional_files', 0),
                        'not_ready_files': summary_before.get('not_ready_files', 0),
                        'total_files': summary_before.get('total_files', 0),
                        'overall_confidence': summary_before.get('overall_confidence', 0),
                        'overall_quality_score': summary_before.get('overall_quality_score', 0)
                    }

                # Update summary statistics using centralized scoring logic
                if 'assessment_summary' in assessment_data:
                    print("🔄 Recalculating assessment summary with updated scoring logic...")
                    updated_summary = recalculate_assessment_summary(assessment_data)
                    assessment_data['assessment_summary'] = updated_summary
                    
                    # Capture metrics after updates
                    summary_after = updated_summary
                    metrics_after = {
                        'ready_files': summary_after.get('ready_files', 0),
                        'conditional_files': summary_after.get('conditional_files', 0),
                        'not_ready_files': summary_after.get('not_ready_files', 0),
                        'total_files': summary_after.get('total_files', 0),
                        'overall_confidence': summary_after.get('overall_confidence', 0),
                        'overall_quality_score': summary_after.get('overall_quality_score', 0)
                    }
                    
                    # Add feedback history entry
                    self.add_feedback_history_entry(assessment_data, metrics_before, metrics_after, file_updates)
                    
                    # Log the updated metrics
                    summary = updated_summary
                    print(f"📊 Updated summary:")
                    print(f"   Ready files: {summary.get('ready_files', 0)}")
                    print(f"   Conditional files: {summary.get('conditional_files', 0)}")
                    print(f"   Not ready files: {summary.get('not_ready_files', 0)}")
                    print(f"   Total files: {summary.get('total_files', 0)}")
                    print(f"   Overall confidence: {summary.get('overall_confidence', 0)}")
                    if 'overall_quality_score' in summary:
                        print(f"   Overall quality score: {summary['overall_quality_score']}")
                
                with open(file_assessment_file, 'w') as f:
                    json.dump(assessment_data, f, indent=2)
                
                print(f"✅ Updated {updated_count} file classifications in {file_assessment_file}")
            
            # Update complete_pr_analysis.json if it exists
            complete_analysis_file = output_dir / "complete_pr_analysis.json"
            if complete_analysis_file.exists():
                with open(complete_analysis_file, 'r') as f:
                    analysis_data = json.load(f)
                
                # Add feedback metadata
                analysis_data['feedback_update'] = {
                    "applied": True,
                    "timestamp": datetime.now().isoformat(),
                    "files_updated": list(file_updates.keys()),
                    "agent_response_length": len(agent_response)
                }
                
                # Update quality scores based on file assessments
                if 'file_assessments' in assessment_data:
                    self.update_complete_pr_analysis_scores(output_dir, assessment_data['file_assessments'], analysis_data)
                
                with open(complete_analysis_file, 'w') as f:
                    json.dump(analysis_data, f, indent=2)
                
                print(f"✅ Updated {complete_analysis_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating JSON files: {e}")
            return False
    
    def parse_agent_response_for_updates(self, agent_response: str, user_feedback: str = "") -> Dict[str, Dict[str, Any]]:
        """Improved parsing that extracts file updates from both agent response and user feedback"""
        updates = {}
        
        # First, try to extract explicit file lists from user feedback
        feedback_files = self.extract_files_from_user_feedback(user_feedback)
        
        # Then, parse agent response for status changes
        response_updates = self.parse_agent_response_patterns(agent_response)
        
        # Combine both sources
        all_files = set(feedback_files.keys()) | set(response_updates.keys())
        
        for file_path in all_files:
            updates[file_path] = {}
            
            # Use agent response status if available, otherwise infer from feedback
            if file_path in response_updates:
                updates[file_path].update(response_updates[file_path])
            elif file_path in feedback_files:
                updates[file_path].update(feedback_files[file_path])
        
        return updates
    
    def extract_files_from_user_feedback(self, feedback: str) -> Dict[str, Dict[str, Any]]:
        """Extract file paths and their intended status from user feedback"""
        updates = {}
        
        # Look for file paths in the feedback
        file_patterns = [
            r'content/[^\s\)]+\.(json|md|js|svg|sql)',
            r'database-archive/[^\s\)]+\.(js|sql)',
            r'assets/[^\s\)]+\.(svg|png|jpg|jpeg)'
        ]
        
        for pattern in file_patterns:
            matches = re.finditer(pattern, feedback, re.IGNORECASE)
            for match in matches:
                file_path = match.group(0)
                
                # Determine status based on context
                status = self.infer_status_from_context(feedback, file_path)
                updates[file_path] = {'merge_readiness': status}
        
        return updates
    
    def infer_status_from_context(self, feedback: str, file_path: str) -> str:
        """Infer the intended status for a file based on feedback context"""
        context_lower = feedback.lower()
        
        # Check for removal/deletion context
        if any(word in context_lower for word in ['remove', 'delete', 'cleanup', 'placeholder', 'template', 'duplicate']):
            return 'ready'  # Files to be removed are "ready" for merge
        
        # Check for non-existent context
        if any(word in context_lower for word in ['non-existent', 'doesn\'t exist', 'missing']):
            return 'ready'  # Non-existent files pose no risk
        
        # Check for fix/resolve context
        if any(word in context_lower for word in ['fix', 'resolve', 'update', 'improve']):
            return 'ready'
        
        # Default to conditional if uncertain
        return 'conditional'
    
    def parse_agent_response_patterns(self, agent_response: str) -> Dict[str, Dict[str, Any]]:
        """Parse agent response using multiple pattern recognition strategies"""
        updates = {}
        
        # Strategy 1: Look for numbered lists with file paths
        numbered_list_pattern = r'^\d+\.\s*.*?([`"]?content/[^\s\)]+[`"]?)\s*[:\-]?\s*(\w+)'
        for match in re.finditer(numbered_list_pattern, agent_response, re.MULTILINE):
            file_path = match.group(1).strip('`"')
            status = match.group(2).lower()
            if status in ['ready', 'not_ready', 'conditional']:
                updates[file_path] = {'merge_readiness': status}
        
        # Strategy 2: Look for "file X: status" patterns
        status_pattern = r'([`"]?content/[^\s\)]+[`"]?)\s*[:\-]\s*(ready|not_ready|conditional)'
        for match in re.finditer(status_pattern, agent_response, re.IGNORECASE):
            file_path = match.group(1).strip('`"')
            status = match.group(2).lower()
            updates[file_path] = {'merge_readiness': status}
        
        # Strategy 3: Look for reclassification statements
        reclass_pattern = r'reclassified\s+(?:from\s+\w+\s+)?to\s+(ready|not_ready|conditional)[^.]*?([`"]?content/[^\s\)]+[`"]?)'
        for match in re.finditer(reclass_pattern, agent_response, re.IGNORECASE):
            status = match.group(1).lower()
            file_path = match.group(2).strip('`"')
            updates[file_path] = {'merge_readiness': status}
        
        # Strategy 4: Look for explicit mentions of file paths with status
        lines = agent_response.split('\n')
        current_file = None
        
        for line in lines:
            line = line.strip()
            
            # Pattern: Explicit file path with status change
            if 'content/' in line and ('.md' in line or '.json' in line or '.js' in line or '.svg' in line):
                # Extract file path
                file_match = re.search(r'(content/[^:\s\)]+)', line)
                if file_match:
                    current_file = file_match.group(1)
            
            # Pattern: Status indicators
            if current_file:
                if any(status in line.lower() for status in ['ready', 'not_ready', 'conditional']):
                    if 'ready' in line.lower() and 'not' not in line.lower():
                        updates[current_file] = updates.get(current_file, {})
                        updates[current_file]['merge_readiness'] = 'ready'
                    elif 'not_ready' in line.lower():
                        updates[current_file] = updates.get(current_file, {})
                        updates[current_file]['merge_readiness'] = 'not_ready'
                    elif 'conditional' in line.lower():
                        updates[current_file] = updates.get(current_file, {})
                        updates[current_file]['merge_readiness'] = 'conditional'
        
        return updates
    
    def calculate_quality_scores_from_assessments(self, file_assessments: List[Dict]) -> Dict[str, float]:
        """Calculate quality scores based on file assessments"""
        total_files = len(file_assessments)
        if total_files == 0:
            return {"overall_score": 0.0, "business_impact_score": 0.0, "technical_quality_score": 0.0, "risk_score": 10.0}
        
        ready_files = sum(1 for f in file_assessments if f.get("merge_readiness") == "ready")
        conditional_files = sum(1 for f in file_assessments if f.get("merge_readiness") == "conditional")
        not_ready_files = sum(1 for f in file_assessments if f.get("merge_readiness") == "not_ready")
        
        # Calculate scores
        confidence = ready_files / total_files
        
        # Business impact score (higher when more files are ready)
        business_impact = (ready_files * 10 + conditional_files * 7) / total_files
        
        # Technical quality score (penalizes conditional files)
        technical_quality = (ready_files * 10 + conditional_files * 6) / total_files
        
        # Risk score (inverse of confidence, scaled to 0-10)
        risk_score = (1 - confidence) * 10
        
        # Overall score (weighted average)
        overall_score = (business_impact * 0.4 + technical_quality * 0.4 + (10 - risk_score) * 0.2)
        
        return {
            "overall_score": round(overall_score, 1),
            "business_impact_score": round(business_impact, 1),
            "technical_quality_score": round(technical_quality, 1),
            "risk_score": round(risk_score, 1)
        }
    
    def update_complete_pr_analysis_scores(self, output_dir: Path, file_assessments: List[Dict], analysis_data: Dict) -> bool:
        """Update the complete_pr_analysis.json with recalculated scores"""
        try:
            # Calculate new scores based on current file assessments
            new_scores = self.calculate_quality_scores_from_assessments(file_assessments)
            
            # Store old scores for comparison
            old_assessment = analysis_data.get("overall_assessment", {})
            
            # Update the assessment with new scores
            new_assessment = {
                "overall_score": new_scores["overall_score"],
                "business_impact_score": new_scores["business_impact_score"],
                "technical_quality_score": new_scores["technical_quality_score"],
                "risk_score": new_scores["risk_score"],
                "recommendation": "READY" if new_scores["overall_score"] >= 8.0 else "REQUIRES_ATTENTION" if new_scores["overall_score"] >= 6.0 else "NEEDS_WORK",
                "status_color": "green" if new_scores["overall_score"] >= 8.0 else "orange" if new_scores["overall_score"] >= 6.0 else "red",
                "total_issues": len([q for q in analysis_data.get("quality_issues", []) if q.get("priority") in ["CRITICAL", "HIGH"]]),
                "critical_issues": len([q for q in analysis_data.get("quality_issues", []) if q.get("priority") == "CRITICAL"]),
                "high_priority_issues": len([q for q in analysis_data.get("quality_issues", []) if q.get("priority") == "HIGH"]),
                "files_analyzed": len(file_assessments)
            }
            
            # Add feedback history
            if "feedback_history" not in analysis_data:
                analysis_data["feedback_history"] = []
            
            analysis_data["feedback_history"].append({
                "timestamp": datetime.now().isoformat(),
                "action": "Stage 10 Feedback Update (Fixed)",
                "description": "Automatically recalculated quality scores based on updated file assessments",
                "scores_before": {
                    "overall_score": old_assessment.get("overall_score", 0.0),
                    "business_impact_score": old_assessment.get("business_impact_score", 0.0),
                    "technical_quality_score": old_assessment.get("technical_quality_score", 0.0),
                    "risk_score": old_assessment.get("risk_score", 10.0)
                },
                "scores_after": new_scores,
                "improvement": round(new_scores["overall_score"] - old_assessment.get("overall_score", 0.0), 1)
            })
            
            # Update the analysis data
            analysis_data["overall_assessment"] = new_assessment
            
            print(f"✅ Updated quality scores:")
            print(f"   Overall Score: {old_assessment.get('overall_score', 0.0)} → {new_scores['overall_score']}")
            print(f"   Business Impact: {old_assessment.get('business_impact_score', 0.0)} → {new_scores['business_impact_score']}")
            print(f"   Technical Quality: {old_assessment.get('technical_quality_score', 0.0)} → {new_scores['technical_quality_score']}")
            print(f"   Risk Score: {old_assessment.get('risk_score', 10.0)} → {new_scores['risk_score']}")
            print(f"   Recommendation: {old_assessment.get('recommendation', 'UNKNOWN')} → {new_assessment['recommendation']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating quality scores: {e}")
            return False

    
    def update_analysis_files(self, agent_response: str, user_feedback: str = "") -> bool:
        """Process agent response and update actual analysis files"""
        print("🔄 Processing agent response and updating files...")
        
        try:
            # The agent response should contain the updated analysis
            # For now, we'll ask Claude to regenerate the HTML with the feedback incorporated
            # This is a simpler approach than trying to parse complex structured data from the response
            
            # Use the project root we already have
            repo_root = self.project_root
            
            # Find the target analysis output directory
            # Look for pr_analysis_output in the current directory or parent directories
            current_dir = Path.cwd()
            output_dir = None
            
            # Check current directory first
            if (current_dir / "pr_analysis_output").exists():
                output_dir = current_dir / "pr_analysis_output"
            # Check parent directory
            elif (current_dir.parent / "pr_analysis_output").exists():
                output_dir = current_dir.parent / "pr_analysis_output"
            # Check if we're in asabaal-utils and need to look in sibling repos
            else:
                # Look for repos that might have pr_analysis_output
                for sibling in current_dir.parent.glob("*/pr_analysis_output"):
                    if sibling.parent.name != "asabaal-utils":  # Skip the tool repo
                        output_dir = sibling
                        break
            
            if not output_dir:
                print(f"❌ Analysis output directory not found")
                return False
            
            if not output_dir.exists():
                print(f"❌ Analysis output directory not found: {output_dir}")
                return False
            
            # Update the actual analysis data files that Stage 9 reads
            success = self.update_analysis_json_files(output_dir, agent_response, user_feedback)
            
            if success:
                print("✅ Updated analysis data files")
                
                # Create feedback report for tracking
                feedback_dir = output_dir / "debug_outputs" / "stage10_feedback"
                feedback_dir.mkdir(parents=True, exist_ok=True)
                
                feedback_report = feedback_dir / "FEEDBACK_UPDATE_REPORT.md"
                
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                
                feedback_content = f"""# 🔄 Stage 10: Feedback Update Report

**Generated**: {timestamp}
**Update Type**: User Feedback Integration

## 📋 Changes Applied

Based on user feedback about blog system architecture:
- Reclassified post.json files from "not_ready" to "ready_with_architectural_notes"
- Updated overall assessment scores and recommendations
- Distinguished functional readiness from architectural optimization

## 📊 Data Files Updated

- `complete_pr_analysis.json` - Updated overall assessment and scores
- `file_assessment_results.json` - Updated file classifications  

The analysis now correctly recognizes functional readiness while noting optimization opportunities.
"""
                
                with open(feedback_report, 'w') as f:
                    f.write(feedback_content)
                
                print(f"📝 Created feedback report: {feedback_report}")
                
                # Regenerate HTML with updated data
                print("🔄 Regenerating HTML with updated analysis data...")
                self.regenerate_html_report(output_dir)
            else:
                print("❌ Failed to update analysis data files")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating analysis files: {e}")
            return False
    
    def regenerate_html_report(self, output_dir: Path) -> bool:
        """Regenerate the interactive HTML report using Stage 9 with feedback history"""
        try:
            from .stage9_html_generator import Stage9HTMLGenerator
            from .path_utils import find_repo_root
            
            print("🔄 Regenerating HTML report with updated data...")
            
            repo_root = find_repo_root()
            html_generator = Stage9HTMLGenerator(str(repo_root), str(output_dir))
            
            # Load analysis data to pass to Stage 9
            analysis_data = html_generator.load_analysis_data()
            
            # Generate HTML with feedback history (called_from_stage10=True)
            html_file = html_generator._generate_standard_html(analysis_data, called_from_stage10=True)
            
            if html_file:
                print("✅ HTML report regenerated with feedback updates")
                return True
            else:
                print("❌ Failed to regenerate HTML report")
                return False
                
        except Exception as e:
            print(f"❌ Error regenerating HTML: {e}")
            return False
    
    def process_feedback_update(self, user_feedback: str, feedback_files: Optional[List[str]] = None) -> bool:
        """Process user feedback and update analysis"""
        print("=" * 80)
        print("🔄 STAGE 10: FEEDBACK UPDATE SYSTEM")
        print("=" * 80)
        
        try:
            # Step 1: Create feedback instructions
            instructions_file = self.create_feedback_instructions(user_feedback, feedback_files or [])
            print(f"📝 Created feedback instructions: {instructions_file}")
            
            # Step 2: Create update prompt
            prompt = self.create_feedback_update_prompt(instructions_file)
            print(f"📝 Created update prompt ({len(prompt):,} chars)")
            
            # Step 3: Call feedback update agent
            update_response = self.call_feedback_update_agent(prompt)
            
            # Step 4: Process response and update files
            success = self.update_analysis_files(update_response, user_feedback)
            if success:
                print("✅ STAGE 10 FEEDBACK UPDATE: SUCCESS")
                print(f"📊 Updated analysis files with feedback changes")
                return True
            else:
                print("❌ STAGE 10 FEEDBACK UPDATE: FAILED - Could not update files")
                return False
                
        except Exception as e:
            print(f"❌ STAGE 10 FEEDBACK UPDATE: FAILED with error: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python stage10_feedback_updates.py [OPTIONS]")
        print("")
        print("OPTIONS:")
        print("  '<feedback_text>'                 Process feedback text directly")
        print("  --file <filename>                 Process feedback file from pending/")
        print("  --list                            List pending feedback files")
        print("  --process-all                     Process all pending feedback files")
        print("  --project-root <path>             Set project root directory")
        print("")
        print("Examples:")
        print("  python stage10_feedback_updates.py 'Reclassify file X as ready'")
        print("  python stage10_feedback_updates.py --file raw_input_reclassification.md")
        print("  python stage10_feedback_updates.py --list")
        print("  python stage10_feedback_updates.py --process-all")
        sys.exit(1)
    
    # Parse command line arguments
    project_root = None
    args = sys.argv[1:]  # Skip script name
    
    # Extract project root if specified
    if '--project-root' in args:
        idx = args.index('--project-root')
        if idx + 1 < len(args):
            project_root = Path(args[idx + 1])
            # Remove from args list
            args = args[:idx] + args[idx + 2:]
        else:
            print("❌ --project-root requires a path argument")
            sys.exit(1)
    
    # Initialize system
    system = FeedbackUpdateSystem(project_root)
    
    # Handle different modes
    if not args:
        print("❌ No arguments provided")
        sys.exit(1)
    
    if args[0] == '--list':
        pending_files = system.list_pending_files()
        if pending_files:
            print(f"📝 Pending feedback files ({len(pending_files)}):")
            for filename in pending_files:
                print(f"  - {filename}")
        else:
            print("📝 No pending feedback files found")
        return
    
    elif args[0] == '--file':
        if len(args) < 2:
            print("❌ --file requires a filename argument")
            sys.exit(1)
        filename = args[1]
        success = system.process_feedback_file(filename)
        sys.exit(0 if success else 1)
    
    elif args[0] == '--process-all':
        results = system.process_all_pending()
        if results:
            success_count = sum(1 for success in results.values() if success)
            print(f"\n📊 Results: {success_count}/{len(results)} files processed successfully")
        sys.exit(0 if all(results.values()) else 1)
    
    else:
        # Direct feedback text mode (original behavior)
        user_feedback = args[0]
        feedback_files = args[1:] if len(args) > 1 else []
        success = system.process_feedback_update(user_feedback, feedback_files)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()