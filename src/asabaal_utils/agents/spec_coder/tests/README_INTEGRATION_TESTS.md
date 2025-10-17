# Integration Tests for CodeGenerator

This directory contains integration tests that make **real AI model calls** to validate the actual quality and behavior of the CodeGenerator with Ollama models.

## 🎯 Purpose

Unlike unit tests that use mocks, integration tests:

1. **Validate Prompt Quality**: Test if our prompts actually generate good code
2. **Test Model Behavior**: See how different AI models respond to specifications
3. **Check Output Format**: Verify generated code follows expected patterns
4. **End-to-End Testing**: Test the complete pipeline with real AI responses

## 🚀 Quick Start

### Option 1: Run the Standalone Script

```bash
# Basic test with default model (llama3.1:8b)
python run_integration_test.py

# Test with specific model
python run_integration_test.py --model qwen3-coder:latest

# Save output to permanent directory
python run_integration_test.py --output-dir ./test_output
```

### Option 2: Run with Pytest

```bash
# Run all integration tests (requires Ollama running)
pytest tests/test_generator_integration.py -v -m integration

# Run specific integration test
pytest tests/test_generator_integration.py::TestCodeGeneratorIntegrationManual::test_manual_simple_generation -v -s

# Skip the pytest.skip() calls to force run
pytest tests/test_generator_integration.py -v -s --no-skip
```

## 📋 Prerequisites

1. **Ollama Running**: Make sure Ollama is installed and running
   ```bash
   ollama serve
   ```

2. **Models Available**: At least one of these models should be available:
   ```bash
   ollama list
   # Expected: llama3.1:8b, qwen3-coder:latest, llama3.1:latest, etc.
   ```

3. **Pull Models if Needed**:
   ```bash
   ollama pull llama3.1:8b
   ollama pull qwen3-coder:latest
   ```

## 🧪 Test Types

### 1. Simple Specification Tests
- **File**: `test_generator_integration.py`
- **Class**: `TestCodeGeneratorIntegration`
- **Tests**: Basic calculator, string utilities, etc.
- **Purpose**: Validate core functionality with simple specs

### 2. Complex Specification Tests
- **File**: `test_generator_integration.py`
- **Tests**: Data processing pipelines, multi-class systems
- **Purpose**: Test handling of complex requirements

### 3. Quality Metrics Tests
- **Metrics**: Line count, function count, documentation coverage
- **Checks**: Error handling, type hints, code structure
- **Purpose**: Quantify code quality

### 4. Model Comparison Tests
- **Models**: Test multiple models with same specification
- **Metrics**: Speed, output quality, success rate
- **Purpose**: Find best performing model

## 📊 What Gets Tested

### Code Quality Metrics
- ✅ Function count matches requirements
- ✅ Documentation (docstrings) present
- ✅ Error handling implemented
- ✅ Type hints used
- ✅ Import statements present
- ✅ Main guard (`if __name__ == "__main__"`)

### Functional Requirements
- ✅ All required functions/methods generated
- ✅ Correct function signatures
- ✅ Class structure matches interfaces
- ✅ Acceptance criteria addressed

### Output Structure
- ✅ Files created in correct locations
- ✅ Proper naming conventions
- ✅ File permissions set correctly
- ✅ Multiple file types generated (source, tests, docs, CI)

## 🔧 Customization

### Adding New Test Specifications

1. Create a new YAML specification in the test
2. Add requirements with validation criteria
3. Define interfaces if needed
4. Add quality assertions

Example:
```python
@pytest.fixture
def my_custom_spec(self, temp_dir):
    spec_content = """
spec_id: "my-spec-001"
title: "My Custom Component"
version: "1.0.0"
requirements:
  - id: "req-001"
    title: "My Function"
    description: "Function that does something"
    validation:
      - type: "unit"
        target: "test_my_function"
"""
    spec_file = temp_dir / "my_spec.yml"
    spec_file.write_text(spec_content)
    return spec_file
```

### Testing Different Models

```python
@pytest.fixture
def custom_config(self, temp_dir):
    config = {
        'model': {
            'model': 'your-model-name',
            'temperature': 0.3,
            'max_tokens': 2000
        },
        'generation': {'overwrite': True}
    }
    config_file = temp_dir / "config.yaml"
    config_file.write_text(yaml.dump(config))
    return config_file
```

## 📈 Example Output

```
🚀 Running integration test with model: llama3.1:8b
============================================================
📋 Test specification: /tmp/tmp123/spec.yml
⚙️  Configuration: /tmp/tmp123/config.yaml
📁 Output directory: /tmp/tmp123/output

🤖 Starting AI generation...
⏱️  Generation completed in 23.45 seconds

✅ Generation successful!
📄 Files generated: 6
   📄 /tmp/tmp123/output/scaffolds/src/string_utils.py
      📊 Lines: 45, Functions: 2
      📝 Has docstrings: True
      🔧 Has imports: True
      🛡️  Has error handling: True
      📝 Has type hints: True
      📖 Code preview:
         1: """String utilities module."""
         2: 
         3: from typing import Union
         4: 
         5: 
         6: class StringUtils:
         7:     """Utility class for string operations."""
         8: 
         9:     @staticmethod
        10:     def reverse_string(text: str) -> str:
        ...

🔍 Validating generated code against requirements...
   ✅ Found function: reverse_string
   ✅ Found function: capitalize_words
   ✅ Found class: StringUtils

🎉 Integration test completed!
```

## 🐛 Troubleshooting

### Common Issues

1. **"Model not found" Error**
   ```bash
   ollama pull llama3.1:8b
   ```

2. **"Connection failed" Error**
   ```bash
   # Make sure Ollama is running
   ollama serve
   ```

3. **Tests Skip Automatically**
   - Integration tests are skipped by default
   - Use `--no-skip` flag or remove `pytest.skip()` calls

4. **Slow Performance**
   - Use smaller models (`llama3.1:8b` instead of `qwen3:30b`)
   - Reduce `max_tokens` in config
   - Use simpler specifications

### Debug Mode

```bash
# Run with verbose output
python run_integration_test.py --model llama3.1:8b --output-dir ./debug_output

# Run pytest with maximum verbosity
pytest tests/test_generator_integration.py -v -s --tb=long
```

## 📝 Best Practices

1. **Run Before Major Changes**: Validate that prompts still work
2. **Test Multiple Models**: Ensure compatibility across models
3. **Monitor Quality**: Track code quality metrics over time
4. **Save Outputs**: Keep examples of good and bad generations
5. **Update Regularly**: Add new test cases as features evolve

## 🔄 Continuous Integration

These integration tests are **too slow for CI/CD** and should be run:

- Before releases
- During development when changing prompts
- When updating model configurations
- As part of manual testing procedures

To exclude from CI:
```bash
# Run only unit tests
pytest tests/ -v -m "not integration"

# Run only fast tests
pytest tests/ -v -m "not slow"
```