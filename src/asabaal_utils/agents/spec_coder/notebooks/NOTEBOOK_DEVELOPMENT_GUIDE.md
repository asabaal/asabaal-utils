# SpecCoder Notebook Development Guide

## 🎯 Overview

This guide documents the proper import patterns and development practices for creating and maintaining SpecCoder notebooks that work with the real `asabaal_utils.agents.spec_coder` package structure.

## 📦 Package Import Pattern

### ✅ Correct Import Pattern

All notebooks should use full package imports to ensure they work as if a real user were importing the modules:

```python
# Set up proper path resolution
from pathlib import Path
import sys

# Get the notebook directory and resolve to repo root
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
repo_root = current_dir.parent.parent.parent.parent  # Navigate from notebooks/ to repo root
sys.path.insert(0, str(repo_root))

# Use full package imports (REAL USER EXPERIENCE)
from asabaal_utils.agents.spec_coder.spec_parser import SpecParser
from asabaal_utils.agents.spec_coder.generator import CodeGenerator
from asabaal_utils.agents.spec_coder.cli import main
from asabaal_utils.agents.spec_coder.tester import AnalysisEngine
from asabaal_utils.agents.spec_coder.heal.heal import Healer
from asabaal_utils.agents.spec_coder.organizer import CodeOrganizer
from asabaal_utils.agents.spec_coder.orchestrator import IntegrationOrchestrator
```

### ❌ Incorrect Import Pattern (DO NOT USE)

```python
# AVOID: Local path manipulation
import sys
sys.path.append(str(Path(__file__).parent.parent))
from spec_parser import SpecParser  # This creates artificial import environment
```

## 🏗️ Directory Structure

```
asabaal-utils/src/asabaal_utils/agents/spec_coder/
├── notebooks/
│   ├── module_specific/     # Individual module tutorials
│   ├── stage_specific/      # Pipeline stage demos
│   ├── testing_series/      # Testing workflows
│   └── NOTEBOOK_DEVELOPMENT_GUIDE.md
├── spec_parser.py
├── generator.py
├── cli.py
├── tester.py
└── ... (other modules)
```

## 📝 Notebook Template

Use this template for new notebooks:

```python
#!/usr/bin/env python3
"""
[Notebook Title]

[Description of what this notebook demonstrates]
"""

# === Standard Setup ===
from pathlib import Path
import sys

# === Path Resolution ===
current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
repo_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

# === Package Imports (Real User Experience) ===
from asabaal_utils.agents.spec_coder.[module] import [Class]

# === Notebook Content ===
# Your tutorial/demonstration code here
```

## 🔧 Common Import Patterns

### SpecParser Usage
```python
from asabaal_utils.agents.spec_coder.spec_parser import SpecParser

parser = SpecParser()
spec = parser.parse_file("example_spec.yml")
```

### CodeGenerator Usage
```python
from asabaal_utils.agents.spec_coder.generator import CodeGenerator

generator = CodeGenerator()
result = generator.generate_from_spec(Path("spec.yml"))
```

### CLI Usage
```python
from asabaal_utils.agents.spec_coder.cli import main

# Use CLI programmatically
main(['stage1', 'spec.yml', '-o', 'output/'])
```

## 📋 File Synchronization

The project includes `sync_notebooks.py` to synchronize .py changes back to .ipynb format:

```bash
python sync_notebooks.py
```

This ensures both .py and .ipynb files stay consistent with the proper import patterns.

## ✅ Validation Checklist

Before committing a notebook, ensure:

- [ ] Uses full package imports: `from asabaal_utils.agents.spec_coder.*`
- [ ] Proper path resolution: `repo_root = current_dir.parent.parent.parent.parent`
- [ ] No local path manipulation or sys.path abuse
- [ ] Works when run as Python script
- [ ] Works when converted to Jupyter notebook
- [ ] Demonstrates real user usage patterns
- [ ] Includes proper error handling and logging

## 🚀 Best Practices

1. **Always use full package imports** - this ensures notebooks demonstrate real usage
2. **Include proper path resolution** - makes notebooks runnable from any location
3. **Test both .py and .ipynb versions** - ensure synchronization works
4. **Use descriptive logging** - helps users understand what's happening
5. **Include practical examples** - show real-world usage scenarios
6. **Document expected outputs** - make tutorials self-contained

## 🔄 Migration Notes

When updating existing notebooks:

1. Replace local imports with full package imports
2. Add proper path resolution code
3. Test functionality still works
4. Sync changes back to .ipynb format
5. Update any documentation that references old import patterns

## 📚 Reference Examples

See these notebooks for correct import patterns:
- `01_spec_parser_part1.py` - SpecParser usage
- `02_code_generator_part1.py` - CodeGenerator usage  
- `05_cli_interface_part1.py` - CLI interface usage
- `stage1_spec_to_scaffold.py` - Pipeline stage execution

---

**Remember**: The goal is to create notebooks that work exactly as a real user would experience the SpecCoder package!