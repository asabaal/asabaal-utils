# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 6: Code Organizer - Part 1
#
# ## 🎯 **Module Overview**
# This module documents the `organizer.py` file - the code organization and consolidation system. The CodeOrganizer transforms generated code into a clean, modular architecture suitable for production use.
#
# ## 📋 **What We'll Learn**
# - File categorization and organization strategies
# - Directory structure creation and management
# - Test file consolidation and import fixing
# - Module initialization file generation
# - Infrastructure separation from production code
# - Validation and logging of organization process
#
# ## 🔧 **Key Components**
# - **File Categorization**: Maps files to appropriate modules based on keywords
# - **Directory Management**: Creates and maintains proper directory structure
# - **Test Consolidation**: Merges and fixes test files from multiple sources
# - **Module Generation**: Creates __init__.py files and module consolidations
# - **Import Fixing**: Updates import statements to match new structure
# - **Validation**: Ensures organization was successful

# %%
# Cell 1: Setup and Mock Dependencies
import json
import shutil
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional
import re

# Create temporary directories for testing
temp_base = Path(tempfile.mkdtemp())
print(f"📁 Temporary base directory: {temp_base}")

# Create directory structure
generated_dir = temp_base / "generated_functions"
reports_dir = temp_base / "reports"
test_env_dir = reports_dir / "test_env"
src_dir = temp_base / "src"
tests_dir = temp_base / "tests"

