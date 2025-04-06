"""Storage mechanism for debug sessions.

This module provides the SessionStorage class, which is responsible for
saving and loading debug sessions from disk.
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .session import DebugSession


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that converts datetime objects to ISO format strings."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class SessionStorage:
    """Storage backend for debug sessions.

    This class handles the persistence of debug sessions to disk and provides
    methods for loading, saving, and listing sessions.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize the session storage.

        Args:
            storage_dir: Directory where sessions will be stored
        """
        # Determine the storage directory
        if storage_dir is None:
            # Default to user's home directory + .asabaal/debug_sessions
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".asabaal", "debug_sessions")
            
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        self.storage_dir = storage_dir

    def _get_session_path(self, session_id: str) -> str:
        """Get the file path for a session.

        Args:
            session_id: The unique ID of the session

        Returns:
            The file path where the session is stored
        """
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def save_session(self, session: DebugSession) -> bool:
        """Save a session to disk.

        Args:
            session: The session to save

        Returns:
            True if the session was saved successfully, False otherwise
        """
        try:
            # Convert the session to a dictionary
            session_dict = session.to_dict()
            
            # Write the session to disk as JSON using the custom encoder
            session_path = self._get_session_path(session.id)
            with open(session_path, 'w') as f:
                json.dump(session_dict, f, indent=2, cls=DateTimeEncoder)
                
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[DebugSession]:
        """Load a session from disk.

        Args:
            session_id: The unique ID of the session to load

        Returns:
            The loaded DebugSession if found, otherwise None
        """
        session_path = self._get_session_path(session_id)
        
        try:
            # Check if the session file exists
            if not os.path.exists(session_path):
                return None
                
            # Read the session from disk
            with open(session_path, 'r') as f:
                session_dict = json.load(f)
                
            # Convert the dictionary back to a DebugSession
            return DebugSession.from_dict(session_dict)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from disk.

        Args:
            session_id: The unique ID of the session to delete

        Returns:
            True if the session was deleted successfully, False otherwise
        """
        session_path = self._get_session_path(session_id)
        
        try:
            # Check if the session file exists
            if not os.path.exists(session_path):
                return False
                
            # Delete the session file
            os.remove(session_path)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def list_sessions(self, status: Optional[str] = None) -> List[DebugSession]:
        """List all sessions or sessions with a specific status.

        Args:
            status: Optional filter for session status

        Returns:
            A list of DebugSession instances
        """
        sessions = []
        
        try:
            # Get all session files
            session_pattern = os.path.join(self.storage_dir, "*.json")
            session_files = glob.glob(session_pattern)
            
            # Load each session
            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_dict = json.load(f)
                        
                    # Filter by status if provided
                    if status is not None and session_dict.get('status') != status:
                        continue
                        
                    # Convert the dictionary back to a DebugSession
                    session = DebugSession.from_dict(session_dict)
                    sessions.append(session)
                except Exception as e:
                    print(f"Error loading session from {session_file}: {e}")
        except Exception as e:
            print(f"Error listing sessions: {e}")
            
        return sessions

    def backup_sessions(self, backup_dir: str) -> bool:
        """Backup all sessions to a backup directory.

        Args:
            backup_dir: Directory where sessions will be backed up

        Returns:
            True if the backup was successful, False otherwise
        """
        try:
            # Create the backup directory if it doesn't exist
            os.makedirs(backup_dir, exist_ok=True)
            
            # Get all session files
            session_pattern = os.path.join(self.storage_dir, "*.json")
            session_files = glob.glob(session_pattern)
            
            # Copy each session file to the backup directory
            import shutil
            for session_file in session_files:
                filename = os.path.basename(session_file)
                backup_path = os.path.join(backup_dir, filename)
                shutil.copy2(session_file, backup_path)
                
            return True
        except Exception as e:
            print(f"Error backing up sessions: {e}")
            return False

    def import_sessions(self, import_dir: str) -> int:
        """Import sessions from a directory.

        Args:
            import_dir: Directory containing sessions to import

        Returns:
            Number of sessions imported
        """
        imported_count = 0
        
        try:
            # Get all session files in the import directory
            session_pattern = os.path.join(import_dir, "*.json")
            session_files = glob.glob(session_pattern)
            
            # Import each session file
            for session_file in session_files:
                try:
                    # Read the session file
                    with open(session_file, 'r') as f:
                        session_dict = json.load(f)
                        
                    # Convert the dictionary to a DebugSession
                    session = DebugSession.from_dict(session_dict)
                    
                    # Save the session to our storage
                    if self.save_session(session):
                        imported_count += 1
                except Exception as e:
                    print(f"Error importing session from {session_file}: {e}")
        except Exception as e:
            print(f"Error importing sessions: {e}")
            
        return imported_count

    def clear_sessions(self, status: Optional[str] = None) -> int:
        """Clear all sessions or sessions with a specific status.

        Args:
            status: Optional filter for session status

        Returns:
            Number of sessions cleared
        """
        cleared_count = 0
        
        try:
            # Get sessions to clear
            sessions = self.list_sessions(status)
            
            # Delete each session
            for session in sessions:
                if self.delete_session(session.id):
                    cleared_count += 1
        except Exception as e:
            print(f"Error clearing sessions: {e}")
            
        return cleared_count
