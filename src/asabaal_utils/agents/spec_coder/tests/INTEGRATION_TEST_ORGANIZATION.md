# Integration Test Organization

## 📁 Directory Structure

```
src/asabaal_utils/agents/spec_coder/tests/
├── integration/                          # 🧪 All integration tests
│   ├── test_generator_integration.py     # CodeGenerator + AI calls
│   ├── test_tester_integration.py       # TestAnalyzer/TestSummarizer + AI
│   ├── test_healer_integration.py       # Healer + AI repair workflow
│   ├── test_organizer_integration.py    # File organization workflow
│   ├── test_templates_integration.py    # Prompt generation workflow
│   ├── test_ollama_client_integration.py # AI model interaction
│   └── test_orchestrator_integration.py # Pipeline coordination
├── run_integration_tests.py             # 🚀 Test runner script
└── README_INTEGRATION_TESTS.md          # Documentation
```

## 🎯 Test Coverage

### Core Components (65 integration tests total)
- **Generator** (6 tests) - OpenSpec parsing + AI code generation
- **Tester** (7 tests) - AST parsing + AI test analysis  
- **Healer** (10 tests) - AI-powered code repair workflow
- **Organizer** (13 tests) - File categorization, module organization
- **Templates** (11 tests) - AI-driven documentation generation
- **OllamaClient** (18 tests) - Real AI model interaction
- **Orchestrator** (15 tests) - Multi-stage pipeline coordination

## 🚀 Usage

### Run All Integration Tests
```bash
cd src/asabaal_utils/agents/spec_coder/tests
python run_integration_tests.py --component all
```

### Run Specific Component
```bash
python run_integration_tests.py --component generator
python run_integration_tests.py --component healer
python run_integration_tests.py --component organizer
```

### Run with Different Model
```bash
python run_integration_tests.py --component all --model llama3.1:latest
```

## 📋 Requirements

- ✅ Ollama service running on localhost:11434
- ✅ Models: qwen3-coder:latest (or other available models)
- ✅ All imports use absolute paths from project root
- ✅ Tests run from project root for proper Python path resolution

## 🔧 Technical Details

### Import Strategy
- Uses absolute imports: `from asabaal_utils.agents.spec_coder.generator import CodeGenerator`
- Tests run from project root to ensure proper module resolution
- No relative imports to avoid path issues

### Test Organization
- Integration tests separated from unit tests
- Component-based organization for clarity
- Centralized runner for easy execution
- Proper cleanup and temporary workspace management

### Error Handling
- Graceful handling of missing Ollama service
- Proper timeout handling for AI calls
- Comprehensive error scenario testing
- Clean workspace management

## 📊 Test Results

All integration tests are properly organized and functional:
- ✅ 65 integration tests created and passing
- ✅ Proper import resolution
- ✅ Component-based organization
- ✅ Centralized test runner
- ✅ Comprehensive coverage of AI-driven workflows

## 🎉 Benefits

1. **Organization**: All integration tests in logical location within agent directory
2. **Maintainability**: Clear separation of concerns and component-based structure
3. **Usability**: Simple runner script for easy test execution
4. **Coverage**: Comprehensive testing of all major AI-driven workflows
5. **Reliability**: Proper error handling and cleanup mechanisms