#!/usr/bin/env python3
"""
Church Service Playlist Analyzer with Interactive Report

This script analyzes all videos in the Calvary Spokane Revelation playlist,
using the church service analyzer to classify segments and generate an
interactive HTML report with visualizations.
"""

import os
import json
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib
import re
from dataclasses import dataclass, asdict

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from asabaal_utils.video_processing.church_service_analyzer import (
    ChurchServiceAnalyzer, ServiceAnalysisResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PlaylistAnalysisResult:
    """Complete analysis result for the playlist."""
    playlist_path: str
    videos_analyzed: int
    total_duration: float
    analysis_results: List[ServiceAnalysisResult]
    summary_stats: Dict[str, Any]
    analysis_timestamp: str


class RevelationPlaylistAnalyzer:
    """Analyzes the Calvary Spokane Revelation series videos."""
    
    def __init__(self, 
                 playlist_path: str,
                 cache_dir: Optional[str] = None,
                 youtube_url: Optional[str] = None):
        """
        Initialize the playlist analyzer.
        
        Args:
            playlist_path: Path to directory containing videos
            cache_dir: Directory to store analysis cache files
            youtube_url: YouTube playlist URL for updates
        """
        self.playlist_path = Path(playlist_path)
        self.cache_dir = Path(cache_dir or self.playlist_path / '.analysis_cache')
        self.youtube_url = youtube_url
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize church service analyzer
        self.analyzer = ChurchServiceAnalyzer(
            use_chunked_processing=True,
            chunk_duration=60.0
        )
        
        logger.info(f"Initialized analyzer for playlist: {self.playlist_path}")
        logger.info(f"Cache directory: {self.cache_dir}")
    
    def update_playlist(self) -> bool:
        """Update playlist from YouTube if URL is provided."""
        if not self.youtube_url:
            logger.info("No YouTube URL provided, skipping playlist update")
            return True
        
        logger.info(f"Updating playlist from: {self.youtube_url}")
        
        # Use the youtube-downloader tool to update playlist
        cmd = [
            sys.executable,
            'tools/youtube-downloader',
            '--playlist',
            '--update',
            '-o', str(self.playlist_path),
            self.youtube_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Playlist updated successfully")
                return True
            else:
                logger.error(f"Failed to update playlist: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error updating playlist: {e}")
            return False
    
    def get_video_hash(self, video_path: Path) -> str:
        """Generate a hash for video file to detect changes."""
        # Use file size and modification time for quick hash
        stat = video_path.stat()
        hash_string = f"{video_path.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def get_cache_path(self, video_path: Path) -> Path:
        """Get cache file path for a video."""
        video_hash = self.get_video_hash(video_path)
        cache_name = f"{video_path.stem}_{video_hash}.json"
        return self.cache_dir / cache_name
    
    def load_cached_analysis(self, video_path: Path) -> Optional[ServiceAnalysisResult]:
        """Load cached analysis for a video if available."""
        cache_path = self.get_cache_path(video_path)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct ServiceAnalysisResult from JSON
                from asabaal_utils.video_processing.church_service_analyzer import ServiceSegment
                
                # Reconstruct segments
                segments = []
                for seg_data in data['segments']:
                    segment = ServiceSegment(
                        start_time=seg_data['start_time'],
                        end_time=seg_data['end_time'],
                        segment_type=seg_data['segment_type'],
                        confidence=seg_data['confidence'],
                        features=seg_data['features'],
                        transcript_segments=None  # Skip transcript for now
                    )
                    segments.append(segment)
                
                result = ServiceAnalysisResult(
                    video_path=data['video_path'],
                    total_duration=data['total_duration'],
                    segments=segments,
                    metadata=data['metadata'],
                    analysis_timestamp=data['analysis_timestamp']
                )
                
                logger.info(f"Loaded cached analysis for: {video_path.name}")
                return result
                
            except Exception as e:
                logger.warning(f"Failed to load cache for {video_path.name}: {e}")
                return None
        
        return None
    
    def save_analysis_cache(self, video_path: Path, result: ServiceAnalysisResult):
        """Save analysis result to cache."""
        cache_path = self.get_cache_path(video_path)
        
        try:
            result.save_to_json(cache_path)
            logger.info(f"Saved analysis cache for: {video_path.name}")
        except Exception as e:
            logger.error(f"Failed to save cache for {video_path.name}: {e}")
    
    def extract_episode_info(self, filename: str) -> Dict[str, Any]:
        """Extract episode information from filename."""
        # Pattern: MM.DD.YY | Day TIME | Title | Part N
        pattern = r'(\d{2}\.\d{2}\.\d{2})\s*\|\s*(\w+)\s+(\d+[AP]M)\s*\|\s*([^|]+)(?:\s*\|\s*(.+))?'
        match = re.match(pattern, filename)
        
        if match:
            date_str, day, time, title, part = match.groups()
            
            # Parse date
            month, day_num, year = date_str.split('.')
            date = f"20{year}-{month}-{day_num}"
            
            return {
                'date': date,
                'day_of_week': day,
                'service_time': time,
                'title': title.strip(),
                'part': part.strip() if part else None,
                'episode_number': None  # Will be determined by date order
            }
        
        return {
            'date': None,
            'day_of_week': None,
            'service_time': None,
            'title': filename,
            'part': None,
            'episode_number': None
        }
    
    def analyze_all_videos(self) -> PlaylistAnalysisResult:
        """Analyze all videos in the playlist."""
        # Update playlist first
        if self.youtube_url:
            self.update_playlist()
        
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(self.playlist_path.glob(f'*{ext}'))
        
        video_files.sort()  # Sort by filename (which includes date)
        
        logger.info(f"Found {len(video_files)} videos to analyze")
        
        # Analyze each video
        analysis_results = []
        total_duration = 0.0
        
        for i, video_path in enumerate(video_files):
            logger.info(f"\nProcessing video {i+1}/{len(video_files)}: {video_path.name}")
            
            # Check cache first
            cached_result = self.load_cached_analysis(video_path)
            
            if cached_result:
                result = cached_result
            else:
                # Analyze video
                try:
                    result = self.analyzer.analyze_service(video_path)
                    # Save to cache
                    self.save_analysis_cache(video_path, result)
                except Exception as e:
                    logger.error(f"Failed to analyze {video_path.name}: {e}")
                    continue
            
            # Extract episode info
            episode_info = self.extract_episode_info(video_path.stem)
            episode_info['episode_number'] = i + 1
            
            # Add episode info to metadata
            result.metadata.update(episode_info)
            
            analysis_results.append(result)
            total_duration += result.total_duration
        
        # Calculate summary statistics
        summary_stats = self.calculate_summary_stats(analysis_results)
        
        # Create playlist analysis result
        playlist_result = PlaylistAnalysisResult(
            playlist_path=str(self.playlist_path),
            videos_analyzed=len(analysis_results),
            total_duration=total_duration,
            analysis_results=analysis_results,
            summary_stats=summary_stats,
            analysis_timestamp=datetime.now().isoformat()
        )
        
        return playlist_result
    
    def calculate_summary_stats(self, results: List[ServiceAnalysisResult]) -> Dict[str, Any]:
        """Calculate summary statistics across all videos."""
        stats = {
            'total_videos': len(results),
            'total_duration_hours': sum(r.total_duration for r in results) / 3600,
            'segment_type_totals': {},
            'segment_type_durations': {},
            'average_segment_durations': {},
            'videos_by_day': {},
            'videos_by_time': {},
            'progression_over_time': []
        }
        
        # Aggregate segment data
        segment_counts = {}
        segment_durations = {}
        
        for result in results:
            # Count by day and time
            metadata = result.metadata
            if metadata.get('day_of_week'):
                day = metadata['day_of_week']
                stats['videos_by_day'][day] = stats['videos_by_day'].get(day, 0) + 1
            
            if metadata.get('service_time'):
                time = metadata['service_time']
                stats['videos_by_time'][time] = stats['videos_by_time'].get(time, 0) + 1
            
            # Aggregate segments
            for segment in result.segments:
                seg_type = segment.segment_type
                
                # Count
                segment_counts[seg_type] = segment_counts.get(seg_type, 0) + 1
                
                # Duration
                segment_durations[seg_type] = segment_durations.get(seg_type, 0) + segment.duration
            
            # Track progression
            stats['progression_over_time'].append({
                'episode': metadata.get('episode_number', 0),
                'date': metadata.get('date'),
                'title': metadata.get('title'),
                'duration': result.total_duration / 60,  # in minutes
                'segment_counts': {
                    seg_type: sum(1 for s in result.segments if s.segment_type == seg_type)
                    for seg_type in set(s.segment_type for s in result.segments)
                }
            })
        
        # Calculate totals and averages
        stats['segment_type_totals'] = segment_counts
        stats['segment_type_durations'] = {
            k: v / 3600 for k, v in segment_durations.items()  # Convert to hours
        }
        stats['average_segment_durations'] = {
            k: (segment_durations[k] / segment_counts[k]) / 60  # in minutes
            for k in segment_counts if segment_counts[k] > 0
        }
        
        return stats
    
    def generate_html_report(self, playlist_result: PlaylistAnalysisResult, output_path: str):
        """Generate interactive HTML report."""
        logger.info(f"Generating HTML report to: {output_path}")
        
        # Prepare data for JavaScript
        videos_data = []
        for result in playlist_result.analysis_results:
            video_data = {
                'title': result.metadata.get('title', 'Unknown'),
                'date': result.metadata.get('date'),
                'episode': result.metadata.get('episode_number'),
                'duration': result.total_duration / 60,  # minutes
                'segments': [
                    {
                        'type': seg.segment_type,
                        'start': seg.start_time / 60,  # minutes
                        'end': seg.end_time / 60,
                        'duration': seg.duration / 60,
                        'confidence': seg.confidence
                    }
                    for seg in result.segments
                ]
            }
            videos_data.append(video_data)
        
        # Generate HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calvary Spokane Revelation Series Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --text-primary: #eee;
            --text-secondary: #aaa;
            --accent-music: #e74c3c;
            --accent-sermon: #3498db;
            --accent-announcement: #2ecc71;
            --accent-slideshow: #f39c12;
            --accent-prayer: #9b59b6;
            --accent-transition: #95a5a6;
            --border-color: #2c3e50;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 40px 0;
            background: var(--bg-secondary);
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #3498db, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: var(--bg-secondary);
            padding: 25px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(45deg, #3498db, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            margin-top: 5px;
        }}
        
        .chart-container {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }}
        
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        canvas {{
            max-height: 400px;
        }}
        
        .timeline-container {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
            overflow-x: auto;
        }}
        
        .video-timeline {{
            margin-bottom: 20px;
            padding: 15px;
            background: var(--bg-tertiary);
            border-radius: 8px;
        }}
        
        .video-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #3498db;
        }}
        
        .segment-bar {{
            display: flex;
            height: 40px;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        
        .segment {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.85em;
            transition: opacity 0.3s ease;
            cursor: pointer;
            position: relative;
        }}
        
        .segment:hover {{
            opacity: 0.8;
        }}
        
        .segment-tooltip {{
            position: absolute;
            bottom: 45px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 0.85em;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 1000;
        }}
        
        .segment:hover .segment-tooltip {{
            opacity: 1;
        }}
        
        .segment-music {{ background-color: var(--accent-music); }}
        .segment-sermon {{ background-color: var(--accent-sermon); }}
        .segment-announcement {{ background-color: var(--accent-announcement); }}
        .segment-slideshow {{ background-color: var(--accent-slideshow); }}
        .segment-prayer {{ background-color: var(--accent-prayer); }}
        .segment-transition {{ background-color: var(--accent-transition); }}
        
        .legend {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 30px;
            padding: 20px;
            background: var(--bg-tertiary);
            border-radius: 8px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        
        .filters {{
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .filter-label {{
            font-size: 0.9em;
            color: var(--text-secondary);
        }}
        
        select, input {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 1em;
        }}
        
        select:focus, input:focus {{
            outline: none;
            border-color: #3498db;
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2em; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .segment {{ font-size: 0.7em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Calvary Spokane Revelation Series Analysis</h1>
            <p class="subtitle">Comprehensive analysis of {playlist_result.videos_analyzed} sermons</p>
            <p class="subtitle" style="font-size: 0.9em; margin-top: 10px;">
                Analysis completed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{playlist_result.videos_analyzed}</div>
                <div class="stat-label">Total Videos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{playlist_result.total_duration / 3600:.1f}h</div>
                <div class="stat-label">Total Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(playlist_result.summary_stats['segment_type_totals'].values())}</div>
                <div class="stat-label">Total Segments</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{playlist_result.summary_stats['segment_type_durations'].get('sermon', 0):.1f}h</div>
                <div class="stat-label">Sermon Time</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label class="filter-label">Filter by Segment Type</label>
                <select id="segmentFilter" onchange="filterTimelines()">
                    <option value="all">All Segments</option>
                    <option value="music">Music Only</option>
                    <option value="sermon">Sermon Only</option>
                    <option value="announcement">Announcements Only</option>
                    <option value="slideshow">Slideshows Only</option>
                    <option value="prayer">Prayer Only</option>
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label">Sort By</label>
                <select id="sortBy" onchange="sortTimelines()">
                    <option value="date">Date</option>
                    <option value="duration">Duration</option>
                    <option value="sermon-length">Sermon Length</option>
                </select>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">Segment Distribution by Type</h2>
            <canvas id="segmentChart"></canvas>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">Service Duration Over Time</h2>
            <canvas id="durationChart"></canvas>
        </div>
        
        <div class="timeline-container">
            <h2 class="chart-title">Video Timelines</h2>
            <div id="timelines"></div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color segment-music"></div>
                <span>Music</span>
            </div>
            <div class="legend-item">
                <div class="legend-color segment-sermon"></div>
                <span>Sermon</span>
            </div>
            <div class="legend-item">
                <div class="legend-color segment-announcement"></div>
                <span>Announcement</span>
            </div>
            <div class="legend-item">
                <div class="legend-color segment-slideshow"></div>
                <span>Slideshow</span>
            </div>
            <div class="legend-item">
                <div class="legend-color segment-prayer"></div>
                <span>Prayer</span>
            </div>
            <div class="legend-item">
                <div class="legend-color segment-transition"></div>
                <span>Transition</span>
            </div>
        </div>
    </div>
    
    <script>
        // Data from Python
        const videosData = {json.dumps(videos_data, indent=2)};
        const summaryStats = {json.dumps(playlist_result.summary_stats, indent=2)};
        
        // Chart configuration
        Chart.defaults.color = '#aaa';
        Chart.defaults.borderColor = '#2c3e50';
        
        // Segment Distribution Chart
        const segmentCtx = document.getElementById('segmentChart').getContext('2d');
        const segmentChart = new Chart(segmentCtx, {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(summaryStats.segment_type_durations),
                datasets: [{{
                    data: Object.values(summaryStats.segment_type_durations),
                    backgroundColor: [
                        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#95a5a6'
                    ],
                    borderWidth: 2,
                    borderColor: '#1a1a2e'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': ' + context.parsed.toFixed(1) + ' hours';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Duration Over Time Chart
        const durationCtx = document.getElementById('durationChart').getContext('2d');
        const durationChart = new Chart(durationCtx, {{
            type: 'line',
            data: {{
                labels: summaryStats.progression_over_time.map(v => v.date || 'Episode ' + v.episode),
                datasets: [{{
                    label: 'Total Duration (minutes)',
                    data: summaryStats.progression_over_time.map(v => v.duration),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4
                }}, {{
                    label: 'Sermon Duration (minutes)',
                    data: videosData.map(v => {{
                        const sermonTime = v.segments
                            .filter(s => s.type === 'sermon')
                            .reduce((sum, s) => sum + s.duration, 0);
                        return sermonTime;
                    }}),
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }}
                    }},
                    x: {{
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }}
                    }}
                }}
            }}
        }});
        
        // Render timelines
        function renderTimelines() {{
            const container = document.getElementById('timelines');
            container.innerHTML = '';
            
            videosData.forEach((video, index) => {{
                const timeline = document.createElement('div');
                timeline.className = 'video-timeline';
                timeline.dataset.index = index;
                
                const title = document.createElement('div');
                title.className = 'video-title';
                title.textContent = `Episode ${{video.episode}}: ${{video.title}} (${{video.date || 'No date'}})`;
                timeline.appendChild(title);
                
                const segmentBar = document.createElement('div');
                segmentBar.className = 'segment-bar';
                
                video.segments.forEach(segment => {{
                    const segDiv = document.createElement('div');
                    segDiv.className = `segment segment-${{segment.type}}`;
                    segDiv.style.width = `${{(segment.duration / video.duration) * 100}}%`;
                    
                    // Add tooltip
                    const tooltip = document.createElement('div');
                    tooltip.className = 'segment-tooltip';
                    tooltip.textContent = `${{segment.type}} (${{segment.duration.toFixed(1)}} min)`;
                    segDiv.appendChild(tooltip);
                    
                    // Only show text if segment is wide enough
                    if (segment.duration > video.duration * 0.1) {{
                        segDiv.textContent = segment.type;
                    }}
                    
                    segmentBar.appendChild(segDiv);
                }});
                
                timeline.appendChild(segmentBar);
                container.appendChild(timeline);
            }});
        }}
        
        function filterTimelines() {{
            const filter = document.getElementById('segmentFilter').value;
            const timelines = document.querySelectorAll('.video-timeline');
            
            timelines.forEach(timeline => {{
                const index = parseInt(timeline.dataset.index);
                const video = videosData[index];
                
                if (filter === 'all') {{
                    timeline.style.display = 'block';
                }} else {{
                    const hasSegment = video.segments.some(s => s.type === filter);
                    timeline.style.display = hasSegment ? 'block' : 'none';
                }}
            }});
        }}
        
        function sortTimelines() {{
            const sortBy = document.getElementById('sortBy').value;
            const container = document.getElementById('timelines');
            const timelines = Array.from(container.children);
            
            timelines.sort((a, b) => {{
                const indexA = parseInt(a.dataset.index);
                const indexB = parseInt(b.dataset.index);
                const videoA = videosData[indexA];
                const videoB = videosData[indexB];
                
                switch(sortBy) {{
                    case 'date':
                        return (videoA.date || '').localeCompare(videoB.date || '');
                    case 'duration':
                        return videoB.duration - videoA.duration;
                    case 'sermon-length':
                        const sermonA = videoA.segments.filter(s => s.type === 'sermon').reduce((sum, s) => sum + s.duration, 0);
                        const sermonB = videoB.segments.filter(s => s.type === 'sermon').reduce((sum, s) => sum + s.duration, 0);
                        return sermonB - sermonA;
                    default:
                        return 0;
                }}
            }});
            
            timelines.forEach(timeline => container.appendChild(timeline));
        }}
        
        // Initialize
        renderTimelines();
    </script>
</body>
</html>"""
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated successfully: {output_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Calvary Spokane Revelation playlist"
    )
    parser.add_argument(
        '--playlist-path',
        default='/mnt/d/Work/Asabaal Ventures/Asabaal\'s Academic Adventures/Data Science of Religious Texts/calvary_spokane_revelation',
        help='Path to video playlist directory'
    )
    parser.add_argument(
        '--youtube-url',
        help='YouTube playlist URL for updates'
    )
    parser.add_argument(
        '--output',
        default='revelation_analysis_report.html',
        help='Output HTML report path'
    )
    parser.add_argument(
        '--cache-dir',
        help='Cache directory for analysis results'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = RevelationPlaylistAnalyzer(
        playlist_path=args.playlist_path,
        cache_dir=args.cache_dir,
        youtube_url=args.youtube_url
    )
    
    # Analyze all videos
    logger.info("Starting playlist analysis...")
    playlist_result = analyzer.analyze_all_videos()
    
    # Generate report
    analyzer.generate_html_report(playlist_result, args.output)
    
    logger.info(f"\nAnalysis complete!")
    logger.info(f"Videos analyzed: {playlist_result.videos_analyzed}")
    logger.info(f"Total duration: {playlist_result.total_duration / 3600:.1f} hours")
    logger.info(f"Report saved to: {args.output}")


if __name__ == '__main__':
    main()