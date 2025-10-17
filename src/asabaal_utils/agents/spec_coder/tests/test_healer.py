"""
Test suite for the Healer class.
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, call

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from healer import Healer


class TestHealer:
    """Test cases for Healer class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def healer(self, temp_dir):
        """Create a Healer instance."""
        # Mock the SignatureEnforcer to avoid catalog dependency
        with patch('healer.enforce_signature.SignatureEnforcer'):
            with patch('healer.classify_failures.FailureClassifier'):
                with patch('healer.plan_patches.PatchPlanner'):
                    return Healer(healer_dir=temp_dir)
    
    def test_healer_initialization(self, healer, temp_dir):
        """Test that Healer can be initialized."""
        assert healer is not None
        assert healer.healer_dir == temp_dir
        assert healer.artifacts_dir == temp_dir / "artifacts"
    
    def test_healer_initialization_default_model(self, healer):
        """Test healer initialization with default model."""
        assert healer.ollama_model == "qwen3-coder:latest"
    
    def test_healer_initialization_custom_model(self, temp_dir):
        """Test healer initialization with custom model."""
        custom_model = "custom-model:latest"
        with patch('healer.enforce_signature.SignatureEnforcer'):
            with patch('healer.classify_failures.FailureClassifier'):
                with patch('healer.plan_patches.PatchPlanner'):
                    healer = Healer(healer_dir=temp_dir, ollama_model=custom_model)
                    assert healer.ollama_model == custom_model
    
    def test_load_failure_classifications_success(self, healer, temp_dir):
        """Test loading failure classifications successfully."""
        # Create mock classification file
        artifacts_dir = temp_dir / "artifacts"
        artifacts_dir.mkdir()
        classification_file = artifacts_dir / "failure_classifications.yaml"
        
        mock_classifications = {
            "failures": [
                {
                    "function": "test_func",
                    "type": "import_error",
                    "description": "Missing import"
                }
            ]
        }
        
        with open(classification_file, 'w') as f:
            yaml.dump(mock_classifications, f)
        
        result = healer.load_failure_classifications()
        assert result == mock_classifications
    
    def test_load_failure_classifications_not_found(self, healer):
        """Test loading failure classifications when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            healer.load_failure_classifications()
    
    @patch('builtins.open', new_callable=mock_open, read_data='def test_func(): pass')
    def test_load_function_code_success(self, mock_file, healer, temp_dir):
        """Test loading function code successfully."""
        function_name = "test_func"
        
        # Mock the path existence
        with patch.object(Path, 'exists', return_value=True):
            result = healer.load_function_code(function_name)
            assert result == 'def test_func(): pass'
    
    def test_heal_all_functions_no_failures(self, healer, temp_dir):
        """Test healing when there are no failures."""
        # Create empty classifications with correct structure
        artifacts_dir = temp_dir / "artifacts"
        artifacts_dir.mkdir()
        classification_file = artifacts_dir / "failure_classifications.yaml"
        
        with open(classification_file, 'w') as f:
            yaml.dump({}, f)
        
        with patch.object(healer, 'load_function_code', return_value='def test_func(): pass'):
            results = healer.heal_all_functions()
            assert len(results) == 0