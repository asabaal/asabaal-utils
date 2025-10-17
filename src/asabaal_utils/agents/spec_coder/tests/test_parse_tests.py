"""
Comprehensive test suite for the parse_tests module.
"""

import pytest
import tempfile
import ast
from pathlib import Path
from unittest.mock import Mock, patch

from ..parse_tests import TestInfo, TestVisitor, parse_test_file


class TestTestInfo:
    """Test cases for TestInfo dataclass."""
    
    def test_test_info_creation(self):
        """Test creating TestInfo instance."""
        test_info = TestInfo(
            name="test_function",
            target_function="my_function",
            inputs={"param1": "value1", "param2": 42},
            assertions=["assert result == expected", "assert len(result) > 0"]
        )
        
        assert test_info.name == "test_function"
        assert test_info.target_function == "my_function"
        assert test_info.inputs == {"param1": "value1", "param2": 42}
        assert len(test_info.assertions) == 2
        assert "assert result == expected" in test_info.assertions


class TestTestVisitor:
    """Test cases for TestVisitor class."""
    
    def test_visitor_init(self):
        """Test TestVisitor initialization."""
        visitor = TestVisitor()
        
        assert visitor.tests == []
        assert visitor.current_test is None
        assert visitor.imports == {}
        assert visitor.from_imports == {}
    
    def test_visit_import(self):
        """Test visiting import statements."""
        code = """
import os
import sys as system
import numpy as np
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert visitor.imports["os"] == "os"
        assert visitor.imports["system"] == "sys"
        assert visitor.imports["np"] == "numpy"
    
    def test_visit_import_from(self):
        """Test visiting from-import statements."""
        code = """
from typing import List, Dict
from unittest.mock import Mock, patch
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert "typing" in visitor.from_imports
        assert "List" in visitor.from_imports["typing"]
        assert "Dict" in visitor.from_imports["typing"]
        assert "unittest.mock" in visitor.from_imports
        assert "Mock" in visitor.from_imports["unittest.mock"]
        assert "patch" in visitor.from_imports["unittest.mock"]
    
    def test_visit_simple_test_function(self):
        """Test visiting a simple test function."""
        code = """
def test_simple_function():
    result = add(2, 3)
    assert result == 5
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert len(visitor.tests) == 1
        test = visitor.tests[0]
        assert test.name == "test_simple_function"
        assert test.target_function == "add"
        assert test.inputs == {}
        assert len(test.assertions) == 1
        assert "assert result == 5" in test.assertions[0]
    
    def test_visit_test_with_inputs(self):
        """Test visiting a test function with explicit inputs."""
        code = """
def test_with_inputs():
    a = 10
    b = 20
    result = multiply(a, b)
    assert result == 200
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert len(visitor.tests) == 1
        test = visitor.tests[0]
        assert test.name == "test_with_inputs"
        assert test.target_function == "multiply"
        assert test.inputs == {"a": 10, "b": 20}
    
    def test_visit_test_with_multiple_assertions(self):
        """Test visiting a test function with multiple assertions."""
        code = """
def test_multiple_assertions():
    result = process_data([1, 2, 3])
    assert len(result) == 3
    assert all(x > 0 for x in result)
    assert isinstance(result, list)
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert len(visitor.tests) == 1
        test = visitor.tests[0]
        assert len(test.assertions) == 3
        assert "assert len(result) == 3" in test.assertions
        assert "assert all(x > 0 for x in result)" in test.assertions
        assert "assert isinstance(result, list)" in test.assertions
    
    def test_visit_non_test_function(self):
        """Test visiting non-test functions."""
        code = """
def helper_function():
    return "helper"

def not_a_test():
    pass

def test_actual_test():
    assert True
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        # Should only extract the actual test function
        assert len(visitor.tests) == 1
        assert visitor.tests[0].name == "test_actual_test"
    
    def test_visit_test_with_method_calls(self):
        """Test visiting test with method calls."""
        code = """
def test_method_call():
    obj = MyClass()
    result = obj.process_data("input")
    assert result.success is True
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert len(visitor.tests) == 1
        test = visitor.tests[0]
        # Should handle method calls appropriately
        assert test.name == "test_method_call"
    
    def test_visit_test_with_complex_expressions(self):
        """Test visiting test with complex expressions."""
        code = """
def test_complex_expressions():
    data = [x for x in range(10) if x % 2 == 0]
    result = transform(data)
    assert sum(result) > 0 and len(result) == 5
"""
        tree = ast.parse(code)
        visitor = TestVisitor()
        visitor.visit(tree)
        
        assert len(visitor.tests) == 1
        test = visitor.tests[0]
        assert test.name == "test_complex_expressions"
        assert "data" in test.inputs


class TestParseTestFile:
    """Test cases for parse_test_file function."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        import tempfile
        import shutil
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_parse_test_file_success(self, temp_dir):
        """Test parsing a test file successfully."""
        test_file = temp_dir / "test_example.py"
        test_file.write_text("""
def test_addition():
    a = 5
    b = 3
    result = add(a, b)
    assert result == 8

def test_subtraction():
    x = 10
    y = 4
    result = subtract(x, y)
    assert result == 6
""")
        
        result = parse_test_file(test_file)
        
        assert result["success"] is True
        assert len(result["tests"]) == 2
        
        # Check first test
        test1 = result["tests"][0]
        assert test1.name == "test_addition"
        assert test1.target_function == "add"
        assert test1.inputs == {"a": 5, "b": 3}
        
        # Check second test
        test2 = result["tests"][1]
        assert test2.name == "test_subtraction"
        assert test2.target_function == "subtract"
        assert test2.inputs == {"x": 10, "y": 4}
    
    def test_parse_test_file_not_found(self):
        """Test parsing a non-existent test file."""
        non_existent = Path("non_existent.py")
        
        result = parse_test_file(non_existent)
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()
    
    def test_parse_test_file_syntax_error(self, temp_dir):
        """Test parsing a test file with syntax errors."""
        test_file = temp_dir / "test_syntax_error.py"
        test_file.write_text("""
def test_broken()
    # Missing colon
    print("hello")
    assert True
    """)
        
        result = parse_test_file(test_file)
        
        assert result["success"] is False
        assert "error" in result
        assert "syntax" in result["error"].lower()
    
    def test_parse_test_file_empty(self, temp_dir):
        """Test parsing an empty test file."""
        test_file = temp_dir / "test_empty.py"
        test_file.write_text("")
        
        result = parse_test_file(test_file)
        
        assert result["success"] is True
        assert len(result["tests"]) == 0
    
    def test_parse_test_file_no_tests(self, temp_dir):
        """Test parsing a file with no test functions."""
        test_file = temp_dir / "no_tests.py"
        test_file.write_text("""
def helper_function():
    return "helper"

def utility():
    pass
""")
        
        result = parse_test_file(test_file)
        
        assert result["success"] is True
        assert len(result["tests"]) == 0


class TestParseTestMain:
    """Test cases for main function in parse_tests."""
    
    def test_main_function_exists(self):
        """Test that main function exists."""
        from ..parse_tests import main
        assert callable(main)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])