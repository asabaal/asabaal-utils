"""
Comprehensive test suite for the spec-coder orchestrator pipeline.
"""

import pytest
import json
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Import the orchestrator module so we can patch it directly
import asabaal_utils.agents.spec_coder.orchestrator as orch_mod
from asabaal_utils.agents.spec_coder.generator import GenerationResult
from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_spec_file(temp_dir):
    """Create a sample OpenSpec YAML file for testing."""
    spec_content = """
spec_id: "test-001"
title: "Test Specification"
version: "1.0.0"
description: "A test specification for unit testing"

requirements:
  - id: "req-001"
    title: "Test Requirement"
    description: "A test requirement"
    validation: "should return True"
    priority: "high"
"""
    spec_file = temp_dir / "test_spec.yml"
    spec_file.write_text(spec_content)
    return spec_file


@pytest.fixture
def mock_code_generator():
    """Provides a reusable mock for CodeGenerator."""
    mock_generator = Mock()
    mock_result = GenerationResult(
        success=True,
        files_generated=["test.py"],
        errors=[],
        warnings=["Test warning"],
        execution_time=2.5,
    )
    mock_generator.generate_from_spec.return_value = mock_result
    with patch.object(sys.modules[orch_mod.__name__], "CodeGenerator", return_value=mock_generator):
        yield mock_generator


class TestIntegrationOrchestrator:
    """Test cases for IntegrationOrchestrator class."""

    def test_init_with_default_directory(self):
        orch = IntegrationOrchestrator()
        assert orch.base_dir == Path.cwd()
        assert orch.spec_file_path is None

    def test_init_with_custom_directory(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        assert orch.base_dir == temp_dir
        assert orch.spec_file_path is None

    def test_get_reports_dir_with_output_dir(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        output_dir = temp_dir / "output"
        reports_dir = orch.get_reports_dir(output_dir)
        assert reports_dir == output_dir / "reports"

    def test_get_reports_dir_without_output_dir(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        reports_dir = orch.get_reports_dir(None)
        assert reports_dir == Path.cwd() / "reports"

    def test_load_spec_file_path_from_metadata(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        reports_dir = temp_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "spec_file_path": str(temp_dir / "test.yml"),
            "stage_completed": "stage1",
            "timestamp": datetime.now().isoformat(),
        }
        metadata_file = reports_dir / "pipeline_metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        success = orch.load_spec_file_path_from_metadata(output_dir=temp_dir)
        assert success
        assert orch.spec_file_path == Path(temp_dir / "test.yml")

    def test_load_spec_file_path_from_metadata_not_found(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        success = orch.load_spec_file_path_from_metadata(output_dir=temp_dir / "different")
        assert not success
        assert orch.spec_file_path is None

    def test_load_spec_file_path_already_set(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        orch.spec_file_path = temp_dir / "existing.yml"
        success = orch.load_spec_file_path_from_metadata()
        assert success
        assert orch.spec_file_path == temp_dir / "existing.yml"

    def test_stage1_spec_to_scaffold_success(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test successful Stage 1 execution."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        result = orch._stage1_spec_to_scaffold(sample_spec_file, None)
        assert result

    def test_stage1_spec_to_scaffold_report_save_failure(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test Stage 1 when report saving fails."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        output_dir = temp_dir / "output"
        
        # Force an IOError when writing the report file
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = orch._stage1_spec_to_scaffold(sample_spec_file, output_dir)
        
        # Should fail if report/metadata saving fails
        assert not result

    def test_stage1_spec_to_scaffold_exception(self, temp_dir, sample_spec_file):
        """Test Stage 1 when an exception occurs."""
        with patch.object(sys.modules[orch_mod.__name__], "CodeGenerator", side_effect=Exception("Test exception")):
            orch = IntegrationOrchestrator(base_dir=temp_dir)
            result = orch._stage1_spec_to_scaffold(sample_spec_file, temp_dir / "output")
        assert not result


class TestDirectoryCreation:
    """Test cases specifically for directory creation issues."""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_reports_directory_creation_with_output_dir(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        output_dir = temp_dir / "output"
        reports_dir = orch.get_reports_dir(output_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        assert reports_dir.exists()
        assert reports_dir.is_dir()
        assert reports_dir == output_dir / "reports"

    def test_reports_directory_creation_without_output_dir(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        reports_dir = orch.get_reports_dir(None)
        reports_dir.mkdir(parents=True, exist_ok=True)
        assert reports_dir.exists()
        assert reports_dir.is_dir()
        assert reports_dir == Path.cwd() / "reports"

    def test_nested_directory_creation(self, temp_dir):
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        output_dir = temp_dir / "level1" / "level2" / "output"
        reports_dir = orch.get_reports_dir(output_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        assert reports_dir.exists()
        assert reports_dir.is_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
