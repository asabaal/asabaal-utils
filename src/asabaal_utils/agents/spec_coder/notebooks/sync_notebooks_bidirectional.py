#!/usr/bin/env python3
# %%
"""
Bidirectional notebook sync script - syncs from newer to older file.
Supports .py ↔ .ipynb synchronization based on file modification times.
"""

# %%
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

# %%
def get_file_mod_time(file_path: Path) -> datetime:
    """Get the modification time of a file."""
    if not file_path.exists():
        return datetime.min
    return datetime.fromtimestamp(file_path.stat().st_mtime)

# %%
def sync_file(source: Path, target: Path, file_type: str) -> bool:
    """
    Sync from source file to target file using jupytext.
    
    NOTE: This script does NOT create backup files to prevent accumulation
    of .backup files throughout the project. The sync is bidirectional
    and based on modification times, so data loss is minimal.
    
    Args:
        source: The newer file to sync from
        target: The older file to sync to
        file_type: 'py' or 'ipynb' indicating the target format
        
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"🔄 Syncing {source.name} → {target.name}")
        
        # NO BACKUP - overwrite target directly
        # This prevents accumulation of backup files
        
        # Determine jupytext conversion direction
        if file_type == 'ipynb':
            # Converting .py → .ipynb
            cmd = ['jupytext', '--to', 'ipynb', str(source), '--output', str(target)]
            # Add update flag only for ipynb conversions (jupytext limitation)
            cmd.append('--update')
        else:
            # Converting .ipynb → .py
            cmd = ['jupytext', '--to', 'py:percent', str(source), '--output', str(target)]
            # Don't add --update for py conversions - jupytext will overwrite by default
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Verify the target was created/updated
        if target.exists():
            # Sync timestamps - set target timestamp to match source
            source_time = get_file_mod_time(source)
            import os
            import time
            os.utime(target, (source_time.timestamp(), source_time.timestamp()))
            
            mod_time = get_file_mod_time(target)
            print(f"   ✅ Successfully synced {target.name} (timestamp synced: {mod_time.strftime('%H:%M:%S')})")
            return True
        else:
            print(f"   ❌ Failed to create {target.name}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error syncing {source.name}: {e}")
        if e.stderr:
            print(f"   stderr: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error with {source.name}: {e}")
        return False

# %%
def sync_notebook_pair(base_path: Path, notebook_name: str) -> tuple[bool, str]:
    """
    Sync a notebook pair (.py and .ipynb) from newer to older.
    
    Returns:
        (success, direction) where direction is 'py→ipynb', 'ipynb→py', or 'none'
    """
    py_file = base_path / f"{notebook_name}.py"
    ipynb_file = base_path / f"{notebook_name}.ipynb"
    
    # Check which files exist
    py_exists = py_file.exists()
    ipynb_exists = ipynb_file.exists()
    
    if not py_exists and not ipynb_exists:
        return False, "none"
    
    if py_exists and not ipynb_exists:
        # Only .py exists, create .ipynb
        success = sync_file(py_file, ipynb_file, 'ipynb')
        return success, "py→ipynb" if success else "none"
    
    if ipynb_exists and not py_exists:
        # Only .ipynb exists, create .py
        success = sync_file(ipynb_file, py_file, 'py')
        return success, "ipynb→py" if success else "none"
    
    # Both exist - compare modification times
    py_time = get_file_mod_time(py_file)
    ipynb_time = get_file_mod_time(ipynb_file)
    
    if py_time == ipynb_time:
        print(f"⏭️  {notebook_name}: Files are already in sync (same timestamp)")
        return True, "none"
    
    if py_time > ipynb_time:
        # .py is newer, sync to .ipynb
        success = sync_file(py_file, ipynb_file, 'ipynb')
        return success, "py→ipynb" if success else "none"
    else:
        # .ipynb is newer, sync to .py
        success = sync_file(ipynb_file, py_file, 'py')
        return success, "ipynb→py" if success else "none"

# %%
def find_notebook_pairs(base_path: Path) -> list[str]:
    """
    Find all notebook pairs (.py and/or .ipynb files) in the given directory.
    """
    notebook_names = set()
    
    # Find all .py files
    for py_file in base_path.rglob("*.py"):
        if py_file.is_file():
            # Convert path to relative name without extension
            rel_path = py_file.relative_to(base_path)
            notebook_name = str(rel_path.with_suffix(''))
            notebook_names.add(notebook_name)
    
    # Find all .ipynb files
    for ipynb_file in base_path.rglob("*.ipynb"):
        if ipynb_file.is_file():
            # Convert path to relative name without extension
            rel_path = ipynb_file.relative_to(base_path)
            notebook_name = str(rel_path.with_suffix(''))
            notebook_names.add(notebook_name)
    
    return sorted(notebook_names)

# %%
def main():
    """Main function to sync notebooks bidirectionally."""
    print("🔄 Bidirectional Notebook Sync")
    print("   Syncs from newer file to older file (.py ↔ .ipynb)")
    print("=" * 60)
    
    notebooks_dir = Path(__file__).parent
    
    # Check if jupytext is available
    try:
        subprocess.run(['jupytext', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ jupytext not found. Please install it with:")
        print("   pip install jupytext")
        return False
    
    # Get command line arguments
    force_all = '--all' in sys.argv
    specific_notebook = None
    
    # Check for specific notebook argument
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and arg.endswith('.py'):
            specific_notebook = arg[:-3]  # Remove .py extension
        elif not arg.startswith('--') and arg.endswith('.ipynb'):
            specific_notebook = arg[:-6]  # Remove .ipynb extension
    
    if specific_notebook:
        print(f"🎯 Syncing specific notebook: {specific_notebook}")
        notebook_names = [specific_notebook]
    elif force_all:
        print("🔍 Finding all notebook pairs...")
        notebook_names = find_notebook_pairs(notebooks_dir)
        print(f"   Found {len(notebook_names)} notebook pair(s)")
    else:
        # Default list of commonly updated notebooks
        notebook_names = [
            "module_specific/01_spec_parser_part1",
            "module_specific/02_code_generator_part1", 
            "module_specific/05_cli_interface_part1",
            "module_specific/09_aggregate_behaviors",
            "stage_specific/stage1_spec_to_scaffold",
            "stage_specific/stage5_healer"
        ]
        print(f"📋 Syncing default notebook list ({len(notebook_names)} files)")
        print("   Use --all to sync all notebooks, or specify a notebook name")
    
    # Sync each notebook pair
    success_count = 0
    sync_directions = {"py→ipynb": 0, "ipynb→py": 0, "none": 0}
    
    for notebook_name in notebook_names:
        print(f"\n📓 {notebook_name}")
        print("-" * 40)
        
        success, direction = sync_notebook_pair(notebooks_dir, notebook_name)
        
        if success:
            success_count += 1
        
        sync_directions[direction] += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Sync Summary:")
    print(f"   Total notebooks: {len(notebook_names)}")
    print(f"   Successfully synced: {success_count}")
    print(f"   .py → .ipynb: {sync_directions['py→ipynb']}")
    print(f"   .ipynb → .py: {sync_directions['ipynb→py']}")
    print(f"   Already in sync: {sync_directions['none']}")
    
    if success_count == len(notebook_names):
        print("🎉 All notebooks successfully synced!")
    else:
        failed = len(notebook_names) - success_count
        print(f"⚠️  {failed} notebook(s) failed to sync.")
    
    print("\n💡 Usage tips:")
    print("   • Run without arguments to sync default notebooks")
    print("   • Use --all to sync every notebook in the directory")
    print("   • Specify a notebook: python sync_notebooks_bidirectional.py stage1_spec_to_scaffold.py")
    print("   • The script automatically detects which file is newer")
    
    return success_count == len(notebook_names)

# %%
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
