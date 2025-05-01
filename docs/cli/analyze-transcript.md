# analyze-transcript

The `analyze-transcript` command analyzes transcripts to identify topics, key points, and optimal clip segments. This tool is useful for content creators who want to extract the most important parts of a video or understand its structure.

## Usage

```bash
analyze-transcript TRANSCRIPT_FILE [options]
```

## Parameters

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `TRANSCRIPT_FILE` | Path to the transcript file (SRT, JSON, or CapCut format) |

### Transcript Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--format FORMAT` | string | 'capcut' | Transcript format: 'srt', 'json', or 'capcut' |
| `--enhance-transcript` | flag | False | Enhance transcript by removing filler words and handling repetitions |
| `--save-enhanced-transcript` | flag | False | Save the enhanced transcript as a plain text file |

### Enhancement Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--remove-fillers` | flag | False | Remove filler words like 'um', 'uh', etc. |
| `--handle-repetitions` | flag | False | Remove or consolidate repeated phrases |
| `--respect-sentences` | flag | False | Optimize clip boundaries to respect sentence boundaries |
| `--preserve-semantic-units` | flag | False | Preserve semantic units like explanations and lists |
| `--filler-policy POLICY` | string | 'remove_all' | Policy for handling filler words: 'remove_all', 'keep_all', or 'context_sensitive' |
| `--repetition-strategy STRATEGY` | string | 'first_instance' | Strategy for handling repetitions: 'first_instance', 'cleanest_instance', or 'combine' |

### Analysis Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--min-clip-duration MIN` | float | 10.0 | Minimum clip duration in seconds |
| `--max-clip-duration MAX` | float | 60.0 | Maximum clip duration in seconds |
| `--topic-change-threshold THR` | float | 0.3 | Threshold for detecting topic changes (0.0-1.0) |

### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--output-file FILE` | string | [TRANSCRIPT].clips.json | Path to save analysis results (JSON format) |
| `--log-level LEVEL` | string | 'INFO' | Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

## Examples

### Basic Usage

Analyze a transcript file with default settings:

```bash
analyze-transcript subtitles.srt --format srt --output-file analysis.json
```

### Enhance Transcript

Analyze a transcript and enhance it by removing filler words:

```bash
analyze-transcript subtitles.srt --format srt --enhance-transcript --save-enhanced-transcript
```

### Custom Analysis Parameters

Adjust analysis parameters to find shorter clips with more topic segmentation:

```bash
analyze-transcript presentation.json --format json --min-clip-duration 5 --max-clip-duration 30 --topic-change-threshold 0.4
```

### Advanced Enhancement Options

Use advanced transcript enhancement options:

```bash
analyze-transcript interview.srt --format srt --enhance-transcript --remove-fillers --handle-repetitions --filler-policy context_sensitive --repetition-strategy cleanest_instance
```

## Output

The command produces a JSON file containing detailed analysis of the transcript, including:

1. Detected topics and their timestamps
2. Suggested clip segments
3. Key points and timestamps

Example output format:
```json
{
  "file": "subtitles.srt",
  "suggested_clips": [
    {
      "id": 1,
      "topic": "Introduction and Background",
      "start_time": 45.2,
      "end_time": 95.7,
      "duration": 50.5,
      "text": "The speaker introduces themselves and discusses their background in the field.",
      "importance_score": 0.85
    },
    // Additional clips...
  ]
}
```

## Related Commands

- [`extract-clips`](extract-clips.md) - Extract clips from videos based on analysis results
- [`create-summary`](create-summary.md) - Create video summaries using transcript analysis

## Related API

For programmatic access to this functionality, see the [transcript_analyzer](../api/transcript_analyzer.md) API documentation.