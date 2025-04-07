"""File change tracking for Debug Session Tracker.

This module provides the FileChange class for tracking changes to files during
debugging sessions.
"""

import os
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class FileChange:
    """A change to a file during a debugging session.

    This class represents a change to a file, including the before and after
    states and a diff of the changes.

    Attributes:
        file_path: Path to the modified file
        before_state: Content or hash of the file before the change
        after_state: Content or hash of the file after the change
        diff: Text representation of the changes
    """

    file_path: str
    before_state: str
    after_state: str
    diff: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the file change to a dictionary.

        Returns:
            Dictionary representation of the file change
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileChange':
        """Create a file change from a dictionary.

        Args:
            data: Dictionary representation of a file change

        Returns:
            A new FileChange instance
        """
        return cls(**data)

    def get_before_hash(self) -> str:
        """Get a hash of the before state.

        Returns:
            SHA-256 hash of the before state
        """
        return hashlib.sha256(self.before_state.encode()).hexdigest()

    def get_after_hash(self) -> str:
        """Get a hash of the after state.

        Returns:
            SHA-256 hash of the after state
        """
        return hashlib.sha256(self.after_state.encode()).hexdigest()

    def save_states(self, directory: str) -> Dict[str, str]:
        """Save before and after states to files.

        This method saves the before and after states to files in the specified
        directory, using the file path and hashes to generate unique filenames.

        Args:
            directory: Directory where states will be saved

        Returns:
            Dictionary with paths to the saved files
        """
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate base filename from the file path
        base_name = os.path.basename(self.file_path)
        
        # Save before state
        before_hash = self.get_before_hash()
        before_path = os.path.join(directory, f"{base_name}.before.{before_hash[:8]}")
        with open(before_path, 'w') as f:
            f.write(self.before_state)
            
        # Save after state
        after_hash = self.get_after_hash()
        after_path = os.path.join(directory, f"{base_name}.after.{after_hash[:8]}")
        with open(after_path, 'w') as f:
            f.write(self.after_state)
            
        # Save diff
        diff_path = os.path.join(directory, f"{base_name}.diff.{before_hash[:8]}_{after_hash[:8]}")
        with open(diff_path, 'w') as f:
            f.write(self.diff)
            
        return {
            "before": before_path,
            "after": after_path,
            "diff": diff_path
        }

    def has_changes(self) -> bool:
        """Check if the file actually changed.

        Returns:
            True if the file changed, False otherwise
        """
        return self.before_state != self.after_state

    def summarize_changes(self) -> Dict[str, Any]:
        """Generate a summary of the changes.

        Returns:
            Dictionary with change summary
        """
        # Count lines added, removed, and modified
        added_lines = 0
        removed_lines = 0
        
        for line in self.diff.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines += 1
                
        # Calculate change percentage
        before_lines = len(self.before_state.splitlines())
        after_lines = len(self.after_state.splitlines())
        
        if before_lines > 0:
            change_percentage = abs(after_lines - before_lines) / before_lines * 100
        else:
            change_percentage = 100 if after_lines > 0 else 0
            
        return {
            "file_path": self.file_path,
            "lines_before": before_lines,
            "lines_after": after_lines,
            "lines_added": added_lines,
            "lines_removed": removed_lines,
            "lines_modified": min(added_lines, removed_lines),
            "change_percentage": round(change_percentage, 2)
        }

    def get_changed_functions(self) -> list:
        """Attempt to identify which functions were changed.

        This is a simple implementation that looks for function definitions
        in the diff. A more sophisticated implementation would use an AST parser.

        Returns:
            List of function names that were changed
        """
        changed_functions = []
        
        # Look for Python function definitions
        current_function = None
        in_function_def = False
        
        for line in self.diff.splitlines():
            # Only look at added or removed lines
            if not (line.startswith('+') or line.startswith('-')):
                continue
                
            # Remove the diff marker
            code_line = line[1:].strip()
            
            # Look for function definitions
            if code_line.startswith('def '):
                # Extract function name
                try:
                    func_name = code_line.split('def ')[1].split('(')[0].strip()
                    if func_name not in changed_functions:
                        changed_functions.append(func_name)
                except:
                    pass
                    
        return changed_functions

    def rollback(self) -> bool:
        """Attempt to rollback the change by restoring the before state.

        Returns:
            True if the rollback was successful, False otherwise
        """
        try:
            # Write the before state back to the file
            with open(self.file_path, 'w') as f:
                f.write(self.before_state)
                
            return True
        except Exception as e:
            print(f"Error rolling back change: {e}")
            return False
