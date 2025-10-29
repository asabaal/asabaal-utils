#!/usr/bin/env python3
"""
CLI for bidirectional notebook synchronization using jupytext.
Syncs .py ↔ .ipynb files based on modification times.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def get_file_mod_time(file_path: Path) -> datetime:
    """Get the modification time of a file."""
    if not file_path.exists():
        return datetime.min
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def get_content_hash(file_path: Path) -> str:
    """Get a hash of the actual notebook content, ignoring metadata differences."""
    import hashlib
    
    try:
        # Convert to a common format for comparison
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp:
            if file_path.suffix == '.ipynb':
                # Convert .ipynb to .py format
                subprocess.run(['jupytext', '--to', 'py:percent', str(file_path), '--output', tmp.name], 
                             capture_output=True, check=True)
            else:
                # Copy .py file
                subprocess.run(['cp', str(file_path), tmp.name], check=True)
            
            # Read and normalize content
            with open(tmp.name, 'r') as f:
                content = f.read()
            
            # Remove jupytext metadata headers for comparison
            import re
            content = re.sub(r'^# ---.*?---\n\n', '', content, flags=re.DOTALL)
            
            # Clean up temp file
            import os
            os.unlink(tmp.name)
            
            # Return hash of normalized content
            return hashlib.md5(content.encode()).hexdigest()
            
    except Exception:
        return ""


def sync_file(source: Path, target: Path, file_type: str) -> bool:
    """
    Sync from source file to target file using jupytext.
    
    Args:
        source: The newer file to sync from
        target: The older file to sync to
        file_type: 'py' or 'ipynb' indicating the target format
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Determine jupytext conversion direction
        if file_type == 'ipynb':
            # Converting .py → .ipynb
            cmd = ['jupytext', '--to', 'ipynb', str(source), '--output', str(target)]
            cmd.append('--update')
        else:
            # Converting .ipynb → .py
            cmd = ['jupytext', '--to', 'py:percent', str(source), '--output', str(target)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            # If --update flag causes issues (e.g., version compatibility), try without it
            if '--update' in cmd and 'version' in e.stderr.lower():
                cmd.remove('--update')
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            else:
                raise
        
        # Verify the target was created/updated and content is actually synced
        if target.exists():
            # Verify content is equivalent by comparing hashes
            source_hash = get_content_hash(source)
            target_hash = get_content_hash(target)
            
            if source_hash != target_hash:
                # Content differs, sync failed
                return False
            
            # Sync timestamps - set target timestamp to match source
            source_time = get_file_mod_time(source)
            import os
            import time
            os.utime(target, (source_time.timestamp(), source_time.timestamp()))
            
            return True
        else:
            return False
            
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


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
    
    # Both exist - compare content first, then timestamps
    py_hash = get_content_hash(py_file)
    ipynb_hash = get_content_hash(ipynb_file)
    
    if py_hash == ipynb_hash:
        # Content is the same, sync timestamps to match and return
        py_time = get_file_mod_time(py_file)
        ipynb_time = get_file_mod_time(ipynb_file)
        
        # Set both timestamps to the newer one
        newer_time = max(py_time, ipynb_time)
        import os
        import time
        os.utime(py_file, (newer_time.timestamp(), newer_time.timestamp()))
        os.utime(ipynb_file, (newer_time.timestamp(), newer_time.timestamp()))
        
        return True, "none"
    
    # Content differs, use modification times to determine sync direction
    py_time = get_file_mod_time(py_file)
    ipynb_time = get_file_mod_time(ipynb_file)
    
    if py_time > ipynb_time:
        # .py is newer, sync to .ipynb
        success = sync_file(py_file, ipynb_file, 'ipynb')
        return success, "py→ipynb" if success else "none"
    else:
        # .ipynb is newer, sync to .py
        success = sync_file(ipynb_file, py_file, 'py')
        return success, "ipynb→py" if success else "none"


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


def clean_notebook_name(name: str) -> str:
    """Clean notebook name by removing .py or .ipynb extensions if present."""
    # Keep the directory path, just remove the extension
    if name.endswith('.py'):
        return name[:-3]
    elif name.endswith('.ipynb'):
        return name[:-6]
    return name


@click.command()
@click.argument('directory', type=click.Path(exists=True, path_type=Path), required=True)
@click.option('--all', 'sync_all', is_flag=True, help='Sync all notebook pairs in the directory')
@click.option('--notebook', '-n', multiple=True, help='Sync specific notebook(s) by name (with or without extension)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed sync information')
def sync_notebooks(directory: Path, sync_all: bool, notebook: tuple, verbose: bool):
    """
    Bidirectional notebook synchronization using jupytext.
    
    Syncs .py ↔ .ipynb files based on modification times from newer to older.
    
    DIRECTORY: Path to the directory containing notebooks to sync
    """
    
    # Check if jupytext is available
    try:
        subprocess.run(['jupytext', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("❌ jupytext not found. Please install it with:", style="red")
        console.print("   pip install jupytext", style="yellow")
        sys.exit(1)
    
    console.print("🔄 Bidirectional Notebook Sync", style="blue")
    console.print(f"   Directory: {directory}", style="dim")
    console.print("=" * 60)
    
    # Determine which notebooks to sync
    if notebook:
        # Clean notebook names by removing extensions if present
        notebook_names = [clean_notebook_name(name) for name in notebook]
        console.print(f"🎯 Syncing {len(notebook_names)} specific notebook(s)", style="green")
    elif sync_all:
        console.print("🔍 Finding all notebook pairs...", style="yellow")
        notebook_names = find_notebook_pairs(directory)
        console.print(f"   Found {len(notebook_names)} notebook pair(s)", style="dim")
    else:
        console.print("❌ No notebooks specified. Use --all or --notebook", style="red")
        console.print("   Use --help for usage information", style="dim")
        sys.exit(1)
    
    if not notebook_names:
        console.print("📭 No notebooks found to sync", style="yellow")
        return
    
    # Sync each notebook pair
    success_count = 0
    sync_directions = {"py→ipynb": 0, "ipynb→py": 0, "none": 0}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        sync_task = progress.add_task("Syncing notebooks...", total=len(notebook_names))
        
        for notebook_name in notebook_names:
            if verbose:
                console.print(f"\n📓 {notebook_name}", style="blue")
                console.print("-" * 40)
            
            success, direction = sync_notebook_pair(directory, notebook_name)
            
            if success:
                success_count += 1
            
            sync_directions[direction] += 1
            
            if verbose:
                if direction == "none":
                    console.print(f"⏭️  Already in sync", style="dim")
                elif direction == "py→ipynb":
                    console.print(f"🔄 .py → .ipynb", style="green")
                elif direction == "ipynb→py":
                    console.print(f"🔄 .ipynb → .py", style="green")
                else:
                    console.print(f"❌ Failed to sync", style="red")
            
            progress.advance(sync_task)
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("📊 Sync Summary:", style="blue")
    console.print(f"   Total notebooks: {len(notebook_names)}", style="dim")
    console.print(f"   Successfully synced: {success_count}", style="green")
    console.print(f"   .py → .ipynb: {sync_directions['py→ipynb']}", style="cyan")
    console.print(f"   .ipynb → .py: {sync_directions['ipynb→py']}", style="cyan")
    console.print(f"   Already in sync: {sync_directions['none']}", style="dim")
    
    if success_count == len(notebook_names):
        console.print("🎉 All notebooks successfully synced!", style="green bold")
    else:
        failed = len(notebook_names) - success_count
        console.print(f"⚠️  {failed} notebook(s) failed to sync.", style="yellow")
    
    if not verbose:
        console.print("\n💡 Use --verbose for detailed sync information", style="dim")


def main():
    """Entry point for the CLI."""
    sync_notebooks()


if __name__ == "__main__":
    main()