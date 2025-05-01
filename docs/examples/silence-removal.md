# Silence Removal Workflow

This example workflow demonstrates how to detect and remove silent segments from a video to create a more concise and engaging output.

## Problem Statement

Long-form videos like interviews, lectures, or presentations often contain silent segments that can make the content less engaging. These might include:

- Pauses between questions and answers
- Moments of reflection or thinking
- Technical delays or interruptions
- Silence during slide transitions

Removing these silent segments can significantly improve viewer engagement while preserving all the meaningful content.

## Complete Workflow

### 1. Basic Silence Removal

For a quick and simple silence removal process:

```bash
# Install the package if you haven't already
pip install asabaal-utils

# Basic silence removal with default settings
remove-silence interview.mp4 interview_no_silence.mp4
```

This command will:
1. Detect silent segments using a default threshold of -30dB
2. Remove segments longer than 0.5 seconds
3. Preserve a 0.1-second padding around non-silent segments
4. Create a new video with silent segments removed

### 2. Customizing Detection Parameters

Adjust silence detection parameters based on your content:

```bash
# Lower threshold for videos with background noise
remove-silence noisy_interview.mp4 output.mp4 --threshold -25 --duration 0.8

# Higher threshold for very clean audio
remove-silence studio_recording.mp4 output.mp4 --threshold -40 --duration 0.3
```

### 3. Memory-Efficient Processing for Large Files

Process large video files with memory optimization:

```bash
# Process a large lecture video
remove-silence 2hour_lecture.mp4 lecture_no_silence.mp4 --chunk-size 10 --max-memory 1000
```

### 4. Analyzing Silent Segments

Generate a report without modifying the video:

```bash
# Create a silence analysis report
remove-silence conference_talk.mp4 output.mp4 --dry-run --report --report-file silence_report.json

# Print statistics about the silent segments
python -c "
import json
with open('silence_report.json') as f:
    data = json.load(f)
    
total_silence = sum(segment['duration'] for segment in data['silence_segments'])
print(f'Total video duration: {data[\"total_duration\"]:.1f} seconds')
print(f'Total silence: {total_silence:.1f} seconds ({total_silence/data[\"total_duration\"]*100:.1f}%)')
print(f'Number of silent segments: {len(data[\"silence_segments\"])}')
"
```

### 5. Processing Audio-Only

Remove silence from just the audio track:

```bash
# Process only the audio track
remove-silence presentation.mp4 presentation_fixed_audio.mp4 --audio-only
```

## Advanced Workflow

Here's a more advanced workflow using both the CLI and Python API:

### 1. Analyze Multiple Videos

First, analyze a set of videos to determine optimal silence parameters:

```bash
# Create a bash script to analyze multiple videos
cat > analyze_silence.sh << 'EOF'
#!/bin/bash
for video in *.mp4; do
  echo "Analyzing $video..."
  remove-silence "$video" "dummy_output.mp4" --dry-run --report --report-file "${video%.mp4}_silence.json"
done

# Summarize results
echo "Video,Duration,Silent Segments,Total Silence,Silence Percentage"
for json in *_silence.json; do
  video="${json%_silence.json}.mp4"
  duration=$(jq .total_duration "$json")
  segments=$(jq '.silence_segments | length' "$json")
  silence=$(jq '.silence_segments | map(.duration) | add' "$json")
  percentage=$(echo "$silence/$duration*100" | bc -l | xargs printf "%.1f")
  echo "$video,$duration,$segments,$silence,$percentage%"
done
EOF

chmod +x analyze_silence.sh
./analyze_silence.sh
```

### 2. Custom Python Processing

Create a custom Python script for batch processing with adaptive parameters:

