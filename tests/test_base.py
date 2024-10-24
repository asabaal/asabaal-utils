import pytest
from pathlib import Path
import types
from unittest.mock import Mock, patch
from asabaal_utils import find_package_location

class TestFindPackageLocation:
    """
    Test suite for the find_package_location function.

    This test suite verifies the functionality of the find_package_location function,
    which locates the installation directory of Python packages. It provides comprehensive
    coverage of both successful and error cases through systematic testing of input
    variations and edge cases.

    Test Case Selection Rationale
    ----------------------------
    The test cases were selected using the following systematic approach:

    1. Input Type Coverage:
        - String inputs (valid package names)
        - Module object inputs (already imported modules)
        - Invalid type inputs (numbers, None, etc.)
        This ensures all possible input types are tested.

    2. Valid Cases:
        - Standard library packages (guaranteed to exist)
        - Custom module paths
        - Packages with dot notation
        These cover the main success scenarios users will encounter.

    3. Error Cases:
        - Non-existent packages
        - Empty/whitespace package names
        - Built-in modules without file paths
        - Import failures
        These verify proper error handling for all expected failure modes.

    4. Edge Cases:
        - Modules without __name__ attribute
        - Custom installation paths
        - Various string format variations
        These ensure robustness against unusual but possible scenarios.

    Methods
    -------
    test_valid_string_input
        Test function behavior with valid package name strings.
    test_valid_module_input
        Test function behavior with valid module objects.
    test_nonexistent_package
        Test handling of non-installed packages.
    test_invalid_input_type
        Test handling of invalid input types.
    test_builtin_module
        Test handling of built-in modules.
    test_import_error
        Test handling of import errors.
    test_module_with_custom_path
        Test handling of modules with custom installation paths.
    test_valid_package_names
        Test handling of various valid package name formats.
    test_invalid_package_names
        Test handling of invalid package name formats.
    test_none_input
        Test handling of None input.
    test_module_without_name
        Test handling of modules without __name__ attribute.

    Notes
    -----
    - All test methods use type hints for better code clarity
    - Mock objects are used to simulate modules without creating real ones
    - pytest.raises contexts verify proper exception handling
    - Parametrized tests are used for related input variations
    """

    def test_valid_string_input(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a valid package name as string.

        This test verifies that when given a valid package name (like 'os'),
        the function successfully returns the path to the package's installation
        directory. The 'os' package is used because it's part of Python's standard
        library and therefore guaranteed to be available.
        """
        # Call the function with 'os' package name and store the result
        result: str = find_package_location('os')
        
        # Verify that the result is a string (not None or another type)
        assert isinstance(result, str)
        
        # Convert the result to a Path object and check if it exists on the filesystem
        assert Path(result).exists()

    def test_valid_module_input(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a valid module object.

        This test verifies that the function works correctly when given an already
        imported module object instead of a string name. It uses the 'json' module
        as a test case since it's guaranteed to be available in Python's standard
        library.
        """
        # Import the json module to use as a test case
        import json
        
        # Call the function with the imported module object
        result: str = find_package_location(json)
        
        # Verify the result type and existence of the path
        assert isinstance(result, str)
        assert Path(result).exists()

    def test_nonexistent_package(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a package name that doesn't exist.

        This test verifies that the function raises an ImportError when trying
        to locate a package that isn't installed in the Python environment.
        We use a deliberately invalid package name to trigger this error.

        Raises
        ------
        ImportError
            Expected when the package doesn't exist in the Python environment.
        """
        # pytest.raises is a context manager that verifies an exception is raised
        # In this case, we expect an ImportError when trying to find a non-existent package
        with pytest.raises(ImportError):
            find_package_location('nonexistent_package_xyz')

    def test_invalid_input_type(self: "TestFindPackageLocation") -> None:
        """
        Test the function with invalid input type.

        This test ensures that the function properly handles invalid input types
        by raising a TypeError. We test this by passing an integer (123) instead
        of the expected string or module object.

        Raises
        ------
        TypeError
            Expected when the input type is neither string nor module.
        """
        # Test with an integer (invalid type) and capture the error details
        with pytest.raises(TypeError) as exc_info:
            # type: ignore tells the type checker to ignore this line
            # since we're deliberately passing the wrong type for testing
            find_package_location(123)  # type: ignore
            
        # Verify the error message contains the expected text
        assert "must be a string" in str(exc_info.value)

    def test_builtin_module(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a built-in module that lacks __file__ attribute.

        This test verifies that the function properly handles built-in modules
        that don't have a __file__ attribute (which normally points to the module's
        location on disk). Built-in modules are implemented in C and don't have
        corresponding Python files.

        Raises
        ------
        AttributeError
            Expected when trying to access the non-existent __file__ attribute.
        """
        # Create a mock module object that simulates a built-in module
        mock_module: Mock = Mock(spec=types.ModuleType)
        mock_module.__name__ = 'sys'  # Give it a name like a real module
        delattr(mock_module, '__file__')  # Remove the __file__ attribute
        
        # Verify that the function raises AttributeError for this case
        with pytest.raises(AttributeError) as exc_info:
            find_package_location(mock_module)
            
        # Check that the error message includes helpful information
        assert "Unable to determine the location" in str(exc_info.value)
        assert "built-in module" in str(exc_info.value)

    @patch('importlib.import_module')  # Decorator that replaces import_module with a mock
    def test_import_error(self: "TestFindPackageLocation", mock_import: Mock) -> None:
        """
        Test the function's handling of ImportError.

        This test verifies that the function properly handles cases where
        importing a package fails. We use unittest.mock to simulate an import
        failure without needing an actual failing import.

        Parameters
        ----------
        mock_import : Mock
            A mock object that replaces importlib.import_module for this test.
            When called, it will raise an ImportError.

        Raises
        ------
        ImportError
            Expected when the module import fails.
        """
        # Configure the mock to raise ImportError when called
        mock_import.side_effect = ImportError("Mock import error")
        
        # Verify that the function propagates the ImportError
        with pytest.raises(ImportError):
            find_package_location('package_causing_import_error')

    def test_module_with_custom_path(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a module that has a custom __file__ path.

        This test verifies that the function correctly handles modules installed
        in non-standard locations by properly parsing their file paths. It uses
        a mock module with a custom file path to simulate this scenario.
        """
        # Create a mock module with a custom file path
        mock_module: Mock = Mock(spec=types.ModuleType)
        mock_module.__file__ = '/usr/local/lib/python3.8/site-packages/custom_package/__init__.py'
        
        # Call the function and verify it returns the expected path
        result: str = find_package_location(mock_module)
        assert isinstance(result, str)
        assert result == '/usr/local/lib/python3.8'

    @pytest.mark.parametrize("package_name", ["package.with.dots"])
    def test_valid_package_names(self: "TestFindPackageLocation", package_name: str) -> None:
        """
        Test the function with valid package names containing dots.

        This test verifies that the function correctly handles package names
        that include dot notation (e.g., 'package.subpackage'). Since we're
        using a non-existent package, we expect an ImportError.

        Parameters
        ----------
        package_name : str
            The package name to test, including dots.

        Raises
        ------
        ImportError
            Expected since the test package doesn't exist.
        """
        # Attempt to find location of a dotted package name (which doesn't exist)
        with pytest.raises(ImportError):
            find_package_location(package_name)

    @pytest.mark.parametrize("invalid_name", [
        "",  # Empty string
        "   ",  # Whitespace only
        "\n",  # Just a newline
    ])
    def test_invalid_package_names(self: "TestFindPackageLocation", invalid_name: str) -> None:
        """
        Test the function with invalid package names.

        This test verifies that the function raises appropriate errors when given
        invalid package names such as empty strings, whitespace-only strings, or
        strings containing only newline characters.

        Parameters
        ----------
        invalid_name : str
            The invalid package name to test.

        Raises
        ------
        ValueError
            Expected when the package name is empty or whitespace-only.
        """
        # Verify that empty or whitespace-only names raise ValueError
        with pytest.raises(ValueError) as exc_info:
            find_package_location(invalid_name)
        assert "Empty module name" in str(exc_info.value)

    def test_none_input(self: "TestFindPackageLocation") -> None:
        """
        Test the function with None input.

        This test verifies that the function properly handles the case where
        None is passed as an argument instead of a string or module object.
        This should raise a TypeError.

        Raises
        ------
        TypeError
            Expected when the input is None.
        """
        # Verify that None input raises TypeError
        with pytest.raises(TypeError) as exc_info:
            find_package_location(None)  # type: ignore
        assert "must be a string" in str(exc_info.value)

    def test_module_without_name(self: "TestFindPackageLocation") -> None:
        """
        Test the function with a module that doesn't have __name__ attribute.

        This test verifies that the function can still return a valid path
        even when the module object is missing its __name__ attribute. This
        is an edge case that could occur with certain types of mock or
        custom modules.
        """
        # Create a mock module without a __name__ attribute but with a valid path
        mock_module: Mock = Mock(spec=types.ModuleType)
        mock_module.__file__ = '/path/to/module/__init__.py'
        delattr(mock_module, '__name__')
        
        # Verify that the function still returns the correct parent path
        result: str = find_package_location(mock_module)
        assert isinstance(result, str)
        assert result == '/path'  # Three levels up from /path/to/module/__init__.py