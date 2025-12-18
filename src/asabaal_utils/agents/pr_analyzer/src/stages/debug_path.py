#!/usr/bin/env python3
from pathlib import Path
import sys

print("Current file:", __file__)
asabaal_root = Path(__file__).parent.parent.parent.parent.parent
print(f'Asabaal root: {asabaal_root}')
print(f'Exists: {asabaal_root.exists()}')
if asabaal_root.exists():
    print(f'Contents: {[d.name for d in asabaal_root.iterdir() if d.is_dir()]}')

# Check for shared directory
shared_path = asabaal_root / "shared"
print(f'Shared path: {shared_path}')
print(f'Exists: {shared_path.exists()}')

if shared_path.exists():
    print(f'Shared contents: {[d.name for d in shared_path.iterdir()]}')
    
    # Test the import
    import sys
    parent_root = asabaal_root.parent  # This should be /home/asabaal/repos/asabaal-utils/src
    sys.path.insert(0, str(parent_root))
    sys.path.insert(0, str(shared_path))
    
    try:
        from asabaal_utils.shared.agentic_toolkit.backend_config import BackendManager
        print("✅ BackendManager import successful")
    except ImportError as e:
        print(f"❌ BackendManager import failed: {e}")