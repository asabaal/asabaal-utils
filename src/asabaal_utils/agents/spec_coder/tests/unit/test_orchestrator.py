"""
Comprehensive test suite for the spec-coder orchestrator pipeline.
"""

import pytest
import json
import tempfile
import shutil
import sys
import subprocess
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
    with patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator', return_value=mock_generator):
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


class TestOrchestratorMethods:
    """Test cases for additional orchestrator methods."""

    def test_run_command_success(self, temp_dir):
        """Test successful command execution."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = orch.run("echo test", capture=True)
            
            assert result == mock_result
            mock_run.assert_called_once_with(
                "echo test", shell=True, capture_output=True, text=True, 
                cwd=temp_dir, timeout=300
            )

    def test_run_command_timeout(self, temp_dir):
        """Test command execution with timeout."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("test", 300)):
            result = orch.run("sleep 10", capture=True)
            
            assert result.returncode == 1
            assert result.stderr == "Timeout"

    def test_run_command_exception(self, temp_dir):
        """Test command execution with exception."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch('subprocess.run', side_effect=Exception("Command failed")):
            result = orch.run("invalid_command", capture=True)
            
            assert result.returncode == 1
            assert "Command failed" in result.stderr

    def test_run_command_no_capture(self, temp_dir):
        """Test command execution without capture."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_run.return_value = mock_result
            
            result = orch.run("echo test", capture=False)
            
            assert result == mock_result
            mock_run.assert_called_once_with(
                "echo test", shell=True, cwd=temp_dir, timeout=300
            )

    def test_clean_test_file_content(self, temp_dir):
        """Test test file content cleaning."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        # Test with various content issues
        content_with_issues = '''
        import pytest
        
        def test_example():
            """Test function."""
            assert True
            
        class TestClass:
            def test_method(self):
                pass
        '''
        
        cleaned = orch._clean_test_file_content(content_with_issues)
        
        # Should preserve important content
        assert "import pytest" in cleaned
        assert "def test_example():" in cleaned
        assert "class TestClass:" in cleaned
        # Should not start or end with blank lines
        assert not cleaned.startswith('\n')
        assert not cleaned.endswith('\n')

    def test_clean_test_file_content_empty(self, temp_dir):
        """Test cleaning empty content."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        cleaned = orch._clean_test_file_content("")
        assert cleaned == ""

    def test_clean_test_file_content_fix_indentation(self, temp_dir):
        """Test fixing indentation issues."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        # Content with incorrect indentation - only fixes lines that don't start with 4 spaces
        # and are within first 5 lines
        bad_content = "  def test_function():\n        assert True"
        
        cleaned = orch._clean_test_file_content(bad_content)
        
        # Should fix indentation for function definition (first line with 2 spaces)
        lines = cleaned.split('\n')
        func_line = next((line for line in lines if 'def test_function():' in line), None)
        assert func_line is not None
        assert func_line == "def test_function():"

    def test_run_mode_fresh(self, temp_dir, sample_spec_file):
        """Test run_mode with 'fresh' mode."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        # Current implementation just prints and returns True for any mode
        result = orch.run_mode('fresh')
        
        assert result is True

    def test_run_mode_invalid(self, temp_dir):
        """Test run_mode with invalid mode."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        # Current implementation just prints and returns True for any mode
        result = orch.run_mode('invalid')
        
        assert result is True  # Current implementation returns True for any mode

    def test_run_full_pipeline_success(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test successful full pipeline execution."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        # Mock all stage methods
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=True) as mock_stage1:
            with patch.object(orch, '_stage2_scaffold_to_requirements', return_value=True) as mock_stage2:
                with patch.object(orch, '_stage3_requirements_to_alignment', return_value=True) as mock_stage3:
                    with patch.object(orch, '_stage4_alignment_to_code', return_value=True) as mock_stage4:
                        
                        result = orch.run_full_pipeline(sample_spec_file, temp_dir / "output")
                        
                        assert result
                        assert orch.spec_file_path == sample_spec_file
                        mock_stage1.assert_called_once()
                        mock_stage2.assert_called_once()
                        mock_stage3.assert_called_once()
                        mock_stage4.assert_called_once()

    def test_run_full_pipeline_stage1_failure(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test full pipeline when stage 1 fails."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=False) as mock_stage1:
            result = orch.run_full_pipeline(sample_spec_file, temp_dir / "output")
            
            assert not result
            mock_stage1.assert_called_once()

    def test_run_full_pipeline_stage2_failure(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test full pipeline when stage 2 fails."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=True) as mock_stage1:
            with patch.object(orch, '_stage2_scaffold_to_requirements', return_value=False) as mock_stage2:
                result = orch.run_full_pipeline(sample_spec_file, temp_dir / "output")
                
                assert not result
                mock_stage1.assert_called_once()
                mock_stage2.assert_called_once()

    def test_run_full_pipeline_stage3_failure(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test full pipeline when stage 3 fails."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=True) as mock_stage1:
            with patch.object(orch, '_stage2_scaffold_to_requirements', return_value=True) as mock_stage2:
                with patch.object(orch, '_stage3_requirements_to_alignment', return_value=False) as mock_stage3:
                    result = orch.run_full_pipeline(sample_spec_file, temp_dir / "output")
                    
                    assert not result
                    mock_stage1.assert_called_once()
                    mock_stage2.assert_called_once()
                    mock_stage3.assert_called_once()

    def test_run_full_pipeline_stage4_failure(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test full pipeline when stage 4 fails."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=True) as mock_stage1:
            with patch.object(orch, '_stage2_scaffold_to_requirements', return_value=True) as mock_stage2:
                with patch.object(orch, '_stage3_requirements_to_alignment', return_value=True) as mock_stage3:
                    with patch.object(orch, '_stage4_alignment_to_code', return_value=False) as mock_stage4:
                        result = orch.run_full_pipeline(sample_spec_file, temp_dir / "output")
                        
                        assert not result
                        mock_stage1.assert_called_once()
                        mock_stage2.assert_called_once()
                        mock_stage3.assert_called_once()
                        mock_stage4.assert_called_once()

    def test_run_full_pipeline_default_output_dir(self, temp_dir, sample_spec_file, mock_code_generator):
        """Test full pipeline with default output directory."""
        orch = IntegrationOrchestrator(base_dir=temp_dir)
        
        with patch.object(orch, '_stage1_spec_to_scaffold', return_value=True) as mock_stage1:
            with patch.object(orch, '_stage2_scaffold_to_requirements', return_value=True) as mock_stage2:
                with patch.object(orch, '_stage3_requirements_to_alignment', return_value=True) as mock_stage3:
                    with patch.object(orch, '_stage4_alignment_to_code', return_value=True) as mock_stage4:
                        
                        result = orch.run_full_pipeline(sample_spec_file)  # No output_dir specified
                        
                        assert result
                        # Should call stages with None output_dir (default behavior)
                        mock_stage1.assert_called_once_with(sample_spec_file, None)


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
