#!/usr/bin/env python
"""
Run all transcript processor tests.

This script discovers and runs all the transcript processor tests
in the tests directory, with a focus on the transcript_processors module.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so imports work correctly
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

def run_all_tests():
    """
    Discover and run all tests in the tests directory.
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Discover tests in the current directory
    test_dir = Path(__file__).parent
    test_suite = loader.discover(start_dir=str(test_dir), pattern='test_*.py')
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(test_suite)
    
    # Return True if success, False otherwise
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    
    # Exit with 0 if all tests passed, 1 otherwise
    sys.exit(0 if success else 1)