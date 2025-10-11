# CLI Commands Overview

Asabaal Video Utilities provides a set of powerful command-line tools for video processing, analysis, and enhancement. Each tool is designed to perform a specific function and can be used independently or as part of a workflow.

## Available Commands

| Command | Description |
|---------|-------------|
| [`remove-silence`](remove-silence.md) | Detects and removes silent segments from videos |
| [`analyze-transcript`](analyze-transcript.md) | Analyzes video transcripts to identify topics and optimal clip points |
| [`generate-thumbnails`](generate-thumbnails.md) | Creates quality-scored thumbnail candidates from videos |
| [`analyze-colors`](analyze-colors.md) | Extracts color palettes and analyzes color themes in videos |
| [`detect-jump-cuts`](detect-jump-cuts.md) | Detects and optionally smooths jump cuts in videos |
| [`create-summary`](create-summary.md) | Creates content-aware video summaries with different style options |
| [`extract-clips`](extract-clips.md) | Extracts clips from videos based on transcript analysis |

## Common Parameters

All CLI commands share some common parameters for consistency:

| Parameter | Description |
|-----------|-------------|
| `--verbose` | Increase output verbosity |
| `--quiet` | Suppress all output except errors |
| `--log-file FILE` | Log output to specified file instead of stdout |
| `--version` | Show version information and exit |
| `--help` | Show help message and exit |

## Memory Management Parameters

Many commands that process video files support memory management parameters:

| Parameter | Description |
|-----------|-------------|
| `--chunk-size SIZE` | Process video in chunks of SIZE MB (default varies by command) |
| `--max-memory SIZE` | Limit memory usage to SIZE MB (default: 75% of system RAM) |
| `--temp-dir DIR` | Directory to store temporary files (default: system temp directory) |

## Usage Examples

### Basic Command Structure

Most commands follow a similar structure:

```bash
command-name input_file [output_file] [options]
```

### Chaining Commands

Commands can be chained together using shell pipes or by saving intermediate results:

```bash
# Process video in multiple stages
remove-silence input.mp4 temp.mp4
extract-clips temp.mp4 clips/ --transcript input.srt
```

### Using JSON Configuration

Some commands support loading options from a JSON configuration file:

```bash
# Using a config file
analyze-transcript input.mp4 --config my_config.json
```

Example configuration file (`my_config.json`):
```json
{
  "min_clip_length": 5,
  "max_clip_length": 30,
  "topic_change_threshold": 0.7,
  "output": "analysis_results.json"
}
```

## Next Steps

For detailed information about each command, including all available parameters and examples, click on the command name in the table above or use the navigation menu.