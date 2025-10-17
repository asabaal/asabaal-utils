#!/usr/bin/env python3
"""
Integration Test Runner for Spec Coder Components

This script runs integration tests that require external dependencies like Ollama.
Use this to run integration tests separately from unit tests.

Usage:
    python run_integration_tests.py [--component COMPONENT] [--model MODEL]

Components:
    generator    - Test CodeGenerator with real AI calls
    tester       - Test TestAnalyzer/TestSummarizer with real AI calls
    healer       - Test Healer with real AI calls
    organizer    - Test Organizer with file organization workflow
    templates    - Test Templates with prompt generation workflow
    ollama       - Test OllamaClient with AI model interaction
    orchestrator - Test Orchestrator with pipeline coordination
    all          - Run all integration tests (default)

Models:
    qwen3-coder:latest (default)
    llama3.1:8b
    llama3.1:latest
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_integration_tests(component="all", model="qwen3-coder:latest"):
    """Run integration tests for specified component."""
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("❌ Ollama is not responding. Please start Ollama with: ollama serve")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Please start Ollama with: ollama serve")
        return False
    
    # Check if model is available
    models = response.json().get('models', [])
    model_names = [model.get('name', '') for model in models]
    
    if model not in model_names:
        print(f"❌ Model '{model}' not found. Available models:")
        for name in model_names:
            print(f"   - {name}")
        print(f"\nPull the model with: ollama pull {model}")
        return False
    
    print(f"✅ Ollama is running with model: {model}")
    
    # Determine which tests to run
    test_files = []
    
    if component in ["all", "generator"]:
        test_files.append("integration/test_generator_integration.py")
    
    if component in ["all", "tester"]:
        test_files.append("integration/test_tester_integration.py")
    
    if component in ["all", "healer"]:
        test_files.append("integration/test_healer_integration.py")
    
    if component in ["all", "organizer"]:
        test_files.append("integration/test_organizer_integration.py")
    
    if component in ["all", "templates"]:
        test_files.append("integration/test_templates_integration.py")
    
    if component in ["all", "ollama"]:
        test_files.append("integration/test_ollama_client_integration.py")
    
    if component in ["all", "orchestrator"]:
        test_files.append("integration/test_orchestrator_integration.py")
    
    if not test_files:
        print(f"❌ Unknown component: {component}")
        return False
    
    # Run the tests
    test_dir = Path(__file__).parent
    all_passed = True
    
    for test_file in test_files:
        print(f"\n🧪 Running {test_file}...")
        print("=" * 60)
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_dir / test_file),
            "-v",
            "-s",  # Show output
            "--tb=short"  # Short traceback format
        ]
        
        try:
            result = subprocess.run(cmd, cwd=test_dir.parent.parent.parent.parent, capture_output=False)
            if result.returncode != 0:
                all_passed = False
                print(f"❌ {test_file} failed")
            else:
                print(f"✅ {test_file} passed")
        except KeyboardInterrupt:
            print(f"\n⏹️  Interrupted {test_file}")
            return False
        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run integration tests for spec_coder components")
    parser.add_argument(
        "--component", 
        choices=["all", "generator", "tester", "healer", "organizer", "templates", "ollama", "orchestrator"], 
        default="all",
        help="Which component to test (default: all)"
    )
    parser.add_argument(
        "--model",
        default="qwen3-coder:latest",
        help="Which Ollama model to use (default: qwen3-coder:latest)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Integration Test Runner for Spec Coder")
    print(f"Component: {args.component}")
    print(f"Model: {args.model}")
    print("=" * 60)
    
    success = run_integration_tests(args.component, args.model)
    
    if success:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()