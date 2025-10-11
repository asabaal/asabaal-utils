# Transcript Analyzer

The transcript analyzer module provides tools for analyzing video transcripts to identify topics, key points, and optimal clip segments.

## TranscriptAnalyzer Class

```python
class TranscriptAnalyzer:
    """
    Analyzes video transcripts to identify topics, key points, and optimal clip segments.
    
    This class provides methods for analyzing transcripts to determine 
    topic boundaries, key points, and optimal clip segments for content extraction.
    
    Attributes:
        min_clip_length (float): Minimum clip length in seconds (default: 3.0)
        max_clip_length (float): Maximum clip length in seconds (default: 60.0)
        topic_change_threshold (float): Threshold for detecting topic changes (default: 0.7)
        nlp_model (str): NLP model to use for analysis (default: 'default')
    """
    
    def __init__(
        self,
        min_clip_length=3.0,
        max_clip_length=60.0,
        topic_change_threshold=0.7,
        nlp_model="default",
        language="en",
        summarize=False,
        sentiment_analysis=False
    ):
        """
        Initialize the TranscriptAnalyzer with analysis parameters.
        
        Args:
            min_clip_length: Minimum clip length in seconds (default: 3.0)
            max_clip_length: Maximum clip length in seconds (default: 60.0)
            topic_change_threshold: Threshold for detecting topic changes (default: 0.7)
            nlp_model: NLP model to use for analysis (default: 'default')
            language: Language code for the transcript (default: 'en')
            summarize: Generate text summaries for each topic (default: False)
            sentiment_analysis: Include sentiment analysis in results (default: False)
        """
        pass
        
    def extract_transcript(self, video_file, output_file=None):
        """
        Extract transcript from a video file.
        
        Args:
            video_file: Path to the video file
            output_file: Optional path to save the transcript
            
        Returns:
            Dictionary containing transcript data
        """
        pass
        
    def enhance_transcript(self, transcript):
        """
        Enhance a transcript by removing filler words and handling repetitions.
        
        Args:
            transcript: Transcript dictionary
            
        Returns:
            Enhanced transcript dictionary
        """
        pass
        
    def analyze(self, transcript):
        """
        Analyze a transcript to identify topics and key points.
        
        Args:
            transcript: Transcript dictionary
            
        Returns:
            Dictionary containing analysis results
        """
        pass
        
    def export_clips(self, analysis, output_file, format="edl"):
        """
        Export clip points to a file in the specified format.
        
        Args:
            analysis: Analysis dictionary from analyze()
            output_file: Path to save the export file
            format: Export format ('edl', 'fcpxml', or 'csv')
            
        Returns:
            Path to the export file
        """
        pass
        
    def visualize(self, analysis, output_file):
        """
        Generate a visualization of the analysis.
        
        Args:
            analysis: Analysis dictionary from analyze()
            output_file: Path to save the visualization
            
        Returns:
            Path to the visualization file
        """
        pass
```

## Functions

### analyze_transcript

```python
def analyze_transcript(
    input_file=None,
    transcript=None,
    min_clip_length=3.0,
    max_clip_length=60.0,
    topic_change_threshold=0.7,
    nlp_model="default",
    language="en",
    format="auto",
    summarize=False,
    sentiment_analysis=False,
    keywords=None,
    max_topics=0,
    output=None,
    **kwargs
):
    """
    Analyze a transcript to identify topics, key points, and optimal clip segments.
    
    Args:
        input_file: Path to the video or transcript file (optional if transcript is provided)
        transcript: Transcript dictionary (optional if input_file is provided)
        min_clip_length: Minimum clip length in seconds (default: 3.0)
        max_clip_length: Maximum clip length in seconds (default: 60.0)
        topic_change_threshold: Threshold for detecting topic changes (default: 0.7)
        nlp_model: NLP model to use for analysis (default: 'default')
        language: Language code for the transcript (default: 'en')
        format: Transcript format ('srt', 'json', 'txt', or 'auto')
        summarize: Generate text summaries for each topic (default: False)
        sentiment_analysis: Include sentiment analysis in results (default: False)
        keywords: List of keywords to highlight in analysis (default: None)
        max_topics: Maximum number of topics to detect (0 for automatic) (default: 0)
        output: Path to save analysis results (default: None)
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing analysis results
    """
    pass
```

### extract_transcript

```python
def extract_transcript(
    video_file,
    output_file=None,
    format="srt",
    language="en",
    **kwargs
):
    """
    Extract a transcript from a video file.
    
    Args:
        video_file: Path to the video file
        output_file: Path to save the transcript (default: None)
        format: Output format ('srt', 'json', or 'txt') (default: 'srt')
        language: Language code (default: 'en')
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing transcript data
    """
    pass
```

