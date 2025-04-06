"""Debug Session Tracker for asabaal_utils.

This module provides tools for tracking, visualizing, and reporting on debug sessions.
"""

__version__ = "0.1.0"

# Import key classes for easier access
from .session.session import DebugSession
from .session.manager import DebugSessionManager
from .tracking.diagnostics import DiagnosticRun, Issue, PythonLintDiagnostic
from .tracking.fixes import AppliedFix
from .tracking.changes import FileChange
from .visualization.timeline import Timeline
from .reporting.markdown import MarkdownReport
from .reporting.html import HTMLReport

# Export classes
__all__ = [
    'DebugSession',
    'DebugSessionManager',
    'DiagnosticRun',
    'Issue',
    'PythonLintDiagnostic',
    'AppliedFix',
    'FileChange',
    'Timeline',
    'MarkdownReport',
    'HTMLReport',
]
