#!/usr/bin/env python3
"""
Failure Classifier - Extracts and labels failures from test reports
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

class FailureClassifier:
    """Classifies test failures into specific categories for targeted repair."""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
    
    def load_test_results(self) -> Dict:
        """Load the latest test results."""
        # First try the latest file
        test_results_path = self.reports_dir / "latest_test_results.json"
        
        if test_results_path.exists():
            with open(test_results_path, 'r') as f:
                return json.load(f)
        
        # If not found, look for the most recent test_results_*.json file
        import glob
        test_files = list(self.reports_dir.glob("test_results_*.json"))
        
        if not test_files:
            raise FileNotFoundError(f"No test results found in {self.reports_dir}")
        
        # Get the most recent file
        latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            return json.load(f)
    
    def classify_failure(self, stdout: str, stderr: str, function_name: str) -> str:
        """Classify a specific function's test failure."""
        # Combine stdout and stderr for analysis
        output = f"{stdout} {stderr}"
        
        # NameError during import/collection - missing imports like 'Any'
        if "NameError" in output and "not defined" in output and "collecting" in output:
            return "import_error"
        
        # Signature mismatch detection - missing required arguments
        if ("missing" in output and "required positional" in output) or \
           ("takes" in output and "positional argument" in output) or \
           ("unexpected keyword argument" in output):
            return "signature_mismatch"
        
        # Smoke test failures - look for basic_execution test failures with any exception
        basic_execution_pattern = f"test_{function_name}_basic_execution"
        if basic_execution_pattern in output and "FAILED" in output:
            # Check if it's a signature issue (missing arguments)
            if "missing" in output and "required positional" in output:
                return "signature_mismatch"
            # Otherwise, it's a smoke test failure (function throws with defaults)
            return "throws_on_smoke"
        
        # Import errors
        if "ImportError" in output or "ModuleNotFoundError" in output:
            return "import_error"
        
        # Syntax errors
        if "SyntaxError" in output or "IndentationError" in output:
            return "syntax_error"
        
        # NameError during execution (undefined variables)
        if "NameError" in output and "not defined" in output:
            return "logic_mismatch"
        
        # ValueError during execution
        if "ValueError" in output:
            return "throws_on_smoke"
        
        # Type errors (that aren't signature issues)
        if "TypeError" in output and "missing" not in output:
            return "type_error"
        
        # Default to logic mismatch for assertion failures and other issues
        if "AssertionError" in output or "assert" in output:
            return "logic_mismatch"
        
        # If no specific pattern detected, classify as logic_mismatch
        return "logic_mismatch"
    
    def classify_all_failures(self) -> List[Dict]:
        """Classify all failed functions from the test results."""
        test_results = self.load_test_results()
        classified_failures = []
        
        for result in test_results.get("results", []):
            if not result.get("success", True):
                classification = self.classify_failure(
                    result.get("stdout", ""),
                    result.get("stderr", ""),
                    result.get("function_name", "")
                )
                
                classified_failures.append({
                    "function_name": result.get("function_name"),
                    "classification": classification,
                    "returncode": result.get("returncode"),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "test_dir": result.get("test_dir")
                })
        
        return classified_failures
    
    def save_classification_report(self, failures: List[Dict]) -> str:
        """Save the classification report."""
        report = {
            "metadata": {
                "timestamp": json.dumps({"$date": {"$numberLong": str(int(Path().resolve().stat().st_mtime * 1000))}}),
                "total_failures": len(failures)
            },
            "failures": failures
        }
        
        # Create artifacts directory
        artifacts_dir = Path("healer/artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # Save with timestamp
        import time
        timestamp = int(time.time())
        report_path = artifacts_dir / f"classification_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save as latest
        latest_path = artifacts_dir / "latest_classification_report.json"
        with open(latest_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_path)


def main():
    """Main classification process."""
    classifier = FailureClassifier()
    
    try:
        failures = classifier.classify_all_failures()
        
        if not failures:
            print("✅ No failures to classify!")
            return
        
        print(f"🔍 Classifying {len(failures)} failures...")
        
        for failure in failures:
            print(f"  {failure['function_name']}: {failure['classification']}")
        
        report_path = classifier.save_classification_report(failures)
        print(f"📄 Classification report saved: {report_path}")
        
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())