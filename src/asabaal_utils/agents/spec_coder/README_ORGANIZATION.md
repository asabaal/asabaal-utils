# 📁 SpecCoder Directory Organization

This document explains the reorganized directory structure to eliminate confusion between different types of scripts and tests.

## 🎯 Overview

The SpecCoder system has been reorganized into clear, purpose-driven directories:

```
spec_coder/
├── 📚 examples/          # Educational and demonstration scripts
├── 🛠️ tools/            # Analysis and utility scripts  
├── 🧪 tests/            # Formal test suite (unit + integration)
├── 🔧 healer/           # Code healing and repair modules
├── 📋 config/           # Configuration files
├── 📖 docs/             # Documentation
├── 📓 notebooks/        # Jupyter notebooks for learning
└── 🎯 [core modules]    # Main implementation files
```

---

## 📚 Examples Directory

**Purpose**: Educational scripts and demonstrations for learning and manual testing

### When to Use:
- **Learning** how SpecCoder works
- **Demonstrating** capabilities to stakeholders  
- **Manual testing** during development
- **Quick validation** without pytest overhead

### Files:
- `run_integration_test.py` - Simple integration test with real AI
- `run_complex_integration_test.py` - Advanced integration testing
- `example_runner.py` - Complete pipeline demonstration

### Usage:
```bash
cd examples/
python run_integration_test.py --model qwen3-coder:latest
python example_runner.py
```

---

## 🛠️ Tools Directory  

**Purpose**: Analysis utilities and development support tools

### When to Use:
- **Deep analysis** of test files and generated code
- **Batch processing** of test results
- **Investigation** and debugging
- **Development support** and maintenance

### Files:
- `analyze_tests.py` - Test analysis orchestrator
- `summarize_tests.py` - AI-powered test summarization
- `analyze_all_runs.py` - Batch run analysis
- `run_comparison_analysis.py` - Comparative analysis

### Usage:
```bash
cd tools/
python analyze_tests.py --test-dir ../tests/unit/
python summarize_tests.py --test-file test_example.py
```

---

## 🧪 Tests Directory

**Purpose**: Formal automated test suite for CI/CD and regression protection

### When to Use:
- **Automated testing** in CI/CD pipelines
- **Regression protection** during development
- **Quality assurance** before releases
- **Comprehensive validation** of system behavior

### Structure:
```
tests/
├── unit/                 # Unit tests for individual modules
├── integration/          # Integration tests for component interaction
├── conftest.py          # Shared pytest configuration
└── README_*.md          # Test documentation
```

### Usage:
```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run with coverage
pytest tests/ --cov=asabaal_utils.agents.spec_coder
```

---

## 🎯 Core Modules

**Purpose**: Main implementation files that constitute the SpecCoder system

### Key Components:
- `generator.py` - AI-powered code generation
- `orchestrator.py` - Pipeline orchestration and coordination
- `cli.py` - Command-line interface
- `tester.py` - Test execution and validation
- `healer/` - Code repair and healing modules
- `templates.py` - Prompt templates
- `ollama_client.py` - AI model interface

---

## 🔄 Migration Guide

### Before Organization:
```
spec_coder/
├── run_integration_test.py      ❌ Confusing location
├── example_runner.py            ❌ Mixed with core modules  
├── analyze_tests.py             ❌ Unclear purpose
├── summarize_tests.py           ❌ Scattered utilities
├── test_*.py                    ❌ Mixed types of tests
└── [core modules]               ✅ Clear
```

### After Organization:
```
spec_coder/
├── examples/                    ✅ Educational scripts
│   ├── run_integration_test.py
│   ├── run_complex_integration_test.py  
│   └── example_runner.py
├── tools/                       ✅ Analysis utilities
│   ├── analyze_tests.py
│   ├── summarize_tests.py
│   └── analyze_all_runs.py
├── tests/                       ✅ Formal test suite
│   ├── unit/
│   └── integration/
└── [core modules]               ✅ Clear separation
```

---

## 🚀 Quick Start Guide

### For Learning:
```bash
cd examples/
python example_runner.py    # Full pipeline demo
python run_integration_test.py  # Quick test
```

### For Development:
```bash
cd tools/
python analyze_tests.py --test-dir ../tests/unit/  # Analyze tests
```

### For Testing:
```bash
pytest tests/unit/          # Run unit tests
pytest tests/integration/   # Run integration tests
```

---

## 📋 Decision Matrix

| **Need** | **Use Directory** | **Why** |
|----------|-------------------|---------|
| Learn SpecCoder | `examples/` | Educational, step-by-step |
| Demo to stakeholders | `examples/` | Visual, impressive output |
| Quick manual test | `examples/` | No pytest setup needed |
| Analyze test results | `tools/` | Deep analysis capabilities |
| Debug failing tests | `tools/` | Investigation utilities |
| Automated testing | `tests/` | CI/CD ready, comprehensive |
| Regression protection | `tests/` | Formal test framework |

---

## 🎓 Benefits of Organization

### ✅ **Clear Purpose Separation**
- Educational vs. production tools
- Manual vs. automated testing
- Analysis vs. execution

### ✅ **Reduced Confusion**  
- No more wondering what script does what
- Clear usage patterns for each directory
- Better discoverability

### ✅ **Improved Maintainability**
- Related files grouped together
- Easier to find and update code
- Clear ownership and responsibility

### ✅ **Better Developer Experience**
- Intuitive directory structure
- Clear documentation for each area
- Easy onboarding for new developers

---

## 🔧 Future Maintenance

When adding new files, ask:

1. **Is it for learning/demonstration?** → `examples/`
2. **Is it for analysis/utilities?** → `tools/`  
3. **Is it for automated testing?** → `tests/`
4. **Is it core functionality?** → Root directory

This structure ensures the codebase remains organized and confusion-free as it grows.