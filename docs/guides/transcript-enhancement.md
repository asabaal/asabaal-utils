# Transcript Enhancement Guide

High-quality transcripts are essential for effective video analysis, clip extraction, and summarization. This guide covers techniques for enhancing video transcripts using Asabaal Video Utilities.

## Understanding Transcript Quality Issues

Raw transcripts often contain issues that can affect analysis quality:

1. **Filler words**: "um", "uh", "like", "you know", etc.
2. **Repetitions**: Stuttering, false starts, and repeated phrases
3. **Formatting inconsistencies**: Inconsistent punctuation, capitalization, etc.
4. **Speaker identification issues**: Missing or incorrect speaker labels
5. **Timing inaccuracies**: Misaligned timestamps

## Basic Transcript Enhancement

The `enhance_transcript` function provides basic transcript enhancement:

```python
from asabaal_utils.video_processing.transcript_analyzer import enhance_transcript
from asabaal_utils.video_processing.srt_utils import load_srt, save_srt

# Load a transcript
transcript = load_srt("raw_transcript.srt")

# Enhance the transcript
enhanced_transcript = enhance_transcript(
    transcript=transcript,
    remove_fillers=True,  # Remove filler words
    handle_repetitions=True,  # Fix repetitive phrases
    normalize_text=True  # Standardize formatting
)

# Save the enhanced transcript
save_srt(enhanced_transcript, "enhanced_transcript.srt")
```

Command-line usage:
```bash
analyze-transcript video.mp4 --transcript raw_transcript.srt --enhance-transcript --save-transcript enhanced.srt
```

## Advanced Enhancement Techniques

### 1. Customizing Filler Word Removal

Specify custom filler words to remove:

```python
from asabaal_utils.video_processing.transcript_processors import enhance_transcript, create_filler_word_set

# Create custom filler word set
custom_fillers = create_filler_word_set(
    base_language="en",  # Start with English fillers
    additional_words=["actually", "basically", "literally"],  # Add custom words
    remove_words=["well"]  # Keep some default fillers
)

# Enhance transcript with custom filler set
enhanced_transcript = enhance_transcript(
    transcript=transcript,
    filler_words=custom_fillers,
    remove_fillers=True
)
```

### 2. Handling Repetitions and False Starts

Configure repetition detection settings:

```python
from asabaal_utils.video_processing.transcript_processors import enhance_transcript

# Configure repetition handling
enhanced_transcript = enhance_transcript(
    transcript=transcript,
    handle_repetitions=True,
    repetition_window=3,  # Look for repetitions within 3 words
    repetition_threshold=0.8,  # 80% similarity threshold
    preserve_emphasis_repetition=True  # Keep intentional repetitions for emphasis
)
```

### 3. Speaker Diarization and Normalization

Identify and normalize speaker labels:

```python
from asabaal_utils.video_processing.transcript_processors import normalize_speakers

# Normalize speaker labels
transcript_with_speakers = normalize_speakers(
    transcript=transcript,
    identify_speakers=True,  # Try to identify unlabeled speakers
    speaker_prefix="Speaker",  # Use "Speaker 1", "Speaker 2", etc.
    merge_adjacent=True  # Merge adjacent segments from the same speaker
)
```

### 4. Punctuation and Grammar Correction

Improve text formatting and grammar:

```python
from asabaal_utils.video_processing.transcript_processors import enhance_transcript

# Focus on punctuation and grammar
enhanced_transcript = enhance_transcript(
    transcript=transcript,
    fix_punctuation=True,  # Add missing periods, commas, question marks
    capitalize_sentences=True,  # Fix capitalization
    grammar_check=True  # Apply basic grammar correction
)
```

### 5. Transcript Alignment Correction

Fix timing issues in transcripts:

```python
from asabaal_utils.video_processing.transcript_processors import realign_transcript
from asabaal_utils.video_processing.srt_utils import load_srt

# Load transcript with timing issues
misaligned_transcript = load_srt("misaligned.srt")

# Realign transcript using the video's audio
aligned_transcript = realign_transcript(
    transcript=misaligned_transcript,
    video_file="video.mp4",
    force_alignment=True,
    max_drift=2.0  # Maximum timestamp adjustment in seconds
)
```

## Comprehensive Transcript Enhancement Pipeline

Combine multiple enhancement techniques:

