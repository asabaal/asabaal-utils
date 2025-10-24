# 📚 Examples Directory

This directory contains example scripts and demonstrations for the SpecCoder system.

## 🎯 Purpose

These scripts are designed for:
- **Learning**: Understanding how SpecCoder works
- **Demonstration**: Showing capabilities to stakeholders
- **Manual Testing**: Quick validation without pytest overhead
- **Development**: Interactive testing during development

## 📁 Files

### **Integration Test Examples**
- **`run_integration_test.py`** - Simple integration test with real AI model calls
  - Tests basic string utilities generation
  - Validates generated code quality
  - Good for quick manual validation

- **`run_complex_integration_test.py`** - Advanced integration test with complex specifications
  - Uses `complex_test_spec.yml` for sophisticated testing
  - Validates class structures and multiple methods
  - Comprehensive code quality analysis

### **Pipeline Demonstration**
- **`example_runner.py`** - Complete pipeline demonstration
  - Runs full 4-stage SpecCoder pipeline
  - Organizes output by stages for inspection
  - Creates comprehensive summaries
  - Perfect for learning the system

## 🚀 Usage

### Quick Integration Test
```bash
cd examples/
python run_integration_test.py --model qwen3-coder:latest
```

### Complex Integration Test
```bash
cd examples/
python run_complex_integration_test.py --model llama3.1:8b
```

### Full Pipeline Demo
```bash
cd examples/
python example_runner.py
```

## 📋 Requirements

- **Ollama** must be running (`http://localhost:11434`)
- **AI Models** should be available (qwen3-coder:latest, llama3.1:8b, etc.)
- **Python Dependencies** from `requirements.txt`

## 🎓 Learning Path

1. **Start with** `run_integration_test.py` to understand basic generation
2. **Try** `run_complex_integration_test.py` for advanced scenarios
3. **Explore** `example_runner.py` for complete pipeline understanding
4. **Examine** the generated output files to learn the system

## 📊 Output

All scripts generate output in temporary directories (unless specified with `--output-dir`). The example runner creates organized output in `example_output/` with stages clearly separated.

## 🔧 Customization

Each script accepts command-line arguments for:
- **Model selection** (`--model`)
- **Output directory** (`--output-dir`)
- **Configuration options**

## ⚠️ Note

These are **educational/demonstration scripts**, not automated tests. For formal testing, see the `../tests/` directory.