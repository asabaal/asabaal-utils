#!/usr/bin/env python3
"""
Plan Patches - Map failure classifications to repair strategies

This module creates repair recipes based on failure classifications.
It provides structured prompts and strategies for the OLAMA repair process.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RepairStrategy:
    """Defines a repair strategy for a specific failure type."""
    name: str
    description: str
    prompt_template: str
    max_attempts: int = 3
    confidence_threshold: float = 0.8
    requires_signature_fix: bool = False
    allowed_changes: int = 20

class PatchPlanner:
    """Maps failure classifications to repair strategies."""
    
    def __init__(self, healer_dir: Path):
        self.healer_dir = healer_dir
        self.artifacts_dir = healer_dir / "artifacts"
        self.strategies = self._initialize_strategies()
        
    def _initialize_strategies(self) -> Dict[str, RepairStrategy]:
        """Initialize repair strategies for each failure type."""
        return {
            "signature_mismatch": RepairStrategy(
                name="signature_mismatch",
                description="Function signature doesn't match expected canonical form",
                prompt_template=self._signature_mismatch_prompt(),
                max_attempts=2,
                confidence_threshold=0.9,
                requires_signature_fix=True,
                allowed_changes=5
            ),
            
            "throws_on_smoke": RepairStrategy(
                name="throws_on_smoke",
                description="Function crashes on basic smoke test",
                prompt_template=self._throws_on_smoke_prompt(),
                max_attempts=3,
                confidence_threshold=0.8,
                allowed_changes=15
            ),
            
            "logic_mismatch": RepairStrategy(
                name="logic_mismatch",
                description="Function logic doesn't match expected behavior",
                prompt_template=self._logic_mismatch_prompt(),
                max_attempts=3,
                confidence_threshold=0.7,
                allowed_changes=20
            ),
            
            "import_error": RepairStrategy(
                name="import_error",
                description="Missing or incorrect imports",
                prompt_template=self._import_error_prompt(),
                max_attempts=2,
                confidence_threshold=0.9,
                allowed_changes=3
            ),
            
            "syntax_error": RepairStrategy(
                name="syntax_error",
                description="Python syntax errors",
                prompt_template=self._syntax_error_prompt(),
                max_attempts=2,
                confidence_threshold=0.95,
                allowed_changes=10
            ),
            
            "type_error": RepairStrategy(
                name="type_error",
                description="Type-related runtime errors",
                prompt_template=self._type_error_prompt(),
                max_attempts=3,
                confidence_threshold=0.8,
                allowed_changes=12
            ),
            
            "attribute_error": RepairStrategy(
                name="attribute_error",
                description="Missing or incorrect attributes/method calls",
                prompt_template=self._attribute_error_prompt(),
                max_attempts=3,
                confidence_threshold=0.8,
                allowed_changes=15
            ),
            
            "value_error": RepairStrategy(
                name="value_error",
                description="Invalid values or edge cases",
                prompt_template=self._value_error_prompt(),
                max_attempts=3,
                confidence_threshold=0.7,
                allowed_changes=15
            )
        }
    
    def _signature_mismatch_prompt(self) -> str:
        """Generate prompt for signature mismatch repairs."""
        return """You are fixing a Python function signature mismatch.

CURRENT FUNCTION:
```python
{function_code}
```

EXPECTED SIGNATURE:
```python
{expected_signature}
```

ERROR DETAILS:
{error_details}

REPAIR INSTRUCTIONS:
1. Change ONLY the function signature to match the expected form
2. Keep all parameter names the same if possible
3. Preserve the function body logic
4. Add type hints if missing in expected signature
5. Do not change the function implementation

Return ONLY the complete fixed function with the correct signature."""
    
    def _throws_on_smoke_prompt(self) -> str:
        """Generate prompt for smoke test failure repairs."""
        return """You are fixing a Python function that crashes on basic smoke test.

CURRENT FUNCTION:
```python
{function_code}
```

SMOKE TEST ERROR:
{error_details}

EXPECTED BEHAVIOR:
- Function must work with no arguments (smoke test) using default parameters
- Should not raise exceptions when called with defaults
- Should return a reasonable default value when called with defaults
- Should preserve core functionality when called with proper arguments

REPAIR INSTRUCTIONS:
1. Ensure all parameters have sensible defaults
2. Add guards to prevent crashes when using defaults (e.g., empty lists, zero values)
3. Return a reasonable default value (empty list, empty dict, None, etc.) when called with defaults
4. Preserve the core logic for when proper arguments are provided
5. Handle edge cases gracefully without raising exceptions

Return ONLY the complete fixed function."""
    
    def _logic_mismatch_prompt(self) -> str:
        """Generate prompt for logic mismatch repairs."""
        return """You are fixing a Python function with incorrect logic.

CURRENT FUNCTION:
```python
{function_code}
```

TEST FAILURE DETAILS:
{error_details}

EXPECTED BEHAVIOR:
{expected_behavior}

REPAIR INSTRUCTIONS:
1. Analyze the test failure to understand expected behavior
2. Fix the logic to match the expected behavior
3. Preserve the function's overall purpose and structure
4. Ensure the fix handles the failing test case
5. Keep changes focused on the logic issue

Return ONLY the complete fixed function."""
    
    def _import_error_prompt(self) -> str:
        """Generate prompt for import error repairs."""
        return """You are fixing import errors in a Python function.

