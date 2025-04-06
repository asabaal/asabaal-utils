"""DebugSessionManager for managing debug sessions.

This module provides the DebugSessionManager class, which is responsible for
creating, retrieving, and managing debug sessions.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from .session import DebugSession
from .storage import SessionStorage


class DebugSessionManager:
    """Manager for debug sessions.

    This class provides methods for creating, retrieving, and managing debug
    sessions. It is the main entry point for using the Debug Session Tracker.
    """

    _instance = None  # Singleton instance
    _sessions: Dict[str, DebugSession] = {}  # In-memory session cache
    _storage = None  # Storage backend

    def __new__(cls):
        """Create a new singleton instance of DebugSessionManager."""
        if cls._instance is None:
            cls._instance = super(DebugSessionManager, cls).__new__(cls)
            # Initialize the storage backend
            from .storage import SessionStorage
            cls._storage = SessionStorage()
        return cls._instance

    @classmethod
    def get_storage(cls):
        """Get the storage instance, creating it if necessary.
        
        Returns:
            The singleton DebugSessionManager instance
        """
        if cls._instance is None:
            return cls()
        return cls._instance

    @classmethod
    def create(cls, name: str, project: str, **kwargs) -> DebugSession:
        """Create a new debug session.

        Args:
            name: A user-friendly name for the session
            project: The name of the project/repository the session is for
            **kwargs: Additional session attributes

        Returns:
            A new DebugSession instance
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Generate a unique ID for the session
        session_id = str(uuid.uuid4())
        
        # Create session with current timestamp
        now = datetime.now()
        session = DebugSession(
            id=session_id,
            name=name,
            project=project,
            created_at=now,
            updated_at=now,
            status="active",
            diagnostics=[],
            fixes=[],
            **kwargs
        )
        
        # Store the session
        cls._sessions[session_id] = session
        manager._storage.save_session(session)
        
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[DebugSession]:
        """Get a debug session by ID.

        Args:
            session_id: The unique ID of the session to retrieve

        Returns:
            The DebugSession if found, otherwise None
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Check in-memory cache first
        if session_id in cls._sessions:
            return cls._sessions[session_id]
        
        # If not in cache, try to load from storage
        session = manager._storage.load_session(session_id)
        if session:
            cls._sessions[session_id] = session
        
        return session

    @classmethod
    def get_active_sessions(cls) -> List[DebugSession]:
        """Get all active debug sessions.

        Returns:
            A list of active DebugSession instances
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Load all sessions from storage
        sessions = manager._storage.list_sessions(status="active")
        
        # Update cache with loaded sessions
        for session in sessions:
            cls._sessions[session.id] = session
            
        return sessions

    @classmethod
    def get_all_sessions(cls) -> List[DebugSession]:
        """Get all debug sessions.

        Returns:
            A list of all DebugSession instances
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Load all sessions from storage
        sessions = manager._storage.list_sessions()
        
        # Update cache with loaded sessions
        for session in sessions:
            cls._sessions[session.id] = session
            
        return sessions

    @classmethod
    def update_session(cls, session: DebugSession) -> None:
        """Update a debug session.

        Args:
            session: The session to update
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Update the session timestamp
        session.updated_at = datetime.now()
        
        # Update the session in the cache and storage
        cls._sessions[session.id] = session
        manager._storage.save_session(session)

    @classmethod
    def delete_session(cls, session_id: str) -> bool:
        """Delete a debug session.

        Args:
            session_id: The unique ID of the session to delete

        Returns:
            True if the session was deleted, False otherwise
        """
        # Ensure the manager instance exists
        manager = cls.get_storage()
        
        # Remove from cache
        if session_id in cls._sessions:
            del cls._sessions[session_id]
        
        # Delete from storage
        return manager._storage.delete_session(session_id)

    @classmethod
    def complete_session(cls, session_id: str, summary: Optional[str] = None) -> Optional[DebugSession]:
        """Mark a debug session as completed.

        Args:
            session_id: The unique ID of the session to complete
            summary: Optional summary of the debugging session

        Returns:
            The updated DebugSession if found, otherwise None
        """
        session = cls.get_session(session_id)
        if not session:
            return None
            
        # Update session status and summary
        session.status = "completed"
        if summary:
            session.summary = summary
        session.updated_at = datetime.now()
        
        # Save the updated session
        cls.update_session(session)
        
        return session

    @classmethod
    def abandon_session(cls, session_id: str, reason: Optional[str] = None) -> Optional[DebugSession]:
        """Mark a debug session as abandoned.

        Args:
            session_id: The unique ID of the session to abandon
            reason: Optional reason for abandoning the session

        Returns:
            The updated DebugSession if found, otherwise None
        """
        session = cls.get_session(session_id)
        if not session:
            return None
            
        # Update session status and abandonment reason
        session.status = "abandoned"
        if reason:
            session.abandonment_reason = reason
        session.updated_at = datetime.now()
        
        # Save the updated session
        cls.update_session(session)
        
        return session
