"""
Path utilities for PR analyzer - provides robust path resolution
"""

from pathlib import Path

def find_repo_root(start_path: Path = None) -> Path:
    """
    Find the asabaal-utils repository root by walking up the directory tree.
    
    Args:
        start_path: Starting path (defaults to current file's location)
        
    Returns:
        Path to the repository root
        
    Raises:
        Exception: If repository root cannot be found
    """
    if start_path is None:
        start_path = Path(__file__)
    
    current = start_path.resolve()
    
    # Walk up until we find the repo root
    while current.name != "asabaal-utils" and current.parent != current:
        current = current.parent
    
    if current.name != "asabaal-utils":
        raise Exception(f"Could not find asabaal-utils repository root from {start_path}")
    
    return current

def get_config_path(config_file: str) -> Path:
    """Get path to a config file in the pr_analyzer/config directory"""
    repo_root = find_repo_root()
    return repo_root / "src" / "asabaal_utils" / "pr_analyzer" / "config" / config_file

def get_template_path(template_file: str) -> Path:
    """Get path to a template file in the templates directory"""
    repo_root = find_repo_root()
    return repo_root / "templates" / template_file

def get_main_output_dir(debug_output_dir: Path) -> Path:
    """
    Get the main output directory from a debug output subdirectory.
    
    Args:
        debug_output_dir: Path like .../pr_analysis_output/debug_outputs/stage1
        
    Returns:
        Path to main output directory (pr_analysis_output)
    """
    current = debug_output_dir.resolve()
    
    # Walk up until we find a directory containing "debug_outputs"
    while current.name not in ["pr_analysis_output", "test_output"] and current.parent != current:
        current = current.parent
        
    if current.name in ["pr_analysis_output", "test_output"]:
        return current
    else:
        # Fallback: assume debug_outputs is 2 levels down
        return debug_output_dir.parent.parent