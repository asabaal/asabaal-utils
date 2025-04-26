"""
Transcript analyzer module for video processing.

This module provides utilities for analyzing video transcripts and
suggesting optimal clip splits for better content flow.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
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
        return " ".join(segment.text for segment in self.segments)


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
        texts = [segment.text for segment in segments]
        
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
    
    def score_split_points(
        self, 
        segments: List[TranscriptSegment],
        topic_changes: List[int]
    ) -> Dict[int, float]:
        """
        Score potential split points in the transcript.
        
        Args:
            segments: List of TranscriptSegment objects.
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
            if self.sentence_end_pattern.search(prev_segment.text):
                score += self.sentence_end_weight
            
            # Keyword score
            for keyword in self.keywords:
                if prev_segment.text.lower().endswith(keyword.lower()):
                    score += self.keyword_weight
                if segments[i].text.lower().startswith(keyword.lower()):
                    score += self.keyword_weight
            
            # Pause score
            time_diff = segments[i].start_time - prev_segment.end_time
            if time_diff > 0.5:  # Significant pause
                score += self.pause_weight * min(3.0, time_diff)
            
            # Speaker change score
            if (prev_segment.speaker and segments[i].speaker and 
                prev_segment.speaker != segments[i].speaker):
                score += self.speaker_change_weight
            
            scores[i] = score
        
        return scores
    
    def generate_clip_suggestions(
        self, 
        segments: List[TranscriptSegment]
    ) -> List[ClipSuggestion]:
        """
        Generate suggested clips from transcript segments.
        
        Args:
            segments: List of TranscriptSegment objects.
            
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
            start_time=segments[0].start_time,
            end_time=segments[-1].end_time,
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
                    
                    part1_duration = part1[-1].end_time - part1[0].start_time
                    part2_duration = part2[-1].end_time - part2[0].start_time
                    
                    if part1_duration >= self.min_clip_duration and part2_duration >= self.min_clip_duration:
                        # Extract topics from each part
                        topic1 = self._extract_topic(part1)
                        topic2 = self._extract_topic(part2)
                        
                        # Create two new clips
                        new_clips.append(ClipSuggestion(
                            start_time=part1[0].start_time,
                            end_time=part1[-1].end_time,
                            topic=topic1,
                            segments=part1,
                            importance_score=score
                        ))
                        new_clips.append(ClipSuggestion(
                            start_time=part2[0].start_time,
                            end_time=part2[-1].end_time,
                            topic=topic2,
                            segments=part2,
                            importance_score=score
                        ))
                    else:
                        # Can't split at this point, keep the original clip
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
            current_start = segments[0].start_time
            
            for segment in segments:
                current_segments.append(segment)
                current_duration += segment.duration
                
                if current_duration >= target_duration and len(current_segments) > 1:
                    # Extract topic
                    topic = self._extract_topic(current_segments)
                    
                    # Create a new clip
                    new_clips.append(ClipSuggestion(
                        start_time=current_start,
                        end_time=current_segments[-1].end_time,
                        topic=topic,
                        segments=current_segments.copy(),
                        importance_score=5.0  # Medium importance
                    ))
                    
                    # Reset for the next clip
                    current_segments = []
                    current_duration = 0.0
                    current_start = segment.end_time
            
            # Add the last clip if there are segments left
            if current_segments:
                topic = self._extract_topic(current_segments)
                new_clips.append(ClipSuggestion(
                    start_time=current_start,
                    end_time=current_segments[-1].end_time,
                    topic=topic,
                    segments=current_segments,
                    importance_score=5.0
                ))
            
            clips = new_clips
        
        return sorted(clips, key=lambda x: x.start_time)
    
    def _extract_topic(self, segments: List[TranscriptSegment]) -> str:
        """
        Extract a topic description from a list of segments.
        
        Args:
            segments: List of TranscriptSegment objects.
            
        Returns:
            A string describing the topic.
        """
        if not segments:
            return "Unknown"
        
        # Simple approach: use the first few words of the first segment
        first_segment = segments[0].text
        
        # Remove any leading transition words
        for keyword in sorted(self.keywords, key=len, reverse=True):
            if first_segment.lower().startswith(keyword.lower()):
                first_segment = first_segment[len(keyword):].strip()
                break
        
        # Limit to first 30 characters for a brief topic
        topic = first_segment[:30].strip()
        if len(first_segment) > 30:
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
        transcript_format: Format of the transcript file ('capcut' or 'json').
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