```python
from asabaal_utils.video_processing.transcript_processors import (
    enhance_transcript,
    normalize_speakers,
    realign_transcript
)
from asabaal_utils.video_processing.srt_utils import load_srt, save_srt

# Load raw transcript
raw_transcript = load_srt("raw_transcript.srt")

# Step 1: Align transcript (if timing issues exist)
aligned_transcript = realign_transcript(
    transcript=raw_transcript,
    video_file="video.mp4"
)

# Step 2: Normalize speaker labels
transcript_with_speakers = normalize_speakers(
    transcript=aligned_transcript,
    identify_speakers=True
)

# Step 3: Enhance text content
enhanced_transcript = enhance_transcript(
    transcript=transcript_with_speakers,
    remove_fillers=True,
    handle_repetitions=True,
    fix_punctuation=True,
    capitalize_sentences=True,
    grammar_check=True
)

# Save final enhanced transcript
save_srt(enhanced_transcript, "fully_enhanced.srt")
```

## Working with Different Transcript Formats

### SRT Format

SRT is the most common subtitle format:

```python
from asabaal_utils.video_processing.srt_utils import load_srt, save_srt
from asabaal_utils.video_processing.transcript_processors import enhance_transcript

# Load and enhance SRT
transcript = load_srt("subtitles.srt")
enhanced = enhance_transcript(transcript)
save_srt(enhanced, "enhanced.srt")
```

### JSON Format

Some transcription services provide JSON output:

```python
from asabaal_utils.video_processing.transcript_processors import (
    load_json_transcript,
    save_json_transcript,
    enhance_transcript
)

# Load JSON transcript
transcript = load_json_transcript("transcript.json")

# Enhance
enhanced = enhance_transcript(transcript)

# Save as JSON
save_json_transcript(enhanced, "enhanced.json")

# Or convert to SRT
from asabaal_utils.video_processing.srt_utils import save_srt
save_srt(enhanced, "enhanced.srt")
```

### Plain Text Format

For simple transcripts without timing information:

```python
from asabaal_utils.video_processing.transcript_processors import (
    load_text_transcript,
    enhance_text_transcript
)

# Load and enhance text transcript
text_transcript = load_text_transcript("transcript.txt")
enhanced_text = enhance_text_transcript(
    text=text_transcript,
    remove_fillers=True,
    fix_punctuation=True
)

# Save enhanced text
with open("enhanced_transcript.txt", "w") as f:
    f.write(enhanced_text)
```

## Evaluating Enhancement Quality

Measure the impact of enhancement:

```python
from asabaal_utils.video_processing.transcript_processors import (
    compare_transcripts,
    calculate_readability
)

# Compare original and enhanced transcripts
comparison = compare_transcripts(
    original_transcript=raw_transcript,
    enhanced_transcript=enhanced_transcript
)

print(f"Filler words removed: {comparison['filler_words_removed']}")
print(f"Repetitions fixed: {comparison['repetitions_fixed']}")
print(f"Punctuation added/fixed: {comparison['punctuation_changes']}")

# Calculate readability scores
readability = calculate_readability(enhanced_transcript)
print(f"Readability score: {readability['score']}")
print(f"Grade level: {readability['grade_level']}")
```

## Transcript Enhancement Best Practices

1. **Start with alignment**: Fix timing issues before other enhancements
2. **Be conservative with repetition removal**: Some repetitions are intentional for emphasis
3. **Customize for speaker style**: Adjust filler word lists based on the speaker's style
4. **Preserve meaning**: Ensure enhancements don't alter the original meaning
5. **Manual review**: For critical content, review enhanced transcripts
6. **Save interim results**: Keep copies at each stage of the enhancement pipeline
7. **Compare analysis results**: Test how enhancement affects downstream analysis

## Using Enhanced Transcripts

Once enhanced, transcripts can be used for more effective:

1. **Topic detection**: Cleaner text improves topic boundary detection
2. **Sentiment analysis**: Removes noise that can affect sentiment scoring
3. **Clip extraction**: More accurate identification of key points
4. **Content summarization**: Better selection of important content
5. **Search indexing**: Improved searchability of video content

Example workflow:
```python
from asabaal_utils.video_processing.transcript_analyzer import analyze_transcript
from asabaal_utils.video_processing.transcript_processors import enhance_transcript

# Enhance transcript
enhanced = enhance_transcript(transcript)

# Analyze enhanced transcript
analysis = analyze_transcript(
    transcript=enhanced,
    min_clip_length=3.0,
    max_clip_length=60.0
)

# Extract key points from enhanced transcript
from asabaal_utils.video_processing.clip_extractor import extract_clips
clips = extract_clips(
    video_file="lecture.mp4",
    analysis=analysis,
    output_dir="clips/"
)
```

By following these techniques, you can significantly improve the quality of transcripts, leading to better video analysis and content extraction results.