```python
# Save this as batch_silence_removal.py
import os
import json
from asabaal_utils.video_processing import silence_detector
from asabaal_utils.video_processing.memory_utils import recommend_chunk_size

def process_video(input_file, threshold=None):
    """Process a video with adaptive parameters based on content."""
    # Analyze the video first
    print(f"Analyzing {input_file}...")
    detector = silence_detector.SilenceDetector()
    silence_info = detector.detect_silence(input_file)
    
    # Calculate statistics
    total_duration = silence_info['total_duration']
    silence_segments = silence_info['silence_segments']
    total_silence = sum(segment['duration'] for segment in silence_segments)
    silence_percentage = (total_silence / total_duration) * 100
    
    print(f"Video duration: {total_duration:.1f} seconds")
    print(f"Total silence: {total_silence:.1f} seconds ({silence_percentage:.1f}%)")
    print(f"Number of silent segments: {len(silence_segments)}")
    
    # Determine optimal parameters based on content
    if silence_percentage < 5:
        print("Low silence content - using sensitive detection")
        threshold = -35 if threshold is None else threshold
        min_silence = 0.3
    elif silence_percentage > 20:
        print("High silence content - using aggressive detection")
        threshold = -25 if threshold is None else threshold
        min_silence = 0.7
    else:
        print("Medium silence content - using balanced detection")
        threshold = -30 if threshold is None else threshold
        min_silence = 0.5
    
    # Determine optimal chunk size
    chunk_size = recommend_chunk_size(input_file)
    print(f"Using chunk size: {chunk_size}MB")
    
    # Process the video with optimized parameters
    output_file = f"{os.path.splitext(input_file)[0]}_no_silence.mp4"
    print(f"Processing {input_file} -> {output_file}")
    print(f"Parameters: threshold={threshold}dB, min_silence={min_silence}s")
    
    result = silence_detector.remove_silence(
        input_file=input_file,
        output_file=output_file,
        threshold=threshold,
        min_silence_duration=min_silence,
        chunk_size=chunk_size
    )
    
    # Save detailed report
    report_file = f"{os.path.splitext(input_file)[0]}_report.json"
    with open(report_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Original duration: {result['total_duration']:.1f} seconds")
    print(f"New duration: {result['output_duration']:.1f} seconds")
    print(f"Time saved: {result['time_saved']:.1f} seconds ({result['time_saved']/result['total_duration']*100:.1f}%)")
    print(f"Report saved to {report_file}")
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python batch_silence_removal.py video1.mp4 [video2.mp4 ...]")
        sys.exit(1)
    
    for video_file in sys.argv[1:]:
        print(f"\nProcessing {video_file}...")
        process_video(video_file)
```

Run the script on multiple videos:
```bash
python batch_silence_removal.py video1.mp4 video2.mp4 video3.mp4
```

### 3. Integration with Video Editing Software

Create an EDL (Edit Decision List) file for use in professional video editing software:

```python
# Save as create_silence_edl.py
import argparse
import json
from asabaal_utils.video_processing import silence_detector

def create_edl_from_silence(video_file, edl_file):
    """Create an EDL file from silence detection that keeps non-silent parts."""
    # Detect silence
    detector = silence_detector.SilenceDetector()
    silence_info = detector.detect_silence(video_file)
    
    # Convert silence segments to EDL format
    total_duration = silence_info['total_duration']
    silence_segments = silence_info['silence_segments']
    
    # Create list of segments to keep (inverse of silence)
    keep_segments = []
    last_end = 0
    
    for segment in silence_segments:
        if segment['start'] > last_end:
            keep_segments.append({
                'start': last_end,
                'end': segment['start']
            })
        last_end = segment['end']
    
    # Add final segment if needed
    if last_end < total_duration:
        keep_segments.append({
            'start': last_end,
            'end': total_duration
        })
    
    # Write EDL file
    with open(edl_file, 'w') as f:
        f.write("TITLE: Silence Removal EDL\n\n")
        for i, segment in enumerate(keep_segments):
            start_tc = format_timecode(segment['start'])
            end_tc = format_timecode(segment['end'])
            f.write(f"{i+1:03d}  AX       AA/V  C        {start_tc} {end_tc} {start_tc} {end_tc}\n")
            f.write(f"* FROM CLIP NAME: {video_file}\n\n")
    
    print(f"Created EDL with {len(keep_segments)} segments")
    print(f"EDL file saved to {edl_file}")
    
    return keep_segments

def format_timecode(seconds):
    """Convert seconds to timecode format HH:MM:SS:FF."""
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    frames = int((seconds % 1) * 30)  # Assuming 30fps
    return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create EDL file from silence detection")
    parser.add_argument("video_file", help="Input video file")
    parser.add_argument("--output", "-o", default=None, help="Output EDL file")
    args = parser.parse_args()
    
    edl_file = args.output if args.output else f"{args.video_file}.edl"
    create_edl_from_silence(args.video_file, edl_file)
```

Use the script to create an EDL:
```bash
python create_silence_edl.py interview.mp4 --output interview_silence_removal.edl
```

## Results and Variations

### Comparison of Different Threshold Settings

| Threshold (dB) | Time Saved (%) | Notes |
|----------------|----------------|-------|
| -20            | 5-10%          | Conservative; only removes very clear silence |
| -30            | 10-20%         | Balanced; good for most content |
| -40            | 15-30%         | Aggressive; may remove quiet speech |

### Different Content Types

| Content Type   | Recommended Settings | Typical Time Saved |
|----------------|----------------------|-------------------|
| Interview      | -30dB, 0.5s          | 15-25%           |
| Lecture        | -25dB, 0.7s          | 10-20%           |
| Presentation   | -30dB, 0.8s          | 20-30%           |
| Dialog/Movie   | -35dB, 0.3s          | 5-15%            |
| Noisy Setting  | -20dB, 1.0s          | 5-10%            |

## Conclusion

Silence removal is a simple yet effective technique for improving video engagement. The workflow can be customized based on:

- Content type
- Audio quality
- Target audience
- Memory constraints

For best results:
1. Start with analysis to understand silence patterns in your content
2. Adjust parameters based on content type
3. Review results and fine-tune as needed
4. Use memory optimization for large files

By following this workflow, you can significantly reduce video duration while preserving all meaningful content.