### enhance_transcript

```python
def enhance_transcript(
    transcript,
    remove_fillers=True,
    handle_repetitions=True,
    normalize_text=True,
    fix_punctuation=False,
    capitalize_sentences=False,
    grammar_check=False,
    **kwargs
):
    """
    Enhance a transcript by removing filler words and handling repetitions.
    
    Args:
        transcript: Transcript dictionary
        remove_fillers: Remove filler words like "um", "uh", etc. (default: True)
        handle_repetitions: Fix repetitive phrases (default: True)
        normalize_text: Standardize formatting (default: True)
        fix_punctuation: Add missing punctuation (default: False)
        capitalize_sentences: Fix capitalization (default: False)
        grammar_check: Apply basic grammar correction (default: False)
        **kwargs: Additional parameters
        
    Returns:
        Enhanced transcript dictionary
    """
    pass
```

## Example Usage

### Basic Usage

```python
from asabaal_utils.video_processing.transcript_analyzer import analyze_transcript

# Analyze transcript from a video file
analysis = analyze_transcript(
    input_file="interview.mp4",
    min_clip_length=3.0,
    max_clip_length=60.0,
    topic_change_threshold=0.7
)

# Print detected topics
print("Detected Topics:")
for i, topic in enumerate(analysis['topics']):
    print(f"Topic {i+1}: {topic['name']} ({topic['start_time']:.1f}s - {topic['end_time']:.1f}s)")

# Print suggested clips
print("\nSuggested Clips:")
for i, clip in enumerate(analysis['suggested_clips']):
    print(f"Clip {i+1}: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s (Quality: {clip['quality_score']:.2f})")

# Save analysis results to a file
import json
with open("transcript_analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)
```

### Working with External Transcripts

```python
from asabaal_utils.video_processing.transcript_analyzer import analyze_transcript, extract_transcript

# Extract transcript from a video file
transcript = extract_transcript(
    video_file="lecture.mp4",
    output_file="transcript.srt"
)

# Analyze the transcript
analysis = analyze_transcript(
    transcript=transcript,  # Pass transcript directly
    min_clip_length=5.0,
    max_clip_length=30.0,
    topic_change_threshold=0.6,
    nlp_model="advanced"  # Use advanced NLP model
)
```

### Enhancing Transcripts

```python
from asabaal_utils.video_processing.transcript_analyzer import enhance_transcript

# Enhance a transcript
enhanced_transcript = enhance_transcript(
    transcript=transcript,
    remove_fillers=True,  # Remove filler words like "um", "uh", etc.
    handle_repetitions=True,  # Fix repetitive phrases
    normalize_text=True,  # Standardize formatting
    fix_punctuation=True,  # Add missing punctuation
    capitalize_sentences=True  # Fix capitalization
)
```

### Advanced Usage with TranscriptAnalyzer Class

```python
from asabaal_utils.video_processing.transcript_analyzer import TranscriptAnalyzer

# Create an analyzer with custom settings
analyzer = TranscriptAnalyzer(
    min_clip_length=4.0,
    max_clip_length=45.0,
    topic_change_threshold=0.65,
    nlp_model="advanced",
    language="en",
    summarize=True,  # Generate text summaries for each topic
    sentiment_analysis=True  # Include sentiment analysis
)

# Load and enhance a transcript
transcript = analyzer.extract_transcript("presentation.mp4")
enhanced_transcript = analyzer.enhance_transcript(transcript)

# Analyze the transcript
analysis = analyzer.analyze(enhanced_transcript)

# Export clip points to an EDL file
analyzer.export_clips(
    analysis=analysis,
    output_file="suggested_clips.edl",
    format="edl"
)

# Visualize the analysis
analyzer.visualize(
    analysis=analysis,
    output_file="transcript_visualization.png"
)
```

## Working with Different Transcript Formats

The transcript analyzer supports multiple transcript formats:

```python
# Analyze an SRT file
analysis = analyze_transcript(
    input_file="subtitles.srt",
    format="srt"
)

# Analyze a JSON transcript
analysis = analyze_transcript(
    input_file="transcript.json",
    format="json"
)

# Auto-detect format
analysis = analyze_transcript(
    input_file="transcript_file",
    format="auto"
)
```

## Performance Considerations

- **NLP Model**: The "basic" model is faster but less accurate, while the "advanced" model provides better topic segmentation but is slower
- **Topic Change Threshold**: Lower values (0.5-0.6) create more topic segments, higher values (0.7-0.8) result in fewer, more distinct topics
- **Language Support**: Best performance is achieved with English transcripts, but many other languages are supported
- **Transcript Quality**: Higher quality transcripts result in better analysis; consider enhancing transcripts first