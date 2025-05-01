# Asabaal Video Utilities Documentation

This directory contains the documentation for the Asabaal Video Utilities package.

## Building the Documentation

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material](https://squidfunk.github.io/mkdocs-material/) theme and the [MkDocstrings](https://mkdocstrings.github.io/) plugin for automatic API documentation generation.

To build the documentation:

```bash
# Install requirements
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python

# Build the documentation
mkdocs build

# Serve the documentation locally
mkdocs serve
```

Alternatively, you can use the provided build script:

```bash
# Make the script executable
chmod +x build_docs.sh

# Build the documentation
./build_docs.sh

# Build and serve locally
./build_docs.sh --serve

# Build and deploy to GitHub Pages
./build_docs.sh --deploy

# Treat warnings as errors (useful for CI)
./build_docs.sh --warnings-as-errors
```

## Documentation Structure

- `index.md`: Main documentation page
- `installation.md`: Installation instructions
- `quickstart.md`: Getting started guide
- `cli/`: CLI command documentation
- `api/`: Python API documentation
- `guides/`: In-depth guides
- `examples/`: Example workflows
- `contributing.md`: Guide for contributors

## Adding New Documentation

When adding new documentation:

1. Create the Markdown file in the appropriate directory
2. Update the `nav` section in `mkdocs.yml` to include the new file
3. Build the documentation to check for any issues
4. If adding API documentation for a new module, follow the existing pattern in the `api/` directory

## Style Guidelines

- Use headers (##, ###, etc.) to structure your documentation
- Include code examples using fenced code blocks with language specification
- Use tables for parameter descriptions
- Include links to related documentation
- Use admonitions for notes, warnings, and tips

Example admonition:
```markdown
!!! note "Note"
    This is a note admonition.

!!! warning "Warning"
    This is a warning admonition.

!!! tip "Tip"
    This is a tip admonition.
```