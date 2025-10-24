
import pytest
from pathlib import Path

def test_file_processing():
    """Test basic file processing functionality."""
    test_file = Path("test.txt")
    assert test_file.suffix == ".txt"
    assert test_file.name == "test.txt"

def test_error_handling():
    """Test error handling in file operations."""
    with pytest.raises(FileNotFoundError):
        Path("nonexistent.txt").read_text()

class TestFileOperations:
    """Test class for file operations."""
    
    def test_class_method(self):
        """Test class-based test method."""
        assert True
