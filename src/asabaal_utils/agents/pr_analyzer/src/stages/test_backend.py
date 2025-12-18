#!/usr/bin/env python3
import sys
from pathlib import Path

# Add paths
asabaal_root = Path(__file__).parent.parent.parent.parent.parent
parent_root = asabaal_root.parent
shared_path = asabaal_root / "shared"

sys.path.insert(0, str(parent_root))
sys.path.insert(0, str(shared_path))

try:
    from asabaal_utils.shared.agentic_toolkit.backend_config import BackendManager, list_available_backends
    print("✅ Imports successful")
    
    # List backends
    backends = list_available_backends()
    print("Available backends:")
    for name, info in backends.items():
        status = "✅" if info['available'] else "❌"
        print(f"  {status} {name}: {info}")
    
    # Create backend manager
    manager = BackendManager()
    backend_info = manager.get_backend_info()
    print(f"\nSelected backend: {backend_info}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()