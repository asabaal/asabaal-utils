"""Diagnostic tracking for Debug Session Tracker.

This module provides classes for tracking diagnostic runs and issues found during
debugging sessions.
"""

import uuid
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Issue:
    """An issue found during a diagnostic run.

    This class represents an issue found during a diagnostic run, such as an error,
    warning, or other problem that needs to be fixed.

    Attributes:
        id: Unique issue identifier
        type: Issue category/type
        severity: Issue severity (critical, high, medium, low)
        location: File/line number where the issue is located
        description: Description of the issue
        fixed_by: Reference to the fix that resolved this issue
    """

    id: str
    type: str
    severity: str
    location: str
    description: str
    fixed_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary.

        Returns:
            Dictionary representation of the issue
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create an issue from a dictionary.

        Args:
            data: Dictionary representation of an issue

        Returns:
            A new Issue instance
        """
        return cls(**data)

    def is_fixed(self) -> bool:
        """Check if the issue is fixed.

        Returns:
            True if the issue is fixed, False otherwise
        """
        return self.fixed_by is not None

    def mark_fixed(self, fix_id: str) -> None:
        """Mark the issue as fixed.

        Args:
            fix_id: The ID of the fix that resolved this issue
        """
        self.fixed_by = fix_id


@dataclass
class DiagnosticRun:
    """A diagnostic run in a debugging session.

    This class represents a single diagnostic run, which checks for issues
    in a target file or module.

    Attributes:
        id: Unique diagnostic run identifier
        session_id: The ID of the session this diagnostic belongs to
        tool: Diagnostic tool used
        target: File/module diagnosed
        start_time: Time when the diagnostic started
        end_time: Time when the diagnostic completed
        parameters: Tool-specific parameters
        results: Structured diagnostic results
        issues_found: List of issues found during the diagnostic
    """

    id: str
    session_id: str
    tool: str
    target: str
    start_time: datetime
    end_time: Optional[datetime] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    issues_found: List[Issue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the diagnostic run to a dictionary.

        Returns:
            Dictionary representation of the diagnostic run
        """
        diagnostic_dict = asdict(self)
        
        # Convert datetime objects to ISO format strings
        if self.start_time:
            diagnostic_dict['start_time'] = self.start_time.isoformat()
        if self.end_time:
            diagnostic_dict['end_time'] = self.end_time.isoformat()
            
        return diagnostic_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiagnosticRun':
        """Create a diagnostic run from a dictionary.

        Args:
            data: Dictionary representation of a diagnostic run

        Returns:
            A new DiagnosticRun instance
        """
        # Convert ISO format strings back to datetime objects
        if 'start_time' in data and isinstance(data['start_time'], str):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data and isinstance(data['end_time'], str):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
            
        # Convert issues_found dictionaries to Issue objects
        if 'issues_found' in data and isinstance(data['issues_found'], list):
            issues = []
            for issue_data in data['issues_found']:
                issues.append(Issue.from_dict(issue_data))
            data['issues_found'] = issues
            
        return cls(**data)

    def add_issue(self, issue: Issue) -> None:
        """Add an issue to the diagnostic run.

        Args:
            issue: The issue to add
        """
        self.issues_found.append(issue)

    def create_issue(self, type: str, severity: str, location: str, description: str, **kwargs) -> Issue:
        """Create a new issue and add it to the diagnostic run.

        Args:
            type: Issue category/type
            severity: Issue severity (critical, high, medium, low)
            location: File/line number where the issue is located
            description: Description of the issue
            **kwargs: Additional issue attributes

        Returns:
            The created Issue
        """
        issue = Issue(
            id=f"issue_{len(self.issues_found) + 1}_{self.id}",
            type=type,
            severity=severity,
            location=location,
            description=description,
            **kwargs
        )
        self.add_issue(issue)
        return issue

    def get_issue_by_id(self, issue_id: str) -> Optional[Issue]:
        """Get an issue by ID.

        Args:
            issue_id: The ID of the issue to retrieve

        Returns:
            The Issue if found, otherwise None
        """
        for issue in self.issues_found:
            if issue.id == issue_id:
                return issue
        return None

    def count_issues_by_severity(self) -> Dict[str, int]:
        """Count issues by severity.

        Returns:
            Dictionary mapping severity levels to issue counts
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for issue in self.issues_found:
            if issue.severity.lower() in counts:
                counts[issue.severity.lower()] += 1
                
        return counts

    def duration(self) -> Optional[float]:
        """Calculate the duration of the diagnostic run in seconds.

        Returns:
            Duration in seconds, or None if the run hasn't completed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def complete(self) -> None:
        """Mark the diagnostic run as complete."""
        if not self.end_time:
            self.end_time = datetime.now()

    def run_command(self, command: List[str]) -> None:
        """Run a command as part of the diagnostic.

        This method executes a command and stores the results.

        Args:
            command: Command to run as a list of strings
        """
        self.start_time = datetime.now()
        
        try:
            # Run the command and capture output
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Store command results
            self.results = {
                "command": " ".join(command),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            # Parse issues from the output (implementation depends on the tool)
            self._parse_issues_from_output(result.stdout, result.stderr)
            
        except Exception as e:
            # Store error information
            self.results = {
                "command": " ".join(command),
                "error": str(e),
                "success": False
            }
            
        finally:
            # Mark the diagnostic as complete
            self.complete()

    def _parse_issues_from_output(self, stdout: str, stderr: str) -> None:
        """Parse issues from command output.

        This method is a placeholder that should be overridden by subclasses
        that know how to parse output from specific diagnostic tools.

        Args:
            stdout: Standard output from the command
            stderr: Standard error from the command
        """
        # This is a placeholder implementation that creates an issue for each line
        # of stderr if there is any non-empty output
        if stderr and stderr.strip():
            for i, line in enumerate(stderr.strip().split("\n")):
                if line.strip():
                    self.create_issue(
                        type="error",
                        severity="high",
                        location=f"{self.target}",
                        description=line.strip()
                    )


class PythonLintDiagnostic(DiagnosticRun):
    """A diagnostic run using a Python linter.

    This class specializes DiagnosticRun for Python linting tools like pylint,
    flake8, etc.
    """

    def __init__(self, session_id: str, target: str, tool: str = "pylint", **kwargs):
        """Initialize a Python lint diagnostic.

        Args:
            session_id: The ID of the session this diagnostic belongs to
            target: File/module to diagnose
            tool: Linting tool to use (pylint, flake8, etc.)
            **kwargs: Additional diagnostic attributes
        """
        super().__init__(
            id=f"lint_{str(uuid.uuid4())[:8]}",
            session_id=session_id,
            tool=tool,
            target=target,
            start_time=datetime.now(),
            **kwargs
        )

    def run(self) -> None:
        """Run the linting diagnostic."""
        command = [self.tool, self.target]
        self.run_command(command)

    def _parse_issues_from_output(self, stdout: str, stderr: str) -> None:
        """Parse issues from linter output.

        This method parses output from Python linting tools like pylint and flake8.

        Args:
            stdout: Standard output from the linter
            stderr: Standard error from the linter
        """
        # Combine stdout and stderr since some linters use stdout for warnings
        output = "\n".join([stdout, stderr]).strip()
        
        if not output:
            return
            
        # Parse based on the tool
        if self.tool == "pylint":
            self._parse_pylint_output(output)
        elif self.tool == "flake8":
            self._parse_flake8_output(output)
        else:
            # Default parsing for unknown tools
            super()._parse_issues_from_output(stdout, stderr)

    def _parse_pylint_output(self, output: str) -> None:
        """Parse output from pylint.

        Args:
            output: Output from pylint
        """
        for line in output.split("\n"):
            if not line.strip() or "Your code has been rated at" in line:
                continue
                
            try:
                # Pylint format: path:line:column: message-id: message
                parts = line.split(":", 4)
                if len(parts) >= 5:
                    file_path = parts[0]
                    line_num = parts[1]
                    col_num = parts[2]
                    msg_id_severity = parts[3].strip()
                    message = parts[4].strip()
                    
                    # Determine severity based on message ID
                    severity = "medium"  # Default severity
                    if msg_id_severity.startswith("E") or msg_id_severity.startswith("F"):
                        severity = "high"
                    elif msg_id_severity.startswith("W"):
                        severity = "medium"
                    elif msg_id_severity.startswith("C"):
                        severity = "low"
                    
                    self.create_issue(
                        type="pylint",
                        severity=severity,
                        location=f"{file_path}:{line_num}:{col_num}",
                        description=message,
                        metadata={"message_id": msg_id_severity}
                    )
            except Exception as e:
                # If we can't parse the line, create a generic issue
                self.create_issue(
                    type="pylint",
                    severity="medium",
                    location=self.target,
                    description=line.strip()
                )

    def _parse_flake8_output(self, output: str) -> None:
        """Parse output from flake8.

        Args:
            output: Output from flake8
        """
        for line in output.split("\n"):
            if not line.strip():
                continue
                
            try:
                # Flake8 format: path:line:column: code message
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = parts[1]
                    col_num = parts[2]
                    code_message = parts[3].strip()
                    
                    # Extract code and message
                    code_parts = code_message.split(" ", 1)
                    code = code_parts[0]
                    message = code_parts[1] if len(code_parts) > 1 else code_message
                    
                    # Determine severity based on code
                    severity = "medium"  # Default severity
                    if code.startswith("F"):
                        severity = "high"  # Fatal errors
                    elif code.startswith("E"):
                        severity = "medium"  # Errors
                    elif code.startswith("W"):
                        severity = "low"  # Warnings
                    
                    self.create_issue(
                        type="flake8",
                        severity=severity,
                        location=f"{file_path}:{line_num}:{col_num}",
                        description=message,
                        metadata={"code": code}
                    )
            except Exception as e:
                # If we can't parse the line, create a generic issue
                self.create_issue(
                    type="flake8",
                    severity="medium",
                    location=self.target,
                    description=line.strip()
                )
