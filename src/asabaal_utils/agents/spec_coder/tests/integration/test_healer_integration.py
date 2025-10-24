"""
Integration tests for Healer component with real AI model calls.

These tests make actual calls to Ollama models to validate the complete
healing workflow: failure classification → patch planning → AI repair → validation.

Run with: pytest tests/test_healer_integration.py -v

Requires:
- Ollama service running on localhost:11434
- Models: qwen3-coder:latest (or other available models)
- Test failure data and generated code artifacts
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
import time
import subprocess

from asabaal_utils.agents.spec_coder.healer import Healer, FailureClassifier, PatchPlanner, SignatureEnforcer
from asabaal_utils.agents.spec_coder.healer.heal import RepairResult


class TestHealerIntegration:
    """Integration tests for Healer with real AI calls."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def healer_setup(self, temp_dir):
        """Create a complete healer environment with test data."""
        # Create healer directory structure
        healer_dir = temp_dir / "healer"
        artifacts_dir = healer_dir / "artifacts"
        generated_functions_dir = temp_dir / "generated_functions"
        reports_dir = temp_dir / "reports"
        logic_catalog_dir = temp_dir / "logic_catalog"
        
        artifacts_dir.mkdir(parents=True)
        generated_functions_dir.mkdir(parents=True)
        reports_dir.mkdir(parents=True)
        logic_catalog_dir.mkdir(parents=True)
        
        # Create a minimal functional catalog
        functional_catalog = {
            'metadata': {
                'catalog_version': '1.0.0',
                'generated_at': '2025-10-16',
                'total_functions': 3,
                'categories': {
                    'arithmetic': ['add_function', 'divide_function'],
                    'utility': ['import_error_function']
                }
            },
            'functions': {
                'add_function': {
                    'category': 'arithmetic',
                    'signature': 'def add(a: float, b: float) -> float:',
                    'description': 'Add two numbers and return the result'
                },
                'divide_function': {
                    'category': 'arithmetic', 
                    'signature': 'def divide(a: float, b: float) -> float:',
                    'description': 'Divide a by b and handle division by zero'
                },
                'import_error_function': {
                    'category': 'utility',
                    'signature': 'def process_list(items: List[str]) -> List[str]:',
                    'description': 'Process a list of strings'
                }
            }
        }
        
        catalog_file = logic_catalog_dir / "functional_catalog.yaml"
        catalog_file.write_text(yaml.dump(functional_catalog))
        
        # Create sample failure classifications
        failure_classifications = {
            "add_function": {
                "status": "failed",
                "failure_type": "throws_on_smoke",
                "error_details": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
                "expected_signature": "def add(a: float, b: float) -> float:",
                "test_output": "Traceback (most recent call last):\n  File test_add.py, line 5, in test_add_basic\n    result = calc.add(2, 3)\nTypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"
            },
            "divide_function": {
                "status": "failed", 
                "failure_type": "signature_mismatch",
                "error_details": "TypeError: divide() missing 1 required positional argument: 'b'",
                "expected_signature": "def divide(a: float, b: float) -> float:",
                "test_output": "TypeError: divide() missing 1 required positional argument: 'b'"
            },
            "import_error_function": {
                "status": "failed",
                "failure_type": "import_error", 
                "error_details": "NameError: name 'List' is not defined",
                "expected_signature": "def process_list(items: List[str]) -> List[str]:",
                "test_output": "NameError: name 'List' is not defined"
            }
        }
        
        classification_file = artifacts_dir / "failure_classifications.yaml"
        classification_file.write_text(yaml.dump(failure_classifications))
        
        # Create sample broken function files
        broken_functions = {
            "add_function": '''
def add(a, b):
    """TODO RPG-001: Add two numbers and return the result."""
    pass  # Not implemented
''',
            "divide_function": '''
def divide(a):  # Missing parameter b
    """TODO RPG-001: Divide a by b and handle division by zero."""
    pass
''',
            "import_error_function": '''
def process_list(items):
    """TODO RPG-002: Process a list of strings."""
    # Missing import for List
    return [item.upper() for item in items]
'''
        }
        
        for func_name, code in broken_functions.items():
            func_file = generated_functions_dir / f"{func_name}.py"
            func_file.write_text(code)
        
        return {
            'healer_dir': healer_dir,
            'artifacts_dir': artifacts_dir,
            'generated_functions_dir': generated_functions_dir,
            'reports_dir': reports_dir,
            'failure_classifications': failure_classifications,
            'broken_functions': broken_functions
        }
    
    @pytest.mark.integration
    def test_real_ai_heal_single_function(self, healer_setup):
        """Test healing a single function with real AI."""
        
        healer = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="qwen3-coder:latest"
        )
        
        # Test healing the add_function
        result = healer.repair_function(
            function_name="add_function",
            failure_type="throws_on_smoke",
            error_details="TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
            expected_signature="def add(a: float, b: float) -> float:"
        )
        
        # Verify repair result
        assert isinstance(result, RepairResult)
        assert result.function_name == "add_function"
        assert result.failure_type == "throws_on_smoke"
        assert result.attempt >= 1
        assert len(result.original_code) > 0
        
        # Check if repair was attempted (may not always succeed)
        if result.success:
            assert result.repaired_code is not None
            assert len(result.repaired_code) > 50  # Should have substantial content
            assert "def add(" in result.repaired_code
            assert "return" in result.repaired_code
            print(f"✅ Successfully repaired {result.function_name}")
        else:
            print(f"⚠️  Repair failed for {result.function_name}: {result.error_message}")
        
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Attempt: {result.attempt}")
    
    @pytest.mark.integration
    def test_real_ai_heal_all_functions(self, healer_setup):
        """Test healing all functions with real AI."""
        # Integration test enabled
        
        healer = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="qwen3-coder:latest"
        )
        
        # Heal all functions
        start_time = time.time()
        results = healer.heal_all_functions()
        healing_time = time.time() - start_time
        
        # Verify results
        assert len(results) == 3  # Should have 3 functions to heal
        assert healing_time < 120  # Should complete within 2 minutes
        
        successful_repairs = sum(1 for r in results if r.success)
        print(f"✅ Healed {successful_repairs}/{len(results)} functions in {healing_time:.2f}s")
        
        # Check each result
        for result in results:
            assert isinstance(result, RepairResult)
            assert result.function_name in healer_setup['failure_classifications']
            
            if result.success:
                assert result.repaired_code is not None
                assert len(result.repaired_code) > 0
                print(f"   ✅ {result.function_name}: SUCCESS")
            else:
                print(f"   ❌ {result.function_name}: {result.error_message}")
    
    @pytest.mark.integration
    def test_real_ai_signature_enforcement(self, healer_setup):
        """Test signature enforcement with real AI."""
        # Integration test enabled
        
        enforcer = SignatureEnforcer(healer_setup['healer_dir'])
        
        # Test signature enforcement
        broken_code = "def divide(a):  # Missing parameter\n    pass"
        function_name = "divide"
        
        enforced_code = enforcer.enforce_signature(broken_code, function_name)
        
        # Verify signature was enforced
        assert enforced_code != broken_code
        assert "def divide(" in enforced_code
        assert "b:" in enforced_code
        
        print(f"✅ Signature enforcement applied")
        print(f"   Original: {broken_code[:50]}...")
        print(f"   Enforced: {enforced_code[:50]}...")
    
    @pytest.mark.integration
    def test_real_ai_failure_classification(self, healer_setup):
        """Test failure classification with real test outputs."""
        # Integration test enabled
        
        classifier = FailureClassifier(str(healer_setup['reports_dir']))
        
        # Create test results file
        test_results = {
            "summary": {
                "total": 3,
                "passed": 0,
                "failed": 3,
                "errors": 0
            },
            "tests": [
                {
                    "name": "test_add_basic",
                    "function": "add_function",
                    "status": "failed",
                    "stdout": "",
                    "stderr": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"
                },
                {
                    "name": "test_divide_basic", 
                    "function": "divide_function",
                    "status": "failed",
                    "stdout": "",
                    "stderr": "TypeError: divide() missing 1 required positional argument: 'b'"
                }
            ]
        }
        
        test_results_file = healer_setup['reports_dir'] / "latest_test_results.json"
        test_results_file.write_text(json.dumps(test_results, indent=2))
        
        # Test classification
        for test in test_results["tests"]:
            failure_type = classifier.classify_failure(
                test["stdout"], 
                test["stderr"], 
                test["function"]
            )
            
            assert failure_type in [
                "throws_on_smoke", "signature_mismatch", "import_error",
                "runtime_error", "assertion_error", "type_error", "unknown"
            ]
            
            print(f"✅ Classified {test['function']}: {failure_type}")
    
    @pytest.mark.integration
    def test_real_ai_patch_planning(self, healer_setup):
        """Test patch planning with real AI."""
        # Integration test enabled
        
        planner = PatchPlanner(healer_setup['healer_dir'])
        
        # Test creating repair plan for different failure types
        test_cases = [
            {
                "function_name": "add_function",
                "failure_type": "throws_on_smoke",
                "function_code": "def add(a, b):\n    pass",
                "error_details": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"
            },
            {
                "function_name": "divide_function", 
                "failure_type": "signature_mismatch",
                "function_code": "def divide(a):\n    pass",
                "error_details": "TypeError: divide() missing 1 required positional argument: 'b'"
            }
        ]
        
        for test_case in test_cases:
            repair_plan = planner.create_repair_plan(**test_case)
            
            assert "prompt" in repair_plan
            assert "allowed_changes" in repair_plan
            assert len(repair_plan["prompt"]) > 100
            assert test_case["function_name"] in repair_plan["prompt"]
            assert test_case["error_details"] in repair_plan["prompt"]
            
            print(f"✅ Created repair plan for {test_case['function_name']}")
            print(f"   Strategy: {repair_plan.get('strategy', 'unknown')}")
            print(f"   Allowed changes: {repair_plan['allowed_changes']}")
    
    @pytest.mark.integration
    def test_real_ai_code_extraction(self, healer_setup):
        """Test Python code extraction from AI responses."""
        # Integration test enabled
        
        healer = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="qwen3-coder:latest"
        )
        
        # Test responses with different code formats
        test_responses = [
            '''Here's the fixed function:

```python
def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b
```

This should work now.''',
            
            '''def divide(a: float, b: float) -> float:
    """Divide two numbers and handle division by zero."""
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b''',
            
            '''The function needs to be implemented. Here you go:

def process_list(items: List[str]) -> List[str]:
    """Process a list of strings."""
    return [item.upper() for item in items]

This should fix the issue.'''
        ]
        
        for i, response in enumerate(test_responses):
            extracted_code = healer.extract_python_code(response)
            
            assert extracted_code is not None
            assert "def " in extracted_code
            assert len(extracted_code) > 20
            
            print(f"✅ Extracted code from response {i+1}")
            print(f"   Code: {extracted_code[:50]}...")
    
    @pytest.mark.integration
    def test_real_ai_healing_workflow(self, healer_setup):
        """Test complete healing workflow with real AI."""
        # Integration test enabled
        
        healer = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="qwen3-coder:latest"
        )
        
        # Run complete workflow
        start_time = time.time()
        results = healer.heal_all_functions()
        healing_time = time.time() - start_time
        
        # Save results
        healer.save_healing_results(results)
        
        # Verify results file was created
        results_file = healer_setup['artifacts_dir'] / "healing_results.yaml"
        assert results_file.exists()
        
        # Load and verify saved results
        with open(results_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert "healing_results" in saved_data
        assert "summary" in saved_data
        assert saved_data["summary"]["total_functions"] == len(results)
        
        # Print summary
        summary = saved_data["summary"]
        print(f"✅ Complete workflow finished in {healing_time:.2f}s")
        print(f"   Total functions: {summary['total_functions']}")
        print(f"   Successful repairs: {summary['successful_repairs']}")
        print(f"   Failed repairs: {summary['failed_repairs']}")
        print(f"   Success rate: {summary['success_rate']:.2%}")
    
    @pytest.mark.integration
    def test_real_ai_error_handling(self, healer_setup):
        """Test error handling in healing process."""
        # Integration test enabled
        
        healer = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="qwen3-coder:latest"
        )
        
        # Test with non-existent function
        result = healer.repair_function(
            function_name="non_existent_function",
            failure_type="throws_on_smoke",
            error_details="Test error"
        )
        
        assert not result.success
        assert result.error_message and "not found" in result.error_message.lower()
        
        # Test with invalid model (should fallback gracefully)
        healer_invalid = Healer(
            healer_dir=healer_setup['healer_dir'],
            ollama_model="non-existent-model:latest"
        )
        
        # This should handle the model error gracefully
        try:
            result = healer_invalid.repair_function(
                function_name="add_function",
                failure_type="throws_on_smoke",
                error_details="Test error"
            )
            # If it doesn't crash, that's good error handling
            print("✅ Invalid model handled gracefully")
        except Exception as e:
            # Should be a graceful error, not a crash
            assert "model" in str(e).lower() or "ollama" in str(e).lower()
            print(f"✅ Invalid model error handled: {e}")


