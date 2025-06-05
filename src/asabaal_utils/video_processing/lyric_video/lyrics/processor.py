"""Main lyric processor combining parsing and synchronization."""

from typing import List, Optional, Union, Tuple
from pathlib import Path
import logging

from .parser import LyricParser, LyricLine, LyricWord
from .synchronizer import LyricSynchronizer
from ..audio.features import AudioFeatures

logger = logging.getLogger(__name__)


class LyricProcessor:
    """Complete lyric processing pipeline."""
    
    def __init__(self):
        self.parser = LyricParser()
        self.lyrics: Optional[List[LyricLine]] = None
        self.synchronizer: Optional[LyricSynchronizer] = None
        
    def parse_lyrics(self, lyric_file_or_text: Union[str, Path]) -> List[LyricLine]:
        """Parse lyrics from file or text.
        
        Args:
            lyric_file_or_text: Path to lyric file or raw text
            
        Returns:
            Parsed lyric lines
        """
        if isinstance(lyric_file_or_text, (str, Path)):
            path = Path(lyric_file_or_text)
            if path.exists() and path.is_file():
                # Parse from file
                self.lyrics = self.parser.parse_file(path)
            else:
                # Treat as raw text
                self.lyrics = self.parser.parse_plain_text(str(lyric_file_or_text))
        else:
            raise ValueError("Input must be a file path or text string")
            
        logger.info(f"Parsed {len(self.lyrics)} lyric lines")
        return self.lyrics
        
    def align_to_audio(self, audio_features: AudioFeatures, 
                      snap_to_beats: bool = True,
                      snap_to_onsets: bool = True) -> List[LyricLine]:
        """Synchronize lyrics with audio features.
        
        Args:
            audio_features: Analyzed audio features
            snap_to_beats: Align lines to beats
            snap_to_onsets: Align words to onsets
            
        Returns:
            Aligned lyric lines
        """
        if self.lyrics is None:
            raise ValueError("No lyrics loaded. Call parse_lyrics first.")
            
        self.synchronizer = LyricSynchronizer(self.lyrics, audio_features)
        self.lyrics = self.synchronizer.align_to_audio(snap_to_beats, snap_to_onsets)
        
        logger.info("Lyrics aligned to audio features")
        return self.lyrics
        
    def get_words_at_time(self, timestamp: float) -> List[Tuple[LyricWord, float]]:
        """Get active words at given timestamp.
        
        Args:
            timestamp: Time in seconds
            
        Returns:
            List of (word, progress) tuples
        """
        if self.synchronizer is None:
            # Use unsynchronized lyrics
            active_words = []
            for line in self.lyrics or []:
                if line.is_active(timestamp):
                    for word in line.words:
                        if word.is_active(timestamp):
                            progress = (timestamp - word.start_time) / word.duration
                            active_words.append((word, progress))
            return active_words
        else:
            return self.synchronizer.get_words_at_time(timestamp)
            
    def get_active_line(self, timestamp: float) -> Optional[Tuple[LyricLine, float]]:
        """Get the active line at given timestamp.
        
        Args:
            timestamp: Time in seconds
            
        Returns:
            Tuple of (line, progress) or None
        """
        if self.lyrics is None:
            return None
            
        for line in self.lyrics:
            if line.is_active(timestamp):
                progress = line.get_progress(timestamp)
                return (line, progress)
                
        return None
        
    def get_upcoming_words(self, timestamp: float, lookahead: float = 1.0) -> List[LyricWord]:
        """Get words coming up in the next few seconds.
        
        Args:
            timestamp: Current time in seconds
            lookahead: Seconds to look ahead
            
        Returns:
            List of upcoming words
        """
        if self.synchronizer:
            return self.synchronizer.get_upcoming_words(timestamp, lookahead)
        else:
            # Manual implementation without synchronizer
            upcoming = []
            end_time = timestamp + lookahead
            
            for line in self.lyrics or []:
                for word in line.words:
                    if timestamp < word.start_time <= end_time:
                        upcoming.append(word)
                        
            return sorted(upcoming, key=lambda w: w.start_time)