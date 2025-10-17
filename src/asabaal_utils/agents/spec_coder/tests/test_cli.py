"""
Comprehensive test suite for the CLI module.
"""

import pytest
import tempfile
import shutil
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ..cli import setup_logging, cmd_generate, cmd_test, cmd_heal, cmd_organize, cmd_stage1, main


class TestCLI:
    """Test cases for CLI functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_setup_logging_default(self):
        """Test setup logging with default verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbose=False)
            
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == 20  # INFO level
            assert '%(asctime)s' in call_args['format']
    
    def test_setup_logging_verbose(self):
        """Test setup logging with verbose enabled."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbose=True)
            
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args['level'] == 10  # DEBUG level
    
    def test_cmd_generate_spec_not_found(self, temp_dir):
        """Test cmd_generate when spec file doesn't exist."""
        non_existent_file = temp_dir / "nonexistent.md"
        
        args = Mock()
        args.spec_file = non_existent_file
        args.verbose = False
        
        with patch('builtins.print') as mock_print:
            result = cmd_generate(args)
            
            assert result == 1
            mock_print.assert_called_with(f"Error: Specification file not found: {non_existent_file}")
    
    def test_cmd_generate_success(self, temp_dir):
        """Test cmd_generate successful execution."""
        spec_file = temp_dir / "test_spec.md"
        spec_file.write_text("# Test Specification")
        
        args = Mock()
        args.spec_file = spec_file
        args.verbose = False
        args.output = temp_dir / "output"
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.CodeGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            # Mock result object with expected attributes
            mock_result = Mock()
            mock_result.success = True
            mock_result.files_generated = ["file1.py", "file2.py"]
            mock_result.execution_time = 1.5
            mock_result.warnings = []
            mock_result.errors = []
            
            mock_generator.generate_from_spec.return_value = mock_result
            
            result = cmd_generate(args)
            
            assert result == 0
            mock_generator.generate_from_spec.assert_called_once_with(spec_file, args.output)
    
    def test_cmd_generate_failure(self, temp_dir):
        """Test cmd_generate when generation fails."""
        spec_file = temp_dir / "test_spec.md"
        spec_file.write_text("# Test Specification")
        
        args = Mock()
        args.spec_file = spec_file
        args.verbose = False
        args.output_dir = temp_dir / "output"
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.CodeGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            # Mock result object with expected attributes
            mock_result = Mock()
            mock_result.success = False
            mock_result.files_generated = []
            mock_result.execution_time = 0.0
            mock_result.warnings = []
            mock_result.errors = ["Generation failed"]
            
            mock_generator.generate_from_spec.return_value = mock_result
            
            with patch('builtins.print') as mock_print:
                result = cmd_generate(args)
                
                assert result == 1
                # Check that error message was printed
                mock_print.assert_any_call("❌ Generation failed!")
                mock_print.assert_any_call("   - Generation failed")
    
    def test_cmd_generate_exception(self, temp_dir):
        """Test cmd_generate when an exception occurs."""
        spec_file = temp_dir / "test_spec.md"
        spec_file.write_text("# Test Specification")
        
        args = Mock()
        args.spec_file = spec_file
        args.verbose = False
        args.output_dir = temp_dir / "output"
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.CodeGenerator') as mock_generator_class:
            mock_generator_class.side_effect = Exception("Unexpected error")
            
            with patch('builtins.print') as mock_print:
                result = cmd_generate(args)
                
                assert result == 1
                mock_print.assert_any_call("❌ Unexpected error: Unexpected error")
    
    def test_cmd_test_success(self, temp_dir):
        """Test cmd_test successful execution."""
        args = Mock()
        args.test_dir = temp_dir / "tests"
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.TestAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.run_tests.return_value = True
            
            result = cmd_test(args)
            
            assert result == 0
            mock_analyzer.run_tests.assert_called_once_with()
    
    def test_cmd_test_failure(self, temp_dir):
        """Test cmd_test when analysis fails."""
        args = Mock()
        args.test_dir = temp_dir / "tests"
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.TestAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.run_tests.return_value = False
            
            with patch('builtins.print') as mock_print:
                result = cmd_test(args)
                
                assert result == 1
                mock_print.assert_any_call("❌ Some tests failed!")
    
    def test_cmd_heal_success(self, temp_dir):
        """Test cmd_heal successful execution."""
        args = Mock()
        args.base_dir = temp_dir
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.healer.Healer') as mock_healer_class:
            mock_healer = Mock()
            mock_healer_class.return_value = mock_healer
            mock_healer.heal_all_functions.return_value = [Mock(success=True)]
            
            result = cmd_heal(args)
            
            assert result == 0
            mock_healer.heal_all_functions.assert_called_once()
    
    def test_cmd_heal_failure(self, temp_dir):
        """Test cmd_heal when patching fails."""
        args = Mock()
        args.base_dir = temp_dir
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.healer.Healer') as mock_healer_class:
            mock_healer = Mock()
            mock_healer_class.return_value = mock_healer
            mock_healer.heal_all_functions.return_value = [Mock(success=False)]
            
            with patch('builtins.print') as mock_print:
                result = cmd_heal(args)
                
                assert result == 1
                mock_print.assert_called_with("⚠️ Healing completed with some issues")
    
    def test_cmd_organize_success(self, temp_dir):
        """Test cmd_organize successful execution."""
        args = Mock()
        args.base_dir = temp_dir
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.CodeOrganizer') as mock_organizer_class:
            mock_organizer = Mock()
            mock_organizer_class.return_value = mock_organizer
            mock_organizer.run.return_value = True
            
            result = cmd_organize(args)
            
            assert result == 0
            mock_organizer.run.assert_called_once()
    
    def test_cmd_organize_failure(self, temp_dir):
        """Test cmd_organize when organization fails."""
        args = Mock()
        args.base_dir = temp_dir
        args.verbose = False
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.CodeOrganizer') as mock_organizer_class:
            mock_organizer = Mock()
            mock_organizer_class.return_value = mock_organizer
            mock_organizer.run.return_value = False
            
            with patch('builtins.print') as mock_print:
                result = cmd_organize(args)
                
                assert result == 1
                mock_print.assert_any_call("❌ Code organization failed!")
    
    def test_cmd_stage1_success(self, temp_dir):
        """Test cmd_stage1 successful execution."""
        spec_file = temp_dir / "spec.md"
        spec_file.write_text("# Test Spec")
        
        args = Mock()
        args.spec_file = spec_file
        args.verbose = False
        args.output = temp_dir / "output"
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.IntegrationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator._stage1_spec_to_scaffold.return_value = True
            
            result = cmd_stage1(args)
            
            assert result == 0
            mock_orchestrator._stage1_spec_to_scaffold.assert_called_once_with(spec_file, args.output)
    
    def test_cmd_stage1_failure(self, temp_dir):
        """Test cmd_stage1 when stage fails."""
        spec_file = temp_dir / "spec.md"
        spec_file.write_text("# Test Spec")
        
        args = Mock()
        args.spec_file = spec_file
        args.verbose = False
        args.output = temp_dir / "output"
        
        with patch('src.asabaal_utils.agents.spec_coder.cli.IntegrationOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator._stage1_spec_to_scaffold.return_value = False
            
            result = cmd_stage1(args)
            
            assert result == 1
    
    def test_main_generate_command(self, temp_dir):
        """Test main function with generate command."""
        spec_file = temp_dir / "spec.md"
        spec_file.write_text("# Test Spec")
        
        test_args = ['generate', str(spec_file)]
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_generate') as mock_cmd:
                mock_cmd.return_value = 0
                
                result = main()
                
                assert result == 0
                mock_cmd.assert_called_once()
    
    def test_main_test_command(self, temp_dir):
        """Test main function with test command."""
        test_args = ['test']
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_test') as mock_cmd:
                mock_cmd.return_value = 0
                
                result = main()
                
                assert result == 0
                mock_cmd.assert_called_once()
    
    def test_main_heal_command(self, temp_dir):
        """Test main function with heal command."""
        test_args = ['heal']
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_heal') as mock_cmd:
                mock_cmd.return_value = 0
                
                result = main()
                
                assert result == 0
                mock_cmd.assert_called_once()
    
    def test_main_organize_command(self, temp_dir):
        """Test main function with organize command."""
        test_args = ['organize']
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_organize') as mock_cmd:
                mock_cmd.return_value = 0
                
                result = main()
                
                assert result == 0
                mock_cmd.assert_called_once()
    
    def test_main_orchestrate_command(self, temp_dir):
        """Test main function with orchestrate command."""
        spec_file = temp_dir / "spec.md"
        spec_file.write_text("# Test Spec")
        
        test_args = ['full-run', str(spec_file)]
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_full_run') as mock_cmd:
                mock_cmd.return_value = 0
                
                result = main()
                
                assert result == 0
                mock_cmd.assert_called_once()
    
    def test_main_no_command(self):
        """Test main function with no command."""
        test_args = []
        
        with patch('sys.argv', ['cli']):
            with patch('argparse.ArgumentParser.print_help') as mock_help:
                result = main()
                
                assert result == 1
                mock_help.assert_called_once()
    
    def test_main_exception_handling(self):
        """Test main function exception handling."""
        test_args = ['generate', 'nonexistent.md']
        
        with patch('sys.argv', ['cli'] + test_args):
            with patch('src.asabaal_utils.agents.spec_coder.cli.cmd_generate', side_effect=Exception("Unexpected error")):
                with patch('builtins.print') as mock_print:
                    result = main()
                    
                    assert result == 1
                    mock_print.assert_called_with("Unexpected error: Unexpected error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])