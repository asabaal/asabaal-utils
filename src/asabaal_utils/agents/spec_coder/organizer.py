#!/usr/bin/env python3
"""
🗂 Code Organization & Consolidation System

This script consolidates and organizes the working codebase into a clean, 
modular architecture after all test suites are passing.

Usage:
    python scripts/organize_codebase.py
"""

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

class CodeOrganizer:
    """Organizes generated code into production-ready structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir if base_dir is not None else Path(__file__).resolve().parent
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
    
    def ensure_dir(self, path: Path) -> None:
        """Create directory and __init__.py file."""
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
        """Determine which category a file belongs to based on keywords."""
        filename_str = str(filename)
        filename_lower = filename_str.lower()
        
        for category, keywords in self.category_mapping.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        return "misc"  # Default category
    
    def load_integration_summary(self) -> Dict:
        """Load the latest integration summary."""
        summary_file = self.reports_dir / "latest_integration_summary.json"
        if not summary_file.exists():
            raise FileNotFoundError(f"Integration summary not found: {summary_file}")
        
        with open(summary_file) as f:
            return json.load(f)
    
    def extract_successful_functions(self, summary: Dict) -> List[Dict]:
        """Extract list of successful function results from integration summary."""
        test_results = summary.get("stages", {}).get("test_results", {})
        results = test_results.get("results", [])
        
        successful = []
        for result in results:
            if result.get("success", False):
                successful.append(result)
        
        return successful
    
    def move_generated_files(self) -> None:
        """Move generated Python files to appropriate src subdirectories."""
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
    
    def consolidate_tests(self) -> None:
        """Consolidate all test files into tests/ directory and fix imports."""
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
        
        # Don't clean up test environment directory yet - keep it for validation
        if self.test_env_dir.exists():
            print(f"   📁 Keeping test_env directory for validation")
    
    def copy_file_to_src(self, file_path: Path, target_dir: Path) -> bool:
        """Copy a file to the appropriate src subdirectory."""
        try:
            self.ensure_dir(target_dir)
            target_path = target_dir / file_path.name
            
            shutil.copy2(str(file_path), str(target_path))
            
            self.log_entries.append({
                "action": "copy_file",
                "file": file_path.name,
                "from": str(file_path),
                "to": str(target_path),
                "timestamp": self.timestamp
            })
            
            return True
        except Exception as e:
            print(f"Error copying {file_path.name}: {e}")
            return False
    
    def copy_test_to_tests(self, test_file: Path, tests_dir: Path) -> bool:
        """Copy test file to tests directory with proper naming."""
        try:
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            # Read the file content to find test function names
            content = test_file.read_text()
            
            # Look for test function names (simple regex for "def test_*():")
            import re
            test_functions = re.findall(r'def (test_\w+)\s*\(', content)
            
            if test_functions:
                # Use the first test function found for the filename
                target_name = f"{test_functions[0]}.py"
            else:
                # Fallback: use original filename with test_ prefix if needed
                func_name = test_file.stem
                if not func_name.startswith("test_"):
                    target_name = f"test_{func_name}.py"
                else:
                    target_name = test_file.name
            
            target_path = tests_dir / target_name
            
            shutil.copy2(str(test_file), str(target_path))
            
            self.log_entries.append({
                "action": "copy_test",
                "file": test_file.name,
                "from": str(test_file),
                "to": str(target_path),
                "timestamp": self.timestamp
            })
            
            return True
        except Exception as e:
            print(f"Error copying test file {test_file.name}: {e}")
            return False
    
    def organize_successful_functions(self, successful_functions: List[Dict]) -> None:
        """Organize successful functions into appropriate modules."""
        for func_info in successful_functions:
            func_name = func_info.get('function', '')
            if not func_name:
                continue
                
            # Look for the function file in generated_functions
            func_file = self.generated_dir / f"{func_name}.py"
            if func_file.exists():
                category = self.categorize_file(func_file)
                target_dir = self.src_dir / category
                
                if self.copy_file_to_src(func_file, target_dir):
                    print(f"   📄 {func_file.name} → {category}/")
                
                # Also copy the test file if it exists
                test_env_func_dir = self.test_env_dir / func_name
                if test_env_func_dir.exists():
                    test_files = list(test_env_func_dir.glob("test_*.py"))
                    for test_file in test_files:
                        self.copy_test_to_tests(test_file, self.tests_dir)
    
    def create_module_init_files(self) -> None:
        """Create __init__.py files for all modules."""
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
        """Create main __init__.py file for src directory."""
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
    
    def run_no_successful_functions(self) -> bool:
        """Run organizer with no successful functions."""
        print("🗂 Running organizer with no successful functions...")
        
        # Create base directories
        self.ensure_dir(self.src_dir)
        self.ensure_dir(self.tests_dir)
        
        # Create module structure
        self.create_module_init_files()
        self.create_main_init_file()
        
        # Save log
        log_file = self.save_organization_log()
        print(f"   Log saved to: {log_file}")
        
        return True
    
    def run_with_successful_functions(self, successful_functions: List[Dict]) -> bool:
        """Run organizer with successful functions."""
        print("🗂 Running organizer with successful functions...")
        
        # Create base directories
        self.ensure_dir(self.src_dir)
        self.ensure_dir(self.tests_dir)
        
        # Organize successful functions
        self.organize_successful_functions(successful_functions)
        
        # Create module structure
        self.create_module_init_files()
        self.create_main_init_file()
        
        # Save log
        log_file = self.save_organization_log()
        print(f"   Log saved to: {log_file}")
        
        return True
    
    def create_module_structure(self) -> None:
        """Create additional module structure and files."""
        print("🏗️  Creating module structure...")
        
        # Create core module files
        core_dir = self.src_dir / "core"
        self.ensure_dir(core_dir)
        
        # Create timegrid.py (consolidate time grid functions)
        timegrid_file = core_dir / "timegrid.py"
        if not timegrid_file.exists():
            timegrid_content = '''"""