class TestHealerComponentsIntegration:
    """Integration tests for individual healer components."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.integration
    def test_real_ai_classifier_integration(self, temp_dir):
        """Test FailureClassifier with real test data."""
        # Integration test enabled
        
        # Create realistic test failure data
        test_failures = [
            {
                "stdout": "",
                "stderr": "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
                "expected": "type_error"
            },
            {
                "stdout": "",
                "stderr": "TypeError: divide() missing 1 required positional argument: 'b'",
                "expected": "signature_mismatch"
            },
            {
                "stdout": "",
                "stderr": "NameError: name 'List' is not defined",
                "expected": "import_error"
            },
            {
                "stdout": "AssertionError: Expected 5 but got 3",
                "stderr": "",
                "expected": "assertion_error"
            }
        ]
        
        classifier = FailureClassifier(str(temp_dir))
        
        for i, failure in enumerate(test_failures):
            failure_type = classifier.classify_failure(
                failure["stdout"],
                failure["stderr"], 
                f"test_function_{i}"
            )
            
            assert failure_type == failure["expected"], f"Expected {failure['expected']}, got {failure_type}"
            print(f"✅ Correctly classified: {failure['expected']}")
    
    @pytest.mark.integration
    def test_real_ai_planner_strategies(self, temp_dir):
        """Test PatchPlanner strategies with real scenarios."""
        # Integration test enabled
        
        planner = PatchPlanner(temp_dir)
        
        # Test each strategy
        strategies_to_test = [
            "throws_on_smoke",
            "signature_mismatch", 
            "import_error",
            "assertion_error",
            "runtime_error"
        ]
        
        for strategy_name in strategies_to_test:
            if strategy_name in planner.strategies:
                strategy = planner.strategies[strategy_name]
                
                # Create repair plan
                repair_plan = planner.create_repair_plan(
                    function_name=f"test_{strategy_name}",
                    failure_type=strategy_name,
                    function_code="def test_func():\n    pass",
                    error_details=f"Test error for {strategy_name}"
                )
                
                assert "prompt" in repair_plan
                assert len(repair_plan["prompt"]) > 50
                assert strategy_name in repair_plan["prompt"]
                
                print(f"✅ Strategy {strategy_name}: {len(repair_plan['prompt'])} chars")
            else:
                print(f"⚠️  Strategy {strategy_name} not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])