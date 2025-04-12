"""
Project state management for the AI Agent Framework.

This module provides utilities for managing project state, including file tracking,
context management, and providing project-specific information to the agent.
"""

import os
import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


@dataclass
class FileState:
    """Tracks the state of an individual file in the project."""
    path: str
    content: str
    last_modified: float
    hash: str
    is_changed: bool = False
    
    @classmethod
    def from_file(cls, file_path: str) -> "FileState":
        """Create a FileState instance from a file on disk.
        
        Args:
            file_path: Path to the file
            
        Returns:
            A FileState object representing the current state of the file
        """
        path_obj = Path(file_path)
        content = path_obj.read_text(errors="replace")
        last_modified = path_obj.stat().st_mtime
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        return cls(
            path=file_path,
            content=content,
            last_modified=last_modified,
            hash=file_hash,
            is_changed=False
        )


class Project:
    """Manages the state and context for a project being worked on by an agent.
    
    This class is responsible for:
    1. Tracking project files and their changes
    2. Managing project metadata and configuration
    3. Building context for the agent based on relevant files
    4. Providing utilities for querying and updating project state
    """
    
    def __init__(
        self,
        path: str,
        ignore_patterns: Optional[List[str]] = None,
        max_file_size_kb: int = 1024,
        max_context_tokens: int = 150000,
    ):
        """Initialize a project from a directory.
        
        Args:
            path: Path to the project directory
            ignore_patterns: List of glob patterns to ignore (similar to .gitignore)
            max_file_size_kb: Maximum file size to include in context (KB)
            max_context_tokens: Maximum number of tokens to include in context
        """
        self.path = Path(path).absolute()
        self.ignore_patterns = ignore_patterns or [
            "**/.git/**", "**/node_modules/**", "**/__pycache__/**", "**/.venv/**",
            "**/*.pyc", "**/*.pyo", "**/*.pyd", "**/*.so", "**/*.dylib", "**/*.dll",
            "**/*.exe", "**/*.bin", "**/*.dat", "**/*.db", "**/*.sqlite", "**/*.log",
        ]
        self.max_file_size_kb = max_file_size_kb
        self.max_context_tokens = max_context_tokens
        
        # State tracking
        self.files: Dict[str, FileState] = {}
        self.changed_files: Set[str] = set()
        self.last_scan_time = 0.0
        
        # Ensure the project directory exists
        if not self.path.exists():
            raise ValueError(f"Project directory does not exist: {self.path}")
        
        # Initialize by scanning the project
        self.scan()
        
    def scan(self) -> Dict[str, FileState]:
        """Scan the project directory and update the file state.
        
        Returns:
            A dictionary of file paths to FileState objects
        """
        logging.info(f"Scanning project directory: {self.path}")
        
        # Track changed files
        self.changed_files.clear()
        new_files: Dict[str, FileState] = {}
        
        # Walk the directory and gather file info
        for root, dirs, files in os.walk(self.path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._is_ignored(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip ignored files
                if self._is_ignored(file_path):
                    continue
                
                # Skip files that are too large
                file_size_kb = os.path.getsize(file_path) / 1024
                if file_size_kb > self.max_file_size_kb:
                    logging.debug(f"Skipping large file: {file_path} ({file_size_kb:.2f} KB)")
                    continue
                
                # Get relative path for storing
                rel_path = os.path.relpath(file_path, self.path)
                
                try:
                    # Create new file state
                    new_state = FileState.from_file(file_path)
                    
                    # Check if file has changed
                    if rel_path in self.files:
                        old_hash = self.files[rel_path].hash
                        if new_state.hash != old_hash:
                            new_state.is_changed = True
                            self.changed_files.add(rel_path)
                    
                    new_files[rel_path] = new_state
                    
                except Exception as e:
                    logging.warning(f"Failed to process file {file_path}: {e}")
        
        # Update file state
        self.files = new_files
        self.last_scan_time = datetime.now().timestamp()
        
        logging.info(f"Project scan complete. Found {len(self.files)} files, {len(self.changed_files)} changed.")
        return self.files
    
    def get_changed_files(self) -> Dict[str, FileState]:
        """Get all changed files since the last scan.
        
        Returns:
            A dictionary of changed file paths to FileState objects
        """
        return {path: self.files[path] for path in self.changed_files}
    
    def get_file(self, path: str) -> Optional[FileState]:
        """Get the current state of a specific file.
        
        Args:
            path: Path to the file (relative to project directory)
            
        Returns:
            FileState if the file exists, None otherwise
        """
        if path in self.files:
            return self.files[path]
        return None
        
    def save_file(self, path: str, content: str) -> FileState:
        """Save content to a file in the project.
        
        Args:
            path: Path to the file (relative to project directory)
            content: Content to write to the file
            
        Returns:
            The updated FileState for the file
        """
        full_path = self.path / path
        
        # Ensure the directory exists
        os.makedirs(full_path.parent, exist_ok=True)
        
        # Write the content
        with open(full_path, "w") as f:
            f.write(content)
        
        # Update file state
        file_state = FileState.from_file(full_path)
        self.files[path] = file_state
        
        return file_state
    
    def build_context(
        self,
        focus_paths: Optional[List[str]] = None,
        include_all_changed: bool = True,
        max_files: int = 10
    ) -> str:
        """Build a context string for the agent based on project state.
        
        Args:
            focus_paths: Specific file paths to focus on
            include_all_changed: Whether to include all changed files
            max_files: Maximum number of files to include
            
        Returns:
            A context string containing relevant file contents and info
        """
        included_files = []
        
        # First, add focus paths if provided
        if focus_paths:
            for path in focus_paths:
                if path in self.files:
                    included_files.append(path)
        
        # Then add changed files if requested
        if include_all_changed:
            for path in self.changed_files:
                if path not in included_files:
                    included_files.append(path)
        
        # Finally, add important project files up to the max
        important_extensions = ['.py', '.js', '.ts', '.java', '.md', '.json', '.yaml', '.yml']
        important_files = [
            path for path in self.files
            if any(path.endswith(ext) for ext in important_extensions)
            and path not in included_files
        ]
        
        # Sort by importance (based on filename)
        important_files.sort(key=self._file_importance)
        
        # Add important files up to the max
        remaining_slots = max_files - len(included_files)
        if remaining_slots > 0:
            included_files.extend(important_files[:remaining_slots])
        
        # Build the context string
        context_parts = [
            f"Project: {self.path.name}",
            f"Files: {len(self.files)}",
            f"Changed files: {len(self.changed_files)}",
            "\nRelevant files:"
        ]
        
        for path in included_files:
            file_state = self.files[path]
            status = "CHANGED" if file_state.is_changed else "UNCHANGED"
            context_parts.append(f"\n--- {path} ({status}) ---\n{file_state.content}")
        
        return "\n".join(context_parts)
    
    def _is_ignored(self, path: str) -> bool:
        """Check if a path should be ignored based on ignore patterns.
        
        Args:
            path: The path to check
            
        Returns:
            True if the path should be ignored, False otherwise
        """
        from fnmatch import fnmatch
        
        rel_path = os.path.relpath(path, self.path)
        
        for pattern in self.ignore_patterns:
            if fnmatch(rel_path, pattern):
                return True
        
        return False
    
    @staticmethod
    def _file_importance(file_path: str) -> float:
        """Calculate a file's importance based on its path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            An importance score (higher is more important)
        """
        importance = 0.0
        
        # Common important files
        if file_path in ["README.md", "requirements.txt", "package.json", "setup.py", "pyproject.toml"]:
            importance += 10.0
            
        # Important file patterns
        if "main" in file_path:
            importance += 5.0
        if "config" in file_path:
            importance += 3.0
            
        # Extension-based importance
        ext = os.path.splitext(file_path)[1]
        if ext in [".py", ".js", ".ts", ".java"]:
            importance += 2.0
        elif ext in [".md", ".json", ".yaml", ".yml"]:
            importance += 1.0
            
        # Depth penalty (nested files are less important)
        depth = file_path.count(os.sep)
        importance -= depth * 0.5
        
        return importance
