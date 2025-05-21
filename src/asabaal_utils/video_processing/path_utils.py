"""
Path utilities for video processing.

This module provides utilities for handling path conversions between different
operating systems, particularly for WSL and Windows interoperability.
"""

import os
import sys
import re
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def is_windows_path(path):
    """Check if a path is a Windows-style path."""
    if not path:
        return False
    
    # Check for drive letter pattern (C:\ or C:/)
    return bool(re.match(r'^[a-zA-Z]:[/\\]', path))

def convert_windows_path(win_path, wsl_path_prefix=None):
    """
    Convert Windows path to Linux path or vice versa based on the environment.
    
    Args:
        win_path: The Windows-style path to convert
        wsl_path_prefix: WSL path prefix for Windows drives (e.g., '/mnt')
                         If None, will try to detect from environment
    
    Returns:
        The converted path or the original path if no conversion is needed
    """
    if not win_path:
        return None
    
    # If not a Windows path, return as is
    if not is_windows_path(win_path):
        return win_path
    
    # Determine wsl_path_prefix if not provided
    if wsl_path_prefix is None:
        # Check if we're running in WSL
        if os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
            # Try to determine WSL mount point
            try:
                findmnt_output = subprocess.check_output(['findmnt', '-t', 'drvfs', '-n', '-o', 'TARGET']).decode('utf-8').strip()
                if findmnt_output:
                    # Use the first drvfs mount point (typically /mnt)
                    wsl_path_prefix = findmnt_output.split('\n')[0]
                else:
                    # Default to /mnt if not found
                    wsl_path_prefix = '/mnt'
            except (subprocess.SubprocessError, FileNotFoundError):
                # Default to /mnt if findmnt fails
                wsl_path_prefix = '/mnt'
        else:
            # Not in WSL, likely on Windows or native Linux
            # For Windows, keep the path as is
            return win_path.replace('\\', '/')
    
    # Extract drive letter and rest of path
    drive_letter = win_path[0].lower()
    
    # Handle different slash types
    if '/' in win_path:
        # Format with forward slashes
        path_part = win_path[2:] if win_path[2] == '/' else win_path[3:]
        return f"{wsl_path_prefix}/{drive_letter}/{path_part}".replace('\\', '/')
    else:
        # Format with backslashes
        path_part = win_path[2:] if win_path[2] == '\\' else win_path[3:]
        return f"{wsl_path_prefix}/{drive_letter}/{path_part}".replace('\\', '/')

def convert_path_to_current_os(path, wsl_path_prefix=None):
    """
    Convert a path to be compatible with the current OS.
    
    This function handles paths from different operating systems:
    - WSL -> Windows
    - Windows -> WSL (when running in WSL)
    - Keeps path unchanged if already compatible
    
    Args:
        path: The path to convert
        wsl_path_prefix: WSL path prefix for Windows drives (e.g., '/mnt')
    
    Returns:
        The converted path
    """
    if not path:
        return None
    
    # Running in WSL
    if sys.platform.startswith('linux') and os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
        if is_windows_path(path):
            # Convert Windows path to WSL path
            return convert_windows_path(path, wsl_path_prefix)
        else:
            # Already a WSL path
            return path
    
    # Running on Windows
    elif sys.platform.startswith('win'):
        if is_windows_path(path):
            # Already a Windows path
            return path.replace('\\', '/')
        elif path.startswith('/mnt/') or (wsl_path_prefix and path.startswith(f"{wsl_path_prefix}/")):
            # Convert WSL path to Windows path
            prefix = wsl_path_prefix if wsl_path_prefix else '/mnt'
            # Extract drive letter and path
            parts = path.split('/')
            if len(parts) >= 3:
                drive_letter = parts[2].upper()
                path_part = '/'.join(parts[3:])
                return f"{drive_letter}:/{path_part}"
            else:
                logger.warning(f"Invalid WSL path format: {path}")
                return path
        else:
            # Not a recognized format
            return path
    
    # Running on other systems
    else:
        if is_windows_path(path):
            # Try to convert Windows path to Unix-like format
            return path.replace('\\', '/')
        else:
            # Keep as is
            return path

def resolve_media_path(path, possible_mount_points=None, wsl_path_prefix=None):
    """
    Attempt to resolve a media path by trying different mount points and path formats.
    
    Args:
        path: The original path to resolve
        possible_mount_points: List of additional mount points to try
        wsl_path_prefix: WSL path prefix for Windows drives
    
    Returns:
        A tuple of (resolved_path, success) where success is True if the path exists
    """
    if not path:
        return None, False
    
    # Get all possible mount points to try
    all_mount_points = []
    if wsl_path_prefix:
        all_mount_points.append(wsl_path_prefix)
    
    # Auto-detect mount points if running in WSL
    if os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
        # Add detected mounts
        detected_mounts = get_available_wsl_mounts()
        for mount in detected_mounts:
            if mount not in all_mount_points:
                all_mount_points.append(mount)
    
    # Add any additional mount points
    if possible_mount_points:
        for mount in possible_mount_points:
            if mount not in all_mount_points:
                all_mount_points.append(mount)
    
    # If still no mount points, add default /mnt
    if not all_mount_points:
        all_mount_points.append('/mnt')
    
    # First, try with direct conversion
    converted_path = convert_path_to_current_os(path, wsl_path_prefix)
    if os.path.exists(converted_path):
        return converted_path, True
    
    # Then try various mounts systematically
    found_paths = []
    
    # For Windows paths, try with all mount points
    if is_windows_path(path):
        drive_letter = path[0].lower()
        if '/' in path:
            path_part = path[2:] if path[2] == '/' else path[3:]
        else:
            path_part = path[2:] if path[2] == '\\' else path[3:]
            
        # Try all mount points
        for mount_point in all_mount_points:
            # Handle potential double slashes in path (common in CapCut)
            cleaned_path_part = path_part
            while '//' in cleaned_path_part:
                cleaned_path_part = cleaned_path_part.replace('//', '/')
            
            # Normalize backslashes
            cleaned_path_part = cleaned_path_part.replace('\\', '/')
            
            # Build path carefully to avoid double slashes
            # First create base path with drive letter
            base_path = f"{mount_point}/{drive_letter}"
            
            # Normalize path_part
            cleaned_path_part = cleaned_path_part.lstrip('/').lstrip('\\')
            
            # Create test paths
            test_paths = [
                os.path.join(base_path, cleaned_path_part).replace('\\', '/'),
                f"{base_path}/{cleaned_path_part}"
            ]
            
            for test_path in test_paths:
                if os.path.exists(test_path):
                    found_paths.append(test_path)
    
    # If we found paths, return the first one
    if found_paths:
        return found_paths[0], True
    
    # Path couldn't be resolved through any method
    return converted_path, False

def get_available_wsl_mounts():
    """Get all available WSL mount points for Windows drives."""
    try:
        if not os.path.exists('/proc/version') or 'microsoft' not in open('/proc/version').read().lower():
            return []
            
        mounts = []
        
        # Try using findmnt to find drvfs mounts
        try:
            output = subprocess.check_output(['findmnt', '-t', 'drvfs', '-n', '-o', 'TARGET']).decode('utf-8').strip()
            if output:
                mounts.extend(output.split('\n'))
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Check common WSL mount points
        common_mounts = ['/mnt', '/run/desktop/mnt/host']
        for mount in common_mounts:
            if os.path.exists(mount) and mount not in mounts:
                mounts.append(mount)
        
        return mounts
    except Exception as e:
        logger.warning(f"Error getting WSL mounts: {e}")
        return ['/mnt']  # Default to /mnt as fallback