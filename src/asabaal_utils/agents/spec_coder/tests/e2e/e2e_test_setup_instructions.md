# 🚀 End-to-End (E2E) Test Setup Instructions for IntegrationOrchestrator

**Goal:** Add an automated end-to-end (E2E) test that validates the *entire AI generation pipeline* — from reading an OpenSpec file through scaffold, alignment, and final code generation — using the `IntegrationOrchestrator`.

---

## ✅ Step-by-Step Tasks

### 1. Create a new test file

At the same level as your other tests (e.g. inside `tests/`), create:

```
tests/test_end_to_end_pipeline.py
```

---

### 2. Add the following content

```python
# tests/test_end_to_end_pipeline.py
import pytest
import tempfile
import shutil
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
description: "A minimal spec to test the full orchestrator pipeline."
requirements:
  - id: "req-001"
    title: "Basic Function"
    description: "Implement a simple function to verify pipeline flow."
    validation:
      - type: "unit"
        target: "test_basic_function"
interfaces:
  - name: "SimpleInterface"
    methods:
      - name: "basic_function"
        parameters:
          - name: "x"
            type: "int"
        returns:
          type: "int"
'''
    spec_file = temp_dir / "e2e_test_spec.yml"
    spec_file.write_text(spec_content)
    return spec_file

@pytest.mark.e2e
def test_full_pipeline_end_to_end(temp_dir, sample_spec_file):
    """Run the full orchestrator pipeline end-to-end."""
    orch = IntegrationOrchestrator(base_dir=temp_dir)
    success = orch.run_full_pipeline(spec_file=sample_spec_file, output_dir=temp_dir / "output")
    assert success, "❌ Full end-to-end pipeline failed"

    # Verify output artifacts exist
    reports_dir = temp_dir / "output" / "reports"
    assert reports_dir.exists(), "Missing reports directory"
    assert any(reports_dir.glob("*.json")), "No report JSON files found"

    print("✅ E2E pipeline executed successfully.")
```

---

### 3. Add a new marker to your `pytest.ini`

Open (or create) `pytest.ini` in the project root and add this section if not already present:

```ini
[pytest]
markers =
    integration: marks tests that call real AI (deselect with '-m "not integration"')
    e2e: marks end-to-end pipeline tests (deselect with '-m "not e2e"')
addopts = -v
```

---

### 4. Run the E2E test

Use one of these commands:

```bash
# Run only the E2E test
pytest -m e2e -v -s

# Run both integration and E2E tests
pytest -m "integration or e2e" -v -s
```

---

### 5. Expected behavior

✅ A temporary environment is created and destroyed automatically.  
✅ The orchestrator runs **all four stages**:
   - Stage 1: Spec → Scaffold  
   - Stage 2: Scaffold → Requirements  
   - Stage 3: Requirements → Alignment  
   - Stage 4: Alignment → Final Code  
✅ Output artifacts are written to `output/reports/` and validated.  
✅ The test prints “E2E pipeline executed successfully.” when everything passes.

---

## 💡 Notes

- This test **uses real AI model calls**, so ensure `ollama serve` is running.  
- You can later expand this with additional assertions for generated file counts, timing, and quality metrics.
- Keep this test minimal and focused on **pipeline health**, not content accuracy.

---

**Author:** ChatGPT — Tandra Hill / Asabaal Ventures Automation Support  
**Purpose:** Enable automated end-to-end validation of the AI code generation pipeline.
