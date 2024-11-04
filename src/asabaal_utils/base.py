import importlib
import json
import logging
import os
import pathspec
import re
import requests
import sqlite3
import types
import yt_dlp

from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from typing import Dict, List, Optional
from urllib.parse import quote, urljoin

@dataclass
class Album:
    """
    Data class representing an album with its metadata.

    Parameters
    ----------
    title : str
        The album title
    release_date : str
        Release date in YYYY-MM-DD format
    album_type : str
        Type of album (e.g., studio, live, compilation)
    sources : List[str]
        List of sources where this album was found
    tracks : List[str]
        List of track titles
    url : Optional[str]
        URL to the album
    artist : str
        Name of the artist
    last_updated : str
        Timestamp of last update
    """
    title: str
    release_date: str
    album_type: str
    sources: List[str]
    tracks: List[str]
    artist: str
    url: Optional[str] = None
    last_updated: str = datetime.now().isoformat()

class DatabaseManager:
    """
    Handles all database operations for storing and retrieving music data.

    Parameters
    ----------
    db_path : str
        Path to SQLite database file
    """
    
    def __init__(self, db_path: str = "music_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY,
                    artist TEXT NOT NULL,
                    title TEXT NOT NULL,
                    release_date TEXT,
                    album_type TEXT,
                    sources TEXT,
                    tracks TEXT,
                    url TEXT,
                    last_updated TEXT,
                    UNIQUE(artist, title)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT PRIMARY KEY,
                    content TEXT,
                    timestamp TEXT
                )
            """)

    def save_album(self, album: Album) -> None:
        """
        Save album to database.

        Parameters
        ----------
        album : Album
            Album to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO albums 
                (artist, title, release_date, album_type, sources, tracks, url, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                album.artist,
                album.title,
                album.release_date,
                album.album_type,
                json.dumps(album.sources),
                json.dumps(album.tracks),
                album.url,
                album.last_updated
            ))

    def get_artist_albums(self, artist: str) -> List[Album]:
        """
        Retrieve all albums for an artist.

        Parameters
        ----------
        artist : str
            Artist name

        Returns
        -------
        List[Album]
            List of albums found in database
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM albums WHERE artist = ? ORDER BY release_date",
                (artist,)
            )
            return [Album(
                artist=row['artist'],
                title=row['title'],
                release_date=row['release_date'],
                album_type=row['album_type'],
                sources=json.loads(row['sources']),
                tracks=json.loads(row['tracks']),
                url=row['url'],
                last_updated=row['last_updated']
            ) for row in cursor.fetchall()]

class WebScraper:
    """
    Enhanced web scraper with better section targeting.

    Parameters
    ----------
    db_manager : DatabaseManager
        Database manager instance for caching
    cache_duration : int
        How long to cache results in seconds (default: 1 day)
    """

    def __init__(self, db_manager: DatabaseManager, cache_duration: int = 86400):
        self.db_manager = db_manager
        self.cache_duration = cache_duration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MusicDataAggregator/1.0 (Educational Purpose)'
        })

    def _get_cached_or_fetch(self, url: str) -> str:
        """
        Get content from cache or fetch from web.

        Parameters
        ----------
        url : str
            URL to fetch

        Returns
        -------
        str
            Page content
        """
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT content, timestamp FROM cache WHERE url = ?",
                (url,)
            )
            result = cursor.fetchone()
            
            if result:
                content, timestamp = result
                cached_time = datetime.fromisoformat(timestamp)
                if (datetime.now() - cached_time).seconds < self.cache_duration:
                    return content

        response = self.session.get(url)
        response.raise_for_status()
        content = response.text
        
        with sqlite3.connect(self.db_manager.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (url, content, timestamp) VALUES (?, ?, ?)",
                (url, content, datetime.now().isoformat())
            )
        
        return content

    def get_wikipedia_albums(self, artist: str) -> List[Album]:
        """
        Scrape album information from Wikipedia using section targeting.

        Parameters
        ----------
        artist : str
            Artist name

        Returns
        -------
        List[Album]
            List of albums found on Wikipedia
        """
        try:
            # First, get the base Wikipedia URL for the artist
            search_url = f"https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{artist} musician",
                "utf8": 1
            }
            
            response = self.session.get(search_url, params=params)
            data = response.json()
            
            if not data.get("query", {}).get("search"):
                return []

            # Get the page title and construct the URL with the Discography section
            title = data["query"]["search"][0]["title"]
            wiki_url = f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}#Discography"
            
            # Fetch the page content
            content = self._get_cached_or_fetch(wiki_url)
            soup = BeautifulSoup(content, 'html.parser')
            albums: List[Album] = []

            # Find the Discography section using its ID
            discography_section = soup.find(id='Discography')
            if not discography_section:
                logging.warning(f"No Discography section found for {artist}")
                return albums

            # Get the section content (everything up to the next h2)
            current = discography_section.parent  # The h2 containing "Discography"
            section_content = []
            for sibling in current.find_next_siblings():
                if sibling.name == 'h2':
                    break
                section_content.append(sibling)

            # Look for album lists within the section
            for element in section_content:
                if element.name == 'ul':
                    for item in element.find_all('li', recursive=False):
                        # Remove reference tags and notes
                        [ref.decompose() for ref in item.find_all(['sup', 'small'])]
                        text = item.get_text().strip()
                        
                        # Match pattern: Album Name (Year) or Album Name (with Artist) (Year)
                        match = re.search(r'^[*•]?\s*(.+?)\s*(?:\((?:with|featuring|feat\.?).*?\))?\s*\((\d{4})\)', text)
                        
                        if match:
                            title, year = match.groups()
                            # Clean up title
                            title = title.strip('*• ')
                            
                            albums.append(Album(
                                title=title,
                                release_date=year,
                                album_type='studio',
                                sources=['Wikipedia'],
                                tracks=[],
                                artist=artist,
                                url=wiki_url
                            ))

            return albums

        except Exception as e:
            logging.error(f"Error scraping Wikipedia for {artist}: {str(e)}")
            logging.debug(f"Error details: {str(e)}", exc_info=True)
            return []
        
    def _get_discogs_page_url(self, artist: str) -> Optional[str]:
        """
        Find the correct Discogs page URL for an artist.

        Parameters
        ----------
        artist : str
            Artist name

        Returns
        -------
        Optional[str]
            Discogs artist URL if found
        """
        search_url = "https://api.discogs.com/database/search"
        params = {
            "q": artist,
            "type": "artist",
            "per_page": 1
        }
        
        try:
            response = self.session.get(search_url, params=params)
            data = response.json()
            
            if data.get("results"):
                return data["results"][0].get("uri")
        except Exception as e:
            logging.error(f"Error finding Discogs page for {artist}: {str(e)}")
        
        return None


    def get_discogs_albums(self, artist: str) -> List[Album]:
        """
        Enhanced Discogs scraping with better artist page detection.

        Parameters
        ----------
        artist : str
            Artist name

        Returns
        -------
        List[Album]
            List of albums found on Discogs
        """
        discogs_url = self._get_discogs_page_url(artist)
        if not discogs_url:
            return []

        try:
            content = self._get_cached_or_fetch(discogs_url)
            soup = BeautifulSoup(content, 'html.parser')
            albums: List[Album] = []

            # Find the releases section
            releases_section = soup.find(id='artist-releases') or soup.find(class_='releases')
            if releases_section:
                for release in releases_section.find_all(class_=['release', 'card']):
                    title_elem = release.find(class_=['title', 'release-title'])
                    date_elem = release.find(class_=['year', 'release-year'])
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        date = date_elem.get_text().strip() if date_elem else ""
                        
                        # Try to determine album type
                        album_type = 'unknown'
                        format_elem = release.find(class_=['format', 'release-format'])
                        if format_elem:
                            format_text = format_elem.get_text().lower()
                            if 'lp' in format_text or 'album' in format_text:
                                album_type = 'studio'
                            elif 'live' in format_text:
                                album_type = 'live'
                            elif 'compilation' in format_text:
                                album_type = 'compilation'

                        albums.append(Album(
                            title=title,
                            release_date=date,
                            album_type=album_type,
                            sources=['Discogs'],
                            tracks=[],
                            artist=artist,
                            url=urljoin(discogs_url, release.get('href', ''))
                        ))

            return albums

        except Exception as e:
            logging.error(f"Error scraping Discogs for {artist}: {str(e)}")
            return []        
        
class CommunityDataManager:
    """
    Handles loading and managing community-provided data files.

    Parameters
    ----------
    data_dir : str
        Directory containing community data files
    """

    def __init__(self, data_dir: str = "community_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def load_community_data(self, artist: str) -> List[Album]:
        """
        Load album data from community files.

        Parameters
        ----------
        artist : str
            Artist name

        Returns
        -------
        List[Album]
            List of albums found in community data
        """
        albums: List[Album] = []
        
        # Try JSON files first
        artist_file = self.data_dir / f"{artist.lower().replace(' ', '_')}.json"
        if artist_file.exists():
            with open(artist_file) as f:
                data = json.load(f)
                for album_data in data.get('albums', []):
                    albums.append(Album(
                        **{**album_data, 'sources': ['Community Data']}
                    ))

        return albums

class MusicDataAggregator:
    """
    Main class that coordinates data collection from all sources.

    Parameters
    ----------
    db_path : str
        Path to SQLite database
    data_dir : str
        Path to community data directory
    """

    def __init__(self, db_path: str = "music_data.db", data_dir: str = "community_data"):
        self.db_manager = DatabaseManager(db_path)
        self.web_scraper = WebScraper(self.db_manager)
        self.community_data = CommunityDataManager(data_dir)

    def get_artist_discography(self, artist: str, force_refresh: bool = False) -> List[Album]:
        """
        Get complete discography from all sources.

        Parameters
        ----------
        artist : str
            Artist name
        force_refresh : bool
            Whether to force refresh from sources

        Returns
        -------
        List[Album]
            Combined list of unique albums
        """
        if not force_refresh:
            cached_albums = self.db_manager.get_artist_albums(artist)
            if cached_albums:
                return cached_albums

        # Collect from all sources
        wikipedia_albums = self.web_scraper.get_wikipedia_albums(artist)
        discogs_albums = self.web_scraper.get_discogs_albums(artist)
        community_albums = self.community_data.load_community_data(artist)

        # Combine and deduplicate
        all_albums: Dict[str, Album] = {}
        
        for album in wikipedia_albums + discogs_albums + community_albums:
            key = f"{album.title.lower()}_{album.release_date}"
            if key in all_albums:
                existing = all_albums[key]
                existing.sources = list(set(existing.sources + album.sources))
                if album.tracks:
                    existing.tracks = list(set(existing.tracks + album.tracks))
                if not existing.url and album.url:
                    existing.url = album.url
            else:
                all_albums[key] = album

        # Save to database
        for album in all_albums.values():
            self.db_manager.save_album(album)

        return list(all_albums.values())

def format_discography(albums: List[Album]) -> str:
    """
    Format discography data as a readable string.

    Parameters
    ----------
    albums : List[Album]
        List of albums to format

    Returns
    -------
    str
        Formatted string representation of the discography
    """
    if not albums:
        return "No albums found."

    output = []
    for album in sorted(albums, key=lambda x: x.release_date or "9999"):
        output.append(f"\nAlbum: {album.title}")
        if album.release_date:
            output.append(f"Released: {album.release_date}")
        output.append(f"Sources: {', '.join(album.sources)}")
        if album.url:
            output.append(f"URL: {album.url}")
        if album.tracks:
            output.append("\nTracks:")
            for i, track in enumerate(album.tracks, 1):
                output.append(f"{i}. {track}")
        output.append("-" * 50)

    return "\n".join(output)

def download_youtube_video(url, output_path=None, resolution="best"):
    """
    Download a YouTube video from the given URL using yt-dlp.

    Parameters
    ----------
    url : str
        The URL of the YouTube video to download
    output_path : str, optional
        Directory to save the video. If None, saves to Downloads folder
    resolution : str, optional
        Desired resolution for the video download. Options:
            - "best": Highest available quality (default)
            - "worst": Lowest available quality
            - "720", "1080", etc.: Specific resolution (without 'p')

    Returns
    -------
    str
        Full path to the downloaded video file

    Raises
    ------
    Exception
        If video cannot be downloaded or URL is invalid

    Examples
    --------
    >>> # Download at best quality to Downloads folder
    >>> video_path = download_youtube_video("https://www.youtube.com/watch?v=VIDEO_ID")
    
    >>> # Download to specific folder with specific resolution
    >>> video_path = download_youtube_video(
    ...     "https://www.youtube.com/watch?v=VIDEO_ID",
    ...     output_path="/path/to/folder",
    ...     resolution="720"
    ... )
    """
    try:
        # Set default output path to Downloads folder if none provided
        if output_path is None:
            output_path = str(Path.home() / "Downloads")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Configure yt-dlp options
        resolution_format = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst"
        }
        
        if resolution.isdigit():
            format_str = f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best"
        else:
            format_str = resolution_format.get(resolution, resolution_format["best"])
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: print(f'Downloading: {d["_percent_str"]} of {d["_total_bytes_str"]}' if d['status'] == 'downloading' else '')],
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = os.path.join(output_path, ydl.prepare_filename(info))
            print(f"Download complete! Saved to: {video_path}")
            
        return video_path
        
    except Exception as e:
        raise Exception(f"Error downloading video: {str(e)}")

def find_package_location(package_name_or_module: str | types.ModuleType) -> str:
    """
    Find the location of a package, whether it's already imported or not.

    This function determines the installation directory of a Python package by either
    importing it by name or using an already imported module object. It returns the
    parent directory path where the package is installed.

    Parameters
    ----------
    package_name_or_module : Union[str, types.ModuleType]
        Either a string representing the package name or an imported module object.
        For string inputs, the package must be installed and importable.
        For module objects, they must have a valid __file__ attribute.

    Returns
    -------
    str
        The absolute file path to the parent directory containing the package.
        This is typically the directory containing site-packages or similar.

    Raises
    ------
    ValueError
        If the input string is empty or contains only whitespace.
        >>> find_package_location("")
        ValueError: Empty module name
        >>> find_package_location("   ")
        ValueError: Empty module name

    TypeError
        If the input is neither a string nor a module object.
        >>> find_package_location(123)
        TypeError: Argument must be a string (package name) or a module object
        >>> find_package_location(None)
        TypeError: Argument must be a string (package name) or a module object

    ImportError
        If the package cannot be imported (when using string input).
        >>> find_package_location("nonexistent_package")
        ImportError: No module named 'nonexistent_package'

    AttributeError
        If the package location cannot be determined (e.g., built-in modules).
        >>> import sys
        >>> find_package_location(sys)
        AttributeError: Unable to determine the location of 'sys'. It might be a built-in module.

    Examples
    --------
    Using a string package name:
    >>> import os
    >>> path = find_package_location('numpy')
    >>> path
    '/usr/local/lib/python3.8'

    Using an imported module object:
    >>> import pandas as pd
    >>> path = find_package_location(pd)
    >>> path
    '/usr/local/lib/python3.8'

    Using a subpackage:
    >>> path = find_package_location('pandas.core')
    >>> path
    '/usr/local/lib/python3.8'

    Error cases:
    >>> try:
    ...     find_package_location('nonexistent_package')
    ... except ImportError as e:
    ...     print(f"Caught error: {e}")
    Caught error: No module named 'nonexistent_package'

    >>> try:
    ...     find_package_location(123)  # type: ignore
    ... except TypeError as e:
    ...     print(f"Caught error: {e}")
    Caught error: Argument must be a string (package name) or a module object

    Notes
    -----
    - The function returns the parent directory of the package installation,
      not the package directory itself.
    - For standard installations, this is typically the directory containing
      site-packages.
    - The function works with both regular packages and namespace packages.
    - Built-in modules and other modules without a __file__ attribute will
      raise AttributeError.

    See Also
    --------
    importlib.import_module : Used internally to import packages by name
    types.ModuleType : The type of module objects accepted by this function
    pathlib.Path : Used internally for path manipulation
    """
    package: types.ModuleType

    if isinstance(package_name_or_module, str):
        if not package_name_or_module.strip():
            raise ValueError("Empty module name")
        # If it's a string, treat it as a package name and try to import
        package = importlib.import_module(package_name_or_module)
    elif isinstance(package_name_or_module, types.ModuleType):
        # If it's already a module object, use it directly
        package = package_name_or_module
    else:
        raise TypeError("Argument must be a string (package name) or a module object.")
    
    # Get the file path of the package
    if not hasattr(package, '__file__'):
        raise AttributeError(
            f"Unable to determine the location of '{getattr(package, '__name__', 'unknown')}'. "
            "It might be a built-in module."
        )
    
    # Convert to Path object for more reliable path manipulation
    package_path: Path = Path(package.__file__)
    # Get the parent directory that contains all site-packages
    # This is typically two levels up from the module file for regular packages
    site_packages_parent: Path = package_path.parent.parent.parent
    return str(site_packages_parent)

# Common extension sets for different types of files
EXTENSION_SETS = {
    'python': {'.py', '.pyx', '.pyi', '.pyw'},
    'web': {'.html', '.css', '.js', '.jsx', '.ts', '.tsx'},
    'java': {'.java', '.class', '.jar'},
    'c_cpp': {'.c', '.cpp', '.h', '.hpp'},
    'rust': {'.rs', '.rlib'},
    'go': {'.go'},
    'ruby': {'.rb', '.erb'},
    'php': {'.php'},
    'shell': {'.sh', '.bash'},
    'data': {'.json', '.yaml', '.yml', '.xml'},
    'sql': {'.sql'},
    'docs': {'.md', '.rst', '.txt'}
}

# Common extension sets for different types of files
EXTENSION_SETS = {
    'python': {'.py', '.pyx', '.pyi', '.pyw'},
    'web': {'.html', '.css', '.js', '.jsx', '.ts', '.tsx'},
    'java': {'.java', '.class', '.jar'},
    'c_cpp': {'.c', '.cpp', '.h', '.hpp'},
    'rust': {'.rs', '.rlib'},
    'go': {'.go'},
    'ruby': {'.rb', '.erb'},
    'php': {'.php'},
    'shell': {'.sh', '.bash'},
    'data': {'.json', '.yaml', '.yml', '.xml'},
    'sql': {'.sql'},
    'docs': {'.md', '.rst', '.txt'}
}

# Default directories to exclude
DEFAULT_EXCLUDE_DIRS = {
    # Package management
    'node_modules',
    'venv',
    'env',
    '.env',
    'vendor',
    'packages',
    '.npm',
    'bower_components',
    
    # Build outputs
    'build',
    'dist',
    'out',
    'target',
    'output',
    '__pycache__',
    '.next',
    '.nuxt',
    
    # IDE and tools
    '.idea',
    '.vscode',
    '.vs',
    '.eclipse',
    '.settings',
    
    # Other common excludes
    'coverage',
    'logs',
    'temp',
    'tmp',
    'cache',
    '.cache',
    'assets',
    'public/assets',
    'static/assets',
}

# File patterns to exclude
DEFAULT_EXCLUDE_PATTERNS = {
    # Compiled files
    '*.pyc', '*.pyo', '*.pyd',
    '*.so', '*.dll', '*.dylib',
    '*.class', '*.jar',
    '*.min.js', '*.min.css',
    
    # Generated files
    '*.generated.*',
    '*.auto.*',
    '*_generated.*',
    
    # Package files
    'package-lock.json',
    'yarn.lock',
    'Gemfile.lock',
    'poetry.lock',
    
    # Large data files
    '*.csv', '*.sqlite', '*.db',
    '*.pkl', '*.pickle',
    '*.parquet', '*.hdf5',
    
    # Media files
    '*.jpg', '*.jpeg', '*.png', 
    '*.gif', '*.ico', '*.svg',
    '*.mp3', '*.mp4', '*.wav',
    
    # Other
    '*.log', '*.cache',
    '*.bak', '*.swp', '*.swo',
    'thumbs.db', '.DS_Store'
}

def create_code_pdf(directory_path, output_file='code_documentation.pdf', include_extensions=None, 
                   exclude_extensions=None, max_file_size_kb=500, max_total_files=1000):
    """
    Creates a PDF containing all code files from the given directory,
    including the directory structure. Respects .gitignore and applies smart exclusions.
    
    Args:
        directory_path (str): Path to the directory containing code files
        output_file (str): Name of the output PDF file
        include_extensions (set/list/str): Extensions or preset names to include
        exclude_extensions (set/list/str): Extensions to exclude
        max_file_size_kb (int): Maximum size of individual files to include (in KB)
        max_total_files (int): Maximum number of files to include in the PDF
    """
    def load_gitignore(directory):
        """Load and parse .gitignore file if it exists."""
        gitignore_path = os.path.join(directory, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                spec = pathspec.PathSpec.from_lines(
                    pathspec.patterns.GitWildMatchPattern, 
                    f.readlines()
                )
            return spec
        return None

    def resolve_extensions(ext_input):
        """Convert extension input to a set of extensions."""
        if ext_input is None:
            return set()
        
        if isinstance(ext_input, str):
            if ext_input.startswith('.'):
                return {ext_input.lower()}
            return EXTENSION_SETS.get(ext_input.lower(), set())
        
        extensions = set()
        for item in ext_input:
            if item.startswith('.'):
                extensions.add(item.lower())
            elif item.lower() in EXTENSION_SETS:
                extensions.update(EXTENSION_SETS[item.lower()])
        return extensions

    # Resolve includes and excludes
    if include_extensions is None:
        include_exts = set().union(*EXTENSION_SETS.values())
    else:
        include_exts = resolve_extensions(include_extensions)
    
    exclude_exts = resolve_extensions(exclude_extensions)
    CODE_EXTENSIONS = include_exts - exclude_exts
    
    # Load gitignore patterns
    gitignore_spec = load_gitignore(directory_path)
    
    def matches_pattern(path, patterns):
        """Check if path matches any of the glob patterns."""
        from fnmatch import fnmatch
        return any(fnmatch(path, pattern) for pattern in patterns)
    
    def should_include_path(path, is_dir=False):
        """Check if a path should be included based on various criteria."""
        rel_path = os.path.relpath(path, directory_path)
        basename = os.path.basename(path)
        
        # Skip hidden files/directories
        if basename.startswith('.'):
            return False
            
        # Skip excluded directories
        if is_dir and basename in DEFAULT_EXCLUDE_DIRS:
            return False
            
        # Skip files matching exclude patterns
        if not is_dir and matches_pattern(basename, DEFAULT_EXCLUDE_PATTERNS):
            return False
            
        # Check against gitignore patterns
        if gitignore_spec and gitignore_spec.match_file(rel_path):
            return False
            
        # Skip large files
        if not is_dir and os.path.getsize(path) > max_file_size_kb * 1024:
            return False
            
        return True
    
    def is_code_file(filename):
        """Check if a file is a code file based on its extension."""
        return any(filename.lower().endswith(ext) for ext in CODE_EXTENSIONS)
    
    def get_directory_structure(path, indent=''):
        """Returns a formatted string representing the directory structure."""
        structure = []
        try:
            items = sorted(os.listdir(path))
            for item in items:
                item_path = os.path.join(path, item)
                
                if not should_include_path(item_path, os.path.isdir(item_path)):
                    continue
                    
                if os.path.isfile(item_path) and is_code_file(item):
                    structure.append(f"{indent}└── {item}")
                elif os.path.isdir(item_path):
                    structure.append(f"{indent}└── {item}/")
                    structure.extend(get_directory_structure(item_path, indent + "    "))
        except PermissionError:
            structure.append(f"{indent}[Permission Denied]")
        return structure

    def read_file_content(file_path):
        """Reads and returns the content of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    # Initialize PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=8,
        fontName='Courier'
    )
    
    content = []
    
    # Add title and settings info
    content.append(Paragraph("Code Documentation", title_style))
    content.append(Spacer(1, 0.5 * inch))
    
    content.append(Paragraph("Documentation Settings:", heading_style))
    content.append(Spacer(1, 0.2 * inch))
    settings_text = [
        f"• Maximum file size: {max_file_size_kb}KB",
        f"• File types included: {', '.join(sorted(CODE_EXTENSIONS))}",
        "• Excluding common build, dependency, and generated directories",
    ]
    for setting in settings_text:
        content.append(Paragraph(setting, styles['Normal']))
    content.append(Spacer(1, 0.5 * inch))
    
    # Add directory structure
    content.append(Paragraph("Directory Structure:", heading_style))
    content.append(Spacer(1, 0.2 * inch))
    structure = get_directory_structure(directory_path)
    structure_text = '\n'.join(structure)
    content.append(Preformatted(structure_text, code_style))
    content.append(Spacer(1, 0.5 * inch))
    
    # Add file contents
    content.append(Paragraph("File Contents:", heading_style))
    content.append(Spacer(1, 0.2 * inch))
    
    file_count = 0
    for root, dirs, files in os.walk(directory_path, topdown=True):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if should_include_path(os.path.join(root, d), True)]
        
        for file in sorted(files):
            if file_count >= max_total_files:
                content.append(Paragraph(f"Maximum file limit ({max_total_files}) reached.", styles['Normal']))
                break
                
            file_path = os.path.join(root, file)
            
            if not should_include_path(file_path) or not is_code_file(file):
                continue
                
            rel_path = os.path.relpath(file_path, directory_path)
            
            content.append(Paragraph(f"File: {rel_path}", styles['Heading3']))
            content.append(Spacer(1, 0.1 * inch))
            
            file_content = read_file_content(file_path)
            content.append(Preformatted(file_content, code_style))
            content.append(Spacer(1, 0.3 * inch))
            
            file_count += 1
    
    doc.build(content)
    return output_file