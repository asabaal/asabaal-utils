# analyze-transcript

The `analyze-transcript` command analyzes video transcripts to identify topics, key points, and optimal clip segments. This tool is useful for content creators who want to extract the most important parts of a video or understand its structure.

## Usage

```bash
analyze-transcript INPUT_FILE [options]
```

## Parameters

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `INPUT_FILE` | Path to the input video file or transcript file |

### Transcript Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--transcript FILE` | string | None | Path to transcript file (SRT, JSON, or TXT). If not provided, will attempt to extract from video |
| `--format FORMAT` | string | 'auto' | Transcript format: 'srt', 'json', 'txt', or 'auto' to detect automatically |
| `--language LANG` | string | 'en' | Transcript language code (e.g., 'en', 'es', 'fr') |
| `--generate-transcript` | flag | False | Generate transcript if none is provided or found in the video |
| `--enhance-transcript` | flag | False | Enhance transcript by removing filler words and handling repetitions |
| `--save-transcript FILE` | string | None | Save the processed transcript to the specified file |

### Analysis Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--min-clip-length MIN` | float | 3.0 | Minimum clip length in seconds |
| `--max-clip-length MAX` | float | 60.0 | Maximum clip length in seconds |
| `--topic-change-threshold THR` | float | 0.7 | Threshold for detecting topic changes (0.0-1.0) |
| `--keywords LIST` | string | None | Comma-separated list of keywords to highlight in analysis |
| `--nlp-model MODEL` | string | 'default' | NLP model to use for analysis (default, basic, advanced) |
| `--sentiment-analysis` | flag | False | Include sentiment analysis in the results |
| `--summarize` | flag | False | Generate text summaries for each detected topic |
| `--max-topics NUM` | int | 0 | Maximum number of topics to detect (0 for automatic) |

### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--output FILE` | string | None | Path to save analysis results (JSON format) |
| `--visualize` | flag | False | Generate visualization of the analysis |
| `--visualization-file FILE` | string | None | Path to save visualization |
| `--export-clips` | flag | False | Export suggested clip points to an EDL file |
| `--export-clips-file FILE` | string | None | Path to save EDL file with clip points |
| `--timeline-format FORMAT` | string | 'edl' | Timeline export format: 'edl', 'fcpxml', or 'csv' |

### General Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--verbose` | flag | False | Increase output verbosity |
| `--quiet` | flag | False | Suppress all output except errors |
| `--log-file FILE` | string | None | Log output to specified file |

## Examples

### Basic Usage

Analyze a video transcript with default settings:

```bash
analyze-transcript interview.mp4 --output analysis.json
```

### Provide External Transcript

Use an existing transcript file:

```bash
analyze-transcript video.mp4 --transcript subtitles.srt --output analysis.json
```

### Generate and Enhance Transcript

Generate a transcript from the video and enhance it by removing filler words:

```bash
analyze-transcript interview.mp4 --generate-transcript --enhance-transcript --save-transcript enhanced.srt
```

### Custom Analysis Parameters

Adjust analysis parameters to find shorter clips with more topic segmentation:

```bash
analyze-transcript presentation.mp4 --min-clip-length 2 --max-clip-length 30 --topic-change-threshold 0.6 --output analysis.json
```

### Generate Visualization and Export Clips

Analyze the transcript, visualize the results, and export clip points:

```bash
analyze-transcript lecture.mp4 --visualize --visualization-file timeline.png --export-clips --export-clips-file clips.edl
```

### Advanced Analysis with Sentiment

Perform advanced analysis including sentiment analysis and topic summarization:

```bash
analyze-transcript interview.mp4 --nlp-model advanced --sentiment-analysis --summarize --output detailed_analysis.json
```

## Output

The command produces a JSON file containing detailed analysis of the transcript, including:

1. Detected topics and their timestamps
2. Suggested clip segments
3. Key points and keywords
4. (Optional) Sentiment analysis
5. (Optional) Topic summaries

Example output format:
```json
{
  "video_file": "interview.mp4",
  "duration": 1825.4,
  "topics": [
    {
      "id": 1,
      "name": "Introduction and Background",
      "start_time": 0.0,
      "end_time": 120.5,
      "keywords": ["background", "experience", "introduction"],
      "sentiment": "neutral",
      "summary": "The speaker introduces themselves and discusses their background in the field."
    },
    // Additional topics...
  ],
  "suggested_clips": [
    {
      "id": 1,
      "topic_id": 1,
      "start_time": 45.2,
      "end_time": 95.7,
      "quality_score": 0.85,
      "keywords": ["key experience", "major project"]
    },
    // Additional clips...
  ],
  "key_points": [
    {
      "text": "The most important discovery was made in 2018",
      "time": 350.2,
      "topic_id": 3,
      "importance_score": 0.92
    },
    // Additional key points...
  ],
  "settings": {
    "min_clip_length": 3.0,
    "max_clip_length": 60.0,
    "topic_change_threshold": 0.7,
    "nlp_model": "default"
  }
}
```

## Related Commands

- [`extract-clips`](extract-clips.md) - Extract clips from videos based on analysis results
- [`create-summary`](create-summary.md) - Create video summaries using transcript analysis

## Related API

For programmatic access to this functionality, see the [transcript_analyzer](../api/transcript_analyzer.md) API documentation.