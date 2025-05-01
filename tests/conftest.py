"""
Configuration for pytest.

This module provides fixtures and configuration for the test suite.
"""

import os
import sys
import pytest
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Sample transcript data for testing
@pytest.fixture
def sample_transcript_with_fillers():
    """Return a sample transcript with filler words."""
    return "hey everyone what's up so I'm here today to tell you that I have um I'm also here to tell you that I'm starting uh another project"

@pytest.fixture
def sample_transcript_with_repetitions():
    """Return a sample transcript with repetitions."""
    return "so I'm here today to tell you that I have so I'm here today not only to give you an update on the only permits blessing um I'm also here to tell you that in I'm also here to tell you that I'm starting another project"

@pytest.fixture
def sample_transcript_with_boundaries():
    """Return a sample transcript with sentence boundaries."""
    return "this initiative is all about changing the mindset of limitation to one of abundance and possibility. I don't believe that anything is impossible that's what the Bible says that all things are possible for god right"

@pytest.fixture
def sample_transcript_with_semantic_units():
    """Return a sample transcript with semantic units."""
    return "there are three key reasons: first, the cost is too high. second, the timeline is unrealistic. third, we lack resources."

@pytest.fixture
def sample_complex_transcript():
    """Return a complex transcript with multiple issues."""
    return """
    hey everyone what's up
    so I'm here today to tell you that I have
    so I'm here today
    not only to give you an update on the only permits
    blessing um
    I'm also here to tell you that in
    I'm also here to tell you that I'm starting
    another project
    and this one is part of my initiative called Ask
    Seek Knock
    """

@pytest.fixture
def sample_srt_format():
    """Return a sample SRT transcript."""
    return """
    1
    00:00:01,000 --> 00:00:04,000
    so I'm here today to tell you that I have
    
    2
    00:00:04,100 --> 00:00:06,500
    so I'm here today um
    
    3
    00:00:06,600 --> 00:00:10,000
    not only to give you an update on the only permits
    """