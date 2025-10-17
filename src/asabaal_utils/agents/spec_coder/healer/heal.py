#!/usr/bin/env python3
"""
Heal - Execute OLAMA repairs with guided prompts

This module orchestrates the self-healing process by:
1. Loading failure classifications
2. Creating repair plans using PatchPlanner
3. Executing OLAMA repairs with structured prompts
4. Validating repairs and updating functions
"""

import os
import sys
import yaml
import json
import subprocess
import tempfile
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Using subprocess for OLAMA for now
OllamaClient = None

@dataclass
class RepairResult:
    """Result of a repair attempt."""
    function_name: str
    failure_type: str
    attempt: int
    success: bool
    original_code: str
    repaired_code: Optional[str]
    error_message: Optional[str]
    confidence: float

class Healer:
    """Main healing orchestrator."""
    
    def __init__(self, healer_dir: Path, ollama_model: str = "qwen3-coder:latest"):
        self.healer_dir = healer_dir
        self.artifacts_dir = healer_dir / "artifacts"
        self.ollama_model = ollama_model
        
        # Import other healer modules
        from .classify_failures import FailureClassifier
        from .plan_patches import PatchPlanner
        from .enforce_signature import SignatureEnforcer
        
        self.classifier = FailureClassifier(str(healer_dir))
        self.planner = PatchPlanner(healer_dir)
        self.enforcer = SignatureEnforcer(healer_dir)
        
        # Initialize OLAMA client - using subprocess for now
        self.ollama = None
    
    def load_failure_classifications(self) -> Dict:
        """Load failure classifications from artifacts."""
        classification_file = self.artifacts_dir / "failure_classifications.yaml"
        
        if not classification_file.exists():
            raise FileNotFoundError(f"Failure classifications not found: {classification_file}")
        
        with open(classification_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return data
    
    def load_function_code(self, function_name: str) -> str:
        """Load the current code for a function."""
        # Try to find the function in generated_functions
        func_file = self.healer_dir.parent / "generated_functions" / f"{function_name}.py"
        
        if func_file.exists():
            with open(func_file, 'r') as f:
                return f.read()
        
        # Try in other common locations
        for search_dir in [
            self.healer_dir.parent / "output" / "scaffolds" / "src",
            self.healer_dir.parent / "corrected_output" / "scaffolds" / "src"
        ]:
            potential_file = search_dir / f"{function_name}.py"
            if potential_file.exists():
                with open(potential_file, 'r') as f:
                    return f.read()
        
        raise FileNotFoundError(f"Function file not found: {function_name}")
    
    def save_function_code(self, function_name: str, code: str) -> None:
        """Save the repaired function code."""
        # Save to generated_functions directory
        output_dir = self.healer_dir.parent / "generated_functions"
        output_dir.mkdir(exist_ok=True)
        
        func_file = output_dir / f"{function_name}.py"
        with open(func_file, 'w') as f:
            f.write(code)
        
        # Also save to test environment directory
        test_dir = self.healer_dir.parent / "reports" / "test_env" / function_name
        if test_dir.exists():
            test_func_file = test_dir / f"{function_name}.py"
            with open(test_func_file, 'w') as f:
                f.write(code)
    
    def call_ollama_subprocess(self, prompt: str, timeout: int = 180) -> str:
        """Call OLAMA via API."""
        # Using subprocess instead of requests for now
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.ollama_model],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout
            )
            if result.returncode != 0:
                raise RuntimeError(f"OLAMA error: {result.stderr}")
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OLAMA timeout after {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"OLAMA API error: {e}")
    
    def call_ollama(self, prompt: str, timeout: int = 180) -> str:
        """Call OLAMA for repair."""
        if self.ollama:
            try:
                response = self.ollama.generate(prompt, timeout=timeout)
                return response.strip()
            except Exception as e:
                print(f"OLAMA client error, falling back to subprocess: {e}")
                return self.call_ollama_subprocess(prompt, timeout)
        else:
            return self.call_ollama_subprocess(prompt, timeout)
    
    def extract_python_code(self, response: str) -> Optional[str]:
        """Extract Python code from OLAMA response."""
        # Look for code blocks
        code_block_pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Look for any code with def statements
        def_pattern = r'(def\s+\w+\s*\([^)]*\)\s*->[^:]*:.*?)(?=\n\ndef|\n\n|\Z)'
        matches = re.findall(def_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no clear code blocks, try to extract everything that looks like Python
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            line = line.rstrip()
            if line.startswith('def ') or line.startswith('import ') or line.startswith('from '):
                in_code = True
            
            if in_code:
                code_lines.append(line)
                
                # Stop if we hit non-code content
                if line.strip() == '' and len(code_lines) > 1:
                    next_lines = [l.strip() for l in lines[lines.index(line) + 1:lines.index(line) + 3]]
                    if any(next_lines) and not any(l.startswith(('def ', '  ', '    ', '\t')) for l in next_lines):
                        break
        
        if code_lines:
            return '\n'.join(code_lines)
        
        return None
    
    def validate_repair(self, original_code: str, repaired_code: str, 
                       max_changes: int = 20) -> Tuple[bool, str]:
        """Validate that the repair is reasonable."""
        if not repaired_code:
            return False, "No code returned"
        
        # Check for syntax errors
        try:
            compile(repaired_code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # Check that changes are reasonable (relaxed for iterative healing)
        original_lines = original_code.split('\n')
        repaired_lines = repaired_code.split('\n')
        
        # More lenient line change check
        line_diff = abs(len(original_lines) - len(repaired_lines))
        if line_diff > max_changes * 2:  # Allow 2x more line changes
            return False, f"Too many line changes: {len(original_lines)} -> {len(repaired_lines)} (diff: {line_diff})"
        
        # Check that function name is preserved
        original_func_name = None
        for line in original_lines:
            if line.strip().startswith('def '):
                original_func_name = line.strip().split('(')[0].replace('def ', '')
                break
        
        if original_func_name:
            repaired_func_name = None
            for line in repaired_lines:
                if line.strip().startswith('def '):
                    repaired_func_name = line.strip().split('(')[0].replace('def ', '')
                    break
            
            if original_func_name != repaired_func_name:
                return False, f"Function name changed: {original_func_name} -> {repaired_func_name}"
        
        return True, "Valid repair"
    
    def repair_function(self, function_name: str, failure_type: str, 
                       error_details: str, expected_signature: Optional[str] = None,
                       max_attempts: int = 3) -> RepairResult:
        """Repair a single function."""
        
        print(f"Repairing {function_name} ({failure_type})...")
        
        # Load original code
        try:
            original_code = self.load_function_code(function_name)
        except FileNotFoundError as e:
            return RepairResult(
                function_name=function_name,
                failure_type=failure_type,
                attempt=0,
                success=False,
                original_code="",
                repaired_code=None,
                error_message=str(e),
                confidence=0.0
            )
        
        # Apply signature enforcement if needed
        if failure_type == "signature_mismatch" and expected_signature:
            try:
                enforced_code = self.enforcer.enforce_signature(original_code, expected_signature)
                if enforced_code != original_code:
                    print(f"  Applied signature enforcement for {function_name}")
                    original_code = enforced_code
            except Exception as e:
                print(f"  Signature enforcement failed: {e}")
        
        # Create repair plan
        try:
            repair_plan = self.planner.create_repair_plan(
                function_name=function_name,
                failure_type=failure_type,
                function_code=original_code,
                error_details=error_details,
                expected_signature=expected_signature
            )
        except Exception as e:
            return RepairResult(
                function_name=function_name,
                failure_type=failure_type,
                attempt=0,
                success=False,
                original_code=original_code,
                repaired_code=None,
                error_message=f"Failed to create repair plan: {e}",
                confidence=0.0
            )
        
        # Attempt repairs
        last_error = None
        for attempt in range(1, max_attempts + 1):
            print(f"  Attempt {attempt}/{max_attempts}...")
            
            try:
                # Call OLAMA
                response = self.call_ollama(repair_plan["prompt"])
                
                # Extract code
                repaired_code = self.extract_python_code(response)
                
                if not repaired_code:
                    last_error = "No code extracted from response"
                    continue
                
                # Apply signature enforcement if needed
                if failure_type == "signature_mismatch":
                    try:
                        repaired_code = self.enforcer.enforce_signature(repaired_code, function_name)
                        print(f"    Applied signature enforcement for {function_name}")
                    except Exception as e:
                        print(f"    Signature enforcement failed: {e}")
                
                # Validate repair
                is_valid, validation_msg = self.validate_repair(
                    original_code, repaired_code, repair_plan["allowed_changes"]
                )
                
                if not is_valid:
                    last_error = validation_msg
                    print(f"    Invalid repair: {validation_msg}")
                    continue
                
                # Save repaired code
                self.save_function_code(function_name, repaired_code)
                
                print(f"  ✓ Successfully repaired {function_name}")
                return RepairResult(
                    function_name=function_name,
                    failure_type=failure_type,
                    attempt=attempt,
                    success=True,
                    original_code=original_code,
                    repaired_code=repaired_code,
                    error_message=None,
                    confidence=0.8  # TODO: Calculate actual confidence
                )
                
            except Exception as e:
                last_error = str(e)
                print(f"    Attempt failed: {e}")
                continue
        
        # All attempts failed
        return RepairResult(
            function_name=function_name,
            failure_type=failure_type,
            attempt=max_attempts,
            success=False,
            original_code=original_code,
            repaired_code=None,
            error_message=f"All attempts failed. Last error: {last_error}",
            confidence=0.0
        )
    
    def heal_all_functions(self) -> List[RepairResult]:
        """Heal all functions with failures."""
        # Load failure classifications
        classifications = self.load_failure_classifications()
        
        results = []
        
        for function_name, failure_info in classifications.items():
            if failure_info.get("status") == "passed":
                print(f"Skipping {function_name} - already passing")
                continue
            
            failure_type = failure_info.get("failure_type", "unknown")
            error_details = failure_info.get("error_details", "No error details")
            expected_signature = failure_info.get("expected_signature")
            
            # Repair the function
            result = self.repair_function(
                function_name=function_name,
                failure_type=failure_type,
                error_details=error_details,
                expected_signature=expected_signature
            )
            
            results.append(result)
        
        return results
    
    def save_healing_results(self, results: List[RepairResult]) -> None:
        """Save healing results to artifacts."""
        results_data = {
            "healing_results": [
                {
                    "function_name": r.function_name,
                    "failure_type": r.failure_type,
                    "attempt": r.attempt,
                    "success": r.success,
                    "error_message": r.error_message,
                    "confidence": r.confidence
                }
                for r in results
            ],
            "summary": {
                "total_functions": len(results),
                "successful_repairs": sum(1 for r in results if r.success),
                "failed_repairs": sum(1 for r in results if not r.success),
                "success_rate": sum(1 for r in results if r.success) / len(results) if results else 0
            }
        }
        
        results_file = self.artifacts_dir / "healing_results.yaml"
        with open(results_file, 'w') as f:
            yaml.dump(results_data, f, default_flow_style=False, indent=2)
        
        print(f"\nHealing Results:")
        print(f"  Total functions: {results_data['summary']['total_functions']}")
        print(f"  Successful repairs: {results_data['summary']['successful_repairs']}")
        print(f"  Failed repairs: {results_data['summary']['failed_repairs']}")
        print(f"  Success rate: {results_data['summary']['success_rate']:.1%}")
        print(f"  Results saved to: {results_file}")

def main():
    """Main healing function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Heal failing functions")
    parser.add_argument("--model", default="qwen3-coder:latest", help="OLAMA model to use")
    parser.add_argument("--function", help="Repair specific function only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    healer_dir = Path(__file__).parent
    healer = Healer(healer_dir, ollama_model=args.model)
    
    if args.function:
        # Repair specific function
        classifications = healer.load_failure_classifications()
        if args.function not in classifications:
            print(f"Function {args.function} not found in classifications")
            return
        
        failure_info = classifications[args.function]
        result = healer.repair_function(
            function_name=args.function,
            failure_type=failure_info.get("failure_type", "unknown"),
            error_details=failure_info.get("error_details", "No error details"),
            expected_signature=failure_info.get("expected_signature")
        )
        
        print(f"\nRepair result for {args.function}:")
        print(f"  Success: {result.success}")
        if result.error_message:
            print(f"  Error: {result.error_message}")
        
    else:
        # Heal all functions
        results = healer.heal_all_functions()
        healer.save_healing_results(results)

if __name__ == "__main__":
    main()