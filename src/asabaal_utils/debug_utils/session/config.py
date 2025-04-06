"""Configuration for debug sessions.

This module provides the SessionConfig class for managing debug session configuration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SessionConfig:
    """Configuration for debug sessions.

    This class handles configuration settings for debug sessions, including
    storage location, default parameters, and user preferences.

    Attributes:
        config_file: Path to the configuration file
        config: Dictionary of configuration settings
    """

    DEFAULT_CONFIG = {
        "storage_dir": None,  # Will default to ~/.asabaal/debug_sessions
        "backup_dir": None,   # Will default to ~/.asabaal/debug_backups
        "max_sessions": 100,  # Maximum number of sessions to keep
        "auto_backup": True,  # Whether to automatically backup sessions
        "backup_frequency": 10,  # Backup every 10 saves
        "default_report_format": "markdown",  # Default report format
        "colors": {
            "critical": "#ff0000",
            "high": "#ff6600",
            "medium": "#ffcc00",
            "low": "#00cc00"
        }
    }

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the session configuration.

        Args:
            config_file: Path to the configuration file
        """
        # Determine the configuration file path
        if config_file is None:
            # Default to user's home directory + .asabaal/config
            home_dir = os.path.expanduser("~")
            config_dir = os.path.join(home_dir, ".asabaal")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "debug_config.json")
            
        self.config_file = config_file
        
        # Initialize with default config
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if it exists
        self.load()

    def load(self) -> bool:
        """Load configuration from file.

        Returns:
            True if the configuration was loaded successfully, False otherwise
        """
        try:
            # Check if the configuration file exists
            if not os.path.exists(self.config_file):
                return False
                
            # Read the configuration from file
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                
            # Update the configuration with loaded values
            self.config.update(loaded_config)
            
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def save(self) -> bool:
        """Save configuration to file.

        Returns:
            True if the configuration was saved successfully, False otherwise
        """
        try:
            # Write the configuration to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            The configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

    def get_storage_dir(self) -> str:
        """Get the storage directory for debug sessions.

        Returns:
            Path to the storage directory
        """
        storage_dir = self.get("storage_dir")
        
        if storage_dir is None:
            # Default to user's home directory + .asabaal/debug_sessions
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".asabaal", "debug_sessions")
            
        # Create the directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        return storage_dir

    def get_backup_dir(self) -> str:
        """Get the backup directory for debug sessions.

        Returns:
            Path to the backup directory
        """
        backup_dir = self.get("backup_dir")
        
        if backup_dir is None:
            # Default to user's home directory + .asabaal/debug_backups
            home_dir = os.path.expanduser("~")
            backup_dir = os.path.join(home_dir, ".asabaal", "debug_backups")
            
        # Create the directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        return backup_dir

    def get_color(self, severity: str) -> str:
        """Get the color for a severity level.

        Args:
            severity: Severity level (critical, high, medium, low)

        Returns:
            Color for the severity level
        """
        colors = self.get("colors", {})
        return colors.get(severity.lower(), "#000000")

    def should_backup(self, save_count: int) -> bool:
        """Check if a backup should be performed.

        Args:
            save_count: Number of saves performed

        Returns:
            True if a backup should be performed, False otherwise
        """
        auto_backup = self.get("auto_backup", True)
        if not auto_backup:
            return False
            
        backup_frequency = self.get("backup_frequency", 10)
        return save_count % backup_frequency == 0

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