for dir_path in [generated_dir, reports_dir, test_env_dir, src_dir, tests_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Create mock integration summary
integration_summary = {
    "stages": {
        "test_results": {
            "results": [
                {"function": "generate_time_grid", "success": True},
                {"function": "apply_accent_pattern", "success": True},
                {"function": "export_as_midi", "success": True},
                {"function": "generate_song", "success": False}
            ]
        }
    }
}

# Save integration summary
summary_file = reports_dir / "latest_integration_summary.json"
with open(summary_file, 'w') as f:
    json.dump(integration_summary, f)

# Create mock generated files
mock_files = {
    "generate_time_grid.py": "def generate_time_grid(): pass",
    "apply_accent_pattern.py": "def apply_accent_pattern(): pass",
    "export_as_midi.py": "def export_as_midi(): pass",
    "validate_data.py": "def validate_data(): pass"
}

for filename, content in mock_files.items():
    (generated_dir / filename).write_text(content)

# Create mock test files
test_env_func_dir = test_env_dir / "generate_time_grid"
test_env_func_dir.mkdir(exist_ok=True)
(test_env_func_dir / "test_generate_time_grid.py").write_text("def test_generate_time_grid(): pass")

print("✅ Mock environment setup complete")
print(f"📁 Generated files: {list(generated_dir.glob('*.py'))}")
print(f"🧪 Test files: {list(test_env_dir.rglob('test_*.py'))}")
print(f"📊 Integration summary: {summary_file.exists()}")

# %%
# Cell 2: CodeOrganizer Class Initialization
"""
Lines 18-40: CodeOrganizer class initialization

The CodeOrganizer class sets up the directory structure and configuration
for organizing generated code into a production-ready architecture.
"""

class CodeOrganizer:
    """Organizes generated code into production-ready structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Lines 21-40: Initialize the CodeOrganizer
        
        Sets up:
        - Base directory (defaults to current script directory)
        - Directory paths for generated code, reports, source, tests
        - Organization log for tracking actions
        - File categorization mapping based on keywords
        """
        self.base_dir = base_dir if base_dir is not None else temp_base
        self.generated_dir = self.base_dir / "generated_functions"
        self.reports_dir = self.base_dir / "reports"
        self.test_env_dir = self.reports_dir / "test_env"
        self.src_dir = self.base_dir / "src"
        self.tests_dir = self.base_dir / "tests"
        
        # Organization log
        self.log_entries = []
        self.timestamp = time.time()
        
        # File categorization mapping
        self.category_mapping = {
            "core": ["generate_time_grid", "apply_accent", "pattern", "rhythm", "timegrid"],
            "export": ["export_as_midi", "midi_export"],
            "generate": ["song", "structure", "generate"],
            "utils": ["validate", "io", "utils", "validation"]
        }

# Test the initialization
print("🧪 Testing CodeOrganizer initialization:")

organizer = CodeOrganizer(base_dir=temp_base)

print(f"📁 Base directory: {organizer.base_dir}")
print(f"📂 Generated directory: {organizer.generated_dir}")
print(f"📊 Reports directory: {organizer.reports_dir}")
print(f"🧪 Test environment: {organizer.test_env_dir}")
print(f"💻 Source directory: {organizer.src_dir}")
print(f"🧪 Tests directory: {organizer.tests_dir}")
print(f"📝 Log entries: {len(organizer.log_entries)}")
print(f"🏷️  Categories: {list(organizer.category_mapping.keys())}")

print("\n📋 Category mapping:")
for category, keywords in organizer.category_mapping.items():
    print(f"   {category}: {keywords}")

# %%
# Cell 3: Directory and File Management Methods
"""
Lines 41-64: Directory creation and file categorization methods

These methods handle the fundamental operations of creating directories
and categorizing files based on their names and content.
"""

def ensure_dir(self, path: Path) -> None:
    """
    Lines 41-53: Create directory and __init__.py file
    
    Creates the directory if it doesn't exist, and adds an __init__.py file
    to make it a proper Python package. Logs the creation action.
    """
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        self.log_entries.append({
            "action": "create_init",
            "file": "__init__.py",
            "path": str(init_file),
            "timestamp": self.timestamp
        })

def categorize_file(self, filename) -> str:
    """
    Lines 54-63: Determine file category based on keywords
    
    Uses the category_mapping to determine which category a file belongs to
    based on keywords in the filename. Returns 'misc' if no match found.
    """
    filename_str = str(filename)
    filename_lower = filename_str.lower()
    
    for category, keywords in self.category_mapping.items():
        if any(keyword in filename_lower for keyword in keywords):
            return category
    
    return "misc"  # Default category

# Add methods to the class
CodeOrganizer.ensure_dir = ensure_dir
CodeOrganizer.categorize_file = categorize_file

# Test directory creation
print("🧪 Testing directory management:")

test_dir = temp_base / "test_module"
print(f"📁 Creating directory: {test_dir}")
organizer.ensure_dir(test_dir)

init_file = test_dir / "__init__.py"
print(f"📄 __init__.py exists: {init_file.exists()}")
print(f"📝 Log entries after dir creation: {len(organizer.log_entries)}")

# Test file categorization
print("\n🏷️  Testing file categorization:")

test_files = [
    "generate_time_grid.py",
    "apply_accent_pattern.py", 
    "export_as_midi.py",
    "generate_song.py",
    "validate_data.py",
    "unknown_file.py"
]

for filename in test_files:
    category = organizer.categorize_file(filename)
    print(f"   {filename} → {category}")

# %%
# Cell 4: Integration Summary Processing
"""
Lines 65-84: Integration summary loading and successful function extraction

These methods process the integration summary to identify which functions
passed their tests and should be included in the organized codebase.
"""

def load_integration_summary(self) -> Dict:
    """
    Lines 65-72: Load the latest integration summary
    
    Reads the integration summary JSON file to get test results
    and other pipeline information.
    """
    summary_file = self.reports_dir / "latest_integration_summary.json"
    if not summary_file.exists():
        raise FileNotFoundError(f"Integration summary not found: {summary_file}")
    
    with open(summary_file) as f:
        return json.load(f)

def extract_successful_functions(self, summary: Dict) -> List[Dict]:
    """
    Lines 74-84: Extract successful function results
    
    Filters the test results to return only functions that
    passed their tests (success=True).
    """
    test_results = summary.get("stages", {}).get("test_results", {})
    results = test_results.get("results", [])
    
    successful = []
    for result in results:
        if result.get("success", False):
            successful.append(result)
    
    return successful

# Add methods to the class
CodeOrganizer.load_integration_summary = load_integration_summary
CodeOrganizer.extract_successful_functions = extract_successful_functions

# Test integration summary processing
print("🧪 Testing integration summary processing:")

try:
    summary = organizer.load_integration_summary()
    print(f"📊 Integration summary loaded successfully")
    print(f"📋 Stages: {list(summary.get('stages', {}).keys())}")
    
    successful_functions = organizer.extract_successful_functions(summary)
    print(f"\n✅ Successful functions ({len(successful_functions)}):")
    for func in successful_functions:
        print(f"   - {func.get('function', 'Unknown')}: {func.get('success', False)}")
        
except FileNotFoundError as e:
    print(f"❌ {e}")
except Exception as e:
    print(f"❌ Error processing summary: {e}")

# %%
# Cell 5: File Movement and Organization
"""
Lines 86-116: Moving generated files to appropriate directories

These methods handle the core organization task of moving files
from the generated_functions directory to categorized src subdirectories.
"""

def move_generated_files(self) -> None:
    """
    Lines 86-116: Move generated Python files to appropriate src subdirectories
    
    Process:
    1. Check if generated_functions directory exists
    2. For each Python file, determine its category
    3. Create target directory if needed
    4. Move file and log the action
    """
    if not self.generated_dir.exists():
        print(f"⚠️  Generated functions directory not found: {self.generated_dir}")
        return
    
    print(f"📁 Moving files from {self.generated_dir} to {self.src_dir}")
    
    for py_file in self.generated_dir.glob("*.py"):
        category = self.categorize_file(py_file.name)
        target_dir = self.src_dir / category
        
        # Ensure target directory exists
        self.ensure_dir(target_dir)
        
        # Move file
        target_path = target_dir / py_file.name
        shutil.move(str(py_file), str(target_path))
        
        # Log the move
        self.log_entries.append({
            "action": "move_file",
            "file": py_file.name,
            "from": str(py_file),
            "to": str(target_path),
            "category": category,
            "timestamp": self.timestamp
        })
        
        print(f"   📄 {py_file.name} → {category}/")

# Add method to the class
CodeOrganizer.move_generated_files = move_generated_files

# Test file movement
print("🧪 Testing file movement:")
print(f"📁 Files before move: {list(generated_dir.glob('*.py'))}")

organizer.move_generated_files()

print(f"\n📁 Files after move: {list(generated_dir.glob('*.py'))}")
print("\n📂 Organized files:")
for category_dir in src_dir.iterdir():
    if category_dir.is_dir():
        files = list(category_dir.glob("*.py"))
        if files:
            print(f"   {category_dir.name}/: {[f.name for f in files]}")

print(f"\n📝 Log entries after move: {len(organizer.log_entries)}")
move_logs = [log for log in organizer.log_entries if log['action'] == 'move_file']
print(f"📊 Move operations: {len(move_logs)}")

# %%
# Cell 6: Test Consolidation and Import Fixing
"""
Lines 117-168: Test file consolidation and import fixing

These methods handle consolidating test files from multiple sources
and fixing import statements to match the new module structure.
"""

def consolidate_tests(self) -> None:
    """
    Lines 117-168: Consolidate all test files into tests/ directory and fix imports
    
    Process:
    1. Ensure tests directory exists
    2. Fix imports in existing test files
    3. Copy new test files from test_env
    4. Fix imports in copied files
    5. Log all actions
    """
    # Ensure tests directory exists
    self.ensure_dir(self.tests_dir)
    
    test_files_fixed = 0
    
    # First, fix imports in existing test files
    if self.tests_dir.exists():
        print(f"🔧 Fixing imports in existing test files in {self.tests_dir}")
        for test_file in self.tests_dir.glob("test_*.py"):
            self.fix_test_imports(test_file)
            test_files_fixed += 1
    
    # Then, copy any new test files from test_env
    if self.test_env_dir.exists():
        print(f"🧪 Copying additional tests from {self.test_env_dir} to {self.tests_dir}")
        
        test_files_copied = 0
        for test_file in self.test_env_dir.glob("**/test_*.py"):
            target_path = self.tests_dir / test_file.name
            
            # Avoid overwriting if file already exists
            if target_path.exists():
                print(f"   ⚠️  Test file already exists: {test_file.name}")
                continue
            
            shutil.copy(str(test_file), str(target_path))
            
            # Fix imports in the copied test file
            self.fix_test_imports(target_path)
            
            # Log the copy
            self.log_entries.append({
                "action": "copy_test",
                "file": test_file.name,
                "from": str(test_file),
                "to": str(target_path),
                "timestamp": self.timestamp
            })
            
            test_files_copied += 1
            print(f"   🧪 {test_file.name}")
        
        print(f"   📊 Copied {test_files_copied} new test files")
    
    print(f"   🔧 Fixed imports in {test_files_fixed} existing test files")

def fix_test_imports(self, test_file: Path) -> None:
    """
    Lines 462-508: Fix import statements in test files
    
    Updates import statements to match the new module structure.
    Maps old import paths to new categorized paths.
    """
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Define import mappings based on file organization
        import_mappings = {
            # Core functions
            'from generate_time_grid import generate_time_grid': 'from src.core.generate_time_grid import generate_time_grid',
            'from apply_accent_pattern import apply_accent_pattern': 'from src.core.apply_accent_pattern import apply_accent_pattern',
            # Export functions
            'from export_as_midi import export_as_midi': 'from src.export.export_as_midi import export_as_midi',
            # Generate functions
            'from generate import generate': 'from src.generate.generate import generate',
        }
        
        # Apply import fixes
        for old_import, new_import in import_mappings.items():
            content = content.replace(old_import, new_import)
        
        # Only write if content changed
        if content != original_content:
            with open(test_file, 'w') as f:
                f.write(content)
            
            self.log_entries.append({
                "action": "fix_test_import",
                "file": test_file.name,
                "path": str(test_file),
                "timestamp": self.timestamp
            })
            print(f"   🔧 Fixed imports in {test_file.name}")
    
    except Exception as e:
        print(f"   ⚠️  Could not fix imports in {test_file.name}: {e}")

# Add methods to the class
CodeOrganizer.consolidate_tests = consolidate_tests
CodeOrganizer.fix_test_imports = fix_test_imports

# Test consolidation
print("🧪 Testing test consolidation:")

organizer.consolidate_tests()

print(f"\n📁 Test files after consolidation: {list(tests_dir.glob('test_*.py'))}")

# Test import fixing
test_file = tests_dir / "test_generate_time_grid.py"
if test_file.exists():
    content = test_file.read_text()
    print(f"\n📄 Test file content: {content}")

# %%
# Cell 7: Module Structure Creation
"""
Lines 253-308: Module initialization file creation

These methods create __init__.py files for modules and the main package,
enabling proper Python package structure and imports.
"""

def create_module_init_files(self) -> None:
    """
    Lines 253-279: Create __init__.py files for all modules
    
    Creates __init__.py files that import all functions from each module,
    making them available when the module is imported.
    """
    for category in ['core', 'export', 'generate', 'utils']:
        category_dir = self.src_dir / category
        if category_dir.exists():
            self.ensure_dir(category_dir)
            
            # Create __init__.py with imports for all Python files
            init_file = category_dir / "__init__.py"
            py_files = [f for f in category_dir.glob("*.py") if f.name != "__init__.py"]
            
            if py_files:
                imports = []
                for py_file in py_files:
                    module_name = py_file.stem
                    imports.append(f"from .{module_name} import *")
                
                content = "\n".join(imports) + "\n"
                init_file.write_text(content)
                
                self.log_entries.append({
                    "action": "create_init",
                    "file": f"{category}/__init__.py",
                    "path": str(init_file),
                    "timestamp": self.timestamp
                })

def create_main_init_file(self) -> None:
    """
    Lines 280-307: Create main __init__.py file for src directory
    
    Creates the main package __init__.py that imports from all modules,
    making the entire package functionality available.
    """
    init_file = self.src_dir / "__init__.py"
    if not init_file.exists():
        init_content = '''"""
Main package for organized codebase.
"""

from .core import *
from .export import *
from .generate import *

try:
    from .utils import *
except ImportError:
    pass  # utils module is optional

__all__ = ["core", "export", "generate"]
'''
        init_file.write_text(init_content)
        
        self.log_entries.append({
            "action": "create_init",
            "file": "__init__.py",
            "path": str(init_file),
            "timestamp": self.timestamp
        })

# Add methods to the class
CodeOrganizer.create_module_init_files = create_module_init_files
CodeOrganizer.create_main_init_file = create_main_init_file

# Test module creation
print("🧪 Testing module structure creation:")

organizer.create_module_init_files()
organizer.create_main_init_file()

print("\n📁 Module __init__.py files:")
for category_dir in src_dir.iterdir():
    if category_dir.is_dir():
        init_file = category_dir / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            print(f"\n📄 {category_dir.name}/__init__.py:")
            print(f"   {content.strip()}")

# Test main init file
main_init = src_dir / "__init__.py"
if main_init.exists():
    content = main_init.read_text()
    print(f"\n📄 Main __init__.py:")
    print(f"   {content[:100]}...")

# %%
# Cell 8: Complete Organization Workflow and Validation
"""
Lines 595-682: Complete organization workflow and validation

The main run() method orchestrates the entire organization process
and includes validation to ensure success.
"""

def run_validation(self) -> bool:
    """
    Lines 550-594: Run basic validation to ensure organization was successful
    
    Validates:
    - src directory exists
    - subdirectories have __init__.py files
    - tests directory exists
    - counts test files
    """
    print("🔍 Running validation...")
    
    # Check that src directory exists and has subdirectories
    if not self.src_dir.exists():
        print("   ❌ src directory not found")
        return False
    
    # Check which subdirectories actually exist
    existing_subdirs = [d.name for d in self.src_dir.iterdir() if d.is_dir()]
    
    # At minimum, we should have some directories
    if not existing_subdirs:
        print("   ❌ No subdirectories found in src/")
        return False
    
    # Check that existing directories have __init__.py files
    for subdir in existing_subdirs:
        subdir_path = self.src_dir / subdir
        if not (subdir_path / "__init__.py").exists():
            print(f"   ❌ src/{subdir}/__init__.py not found")
            return False
    
    # Check that tests directory exists
    if not self.tests_dir.exists():
        print("   ❌ tests directory not found")
        return False
    
    # Count test files (optional - don't fail if none exist)
    test_files = list(self.tests_dir.glob("test_*.py"))
    if test_files:
        print(f"   ✅ Found {len(test_files)} test files")
    else:
        print("   ℹ️  No test files found in tests/ (this is OK)")
    print("   ✅ Directory structure validation passed")
    return True

def save_organization_log(self) -> Path:
    """
    Lines 441-461: Save the organization log to reports directory
    
    Creates a JSON log of all organization actions for audit trail.
    """
    log_file = self.reports_dir / "organization_log.json"
    
    log_data = {
        "timestamp": self.timestamp,
        "total_actions": len(self.log_entries),
        "summary": {
            "files_moved": len([e for e in self.log_entries if e["action"] == "move_file"]),
            "tests_copied": len([e for e in self.log_entries if e["action"] == "copy_test"]),
            "directories_created": len([e for e in self.log_entries if e["action"] == "create_init"]),
            "modules_created": len([e for e in self.log_entries if e["action"] == "create_module"])
        },
        "actions": self.log_entries
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    return log_file

# Add methods to the class
CodeOrganizer.run_validation = run_validation
CodeOrganizer.save_organization_log = save_organization_log

# Test validation and logging
print("🧪 Testing validation and logging:")

validation_result = organizer.run_validation()
print(f"✅ Validation result: {validation_result}")

log_file = organizer.save_organization_log()
print(f"📄 Organization log saved: {log_file}")

# Read and display log summary
with open(log_file) as f:
    log_data = json.load(f)

print(f"\n📊 Organization Summary:")
print(f"   Total actions: {log_data['total_actions']}")
print(f"   Files moved: {log_data['summary']['files_moved']}")
print(f"   Tests copied: {log_data['summary']['tests_copied']}")
print(f"   Directories created: {log_data['summary']['directories_created']}")

print("\n🎉 Code Organization Module Testing Complete!")
print("\n📁 Final directory structure:")
for root, dirs, files in os.walk(temp_base):
    level = root.replace(str(temp_base), '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

print("\n🔍 Code Organizer Features Documented:")
print("   📁 Directory structure creation")
print("   🏷️  File categorization by keywords")
print("   📦 File movement and organization")
print("   🧪 Test consolidation and import fixing")
print("   📄 Module initialization file generation")
print("   🔍 Validation of organization results")
print("   📊 Comprehensive logging and audit trail")
print("   🏗️  Infrastructure separation capabilities")
print("   🔧 Import statement fixing")
print("   📋 Integration summary processing")
