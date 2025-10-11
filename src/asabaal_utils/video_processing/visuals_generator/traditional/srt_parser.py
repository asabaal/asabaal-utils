import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import timedelta


@dataclass
class Subtitle:
    index: int
    start_time: float
    end_time: float
    text: str
    
    def __repr__(self):
        return f"Subtitle({self.index}, {self.start_time:.2f}-{self.end_time:.2f}, '{self.text[:30]}...')"


@dataclass
class Gap:
    start_time: float
    end_time: float
    duration: float
    narrative_context: str
    surrounding_subtitles: List[Subtitle]
    
    @property
    def time_range_str(self):
        return f"{format_time(self.start_time)}-{format_time(self.end_time)}"


def parse_timestamp(timestamp: str) -> float:
    """Convert SRT timestamp to seconds."""
    parts = timestamp.strip().replace(',', '.').split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_time(seconds: float) -> str:
    """Convert seconds to H:MM:SS or MM:SS format."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def parse_time_range(time_range: str) -> Tuple[float, float]:
    """Parse time range like '36:19-41:15' to seconds."""
    start, end = time_range.strip().split('-')
    return parse_user_time(start), parse_user_time(end)


def parse_user_time(time_str: str) -> float:
    """Parse user input time (MM:SS or H:MM:SS) to seconds."""
    parts = time_str.strip().split(':')
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:  # H:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def parse_srt_content(srt_content: str) -> List[Subtitle]:
    """Parse SRT file content into Subtitle objects."""
    subtitles = []
    
    # Split by double newlines to get subtitle blocks
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                time_line = lines[1]
                
                # Parse timestamp line
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                if time_match:
                    start_time = parse_timestamp(time_match.group(1))
                    end_time = parse_timestamp(time_match.group(2))
                    
                    # Join remaining lines as text
                    text = ' '.join(lines[2:])
                    
                    subtitles.append(Subtitle(index, start_time, end_time, text))
            except (ValueError, IndexError):
                continue
    
    return sorted(subtitles, key=lambda x: x.start_time)


def get_narrative_context(subtitles: List[Subtitle], start_time: float, end_time: float, 
                         context_window: int = 3) -> Tuple[str, List[Subtitle]]:
    """Extract narrative context around a time gap."""
    # Find subtitles before, during, and after the gap
    before = []
    during = []
    after = []
    
    for sub in subtitles:
        if sub.end_time <= start_time:
            before.append(sub)
        elif sub.start_time >= end_time:
            after.append(sub)
        else:
            during.append(sub)
    
    # Get surrounding context
    context_before = before[-context_window:] if before else []
    context_after = after[:context_window] if after else []
    
    # Build narrative context
    context_parts = []
    
    if context_before:
        context_parts.append("Before: " + ' '.join([s.text for s in context_before]))
    
    if during:
        context_parts.append("During gap: " + ' '.join([s.text for s in during]))
    
    if context_after:
        context_parts.append("After: " + ' '.join([s.text for s in context_after]))
    
    narrative_context = ' | '.join(context_parts) if context_parts else "No immediate context found"
    surrounding_subtitles = context_before + during + context_after
    
    return narrative_context, surrounding_subtitles


def get_total_duration(subtitles: List[Subtitle]) -> float:
    """Get total duration from SRT data."""
    if not subtitles:
        return 0.0
    return max(sub.end_time for sub in subtitles)


def validate_time_ranges(time_ranges: List[str], total_duration: float) -> List[str]:
    """Validate and clean time ranges."""
    validated = []
    errors = []
    
    for time_range in time_ranges:
        try:
            start, end = parse_time_range(time_range)
            
            if start >= end:
                errors.append(f"Invalid range {time_range}: start >= end")
            elif start < 0:
                errors.append(f"Invalid range {time_range}: negative start time")
            elif end > total_duration:
                errors.append(f"Warning: {time_range} extends beyond video duration")
            
            validated.append(time_range)
            
        except Exception as e:
            errors.append(f"Error parsing {time_range}: {str(e)}")
    
    return validated, errors