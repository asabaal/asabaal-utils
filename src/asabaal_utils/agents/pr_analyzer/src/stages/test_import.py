#!/usr/bin/env python3
from pathlib import Path
import sys

print("Current file:", __file__)
print("Current directory:", Path.cwd())

shared_path = Path(__file__).parent.parent.parent.parent / "shared"
print(f"Shared path: {shared_path}")
print(f"Exists: {shared_path.exists()}")

if shared_path.exists():
    print(f"Contents: {[d.name for d in shared_path.iterdir()]}")

# Test the import - add asabaal_utils root to path
asabaal_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(asabaal_root))
sys.path.insert(0, str(shared_path))
try:
    from asabaal_utils.shared.agentic_toolkit.backend_config import BackendManager
    print("✅ BackendManager import successful")
except ImportError as e:
    print(f"❌ BackendManager import failed: {e}")