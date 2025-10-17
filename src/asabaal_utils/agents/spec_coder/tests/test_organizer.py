"""
Comprehensive test suite for the CodeOrganizer class.
"""

import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from ..organizer import CodeOrganizer


class TestCodeOrganizer:
    """Test cases for CodeOrganizer class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def organizer(self, temp_dir):
        """Create a CodeOrganizer instance."""
        return CodeOrganizer(base_dir=temp_dir)
    
    def test_init_default_directory(self):
        """Test organizer initialization with default directory."""
        test_organizer = CodeOrganizer()
        expected_base = Path(__file__).resolve().parents[1]
        assert test_organizer.base_dir == expected_base
    
    def test_init_custom_directory(self, organizer, temp_dir):
        """Test organizer initialization with custom directory."""
        assert organizer.base_dir == temp_dir
        assert organizer.generated_dir == temp_dir / "generated_functions"
        assert organizer.reports_dir == temp_dir / "reports"
        assert organizer.test_env_dir == temp_dir / "reports" / "test_env"
        assert organizer.src_dir == temp_dir / "src"
        assert organizer.tests_dir == temp_dir / "tests"
    
    def test_category_mapping(self, organizer):
        """Test category mapping configuration."""
        assert "core" in organizer.category_mapping
        assert "export" in organizer.category_mapping
        assert "generate" in organizer.category_mapping
        assert "utils" in organizer.category_mapping
        assert "timegrid" in organizer.category_mapping["core"]
        assert "midi_export" in organizer.category_mapping["export"]
    
    def test_ensure_dir_new_directory(self, organizer, temp_dir):
        """Test ensuring a new directory exists."""
        new_dir = temp_dir / "new_subdir"
        
        organizer.ensure_dir(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()
        init_file = new_dir / "__init__.py"
        assert init_file.exists()
        assert len(organizer.log_entries) == 1
        assert organizer.log_entries[0]["action"] == "create_init"
    
    def test_ensure_dir_existing_directory(self, organizer, temp_dir):
        """Test ensuring an existing directory with __init__.py."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()
        (existing_dir / "__init__.py").touch()
        
        initial_log_count = len(organizer.log_entries)
        
        organizer.ensure_dir(existing_dir)
        
        assert len(organizer.log_entries) == initial_log_count
    
    def test_ensure_dir_existing_without_init(self, organizer, temp_dir):
        """Test ensuring an existing directory without __init__.py."""
        existing_dir = temp_dir / "existing_no_init"
        existing_dir.mkdir()
        
        organizer.ensure_dir(existing_dir)
        
        init_file = existing_dir / "__init__.py"
        assert init_file.exists()
        assert len(organizer.log_entries) == 1
    
    def test_categorize_file_core(self, organizer):
        """Test categorizing a core functionality file."""
        file_path = Path("generate_time_grid.py")
        
        category = organizer.categorize_file(file_path)
        
        assert category == "core"
    
    def test_categorize_file_export(self, organizer):
        """Test categorizing an export functionality file."""
        file_path = Path("export_as_midi.py")
        
        category = organizer.categorize_file(file_path)
        
        assert category == "export"
    
    def test_categorize_file_generate(self, organizer):
        """Test categorizing a generation functionality file."""
        file_path = Path("song_generator.py")
        
        category = organizer.categorize_file(file_path)
        
        assert category == "generate"
    
    def test_categorize_file_utils(self, organizer):
        """Test categorizing a utility file."""
        file_path = Path("validation_utils.py")
        
        category = organizer.categorize_file(file_path)
        
        assert category == "utils"
    
    def test_categorize_file_unknown(self, organizer):
        """Test categorizing a file with unknown functionality."""
        file_path = Path("unknown_feature.py")
        
        category = organizer.categorize_file(file_path)
        
        assert category == "misc"
    
    def test_load_integration_summary_success(self, organizer, temp_dir):
        """Test loading integration summary successfully."""
        reports_dir = temp_dir / "reports"
        reports_dir.mkdir()
        summary_file = reports_dir / "latest_integration_summary.json"
        
        mock_summary = {
            "stages": {
                "test_results": {
                    "results": [
                        {"function": "test_func", "success": True}
                    ]
                }
            }
        }
        
        summary_file.write_text(json.dumps(mock_summary))
        
        result = organizer.load_integration_summary()
        
        assert result == mock_summary
    
    def test_load_integration_summary_not_found(self, organizer):
        """Test loading integration summary when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            organizer.load_integration_summary()
    
    def test_extract_successful_functions(self, organizer):
        """Test extracting successful functions from summary."""
        summary = {
            "stages": {
                "test_results": {
                    "results": [
                        {"function": "working_func1", "success": True},
                        {"function": "broken_func", "success": False},
                        {"function": "working_func2", "success": True}
                    ]
                }
            }
        }
        
        successful = organizer.extract_successful_functions(summary)
        
        assert len(successful) == 2
        assert successful[0]["function"] == "working_func1"
        assert successful[1]["function"] == "working_func2"
    
    def test_copy_file_to_src(self, organizer, temp_dir):
        """Test copying a file to src directory."""
        # Create source file
        src_file = temp_dir / "generated_functions" / "test_func.py"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("def test_func():\n    pass")
        
        # Create target directory
        target_dir = temp_dir / "src" / "core"
        target_dir.mkdir(parents=True)
        
        result = organizer.copy_file_to_src(src_file, target_dir)
        
        assert result is True
        target_file = target_dir / "test_func.py"
        assert target_file.exists()
        assert target_file.read_text() == src_file.read_text()
        assert len(organizer.log_entries) >= 1
    
    def test_copy_file_to_src_create_directory(self, organizer, temp_dir):
        """Test copying file when target directory needs to be created."""
        src_file = temp_dir / "generated_functions" / "test_func.py"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("def test_func():\n    pass")
        
        target_dir = temp_dir / "src" / "new_category"
        
        result = organizer.copy_file_to_src(src_file, target_dir)
        
        assert result is True
        assert target_dir.exists()
        assert (target_dir / "__init__.py").exists()
        target_file = target_dir / "test_func.py"
        assert target_file.exists()
    
    def test_copy_file_to_src_source_not_found(self, organizer, temp_dir):
        """Test copying file when source doesn't exist."""
        src_file = temp_dir / "nonexistent.py"
        target_dir = temp_dir / "src" / "core"
        
        result = organizer.copy_file_to_src(src_file, target_dir)
        
        assert result is False
    
    def test_copy_test_to_tests(self, organizer, temp_dir):
        """Test copying test file to tests directory."""
        # Create test file in test_env
        test_env_file = temp_dir / "reports" / "test_env" / "test_func" / "test_func.py"
        test_env_file.parent.mkdir(parents=True)
        test_env_file.write_text("def test_test_func():\n    assert True")
        
        # Create tests directory
        tests_dir = temp_dir / "tests" / "core"
        tests_dir.mkdir(parents=True)
        
        result = organizer.copy_test_to_tests(test_env_file, tests_dir)
        
        assert result is True
        target_test = tests_dir / "test_test_func.py"
        assert target_test.exists()
        assert target_test.read_text() == test_env_file.read_text()
    
    def test_organize_successful_functions(self, organizer, temp_dir):
        """Test organizing successful functions."""
        # Create directory structure
        (temp_dir / "generated_functions").mkdir()
        (temp_dir / "reports").mkdir()
        (temp_dir / "reports" / "test_env").mkdir()
        
        # Create function files
        func_file = temp_dir / "generated_functions" / "generate_time_grid.py"
        func_file.write_text("def generate_time_grid():\n    pass")
        
        # Create test files
        test_dir = temp_dir / "reports" / "test_env" / "generate_time_grid"
        test_dir.mkdir()
        test_file = test_dir / "test_generate_time_grid.py"
        test_file.write_text("def test_generate_time_grid():\n    assert True")
        
        # Mock successful functions
        successful_functions = [
            {"function": "generate_time_grid", "success": True}
        ]
        
        with patch.object(organizer, 'copy_file_to_src', return_value=True) as mock_copy_src:
            with patch.object(organizer, 'copy_test_to_tests', return_value=True) as mock_copy_test:
                organizer.organize_successful_functions(successful_functions)
                
                mock_copy_src.assert_called_once()
                mock_copy_test.assert_called_once()
    
    def test_create_module_init_files(self, organizer, temp_dir):
        """Test creating module __init__.py files with imports."""
        # Create src structure
        core_dir = temp_dir / "src" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "func1.py").touch()
        (core_dir / "func2.py").touch()
        
        export_dir = temp_dir / "src" / "export"
        export_dir.mkdir(parents=True)
        (export_dir / "midi_func.py").touch()
        
        organizer.create_module_init_files()
        
        # Check core __init__.py
        core_init = core_dir / "__init__.py"
        assert core_init.exists()
        core_content = core_init.read_text()
        assert "from .func1 import" in core_content or "from .func2 import" in core_content
        
        # Check export __init__.py
        export_init = export_dir / "__init__.py"
        assert export_init.exists()
    
    def test_create_main_init_file(self, organizer, temp_dir):
        """Test creating main __init__.py file."""
        # Create src structure
        src_dir = temp_dir / "src"
        core_dir = src_dir / "core"
        export_dir = src_dir / "export"
        core_dir.mkdir(parents=True)
        export_dir.mkdir(parents=True)
        (core_dir / "__init__.py").touch()
        (export_dir / "__init__.py").touch()
        
        organizer.create_main_init_file()
        
        main_init = src_dir / "__init__.py"
        assert main_init.exists()
        content = main_init.read_text()
        assert "from .core import" in content
        assert "from .export import" in content
    
    def test_save_organization_log(self, organizer, temp_dir):
        """Test saving organization log."""
        reports_dir = temp_dir / "reports"
        reports_dir.mkdir()
        
        organizer.log_entries = [
            {"action": "create_init", "file": "__init__.py"},
            {"action": "copy_file", "file": "test_func.py"}
        ]
        
        log_file = organizer.save_organization_log()
        
        assert log_file == reports_dir / "organization_log.json"
        assert log_file.exists()
        
        log_data = json.loads(log_file.read_text())
        assert "timestamp" in log_data
        assert "total_actions" in log_data
        assert log_data["total_actions"] == 2
        assert len(log_data["actions"]) == 2
    
    def test_run_no_successful_functions(self, organizer, temp_dir):
        """Test running organization with no successful functions."""
        # Create required directories and files
        reports_dir = temp_dir / "reports"
        reports_dir.mkdir()
        summary_file = reports_dir / "latest_integration_summary.json"
        
        summary = {
            "stages": {
                "test_results": {
                    "results": [
                        {"function": "broken_func", "success": False}
                    ]
                }
            }
        }
        summary_file.write_text(json.dumps(summary))
        
        with patch('builtins.print') as mock_print:
            result = organizer.run()
            
            assert result is True
            mock_print.assert_any_call("✅ No functions to organize - all tests failed!")
    
    def test_run_with_successful_functions(self, organizer, temp_dir):
        """Test running organization with successful functions."""
        # Create directory structure
        reports_dir = temp_dir / "reports"
        generated_dir = temp_dir / "generated_functions"
        reports_dir.mkdir()
        generated_dir.mkdir()
        
        # Create summary with successful functions
        summary_file = reports_dir / "latest_integration_summary.json"
        summary = {
            "stages": {
                "test_results": {
                    "results": [
                        {"function": "generate_time_grid", "success": True}
                    ]
                }
            }
        }
        summary_file.write_text(json.dumps(summary))
        
        # Create function file
        func_file = generated_dir / "generate_time_grid.py"
        func_file.write_text("def generate_time_grid():\n    pass")
        
        with patch.object(organizer, 'organize_successful_functions') as mock_organize:
            with patch.object(organizer, 'create_module_init_files') as mock_init:
                with patch.object(organizer, 'create_main_init_file') as mock_main:
                    with patch.object(organizer, 'save_organization_log') as mock_save:
                        result = organizer.run()
                        
                        assert result is True
                        mock_organize.assert_called_once()
                        mock_init.assert_called_once()
                        mock_main.assert_called_once()
                        mock_save.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])