Time grid generation and manipulation functions.

This module consolidates all time grid related functionality.
"""

from .generate_time_grid import generate_time_grid
from .generate_time_grid_negative_tempo import generate_time_grid_negative_tempo
from .generate_time_grid_zero_tempo import generate_time_grid_zero_tempo

__all__ = [
    "generate_time_grid",
    "generate_time_grid_negative_tempo", 
    "generate_time_grid_zero_tempo"
]
'''
            timegrid_file.write_text(timegrid_content)
            self.log_entries.append({
                "action": "create_module",
                "file": "timegrid.py",
                "path": str(timegrid_file),
                "timestamp": self.timestamp
            })
        
        # Create rhythm.py (consolidate accent pattern functions)
        rhythm_file = core_dir / "rhythm.py"
        if not rhythm_file.exists():
            rhythm_content = '''"""
Rhythm and accent pattern functions.

This module consolidates all rhythm and accent pattern functionality.
"""

from .apply_accent_pattern import apply_accent_pattern
from .apply_accent_pattern_pattern import apply_accent_pattern_pattern

__all__ = [
    "apply_accent_pattern",
    "apply_accent_pattern_pattern"
]
'''
            rhythm_file.write_text(rhythm_content)
            self.log_entries.append({
                "action": "create_module",
                "file": "rhythm.py", 
                "path": str(rhythm_file),
                "timestamp": self.timestamp
            })
        
        # Create export module files
        export_dir = self.src_dir / "export"
        self.ensure_dir(export_dir)
        
        midi_export_file = export_dir / "midi_export.py"
        if not midi_export_file.exists():
            midi_export_content = '''"""
MIDI export functionality.

