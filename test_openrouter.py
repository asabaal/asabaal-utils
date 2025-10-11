#!/usr/bin/env python3
"""
Test OpenRouter client
"""

import sys
import os
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import OpenRouter client directly
sys.path.insert(0, str(Path(__file__).parent / "src" / "asabaal_utils" / "agentic_toolkit"))
from openrouter_client import OpenRouterClient

def test_openrouter():
    """Test OpenRouter client"""
    print("🧪 Testing OpenRouter client...")
    
    try:
        client = OpenRouterClient()
        print("✅ OpenRouter client initialized successfully")
        
        # Test with a simple prompt
        prompt = "Hello, please respond with just 'OpenRouter test successful' and nothing else."
        print(f"🔄 Sending test prompt: {prompt}")
        
        response = client.ask(prompt).content
        print(f"✅ Response received: {response}")
        
        if "OpenRouter test successful" in response:
            print("🎉 OpenRouter client test PASSED!")
            return True
        else:
            print("❌ OpenRouter client test FAILED - unexpected response")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter client test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_openrouter()
    sys.exit(0 if success else 1)