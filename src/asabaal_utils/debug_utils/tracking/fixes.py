"""Fix tracking for Debug Session Tracker.

This module provides classes for tracking applied fixes and file changes during
debugging sessions.
"""

import os
import hashlib
import difflib
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

from .changes import FileChange


@dataclass
class AppliedFix:
    """A fix applied during a debugging session.

    This class represents a fix that was applied to address one or more issues
    found during diagnostics.

    Attributes:
        id: Unique fix identifier
        session_id: The ID of the session this fix belongs to
        script: Fix script/command used
        target: File/module fixed
        timestamp: Time when the fix was applied
        parameters: Fix-specific parameters
        changes: List of file changes made by the fix
        resolved_issues: List of issue IDs resolved by the fix
        successful: Whether the fix was successful
    """

    id: str
    session_id: str
    script: str
    target: str
    timestamp: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)
    changes: List[FileChange] = field(default_factory=list)
    resolved_issues: List[str] = field(default_factory=list)
    successful: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the fix to a dictionary.

        Returns:
            Dictionary representation of the fix
        """
        fix_dict = asdict(self)
        
        # Convert datetime objects to ISO format strings
        fix_dict['timestamp'] = self.timestamp.isoformat()
        
        return fix_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppliedFix':
        """Create a fix from a dictionary.

        Args:
            data: Dictionary representation of a fix

        Returns:
            A new AppliedFix instance
        """
        # Convert ISO format strings back to datetime objects
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
        # Convert changes dictionaries to FileChange objects
        if 'changes' in data and isinstance(data['changes'], list):
            changes = []
            for change_data in data['changes']:
                changes.append(FileChange.from_dict(change_data))
            data['changes'] = changes
            
        return cls(**data)

    def mark_resolved(self, issue_id: str) -> None:
        """Mark an issue as resolved by this fix.

        Args:
            issue_id: The ID of the issue that was resolved
        """
        if issue_id not in self.resolved_issues:
            self.resolved_issues.append(issue_id)

    def add_change(self, change: FileChange) -> None:
        """Add a file change to the fix.

        Args:
            change: The file change to add
        """
        self.changes.append(change)

    def create_change(self, file_path: str, before_state: Optional[str] = None, after_state: Optional[str] = None) -> FileChange:
        """Create a new file change and add it to the fix.

        Args:
            file_path: Path to the modified file
            before_state: Content of the file before the change
            after_state: Content of the file after the change

        Returns:
            The created FileChange
        """
        # If states not provided, try to read from file
        if before_state is None or after_state is None:
            try:
                # Read the current state if after_state not provided
                if after_state is None and os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        after_state = f.read()
                        
                # We can't determine before_state if not provided
                # This would typically come from version control or a backup
                if before_state is None:
                    before_state = ""
            except Exception as e:
                print(f"Error reading file states: {e}")
        
        # Create the change
        change = FileChange(
            file_path=file_path,
            before_state=before_state or "",
            after_state=after_state or "",
            diff=self._generate_diff(before_state or "", after_state or "")
        )
        
        # Add the change to this fix
        self.add_change(change)
        
        return change

    def _generate_diff(self, before_state: str, after_state: str) -> str:
        """Generate a text diff between two states.

        Args:
            before_state: Content before the change
            after_state: Content after the change

        Returns:
            Text representation of the diff
        """
        # Generate a unified diff
        diff = difflib.unified_diff(
            before_state.splitlines(keepends=True),
            after_state.splitlines(keepends=True),
            fromfile="before",
            tofile="after"
        )
        
        return "".join(diff)

    def run_script(self, script_path: Optional[str] = None, capture_changes: bool = True) -> bool:
        """Run a fix script.

        This method executes a script to apply a fix and optionally captures
        file changes.

        Args:
            script_path: Path to the script to run (defaults to self.script)
            capture_changes: Whether to capture file changes

        Returns:
            True if the script was successful, False otherwise
        """
        script_to_run = script_path or self.script
        
        # If capture_changes is True, we need to snapshot the target file before running
        before_state = None
        if capture_changes and os.path.exists(self.target) and os.path.isfile(self.target):
            try:
                with open(self.target, 'r') as f:
                    before_state = f.read()
            except Exception as e:
                print(f"Error capturing before state: {e}")
        
        try:
            # Run the script
            result = subprocess.run(
                [script_to_run, self.target],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Store script results in metadata
            self.metadata["script_output"] = {
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Update success status
            self.successful = result.returncode == 0
            
            # If capture_changes is True and we have a before state, capture the after state
            if capture_changes and before_state is not None and os.path.exists(self.target):
                try:
                    with open(self.target, 'r') as f:
                        after_state = f.read()
                    
                    # Only create a change if the file actually changed
                    if before_state != after_state:
                        self.create_change(self.target, before_state, after_state)
                except Exception as e:
                    print(f"Error capturing after state: {e}")
            
            return self.successful
            
        except Exception as e:
            # Store error information
            self.metadata["script_error"] = str(e)
            self.successful = False
            return False
