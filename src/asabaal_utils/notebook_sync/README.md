# Notebook Sync CLI

A command-line tool for bidirectional synchronization of Jupyter notebooks (.ipynb) and Python scripts (.py) using jupytext.

## Features

- **Bidirectional Sync**: Automatically syncs from newer to older file based on modification times
- **Smart Detection**: Only syncs when files are out of sync
- **Flexible Targeting**: Sync all notebooks or specific ones
- **Rich Output**: Beautiful progress indicators and detailed summaries
- **Timestamp Preservation**: Maintains consistent timestamps to prevent unnecessary re-syncs

## Installation

The CLI is included in the `asabaal-utils` package. Install it with:

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# Sync all notebooks in a directory
sync-notebooks --all /path/to/notebooks

# Sync specific notebooks
sync-notebooks /path/to/notebooks --notebook notebook1 --notebook notebook2

# Show detailed sync information
sync-notebooks --all /path/to/notebooks --verbose
```

### Command Options

- `DIRECTORY`: Path to the directory containing notebooks (required)
- `--all`: Sync all notebook pairs in the directory
- `--notebook, -n`: Sync specific notebook(s) by name (without extension). Can be used multiple times
- `--verbose, -v`: Show detailed sync information
- `--help`: Show help message

### Examples

```bash
# Sync all notebooks in the current directory
sync-notebooks --all .

# Sync specific notebooks
sync-notebooks . --notebook analysis --notebook data_processing

# Sync with verbose output
sync-notebooks --all ./notebooks --verbose
```

## How It Works

1. **File Discovery**: The tool scans the directory for .py and .ipynb files
2. **Pairing**: Files with the same base name are paired (e.g., `notebook.py` ↔ `notebook.ipynb`)
3. **Comparison**: Modification times are compared to determine which file is newer
4. **Sync Direction**: The newer file is synced to the older file using jupytext
5. **Timestamp Sync**: After successful sync, timestamps are synchronized to prevent re-syncing

## Sync Behavior

- If only `.py` exists: Creates corresponding `.ipynb`
- If only `.ipynb` exists: Creates corresponding `.py`
- If both exist: Syncs from newer to older file
- If timestamps match: No sync needed (already in sync)

## Requirements

- `jupytext` >= 1.14.0 (automatically installed with asabaal-utils)

## Error Handling

The tool gracefully handles:
- Missing jupytext installation
- File permission issues
- Invalid notebook formats
- Network or filesystem errors

All errors are reported with clear messages and the sync continues for other files.