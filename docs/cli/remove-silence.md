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
| `--threshold-db THRESHOLD` | float | -40.0 | Silence detection threshold in dB. Lower values (e.g., -40) will consider more audio as silence |
| `--min-silence DURATION` | float | 0.5 | Minimum duration of silence to remove in seconds |
| `--min-sound DURATION` | float | 0.3 | Minimum duration of sound to keep in seconds |
| `--padding PADDING` | float | 0.1 | Amount of padding to keep around non-silent segments in seconds |
| `--chunk-size SIZE` | float | 0.05 | Size of audio chunks for analysis in seconds |
| `--aggressive` | flag | False | Use aggressive silence rejection algorithms |

### Memory Management Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--strategy STRATEGY` | string | "auto" | Processing strategy to use: "auto", "full_quality", "reduced_resolution", "chunked", "segment", "streaming" |
| `--segment-count COUNT` | int | None | Number of segments to split video into when using segment strategy |
| `--chunk-duration DURATION` | float | None | Duration of each chunk in seconds when using chunked strategy |
| `--resolution-scale SCALE` | float | None | Scale factor for resolution when using reduced_resolution strategy (0.25-0.75) |
| `--disable-memory-adaptation` | flag | False | Disable memory-adaptive processing entirely |
| `--disable-ffmpeg` | flag | False | Disable direct FFmpeg implementation and use MoviePy instead |

### General Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--log-level LEVEL` | string | "INFO" | Set the logging level: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" |

## Examples

### Basic Usage

Remove silent segments using default settings:

```bash
remove-silence input.mp4 output.mp4
```

### Custom Silence Detection

Adjust the silence threshold and minimum duration:

```bash
remove-silence input.mp4 output.mp4 --threshold-db -40 --min-silence 1.0
```

### Memory-Efficient Processing

Process a large video file with memory optimization:

```bash
remove-silence large_video.mp4 output.mp4 --strategy chunked --chunk-duration 60
```

### Using Aggressive Mode

Use aggressive silence detection for more silence removal:

```bash
remove-silence input.mp4 output.mp4 --aggressive --threshold-db -35
```

### Customizing Audio Analysis

Fine-tune audio analysis parameters:

```bash
remove-silence input.mp4 output.mp4 --min-silence 0.8 --min-sound 0.5 --padding 0.2
```

## Output

The command produces a processed video file with silent segments removed and reports:

- Original duration of the video
- Output duration of the processed video
- Time saved by removing silent segments
- Percentage of time saved

Example output:
```
Silence removal complete:
- Original duration: 120.50s
- Output duration: 95.20s
- Time saved: 25.30s (21.0%)
- Output file: /path/to/output.mp4
```

## Related Commands

- [`create-summary`](create-summary.md) - Create content-aware video summaries
- [`extract-clips`](extract-clips.md) - Extract specific segments from videos
- [`analyze-transcript`](analyze-transcript.md) - Analyze video transcripts

## Related API

For programmatic access to this functionality, see the [silence_detector](../api/silence_detector.md) API documentation.