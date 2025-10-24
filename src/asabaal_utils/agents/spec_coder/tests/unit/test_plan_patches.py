"""
Comprehensive test suite for the plan_patches module.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from asabaal_utils.agents.spec_coder.healer.plan_patches import PatchPlanner, RepairStrategy


class TestRepairStrategy:
    """Test cases for RepairStrategy dataclass."""
    
    def test_repair_strategy_creation(self):
        """Test creating a RepairStrategy with all parameters."""
        strategy = RepairStrategy(
            name="test_strategy",
            description="Test strategy for testing",
            prompt_template="Test prompt template",
            max_attempts=5,
            confidence_threshold=0.9,
            requires_signature_fix=True,
            allowed_changes=15
        )
        
        assert strategy.name == "test_strategy"
        assert strategy.description == "Test strategy for testing"
        assert strategy.prompt_template == "Test prompt template"
        assert strategy.max_attempts == 5
        assert strategy.confidence_threshold == 0.9
        assert strategy.requires_signature_fix is True
        assert strategy.allowed_changes == 15
    
    def test_repair_strategy_defaults(self):
        """Test creating a RepairStrategy with default values."""
        strategy = RepairStrategy(
            name="test_strategy",
            description="Test strategy",
            prompt_template="Test prompt"
        )
        
        assert strategy.max_attempts == 3  # default
        assert strategy.confidence_threshold == 0.8  # default
        assert strategy.requires_signature_fix is False  # default
        assert strategy.allowed_changes == 20  # default


class TestPatchPlanner:
    """Test cases for PatchPlanner class."""
    
    @pytest.fixture
    def temp_healer_dir(self):
        """Create a temporary healer directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        healer_dir = temp_dir / "healer"
        healer_dir.mkdir()
        artifacts_dir = healer_dir / "artifacts"
        artifacts_dir.mkdir()
        yield healer_dir
        shutil.rmtree(temp_dir)
    
    def test_patch_planner_initialization(self, temp_healer_dir):
        """Test PatchPlanner initialization."""
        planner = PatchPlanner(temp_healer_dir)
        
        assert planner.healer_dir == temp_healer_dir
        assert planner.artifacts_dir == temp_healer_dir / "artifacts"
        assert isinstance(planner.strategies, dict)
        assert len(planner.strategies) > 0
    
    def test_patch_planner_strategies_count(self, temp_healer_dir):
        """Test that all expected strategies are initialized."""
        planner = PatchPlanner(temp_healer_dir)
        
        expected_strategies = [
            "signature_mismatch",
            "throws_on_smoke",
            "logic_mismatch",
            "import_error",
            "syntax_error",
            "type_error",
            "attribute_error",
            "value_error"
        ]
        
        for strategy_name in expected_strategies:
            assert strategy_name in planner.strategies
            assert isinstance(planner.strategies[strategy_name], RepairStrategy)
    
    def test_get_strategy_from_strategies_dict(self, temp_healer_dir):
        """Test getting strategy from the strategies dictionary."""
        planner = PatchPlanner(temp_healer_dir)
        
        strategy = planner.strategies.get("signature_mismatch")
        assert strategy is not None
        assert strategy.name == "signature_mismatch"
        assert strategy.requires_signature_fix is True
        assert strategy.max_attempts == 2
        assert strategy.allowed_changes == 5
    
    def test_get_unknown_strategy_from_strategies_dict(self, temp_healer_dir):
        """Test getting unknown strategy from the strategies dictionary."""
        planner = PatchPlanner(temp_healer_dir)
        
        strategy = planner.strategies.get("unknown_failure")
        assert strategy is None
    
    def test_signature_mismatch_strategy_properties(self, temp_healer_dir):
        """Test signature mismatch strategy has correct properties."""
        planner = PatchPlanner(temp_healer_dir)
        strategy = planner.strategies["signature_mismatch"]
        
        assert strategy.name == "signature_mismatch"
        assert "signature" in strategy.description.lower()
        assert strategy.requires_signature_fix is True
        assert strategy.max_attempts == 2
        assert strategy.confidence_threshold == 0.9
        assert strategy.allowed_changes == 5
    
    def test_throws_on_smoke_strategy_properties(self, temp_healer_dir):
        """Test throws_on_smoke strategy has correct properties."""
        planner = PatchPlanner(temp_healer_dir)
        strategy = planner.strategies["throws_on_smoke"]
        
        assert strategy.name == "throws_on_smoke"
        assert "smoke" in strategy.description.lower()
        assert strategy.requires_signature_fix is False
        assert strategy.max_attempts == 3
        assert strategy.confidence_threshold == 0.8
    
    def test_type_error_strategy_properties(self, temp_healer_dir):
        """Test type_error strategy has correct properties."""
        planner = PatchPlanner(temp_healer_dir)
        strategy = planner.strategies["type_error"]
        
        assert strategy.name == "type_error"
        assert "type" in strategy.description.lower()
        assert strategy.requires_signature_fix is False
        assert strategy.max_attempts == 3
    
    def test_import_error_strategy_properties(self, temp_healer_dir):
        """Test import_error strategy has correct properties."""
        planner = PatchPlanner(temp_healer_dir)
        strategy = planner.strategies["import_error"]
        
        assert strategy.name == "import_error"
        assert "import" in strategy.description.lower()
        assert strategy.requires_signature_fix is False
        assert strategy.max_attempts == 2
    
    def test_all_strategies_have_required_fields(self, temp_healer_dir):
        """Test that all strategies have required fields populated."""
        planner = PatchPlanner(temp_healer_dir)
        
        for strategy_name, strategy in planner.strategies.items():
            assert isinstance(strategy, RepairStrategy)
            assert strategy.name == strategy_name
            assert strategy.description is not None and len(strategy.description) > 0
            assert strategy.prompt_template is not None and len(strategy.prompt_template) > 0
            assert strategy.max_attempts > 0
            assert 0 <= strategy.confidence_threshold <= 1.0
            assert strategy.allowed_changes > 0
            assert isinstance(strategy.requires_signature_fix, bool)
    
    def test_prompt_templates_contain_placeholders(self, temp_healer_dir):
        """Test that prompt templates contain expected placeholders."""
        planner = PatchPlanner(temp_healer_dir)
        
        for strategy_name, strategy in planner.strategies.items():
            # Check for common placeholders in prompt templates
            template = strategy.prompt_template
            # Most templates should have function_code and error_details
            assert "{function_code}" in template
            assert "{error_details}" in template
    
    def test_strategy_prompt_templates_are_unique(self, temp_healer_dir):
        """Test that different strategies have different prompt templates."""
        planner = PatchPlanner(temp_healer_dir)
        
        templates = [strategy.prompt_template for strategy in planner.strategies.values()]
        # Most templates should be unique (allowing for some similarities)
        unique_templates = set(templates)
        assert len(unique_templates) >= len(templates) * 0.8  # At least 80% unique
    
    def test_create_repair_plan_signature_mismatch(self, temp_healer_dir):
        """Test creating a repair plan for signature mismatch."""
        planner = PatchPlanner(temp_healer_dir)
        
        function_code = "def add_numbers(a, b):\n    return a + b"
        error_details = "Signature mismatch: expected (a: int, b: int) -> int"
        expected_signature = "def add_numbers(a: int, b: int) -> int:"
        
        plan = planner.create_repair_plan(
            "add_numbers", 
            "signature_mismatch",
            function_code,
            error_details,
            expected_signature
        )
        
        assert plan is not None
        assert plan["function_name"] == "add_numbers"
        assert plan["failure_type"] == "signature_mismatch"
        assert plan["strategy"] == "signature_mismatch"
        assert "prompt" in plan
        assert plan["max_attempts"] == 2
        assert plan["requires_signature_fix"] is True
        assert plan["expected_signature"] == expected_signature
    
    def test_create_repair_plan_type_error(self, temp_healer_dir):
        """Test creating a repair plan for type error."""
        planner = PatchPlanner(temp_healer_dir)
        
        function_code = "def add_numbers(a, b):\n    return a + b"
        error_details = "TypeError: unsupported operand type(s) for +: 'str' and 'int'"
        
        plan = planner.create_repair_plan(
            "add_numbers", 
            "type_error",
            function_code,
            error_details
        )
        
        assert plan is not None
        assert plan["function_name"] == "add_numbers"
        assert plan["failure_type"] == "type_error"
        assert plan["strategy"] == "type_error"
        assert plan["requires_signature_fix"] is False
        assert plan["max_attempts"] == 3
    
    def test_create_repair_plan_unknown_failure_type(self, temp_healer_dir):
        """Test creating a repair plan for unknown failure type."""
        planner = PatchPlanner(temp_healer_dir)
        
        function_code = "def test():\n    pass"
        error_details = "Unknown error"
        
        with pytest.raises(ValueError, match="Unknown failure type: unknown_failure"):
            planner.create_repair_plan(
                "test", 
                "unknown_failure",
                function_code,
                error_details
            )
    
    def test_save_repair_plans(self, temp_healer_dir):
        """Test saving repair plans to file."""
        planner = PatchPlanner(temp_healer_dir)
        
        plans = [
            {
                "function_name": "test_function",
                "failure_type": "signature_mismatch",
                "strategy": "signature_mismatch",
                "prompt": "Test prompt",
                "max_attempts": 2,
                "status": "pending"
            }
        ]
        
        plan_file = temp_healer_dir / "artifacts" / "test_plans.yaml"
        planner.save_repair_plans(plans, plan_file)
        
        assert plan_file.exists()
        
        with open(plan_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["total_plans"] == 1
        assert len(saved_data["repair_plans"]) == 1
        assert saved_data["strategies_used"] == ["signature_mismatch"]
    
    def test_load_repair_plans(self, temp_healer_dir):
        """Test loading repair plans from file."""
        planner = PatchPlanner(temp_healer_dir)
        
        # Create a test plan file
        plan_file = temp_healer_dir / "artifacts" / "existing_plans.yaml"
        test_data = {
            "repair_plans": [
                {
                    "function_name": "test_function",
                    "failure_type": "type_error",
                    "strategy": "type_error",
                    "prompt": "Test prompt",
                    "max_attempts": 3,
                    "status": "pending"
                }
            ],
            "total_plans": 1,
            "strategies_used": ["type_error"]
        }
        
        with open(plan_file, 'w') as f:
            yaml.dump(test_data, f)
        
        loaded_plans = planner.load_repair_plans(plan_file)
        
        assert len(loaded_plans) == 1
        assert loaded_plans[0]["function_name"] == "test_function"
        assert loaded_plans[0]["failure_type"] == "type_error"
    
    def test_get_strategy_summary(self, temp_healer_dir):
        """Test getting strategy summary."""
        planner = PatchPlanner(temp_healer_dir)
        
        summary = planner.get_strategy_summary()
        
        assert isinstance(summary, dict)
        assert len(summary) > 0  # Should have strategies
        
        # Check that each strategy summary has required fields
        for strategy_name, strategy_info in summary.items():
            assert "description" in strategy_info
            assert "max_attempts" in strategy_info
            assert "confidence_threshold" in strategy_info
            assert "requires_signature_fix" in strategy_info