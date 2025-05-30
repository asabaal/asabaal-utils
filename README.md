# asabaal-utils

A collection of video processing utilities by Asabaal Ventures, LLC.

## Video Processing Utilities

Tools to speed up video editing workflows by automating common tasks.

### Silence Detection and Removal

Automatically detects and removes silent/near-silent portions of videos to create tighter, more engaging content.

#### Features:

- Adjustable silence threshold to accommodate different recording environments
- Customizable minimum silence duration to avoid choppy editing
- Padding controls to ensure smooth transitions
- Memory-adaptive processing for handling large video files
- Advanced audio analysis with aggressive silence detection option
- Multiple processing strategies to optimize for speed or quality

#### Usage

```bash
# Command-line usage
remove-silence input.mp4 output.mp4 --threshold-db -45 --min-silence 0.7

# Import and use in your own Python scripts
from asabaal_utils.video_processing import remove_silence

remove_silence(
    "input.mp4",
    "output.mp4",
    threshold_db=-40.0,
    min_silence_duration=0.5,
    min_sound_duration=0.3,
    padding=0.1
)
```

### Transcript Analysis for Intelligent Clip Splitting

Analyzes video transcripts (such as those from CapCut) to suggest optimal points to split your videos into coherent clips.

#### Features:

- Topic change detection using NLP techniques
- Speaker change detection
- Identifies natural break points in speech
- Handles CapCut, SRT, and custom JSON transcript formats
- Configurable minimum and maximum clip durations
- Transcript enhancement with filler word removal and repetition handling
- Sentence boundary detection for optimal clip boundaries

#### Usage

```bash
# Command-line usage
analyze-transcript transcript.txt --output-file suggestions.json --min-clip-duration 15 --max-clip-duration 90

# With transcript enhancement
analyze-transcript transcript.txt --enhance-transcript --remove-fillers --respect-sentences

# Import and use in your own Python scripts
from asabaal_utils.video_processing import analyze_transcript

suggestions = analyze_transcript(
    "transcript.txt",
    output_file="suggestions.json",
    transcript_format="capcut",
    min_clip_duration=10.0,
    max_clip_duration=60.0
)
```

### Automatic Thumbnail Generation

Analyzes videos to extract high-quality frames that make excellent thumbnails or preview images.

#### Features:

- Extracts frames based on image quality metrics (brightness, contrast, colorfulness, sharpness)
- Avoids blurry or motion-heavy frames
- Intelligently spaces thumbnails throughout the video
- Options to customize number of candidates and placement
- Generates detailed metadata about each thumbnail candidate

#### Usage

```bash
# Command-line usage
generate-thumbnails video.mp4 --output-dir video_thumbs --count 15 --format jpg

# Import and use in your own Python scripts
from asabaal_utils.video_processing import generate_thumbnails

thumbnails = generate_thumbnails(
    "video.mp4",
    output_dir="video_thumbs",
    frames_to_extract=10,
    skip_start_percent=0.05,
    skip_end_percent=0.05,
    output_format="jpg"
)

# Print the best thumbnail candidate
best_thumbnail = max(thumbnails, key=lambda x: x['quality_score'])
print(f"Best thumbnail at {best_thumbnail['timestamp_str']}: {best_thumbnail['frame_path']}")
```

### Video Color Theme Analysis

Extracts and analyzes color themes and palettes from your videos to help maintain visual consistency.

#### Features:

- Identifies dominant colors and their proportions
- Creates color palette images for reference
- Identifies color theme types (monochromatic, complementary, etc.)
- Suggests complementary colors for graphics and titles
- Provides color emotion and mood analysis
- Tracks color changes throughout the video in segments

#### Usage

```bash
# Command-line usage
analyze-colors video.mp4 --output-dir video_colors --palette-size 6

# Import and use in your own Python scripts
from asabaal_utils.video_processing import analyze_video_colors

color_data = analyze_video_colors(
    "video.mp4",
    output_dir="video_colors",
    palette_size=5,
    create_palette_image=True,
    create_segments=True
)

# Access the color theme information
theme = color_data["theme"]
print(f"Video color theme: {theme['theme_type']}")
print(f"Dominant colors: {', '.join(theme['color_names'])}")
print(f"Emotional associations: {', '.join(theme['emotions'])}")

# Use complementary colors for graphics
for color_hex in theme["complementary_hex"]:
    print(f"Complementary color: {color_hex}")
```

### Jump Cut Detection and Smoothing

Detects abrupt transitions (jump cuts) in videos and can automatically apply smooth transitions to improve flow.

#### Features:

- Identifies jump cuts using multiple detection metrics (similarity, motion, color change)
- Suggests appropriate transitions based on content analysis
- Supports various transition types (crossfade, fade to black/white, wipes, zooms)
- Can save frames before and after each jump cut for manual review
- Option to automatically create a new video with smoothed transitions

#### Usage

```bash
# Command-line usage for detection only
detect-jump-cuts video.mp4 --output-dir video_jump_cuts --sensitivity 0.6

# With automatic smoothing
detect-jump-cuts video.mp4 --smooth-output smoothed_video.mp4 --sensitivity 0.6

# Import and use in your own Python scripts
from asabaal_utils.video_processing import detect_jump_cuts, smooth_jump_cuts

# First detect jump cuts
jump_cuts = detect_jump_cuts(
    "video.mp4", 
    output_dir="video_jump_cuts",
    sensitivity=0.6,
    save_frames=True
)

# Review the detected jump cuts
for cut in jump_cuts:
    print(f"Jump cut at {cut['timestamp_str']} - Suggested transition: {cut['suggested_transition']}")

# Then apply smoothing transitions
smooth_jump_cuts(
    "video.mp4",
    "smoothed_video.mp4",
    jump_cuts,
    apply_all_transitions=True
)
```

