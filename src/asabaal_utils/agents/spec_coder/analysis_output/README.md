# FlowScope Analysis Output

## 📁 Directory Structure

```
analysis_output/
├── README.md                           # This file
├── modules/                            # Individual module analyses
│   ├── aggregate_behaviors.html         # Aggregate behaviors module
│   ├── align_behaviors.html             # Align behaviors module
│   ├── analyze_all_runs.html            # Analyze runs module
│   ├── analyze_tests.html               # Test analysis module
│   ├── build_logic_catalog.html         # Logic catalog builder
│   ├── cli.html                       # CLI interface module
│   ├── compare_behaviors.html           # Compare behaviors module
│   ├── generate_prompts.html            # Prompt generator module
│   ├── generator.html                  # Code generator module
│   ├── ollama_client.html              # Ollama client module
│   ├── orchestrator.html               # Main orchestrator module
│   ├── organizer.html                  # Code organizer module
│   ├── parse_tests.html                # Test parser module
│   ├── pipeline_notebook.html          # Pipeline notebook module
│   ├── run_comparison_analysis.html     # Comparison analysis module
│   ├── spec_parser.html               # Specification parser module
│   ├── summarize_tests.html            # Test summarizer module
│   ├── templates.html                 # Template module
│   ├── tester.html                    # Test runner module
│   └── update_report.html             # Report updater module
└── reports/                           # Comprehensive analyses
    ├── full_spec_coder_clickable       # Full codebase analysis data
    └── full_spec_coder_clickable.html # Interactive visualization with clickable cross-module nodes
```

## 🚀 Key Features

### **Interactive Cross-Module Navigation**
- **Red nodes** indicate cross-module function calls
- **Click red nodes** to open the target module's detailed report
- **Enhanced tooltips** show source/target module information

### **Module-Level Analysis**
Each module has its own interactive HTML visualization showing:
- All functions within the module
- Internal function calls
- Function metadata (file location, line numbers)
- Entry points and leaf functions

### **Comprehensive Codebase View**
The main `full_spec_coder_clickable.html` provides:
- **876 functions** across all modules
- **28 cross-module calls** identified
- **Clickable navigation** between modules
- **Filtered analysis** (no external library noise)

## 📊 Analysis Summary

### **Modules Analyzed**: 20 implementation modules
### **Total Functions**: 876
### **Cross-Module Calls**: 28
### **External Dependencies**: Filtered out

### **Key Cross-Module Relationships**
1. **orchestrator** → **generator** (`generate_from_spec`)
2. **orchestrator** → **spec_parser** (`parse_file`)
3. **pipeline_notebook** → **orchestrator** (stage functions)
4. **cli** → **organizer**, **tester**, **orchestrator** (main functions)

## 🔍 Usage

### **View Individual Module Analysis**
Open any `modules/*.html` file to see detailed function analysis for that specific module.

### **Explore Cross-Module Relationships**
Open `reports/full_spec_coder_clickable.html` and:
1. Look for **red nodes** (cross-module functions)
2. **Click red nodes** to jump to the target module's report
3. Use tooltips to see module relationship details

### **Navigation Tips**
- **Blue nodes**: Local functions within the same module
- **Red nodes**: Cross-module functions (clickable)
- **Green nodes**: Entry points (no incoming calls)
- **Gold nodes**: Leaf functions (no outgoing calls)

## 🛠️ Technical Details

### **FlowScope Features Used**
- **Cross-module detection**: Identifies `module.function` calls between local modules
- **External filtering**: Excludes built-ins, stdlib, and third-party packages
- **Interactive visualization**: Pyvis-based HTML with JavaScript click handlers
- **Module linking**: Automatic detection and linking of module reports

### **Analysis Scope**
- **Included**: All `.py` files in `src/asabaal_utils/agents/spec_coder/`
- **Excluded**: Tests, notebooks, examples, and `__pycache__`
- **Focused**: Application-specific code only (no external noise)

## 📈 Insights

### **Architecture Patterns**
- **Orchestrator pattern**: Central coordination module
- **Pipeline stages**: Sequential processing modules
- **Utility modules**: Supporting functionality (cli, templates, etc.)
- **Analysis modules**: Test and behavior analysis tools

### **Module Coupling**
- **Low coupling**: Most modules are self-contained
- **Key dependencies**: orchestrator → generator/spec_parser
- **Clean separation**: Well-defined module boundaries

This analysis provides a comprehensive, interactive view of the spec-coder codebase architecture with easy navigation between related modules.