This module consolidates all MIDI export functions.
"""

from .export_as_midi import export_as_midi
from .export_as_midi_accents import export_as_midi_accents
from .export_as_midi_outfile import export_as_midi_outfile
from .export_as_midi_time_grid import export_as_midi_time_grid

__all__ = [
    "export_as_midi",
    "export_as_midi_accents", 
    "export_as_midi_outfile",
    "export_as_midi_time_grid"
]
'''
            midi_export_file.write_text(midi_export_content)
            self.log_entries.append({
                "action": "create_module",
                "file": "midi_export.py",
                "path": str(midi_export_file),
                "timestamp": self.timestamp
            })
        
        print("   ✅ Module structure created")
    
    def save_organization_log(self) -> Path:
        """Save the organization log to reports directory."""
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
    
    def fix_test_imports(self, test_file: Path) -> None:
        """Fix import statements in test files to match new module structure."""
        try:
            with open(test_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Define import mappings based on file organization
            import_mappings = {
                # Core functions
                'from generate_time_grid import generate_time_grid': 'from src.core.generate_time_grid import generate_time_grid',
                'from apply_accent_pattern import apply_accent_pattern': 'from src.core.apply_accent_pattern import apply_accent_pattern',
                'from apply_accent_pattern_pattern import apply_accent_pattern_pattern': 'from src.core.apply_accent_pattern_pattern import apply_accent_pattern_pattern',
                'from generate_time_grid_negative_tempo import generate_time_grid_negative_tempo': 'from src.core.generate_time_grid_negative_tempo import generate_time_grid_negative_tempo',
                'from generate_time_grid_zero_tempo import generate_time_grid_zero_tempo': 'from src.core.generate_time_grid_zero_tempo import generate_time_grid_zero_tempo',
                
                # Export functions
                'from export_as_midi import export_as_midi': 'from src.export.export_as_midi import export_as_midi',
                'from export_as_midi_accents import export_as_midi_accents': 'from src.export.export_as_midi_accents import export_as_midi_accents',
                'from export_as_midi_outfile import export_as_midi_outfile': 'from src.export.export_as_midi_outfile import export_as_midi_outfile',
                'from export_as_midi_time_grid import export_as_midi_time_grid': 'from src.export.export_as_midi_time_grid import export_as_midi_time_grid',
                
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
    
    def separate_infrastructure(self) -> None:
        """Separate generator infrastructure from production modules."""
        print("🔧 Separating infrastructure from production modules...")
        
        # Create infrastructure directory
        infra_dir = self.base_dir / "infrastructure"
        infra_dir.mkdir(exist_ok=True)
        self.ensure_dir(infra_dir)
        
        # Infrastructure files to move
        infra_files = [
            "generator.py",
            "ollama_client.py", 
            "spec_parser.py",
            "templates.py",
            "analyze_tests.py",
            "parse_tests.py",
            "summarize_tests.py",
            "align_behaviors.py",
            "compare_behaviors.py",
            "analyze_all_runs.py",
            "update_report.py"
        ]
        
        for infra_file in infra_files:
            src_path = self.src_dir / infra_file
            if src_path.exists():
                dst_path = infra_dir / infra_file
                shutil.move(str(src_path), str(dst_path))
                
                self.log_entries.append({
                    "action": "move_infrastructure",
                    "file": infra_file,
                    "from": str(src_path),
                    "to": str(dst_path),
                    "timestamp": self.timestamp
                })
                print(f"   📁 {infra_file} → infrastructure/")
        
        print("   ✅ Infrastructure separated")
    
    def run_validation(self) -> bool:
        """Run basic validation to ensure organization was successful."""
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
        
        # utils is optional - only validate if it exists
        if "utils" in existing_subdirs:
            utils_path = self.src_dir / "utils"
            if not (utils_path / "__init__.py").exists():
                print(f"   ❌ src/utils/__init__.py not found")
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
    
    def run(self) -> bool:
        """Run the complete organization process."""
        print("🗂 Starting Code Organization & Consolidation")
        print("=" * 50)
        
        try:
            # Load integration summary to check for successful functions
            summary = None
            if self.reports_dir.exists():
                summary_file = self.reports_dir / "latest_integration_summary.json"
                if summary_file.exists():
                    summary = self.load_integration_summary()
            
            # Extract successful functions
            successful_functions = []
            if summary:
                successful_functions = self.extract_successful_functions(summary)
            
            # Handle case with no successful functions
            if not successful_functions:
                print("✅ No functions to organize - all tests failed!")
                # Still create basic structure
                self.ensure_dir(self.src_dir)
                self.ensure_dir(self.tests_dir)
                self.create_module_init_files()
                self.create_main_init_file()
                
                # Save organization log
                print("📄 Saving organization log...")
                log_file = self.save_organization_log()
                print(f"   Log saved to: {log_file}")
                
                return True
            
            # Create base directories
            print("📁 Creating base directories...")
            self.ensure_dir(self.src_dir)
            
            # Organize successful functions
            self.organize_successful_functions(successful_functions)
            
            # Move generated files
            self.move_generated_files()
            
            # Consolidate tests
            self.consolidate_tests()
            
            # Create module structure
            self.create_module_structure()
            
            # Create module init files and main init file
            self.create_module_init_files()
            self.create_main_init_file()
            
            # Separate infrastructure from production
            self.separate_infrastructure()
            
            # Save organization log
            print("📄 Saving organization log...")
            log_file = self.save_organization_log()
            print(f"   Log saved to: {log_file}")
            
            # Run validation
            validation_success = self.run_validation()
            
            # Summary
            print(f"\n📊 Organization Summary:")
            print(f"   Files moved: {len([e for e in self.log_entries if e['action'] == 'move_file'])}")
            print(f"   Tests copied: {len([e for e in self.log_entries if e['action'] == 'copy_test'])}")
            print(f"   Validation: {'✅' if validation_success else '❌'}")
            
            if validation_success:
                print(f"\n🎉 Codebase successfully organized!")
                print(f"📁 Source code: {self.src_dir}")
                print(f"🧪 Tests: {self.tests_dir}")
                print(f"\n💡 Next steps:")
                print(f"   pytest {self.tests_dir}/")
            else:
                print(f"\n⚠️  Organization completed with validation issues")
            
            return validation_success
            
        except Exception as e:
            print(f"❌ Organization failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    organizer = CodeOrganizer()
    success = organizer.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())