### Content-Aware Video Summarization

Automatically analyzes videos to create shorter summaries or highlight reels by extracting the most interesting segments.

#### Features:

- Intelligently identifies the most engaging parts of your videos
- Multiple summary styles (highlights, trailer, overview, teaser, condensed)
- Analyzes visual quality, audio interest, motion, and speech presence
- Detects peak moments and representative segments
- Automatically creates a condensed version with smooth transitions between segments
- Memory-adaptive processing for handling large videos

#### Usage

```bash
# Command-line usage
create-summary input.mp4 summary.mp4 --target-duration 90 --style trailer

# Import and use in your own Python scripts
from asabaal_utils.video_processing import create_video_summary, SummaryStyle

# Create a 60-second highlight reel
segments = create_video_summary(
    "long_video.mp4",
    "highlight_reel.mp4",
    target_duration=60.0,
    summary_style="highlights",
    favor_beginning=True,
    favor_ending=True
)

# Print information about the selected segments
for segment in segments:
    print(f"Included segment from {segment['timestamp_str']} - {segment['category']}")
    print(f"Metrics: Visual={segment['metrics']['visual_interest']}, " 
          f"Audio={segment['metrics']['audio_interest']}")
```

### Clip Extraction

Extract clips from a video based on suggestions from transcript analysis.

#### Features:

- Extracts clips from JSON files generated by transcript analysis
- Can analyze transcripts directly and extract clips in one step
- Filter by clip duration, importance score, or top-N clips
- Optional padding around clips for smoother transitions
- Saves detailed metadata about extracted clips

#### Usage

```bash
# Extract clips using a JSON file with suggestions
extract-clips video.mp4 suggestions.json --output-dir clips --clip-prefix scene

# Directly analyze and extract from a transcript file
extract-clips video.mp4 --transcript-file transcript.srt --output-dir clips

# With transcript enhancement
extract-clips video.mp4 --transcript-file transcript.srt --enhance-transcript --remove-fillers

# Import and use in your own Python scripts
from asabaal_utils.video_processing.clip_extractor import extract_clips_from_json

clips = extract_clips_from_json(
    "video.mp4",
    "suggestions.json",
    output_dir="clips",
    clip_prefix="scene",
    top_n=5,  # Only extract top 5 clips
    min_score=0.7  # Only extract clips with importance > 0.7
)
```

## Presentation Generator

Convert structured JSON data into interactive HTML presentations that can be viewed in any web browser.

### Features:

- Generate professional-looking presentations from JSON data
- Interactive navigation with arrow keys and buttons
- Multiple themes: professional blue, dark, and minimal
- Support for title slides, content slides with bullet points, and closing slides
- Support for markdown-style formatting (bold text)
- Integrated export to PDF functionality
- "Copy HTML" button for easy saving
- Responsive design that works on all screen sizes

### Usage

```bash
# Command-line usage
generate-presentation presentation_data.json --output-file presentation.html --theme professional_blue

# Import and use in your own Python scripts
from asabaal_utils.presentation_generator import generate_presentation_html, save_presentation_html

# Define your presentation data
presentation_data = {
    "title": "Market Intelligence Report",
    "theme": "professional_blue",
    "slides": [
        {
            "type": "title",
            "content": {
                "title": "Market Intelligence Report",
                "subtitle": "Latest Insights Across Key Domains"
            }
        },
        {
            "type": "content",
            "content": {
                "title": "Executive Summary",
                "bullets": [
                    "**Growing focus on sustainability**: New developments...",
                    "**Advancements in technology**: Major breakthroughs...",
                    "**Shifting global politics**: Recent events..."
                ]
            },
            "image": {
                "type": "description",
                "description": "An infographic showing market trends..."
            }
        },
        {
            "type": "closing",
            "content": {
                "title": "Thank You",
                "subtitle": "Questions?"
            }
        }
    ]
}

# Generate and save the HTML presentation
html_content = generate_presentation_html(presentation_data)
save_presentation_html(presentation_data, "presentation.html")
```

## Installation

### Dependencies

The package requires the following dependencies:
- Python 3.7 or higher
- moviepy >= 1.0.3
- numpy >= 1.21.0
- librosa >= 0.9.2
- scikit-learn >= 1.0.2
- scikit-image >= 0.19.0
- tqdm >= 4.62.3
- pillow >= 9.0.0
- scipy >= 1.7.0

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/asabaal/asabaal-utils.git
cd asabaal-utils

# Install with development dependencies
pip install -e .
```

## CLI Commands

After installation, the following command-line tools will be available:

- `remove-silence` - Remove silent portions from videos
- `analyze-transcript` - Analyze transcripts for optimal clip splitting
- `generate-thumbnails` - Generate high-quality thumbnail candidates
- `analyze-colors` - Analyze color themes and palettes in videos
- `detect-jump-cuts` - Detect and smooth jump cuts in videos
- `create-summary` - Create content-aware video summaries
- `extract-clips` - Extract clips based on transcript analysis
- `generate-presentation` - Generate HTML presentations from JSON data

Run any command with `--help` to see all available options.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
