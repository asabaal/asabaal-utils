# 🤖 spec-coder Integration Migration Brief

## 1 | Purpose

This document defines the migration plan for integrating the **spec-driven autonomous coding agent** (the full pipeline we’ve built) into the `asabaal-utils` repository as a new agent: **spec_coder**.

The `spec_coder` agent can autonomously:
- parse OpenSpec specifications,
- generate structured code,
- test and validate it,
- self-patch errors, and
- reorganize finalized modules.

The **music project** remains the canonical test case but is not part of the agent’s core logic.

---

## 2 | Target Repository Layout

```
asabaal-utils/
├── agents/
│   ├── pr_analyzer/
│   ├── data_cleaner/
│   ├── spec_coder/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── orchestrator.py
│   │   ├── generator.py
│   │   ├── tester.py
│   │   ├── healer.py
│   │   ├── organizer.py
│   │   ├── integration.py
│   │   └── prompts/
│   │       ├── base_prompts.md
│   │       ├── example_specs.md
│   │       └── schema_templates.yaml
│   └── __init__.py
├── core/
│   ├── agent_base.py
│   ├── llm_connectors.py
│   ├── repo_tools.py
│   ├── utils.py
│   └── __init__.py
├── scripts/
│   ├── sync_agents.py
│   ├── update_prompts.py
│   └── install_dev_env.py
├── pyproject.toml
└── README.md
```

---

## 3 | CLI Specification

**Command:** `spec-coder`

### Subcommands
| Command | Module | Description |
|----------|---------|-------------|
| `generate` | `generator.py` | Parses specs and generates initial code |
| `test` | `tester.py` | Runs test suites and summarizes results |
| `heal` | `healer.py` | Applies AI-guided repairs to failing tests |
| `organize` | `organizer.py` | Reorganizes verified code into structured layout |
| `full-run` | `orchestrator.py` | Executes the complete pipeline end-to-end |

### Example Usage
```bash
spec-coder generate path/to/spec
spec-coder test
spec-coder heal
spec-coder organize
spec-coder full-run path/to/spec
```

---

## 4 | Integration Hooks

### Agent Registration
```python
# in agents/__init__.py
from .spec_coder import Orchestrator as SpecCoder
```

### Shared Core Modules
- **agent_base**: Lifecycle, error management, and logging
- **llm_connectors**: Connects to OLAMA or external LLM APIs
- **repo_tools**: Handles file operations and commit integration
- **utils**: Provides shared helpers and output formatting

---

## 5 | Module Responsibilities

| Module | Purpose |
|---------|----------|
| **generator.py** | Reads OpenSpec files and generates Python code |
| **tester.py** | Runs pytest, collects and logs test results |
| **healer.py** | Performs AI-guided code patching and validation |
| **organizer.py** | Consolidates tested code into a stable structure |
| **integration.py** | Maintains behavioral alignment and summaries |
| **orchestrator.py** | Coordinates the entire workflow |
| **cli.py** | Exposes a clean CLI command interface |

---

## 6 | pyproject.toml Configuration

Add to `[project.scripts]` section:

```toml
[project.scripts]
spec-coder = "agents.spec_coder.cli:main"
```

After installation, verify with:
```bash
spec-coder --help
```

Expected output:
```
Usage: spec-coder [COMMAND]

Commands:
  generate     Generate code from spec
  test         Run automated tests
  heal         Repair failing tests
  organize     Restructure code
  full-run     Run the entire pipeline
```

---

## 7 | Implementation Phases

| Phase | Task | Description |
|--------|------|-------------|
| 1 | **Create Folder Structure** | Scaffold `agents/spec_coder/` and required files |
| 2 | **Migrate Layer Code** | Copy working modules (generation, testing, healing, organizing) |
| 3 | **Implement CLI** | Add `cli.py` using `argparse` or `typer` |
| 4 | **Register Entry Point** | Update `pyproject.toml` with the CLI script entry |
| 5 | **Run Validation** | Execute full pipeline to confirm proper operation |
| 6 | **Commit & Tag** | Commit as `v0.1.0-spec-coder` |

---

## 8 | Validation Steps

Run:
```bash
spec-coder full-run path/to/specs/
```
Confirm:
- Specs parsed successfully
- Code generated correctly
- Tests executed
- Failing tests healed (if enabled)
- Final code organized into `/src`
- Logs and summary reports created

---

## 9 | Deliverables

| File | Description |
|------|-------------|
| `/agents/spec_coder/` | New autonomous coding agent |
| `cli.py` | CLI entrypoint |
| `generator.py` | Code generation logic |
| `tester.py` | Test execution and reporting |
| `healer.py` | AI repair engine |
| `organizer.py` | Code organization system |
| `integration.py` | Behavioral management |
| `orchestrator.py` | Full pipeline coordination |
| `pyproject.toml` | Updated CLI registration |
| ✅ | `spec-coder` command fully operational |

---

## 10 | Future Improvements

- Integrate git-aware patching system for commit diffs  
- Enable project-type recognition (ML, web, data, etc.)  
- Add local model adapters (Ollama, LM Studio, vLLM) for offline runs  
- Support pipeline visualization dashboard