CURRENT FUNCTION:
```python
{function_code}
```

IMPORT ERROR:
{error_details}

REPAIR INSTRUCTIONS:
1. Fix missing or incorrect imports
2. Use standard library imports when possible
3. Remove unused imports
4. Fix import paths if needed
5. Do not change the function logic

Return ONLY the complete fixed function with correct imports."""
    
    def _syntax_error_prompt(self) -> str:
        """Generate prompt for syntax error repairs."""
        return """You are fixing Python syntax errors.

CURRENT FUNCTION:
```python
{function_code}
```

SYNTAX ERROR:
{error_details}

REPAIR INSTRUCTIONS:
1. Fix the syntax error
2. Ensure proper indentation
3. Fix any missing colons, brackets, etc.
4. Preserve the logic and intent
5. Ensure the code is valid Python

Return ONLY the complete fixed function."""
    
    def _type_error_prompt(self) -> str:
        """Generate prompt for type error repairs."""
        return """You are fixing type-related runtime errors.

CURRENT FUNCTION:
```python
{function_code}
```

TYPE ERROR:
{error_details}

REPAIR INSTRUCTIONS:
1. Fix the type error (wrong operations, method calls, etc.)
2. Add proper type checking/conversion if needed
3. Handle different input types appropriately
4. Preserve the core logic
5. Ensure type safety

Return ONLY the complete fixed function."""
    
    def _attribute_error_prompt(self) -> str:
        """Generate prompt for attribute error repairs."""
        return """You are fixing attribute errors (missing methods/attributes).

CURRENT FUNCTION:
```python
{function_code}
```

ATTRIBUTE ERROR:
{error_details}

REPAIR INSTRUCTIONS:
1. Fix the missing or incorrect attribute/method call
2. Use correct method names and parameters
3. Handle cases where attributes might not exist
4. Use appropriate alternatives if needed
5. Preserve the intended functionality

Return ONLY the complete fixed function."""
    
    def _value_error_prompt(self) -> str:
        """Generate prompt for value error repairs."""
        return """You are fixing value errors (invalid values, edge cases).

CURRENT FUNCTION:
```python
{function_code}
```

VALUE ERROR:
{error_details}

REPAIR INSTRUCTIONS:
1. Fix the invalid value or edge case handling
2. Add proper input validation
3. Handle boundary conditions correctly
4. Provide appropriate defaults or error handling
5. Preserve the core logic

Return ONLY the complete fixed function."""
    
    def create_repair_plan(self, function_name: str, failure_type: str, 
                          function_code: str, error_details: str,
                          expected_signature: Optional[str] = None,
                          expected_behavior: Optional[str] = None) -> Dict:
        """Create a repair plan for a specific function failure."""
        
        if failure_type not in self.strategies:
            raise ValueError(f"Unknown failure type: {failure_type}")
        
        strategy = self.strategies[failure_type]
        
        # Build the prompt
        prompt = strategy.prompt_template.format(
            function_code=function_code,
            error_details=error_details,
            expected_signature=expected_signature or "N/A",
            expected_behavior=expected_behavior or "N/A"
        )
        
        # Create repair plan
        repair_plan = {
            "function_name": function_name,
            "failure_type": failure_type,
            "strategy": strategy.name,
            "prompt": prompt,
            "max_attempts": strategy.max_attempts,
            "confidence_threshold": strategy.confidence_threshold,
            "requires_signature_fix": strategy.requires_signature_fix,
            "allowed_changes": strategy.allowed_changes,
            "expected_signature": expected_signature,
            "status": "pending"
        }
        
        return repair_plan
    
    def save_repair_plans(self, plans: List[Dict], output_file: Path) -> None:
        """Save repair plans to a YAML file."""
        plans_data = {
            "repair_plans": plans,
            "total_plans": len(plans),
            "strategies_used": list(set(plan["failure_type"] for plan in plans))
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(plans_data, f, default_flow_style=False, indent=2)
    
    def load_repair_plans(self, input_file: Path) -> List[Dict]:
        """Load repair plans from a YAML file."""
        with open(input_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return data.get("repair_plans", [])
    
    def get_strategy_summary(self) -> Dict:
        """Get summary of available repair strategies."""
        return {
            name: {
                "description": strategy.description,
                "max_attempts": strategy.max_attempts,
                "confidence_threshold": strategy.confidence_threshold,
                "requires_signature_fix": strategy.requires_signature_fix
            }
            for name, strategy in self.strategies.items()
        }

def main():
    """Main function for testing the patch planner."""
    healer_dir = Path(__file__).parent
    planner = PatchPlanner(healer_dir)
    
    # Test creating a repair plan
    test_function = '''def add_numbers(a, b):
    return a + b'''
    
    test_error = "TypeError: unsupported operand type(s) for +: 'str' and 'int'"
    
    plan = planner.create_repair_plan(
        function_name="add_numbers",
        failure_type="type_error",
        function_code=test_function,
        error_details=test_error
    )
    
    print("Created repair plan:")
    print(yaml.dump(plan, default_flow_style=False, indent=2))
    
    # Show strategy summary
    print("\nAvailable strategies:")
    summary = planner.get_strategy_summary()
    print(yaml.dump(summary, default_flow_style=False, indent=2))

if __name__ == "__main__":
    main()