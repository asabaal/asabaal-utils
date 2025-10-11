"""
Git Analysis Module

Handles all Git operations including repository access, diff parsing,
and change extraction for PR analysis using subprocess calls.
"""

import os
import subprocess
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileChange:
    """Represents a single file change in a PR."""
    file_path: str
    change_type: str  # 'A' (added), 'M' (modified), 'D' (deleted), 'R' (renamed)
    lines_added: int
    lines_removed: int
    old_file_path: Optional[str] = None  # For renamed files
    diff_content: Optional[str] = None
    

@dataclass
class PRAnalysis:
    """Container for complete PR analysis data."""
    from_branch: str
    to_branch: str
    total_files_changed: int
    total_lines_added: int
    total_lines_removed: int
    file_changes: List[FileChange]
    commit_messages: List[str]
    # Separate stats excluding PR analysis files
    total_files_changed_excluding_analysis: int = 0
    total_lines_added_excluding_analysis: int = 0
    total_lines_removed_excluding_analysis: int = 0
    file_changes_excluding_analysis: Optional[List[FileChange]] = None
    

class GitAnalyzer:
    """Analyzes Git repositories and extracts PR change information."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize Git analyzer with repository path."""
        self.repo_path = Path(repo_path).resolve()
        
        # Define patterns for PR analysis files to exclude from recommendations
        self.pr_analysis_patterns = [
            'pr_analysis_output/',
            'pr_analysis.html',
            'pr_analysis_interactive.html',
            'pr_analysis_report.txt',
            'pr_analysis_report.md',
            'complete_pr_analysis.json',
            'prototypes/',
            'prototype/'
        ]
        
        # Verify this is a git repository
        if not (self.repo_path / '.git').exists():
            raise ValueError(f"Not a valid Git repository: {self.repo_path}")
    
    def _get_pr_comparison_range(self, from_branch: str, to_branch: str) -> str:
        """
        Get the correct git comparison range for PR analysis.
        
        For PR analysis, we want to see what changes from_branch introduces
        compared to to_branch (i.e., what's in the PR).
        
        Args:
            from_branch: The feature branch (what we're analyzing)
            to_branch: The target branch (usually main/master)
            
        Returns:
            Git comparison range string in the format "to_branch..from_branch"
        """
        return f"{to_branch}..{from_branch}"
    
    def _run_git_command(self, args: List[str]) -> str:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {' '.join(args)}\nError: {e.stderr}")
    
    def _is_pr_analysis_file(self, file_path: str) -> bool:
        """Check if a file is part of PR analysis output and should be excluded from recommendations."""
        normalized_path = str(Path(file_path)).replace('\\', '/')
        
        # Check against PR analysis patterns
        for pattern in self.pr_analysis_patterns:
            if pattern.endswith('/'):
                # Directory pattern - check if file is under this directory
                if normalized_path.startswith(pattern) or f"/{pattern}" in f"/{normalized_path}":
                    return True
            else:
                # File pattern - check if file matches exactly or is at any path level
                if pattern in normalized_path or normalized_path.endswith(pattern):
                    return True
        
        return False
    
    def analyze_pr(self, from_branch: str, to_branch: str, 
                   include_diffs: bool = True) -> PRAnalysis:
        """
        Analyze changes between two branches/commits.
        
        Args:
            from_branch: Source branch/commit (e.g., 'main', 'HEAD~1')
            to_branch: Target branch/commit (e.g., 'feature-branch', 'HEAD')
            include_diffs: Whether to include full diff content
            
        Returns:
            PRAnalysis object with complete change information
        """
        try:
            # Get file changes using git diff
            file_changes = self._get_file_changes(from_branch, to_branch, include_diffs)
            
            # Calculate totals for all files
            total_lines_added = sum(fc.lines_added for fc in file_changes)
            total_lines_removed = sum(fc.lines_removed for fc in file_changes)
            
            # Separate non-PR-analysis files for recommendations
            file_changes_excluding_analysis = [
                fc for fc in file_changes 
                if not self._is_pr_analysis_file(fc.file_path)
            ]
            
            # Calculate totals excluding PR analysis files
            total_lines_added_excluding = sum(fc.lines_added for fc in file_changes_excluding_analysis)
            total_lines_removed_excluding = sum(fc.lines_removed for fc in file_changes_excluding_analysis)
            
            # Get commit messages
            commit_messages = self._get_commit_messages(from_branch, to_branch)
            
            return PRAnalysis(
                from_branch=from_branch,
                to_branch=to_branch,
                total_files_changed=len(file_changes),
                total_lines_added=total_lines_added,
                total_lines_removed=total_lines_removed,
                file_changes=file_changes,
                commit_messages=commit_messages,
                total_files_changed_excluding_analysis=len(file_changes_excluding_analysis),
                total_lines_added_excluding_analysis=total_lines_added_excluding,
                total_lines_removed_excluding_analysis=total_lines_removed_excluding,
                file_changes_excluding_analysis=file_changes_excluding_analysis
            )
            
        except Exception as e:
            raise RuntimeError(f"Error analyzing PR: {e}")
    
    def _get_file_changes(self, from_branch: str, to_branch: str, 
                         include_diffs: bool) -> List[FileChange]:
        """Get all file changes between two branches."""
        file_changes = []
        
        # Get file status changes - show what from_branch adds compared to to_branch
        # This shows the changes being brought by from_branch (what's in the PR)
        comparison_range = self._get_pr_comparison_range(from_branch, to_branch)
        status_output = self._run_git_command([
            'diff', '--name-status', comparison_range
        ])
        
        # Get line count changes - show what from_branch adds compared to to_branch
        numstat_output = self._run_git_command([
            'diff', '--numstat', comparison_range
        ])
        
        # Parse status changes
        status_lines = [line.strip() for line in status_output.split('\n') if line.strip()]
        numstat_lines = [line.strip() for line in numstat_output.split('\n') if line.strip()]
        
        # Create a mapping of files to line changes
        line_changes = {}
        for line in numstat_lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                added = parts[0] if parts[0] != '-' else '0'
                removed = parts[1] if parts[1] != '-' else '0'
                file_path = parts[2]
                try:
                    line_changes[file_path] = (int(added), int(removed))
                except ValueError:
                    line_changes[file_path] = (0, 0)  # Binary files
        
        # Process status changes
        for line in status_lines:
            if not line:
                continue
                
            parts = line.split('\t')
            status = parts[0]
            
            if status.startswith('R'):  # Renamed file
                # Format: R100\toldfile\tnewfile
                if len(parts) >= 3:
                    old_file = parts[1]
                    new_file = parts[2]
                    lines_added, lines_removed = line_changes.get(new_file, (0, 0))
                    
                    file_changes.append(FileChange(
                        file_path=new_file,
                        change_type='R',
                        lines_added=lines_added,
                        lines_removed=lines_removed,
                        old_file_path=old_file,
                        diff_content=self._get_diff_content(from_branch, to_branch, new_file, include_diffs)
                    ))
            else:
                # Format: A/M/D\tfilename
                if len(parts) >= 2:
                    change_type = status[0]  # First character (A, M, D)
                    file_path = parts[1]
                    lines_added, lines_removed = line_changes.get(file_path, (0, 0))
                    
                    file_changes.append(FileChange(
                        file_path=file_path,
                        change_type=change_type,
                        lines_added=lines_added,
                        lines_removed=lines_removed,
                        diff_content=self._get_diff_content(from_branch, to_branch, file_path, include_diffs)
                    ))
        
        return file_changes
    
    def _get_diff_content(self, from_branch: str, to_branch: str, 
                         file_path: str, include_diffs: bool) -> Optional[str]:
        """Get diff content for a specific file if requested."""
        if not include_diffs:
            return None
        
        try:
            comparison_range = self._get_pr_comparison_range(from_branch, to_branch)
            diff_output = self._run_git_command([
                'diff', comparison_range, '--', file_path
            ])
            return diff_output if diff_output.strip() else None
        except Exception:
            return "[Error retrieving diff content]"
    
    def _get_commit_messages(self, from_branch: str, to_branch: str) -> List[str]:
        """Get commit messages between two branches."""
        try:
            comparison_range = self._get_pr_comparison_range(from_branch, to_branch)
            log_output = self._run_git_command([
                'log', '--pretty=format:%s', comparison_range
            ])
            messages = [line.strip() for line in log_output.split('\n') if line.strip()]
            return messages
        except Exception:
            return []
    
    def get_file_content(self, file_path: str, branch: str) -> Optional[str]:
        """Get content of a specific file at a specific branch/commit."""
        try:
            content = self._run_git_command(['show', f"{branch}:{file_path}"])
            return content
        except Exception:
            return None
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get general repository information."""
        try:
            info = {}
            
            # Current branch
            try:
                current_branch = self._run_git_command(['branch', '--show-current']).strip()
                info['current_branch'] = current_branch
            except:
                info['current_branch'] = 'unknown'
            
            # Origin URL
            try:
                origin_url = self._run_git_command(['remote', 'get-url', 'origin']).strip()
                info['origin_url'] = origin_url
            except:
                info['origin_url'] = None
            
            # Total commits
            try:
                commit_count = self._run_git_command(['rev-list', '--count', 'HEAD']).strip()
                info['total_commits'] = int(commit_count)
            except:
                info['total_commits'] = 0
            
            # Branches
            try:
                branches_output = self._run_git_command(['branch', '--format=%(refname:short)'])
                branches = [b.strip() for b in branches_output.split('\n') if b.strip()]
                info['branches'] = branches
            except:
                info['branches'] = []
            
            # Is dirty (has uncommitted changes)
            try:
                status_output = self._run_git_command(['status', '--porcelain'])
                info['is_dirty'] = bool(status_output.strip())
            except:
                info['is_dirty'] = False
            
            info['repo_path'] = str(self.repo_path)
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def validate_branches(self, from_branch: str, to_branch: str) -> bool:
        """Validate that both branches exist in the repository."""
        try:
            # Try to resolve both branches
            self._run_git_command(['rev-parse', '--verify', from_branch])
            self._run_git_command(['rev-parse', '--verify', to_branch])
            return True
        except Exception:
            return False