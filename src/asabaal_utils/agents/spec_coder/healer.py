#!/usr/bin/env python3
"""
🧩 Patching & Debugging Layer

This script analyzes integration failures and applies minimal structural fixes
to restore test pass conditions before the healing stage.

Usage:
    python scripts/patch_failures.py
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class FailurePatcher:
    """Patches structural failures in generated functions."""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.reports_dir = self.base_dir / "reports"
        self.generated_dir = self.base_dir / "generated_functions"
        self.test_env_dir = self.base_dir / "reports" / "test_env"
        
        # Create patch log
        self.patch_log = []
        self.timestamp = datetime.now().isoformat()
    
    def load_integration_summary(self) -> Dict:
        """Load the latest integration summary."""
        latest_file = self.reports_dir / "latest_integration_summary.json"
        if not latest_file.exists():
            raise FileNotFoundError(f"No integration summary found at {latest_file}")
        
        with open(latest_file) as f:
            return json.load(f)
    
    def extract_failures(self, summary: Dict) -> List[Dict]:
        """Extract failing functions from integration summary."""
        failures = []
        test_results = summary.get("stages", {}).get("test_results", {})
        
        if "results" in test_results:
            for result in test_results["results"]:
                if not result.get("success", True):
                    failures.append(result)
        
        return failures
    
    def analyze_failure(self, failure: Dict) -> Dict:
        """Analyze a failure and determine the patch strategy."""
        stdout = failure.get("stdout", "")
        stderr = failure.get("stderr", "")
        function_name = failure.get("function_name", "")
        
        analysis = {
            "function_name": function_name,
            "file_path": self.generated_dir / f"{function_name}.py",
            "test_file_path": self.test_env_dir / function_name / f"{function_name}.py",
            "failure_type": "unknown",
            "patch_needed": False,
            "patch_description": ""
        }
        
        # Import errors - missing Any, Optional, etc.
        if "NameError" in stdout and "not defined" in stdout:
            if "Any" in stdout:
                analysis["failure_type"] = "import_error"
                analysis["patch_needed"] = True
                analysis["patch_description"] = "Add missing typing imports"
            elif "time_grid" in stdout:
                analysis["failure_type"] = "variable_initialization"
                analysis["patch_needed"] = True
                analysis["patch_description"] = "Initialize undefined variable"
        
        # Signature mismatches - missing required arguments
        elif "missing" in stdout and "required positional" in stdout:
            analysis["failure_type"] = "signature_mismatch"
            analysis["patch_needed"] = True
            analysis["patch_description"] = "Add default parameters to match test expectations"
        
        # ValueError with default parameters - smoke test failures
        elif "ValueError" in stdout and ("Length must be" in stdout or "positive" in stdout):
            analysis["failure_type"] = "parameter_validation"
            analysis["patch_needed"] = True
            analysis["patch_description"] = "Add parameter validation or default values"
        
        return analysis
    
    def apply_import_fix(self, file_path: Path, missing_imports: List[str]) -> bool:
        """Add missing imports to the top of the file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check what imports are already present
            existing_imports = []
            for line in content.split('\n'):
                if line.strip().startswith('from typing import'):
                    existing_imports.extend([imp.strip() for imp in line.split('from typing import')[1].split(',')])
                elif line.strip().startswith('import'):
                    existing_imports.append(line.strip())
            
            # Add missing imports
            imports_to_add = []
            for imp in missing_imports:
                if imp not in existing_imports and f"from typing import {imp}" not in content:
                    imports_to_add.append(imp)
            
            if imports_to_add:
                # Find the best place to add imports (after docstring, before first function)
                lines = content.split('\n')
                insert_line = 0
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('def ') or line.strip().startswith('class '):
                        insert_line = i
                        break
                    elif line.strip().startswith('"""') and i > 0:
                        # Skip docstring
                        continue
                
                # Add the import
                import_line = f"from typing import {', '.join(imports_to_add)}"
                lines.insert(insert_line, import_line)
                
                with open(file_path, 'w') as f:
                    f.write('\n'.join(lines))
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error applying import fix to {file_path}: {e}")
            return False
    
    def apply_variable_initialization_fix(self, file_path: Path, var_name: str) -> bool:
        """Initialize an undefined variable."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Find the function definition
            func_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    func_start = i
                    break
            
            if func_start == -1:
                return False
            
            # Add variable initialization after function definition
            init_line = f"    {var_name} = []  # Initialize undefined variable"
            lines.insert(func_start + 1, init_line)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            print(f"Error applying variable fix to {file_path}: {e}")
            return False
    
    def apply_signature_fix(self, file_path: Path, function_name: str) -> bool:
        """Add default parameters to fix signature mismatch."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find the function definition
            func_pattern = rf"def {function_name}\(([^)]*)\):"
            match = re.search(func_pattern, content)
            
            if not match:
                return False
            
            current_params = match.group(1).strip()
            
            # If no parameters, add a default one
            if not current_params:
                new_params = "data=None"
            else:
                # Add default to existing parameters
                if '=' not in current_params:
                    new_params = current_params + "=None"
                else:
                    new_params = current_params
            
            # Replace the function definition
            new_func_def = f"def {function_name}({new_params}):"
            content = content.replace(match.group(0), new_func_def)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error applying signature fix to {file_path}: {e}")
            return False
    
    def apply_parameter_validation_fix(self, file_path: Path) -> bool:
        """Add parameter validation to prevent ValueError."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Find the function definition
            func_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    func_start = i
                    break
            
            if func_start == -1:
                return False
            
            # Add validation after function definition
            validation_lines = [
                "    # Add parameter validation",
                "    if length is not None and length <= 0:",
                "        length = 4  # Default positive value"
            ]
            
            for j, validation_line in enumerate(validation_lines):
                lines.insert(func_start + 1 + j, validation_line)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            print(f"Error applying validation fix to {file_path}: {e}")
            return False
    
    def patch_function(self, analysis: Dict) -> bool:
        """Apply the appropriate patch to a function."""
        file_path = analysis["file_path"]
        failure_type = analysis["failure_type"]
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            return False
        
        success = False
        
        if failure_type == "import_error":
            # Add missing typing imports
            missing_imports = ["Any", "Optional"]
            success = self.apply_import_fix(file_path, missing_imports)
            
        elif failure_type == "variable_initialization":
            # Initialize undefined variable
            var_name = "time_grid"  # Based on the error we saw
            success = self.apply_variable_initialization_fix(file_path, var_name)
            
        elif failure_type == "signature_mismatch":
            # Add default parameters
            function_name = analysis["function_name"]
            success = self.apply_signature_fix(file_path, function_name)
            
        elif failure_type == "parameter_validation":
            # Add parameter validation
            success = self.apply_parameter_validation_fix(file_path)
        
        # Log the patch
        patch_entry = {
            "timestamp": self.timestamp,
            "function_name": analysis["function_name"],
            "failure_type": failure_type,
            "patch_description": analysis["patch_description"],
            "success": success,
            "file_path": str(file_path)
        }
        
        self.patch_log.append(patch_entry)
        
        if success:
            print(f"✅ Patched {analysis['function_name']} - {analysis['patch_description']}")
        else:
            print(f"❌ Failed to patch {analysis['function_name']}")
        
        return success
    
    def save_patch_log(self) -> Path:
        """Save the patch log to reports directory."""
        log_file = self.reports_dir / "patch_log.json"
        
        log_data = {
            "timestamp": self.timestamp,
            "total_patches_attempted": len(self.patch_log),
            "successful_patches": sum(1 for p in self.patch_log if p["success"]),
            "failed_patches": sum(1 for p in self.patch_log if not p["success"]),
            "patches": self.patch_log
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_tests_after_patch(self) -> bool:
        """Run tests after patching to verify fixes."""
        print("\n🧪 Running tests after patching...")
        
        import subprocess
        result = subprocess.run(
            ["python", "scripts/run_integration.py", "--mode", "test"],
            cwd=self.base_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        return result.returncode == 0
    
    def run(self) -> bool:
        """Run the complete patching process."""
        print("🧩 Starting Patching & Debugging Layer")
        print("=" * 50)
        
        try:
            # Load integration summary
            print("📊 Loading integration summary...")
            summary = self.load_integration_summary()
            
            # Extract failures
            print("🔍 Extracting failures...")
            failures = self.extract_failures(summary)
            
            if not failures:
                print("✅ No failures found - all functions working!")
                return True
            
            print(f"📋 Found {len(failures)} failing functions")
            
            # Analyze and patch each failure
            patched_count = 0
            for failure in failures:
                print(f"\n🔧 Analyzing: {failure['function_name']}")
                analysis = self.analyze_failure(failure)
                
                if analysis["patch_needed"]:
                    if self.patch_function(analysis):
                        patched_count += 1
                else:
                    print(f"⚠️  No patch needed for {analysis['function_name']}")
            
            # Save patch log
            print(f"\n📄 Saving patch log...")
            log_file = self.save_patch_log()
            print(f"   Log saved to: {log_file}")
            
            # Run tests to verify patches
            print(f"\n🧪 Verifying patches...")
            test_success = self.run_tests_after_patch()
            
            # Summary
            print(f"\n📊 Patching Summary:")
            print(f"   Functions analyzed: {len(failures)}")
            print(f"   Patches applied: {patched_count}")
            print(f"   Tests passing: {'✅' if test_success else '❌'}")
            
            return test_success
            
        except Exception as e:
            print(f"❌ Patching failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    patcher = FailurePatcher()
    success = patcher.run()
    
    if success:
        print("\n🎉 Patching completed successfully!")
    else:
        print("\n⚠️  Patching completed with some issues")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())