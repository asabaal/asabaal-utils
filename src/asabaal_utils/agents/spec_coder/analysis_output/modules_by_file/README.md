# Spec-Coder Module Analysis

This directory contains FlowScope analyses broken down by individual Python modules/files in the spec-coder agent.

## Module Breakdown

### Core Components (High Function Count)

**orchestrator** (14 functions)
- Main pipeline orchestration logic
- 119 internal calls, 134 external connections
- Key functions: `main`, `run`, stage methods

**generator** (19 functions) 
- Code generation from specifications
- 93 internal calls, 108 external connections
- Key functions: `generate_from_spec`, `_generate_source_code`

**organizer** (21 functions)
- File organization and structure management
- 85 internal calls, 118 external connections
- Key functions: `main`, `organize_successful_functions`

**test_cli** (34 functions)
- CLI testing utilities
- 36 internal calls, 36 external connections

**test_export_audio** (36 functions)
- Audio export functionality testing
- 6 internal calls, 6 external connections

### Analysis Tools

**test_classify_failures** (33 functions)
- Failure classification and analysis
- 37 internal calls, 37 external connections

**test_orchestrator** (31 functions)
- Orchestrator component testing
- 41 internal calls, 41 external connections

**test_spec_parser** (24 functions)
- Specification parsing tests
- 22 internal calls, 22 external connections

**test_generator** (24 functions)
- Code generator testing
- 37 internal calls, 37 external connections

### Integration Components

**08_integration** (53 functions)
- Integration testing framework
- 169 internal calls, 169 external connections

**test_orchestrator_integration** (21 functions)
- Orchestrator integration tests
- 69 internal calls, 69 external connections

**test_ollama_client_integration** (22 functions)
- Ollama client integration testing
- 25 internal calls, 25 external connections

## Usage

Each module has:
- `{module}_graph.json` - Function call graph data
- `{module}_graph.html` - Interactive visualization
- `{module}_report.txt` - Detailed analysis report

## Key Insights

1. **Test-heavy codebase**: Majority of functions are in test modules
2. **Modular design**: Clear separation between core components and tests
3. **Integration focus**: Extensive integration testing infrastructure
4. **Pipeline architecture**: Clear orchestration → generation → organization flow

## Files Generated

- 70 Python modules analyzed
- Individual graph snapshots and reports for each module
- Interactive HTML visualizations for all modules
- Comprehensive function call mapping for debugging