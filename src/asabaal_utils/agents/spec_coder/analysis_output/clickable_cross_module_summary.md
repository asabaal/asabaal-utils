# FlowScope Clickable Cross-Module Enhancement

## ✅ **New Feature: Clickable Cross-Module Nodes**

FlowScope now supports **clickable cross-module function nodes** that open detailed module reports when clicked.

### **How It Works**

1. **Cross-Module Detection**: Identifies `module.function` calls between local modules
2. **Visual Highlighting**: Red nodes (#ff6b6b) with thick borders indicate cross-module functions
3. **Enhanced Tooltips**: Show "🔗 CROSS-MODULE FUNCTION" with target/source module info
4. **Click Navigation**: Click red nodes to open the target module's HTML report in a new tab

### **Implementation Details**

#### **Enhanced Scanner (`scanner.py`)**
- Added `cross_module=True`, `target_module`, `source_module` attributes
- Detects cross-module calls within the codebase (excludes external libraries)
- Maps module dependencies and import relationships

#### **Interactive Visualization (`visualize.py`)**
- **Red highlighting** for cross-module functions
- **JavaScript click handlers** for navigation
- **Module mapping** system for linking to reports
- **Enhanced tooltips** with click instructions

#### **CLI Enhancement (`cli.py`)**
- `--module-reports` parameter for specifying module reports directory
- Supports both `scan` and `visualize` commands
- Automatic detection of module report files

### **Usage Examples**

#### **Generate Individual Module Reports**
```bash
# Create module-specific reports
flowscope scan generator.py --output module_reports/generator --visualize
flowscope scan spec_parser.py --output module_reports/spec_parser --visualize
```

#### **Generate Main Analysis with Clickable Nodes**
```bash
# Main analysis with clickable cross-module nodes
flowscope scan orchestrator.py --output main_analysis --visualize --module-reports module_reports/
```

#### **Full Directory Analysis**
```bash
# Complete codebase analysis with cross-module linking
flowscope scan src/ --output full_analysis --visualize --module-reports module_reports/
```

### **Files Generated**

#### **Module Reports Directory**
```
module_reports/
├── generator.html          # Generator module visualization
├── spec_parser.html        # Spec parser module visualization
├── orchestrator.html       # Orchestrator module visualization
└── [other_modules].html    # Additional module reports
```

#### **Main Analysis Files**
```
analysis_output/
├── orchestrator_with_clicks.html     # Main visualization with clickable nodes
├── full_spec_coder_clickable.html  # Full codebase with clickable nodes
└── module_reports/                  # Directory of module-specific reports
```

### **Cross-Module Relationships Identified**

#### **Orchestrator Module**
- `orchestrator._stage4_alignment_to_code` → `generator.generate_from_spec`
- `orchestrator._stage4_alignment_to_code` → `spec_parser.parse_file`

#### **Full Spec-Coder Analysis**
- **28 cross-module calls** detected across 876 functions
- **Key modules**: orchestrator, generator, spec_parser, cli, tester, organizer
- **Test modules** linking to production modules

### **Interactive Features**

#### **Visual Indicators**
- 🔴 **Red nodes**: Cross-module functions (clickable)
- 🔵 **Blue nodes**: Local functions
- 🟢 **Green nodes**: Entry points
- 🟡 **Gold nodes**: Leaf functions

#### **Tooltip Information**
```
Function: generator.generate_from_spec
File: src/asabaal_utils/agents/spec_coder/generator.py
Line: 172
🔗 CROSS-MODULE FUNCTION
Target Module: generator
Called From: orchestrator
💡 Click to open module report
In-degree: 3
Out-degree: 0
```

#### **Click Behavior**
- **Single click**: Opens target module report in new tab
- **Automatic detection**: Finds module report files by name
- **Fallback patterns**: Tries multiple naming conventions
- **Error handling**: Graceful fallback if report not found

### **Technical Implementation**

#### **JavaScript Integration**
```javascript
// Module mapping for click handlers
const moduleMapping = {
    "generator": "module_reports/generator.html",
    "spec_parser": "module_reports/spec_parser.html"
};

// Click event handling
network.on("click", function(params) {
    // Detect cross-module node clicks
    // Open corresponding module report
    window.open(moduleMapping[targetModule], '_blank');
});
```

#### **HTML Enhancement**
- Automatic injection of JavaScript click handlers
- Module mapping generation from file system
- Cross-module node detection and linking

### **Benefits**

1. **Navigation**: Quickly jump between related modules
2. **Understanding**: Visualize module dependencies
3. **Analysis**: Explore cross-module relationships
4. **Debugging**: Trace function calls across modules
5. **Documentation**: Interactive architecture exploration

### **Next Steps**

1. **Module-Level View**: High-level module dependency graph
2. **Impact Analysis**: Track changes in cross-module dependencies
3. **Filtering**: Filter by module type or importance
4. **Export**: Export cross-module relationship data
5. **Integration**: IDE plugin for real-time navigation

## **Summary**

FlowScope now provides **interactive cross-module navigation** with:
- ✅ **Clickable red nodes** for cross-module functions
- ✅ **Automatic module report linking**
- ✅ **Enhanced tooltips** with navigation hints
- ✅ **JavaScript-powered interactivity**
- ✅ **Comprehensive cross-module analysis**

The enhancement transforms static code analysis into an **interactive exploration tool** for understanding module relationships and navigating complex codebases.