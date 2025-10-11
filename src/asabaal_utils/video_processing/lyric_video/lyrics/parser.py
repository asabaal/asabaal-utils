"""Lyric file parsing for SRT, LRC, and plain text formats."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class LyricWord:
    """Individual word with timing information."""
    text: str
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        """Get word duration in seconds."""
        return self.end_time - self.start_time
        
    def is_active(self, time: float) -> bool:
        """Check if word is active at given time."""
        return self.start_time <= time <= self.end_time


@dataclass
class LyricLine:
    """A line of lyrics with timing."""
    text: str
    start_time: float
    end_time: float
    words: List[LyricWord]
    
    @property
    def duration(self) -> float:
        """Get line duration in seconds."""
        return self.end_time - self.start_time
        
    def is_active(self, time: float) -> bool:
        """Check if line is active at given time."""
        return self.start_time <= time <= self.end_time
        
    def get_active_words(self, time: float) -> List[LyricWord]:
        """Get words that are active at given time."""
        return [word for word in self.words if word.is_active(time)]
        
    def get_progress(self, time: float) -> float:
        """Get line progress (0.0 to 1.0) at given time."""
        if time < self.start_time:
            return 0.0
        elif time > self.end_time:
            return 1.0
        else:
            return (time - self.start_time) / self.duration


class LyricParser:
    """Parser for various lyric file formats."""
    
    def __init__(self):
        self.lines: List[LyricLine] = []
        
    def parse_file(self, file_path: Union[str, Path]) -> List[LyricLine]:
        """Parse lyrics from file based on extension.
        
        Args:
            file_path: Path to lyric file
            
        Returns:
            List of parsed LyricLine objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Lyric file not found: {file_path}")
            
        ext = file_path.suffix.lower()
        content = file_path.read_text(encoding='utf-8')
        
        if ext == '.srt':
            return self.parse_srt(content)
        elif ext == '.lrc':
            return self.parse_lrc(content)
        elif ext == '.txt':
            logger.warning("Plain text file detected - manual timing will be required")
            return self.parse_plain_text(content)
        else:
            raise ValueError(f"Unsupported lyric format: {ext}")
            
    def parse_srt(self, content: str) -> List[LyricLine]:
        """Parse SRT subtitle format.
        
        Args:
            content: SRT file content
            
        Returns:
            List of parsed LyricLine objects
        """
        lines = []
        srt_blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in srt_blocks:
            lines_in_block = block.strip().split('\n')
            if len(lines_in_block) >= 3:
                # Parse timing line
                timing_match = re.match(
                    r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                    lines_in_block[1]
                )
                
                if timing_match:
                    start_time = self._srt_time_to_seconds(
                        int(timing_match.group(1)),
                        int(timing_match.group(2)),
                        int(timing_match.group(3)),
                        int(timing_match.group(4))
                    )
                    end_time = self._srt_time_to_seconds(
                        int(timing_match.group(5)),
                        int(timing_match.group(6)),
                        int(timing_match.group(7)),
                        int(timing_match.group(8))
                    )
                    
                    # Join remaining lines as text
                    text = ' '.join(lines_in_block[2:])
                    
                    # Create words with interpolated timing
                    words = self._create_words_from_line(text, start_time, end_time)
                    
                    lines.append(LyricLine(
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                        words=words
                    ))
                    
        return lines
        
    def parse_lrc(self, content: str) -> List[LyricLine]:
        """Parse LRC lyric format.
        
        Args:
            content: LRC file content
            
        Returns:
            List of parsed LyricLine objects
        """
        lines = []
        lrc_lines = content.strip().split('\n')
        
        for i, line in enumerate(lrc_lines):
            # Match LRC timestamp format [mm:ss.xx] or [mm:ss]
            match = re.match(r'\[(\d{2}):(\d{2})(?:\.(\d{2}))?\]\s*(.*)', line)
            
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                centiseconds = int(match.group(3) or 0)
                text = match.group(4)
                
                start_time = minutes * 60 + seconds + centiseconds / 100
                
                # Estimate end time from next line or add default duration
                end_time = start_time + 3.0  # Default 3 second duration
                
                # Check if there's a next timestamped line
                for j in range(i + 1, len(lrc_lines)):
                    next_match = re.match(r'\[(\d{2}):(\d{2})(?:\.(\d{2}))?\]', lrc_lines[j])
                    if next_match:
                        next_minutes = int(next_match.group(1))
                        next_seconds = int(next_match.group(2))
                        next_centiseconds = int(next_match.group(3) or 0)
                        end_time = next_minutes * 60 + next_seconds + next_centiseconds / 100
                        break
                        
                # Create words with interpolated timing
                words = self._create_words_from_line(text, start_time, end_time)
                
                lines.append(LyricLine(
                    text=text,
                    start_time=start_time,
                    end_time=end_time,
                    words=words
                ))
                
        return lines
        
    def parse_plain_text(self, content: str, default_duration: float = 3.0) -> List[LyricLine]:
        """Parse plain text with estimated timing.
        
        Args:
            content: Plain text content
            default_duration: Default duration per line in seconds
            
        Returns:
            List of parsed LyricLine objects with estimated timing
        """
        lines = []
        text_lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        current_time = 0.0
        for text in text_lines:
            start_time = current_time
            end_time = current_time + default_duration
            
            # Create words with interpolated timing
            words = self._create_words_from_line(text, start_time, end_time)
            
            lines.append(LyricLine(
                text=text,
                start_time=start_time,
                end_time=end_time,
                words=words
            ))
            
            current_time = end_time
            
        return lines
        
    def _srt_time_to_seconds(self, hours: int, minutes: int, seconds: int, milliseconds: int) -> float:
        """Convert SRT time format to seconds."""
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        
    def _create_words_from_line(self, text: str, start_time: float, end_time: float) -> List[LyricWord]:
        """Create word objects with interpolated timing."""
        words = text.split()
        if not words:
            return []
            
        # Calculate time per word
        duration = end_time - start_time
        time_per_word = duration / len(words)
        
        word_objects = []
        current_time = start_time
        
        for word in words:
            word_objects.append(LyricWord(
                text=word,
                start_time=current_time,
                end_time=current_time + time_per_word
            ))
            current_time += time_per_word
            
        return word_objects