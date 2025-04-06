"""Unit tests for the Debug Session Tracker.

This module tests the core functionality of the Debug Session Tracker.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.asabaal_utils.debug_utils import (
    DebugSession,
    DebugSessionManager,
    DiagnosticRun,
    Issue,
    AppliedFix,
    FileChange
)


class TestDebugSessionTracker(unittest.TestCase):
    """Test case for the Debug Session Tracker."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for session storage
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize the DebugSessionManager with the temporary directory
        DebugSessionManager._storage = None  # Reset the singleton
        self.session_manager = DebugSessionManager()
        self.session_manager._storage.storage_dir = self.temp_dir

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary files
        for filename in os.listdir(self.temp_dir):
            os.unlink(os.path.join(self.temp_dir, filename))
        os.rmdir(self.temp_dir)

    def test_create_session(self):
        """Test creating a debug session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Check if the session was created correctly
        self.assertEqual(session.name, "Test Session")
        self.assertEqual(session.project, "test_project")
        self.assertEqual(session.status, "active")
        self.assertIsNotNone(session.id)
        self.assertIsInstance(session.created_at, datetime)
        self.assertIsInstance(session.updated_at, datetime)
        self.assertEqual(len(session.diagnostics), 0)
        self.assertEqual(len(session.fixes), 0)

    def test_get_session(self):
        """Test retrieving a debug session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Retrieve the session
        retrieved_session = DebugSessionManager.get_session(session.id)
        
        # Check if the retrieved session matches the original
        self.assertEqual(retrieved_session.id, session.id)
        self.assertEqual(retrieved_session.name, session.name)
        self.assertEqual(retrieved_session.project, session.project)

    def test_add_diagnostic(self):
        """Test adding a diagnostic to a session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Create a diagnostic
        diagnostic = DiagnosticRun(
            id="test_diagnostic",
            session_id=session.id,
            tool="test_tool",
            target="test_target",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1)
        )
        
        # Add the diagnostic to the session
        session.add_diagnostic(diagnostic)
        
        # Save the session
        DebugSessionManager.update_session(session)
        
        # Retrieve the session
        retrieved_session = DebugSessionManager.get_session(session.id)
        
        # Check if the diagnostic was added correctly
        self.assertEqual(len(retrieved_session.diagnostics), 1)
        self.assertEqual(retrieved_session.diagnostics[0].id, diagnostic.id)
        self.assertEqual(retrieved_session.diagnostics[0].tool, diagnostic.tool)
        self.assertEqual(retrieved_session.diagnostics[0].target, diagnostic.target)

    def test_add_issue(self):
        """Test adding an issue to a diagnostic."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Create a diagnostic
        diagnostic = DiagnosticRun(
            id="test_diagnostic",
            session_id=session.id,
            tool="test_tool",
            target="test_target",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1)
        )
        
        # Create an issue
        issue = Issue(
            id="test_issue",
            type="test_type",
            severity="high",
            location="test_location",
            description="Test issue description"
        )
        
        # Add the issue to the diagnostic
        diagnostic.add_issue(issue)
        
        # Add the diagnostic to the session
        session.add_diagnostic(diagnostic)
        
        # Check if the issue was added correctly
        self.assertEqual(len(diagnostic.issues_found), 1)
        self.assertEqual(diagnostic.issues_found[0].id, issue.id)
        self.assertEqual(diagnostic.issues_found[0].type, issue.type)
        self.assertEqual(diagnostic.issues_found[0].severity, issue.severity)
        self.assertEqual(diagnostic.issues_found[0].location, issue.location)
        self.assertEqual(diagnostic.issues_found[0].description, issue.description)

    def test_add_fix(self):
        """Test adding a fix to a session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Create a fix
        fix = AppliedFix(
            id="test_fix",
            session_id=session.id,
            script="test_script",
            target="test_target",
            timestamp=datetime.now(),
            successful=True
        )
        
        # Add the fix to the session
        session.add_fix(fix)
        
        # Save the session
        DebugSessionManager.update_session(session)
        
        # Retrieve the session
        retrieved_session = DebugSessionManager.get_session(session.id)
        
        # Check if the fix was added correctly
        self.assertEqual(len(retrieved_session.fixes), 1)
        self.assertEqual(retrieved_session.fixes[0].id, fix.id)
        self.assertEqual(retrieved_session.fixes[0].script, fix.script)
        self.assertEqual(retrieved_session.fixes[0].target, fix.target)
        self.assertEqual(retrieved_session.fixes[0].successful, fix.successful)

    def test_mark_issue_fixed(self):
        """Test marking an issue as fixed."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Create a diagnostic
        diagnostic = DiagnosticRun(
            id="test_diagnostic",
            session_id=session.id,
            tool="test_tool",
            target="test_target",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(seconds=1)
        )
        
        # Create an issue
        issue = Issue(
            id="test_issue",
            type="test_type",
            severity="high",
            location="test_location",
            description="Test issue description"
        )
        
        # Add the issue to the diagnostic
        diagnostic.add_issue(issue)
        
        # Add the diagnostic to the session
        session.add_diagnostic(diagnostic)
        
        # Create a fix
        fix = AppliedFix(
            id="test_fix",
            session_id=session.id,
            script="test_script",
            target="test_target",
            timestamp=datetime.now(),
            successful=True
        )
        
        # Add the fix to the session
        session.add_fix(fix)
        
        # Mark the issue as fixed
        issue.mark_fixed(fix.id)
        fix.mark_resolved(issue.id)
        
        # Check if the issue was marked as fixed correctly
        self.assertEqual(issue.fixed_by, fix.id)
        self.assertTrue(issue.is_fixed())
        self.assertIn(issue.id, fix.resolved_issues)

    def test_complete_session(self):
        """Test completing a debug session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Complete the session
        DebugSessionManager.complete_session(session.id, "Test summary")
        
        # Retrieve the session
        retrieved_session = DebugSessionManager.get_session(session.id)
        
        # Check if the session was completed correctly
        self.assertEqual(retrieved_session.status, "completed")
        self.assertEqual(retrieved_session.summary, "Test summary")

    def test_abandon_session(self):
        """Test abandoning a debug session."""
        # Create a session
        session = DebugSessionManager.create(
            name="Test Session",
            project="test_project"
        )
        
        # Abandon the session
        DebugSessionManager.abandon_session(session.id, "Test reason")
        
        # Retrieve the session
        retrieved_session = DebugSessionManager.get_session(session.id)
        
        # Check if the session was abandoned correctly
        self.assertEqual(retrieved_session.status, "abandoned")
        self.assertEqual(retrieved_session.abandonment_reason, "Test reason")


if __name__ == '__main__':
    unittest.main()
