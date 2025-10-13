# Clip Preview Dashboard

The Clip Preview Dashboard is a visualization tool for video clip timelines that shows thumbnails, detects duplicated content, and provides an interactive filtering interface.

## Features

- **Clip Thumbnails**: Extracts representative frames from each video clip
- **Duplicate Detection**: Identifies clips with similar visual content
- **Timeline Visualization**: Shows where clips appear in the timeline
- **Interactive Filtering**: Filter by clip type, extraction method, frame quality
- **Dark Mode**: Toggle between light and dark themes
- **Quality Assessment**: Evaluates the quality of extracted frames
- **Responsive Design**: Works on desktop and mobile devices

## Usage

```python
from asabaal_utils.video_processing.clip_preview_generator import generate_clip_preview_dashboard

# Generate a dashboard from timeline data
dashboard_path = generate_clip_preview_dashboard(
    timeline_data=timeline_data,          # Timeline data from VideoTimelineAnalyzer
    output_dir="output/dashboard",        # Where to save the dashboard files
    dashboard_file="clip_dashboard.html", # Filename for the HTML dashboard
    similarity_threshold=0.85,            # Threshold for considering clips as duplicates
    frame_extraction_method="one_third_point"  # Method for extracting frames
)

print(f"Dashboard saved to {dashboard_path}")
```

## Duplicate Detection Algorithm

The dashboard identifies duplicate clips by matching the source video filenames:

1. **Filename Matching**: Clips that use the same source video file (same filename) are identified as duplicates
2. **Grouping**: All instances of the same source video are grouped together
3. **Visual Indicators**: Each duplicate group is assigned a unique color and letter (A, B, C, etc.)
4. **Timeline Markers**: Duplicate clips are marked in the timeline with their group's color and letter

### Frame Extraction for Previews

While not used for duplicate detection, the dashboard still extracts frames to display as thumbnails:

- **first_frame**: Uses the first frame of each clip
- **one_third_point**: Uses a frame 1/3 of the way into the clip
- **midpoint_seek**: Uses a frame from the middle of the clip
- **select_filter**: Uses a frame selected based on visual properties

The default method is `one_third_point`, which typically shows representative content rather than opening frames or credits.

## Frame Quality Assessment

Extracted frames are analyzed for quality:

- **Brightness**: Average pixel intensity (0-255)
- **Contrast**: Standard deviation of pixel values
- **Black Frame Detection**: Frames with brightness below 10 are marked as black
- **Quality Rating**: Frames are classified as "high", "low", or "poor" quality

## Dashboard Interface

The dashboard includes:

- **Statistics**: Shows counts of total, unique, and duplicate clips
- **Filters**: Filter by clip type, extraction method, and frame quality
- **Timeline**: Visualizes clips on their respective tracks with color-coding
- **Duplicate Groups**: Shows grouped clips that were identified as duplicates
- **All Clips**: Lists all clips with detailed information
- **Dark Mode Toggle**: Switch between light and dark themes

## Understanding Duplicate Detection

1. **Filename-Based Matching**: The dashboard identifies duplicates based on the source video filename, not content similarity. This means:
   - Multiple clips from the same source file will be marked as duplicates
   - Clips with different filenames but identical content will not be marked as duplicates
   - The content within the clips is not analyzed for duplication

2. **Visual Identification**: 
   - Each duplicate group has a unique color and letter
   - The timeline shows markers above each clip that belongs to a duplicate group
   - Clips are color-coded and grouped together in the Duplicate Groups section

3. **Organizing Content**: Use the duplicate detection to:
   - Identify when the same source video is used multiple times
   - Find different segments from the same video
   - Track how source videos are reused across your timeline