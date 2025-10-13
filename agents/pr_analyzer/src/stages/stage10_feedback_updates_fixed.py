#!/usr/bin/env python3

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import score calculation utilities
try:
    from asabaal_utils.pr_analyzer.score_utils import recalculate_assessment_summary
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False
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
        
        # Calculate quality scores
        business_impact = (ready_count * 10 + conditional_count * 7) / total_count if total_count > 0 else 0.0
        technical_quality = (ready_count * 10 + conditional_count * 6) / total_count if total_count > 0 else 0.0
        risk_score = (1 - confidence_score) * 10
        overall_score = (business_impact * 0.4 + technical_quality * 0.4 + (10 - risk_score) * 0.2)
        
        summary = assessment_data.get('assessment_summary', {})
        summary.update({
            'total_files': total_count,
            'ready_files': ready_count,
            'conditional_files': conditional_count,
            'not_ready_files': not_ready_count,
            'overall_confidence': confidence_score,
            'overall_quality_score': round(overall_score, 1),
            'business_impact_score': round(business_impact, 1),
            'technical_quality_score': round(technical_quality, 1),
            'risk_score': round(risk_score, 1),
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


class FixedFeedbackUpdateSystem:
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
                    provider = backend_cfg.get('provider', 'openrouter')
                    model = backend_cfg.get('model', 'anthropic/claude-3.5-sonnet')
                    
                    if provider == 'ollama':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OLLAMA,
                            model=model,
                            base_url=backend_cfg.get('base_url', 'http://localhost:11434'),
                            timeout=backend_cfg.get('timeout', 300)
                        )
                    elif provider == 'openrouter':
                        backend_config = BackendConfig(
                            backend_type=BackendType.OPENROUTER,
                            model=model,
                            api_key=backend_cfg.get('api_key')
                        )
                    elif provider == 'claude':
                        backend_config = BackendConfig(
                            backend_type=BackendType.CLAUDE,
                            model=model,
                            api_key=backend_cfg.get('api_key')
                        )
                
                self.backend_manager = BackendManager(backend_config)
                
                if self.backend_manager.is_available():
                    print(f"🔧 Backend manager initialized for feedback updates")
                    print(f"   Using {self.backend_manager.config.backend_type.value} backend with model {self.backend_manager.config.model}")
                else:
                    print("⚠️  Backend manager initialization failed")
                    self.backend_manager = None
                    
            except Exception as e:
                print(f"⚠️  Backend manager initialization failed: {e}")
                self.backend_manager = None

    def parse_agent_response_for_updates_improved(self, agent_response: str, user_feedback: str) -> Dict[str, Dict[str, Any]]:
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
    
    def extract_files_from_user_feedback(self, user_feedback: str) -> Dict[str, Dict[str, Any]]:
        """Extract file paths and their intended status from user feedback"""
        updates = {}
        
        # Look for file paths in the feedback
        file_patterns = [
            r'content/[^\s\)]+\.(json|md|js|svg|sql)',
            r'database-archive/[^\s\)]+\.(js|sql)',
            r'assets/[^\s\)]+\.(svg|png|jpg|jpeg)'
        ]
        
        for pattern in file_patterns:
            matches = re.finditer(pattern, user_feedback, re.IGNORECASE)
            for match in matches:
                file_path = match.group(0)
                
                # Determine status based on context
                status = self.infer_status_from_context(user_feedback, file_path)
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
    
    def update_complete_pr_analysis_scores(self, output_dir: Path, file_assessments: List[Dict]) -> bool:
        """Update the complete_pr_analysis.json with recalculated scores"""
        try:
            complete_analysis_file = output_dir / "complete_pr_analysis.json"
            
            if not complete_analysis_file.exists():
                print("⚠️  complete_pr_analysis.json not found")
                return False
            
            with open(complete_analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
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
            
            # Write back to file
            with open(complete_analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            print(f"✅ Updated quality scores in complete_pr_analysis.json")
            print(f"   Overall Score: {old_assessment.get('overall_score', 0.0)} → {new_scores['overall_score']}")
            print(f"   Business Impact: {old_assessment.get('business_impact_score', 0.0)} → {new_scores['business_impact_score']}")
            print(f"   Technical Quality: {old_assessment.get('technical_quality_score', 0.0)} → {new_scores['technical_quality_score']}")
            print(f"   Risk Score: {old_assessment.get('risk_score', 10.0)} → {new_scores['risk_score']}")
            print(f"   Recommendation: {old_assessment.get('recommendation', 'UNKNOWN')} → {new_assessment['recommendation']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating complete_pr_analysis.json: {e}")
            return False
    
    def update_analysis_json_files_fixed(self, output_dir: Path, agent_response: str, user_feedback: str) -> bool:
        """Fixed version that properly updates all analysis files"""
        try:
            # Parse both agent response and user feedback for file updates
            file_updates = self.parse_agent_response_for_updates_improved(agent_response, user_feedback)
            
            if not file_updates:
                print("⚠️  No file updates found")
                return False
            
            print(f"📝 Found {len(file_updates)} file updates to apply")
            
            # Update file_assessment_results.json
            file_assessment_file = output_dir / "file_assessment_results.json"
            updated_assessments = []
            
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
                            
                            # Apply the updates
                            if 'merge_readiness' in update_data:
                                old_status = file_assessment.get('merge_readiness')
                                new_status = update_data['merge_readiness']
                                file_assessment['merge_readiness'] = new_status
                                print(f"🔄 {file_path}: {old_status} → {new_status}")
                            
                            if 'detailed_feedback' in update_data:
                                file_assessment['detailed_feedback'] = update_data['detailed_feedback']
                            
                            if 'recommendations' in update_data:
                                file_assessment['recommendations'] = update_data['recommendations']
                            
                            updated_count += 1
                        
                        updated_assessments.append(file_assessment)
                
                # Recalculate summary statistics
                if 'assessment_summary' in assessment_data:
                    print("🔄 Recalculating assessment summary...")
                    updated_summary = recalculate_assessment_summary(assessment_data)
                    assessment_data['assessment_summary'] = updated_summary
                    
                    # Log the updated metrics
                    summary = updated_summary
                    print(f"📊 Updated summary:")
                    print(f"   Ready files: {summary.get('ready_files', 0)}")
                    print(f"   Conditional files: {summary.get('conditional_files', 0)}")
                    print(f"   Not ready files: {summary.get('not_ready_files', 0)}")
                    print(f"   Total files: {summary.get('total_files', 0)}")
                    print(f"   Overall confidence: {summary.get('overall_confidence', 0):.2%}")
                    if 'overall_quality_score' in summary:
                        print(f"   Overall quality score: {summary['overall_quality_score']}")
                
                with open(file_assessment_file, 'w') as f:
                    json.dump(assessment_data, f, indent=2)
                
                print(f"✅ Updated {updated_count} file classifications in {file_assessment_file}")
            
            # Update complete_pr_analysis.json with new scores
            self.update_complete_pr_analysis_scores(output_dir, updated_assessments)
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating JSON files: {e}")
            return False


# Test the fixed system
if __name__ == "__main__":
    # Example usage
    system = FixedFeedbackUpdateSystem(Path("/home/asabaal/repos/multisensory-experience-website"))
    
    # Test with our feedback
    user_feedback = """
    The 29 files marked as NOT_READY fall into several categories:
    1. Duplicate Template Files (23 files) in content/content/blog/published/ - these should be removed
    2. Empty template file content/raw-input/.md - should be deleted
    3. Non-existent database files - database-archive/supabase-keys.prod.js and database-archive/supabase-setup.sql
    4. Placeholder asset assets/images/icons/cosmic_nebula.svg
    5. Invalid blog post path
    """
    
    agent_response = """
    1. Updated File Classifications:
       - The 23 duplicate blog post JSON files in `content/content/blog/published/` have been reclassified from "NOT_READY" to "READY"
       - The file `content/raw-input/.md` has been reclassified from "NOT_READY" to "READY"
       - The file `assets/images/icons/cosmic_nebula.svg` has been reclassified from "NOT_READY" to "READY"
    """
    
    updates = system.parse_agent_response_for_updates_improved(agent_response, user_feedback)
    print(f"Parsed {len(updates)} file updates")
    for file_path, update in updates.items():
        print(f"  {file_path}: {update}")