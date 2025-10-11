"""
File Classification Module

Categorizes files based on their purpose, type, and relevance to understand
the nature of changes in a PR.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass 
class FileCategory:
    """Represents a file category with its properties."""
    name: str
    patterns: List[str]
    importance: str
    description: str
    icon: str


@dataclass
class ClassifiedFile:
    """Represents a file with its classification."""
    file_path: str
    category: str
    importance: str
    description: str
    icon: str
    matched_pattern: str


class FileClassifier:
    """Classifies files into categories based on patterns and rules."""
    
    def __init__(self, config: Dict = None):
        """Initialize classifier with configuration."""
        if config and 'categories' in config:
            self.categories = self._load_categories_from_config(config['categories'])
        else:
            self.categories = self._get_default_categories()
        
        self.compiled_patterns = self._compile_patterns()
    
    def _get_default_categories(self) -> Dict[str, FileCategory]:
        """Get default file categories if no configuration is provided."""
        categories_config = {
            'CORE_BUSINESS_LOGIC': {
                'patterns': ['*.py', '*.js', '*.ts', '*.java', '*.cs', '*.php', '*.rb', 'src/**', 'lib/**'],
                'importance': 'HIGH',
                'description': 'Core business logic and application code',
                'icon': '🏛️'
            },
            'USER_INTERFACE': {
                'patterns': ['*.html', '*.css', '*.scss', '*.less', '*.jsx', '*.tsx', '*.vue', 'components/**', 'views/**', 'templates/**'],
                'importance': 'HIGH',
                'description': 'User interface components and styling',
                'icon': '🎨'
            },
            'API_INTEGRATION': {
                'patterns': ['api/**', 'endpoints/**', 'routes/**', '*api*', 'controllers/**'],
                'importance': 'HIGH',
                'description': 'API endpoints and integrations',
                'icon': '🔗'
            },
            'DATABASE': {
                'patterns': ['*.sql', 'migrations/**', 'schema/**', 'models/**', '*.db', 'database/**'],
                'importance': 'HIGH',
                'description': 'Database schemas and migrations',
                'icon': '🗄️'
            },
            'CONFIGURATION': {
                'patterns': ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.env*', 'config/**', '.env*', 'docker*', 'Dockerfile*'],
                'importance': 'MEDIUM',
                'description': 'Configuration files and settings',
                'icon': '⚙️'
            },
            'TESTING': {
                'patterns': ['test/**', 'tests/**', '*test*', '*spec*', '*.test.*', '*.spec.*', '__tests__/**'],
                'importance': 'MEDIUM',
                'description': 'Test files and testing utilities',
                'icon': '🧪'
            },
            'DOCUMENTATION': {
                'patterns': ['*.md', '*.rst', '*.txt', 'docs/**', 'doc/**', 'README*', 'CHANGELOG*'],
                'importance': 'LOW',
                'description': 'Documentation and readme files',
                'icon': '📚'
            },
            'BLOG_CONTENT': {
                'patterns': ['blog/**', 'content/**', 'posts/**', '*.md'],
                'importance': 'MEDIUM',
                'description': 'Blog posts and content',
                'icon': '📝'
            },
            'ASSETS_MEDIA': {
                'patterns': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.ico', '*.mp4', '*.mp3', 'assets/**', 'images/**', 'media/**'],
                'importance': 'LOW',
                'description': 'Images, videos and static assets',
                'icon': '🖼️'
            },
            'BUILD_DEPLOY': {
                'patterns': ['*.sh', '*.bat', 'scripts/**', 'deploy/**', 'build/**', 'Makefile', '*.yml', '.github/**'],
                'importance': 'MEDIUM',
                'description': 'Build and deployment scripts',
                'icon': '🚀'
            }
        }
        
        categories = {}
        for name, details in categories_config.items():
            categories[name] = FileCategory(
                name=name,
                patterns=details['patterns'],
                importance=details['importance'],
                description=details['description'],
                icon=details['icon']
            )
        return categories
    
    def _load_categories_from_config(self, categories_config: Dict) -> Dict[str, FileCategory]:
        """Load file categories from configuration dictionary."""
        categories = {}
        for name, details in categories_config.items():
            categories[name] = FileCategory(
                name=name,
                patterns=details['patterns'],
                importance=details['importance'],
                description=details['description'],
                icon=details['icon']
            )
        return categories
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient matching."""
        compiled = {}
        for category_name, category in self.categories.items():
            compiled[category_name] = []
            for pattern in category.patterns:
                # Convert glob-like patterns to regex
                regex_pattern = self._glob_to_regex(pattern)
                compiled[category_name].append(re.compile(regex_pattern, re.IGNORECASE))
        return compiled
    
    def _glob_to_regex(self, pattern: str) -> str:
        """Convert glob-like pattern to regex."""
        # Escape special regex characters except * and ?
        pattern = re.escape(pattern)
        # Convert glob wildcards to regex
        pattern = pattern.replace(r'\*\*', '.*')  # ** matches any path
        pattern = pattern.replace(r'\*', '[^/]*')  # * matches any filename chars
        pattern = pattern.replace(r'\?', '.')
        
        # Handle path separators
        pattern = pattern.replace('/', r'[/\\]')
        
        # Anchor pattern appropriately
        if pattern.startswith('.*'):
            # Already starts with .*, leave as is
            pass
        elif '/' in pattern or '\\' in pattern:
            # Contains path separator, match anywhere in path
            pattern = '.*' + pattern
        else:
            # Simple filename pattern, match at end of path
            pattern = '.*[/\\\\]' + pattern + '$'
        
        return pattern
    
    def classify_file(self, file_path: str) -> ClassifiedFile:
        """
        Classify a single file into a category.
        
        Args:
            file_path: Path to the file (relative or absolute)
            
        Returns:
            ClassifiedFile object with classification details
        """
        # Normalize path for consistent matching
        normalized_path = str(Path(file_path)).replace('\\', '/')
        
        # Try to match against each category in order of importance
        category_order = ['CORE_BUSINESS_LOGIC', 'DATABASE', 'API_INTEGRATION', 'USER_INTERFACE', 
                         'BLOG_CONTENT', 'CONFIGURATION', 'TESTING', 'BUILD_DEPLOY', 
                         'DOCUMENTATION', 'ASSETS_MEDIA']
        
        # First try ordered categories
        for category_name in category_order:
            if category_name in self.compiled_patterns:
                patterns = self.compiled_patterns[category_name]
                for i, pattern in enumerate(patterns):
                    if pattern.search(normalized_path):
                        category = self.categories[category_name]
                        return ClassifiedFile(
                            file_path=file_path,
                            category=category_name,
                            importance=category.importance,
                            description=category.description,
                            icon=category.icon,
                            matched_pattern=category.patterns[i]
                        )
        
        # Then try remaining categories
        for category_name, patterns in self.compiled_patterns.items():
            if category_name not in category_order:
                for i, pattern in enumerate(patterns):
                    if pattern.search(normalized_path):
                        category = self.categories[category_name]
                        return ClassifiedFile(
                            file_path=file_path,
                            category=category_name,
                            importance=category.importance,
                            description=category.description,
                            icon=category.icon,
                            matched_pattern=category.patterns[i]
                        )
        
        # Default category for unmatched files
        return ClassifiedFile(
            file_path=file_path,
            category='UNCATEGORIZED',
            importance='MEDIUM',
            description='Uncategorized file',
            icon='❓',
            matched_pattern='default'
        )
    
    def generate_category_summary(self, classified_files: List[ClassifiedFile]) -> Dict[str, Dict]:
        """
        Generate summary statistics by category.
        
        Returns:
            Dictionary with category names as keys and summary info as values
        """
        summary = {}
        
        for classified_file in classified_files:
            category = classified_file.category
            if category not in summary:
                summary[category] = {
                    'count': 0,
                    'files': [],
                    'importance': classified_file.importance,
                    'description': classified_file.description,
                    'icon': classified_file.icon
                }
            
            summary[category]['count'] += 1
            summary[category]['files'].append(classified_file.file_path)
        
        return summary
    
    def filter_by_importance(self, classified_files: List[ClassifiedFile], 
                           importance_levels: Set[str]) -> List[ClassifiedFile]:
        """Filter files by importance level."""
        return [f for f in classified_files if f.importance in importance_levels]
    
    def filter_by_category(self, classified_files: List[ClassifiedFile],
                          categories: Set[str]) -> List[ClassifiedFile]:
        """Filter files by category."""
        return [f for f in classified_files if f.category in categories]
    
    def get_high_impact_files(self, classified_files: List[ClassifiedFile]) -> List[ClassifiedFile]:
        """Get files that are likely to have high business impact."""
        high_impact_categories = {
            'CORE_BUSINESS_LOGIC', 'USER_INTERFACE', 'API_INTEGRATION', 'DATABASE'
        }
        return [f for f in classified_files if f.category in high_impact_categories]