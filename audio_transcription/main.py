#!/usr/bin/env python3
"""
Standalone entry point for audio transcription CLI
"""

import sys
from pathlib import Path

# Add the audio_transcription directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cli import main
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from cli import main

if __name__ == "__main__":
    main()