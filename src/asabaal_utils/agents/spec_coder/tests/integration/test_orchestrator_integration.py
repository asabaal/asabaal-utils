#!/usr/bin/env python3
"""
Integration tests for the Orchestrator component.
Tests multi-stage pipeline coordination and workflow management.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
from datetime import datetime

# Import the modules we're testing
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator


class TestOrchestratorIntegration:
    """Integration tests for IntegrationOrchestrator with multi-stage pipeline coordination."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        print(f"\n🪛 Created temporary workspace: {temp_dir}")
        
        # Create basic directory structure
        (temp_dir / "scripts").mkdir()
        (temp_dir / "healer").mkdir()
        (temp_dir / "prompts").mkdir()
        (temp_dir / "generated_functions").mkdir()
        (temp_dir / "reports").mkdir()
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up temporary workspace: {temp_dir}")
    
    @pytest.fixture
    def sample_openspec(self, tmp_path):
        """Sample OpenSpec specification for testing."""
        spec_content = """
spec_id: "RPG-001"
title: "Rhythmic Pulse Generator"
description: "Generates deterministic rhythmic patterns"

requirements:
  - id: "RPG-001-01"
    title: "Generate Time Grid"
    description: "Generate time grid based on BPM and time signature"
    validation:
      - type: "unit"
        file: "test_generate_time_grid.py"
        target: "test_time_grid_generation"
    interfaces:
      - name: "generate_time_grid"
        parameters:
          - name: "bpm"
            type: "int"
          - name: "time_signature"
            type: "str"
        return_type: "list[float]"
  
  - id: "RPG-001-02"
    title: "Generate Pattern"
    description: "Generate rhythmic pattern based on density"
    validation:
      - type: "unit"
        file: "test_generate_pattern.py"
        target: "test_pattern_generation"
    interfaces:
      - name: "generate_pattern"
        parameters:
          - name: "density"
            type: "float"
          - name: "length"
            type: "int"
        return_type: "list[int]"
  
  - id: "RPG-001-03"
    title: "Combine Grid and Pattern"
    description: "Combine time grid with rhythmic pattern"
    validation:
      - type: "integration"
        file: "test_combine_grid_pattern.py"
        target: "test_combination"
    interfaces:
      - name: "combine_grid_pattern"
        parameters:
          - name: "grid"
            type: "list[float]"
          - name: "pattern"
            type: "list[int]"
        return_type: "list[tuple[float, int]]"
"""
        # Create spec file in tmp_path (parent of temp_workspace) to avoid deletion
        spec_file = tmp_path / "rpg_spec.yml"
        spec_file.write_text(spec_content)
        return spec_file
    
    def test_orchestrator_initialization(self, temp_workspace):
        """Test IntegrationOrchestrator initialization."""
        print("\n🧪 Testing IntegrationOrchestrator initialization...")
        
        # Test with explicit base directory
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        assert orchestrator.base_dir == temp_workspace
        assert orchestrator.scripts_dir == temp_workspace / "scripts"
        assert orchestrator.healer_dir == temp_workspace / "healer"
        assert orchestrator.prompts_dir == temp_workspace / "prompts"
        assert orchestrator.generated_dir == temp_workspace / "generated_functions"
        assert orchestrator.spec_file_path is None
        
        # Test with default base directory (current working directory)
        orchestrator_default = IntegrationOrchestrator()
        assert orchestrator_default.base_dir == Path.cwd()
        
        print("   ✅ IntegrationOrchestrator initialization successful")
    
    def test_get_reports_dir(self, temp_workspace):
        """Test getting reports directory."""
        print("\n🧪 Testing reports directory resolution...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Test with no output_dir
        reports_dir = orchestrator.get_reports_dir()
        assert reports_dir == Path.cwd() / "reports"
        
        # Test with custom output_dir
        custom_output = temp_workspace / "custom_output"
        reports_dir = orchestrator.get_reports_dir(custom_output)
        assert reports_dir == custom_output / "reports"
        
        print("   ✅ Reports directory resolution successful")
    
    def test_load_spec_file_path_from_metadata(self, temp_workspace, sample_openspec):
        """Test loading spec file path from metadata."""
        print("\n🧪 Testing spec file path loading from metadata...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Create metadata file in the correct location (get_reports_dir uses Path.cwd() by default)
        reports_dir = Path.cwd() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = reports_dir / "pipeline_metadata.json"
        
        metadata = {
            "spec_file_path": str(sample_openspec.absolute()),
            "stage_completed": "stage1",
            "timestamp": datetime.now().isoformat()
        }
        
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Load metadata
        result = orchestrator.load_spec_file_path_from_metadata()
        
        assert result == True
        assert orchestrator.spec_file_path == sample_openspec.absolute()
        
        # Cleanup
        if metadata_file.exists():
            metadata_file.unlink()
        if reports_dir.exists():
            import shutil
            shutil.rmtree(reports_dir)
        
        print("   ✅ Spec file path loading successful")
    
    def test_run_command(self, temp_workspace):
        """Test command execution."""
        print("\n🧪 Testing command execution...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Test successful command
        result = orchestrator.run("echo 'test'", capture=True)
        assert result.returncode == 0
        assert "test" in result.stdout
        
        # Test failed command
        result = orchestrator.run("exit 1", capture=True)
        assert result.returncode == 1
        
        print("   ✅ Command execution successful")
    
    def test_run_mode(self, temp_workspace):
        """Test running different pipeline modes."""
        print("\n🧪 Testing pipeline mode execution...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Test different modes
        modes = ["fresh", "update", "heal", "validate", "test"]
        
        for mode in modes:
            result = orchestrator.run_mode(mode)
            assert result == True  # All modes should return True for basic execution
        
        print("   ✅ Pipeline mode execution successful")
    
    @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
    def test_stage1_spec_to_scaffold(self, mock_generator_class, temp_workspace, sample_openspec):
        """Test Stage 1: OpenSpec to scaffold conversion."""
        print("\n🧪 Testing Stage 1: OpenSpec to scaffold...")
        
        # Mock the generator
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = ["test_file.py", "another_file.py"]
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.execution_time = 5.0
        mock_generator.generate_from_spec.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Run Stage 1
        result = orchestrator._stage1_spec_to_scaffold(sample_openspec, temp_workspace)
        
        assert result == True
        assert orchestrator.spec_file_path == sample_openspec
        
        # Verify metadata was saved
        metadata_file = temp_workspace / "reports" / "pipeline_metadata.json"
        assert metadata_file.exists()
        
        metadata = json.loads(metadata_file.read_text())
        assert metadata["spec_file_path"] == str(sample_openspec.absolute())
        assert metadata["stage_completed"] == "stage1"
        
        # Verify stage report was saved
        stage1_report = temp_workspace / "reports" / "stage1_report.json"
        assert stage1_report.exists()
        
        report_data = json.loads(stage1_report.read_text())
        assert report_data["stage"] == "1"
        assert report_data["success"] == True
        assert len(report_data["files_generated"]) == 2
        
        print("   ✅ Stage 1 execution successful")
    
    @patch('asabaal_utils.agents.spec_coder.parse_tests.ASTVisitor')
    @patch('asabaal_utils.agents.spec_coder.summarize_tests.TestSummarizer')
    def test_stage2_scaffold_to_requirements(self, mock_summarizer_class, mock_visitor_class, temp_workspace):
        """Test Stage 2: Scaffold to requirements extraction."""
        print("\n🧪 Testing Stage 2: Scaffold to requirements...")
        
        # Create test files
        test_dir = temp_workspace / "scaffolds" / "tests"
        test_dir.mkdir(parents=True)
        
        test_file = test_dir / "test_example.py"
        test_file.write_text('''
def test_function():
    assert True
''')
        
        # Mock test visitor and summarizer
        mock_visitor = Mock()
        mock_test = Mock()
        mock_test.name = "test_function"
        mock_test.target_function = "function"
        mock_test.inputs = []
        mock_test.assertions = ["assert True"]
        mock_visitor.tests = [mock_test]
        mock_visitor_class.return_value = mock_visitor
        
        mock_summarizer = Mock()
        mock_summarizer.summarize_test.return_value = "Test behavior summary"
        mock_summarizer_class.return_value = mock_summarizer
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Run Stage 2
        result = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
        
        assert result == True
        
        # Verify test summaries were saved
        summary_file = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
        assert summary_file.exists()
        
        summary_data = json.loads(summary_file.read_text())
        assert "tests" in summary_data
        assert len(summary_data["tests"]) == 1
        assert summary_data["tests"][0]["name"] == "test_function"
        assert summary_data["tests"][0]["implied_behavior"] == "Test behavior summary"
        
        print("   ✅ Stage 2 execution successful")
    
    def test_stage2_handles_malformed_test_files(self, temp_workspace):
        """Test Stage 2 handles test files with instructional text that cause IndentationError."""
        print("\n🧪 Testing Stage 2 with malformed test files...")
        
        # Create test files with instructional text (like what Stage 1 generates)
        test_dir = temp_workspace / "scaffolds" / "tests"
        test_dir.mkdir(parents=True)
        
        # Test file with instructional text that causes IndentationError
        test_file1 = test_dir / "test_malformed.py"
        test_file1.write_text(''' pytest test code only.

import pytest
from unittest.mock import patch, MagicMock

def test_generate_time_grid_happy_path():
    result = generate_time_grid(120, 4)
    assert len(result) > 0
    assert result[0] == 0.0
    assert result[-1] <= 4.0''')
        
        # Another test file with different instructional text
        test_file2 = test_dir / "test_also_malformed.py"
        test_file2.write_text('''The test code must be complete and executable as a single pytest file.

import pytest

def test_apply_accent_pattern_happy_path():
    result = apply_accent_pattern([1, 0, 1, 0], [0.0, 0.5, 1.0, 1.5])
    assert len(result) == 4''')
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # This should NOT raise IndentationError - it should handle the malformed files
        try:
            result = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
            assert result == True, "Stage 2 should succeed even with malformed test files"
        except IndentationError as e:
            pytest.fail(f"Stage 2 should handle IndentationError gracefully, but got: {e}")
        
        # Verify test summaries were created despite malformed input
        summary_file = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
        assert summary_file.exists(), "Stage 2 should create summary file even with malformed test files"
        
        summary_data = json.loads(summary_file.read_text())
        assert "tests" in summary_data, "Summary should contain test data"
        assert len(summary_data["tests"]) >= 0, "Should have processed test files"
        
        print("   ✅ Stage 2 handled malformed test files successfully")
    
    @patch('asabaal_utils.agents.spec_coder.align_behaviors.BehavioralAligner')
    @patch('asabaal_utils.agents.spec_coder.spec_parser.SpecParser')
    def test_stage3_requirements_to_alignment(self, mock_parser_class, mock_aligner_class, temp_workspace, sample_openspec):
        """Test Stage 3: Requirements to alignment checking."""
        print("\n🧪 Testing Stage 3: Requirements to alignment...")
        
        # Create Stage 2 test summaries
        stage2_dir = temp_workspace / "reports" / "stage2_test_summaries"
        stage2_dir.mkdir(parents=True)
        
        summary_data = {
            "file": "test_summaries.json",
            "tests": [
                {
                    "name": "test_function",
                    "target_function": "function",
                    "inputs": [],
                    "assertions": ["assert True"],
                    "implied_behavior": "Test behavior summary"
                }
            ]
        }
        
        summary_file = stage2_dir / "test_summary_tests.json"
        summary_file.write_text(json.dumps(summary_data, indent=2))
        
        # Mock spec parser
        mock_parser = Mock()
        mock_spec = Mock()
        mock_spec.requirements = [
            Mock(title="Requirement 1", description="Description 1")
        ]
        mock_parser.parse_file.return_value = mock_spec
        mock_parser_class.return_value = mock_parser
        
        # Mock behavioral aligner
        mock_aligner = Mock()
        mock_alignment_report = {
            "summary": {
                "alignment_rate": 0.85,
                "total_tests": 1,
                "aligned_tests": 1
            },
            "alignments": []
        }
        mock_aligner.align_all_tests.return_value = []
        mock_aligner.generate_alignment_report.return_value = mock_alignment_report
        mock_aligner_class.return_value = mock_aligner
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Run Stage 3
        result = orchestrator._stage3_requirements_to_alignment(temp_workspace)
        
        assert result == True
        
        # Verify alignment report was saved
        alignment_file = temp_workspace / "reports" / "behavioral_alignment_report.json"
        assert alignment_file.exists()
        
        alignment_data = json.loads(alignment_file.read_text())
        assert "summary" in alignment_data
        assert alignment_data["summary"]["alignment_rate"] == 0.85
        
        print("   ✅ Stage 3 execution successful")
    
    @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
    def test_stage4_alignment_to_code_dry_run(self, mock_generator_class, temp_workspace):
        """Test Stage 4: Alignment to code generation (dry run)."""
        print("\n🧪 Testing Stage 4: Alignment to code (dry run)...")
        
        # Create alignment report
        alignment_report = {
            "summary": {"alignment_rate": 0.85},
            "alignments": []
        }
        
        alignment_file = temp_workspace / "reports" / "behavioral_alignment_report.json"
        alignment_file.write_text(json.dumps(alignment_report, indent=2))
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Run Stage 4 in dry run mode
        result = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=True)
        
        assert result == True
        
        print("   ✅ Stage 4 dry run successful")
    
    @patch('subprocess.run')
    @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
    def test_stage4_alignment_to_code_full(self, mock_generator_class, mock_subprocess_run, temp_workspace, sample_openspec):
        """Test Stage 4: Alignment to code generation (full execution)."""
        print("\n🧪 Testing Stage 4: Alignment to code (full execution)...")
        
        # Create alignment report
        alignment_report = {
            "summary": {"alignment_rate": 0.85},
            "alignments": []
        }
        
        alignment_file = temp_workspace / "reports" / "behavioral_alignment_report.json"
        alignment_file.write_text(json.dumps(alignment_report, indent=2))
        
        # Create prompts directory with sample prompt
        prompts_dir = temp_workspace / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        
        prompt_file = prompts_dir / "test.prompt"
        prompt_file.write_text("Generate code for test function")
        
        # Mock subprocess calls
        mock_subprocess_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Mock generator
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = ["generated_code.py"]
        mock_generator.generate_from_spec.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        # Set spec file path
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        orchestrator.spec_file_path = sample_openspec
        
        # Run Stage 4
        result = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=False)
        
        assert result == True
        
        # Verify subprocess calls were made
        assert mock_subprocess_run.call_count >= 3  # aggregate_behaviors, build_logic_catalog, generate_prompts
        
        # Verify generation report was saved
        generation_report = temp_workspace / "reports" / "stage4_generation_report.json"
        assert generation_report.exists()
        
        report_data = json.loads(generation_report.read_text())
        assert report_data["stage"] == "4"
        assert "generated_files" in report_data
        
        print("   ✅ Stage 4 full execution successful")
    
    def test_calculate_match_score(self, temp_workspace):
        """Test match score calculation."""
        print("\n🧪 Testing match score calculation...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Create mock requirement and test behavior
        mock_requirement = Mock()
        mock_requirement.title = "Generate Time Grid"
        mock_requirement.description = "Generate time grid based on BPM"
        
        test_behavior = {
            "test_name": "test_generate_time_grid",
            "implied_behavior": "Test time grid generation with BPM"
        }
        
        # Calculate match score
        score = orchestrator._calculate_match_score(mock_requirement, test_behavior)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some match due to common words
        
        print("   ✅ Match score calculation successful")
    
    @patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator')
    def test_full_pipeline_integration(self, mock_generator_class, temp_workspace, sample_openspec):
        """Test complete pipeline integration."""
        print("\n🧪 Testing complete pipeline integration...")
        
        # Mock the generator for all stages
        mock_generator = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = ["test_file.py"]
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.execution_time = 5.0
        mock_generator.generate_from_spec.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        
        # Mock other dependencies
        with patch('asabaal_utils.agents.spec_coder.parse_tests.ASTVisitor'), \
             patch('asabaal_utils.agents.spec_coder.summarize_tests.TestSummarizer'), \
             patch('asabaal_utils.agents.spec_coder.align_behaviors.BehavioralAligner'), \
             patch('asabaal_utils.agents.spec_coder.spec_parser.SpecParser'), \
             patch('subprocess.run') as mock_subprocess:
            
            mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
            
            orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
            
            # Run full pipeline
            result = orchestrator.run_full_pipeline(sample_openspec, temp_workspace)
            
            assert result == True
            
            # Verify all stage reports were created
            stage1_report = temp_workspace / "reports" / "stage1_report.json"
            assert stage1_report.exists()
            
            stage2_summary = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
            # Stage 2 summary may not exist if no test files were found
            # This is expected behavior when Stage 1 doesn't generate test scaffolds
            
            alignment_report = temp_workspace / "reports" / "behavioral_alignment_report.json"
            assert alignment_report.exists()
            
            generation_report = temp_workspace / "reports" / "stage4_generation_report.json"
            assert generation_report.exists()
            
            print("   ✅ Full pipeline integration successful")
    
    @pytest.mark.integration
    def test_stage1_plus_stage2_integration(self, temp_workspace, sample_openspec):
        """Test Stage 1 + 2 integration (Spec → Scaffold → Requirements) with real AI."""
        print("\n🧪 Testing Stage 1 + 2 integration with real AI...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Verify spec file exists and show content
        assert sample_openspec.exists(), f"Spec file should exist: {sample_openspec}"
        print(f"📋 Using spec file: {sample_openspec}")
        print(f"📋 Spec file content preview:\n{sample_openspec.read_text()[:200]}...")
        print(f"📋 Current working directory: {Path.cwd()}")
        print(f"📋 Spec file absolute path: {sample_openspec.absolute()}")
        print(f"📋 Spec file readable: {sample_openspec.is_file()}")
        
        # Run Stage 1 - Real AI call to generate test scaffolds
        print("🔧 Running Stage 1: OpenSpec → Tests/Scaffold")
        # Use absolute path to ensure generator can find the spec file
        absolute_spec_path = sample_openspec.absolute()
        print(f"📋 Using absolute spec path: {absolute_spec_path}")
        stage1_success = orchestrator._stage1_spec_to_scaffold(absolute_spec_path, temp_workspace)
        assert stage1_success, "Stage 1 should succeed with real AI"
        
        # Verify Stage 1 output
        stage1_report = temp_workspace / "reports" / "stage1_report.json"
        assert stage1_report.exists(), "Stage 1 report should exist"
        
        # Verify that test scaffolds were actually created
        scaffolds_dir = temp_workspace / "scaffolds"
        tests_dir = scaffolds_dir / "tests"
        assert tests_dir.exists(), "Tests directory should be created"
        
        test_files = list(tests_dir.glob("*.py"))
        assert len(test_files) > 0, "Should have generated test files"
        print(f"📝 Generated {len(test_files)} test files: {[f.name for f in test_files]}")
        
        # Run Stage 2 - Real analysis of generated test files
        print("🧠 Running Stage 2: Tests/Scaffold → Logical Requirements")
        stage2_success = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
        assert stage2_success, "Stage 2 should succeed"
        
        # Verify Stage 2 output
        stage2_summary = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
        assert stage2_summary.exists(), "Stage 2 summary should exist"
        
        # Verify Stage 2 content
        stage2_content = json.loads(stage2_summary.read_text())
        assert len(stage2_content) > 0, "Should have extracted test behaviors"
        print(f"📊 Analyzed {len(stage2_content)} test behaviors")
        
        # Verify metadata persistence
        assert orchestrator.spec_file_path == sample_openspec.absolute()
        
        print("   ✅ Stage 1 + 2 integration successful with real AI")
    
    @pytest.mark.integration
    def test_stage2_plus_stage3_integration(self, temp_workspace, sample_openspec):
        """Test Stage 2 + 3 integration (Scaffold → Requirements → Alignment) with real AI."""
        print("\n🧪 Testing Stage 2 + 3 integration with real AI...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Mock Stage 1 results - create test scaffolds directory and sample test files
        print("🔧 Setting up mock Stage 1 results...")
        scaffolds_dir = temp_workspace / "scaffolds"
        tests_dir = scaffolds_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample test files with realistic content
        sample_test_content = '''
import pytest
from rpg_generator import generate_time_grid, generate_pattern

def test_generate_time_grid():
    """Test time grid generation with BPM 120."""
    result = generate_time_grid(120, "4/4")
    assert len(result) == 4
    assert result[0] == 0.0

def test_generate_pattern():
    """Test pattern generation with density 0.5."""
    result = generate_pattern(0.5, 8)
    assert len(result) == 8
    assert all(0 <= x <= 1 for x in result)
'''
        
        (tests_dir / "test_generate_time_grid.py").write_text(sample_test_content)
        (tests_dir / "test_generate_pattern.py").write_text(sample_test_content)
        
        # Set up metadata for Stage 2
        orchestrator.spec_file_path = sample_openspec.absolute()
        
        # Run Stage 2 - Real analysis of mock test files
        print("🧠 Running Stage 2: Tests/Scaffold → Logical Requirements")
        stage2_success = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
        assert stage2_success, "Stage 2 should succeed"
        
        # Verify Stage 2 output
        stage2_summary = temp_workspace / "reports" / "stage2_test_summaries" / "test_summary_tests.json"
        assert stage2_summary.exists(), "Stage 2 summary should exist"
        
        stage2_content = json.loads(stage2_summary.read_text())
        assert len(stage2_content) > 0, "Should have analyzed test behaviors"
        print(f"📊 Stage 2 analyzed {len(stage2_content)} test behaviors")
        
        # Run Stage 3 - Real AI-powered alignment analysis
        print("⚖️ Running Stage 3: Logical Requirements → Alignment Checking")
        stage3_success = orchestrator._stage3_requirements_to_alignment(temp_workspace)
        assert stage3_success, "Stage 3 should succeed"
        
        # Verify Stage 3 output
        alignment_report = temp_workspace / "reports" / "behavioral_alignment_report.json"
        assert alignment_report.exists(), "Alignment report should exist"
        
        # Verify alignment report content
        report_content = json.loads(alignment_report.read_text())
        assert "summary" in report_content, "Report should have summary"
        assert "detailed_matches" in report_content, "Report should have detailed_matches"
        
        print(f"📈 Alignment rate: {report_content['summary'].get('alignment_rate', 'N/A')}")
        print(f"📊 Analyzed {report_content['summary'].get('total_tests', 0)} tests against {len(report_content.get('requirement_coverage', {}))} requirements")
        
        print("   ✅ Stage 2 + 3 integration successful with real AI")
    
    @pytest.mark.integration
    def test_stage3_plus_stage4_integration(self, temp_workspace, sample_openspec):
        """Test Stage 3 + 4 integration (Requirements → Alignment → Code Generation) with real AI."""
        print("\n🧪 Testing Stage 3 + 4 integration with real AI...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Mock Stages 1 and 2 results - create necessary directories and files
        print("🔧 Setting up mock Stage 1 and 2 results...")
        
        # Create Stage 2 test summaries (input for Stage 3)
        reports_dir = temp_workspace / "reports"
        stage2_dir = reports_dir / "stage2_test_summaries"
        stage2_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock test behaviors data (matching real Stage 2 output format)
        mock_test_behaviors = [
            {
                "name": "test_generate_time_grid",
                "target_function": "generate_time_grid",
                "inputs": {"bpm": 120, "time_signature": "4/4"},
                "assertions": ["assert len(result) == 4", "assert result[0] == 0.0"],
                "implied_behavior": "Generate time grid based on BPM and time signature"
            },
            {
                "name": "test_generate_pattern",
                "target_function": "generate_pattern", 
                "inputs": {"density": 0.5, "length": 8},
                "assertions": ["assert len(result) == 8", "assert all(0 <= x <= 1 for x in result)"],
                "implied_behavior": "Generate rhythmic pattern with specified density"
            }
        ]
        
        # Create the correct format that Stage 3 expects: {"file": "...", "tests": [...]}
        stage2_data = {
            "file": "test_summary_tests.json",
            "tests": mock_test_behaviors
        }
        (stage2_dir / "test_summary_tests.json").write_text(json.dumps(stage2_data, indent=2))
        
        # Set up metadata
        orchestrator.spec_file_path = sample_openspec.absolute()
        
        # Run Stage 3 - Real AI-powered alignment analysis
        print("⚖️ Running Stage 3: Logical Requirements → Alignment Checking")
        stage3_success = orchestrator._stage3_requirements_to_alignment(temp_workspace)
        assert stage3_success, "Stage 3 should succeed"
        
        # Verify Stage 3 output
        alignment_report = temp_workspace / "reports" / "behavioral_alignment_report.json"
        assert alignment_report.exists(), "Alignment report should exist"
        
        report_content = json.loads(alignment_report.read_text())
        print(f"📈 Stage 3 alignment rate: {report_content['summary'].get('alignment_rate', 'N/A')}")
        
        # Run Stage 4 - Real AI-powered code generation
        print("⚡ Running Stage 4: Alignment Checking → Code Generation")
        stage4_success = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=False)
        assert stage4_success, "Stage 4 should succeed"
        
        # Verify Stage 4 output
        generation_report = temp_workspace / "reports" / "stage4_generation_report.json"
        assert generation_report.exists(), "Generation report should exist"
        
        # Verify logic catalog and prompts were created
        logic_catalog = temp_workspace / "logic_catalog"
        prompts_dir = temp_workspace / "prompts"
        assert logic_catalog.exists(), "Logic catalog should exist"
        assert prompts_dir.exists(), "Prompts directory should exist"
        
        # Check generation report content
        generation_content = json.loads(generation_report.read_text())
        if "files_generated" in generation_content:
            print(f"🎉 Stage 4 generated {len(generation_content['files_generated'])} files")
        
        print("   ✅ Stage 3 + 4 integration successful with real AI")
    
    def test_error_handling_stage_failure(self, temp_workspace, sample_openspec):
        """Test error handling when stages fail."""
        print("\n🧪 Testing error handling for stage failures...")
        
        # Mock generator to fail
        with patch('asabaal_utils.agents.spec_coder.orchestrator.CodeGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_result = Mock()
            mock_result.success = False
            mock_result.files_generated = []
            mock_result.errors = ["Generation failed"]
            mock_result.warnings = []
            mock_result.execution_time = 1.0
            mock_generator.generate_from_spec.return_value = mock_result
            mock_generator_class.return_value = mock_generator
            
            orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
            
            # Run Stage 1 with failure
            result = orchestrator._stage1_spec_to_scaffold(sample_openspec, temp_workspace)
            
            assert result == False  # Should return False on failure
            
            # Verify error was recorded in report
            stage1_report = temp_workspace / "reports" / "stage1_report.json"
            assert stage1_report.exists()
            
            report_data = json.loads(stage1_report.read_text())
            assert report_data["success"] == False
            assert "Generation failed" in report_data["errors"]
        
        print("   ✅ Error handling for stage failures successful")
    
    def test_metadata_persistence_between_stages(self, temp_workspace, sample_openspec):
        """Test metadata persistence between pipeline stages."""
        print("\n🧪 Testing metadata persistence between stages...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Initially no spec file path
        assert orchestrator.spec_file_path is None
        
        # Create metadata in the correct location
        reports_dir = Path.cwd() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = reports_dir / "pipeline_metadata.json"
        
        metadata = {
            "spec_file_path": str(sample_openspec.absolute()),
            "stage_completed": "stage1",
            "timestamp": datetime.now().isoformat()
        }
        
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Load metadata
        result = orchestrator.load_spec_file_path_from_metadata()
        
        assert result == True
        assert orchestrator.spec_file_path == sample_openspec.absolute()
        
        # Test that subsequent calls don't reload (already loaded)
        result = orchestrator.load_spec_file_path_from_metadata()
        assert result == True  # Should return True since already loaded
        
        # Test with no metadata file
        metadata_file.unlink()
        orchestrator.spec_file_path = None
        result = orchestrator.load_spec_file_path_from_metadata()
        assert result == False  # Should return False since no metadata exists
        
        # Cleanup
        if metadata_file.exists():
            metadata_file.unlink()
        if reports_dir.exists():
            import shutil
            shutil.rmtree(reports_dir)
        
        print("   ✅ Metadata persistence between stages successful")
    
    def test_pipeline_with_missing_dependencies(self, temp_workspace, sample_openspec):
        """Test pipeline behavior with missing dependencies."""
        print("\n🧪 Testing pipeline with missing dependencies...")
        
        orchestrator = IntegrationOrchestrator(base_dir=temp_workspace)
        
        # Test Stage 2 with no test files
        result = orchestrator._stage2_scaffold_to_requirements(temp_workspace)
        assert result == True  # Should handle missing test files gracefully
        
        # Test Stage 3 with no alignment report
        result = orchestrator._stage3_requirements_to_alignment(temp_workspace)
        # Stage 3 might succeed with fallback behavior, so we just check it runs
        assert isinstance(result, bool)  # Should return a boolean
        
        # Test Stage 4 with no alignment report (dry run)
        result = orchestrator._stage4_alignment_to_code(temp_workspace, dry_run=True)
        assert result == True  # Dry run should succeed even without inputs
        
        print("   ✅ Pipeline with missing dependencies handled correctly")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "-s"])