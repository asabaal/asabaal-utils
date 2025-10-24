#!/usr/bin/env python3
"""
Test AI communication with directory mode
"""

import os
import sys
import json
from pathlib import Path

# Add the analyzer source to Python path
analyzer_src = Path(__file__).parent / "agents" / "pr_analyzer" / "src"
sys.path.insert(0, str(analyzer_src))

# Set test mode
os.environ['PR_ANALYZER_TEST_MODE'] = 'true'

try:
    # Import required modules
    import importlib.util
    
    # Import git analyzer
    spec = importlib.util.spec_from_file_location(
        "git_analyzer", 
        analyzer_src / "core" / "git_analyzer.py"
    )
    git_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(git_analyzer)
    
    # Import AI communicator
    spec = importlib.util.spec_from_file_location(
        "ai_communicator", 
        analyzer_src / "stages" / "stage3_agent_communication.py"
    )
    ai_communicator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ai_communicator)
    
    print("✅ Successfully imported modules")
    
    # Initialize git analyzer and get test files
    test_dir = Path(__file__).parent / "test_projects"
    git_analyzer_instance = git_analyzer.GitAnalyzer(str(test_dir))
    changes = git_analyzer_instance._get_test_file_changes()
    
    print(f"📁 Found {len(changes)} files for analysis")
    
    # Initialize AI communicator with qwen3-coder model
    config = {
        'agentic_backend': {
            'provider': 'ollama',
            'model': 'qwen3-coder:latest'
        }
    }
    
    communicator = ai_communicator.RobustAgentCaller(str(test_dir), config)
    
    print("✅ AI communicator initialized with qwen3-coder:latest")
    
    # Test with a simple prompt about the first file
    first_file = changes[0]
    test_prompt = f"""
Analyze this Python file for code quality issues:

File: {first_file.file_path}
```python
{first_file.content}
```

Please identify:
1. Code quality issues (if any)
2. Best practices violations (if any) 
3. Security concerns (if any)
4. Overall assessment: GOOD or BAD code

Keep your response brief and focused.
"""
    
    print("🤖 Sending test prompt to AI...")
    response = communicator.call_agent(test_prompt)
    
    if response:
        print("✅ AI response received:")
        print("-" * 50)
        print(response[:500] + "..." if len(response) > 500 else response)
        print("-" * 50)
        print("✅ Directory mode with AI communication successful!")
    else:
        print("❌ No response from AI")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()