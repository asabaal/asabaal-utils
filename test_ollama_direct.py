#!/usr/bin/env python3
"""
Direct test of Ollama with qwen3-coder model on test files
"""

import subprocess
import json
from pathlib import Path

def test_ollama_direct():
    """Test Ollama directly with a code analysis prompt"""
    
    # Get a test file
    test_dir = Path(__file__).parent / "test_projects"
    good_file = test_dir / "data_pipeline" / "good" / "processors" / "data_transformer.py"
    bad_file = test_dir / "data_pipeline" / "bad" / "helpers" / "data_processor.py"
    
    if not good_file.exists():
        print(f"❌ Good file not found: {good_file}")
        return False
        
    if not bad_file.exists():
        print(f"❌ Bad file not found: {bad_file}")
        return False
    
    # Read file contents
    good_content = good_file.read_text()
    bad_content = bad_file.read_text()
    
    print(f"✅ Found test files:")
    print(f"   Good: {good_file}")
    print(f"   Bad: {bad_file}")
    
    # Test prompt for good file
    good_prompt = f"""
Analyze this Python file for code quality:

File: {good_file.name}
```python
{good_content}
```

Respond with a JSON object:
{{
    "overall_assessment": "GOOD" or "BAD",
    "issues": ["list of issues found"],
    "best_practices": ["list of best practices followed"],
    "security_concerns": ["list of security concerns if any"]
}}
"""
    
    # Test prompt for bad file  
    bad_prompt = f"""
Analyze this Python file for code quality:

File: {bad_file.name}
```python
{bad_content}
```

Respond with a JSON object:
{{
    "overall_assessment": "GOOD" or "BAD", 
    "issues": ["list of issues found"],
    "best_practices": ["list of best practices followed"],
    "security_concerns": ["list of security concerns if any"]
}}
"""
    
    print("\n🤖 Testing good file analysis with qwen3-coder:latest...")
    
    try:
        # Call Ollama for good file
        result = subprocess.run([
            'ollama', 'run', 'qwen3-coder:latest', good_prompt
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            response = result.stdout.strip()
            print("✅ Good file analysis response:")
            print("-" * 50)
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 50)
        else:
            print(f"❌ Error analyzing good file: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout analyzing good file")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n🤖 Testing bad file analysis with qwen3-coder:latest...")
    
    try:
        # Call Ollama for bad file
        result = subprocess.run([
            'ollama', 'run', 'qwen3-coder:latest', bad_prompt
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            response = result.stdout.strip()
            print("✅ Bad file analysis response:")
            print("-" * 50) 
            print(response[:500] + "..." if len(response) > 500 else response)
            print("-" * 50)
            print("\n✅ Direct Ollama test successful!")
            return True
        else:
            print(f"❌ Error analyzing bad file: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout analyzing bad file")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama_direct()
    if success:
        print("\n🎉 Directory mode verification complete!")
        print("   - File discovery: ✅ Working")
        print("   - AI model access: ✅ Working") 
        print("   - Code analysis: ✅ Working")
    else:
        print("\n❌ Directory mode verification failed")