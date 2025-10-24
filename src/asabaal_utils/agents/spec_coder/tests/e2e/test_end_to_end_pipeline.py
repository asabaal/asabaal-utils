# tests/test_end_to_end_pipeline.py
import pytest
import tempfile
import shutil
import json
import logging
from pathlib import Path
from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator

@pytest.fixture
def temp_dir():
    """Create a temporary directory for end-to-end pipeline output."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_spec_file(temp_dir):
    """Create a lightweight OpenSpec YAML file for E2E testing."""
    spec_content = '''
spec_id: "e2e-001"
title: "E2E Pipeline Sanity Test"
version: "1.0.0"
description: "A minimal spec to test the full orchestrator pipeline with only one function."
requirements:
  - id: "req-001"
    title: "Basic Function"
    description: "Implement a function that takes an integer and returns the same integer multiplied by 2. This is the ONLY function that should be implemented."
    validation:
      - type: "unit"
        file: "test_basic_function.py"
        target: "test_basic_function"
        description: "Test that basic_function multiplies input by 2"
        examples:
          - input: {"x": 5}
            output: 10
          - input: {"x": 0}
            output: 0
    interfaces:
      - name: "basic_function"
        description: "Multiplies the input integer by 2 and returns the result"
        parameters:
          - name: "x"
            type: "int"
            description: "The integer to multiply by 2"
        return_type: "int"
'''
    spec_file = temp_dir / "e2e_test_spec.yml"
    spec_file.write_text(spec_content)
    return spec_file

@pytest.mark.e2e
def test_full_pipeline_end_to_end(temp_dir, sample_spec_file):
    """Run the full orchestrator pipeline end-to-end."""
    # Setup debug logging to a persistent location outside temp_dir
    debug_log = Path("/tmp/e2e_test_debug.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(debug_log),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.debug(f"=== E2E TEST START ===")
    logger.debug(f"Temp dir: {temp_dir}")
    logger.debug(f"Temp dir contents before test: {list(temp_dir.iterdir())}")
    logger.debug(f"Sample spec file: {sample_spec_file}")
    logger.debug(f"Sample spec file exists: {sample_spec_file.exists()}")
    
    orch = IntegrationOrchestrator(base_dir=temp_dir)
    success = orch.run_full_pipeline(spec_file=sample_spec_file, output_dir=temp_dir / "output")
    assert success, "❌ Full end-to-end pipeline failed"

    # Verify output artifacts exist
    reports_dir = temp_dir / "output" / "reports"
    assert reports_dir.exists(), "Missing reports directory"
    assert any(reports_dir.glob("*.json")), "No report JSON files found"

    # Verify alignment rate is above threshold (not 0%)
    alignment_report_file = reports_dir / "behavioral_alignment_report.json"
    if alignment_report_file.exists():
        with open(alignment_report_file, 'r') as f:
            alignment_data = json.load(f)
        alignment_rate = alignment_data.get('summary', {}).get('alignment_rate', 0)
        assert alignment_rate > 0, f"❌ Alignment rate is {alignment_rate:.2%}, expected > 0%"
        print(f"✅ Alignment rate: {alignment_rate:.2%}")

    print("✅ E2E pipeline executed successfully.")