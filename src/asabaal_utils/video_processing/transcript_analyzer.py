"""
Transcript analyzer module for video processing.

This module provides utilities for analyzing video transcripts and
suggesting optimal clip splits for better content flow.
"""

import re
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class TranscriptSegment:
    """A segment of transcript with metadata."""
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    confidence: float = 1.0
    
    @property
    def duration(self) -> float:
        """Get the duration of this segment."""
        return self.end_time - self.start_time


@dataclass
class ClipSuggestion:
    """A suggested clip from the transcript."""
    start_time: float
    end_time: float
    topic: str
    segments: List[TranscriptSegment]
    importance_score: float = 0.0
    
    @property
    def duration(self) -> float:
        """Get the duration of this clip."""
        return self.end_time - self.start_time
    
    @property
    def text(self) -> str:
        """Get the full text of this clip."""
        texts = []
        for segment in self.segments:
            if isinstance(segment, dict):
                if 'text' in segment:
                    texts.append(segment['text'])
            else:
                texts.append(segment.text)
        return " ".join(texts)

class TranscriptAnalyzer:
    """
    Analyzes video transcripts to suggest optimal clip splits.
    
    This class processes video transcripts (such as those from CapCut)
    and suggests optimal points to split videos into coherent clips.
    """
    
    def __init__(
        self,
        min_clip_duration: float = 10.0, 
        max_clip_duration: float = 60.0,
        topic_change_threshold: float = 0.3,
        sentence_end_weight: float = 1.5,
        keyword_weight: float = 2.0,
        pause_weight: float = 1.0,
        speaker_change_weight: float = 1.2,
        keywords: Optional[List[str]] = None
    ):
        """
        Initialize the transcript analyzer.
        
        Args:
            min_clip_duration: Minimum duration in seconds for a suggested clip.
            max_clip_duration: Maximum duration in seconds for a suggested clip.
            topic_change_threshold: Similarity threshold to detect topic changes.
            sentence_end_weight: Weight of sentence ends when scoring split points.
            keyword_weight: Weight of keywords when scoring split points.
            pause_weight: Weight of pauses when scoring split points.
            speaker_change_weight: Weight of speaker changes when scoring split points.
            keywords: List of important keywords to consider when analyzing the transcript.
                If None, will use a default set of transition words and phrases.
        """
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration
        self.topic_change_threshold = topic_change_threshold
        self.sentence_end_weight = sentence_end_weight
        self.keyword_weight = keyword_weight
        self.pause_weight = pause_weight
        self.speaker_change_weight = speaker_change_weight
        
        # Default transition/marker keywords if none provided
        self.keywords = keywords or [
            "firstly", "secondly", "thirdly", "finally", "in conclusion", 
            "to summarize", "in summary", "next", "now", "moving on",
            "let's talk about", "i want to discuss", "another important point",
            "on the other hand", "however", "meanwhile", "by contrast",
            "for example", "specifically", "to illustrate", "such as",
            "in other words", "that is", "to clarify", "put simply",
        ]
        
        # Regular expressions for sentence boundaries
        self.sentence_end_pattern = re.compile(r'[.!?]\s+')
        
        # Vectorizer for topic similarity
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            ngram_range=(1, 2),
            min_df=1, max_df=0.9
        )
        
    def parse_capcut_transcript(self, transcript_file: str) -> List[TranscriptSegment]:
        """
        Parse a transcript file from CapCut.
        
        Args:
            transcript_file: Path to the transcript file.
            
        Returns:
            List of TranscriptSegment objects.
        """
        logger.info(f"Parsing CapCut transcript from {transcript_file}")
        
        transcript_text = Path(transcript_file).read_text(encoding='utf-8')
        lines = transcript_text.strip().split('\n')
        
        segments = []
        current_time = 0.0
        
        for line in lines:
            # CapCut format is typically [time] text
            # Example: [00:01:23] Hello world
            match = re.match(r'\[(\d{2}):(\d{2}):(\d{2})\]\s*(.*)', line)
            if match:
                hours, minutes, seconds, text = match.groups()
                
                # Calculate timestamp in seconds
                timestamp = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                
                # Create a segment
                # We don't know exact end times, so we'll use the next timestamp
                # as the end time for the previous segment
                if segments:
                    segments[-1].end_time = timestamp
                
                segment = TranscriptSegment(
                    text=text.strip(),
                    start_time=timestamp,
                    end_time=timestamp + 5.0,  # Placeholder, will be updated
                    speaker=None,
                    confidence=1.0
                )
                segments.append(segment)
                current_time = timestamp
            else:
                # If we can't parse the line, add it to the previous segment if any
                if segments:
                    segments[-1].text += " " + line.strip()
        
        return segments
    
    def parse_json_transcript(self, transcript_file: str) -> List[TranscriptSegment]:
        """
        Parse a transcript file in JSON format.
        
        Args:
            transcript_file: Path to the transcript file.
            
        Returns:
            List of TranscriptSegment objects.
        """
        logger.info(f"Parsing JSON transcript from {transcript_file}")
        
        with open(transcript_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = []
        
        # This is a generic parser, but the exact structure
        # will depend on your specific JSON format
        if isinstance(data, list):
            # List of segments
            for item in data:
                segment = TranscriptSegment(
                    text=item.get('text', ''),
                    start_time=item.get('start_time', 0.0),
                    end_time=item.get('end_time', 0.0),
                    speaker=item.get('speaker'),
                    confidence=item.get('confidence', 1.0)
                )
                segments.append(segment)
        elif isinstance(data, dict) and 'segments' in data:
            # Dictionary with a 'segments' key
            for item in data['segments']:
                segment = TranscriptSegment(
                    text=item.get('text', ''),
                    start_time=item.get('start_time', 0.0),
                    end_time=item.get('end_time', 0.0),
                    speaker=item.get('speaker'),
                    confidence=item.get('confidence', 1.0)
                )
                segments.append(segment)
        
        return segments

    def parse_enhanced_srt_json_transcript(self, json_file):
        """
        Parse a JSON file created from enhanced SRT data.
        
        Args:
            json_file: Path to enhanced SRT JSON
            
        Returns:
            List of transcript segments
        """
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract segments directly from the enhanced JSON
        if "segments" in data:
            segments = []
            for segment in data["segments"]:
                segments.append({
                    "text": segment["text"],
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "duration": segment.get("end_time", 0) - segment.get("start_time", 0),
                    # Include any other helpful metadata
                    "enhanced": True,
                    "original_text": segment.get("original_text")
                })
            return segments
        
        # Fallback for legacy enhanced format
        logger.warning("Enhanced SRT JSON format not recognized, trying alternative parsing")
        return self.parse_json_transcript(json_file)

    def parse_srt_transcript(self, transcript_file: str) -> List[TranscriptSegment]:
        """
        Parse a transcript file in SRT format.
        
        Args:
            transcript_file: Path to the transcript file.
            
        Returns:
            List of TranscriptSegment objects.
        """
        logger.info(f"Parsing SRT transcript from {transcript_file}")
        
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        
        # Split by double newline which separates entries in SRT
        entries = transcript_text.strip().split('\n\n')
        segments = []
        
        for entry in entries:
            lines = entry.strip().split('\n')
            
            if len(lines) < 3:
                continue  # Skip invalid entries
                
            # First line is the index number
            # Second line contains timestamps "00:00:00,000 --> 00:00:00,983"
            # Remaining lines are the text content
            
            try:
                # Parse timestamps
                timestamp_line = lines[1]
                timestamps = timestamp_line.split(' --> ')
                if len(timestamps) != 2:
                    logger.warning(f"Invalid timestamp format: {timestamp_line}")
                    continue
                    
                start_time_str, end_time_str = timestamps
                
                # Convert timestamp from HH:MM:SS,MS to seconds
                start_time = self._srt_timestamp_to_seconds(start_time_str)
                end_time = self._srt_timestamp_to_seconds(end_time_str)
                
                # Get text content (could be multiple lines)
                text = ' '.join(lines[2:])
                
                segment = TranscriptSegment(
                    text=text,
                    start_time=start_time,
                    end_time=end_time,
                    speaker=None,
                    confidence=1.0
                )
                segments.append(segment)
                
            except Exception as e:
                logger.warning(f"Error parsing SRT entry: {e}")
                continue
        
        return segments

    def _srt_timestamp_to_seconds(self, timestamp: str) -> float:
        """
        Convert SRT timestamp format (HH:MM:SS,MS) to seconds.
        
        Args:
            timestamp: SRT format timestamp
            
        Returns:
            Time in seconds (float)
        """
        # Replace comma with period for milliseconds
        timestamp = timestamp.replace(',', '.')
        
        # Split into hours, minutes, seconds (with milliseconds)
        parts = timestamp.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
            
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        # Convert to seconds
        return hours * 3600 + minutes * 60 + seconds

    # Add this method to TranscriptAnalyzer class
    def _get_segment_attr(self, segment, attr, default=None):
        """
        Safely get an attribute from a segment, whether it's a TranscriptSegment object or a dictionary.
        
        Args:
            segment: TranscriptSegment object or dictionary
            attr: Attribute or key to access
            default: Default value if attribute is not found
            
        Returns:
            The attribute value or default
        """
        if isinstance(segment, dict):
            return segment.get(attr, default)
        else:
            return getattr(segment, attr, default)

    def detect_topic_changes(self, segments: List[TranscriptSegment]) -> List[int]:
        """
        Detect significant topic changes in the transcript.
        
        Args:
            segments: List of TranscriptSegment objects.
            
        Returns:
            List of indices where topics change.
        """

        if len(segments) < 3:
            return []
        
        # Extract text from segments
        texts = [self._get_segment_attr(segment, 'text', '') for segment in segments]
        
        # Create windows of text for analysis
        window_size = 3
        windows = []
        
        for i in range(len(texts) - window_size + 1):
            window_text = " ".join(texts[i:i+window_size])
            windows.append(window_text)
        
        if not windows:
            return []
        
        # Vectorize the windows
        try:
            X = self.vectorizer.fit_transform(windows)
            
            # Calculate similarity between adjacent windows
            similarities = []
            for i in range(len(windows) - 1):
                similarity = cosine_similarity(X[i:i+1], X[i+1:i+2])[0][0]
                similarities.append(similarity)
            
            # Detect significant drops in similarity
            topic_changes = []
            for i, similarity in enumerate(similarities):
                # Add 1 because we're looking at the similarity between window i and i+1
                # and the actual change would happen at i+1 in the original segments
                # We then need to add window_size-1 because each window starts at position i
                if similarity < self.topic_change_threshold:
                    change_idx = i + 1 + (window_size - 1)
                    if change_idx < len(segments):
                        topic_changes.append(change_idx)
            
            return topic_changes
        
        except ValueError:
            # Handle the case where vectorization fails
            logger.warning("Failed to vectorize transcript windows, possibly due to empty text")
            return []
    
    def score_split_points(self, segments, topic_changes):
        """
        Score potential split points in the transcript.
        
        Args:
            segments: List of TranscriptSegment objects or dictionaries.
            topic_changes: List of indices where topics change.
            
        Returns:
            Dictionary mapping segment indices to split scores.
        """
        scores = {}
        
        for i in range(1, len(segments)):
            score = 0.0
            
            # Topic change score
            if i in topic_changes:
                score += 10.0  # High weight for topic changes
            
            # Sentence end score
            prev_segment = segments[i-1]
            prev_text = self._get_segment_attr(prev_segment, 'text', '')
            if self.sentence_end_pattern.search(prev_text):
                score += self.sentence_end_weight
            
            # Keyword score
            current_text = self._get_segment_attr(segments[i], 'text', '')
            for keyword in self.keywords:
                if prev_text.lower().endswith(keyword.lower()):
                    score += self.keyword_weight
                if current_text.lower().startswith(keyword.lower()):
                    score += self.keyword_weight
            
            # Pause score
            prev_end_time = self._get_segment_attr(prev_segment, 'end_time', 0.0)
            current_start_time = self._get_segment_attr(segments[i], 'start_time', 0.0)
            time_diff = current_start_time - prev_end_time
            if time_diff > 0.5:  # Significant pause
                score += self.pause_weight * min(3.0, time_diff)
            
            # Speaker change score
            prev_speaker = self._get_segment_attr(prev_segment, 'speaker')
            current_speaker = self._get_segment_attr(segments[i], 'speaker')
            if (prev_speaker and current_speaker and prev_speaker != current_speaker):
                score += self.speaker_change_weight
            
            scores[i] = score
        
        return scores
    
    def generate_clip_suggestions(
        self, 
        segments: List[Union[TranscriptSegment, Dict]]
    ) -> List[ClipSuggestion]:
        """
        Generate suggested clips from transcript segments.
        
        Args:
            segments: List of TranscriptSegment objects or dictionaries.
            
        Returns:
            List of ClipSuggestion objects.
        """
        if not segments:
            return []
        
        # Detect topic changes
        topic_changes = self.detect_topic_changes(segments)
        
        # Score potential split points
        scores = self.score_split_points(segments, topic_changes)
        
        # Sort split points by score
        sorted_splits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Start with the full video as one clip
        clips = [ClipSuggestion(
            start_time=self._get_segment_attr(segments[0], 'start_time', 0.0),
            end_time=self._get_segment_attr(segments[-1], 'end_time', 0.0),
            topic="Full Video",
            segments=segments.copy(),
            importance_score=0.0
        )]
        
        # Add splits one by one, checking duration constraints
        for split_idx, score in sorted_splits:
            # Try to add this split
            new_clips = []
            for clip in clips:
                # Skip if the clip is already small enough
                if clip.duration <= self.max_clip_duration:
                    new_clips.append(clip)
                    continue
                
                # Check if the split point is within this clip
                if split_idx > 0 and segments[split_idx] in clip.segments:
                    split_pos = clip.segments.index(segments[split_idx])
                    
                    # Split the clip if both resulting parts would be valid
                    part1 = clip.segments[:split_pos]
                    part2 = clip.segments[split_pos:]
                    
                    # Calculate durations for parts
                    if part1 and part2:
                        part1_start = self._get_segment_attr(part1[0], 'start_time', 0.0)
                        part1_end = self._get_segment_attr(part1[-1], 'end_time', 0.0)
                        part1_duration = part1_end - part1_start
                        
                        part2_start = self._get_segment_attr(part2[0], 'start_time', 0.0)
                        part2_end = self._get_segment_attr(part2[-1], 'end_time', 0.0)
                        part2_duration = part2_end - part2_start
                        
                        if part1_duration >= self.min_clip_duration and part2_duration >= self.min_clip_duration:
                            # Extract topics from each part
                            topic1 = self._extract_topic(part1)
                            topic2 = self._extract_topic(part2)
                            
                            # Create two new clips
                            new_clips.append(ClipSuggestion(
                                start_time=part1_start,
                                end_time=part1_end,
                                topic=topic1,
                                segments=part1,
                                importance_score=score
                            ))
                            new_clips.append(ClipSuggestion(
                                start_time=part2_start,
                                end_time=part2_end,
                                topic=topic2,
                                segments=part2,
                                importance_score=score
                            ))
                        else:
                            # Can't split at this point, keep the original clip
                            new_clips.append(clip)
                    else:
                        # One of the parts is empty, keep the original clip
                        new_clips.append(clip)
                else:
                    # Split point not in this clip
                    new_clips.append(clip)
            
            # Update the list of clips
            clips = new_clips
        
        # If we ended up with just one clip, suggest splitting into smaller chunks
        if len(clips) == 1 and clips[0].duration > self.max_clip_duration:
            # Split into roughly equal parts
            total_duration = clips[0].duration
            num_parts = max(2, int(np.ceil(total_duration / self.max_clip_duration)))
            target_duration = total_duration / num_parts
            
            # Find split points that result in roughly equal parts
            new_clips = []
            current_segments = []
            current_duration = 0.0
            current_start = self._get_segment_attr(segments[0], 'start_time', 0.0)
            
            for segment in segments:
                current_segments.append(segment)
                segment_duration = self._get_segment_attr(segment, 'end_time', 0.0) - self._get_segment_attr(segment, 'start_time', 0.0)
                current_duration += segment_duration
                
                if current_duration >= target_duration and len(current_segments) > 1:
                    # Extract topic
                    topic = self._extract_topic(current_segments)
                    
                    # Create a new clip
                    new_clips.append(ClipSuggestion(
                        start_time=current_start,
                        end_time=self._get_segment_attr(current_segments[-1], 'end_time', 0.0),
                        topic=topic,
                        segments=current_segments.copy(),
                        importance_score=5.0  # Medium importance
                    ))
                    
                    # Reset for the next clip
                    current_segments = []
                    current_duration = 0.0
                    current_start = self._get_segment_attr(segment, 'end_time', 0.0)
            
            # Add the last clip if there are segments left
            if current_segments:
                topic = self._extract_topic(current_segments)
                new_clips.append(ClipSuggestion(
                    start_time=current_start,
                    end_time=self._get_segment_attr(current_segments[-1], 'end_time', 0.0),
                    topic=topic,
                    segments=current_segments,
                    importance_score=5.0
                ))
            
            clips = new_clips
        
        return sorted(clips, key=lambda x: x.start_time)
    
    def _extract_topic(self, segments):
        """
        Extract a topic description from a list of segments.
        
        Args:
            segments: List of TranscriptSegment objects or dictionaries.
            
        Returns:
            A string describing the topic.
        """
        if not segments:
            return "Unknown"
        
        # Simple approach: use the first few words of the first segment
        first_segment_text = self._get_segment_attr(segments[0], 'text', '')
        
        # Remove any leading transition words
        for keyword in sorted(self.keywords, key=len, reverse=True):
            if first_segment_text.lower().startswith(keyword.lower()):
                first_segment_text = first_segment_text[len(keyword):].strip()
                break
        
        # Limit to first 30 characters for a brief topic
        topic = first_segment_text[:30].strip()
        if len(first_segment_text) > 30:
            topic += "..."
        
        return topic


def analyze_transcript(
    transcript_file: str,
    output_file: Optional[str] = None,
    transcript_format: str = 'capcut',
    min_clip_duration: float = 10.0,
    max_clip_duration: float = 60.0,
    topic_change_threshold: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Analyze a transcript file and generate clip suggestions.
    
    Args:
        transcript_file: Path to the transcript file.
        output_file: Optional path to save the suggestions as JSON.
        transcript_format: Format of the transcript file ('capcut', 'json', or 'srt').
        min_clip_duration: Minimum duration in seconds for a suggested clip.
        max_clip_duration: Maximum duration in seconds for a suggested clip.
        topic_change_threshold: Similarity threshold to detect topic changes.
        
    Returns:
        List of dictionaries with clip suggestions.
    """
    analyzer = TranscriptAnalyzer(
        min_clip_duration=min_clip_duration,
        max_clip_duration=max_clip_duration,
        topic_change_threshold=topic_change_threshold,
    )
    
    # Parse the transcript
    if transcript_format.lower() == 'capcut':
        segments = analyzer.parse_capcut_transcript(transcript_file)
    elif transcript_format.lower() == 'json':
        segments = analyzer.parse_json_transcript(transcript_file)
    elif transcript_format == "enhanced_srt_json":
        segments = analyzer.parse_enhanced_srt_json_transcript(transcript_file)
    elif transcript_format.lower() == 'srt':
        segments = analyzer.parse_srt_transcript(transcript_file)
    else:
        raise ValueError(f"Unsupported transcript format: {transcript_format}")
    
    # Generate clip suggestions
    suggestions = analyzer.generate_clip_suggestions(segments)
    
    # Convert to dictionaries
    result = []
    for i, suggestion in enumerate(suggestions):
        result.append({
            'id': i + 1,
            'start_time': suggestion.start_time,
            'end_time': suggestion.end_time,
            'duration': suggestion.duration,
            'topic': suggestion.topic,
            'importance_score': suggestion.importance_score,
            'text': suggestion.text,
        })
    
    # Save to file if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
    
    return result