# 🧠 Pytest Integration Test Setup Instructions

**Goal:** Configure `pytest` so that real-AI integration tests can be selectively enabled with a marker called `integration`.

---

## ✅ Step-by-Step Tasks

### 1. Create a configuration file
Create a file at the **root of the repository** named:

```
pytest.ini
```

### 2. Add this content to the file
```ini
[pytest]
markers =
    integration: marks tests that call real AI (deselect with '-m "not integration"')
addopts = -v
```

---

### 3. Update integration test files

For all integration test files (for example, `test_generator_integration.py`):

1. Ensure `import pytest` is at the top.
2. Replace any `pytest.skip("Skip integration test unless explicitly enabled")` lines with:
   ```python
   @pytest.mark.integration
   ```
   directly above test functions that are meant to call real AI models.

Example:

```python
import pytest

@pytest.mark.integration
def test_real_ai_generation_simple_spec(...):
    # This test calls the real Ollama model
    ...
```

---

### 4. Verify setup

Run these commands from the **project root**:

```bash
# Run only fast unit tests (default)
pytest

# Run only integration tests (real AI)
pytest -m integration -v -s
```

---

### 5. Optional: Safe CI/CD configuration

In continuous integration pipelines, ensure only non-AI tests run by default:

```bash
pytest -m "not integration"
```

---

## 💡 Result

With this setup:

| Command | What it does |
|----------|---------------|
| `pytest` | Runs only mocked/unit tests |
| `pytest -m integration` | Runs real AI (Ollama) integration tests |
| `pytest -m "integration or not integration"` | Runs all tests |

---

**Author:** ChatGPT — Tandra Hill / Asabaal Ventures Automation Support  
**Purpose:** To help the coding agent safely manage integration tests that invoke real AI models.
