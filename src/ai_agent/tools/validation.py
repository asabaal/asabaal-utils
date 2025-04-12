"""
Code validation and testing tools for the AI Agent Framework.

This module provides tools for validating code quality and running tests
to verify the functionality of generated code.
"""

import os
import re
import json
import time
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from ..models.base import BaseModel


@dataclass
class ValidationResult:
    """Results of code validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    metrics: Dict[str, any]
    

@dataclass
class TestResult:
    """Results of running tests."""
    success: bool
    passing_tests: int
    failing_tests: int
    error_messages: List[str]
    execution_time: float
    output: str
    command: str


class CodeValidator:
    """Tool for validating code quality and correctness.
    
    This class provides methods for statically analyzing code and checking
    for common issues before execution.
    """
    
    def __init__(self, model: Optional[BaseModel] = None):
        """Initialize the code validator.
        
        Args:
            model: Optional model for AI-based validation
        """
        self.model = model
    
    async def validate_python(self, code: str, strictness_level: str = "medium") -> ValidationResult:
        """Validate Python code for quality and correctness.
        
        Args:
            code: Python code to validate
            strictness_level: Level of strictness for validation (low, medium, high)
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        suggestions = []
        metrics = {}
        
        # Basic syntax check
        syntax_valid, syntax_error = self._check_syntax(code, "python")
        if not syntax_valid:
            errors.append(f"Syntax error: {syntax_error}")
        
        # Check for common issues
        if "import " in code:
            missing_imports = self._check_imports(code)
            if missing_imports:
                for imp in missing_imports:
                    warnings.append(f"Potentially undefined import: {imp}")
        
        # Check for undefined variables
        undefined_vars = self._find_undefined_variables(code)
        if undefined_vars:
            for var in undefined_vars:
                warnings.append(f"Potentially undefined variable: {var}")
        
        # Use pylint if available
        pylint_result = self._run_pylint(code)
        if pylint_result:
            if "errors" in pylint_result:
                errors.extend(pylint_result["errors"])
            if "warnings" in pylint_result:
                warnings.extend(pylint_result["warnings"])
        
        # Use the model for additional checks if available and strictness is high
        if self.model and strictness_level == "high":
            ai_validations = await self._validate_with_model(code, "python")
            if ai_validations:
                if "errors" in ai_validations:
                    errors.extend(ai_validations["errors"])
                if "warnings" in ai_validations:
                    warnings.extend(ai_validations["warnings"])
                if "suggestions" in ai_validations:
                    suggestions.extend(ai_validations["suggestions"])
        
        # Calculate code metrics
        metrics = self._calculate_code_metrics(code)
        
        # Determine overall validity
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metrics=metrics
        )
    
    async def validate_javascript(self, code: str, strictness_level: str = "medium") -> ValidationResult:
        """Validate JavaScript code for quality and correctness.
        
        Args:
            code: JavaScript code to validate
            strictness_level: Level of strictness for validation (low, medium, high)
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        suggestions = []
        metrics = {}
        
        # Basic syntax check
        syntax_valid, syntax_error = self._check_syntax(code, "javascript")
        if not syntax_valid:
            errors.append(f"Syntax error: {syntax_error}")
        
        # Use ESLint if available
        eslint_result = self._run_eslint(code)
        if eslint_result:
            if "errors" in eslint_result:
                errors.extend(eslint_result["errors"])
            if "warnings" in eslint_result:
                warnings.extend(eslint_result["warnings"])
        
        # Use the model for additional checks if available and strictness is high
        if self.model and strictness_level == "high":
            ai_validations = await self._validate_with_model(code, "javascript")
            if ai_validations:
                if "errors" in ai_validations:
                    errors.extend(ai_validations["errors"])
                if "warnings" in ai_validations:
                    warnings.extend(ai_validations["warnings"])
                if "suggestions" in ai_validations:
                    suggestions.extend(ai_validations["suggestions"])
        
        # Calculate code metrics
        metrics = self._calculate_code_metrics(code)
        
        # Determine overall validity
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metrics=metrics
        )
    
    def _check_syntax(self, code: str, language: str) -> Tuple[bool, Optional[str]]:
        """Check the syntax of code without executing it.
        
        Args:
            code: Code to check
            language: Programming language of the code
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return True, None
            except SyntaxError as e:
                return False, str(e)
        
        elif language == "javascript":
            # For JS we need to use a proper parser like esprima or write to a temp file
            # and use Node.js to validate. For simplicity, we'll use a basic regex check.
            # This is not comprehensive and should be replaced with proper parsing.
            try:
                # Create a temp file and run node --check
                with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as temp:
                    temp.write(code.encode())
                    temp_path = temp.name
                
                try:
                    result = subprocess.run(
                        ["node", "--check", temp_path],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    os.unlink(temp_path)
                    
                    if result.returncode == 0:
                        return True, None
                    else:
                        return False, result.stderr.strip()
                except (subprocess.SubprocessError, FileNotFoundError) as e:
                    os.unlink(temp_path)
                    # Fallback to basic check if node is not available
                    # Check for common JS syntax errors
                    unmatched_braces = code.count("{") != code.count("}")
                    unmatched_parens = code.count("(") != code.count(")")
                    unmatched_brackets = code.count("[") != code.count("]")
                    
                    if unmatched_braces or unmatched_parens or unmatched_brackets:
                        return False, "Unmatched delimiters found"
                    
                    # This is a very basic check and not reliable
                    return True, None
            except Exception as e:
                return False, str(e)
        
        # Default fallback
        return True, None
    
    def _check_imports(self, code: str) -> List[str]:
        """Check for potentially undefined imports in Python code.
        
        Args:
            code: Python code to check
            
        Returns:
            List of potentially problematic imports
        """
        standard_libs = [
            "os", "sys", "re", "math", "time", "datetime", "json", "random",
            "collections", "itertools", "functools", "typing", "pathlib"
        ]
        common_third_party = [
            "numpy", "pandas", "requests", "flask", "django", "sqlalchemy",
            "tensorflow", "torch", "matplotlib", "pytest", "selenium"
        ]
        
        # Extract imports
        import_pattern = r"(?:from\s+([.\w]+)\s+import)|(?:import\s+([.\w, ]+))"
        matches = re.findall(import_pattern, code)
        
        potential_issues = []
        for match in matches:
            # from X import Y or import X
            module = match[0] or match[1]
            
            # Handle multiple imports (import os, sys, re)
            for m in module.split(","):
                m = m.strip().split(".")[0]  # Get the base module name
                if m and m not in standard_libs and m not in common_third_party:
                    if m not in code.lower():  # Heuristic to check if defined in the code
                        potential_issues.append(m)
        
        return potential_issues
    
    def _find_undefined_variables(self, code: str) -> List[str]:
        """Find potentially undefined variables in Python code.
        
        Args:
            code: Python code to check
            
        Returns:
            List of potentially undefined variables
        """
        # This is a simplistic implementation and will have false positives
        # A proper implementation would use the ast module to parse and analyze
        
        # Extract variable assignments
        assignment_pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)\s*="
        defined_vars = set(re.findall(assignment_pattern, code))
        
        # Common builtins and keywords to ignore
        builtins = {
            "True", "False", "None", "self", "cls", "print", "len", "range",
            "str", "int", "float", "list", "dict", "set", "tuple", "sum",
            "min", "max", "sorted", "enumerate", "zip", "map", "filter"
        }
        
        # Find variable usages (this is very simplistic)
        usage_pattern = r"[^.'\"a-zA-Z0-9_]([a-zA-Z_][a-zA-Z0-9_]*)[^a-zA-Z0-9_('\".]"
        all_usages = re.findall(usage_pattern, code)
        
        # Filter out defined variables and builtins
        undefined = [var for var in all_usages if var not in defined_vars and var not in builtins]
        
        # Remove duplicates
        return list(set(undefined))
    
    def _run_pylint(self, code: str) -> Optional[Dict]:
        """Run pylint on Python code if available.
        
        Args:
            code: Python code to check
            
        Returns:
            Dictionary with errors and warnings or None if pylint is not available
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp:
                temp.write(code.encode())
                temp_path = temp.name
            
            result = subprocess.run(
                ["pylint", "--output-format=json", temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            os.unlink(temp_path)
            
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    errors = [issue["message"] for issue in issues if issue["type"] == "error"]
                    warnings = [issue["message"] for issue in issues if issue["type"] == "warning"]
                    return {"errors": errors, "warnings": warnings}
                except json.JSONDecodeError:
                    return None
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
    
    def _run_eslint(self, code: str) -> Optional[Dict]:
        """Run eslint on JavaScript code if available.
        
        Args:
            code: JavaScript code to check
            
        Returns:
            Dictionary with errors and warnings or None if eslint is not available
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as temp:
                temp.write(code.encode())
                temp_path = temp.name
            
            result = subprocess.run(
                ["eslint", "--format=json", temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            os.unlink(temp_path)
            
            if result.stdout:
                try:
                    issues = json.loads(result.stdout)
                    if issues and len(issues) > 0:
                        messages = issues[0].get("messages", [])
                        errors = [msg["message"] for msg in messages if msg["severity"] == 2]
                        warnings = [msg["message"] for msg in messages if msg["severity"] == 1]
                        return {"errors": errors, "warnings": warnings}
                except json.JSONDecodeError:
                    return None
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
    
    async def _validate_with_model(self, code: str, language: str) -> Optional[Dict]:
        """Use an AI model to validate code.
        
        Args:
            code: Code to validate
            language: Programming language of the code
            
        Returns:
            Dictionary with errors, warnings, and suggestions
        """
        if not self.model:
            return None
        
        prompt = (
            f"Please analyze this {language} code for potential issues, bugs, and best practices:\n\n"
            f"```{language}\n{code}\n```\n\n"
            f"Provide a list of errors, warnings, and suggestions in the following JSON format:\n"
            f"{{\"errors\": [\"error1\", \"error2\"], \"warnings\": [\"warning1\"], \"suggestions\": [\"suggestion1\"]}}\n\n"
            f"Focus on identifying:\n"
            f"1. Logical errors and bugs\n"
            f"2. Edge cases that might not be handled\n"
            f"3. Performance issues\n"
            f"4. Security concerns\n"
            f"5. Best practice violations\n\n"
            f"Return ONLY the JSON with no additional text."
        )
        
        system_prompt = (
            f"You are an expert {language} code reviewer. Your task is to analyze code and identify "
            f"potential issues, focusing on correctness, security, and best practices. Be thorough "
            f"but avoid false positives. Provide output in the specified JSON format only."
        )
        
        try:
            response = await self.model.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
            )
            
            # Extract JSON from response
            json_match = re.search(r"({.*})", response.content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                    return result
                except json.JSONDecodeError:
                    return None
            return None
        except Exception as e:
            logging.warning(f"Error validating code with model: {e}")
            return None
    
    def _calculate_code_metrics(self, code: str) -> Dict[str, any]:
        """Calculate basic code metrics.
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary of code metrics
        """
        metrics = {}
        
        # Basic metrics
        lines = code.split("\n")
        metrics["total_lines"] = len(lines)
        
        # Non-blank lines
        non_blank_lines = [line for line in lines if line.strip()]
        metrics["non_blank_lines"] = len(non_blank_lines)
        
        # Comment lines (simple approximation)
        comment_lines = len([line for line in lines if line.strip().startswith(("#", "//", "/*"))])
        metrics["comment_lines"] = comment_lines
        
        # Function/method count (very approximate)
        function_count = len(re.findall(r"def\s+\w+\s*\(", code))  # Python
        function_count += len(re.findall(r"function\s+\w+\s*\(", code))  # JavaScript
        metrics["function_count"] = function_count
        
        # Cyclomatic complexity (extremely simplified approximation)
        decision_points = len(re.findall(r"\b(if|while|for|switch)\b", code))
        metrics["estimated_complexity"] = decision_points + 1
        
        return metrics


class TestRunner:
    """Tool for running tests to validate code functionality.
    
    This class provides methods for executing tests for various languages
    and frameworks.
    """
    
    def run_python_tests(
        self,
        code: str,
        test_code: str,
        setup_code: str = "",
        test_framework: str = "pytest",
        timeout: int = 30,
    ) -> TestResult:
        """Run Python tests on the provided code.
        
        Args:
            code: Code to test
            test_code: Test code to run
            setup_code: Optional setup code to run before tests
            test_framework: Test framework to use (pytest, unittest)
            timeout: Maximum execution time in seconds
            
        Returns:
            TestResult with test results
        """
        start_time = time.time()
        
        # Create temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to a module file
            module_path = os.path.join(temp_dir, "module_to_test.py")
            with open(module_path, "w") as f:
                f.write(code)
            
            # Write setup code if provided
            if setup_code:
                setup_path = os.path.join(temp_dir, "setup.py")
                with open(setup_path, "w") as f:
                    f.write(setup_code)
            
            # Write test code
            test_path = os.path.join(temp_dir, "test_module.py")
            with open(test_path, "w") as f:
                # Add import for the module
                test_content = f"from module_to_test import *\n\n{test_code}"
                f.write(test_content)
            
            # Prepare command based on test framework
            if test_framework == "pytest":
                command = ["pytest", "-v", test_path]
            elif test_framework == "unittest":
                command = ["python", "-m", "unittest", test_path]
            else:
                command = ["python", test_path]  # Simple execution
            
            try:
                # Execute the tests
                result = subprocess.run(
                    command,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                output = result.stdout + result.stderr
                
                # Parse test results
                success = result.returncode == 0
                
                # Extract passing/failing test counts
                if test_framework == "pytest":
                    passing_tests = output.count("PASSED")
                    failing_tests = output.count("FAILED")
                else:
                    # Simple approximation for unittest
                    passing_tests = output.count("ok")
                    failing_tests = output.count("FAIL") + output.count("ERROR")
                
                # Extract error messages
                error_messages = []
                if not success:
                    # Extract error messages (this is framework-specific and approximate)
                    error_lines = [line for line in output.split("\n") if "Error" in line or "FAILED" in line]
                    error_messages = error_lines
                
                execution_time = time.time() - start_time
                
                return TestResult(
                    success=success,
                    passing_tests=passing_tests,
                    failing_tests=failing_tests,
                    error_messages=error_messages,
                    execution_time=execution_time,
                    output=output,
                    command=" ".join(command)
                )
                
            except subprocess.TimeoutExpired:
                return TestResult(
                    success=False,
                    passing_tests=0,
                    failing_tests=1,
                    error_messages=["Test execution timed out"],
                    execution_time=timeout,
                    output="Execution timed out after {timeout} seconds",
                    command=" ".join(command)
                )
                
            except Exception as e:
                return TestResult(
                    success=False,
                    passing_tests=0,
                    failing_tests=1,
                    error_messages=[str(e)],
                    execution_time=time.time() - start_time,
                    output=str(e),
                    command=" ".join(command)
                )
    
    def run_javascript_tests(
        self,
        code: str,
        test_code: str,
        setup_code: str = "",
        test_framework: str = "jest",
        timeout: int = 30,
    ) -> TestResult:
        """Run JavaScript tests on the provided code.
        
        Args:
            code: Code to test
            test_code: Test code to run
            setup_code: Optional setup code to run before tests
            test_framework: Test framework to use (jest, mocha)
            timeout: Maximum execution time in seconds
            
        Returns:
            TestResult with test results
        """
        start_time = time.time()
        
        # Create temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to a module file
            module_path = os.path.join(temp_dir, "moduleToTest.js")
            with open(module_path, "w") as f:
                f.write(code)
            
            # Write setup code if provided
            if setup_code:
                setup_path = os.path.join(temp_dir, "setup.js")
                with open(setup_path, "w") as f:
                    f.write(setup_code)
            
            # Write test code
            test_path = os.path.join(temp_dir, "test.js")
            with open(test_path, "w") as f:
                # Add import for the module
                if "import " not in test_code and "require(" not in test_code:
                    test_content = f"const moduleToTest = require('./moduleToTest.js');\n\n{test_code}"
                else:
                    test_content = test_code
                f.write(test_content)
            
            # This is a simplified implementation that assumes the test frameworks are installed
            # In practice, you'd need to set up package.json, install dependencies, etc.
            
            # Simple node execution as fallback
            command = ["node", test_path]
            
            # Check if test framework binaries are available
            if test_framework == "jest":
                jest_path = self._find_executable("jest")
                if jest_path:
                    command = [jest_path, test_path]
            elif test_framework == "mocha":
                mocha_path = self._find_executable("mocha")
                if mocha_path:
                    command = [mocha_path, test_path]
            
            try:
                # Execute the tests
                result = subprocess.run(
                    command,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                output = result.stdout + result.stderr
                
                # Parse test results
                success = result.returncode == 0
                
                # Extract passing/failing test counts (very approximate)
                passing_tests = output.count("PASS") + output.count("✓")
                failing_tests = output.count("FAIL") + output.count("✗")
                
                # Extract error messages
                error_messages = []
                if not success:
                    # Extract error messages (this is framework-specific and approximate)
                    error_lines = [line for line in output.split("\n") if "Error" in line or "FAIL" in line]
                    error_messages = error_lines
                
                execution_time = time.time() - start_time
                
                return TestResult(
                    success=success,
                    passing_tests=passing_tests,
                    failing_tests=failing_tests,
                    error_messages=error_messages,
                    execution_time=execution_time,
                    output=output,
                    command=" ".join(command)
                )
                
            except subprocess.TimeoutExpired:
                return TestResult(
                    success=False,
                    passing_tests=0,
                    failing_tests=1,
                    error_messages=["Test execution timed out"],
                    execution_time=timeout,
                    output="Execution timed out after {timeout} seconds",
                    command=" ".join(command)
                )
                
            except Exception as e:
                return TestResult(
                    success=False,
                    passing_tests=0,
                    failing_tests=1,
                    error_messages=[str(e)],
                    execution_time=time.time() - start_time,
                    output=str(e),
                    command=" ".join(command)
                )
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Find the path to an executable.
        
        Args:
            name: Name of the executable to find
            
        Returns:
            Path to the executable or None if not found
        """
        if os.name == "nt":  # Windows
            path_ext = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            
            for path_dir in path_dirs:
                for ext in path_ext:
                    path = os.path.join(path_dir, name + ext)
                    if os.path.isfile(path):
                        return path
        else:  # Unix-like
            for path_dir in os.environ.get("PATH", "").split(os.pathsep):
                path = os.path.join(path_dir, name)
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
        
        # Check for node_modules/.bin
        node_bin = os.path.join(".", "node_modules", ".bin", name)
        if os.path.isfile(node_bin) and os.access(node_bin, os.X_OK):
            return node_bin
            
        return None
