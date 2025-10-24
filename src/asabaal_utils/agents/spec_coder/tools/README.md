# 🛠️ Tools Directory

This directory contains utility scripts and analysis tools for the SpecCoder system.

## 🎯 Purpose

These tools are designed for:
- **Analysis**: Deep analysis of test files and generated code
- **Utilities**: Helper scripts for development and maintenance
- **Processing**: Batch processing of test results and outputs
- **Investigation**: Debugging and investigation utilities

## 📁 Files

### **Test Analysis Tools**
- **`analyze_tests.py`** - Main test analysis orchestrator
  - Combines AST parsing and AI summarization
  - Coordinates test file analysis workflow
  - Batch processing of test directories
  - Generates comprehensive behavior summaries

- **`summarize_tests.py`** - AI-powered test behavior summarization
  - Uses Ollama to generate natural language descriptions
  - Context-aware analysis (spec/source files)
  - Structured test summary generation
  - Real AI model integration

### **Run Analysis Tools**
- **`analyze_all_runs.py`** - Batch analysis of multiple test runs
  - Processes multiple test result directories
  - Generates comparative analysis reports
  - Identifies patterns across runs
  - Statistical analysis of test performance

- **`run_comparison_analysis.py`** - Comparative analysis between runs
  - Compares different test execution results
  - Identifies regressions and improvements
  - Performance metrics comparison
  - Trend analysis over time

## 🚀 Usage

### Test File Analysis
```bash
cd tools/
python analyze_tests.py --test-dir ../tests/unit/ --output-dir analysis_output/
```

### AI Test Summarization
```bash
cd tools/
python summarize_tests.py --test-file test_example.py --model qwen3-coder:latest
```

### Batch Run Analysis
```bash
cd tools/
python analyze_all_runs.py --runs-dir ../reports/ --output analysis_report.json
```

### Comparison Analysis
```bash
cd tools/
python run_comparison_analysis.py --run1 ../reports/20251015-1400/ --run2 ../reports/20251015-1500/
```

## 📋 Requirements

- **Ollama** must be running for AI-powered tools (`http://localhost:11434`)
- **Python Dependencies** from `requirements.txt`
- **Test Results** directories for analysis tools
- **Generated Code** files for analysis

## 🔧 Configuration

Most tools accept command-line arguments:
- **Input directories** (`--test-dir`, `--runs-dir`)
- **Output files** (`--output`, `--output-dir`)
- **AI models** (`--model`, `--temperature`)
- **Analysis options** (`--verbose`, `--format`)

## 📊 Output Formats

Tools generate various output formats:
- **JSON** for structured data
- **Markdown** for reports
- **CSV** for statistical analysis
- **HTML** for visualization

## 🔍 Integration with Tests

These tools complement the formal test suite:
- **Pre-processing**: Prepare test data for analysis
- **Post-processing**: Analyze test results after execution
- **Investigation**: Debug failing tests and issues
- **Reporting**: Generate comprehensive test reports

## ⚠️ Note

These are **utility tools**, not automated tests. They're designed for manual analysis, investigation, and development support. For formal testing, see the `../tests/` directory.