#!/usr/bin/env python3
"""
Test script to verify PR agent migration success
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test importing from new location
        sys.path.insert(0, str(Path(__file__).parent / "shared"))
        sys.path.insert(0, str(Path(__file__).parent / "agents" / "pr-analyzer" / "src"))
        
        from analyzer import UnifiedPRAnalyzer
        print("✅ UnifiedPRAnalyzer import successful")
        
        from cli import main
        print("✅ CLI import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_directory_structure():
    """Test that directory structure is correct"""
    print("📁 Testing directory structure...")
    
    base_path = Path(__file__).parent
    required_dirs = [
        "agents/pr-analyzer/src",
        "agents/pr-analyzer/src/stages",
        "agents/pr-analyzer/src/core", 
        "agents/pr-analyzer/src/classifiers",
        "agents/pr-analyzer/src/utils",
        "agents/pr-analyzer/configs",
        "shared/agentic_toolkit",
        "shared/mathematical_models"
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            return False
    
    return True

def test_key_files():
    """Test that key files exist"""
    print("📄 Testing key files...")
    
    base_path = Path(__file__).parent
    required_files = [
        "agents/pr-analyzer/src/analyzer.py",
        "agents/pr-analyzer/src/cli.py",
        "agents/pr-analyzer/src/__init__.py",
        "agents/pr-analyzer/configs/config/analysis_config.yaml",
        "agents/pr-analyzer/configs/config/file_categories.yaml"
    ]
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🔍 PR AGENT MIGRATION VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Key Files", test_key_files),
        ("Imports", test_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Migration appears successful.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED! Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())