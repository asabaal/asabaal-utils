# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Install for development: `pip install -e .`
- Run all tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_file.py::TestClass::test_method`
- Run video processing CLI: `create-summary input.mp4 output.mp4`

## Code Style Guidelines
### Imports
- Order: stdlib → third-party → local modules
- Group with blank lines between categories
- Use aliases for common libraries (import numpy as np)

### Type Annotations
- Use typing module (List, Dict, Optional, Union, etc.)
- Annotate function parameters and return values
- Type class attributes

### Docstrings
- Google style format with Args, Returns, Raises sections
- Document parameter units (seconds, percentage, etc.)

### Error Handling
- Use specific exceptions in try/except blocks
- Clean up resources in finally blocks
- Log errors with context information

### Naming/Organization
- snake_case for functions/variables, PascalCase for classes
- Use dataclasses for structured data
- Create Enum classes for related constants
- Memory-adaptive processing for large video files