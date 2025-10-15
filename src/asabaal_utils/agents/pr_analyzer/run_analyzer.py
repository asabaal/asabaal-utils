#!/usr/bin/env python3
"""
PR Analyzer CLI Entry Point
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.cli import main

if __name__ == "__main__":
    main()