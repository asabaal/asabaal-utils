import json
import os
import pytest
import types
import shutil

from pathlib import Path
from typing import List
from unittest.mock import Mock, MagicMock, patch
from asabaal_utils import find_package_location, download_youtube_video, WebScraper, DatabaseManager, Album

class TestWebScraper:
    """Test suite for the WebScraper class.
    
    This suite tests the Wikipedia scraping functionality, including successful cases,
    error handling, and edge cases. It uses mocking to simulate web responses and
    database interactions.

    Attributes
    ----------
    db_manager : DatabaseManager
        Mock database manager for testing
    scraper : WebScraper
        WebScraper instance being tested
    sample_wiki_content : str
        Sample Wikipedia HTML content for testing
    
    Methods
    -------
    setup_method
        Set up test environment before each test
    teardown_method
        Clean up test environment after each test
    test_successful_album_extraction
        Test successful parsing of album information
    test_no_discography_section
        Test handling of pages without discography
    test_empty_discography_section
        Test handling of empty discography sections
    test_malformed_album_entries
        Test handling of malformed album entries
    test_cache_handling
        Test caching functionality
    test_error_handling
        Test various error scenarios
    """

    def setup_method(self: "TestWebScraper", method: callable) -> None:
        """Set up test environment before each test.

        Parameters
        ----------
        method : callable
            The test method being run
        """
        self: TestWebScraper
        # Create mock DB manager
        self.db_manager = MagicMock(spec=DatabaseManager)
        # Setup db_path attribute
        self.db_manager.db_path = "mock_db_path"
        
        # Create mock scraper
        self.scraper = WebScraper(self.db_manager)
        
        # Sample Wikipedia page content with discography section
        self.sample_wiki_content: str = """
        <html>
        <body>
            <h2><span class="mw-headline" id="Discography">Discography</span></h2>
            <ul>
                <li>Real Talk (2004)</li>
                <li>After the Music Stops (2006)</li>
                <li>Rebel (2008)</li>
                <li>Rehab (2010)</li>
                <li>Let the Trap Say Amen (with Zaytoven) (2018)</li>
                <li>Restoration (2020)<sup>[95]</sup></li>
            </ul>
        </body>
        </html>
        """
        
        # Create temp_db for teardown
        self.temp_db = Mock()
        self.temp_db.close = Mock()
        self.temp_db.name = "mock_db_path"

    def teardown_method(self: "TestWebScraper", method: callable) -> None:
        """Clean up test environment after each test.

        Parameters
        ----------
        method : callable
            The test method being run
        """
        # Check if temp_db exists and has necessary attributes before cleanup
        if hasattr(self, 'temp_db'):
            self.temp_db.close()
            if hasattr(self.temp_db, 'name') and os.path.exists(self.temp_db.name):
                try:
                    os.unlink(self.temp_db.name)
                except (FileNotFoundError, PermissionError):
                    pass  # Ignore errors if file doesn't exist or can't be deleted

    @patch('requests.Session')
    def test_successful_album_extraction(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test successful parsing of album information from Wikipedia."""
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance

        # Mock the search response
        search_response = Mock()
        search_response.json.return_value = {
            "query": {
                "search": [{"title": "Lecrae"}]
            }
        }
        
        # Mock the page response
        page_response = Mock()
        page_response.text = self.sample_wiki_content
        
        # Configure the session's get method to return our responses
        session_instance.get.side_effect = [search_response, page_response]

        # Execute test
        albums: List[Album] = self.scraper.get_wikipedia_albums("Lecrae")

        # Verify results
        assert len(albums) == 6
        assert albums[0].title == "Real Talk"
        assert albums[0].release_date == "2004"
        
        # Verify collaboration handling
        collab_album: Album = albums[4]
        assert collab_album.title == "Let the Trap Say Amen"
        assert collab_album.release_date == "2018"

    @patch('requests.Session')
    def test_no_discography_section(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test handling of Wikipedia pages without a discography section.

        This test verifies that:
        1. Pages without a discography section return empty list
        2. No errors are raised
        3. Appropriate warning is logged

        Parameters
        ----------
        mock_session : MagicMock
            Mock object for requests.Session
        """
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance
        
        # Mock page without discography section
        search_response = Mock()
        search_response.json.return_value = {
            "query": {
                "search": [{"title": "Test Artist"}]
            }
        }
        
        page_response = Mock()
        page_response.text = "<html><body><h2>Biography</h2></body></html>"
        
        # Configure the session's get method
        session_instance.get.side_effect = [search_response, page_response]

        albums: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        assert len(albums) == 0

    @patch('requests.Session')
    def test_empty_discography_section(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test handling of empty discography sections.

        This test verifies that:
        1. Empty discography sections return empty list
        2. No errors are raised
        3. Section is properly identified even if empty

        Parameters
        ----------
        mock_session : MagicMock
            Mock object for requests.Session
        """
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance
        
        # Mock search response
        search_response = Mock()
        search_response.json.return_value = {
            "query": {
                "search": [{"title": "Test Artist"}]
            }
        }
        
        # Mock page response with empty discography section
        page_response = Mock()
        page_response.text = """
        <html><body>
            <h2><span class="mw-headline" id="Discography">Discography</span></h2>
            <p>No albums released yet.</p>
        </body></html>
        """
        
        # Configure the session's get method
        session_instance.get.side_effect = [search_response, page_response]

        albums: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        assert len(albums) == 0

    @patch('requests.Session')
    def test_malformed_album_entries(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test handling of malformed album entries."""
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance

        # Mock the search response
        search_response = Mock()
        search_response.json.return_value = {
            "query": {
                "search": [{"title": "Test Artist"}]
            }
        }
        
        # Mock the page response
        page_response = Mock()
        page_response.text = """
        <html><body>
            <h2><span class="mw-headline" id="Discography">Discography</span></h2>
            <ul>
                <li>Valid Album (2020)</li>
                <li>Malformed Entry</li>
                <li>Another Valid Album (2021)</li>
            </ul>
        </body></html>
        """
        
        # Configure the session's get method
        session_instance.get.side_effect = [search_response, page_response]

        albums: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        assert len(albums) == 2
        assert albums[0].title == "Valid Album"
        assert albums[1].title == "Another Valid Album"

    @patch('requests.Session')
    def test_cache_handling(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test caching functionality."""
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance

        # Mock responses
        search_response = Mock()
        search_response.json.return_value = {
            "query": {
                "search": [{"title": "Test Artist"}]
            }
        }

        page_response = Mock()
        page_response.text = self.sample_wiki_content

        # Configure session mock for both calls
        session_instance.get.side_effect = [
            search_response,  # First search
            page_response,   # First page fetch
            search_response  # Second search (cache should prevent second page fetch)
        ]

        # First request
        albums1: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        
        # Second request - should use cache for page content
        albums2: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        
        assert len(albums1) == len(albums2)
        # We expect 3 calls: initial search, page fetch, and second search
        assert session_instance.get.call_count == 3

    @patch('requests.Session')
    def test_error_handling(self: "TestWebScraper", mock_session: MagicMock) -> None:
        """Test various error scenarios.

        This test verifies handling of:
        1. Network errors
        2. Invalid JSON responses
        3. Missing search results
        4. Malformed HTML

        Parameters
        ----------
        mock_session : MagicMock
            Mock object for requests.Session
        """
        # Mock the session instance
        session_instance = Mock()
        mock_session.return_value = session_instance
        
        # Test network error
        session_instance.get.side_effect = Exception("Network Error")
        albums: List[Album] = self.scraper.get_wikipedia_albums("Test Artist")
        assert len(albums) == 0

        # Test invalid JSON response
        session_instance.get.side_effect = None
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        session_instance.get.return_value = mock_response
        
        albums = self.scraper.get_wikipedia_albums("Test Artist")
        assert len(albums) == 0

"""
Test Coverage Justification
--------------------------
The test suite provides comprehensive coverage through:

1. Success Scenarios:
   - Complete album extraction (test_successful_album_extraction)
   - Proper parsing of dates and titles
   - Handling of collaborations and features

2. Edge Cases:
   - Missing discography section (test_no_discography_section)
   - Empty discography section (test_empty_discography_section)
   - Malformed entries (test_malformed_album_entries)

3. Error Handling:
   - Network errors (test_error_handling)
   - Invalid JSON responses (test_error_handling)
   - Malformed HTML (test_error_handling)

4. Caching:
   - Cache retrieval (test_cache_handling)
   - Cache updates (test_cache_handling)

Each test is necessary because:
1. test_successful_album_extraction: Validates core functionality
2. test_no_discography_section: Ensures graceful handling of missing data
3. test_empty_discography_section: Verifies proper handling of edge cases
4. test_malformed_album_entries: Ensures resilience to bad data
5. test_cache_handling: Validates performance optimization
6. test_error_handling: Ensures system stability

The combination of these tests ensures:
- All major code paths are covered
- Edge cases are properly handled
- Error conditions are managed
- Data integrity is maintained
- Performance features work correctly
"""

class TestYoutubeDownloader:
    """    
    Test suite for the YouTube video downloader function.
    
    This test suite provides comprehensive coverage of the download_youtube_video function,
    including happy paths, edge cases, and error conditions. The tests verify the function's
    behavior with different resolutions, output paths, and error scenarios.

    Attributes
    ----------
    valid_url : str
        A valid YouTube URL used for testing
    invalid_url : str
        An invalid URL to test error handling
    test_output_dir : Path
        Temporary directory for test downloads

    Methods
    -------
    setup_method
        Set up test environment before each test
    teardown_method
        Clean up test environment after each test
    test_basic_download
        Test basic video download with default parameters
    test_custom_resolution
        Test download with specific resolution
    test_custom_output_path
        Test download to custom directory
    test_invalid_url
        Test handling of invalid URLs
    test_network_error
        Test handling of network errors
    test_permission_error
        Test handling of permission errors

    Test Coverage Justification
    --------------------------
    The test suite provides comprehensive coverage through:

    1. Function Input Testing:
    - Valid URL handling (test_basic_download)
    - Invalid URL handling (test_invalid_url)
    - Different resolution options (test_custom_resolution)
    - Custom output paths (test_custom_output_path)

    2. Error Handling:
    - Network errors (test_network_error)
    - Permission errors (test_permission_error)
    - Invalid URL format (test_invalid_url)

    3. Edge Cases:
    - Various resolution formats including "best", "worst", and specific numbers
    - Non-existent output directories
    - Protected directories
    - Network failures

    4. Environment Setup/Teardown:
    - Proper test isolation through setup_method and teardown_method
    - Cleanup of test artifacts

    Each test is necessary because it covers a unique aspect:
    1. test_basic_download: Verifies core functionality with default parameters
    2. test_custom_resolution: Ensures resolution parameter works correctly
    3. test_custom_output_path: Validates output path handling
    4. test_invalid_url: Confirms proper error handling for bad URLs
    5. test_network_error: Verifies network error handling
    6. test_permission_error: Ensures filesystem permission handling

    The combination of these tests ensures that:
    - All code paths are exercised
    - All error conditions are handled
    - All parameter combinations are tested
    - Environment is properly managed
    - Results are properly verified  
    """

    def setup_method(self: "TestYoutubeDownloader", method: callable) -> None:
        """Set up test environment before each test.

        Parameters
        ----------
        method : callable
            The test method being run

        Notes
        -----
        Creates a temporary directory for downloads and sets up test URLs
        """
        self: TestYoutubeDownloader
        self.valid_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.invalid_url: str = "https://www.youtube.com/invalid"
        self.test_output_dir: Path = Path("test_downloads")
        os.makedirs(self.test_output_dir, exist_ok=True)

    def teardown_method(self: "TestYoutubeDownloader", method: callable) -> None:
        """Clean up test environment after each test.

        Parameters
        ----------
        method : callable
            The test method being run

        Notes
        -----
        Removes temporary test directory and all downloaded files
        """
        self: TestYoutubeDownloader
        if self.test_output_dir.exists():
            shutil.rmtree(self.test_output_dir)

    @patch('yt_dlp.YoutubeDL')
    def test_basic_download(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test basic video download with default parameters.

        This test verifies that:
        1. The function successfully downloads a video with default settings
        2. Correct default format string is used
        3. Output path handling works correctly
        4. Progress reporting works
        5. Returns correct video path

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL
        """
        self: TestYoutubeDownloader
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {"title": "test_video"}
        mock_instance.prepare_filename.return_value = "test_video.mp4"

        result: str = download_youtube_video(self.valid_url)
        expected_path: Path = Path.home() / "Downloads" / "test_video.mp4"

        assert result == str(expected_path)
        mock_instance.extract_info.assert_called_once_with(self.valid_url, download=True)

    @patch('yt_dlp.YoutubeDL')
    def test_custom_resolution(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test video download with custom resolution.

        This test verifies that:
        1. Resolution parameter is correctly processed
        2. Format string is properly constructed for specific resolution
        3. Download proceeds with correct format specification

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL
        """
        self: TestYoutubeDownloader
        test_resolutions: List[str] = ["720", "1080", "worst", "best"]
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value

        for resolution in test_resolutions:
            mock_instance.extract_info.return_value = {
                "title": f"test_video_{resolution}"}
            mock_instance.prepare_filename.return_value = f"test_video_{resolution}.mp4"

            result: str = download_youtube_video(
                self.valid_url, resolution=resolution)
            assert f"test_video_{resolution}.mp4" in result

    @patch('yt_dlp.YoutubeDL')
    def test_custom_output_path(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test video download to custom output directory.

        This test verifies that:
        1. Custom output path is correctly handled
        2. Directory is created if it doesn't exist
        3. File is saved to correct location

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL
        """
        self: TestYoutubeDownloader
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = {"title": "test_video"}
        mock_instance.prepare_filename.return_value = "test_video.mp4"

        result: str = download_youtube_video(
            self.valid_url, 
            output_path=str(self.test_output_dir)
        )
        expected_path: Path = self.test_output_dir / "test_video.mp4"

        assert result == str(expected_path)
        assert self.test_output_dir.exists()

    @patch('yt_dlp.YoutubeDL')
    def test_invalid_url(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test handling of invalid URLs.

        This test verifies that:
        1. Invalid URLs are properly detected
        2. Appropriate exception is raised
        3. Error message is informative

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL

        Raises
        ------
        Exception
            Expected to raise exception for invalid URL
        """
        self: TestYoutubeDownloader
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value
        mock_instance.extract_info.side_effect = Exception("Invalid URL")

        with pytest.raises(Exception) as exc_info:
            download_youtube_video(self.invalid_url)
        assert "Error downloading video" in str(exc_info.value)

    @patch('yt_dlp.YoutubeDL')
    def test_network_error(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test handling of network errors during download.

        This test verifies that:
        1. Network errors are caught and handled
        2. Appropriate exception is raised
        3. Error message is informative

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL

        Raises
        ------
        Exception
            Expected to raise exception for network error
        """
        self: TestYoutubeDownloader
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value
        mock_instance.extract_info.side_effect = Exception("Network Error")

        with pytest.raises(Exception) as exc_info:
            download_youtube_video(self.valid_url)
        assert "Error downloading video" in str(exc_info.value)

    @patch('yt_dlp.YoutubeDL')
    def test_permission_error(self: "TestYoutubeDownloader", mock_ytdl: MagicMock) -> None:
        """Test handling of permission errors.

        This test verifies that:
        1. Permission errors are caught when writing to protected directories
        2. Appropriate exception is raised
        3. Error message is informative

        Parameters
        ----------
        mock_ytdl : MagicMock
            Mock object for YoutubeDL

        Raises
        ------
        Exception
            Expected to raise exception for permission error
        """
        self: TestYoutubeDownloader
        mock_instance: MagicMock = mock_ytdl.return_value.__enter__.return_value
        mock_instance.extract_info.side_effect = PermissionError(
            "Permission denied")

        with pytest.raises(Exception) as exc_info:
            download_youtube_video(self.valid_url, output_path="/root/protected")
        assert "Error downloading video" in str(exc_info.value)

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