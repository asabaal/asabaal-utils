"""Lyric synchronization with audio features."""

from typing import List, Optional, Tuple
import numpy as np
import logging

from .parser import LyricLine, LyricWord
from ..audio.features import AudioFeatures

logger = logging.getLogger(__name__)


class LyricSynchronizer:
    """Synchronize lyrics with audio features for enhanced timing."""
    
    def __init__(self, lyrics: List[LyricLine], audio_features: AudioFeatures):
        """Initialize synchronizer.
        
        Args:
            lyrics: Parsed lyric lines
            audio_features: Analyzed audio features
        """
        self.lyrics = lyrics
        self.audio_features = audio_features
        
    def align_to_audio(self, snap_to_beats: bool = True, snap_to_onsets: bool = True) -> List[LyricLine]:
        """Align lyrics to audio features.
        
        Args:
            snap_to_beats: Snap line starts to nearest beats
            snap_to_onsets: Snap word starts to nearest onsets
            
        Returns:
            Aligned lyric lines
        """
        aligned_lyrics = []
        
        for line in self.lyrics:
            # Snap line timing to beats if enabled
            if snap_to_beats and len(self.audio_features.beats.times) > 0:
                new_start = self._snap_to_nearest_beat(line.start_time)
                new_end = self._snap_to_nearest_beat(line.end_time)
            else:
                new_start = line.start_time
                new_end = line.end_time
                
            # Align words within the line
            aligned_words = []
            if snap_to_onsets and len(self.audio_features.onset_times) > 0:
                aligned_words = self._align_words_to_onsets(line.words, new_start, new_end)
            else:
                # Re-interpolate words with new line timing
                duration = new_end - new_start
                time_per_word = duration / len(line.words) if line.words else 0
                current_time = new_start
                
                for word in line.words:
                    aligned_words.append(LyricWord(
                        text=word.text,
                        start_time=current_time,
                        end_time=current_time + time_per_word
                    ))
                    current_time += time_per_word
                    
            aligned_lyrics.append(LyricLine(
                text=line.text,
                start_time=new_start,
                end_time=new_end,
                words=aligned_words
            ))
            
        return aligned_lyrics
        
    def get_words_at_time(self, timestamp: float) -> List[Tuple[LyricWord, float]]:
        """Get active words at timestamp with progress.
        
        Args:
            timestamp: Time in seconds
            
        Returns:
            List of (word, progress) tuples where progress is 0.0-1.0
        """
        active_words = []
        
        for line in self.lyrics:
            if line.is_active(timestamp):
                for word in line.words:
                    if word.is_active(timestamp):
                        progress = (timestamp - word.start_time) / word.duration
                        active_words.append((word, progress))
                        
        return active_words
        
    def get_upcoming_words(self, timestamp: float, lookahead: float = 1.0) -> List[LyricWord]:
        """Get words coming up in the next lookahead seconds.
        
        Args:
            timestamp: Current time in seconds
            lookahead: Seconds to look ahead
            
        Returns:
            List of upcoming words
        """
        upcoming = []
        end_time = timestamp + lookahead
        
        for line in self.lyrics:
            for word in line.words:
                if timestamp < word.start_time <= end_time:
                    upcoming.append(word)
                    
        return sorted(upcoming, key=lambda w: w.start_time)
        
    def _snap_to_nearest_beat(self, time: float, max_shift: float = 0.2) -> float:
        """Snap time to nearest beat within max_shift seconds."""
        nearest_beat, _ = self.audio_features.beats.get_nearest_beat(time)
        
        if abs(nearest_beat - time) <= max_shift:
            return nearest_beat
        return time
        
    def _align_words_to_onsets(self, words: List[LyricWord], start_time: float, end_time: float) -> List[LyricWord]:
        """Align words to audio onsets within time range."""
        if not words:
            return []
            
        # Get onsets within the line's time range
        line_onsets = self.audio_features.onset_times[
            (self.audio_features.onset_times >= start_time) &
            (self.audio_features.onset_times <= end_time)
        ]
        
        aligned_words = []
        
        if len(line_onsets) >= len(words):
            # More onsets than words - assign words to first onsets
            for i, word in enumerate(words):
                word_start = line_onsets[i] if i < len(line_onsets) else start_time + i * 0.1
                word_end = line_onsets[i + 1] if i + 1 < len(line_onsets) else end_time
                
                aligned_words.append(LyricWord(
                    text=word.text,
                    start_time=word_start,
                    end_time=word_end
                ))
        else:
            # Fewer onsets than words - distribute words
            if len(line_onsets) > 0:
                # Use onsets as anchors
                words_per_onset = len(words) / len(line_onsets)
                
                for i, word in enumerate(words):
                    onset_idx = int(i / words_per_onset)
                    onset_idx = min(onset_idx, len(line_onsets) - 1)
                    
                    # Interpolate between onsets
                    if onset_idx < len(line_onsets) - 1:
                        onset_start = line_onsets[onset_idx]
                        onset_end = line_onsets[onset_idx + 1]
                        local_idx = i % int(words_per_onset)
                        local_progress = local_idx / words_per_onset
                        
                        word_start = onset_start + local_progress * (onset_end - onset_start)
                        word_end = word_start + (onset_end - onset_start) / words_per_onset
                    else:
                        # Last onset group
                        remaining_words = len(words) - i
                        time_per_word = (end_time - line_onsets[-1]) / remaining_words
                        word_start = line_onsets[-1] + (i - onset_idx * words_per_onset) * time_per_word
                        word_end = word_start + time_per_word
                        
                    aligned_words.append(LyricWord(
                        text=word.text,
                        start_time=word_start,
                        end_time=min(word_end, end_time)
                    ))
            else:
                # No onsets - fall back to even distribution
                duration = end_time - start_time
                time_per_word = duration / len(words)
                current_time = start_time
                
                for word in words:
                    aligned_words.append(LyricWord(
                        text=word.text,
                        start_time=current_time,
                        end_time=current_time + time_per_word
                    ))
                    current_time += time_per_word
                    
        return aligned_words