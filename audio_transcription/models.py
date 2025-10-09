"""
Data models for audio transcription pipeline
"""

from typing import List, Optional
from pydantic import BaseModel


class Word(BaseModel):
    """Individual word with timing information"""
    text: str
    start: Optional[float] = None
    end: Optional[float] = None


class Segment(BaseModel):
    """Transcript segment with timing and optional speaker information"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    words: Optional[List[Word]] = None


class Transcript(BaseModel):
    """Complete transcript with metadata"""
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[Segment]