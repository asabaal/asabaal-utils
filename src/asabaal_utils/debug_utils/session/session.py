"""DebugSession class definition.

This module provides the DebugSession class, which represents a debugging session.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict


@dataclass
class DebugSession:
    """A debugging session.

    This class represents a debugging session, which tracks diagnostics, fixes,
    and other debugging-related information.

    Attributes:
        id: Unique session identifier
        name: User-friendly session name
        project: Associated project/repository
        created_at: Session start time
        updated_at: Last activity time
        status: Current session status (active, completed, abandoned)
        diagnostics: List of diagnostic runs
        fixes: List of applied fixes
    """

    id: str
    name: str
    project: str
    created_at: datetime
    updated_at: datetime
    status: str
    diagnostics: List = field(default_factory=list)
    fixes: List = field(default_factory=list)
    summary: Optional[str] = None
    abandonment_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary.

        Returns:
            Dictionary representation of the session
        """
        # Use dataclasses.asdict for the conversion
        session_dict = asdict(self)
        
        return session_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebugSession':
        """Create a session from a dictionary.

        Args:
            data: Dictionary representation of a session

        Returns:
            A new DebugSession instance
        """
        # Create a copy of the data so we can modify it
        data_copy = data.copy()
        
        # Convert ISO format strings back to datetime objects
        if isinstance(data_copy.get('created_at'), str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        if isinstance(data_copy.get('updated_at'), str):
            data_copy['updated_at'] = datetime.fromisoformat(data_copy['updated_at'])
            
        # Extract diagnostics and fixes before creating the session
        diagnostics_data = data_copy.pop('diagnostics', [])
        fixes_data = data_copy.pop('fixes', [])
        
        # Create the session without diagnostics and fixes
        session = cls(**data_copy, diagnostics=[], fixes=[])
        
        # Add diagnostics
        if diagnostics_data:
            from ..tracking.diagnostics import DiagnosticRun
            for diag_data in diagnostics_data:
                session.diagnostics.append(DiagnosticRun.from_dict(diag_data))
        
        # Add fixes
        if fixes_data:
            from ..tracking.fixes import AppliedFix
            for fix_data in fixes_data:
                session.fixes.append(AppliedFix.from_dict(fix_data))
        
        return session

    def add_diagnostic(self, diagnostic):
        """Add a diagnostic run to the session.

        Args:
            diagnostic: A DiagnosticRun instance
        """
        self.diagnostics.append(diagnostic)
        self.updated_at = datetime.now()

    def add_fix(self, fix):
        """Add an applied fix to the session.

        Args:
            fix: An AppliedFix instance
        """
        self.fixes.append(fix)
        self.updated_at = datetime.now()

    def run_diagnostic(self, tool: str, target: str, parameters: Optional[Dict[str, Any]] = None):
        """Run a diagnostic and track it in the session.

        This method will be expanded once the DiagnosticRun class is implemented.

        Args:
            tool: Diagnostic tool to run
            target: File/module to diagnose
            parameters: Tool-specific parameters

        Returns:
            A DiagnosticRun instance
        """
        # This will be implemented once the DiagnosticRun class exists
        from ..tracking.diagnostics import DiagnosticRun
        
        diagnostic = DiagnosticRun(
            id=f"diag_{len(self.diagnostics) + 1}",
            session_id=self.id,
            tool=tool,
            target=target,
            start_time=datetime.now(),
            end_time=None,  # Will be set when the diagnostic completes
            parameters=parameters or {},
            results={},
            issues_found=[]
        )
        
        # Placeholder for actual diagnostic execution
        # This would typically call the appropriate diagnostic tool
        
        # For demonstration purposes, we'll just update the end_time
        diagnostic.end_time = datetime.now()
        
        # Add the diagnostic to this session
        self.add_diagnostic(diagnostic)
        
        return diagnostic

    def apply_fix(self, script: str, target: str, parameters: Optional[Dict[str, Any]] = None):
        """Apply a fix and track it in the session.

        This method will be expanded once the AppliedFix class is implemented.

        Args:
            script: Fix script to run
            target: File/module to fix
            parameters: Fix-specific parameters

        Returns:
            An AppliedFix instance
        """
        # This will be implemented once the AppliedFix class exists
        from ..tracking.fixes import AppliedFix
        
        fix = AppliedFix(
            id=f"fix_{len(self.fixes) + 1}",
            session_id=self.id,
            script=script,
            target=target,
            timestamp=datetime.now(),
            parameters=parameters or {},
            changes=[],
            resolved_issues=[],
            successful=False  # Will be updated when fix is evaluated
        )
        
        # Placeholder for actual fix application
        # This would typically call the appropriate fix script
        
        # For demonstration purposes, we'll just mark it as successful
        fix.successful = True
        
        # Add the fix to this session
        self.add_fix(fix)
        
        return fix

    def generate_timeline(self):
        """Generate a timeline visualization of the debugging process.

        This method will be expanded once the visualization module is implemented.

        Returns:
            A timeline visualization object
        """
        # This will be implemented once the Timeline class exists
        from ..visualization.timeline import Timeline
        
        timeline = Timeline(self)
        
        return timeline

    def generate_report(self, format: str = "markdown"):
        """Generate a report of the debugging session.

        This method will be expanded once the reporting module is implemented.

        Args:
            format: Report format (markdown, html)

        Returns:
            A string containing the report
        """
        # This will be implemented once the reporting classes exist
        if format.lower() == "markdown":
            from ..reporting.markdown import MarkdownReport
            report = MarkdownReport(self)
        else:
            from ..reporting.html import HTMLReport
            report = HTMLReport(self)
            
        return report.generate()
