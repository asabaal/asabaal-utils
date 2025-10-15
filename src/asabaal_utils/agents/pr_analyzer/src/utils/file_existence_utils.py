"""
File existence validation utilities for PR analysis.
Handles detection of deleted/moved files and provides graceful fallback mechanisms.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
import logging

logger = logging.getLogger(__name__)

class FileExistenceValidator:
    """Validates file existence and handles deleted file detection."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.deleted_files_cache: Set[str] = set()
        
    def validate_file_existence(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if a file exists and return status with reason.
        
        Args:
            file_path: Relative path from repo root
            
        Returns:
            Tuple of (exists, reason)
        """
        full_path = self.repo_root / file_path
        
        if full_path.exists():
            return True, "File exists"
        elif full_path.is_symlink():
            return False, "Broken symlink"
        else:
            return False, "File does not exist"
    
    def find_deleted_files(self, file_assessments: List[Dict]) -> List[Dict]:
        """
        Identify files that are marked as NOT_READY but don't exist.
        
        Args:
            file_assessments: List of file assessment dictionaries
            
        Returns:
            List of deleted file info dictionaries
        """
        deleted_files = []
        
        for assessment in file_assessments:
            file_path = assessment.get('file_path', '')
            
            # Skip if not marked as problematic
            if assessment.get('merge_readiness') not in ['not_ready', 'conditional']:
                continue
                
            exists, reason = self.validate_file_existence(file_path)
            
            if not exists:
                deleted_files.append({
                    'file_path': file_path,
                    'current_status': assessment.get('merge_readiness'),
                    'reason': reason,
                    'recommendations': assessment.get('recommendations', []),
                    'business_impact_score': assessment.get('business_impact_score', 0),
                    'technical_risk_score': assessment.get('technical_risk_score', 0)
                })
                
                # Cache for performance
                self.deleted_files_cache.add(file_path)
                
        logger.info(f"Found {len(deleted_files)} deleted files marked as problematic")
        return deleted_files
    
    def create_deleted_file_feedback(self, deleted_files: List[Dict]) -> Dict:
        """
        Create feedback data structure for deleted files.
        
        Args:
            deleted_files: List of deleted file info
            
        Returns:
            Feedback dictionary for agent processing
        """
        if not deleted_files:
            return {"type": "no_deleted_files", "files": []}
            
        feedback = {
            "type": "deleted_files_detected",
            "description": f"Found {len(deleted_files)} files that are marked as problematic but no longer exist",
            "files": [],
            "recommended_action": "reclassify_to_ready",
            "reason": "Files that don't exist cannot block PR merge"
        }
        
        for file_info in deleted_files:
            feedback["files"].append({
                "file_path": file_info['file_path'],
                "current_status": file_info['current_status'],
                "existence_status": file_info['reason'],
                "recommended_status": "ready",
                "recommended_recommendations": [
                    f"File does not exist ({file_info['reason']}) - no action needed"
                ],
                "impact_assessment": {
                    "business_impact": 0,  # No impact if file doesn't exist
                    "technical_risk": 0,   # No risk if file doesn't exist
                    "merge_blocker": False
                }
            })
            
        return feedback
    
    def auto_reclassify_deleted_files(self, file_assessments: List[Dict], 
                                    deleted_files: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Automatically reclassify deleted files to 'ready' status.
        
        Args:
            file_assessments: Original file assessments
            deleted_files: List of deleted file info
            
        Returns:
            Tuple of (updated_assessments, summary_changes)
        """
        updated_assessments = file_assessments.copy()
        deleted_paths = {f['file_path'] for f in deleted_files}
        
        changes = {
            "files_reclassified": [],
            "reason": "Auto-reclassified deleted files to 'ready' status",
            "impact_on_metrics": {
                "not_ready_before": 0,
                "not_ready_after": 0,
                "ready_before": 0,
                "ready_after": 0
            }
        }
        
        # Count before changes
        changes["impact_on_metrics"]["not_ready_before"] = sum(
            1 for f in updated_assessments if f.get('merge_readiness') == 'not_ready'
        )
        changes["impact_on_metrics"]["ready_before"] = sum(
            1 for f in updated_assessments if f.get('merge_readiness') == 'ready'
        )
        
        # Update deleted files
        for assessment in updated_assessments:
            file_path = assessment.get('file_path', '')
            
            if file_path in deleted_paths:
                old_status = assessment.get('merge_readiness', 'unknown')
                assessment['merge_readiness'] = 'ready'
                assessment['recommendations'] = [
                    f"File does not exist - no action needed"
                ]
                assessment['auto_reclassified'] = True
                assessment['reclassification_reason'] = 'File deleted during analysis'
                
                changes["files_reclassified"].append({
                    'file_path': file_path,
                    'old_status': old_status,
                    'new_status': 'ready'
                })
        
        # Count after changes
        changes["impact_on_metrics"]["not_ready_after"] = sum(
            1 for f in updated_assessments if f.get('merge_readiness') == 'not_ready'
        )
        changes["impact_on_metrics"]["ready_after"] = sum(
            1 for f in updated_assessments if f.get('merge_readiness') == 'ready'
        )
        
        logger.info(f"Auto-reclassified {len(changes['files_reclassified'])} deleted files")
        return updated_assessments, changes
    
    def generate_fallback_prompt_addition(self, deleted_files_feedback: Dict) -> str:
        """
        Generate additional prompt text for handling deleted files.
        
        Args:
            deleted_files_feedback: Feedback dictionary from create_deleted_file_feedback
            
        Returns:
            Prompt addition text
        """
        if deleted_files_feedback["type"] == "no_deleted_files":
            return ""
            
        prompt_addition = f"""

IMPORTANT: Deleted Files Detected
{deleted_files_feedback["description"]}

The following files are marked as problematic but no longer exist in the repository:
"""
        
        for file_info in deleted_files_feedback["files"]:
            prompt_addition += f"""
- {file_info['file_path']}
  * Current Status: {file_info['current_status']}
  * Existence: {file_info['existence_status']}
  * Recommended Action: Change to "{file_info['recommended_status']}"
  * Reason: {file_info['recommended_recommendations'][0]}
"""
        
        prompt_addition += """

INSTRUCTION: Automatically reclassify all deleted files to 'ready' status since:
1. Non-existent files cannot block a PR merge
2. No code changes are required for files that don't exist
3. This improves accuracy of merge readiness assessment

Please update these files in your response and ensure they are marked as 'ready'.
"""
        
        return prompt_addition


def validate_and_create_feedback(repo_root: str, file_assessments: List[Dict]) -> Tuple[Dict, str]:
    """
    Convenience function to validate files and create feedback in one call.
    
    Args:
        repo_root: Repository root path
        file_assessments: List of file assessment dictionaries
        
    Returns:
        Tuple of (feedback_dict, prompt_addition)
    """
    validator = FileExistenceValidator(repo_root)
    deleted_files = validator.find_deleted_files(file_assessments)
    feedback = validator.create_deleted_file_feedback(deleted_files)
    prompt_addition = validator.generate_fallback_prompt_addition(feedback)
    
    return feedback, prompt_addition