#!/usr/bin/env python3
"""
Simple test to verify the cleanup worked
"""

import sys
from pathlib import Path

def test_structure():
    """Test that the structure is clean"""
    print("🧪 Testing cleaned structure...")
    
    # Check that old structures are gone
    old_paths = [
        "src/asabaal_utils/pr_analyzer",
        "pr_analyzer"
    ]
    
    for path in old_paths:
        if Path(path).exists():
            print(f"❌ Old structure still exists: {path}")
            return False
        else:
            print(f"✅ Old structure removed: {path}")
    
    # Check that new structure exists
    new_paths = [
        "agents/pr_analyzer/src",
        "agents/pr_analyzer/configs",
        "src/asabaal_utils/shared"
    ]
    
    for path in new_paths:
        if Path(path).exists():
            print(f"✅ New structure exists: {path}")
        else:
            print(f"❌ New structure missing: {path}")
            return False
    
    # Check root is cleaner
    root_files = list(Path(".").glob("*.py"))
    if len(root_files) > 5:  # Allow for a few legitimate root files
        print(f"⚠️  Root still has many Python files: {len(root_files)}")
        print(f"   Files: {[f.name for f in root_files]}")
    else:
        print(f"✅ Root directory is cleaner: {len(root_files)} Python files")
    
    return True

def test_key_files():
    """Test that key files are in right places"""
    print("\n📁 Testing key file locations...")
    
    key_files = {
        "agents/pr_analyzer/src/analyzer.py": "Main analyzer",
        "agents/pr_analyzer/src/cli.py": "CLI interface", 
        "src/asabaal_utils/shared/agentic_toolkit/__init__.py": "Shared toolkit",
        "docs/README.md": "Main docs",
        "scripts/test_pr_agent_migration.py": "Test scripts"
    }
    
    all_exist = True
    for file_path, description in key_files.items():
        if Path(file_path).exists():
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    print("=" * 60)
    print("🧹 REPOSITORY CLEANUP VERIFICATION")
    print("=" * 60)
    
    structure_ok = test_structure()
    files_ok = test_key_files()
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if structure_ok and files_ok:
        print("🎉 CLEANUP SUCCESSFUL!")
        print("✅ Old structures removed")
        print("✅ New modular structure in place")
        print("✅ Files organized properly")
        return 0
    else:
        print("⚠️  CLEANUP INCOMPLETE")
        if not structure_ok:
            print("❌ Structure issues remain")
        if not files_ok:
            print("❌ Key files missing")
        return 1

if __name__ == "__main__":
    sys.exit(main())