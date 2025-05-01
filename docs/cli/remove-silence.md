# remove-silence

The `remove-silence` command automatically detects and removes silent segments from video files, producing a more concise and engaging output video.

## Usage

```bash
remove-silence INPUT_FILE OUTPUT_FILE [options]
```

## Parameters

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `INPUT_FILE` | Path to the input video file |
| `OUTPUT_FILE` | Path where the processed video will be saved |

### Silence Detection Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--threshold THRESHOLD` | float | -30.0 | Silence detection threshold in dB. Lower values (e.g., -40) will consider more audio as silence |
| `--duration MIN_DURATION` | float | 0.5 | Minimum duration of silence to detect in seconds |
| `--padding PADDING` | float | 0.1 | Amount of padding to keep around non-silent segments in seconds |
| `--min-segment MIN_SEGMENT` | float | 0.5 | Minimum duration of a non-silent segment to keep in seconds |

### Processing Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--chunk-size SIZE` | int | 20 | Process video in chunks of SIZE MB for memory efficiency |
| `--max-memory SIZE` | int | None | Limit memory usage to SIZE MB (default: 75% of system RAM) |
| `--temp-dir DIR` | string | None | Directory for temporary files (default: system temp) |
| `--keep-temp` | flag | False | Don't delete temporary files after processing |
| `--audio-only` | flag | False | Process only the audio track, keep video unchanged |

### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--format FORMAT` | string | None | Output video format (default: same as input) |
| `--quality QUALITY` | int | None | Output video quality (0-100, higher is better) |
| `--dry-run` | flag | False | Analyze but don't create output file |
| `--report` | flag | False | Save a JSON report of detected silence |
| `--report-file FILE` | string | None | Path for the JSON silence report |

### General Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--verbose` | flag | False | Increase output verbosity |
| `--quiet` | flag | False | Suppress all output except errors |
| `--log-file FILE` | string | None | Log output to specified file |

## Examples

### Basic Usage

Remove silent segments using default settings:

```bash
remove-silence input.mp4 output.mp4
```

### Custom Silence Detection

Adjust the silence threshold and minimum duration:

```bash
remove-silence input.mp4 output.mp4 --threshold -40 --duration 1.0
```

### Memory-Efficient Processing

Process a large video file with memory optimization:

```bash
remove-silence large_video.mp4 output.mp4 --chunk-size 10 --max-memory 1000
```

### Generate Silence Report

Analyze the video and generate a report without creating an output file:

```bash
remove-silence input.mp4 output.mp4 --dry-run --report --report-file silence_report.json
```

### Process Only Audio

Remove silence from the audio track while keeping the video unchanged:

```bash
remove-silence interview.mp4 output.mp4 --audio-only
```

## Output

The command produces:

1. A processed video file with silent segments removed
2. (Optional) A JSON report with detailed information about detected silent segments

Example report format:
```json
{
  "input_file": "input.mp4",
  "output_file": "output.mp4",
  "total_duration": 120.5,
  "output_duration": 95.2,
  "time_saved": 25.3,
  "silence_segments": [
    {"start": 10.2, "end": 15.5, "duration": 5.3},
    {"start": 45.7, "end": 55.1, "duration": 9.4},
    {"start": 100.3, "end": 110.9, "duration": 10.6}
  ],
  "settings": {
    "threshold": -30.0,
    "min_silence_duration": 0.5,
    "padding": 0.1
  }
}
```

## Related Commands

- [`create-summary`](create-summary.md) - Create content-aware video summaries
- [`extract-clips`](extract-clips.md) - Extract specific segments from videos

## Related API

For programmatic access to this functionality, see the [silence_detector](../api/silence_detector.md) API documentation.