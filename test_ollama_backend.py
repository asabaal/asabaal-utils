#!/usr/bin/env python3
"""Test script for Ollama backend integration."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_backend_imports():
    """Test that we can import the backend modules."""
    print("Testing backend imports...")
    
    try:
        from asabaal_utils.agentic_toolkit.ollama_client import OllamaClient, test_ollama_connection
        print("✅ OllamaClient import successful")
    except Exception as e:
        print(f"❌ OllamaClient import failed: {e}")
        return False
    
    try:
        from asabaal_utils.agentic_toolkit.backend_config import BackendManager, list_available_backends
        print("✅ BackendManager import successful")
    except Exception as e:
        print(f"❌ BackendManager import failed: {e}")
        return False
    
    return True

def test_ollama_availability():
    """Test if Ollama is available and working."""
    print("\nTesting Ollama availability...")
    
    try:
        from asabaal_utils.agentic_toolkit.ollama_client import test_ollama_connection
        
        # Test with a smaller model first
        if test_ollama_connection("qwen2.5-coder:7b"):
            print("✅ Ollama connection successful with 7B model")
            return True
        else:
            print("⚠️  Trying 32B model...")
            if test_ollama_connection("qwen2.5-coder:32b"):
                print("✅ Ollama connection successful with 32B model")
                return True
            else:
                print("❌ Ollama connection failed")
                return False
                
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

def test_backend_manager():
    """Test the backend manager."""
    print("\nTesting BackendManager...")
    
    try:
        from asabaal_utils.agentic_toolkit.backend_config import BackendManager, list_available_backends
        
        # List available backends
        backends = list_available_backends()
        print("Available backends:")
        for name, info in backends.items():
            status = "✅" if info['available'] else "❌"
            print(f"  {status} {name}")
        
        # Create backend manager
        manager = BackendManager()
        backend_info = manager.get_backend_info()
        print(f"\nSelected backend: {backend_info}")
        
        if backend_info['available']:
            # Test a simple call
            response = manager.call_agent("Hello! Respond with just 'OK'.")
            if 'OK' in response.upper():
                print("✅ Backend manager test successful")
                return True
            else:
                print(f"⚠️  Unexpected response: {response}")
                return False
        else:
            print("❌ Selected backend not available")
            return False
            
    except Exception as e:
        print(f"❌ Backend manager test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Ollama Backend Integration")
    print("=" * 50)
    
    # Test imports
    if not test_backend_imports():
        print("\n❌ Import tests failed - cannot continue")
        return False
    
    # Test Ollama availability
    ollama_available = test_ollama_availability()
    
    # Test backend manager
    backend_manager_works = test_backend_manager()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Imports: ✅")
    print(f"  Ollama: {'✅' if ollama_available else '❌'}")
    print(f"  Backend Manager: {'✅' if backend_manager_works else '❌'}")
    
    if ollama_available and backend_manager_works:
        print("\n🎉 All tests passed! Ready for local PR analysis.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)