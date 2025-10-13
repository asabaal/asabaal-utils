#!/usr/bin/env python3
"""
Great Reconciliation CapCut Project Analyzer

Analyzes CapCut projects from The Great Reconciliation series to extract:
- Project settings and configurations
- Media assets used (videos, images, audio)
- Effects and transitions applied
- Text elements and styling
- Timeline structure
- Asset reuse recommendations for future weeks
"""

import os
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import re
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MediaAsset:
    """Represents a media asset used in CapCut projects."""
    file_path: str
    asset_type: str  # 'video', 'image', 'audio', 'text'
    file_name: str
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    usage_count: int = 0
    projects_used_in: List[str] = None
    
    def __post_init__(self):
        if self.projects_used_in is None:
            self.projects_used_in = []


@dataclass
class EffectInfo:
    """Information about effects applied in projects."""
    effect_name: str
    effect_type: str  # 'video', 'audio', 'text', 'transition'
    parameters: Dict[str, Any]
    usage_count: int = 0
    projects_used_in: List[str] = None
    
    def __post_init__(self):
        if self.projects_used_in is None:
            self.projects_used_in = []


@dataclass
class ProjectAnalysis:
    """Complete analysis of a single CapCut project."""
    project_name: str
    project_path: str
    creation_date: Optional[str]
    total_duration: Optional[float]
    video_tracks: int
    audio_tracks: int
    media_assets: List[MediaAsset]
    effects_used: List[EffectInfo]
    text_elements: List[Dict[str, Any]]
    project_settings: Dict[str, Any]
    timeline_structure: Dict[str, Any]


class GreatReconciliationAnalyzer:
    """Analyzer for Great Reconciliation CapCut projects."""
    
    def __init__(self, capcut_drafts_path: str, output_videos_path: str):
        """
        Initialize the analyzer.
        
        Args:
            capcut_drafts_path: Path to CapCut Drafts directory
            output_videos_path: Path to final video outputs directory
        """
        self.capcut_drafts_path = Path(capcut_drafts_path)
        self.output_videos_path = Path(output_videos_path)
        
        # Videos we're looking for
        self.target_videos = [
            "Vision - Episode 1 - Lyric Video",
            "VISION - Week 2 Lyric Video", 
            "Sacred Listening Space Short",
            "TGR Week 2",
            "WEEK 2 SHORT 2",
            "Sacred Space Short 2"
        ]
        
        # Asset tracking
        self.media_assets = {}
        self.effects_catalog = {}
        self.project_analyses = []
        
        logger.info(f"Initialized analyzer for: {self.capcut_drafts_path}")
        logger.info(f"Output videos path: {self.output_videos_path}")
    
    def find_matching_projects(self) -> List[Path]:
        """Find CapCut projects that match our target videos."""
        matching_projects = []
        
        logger.info("Scanning CapCut projects for matches...")
        
        # Get all project directories
        project_dirs = [d for d in self.capcut_drafts_path.iterdir() if d.is_dir()]
        
        for project_dir in project_dirs:
            meta_info_path = project_dir / "draft_meta_info.json"
            
            if meta_info_path.exists():
                try:
                    with open(meta_info_path, 'r', encoding='utf-8') as f:
                        meta_info = json.load(f)
                    
                    # Check project name
                    project_name = meta_info.get('draft_name', '')
                    
                    # Look for matches with our target videos
                    for target in self.target_videos:
                        if self._is_project_match(project_name, target):
                            matching_projects.append(project_dir)
                            logger.info(f"Found match: {project_name} -> {target}")
                            break
                    
                except Exception as e:
                    logger.warning(f"Could not read meta info for {project_dir.name}: {e}")
        
        logger.info(f"Found {len(matching_projects)} matching projects")
        return matching_projects
    
    def _is_project_match(self, project_name: str, target_name: str) -> bool:
        """Check if a project name matches a target video name."""
        # Normalize names for comparison
        project_norm = re.sub(r'[^a-zA-Z0-9]', '', project_name.lower())
        target_norm = re.sub(r'[^a-zA-Z0-9]', '', target_name.lower())
        
        # Check for direct matches or partial matches
        return (target_norm in project_norm or 
                project_norm in target_norm or
                self._fuzzy_match(project_norm, target_norm))
    
    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Simple fuzzy matching for project names."""
        # Check for key terms
        key_terms = ['vision', 'tgr', 'sacred', 'listening', 'space', 'short', 'week', 'lyric']
        
        str1_terms = set([term for term in key_terms if term in str1])
        str2_terms = set([term for term in key_terms if term in str2])
        
        # If they share 2+ key terms, consider it a match
        return len(str1_terms.intersection(str2_terms)) >= 2
    
    def analyze_project(self, project_path: Path) -> ProjectAnalysis:
        """Analyze a single CapCut project."""
        logger.info(f"Analyzing project: {project_path.name}")
        
        # Read project files
        meta_info = self._read_meta_info(project_path)
        content_data = self._read_content_data(project_path)
        
        # Extract information
        project_name = meta_info.get('draft_name', project_path.name)
        creation_date = meta_info.get('create_time')
        
        # Analyze content
        media_assets = self._extract_media_assets(content_data, project_name)
        effects_used = self._extract_effects(content_data, project_name)
        text_elements = self._extract_text_elements(content_data)
        project_settings = self._extract_project_settings(content_data)
        timeline_structure = self._extract_timeline_structure(content_data)
        
        # Calculate stats
        total_duration = self._calculate_total_duration(content_data)
        tracks = content_data.get('tracks', [])
        video_tracks = len([track for track in tracks if track.get('type') == 'video'])
        audio_tracks = len([track for track in tracks if track.get('type') == 'audio'])
        
        analysis = ProjectAnalysis(
            project_name=project_name,
            project_path=str(project_path),
            creation_date=creation_date,
            total_duration=total_duration,
            video_tracks=video_tracks,
            audio_tracks=audio_tracks,
            media_assets=media_assets,
            effects_used=effects_used,
            text_elements=text_elements,
            project_settings=project_settings,
            timeline_structure=timeline_structure
        )
        
        return analysis
    
    def _read_meta_info(self, project_path: Path) -> Dict[str, Any]:
        """Read draft_meta_info.json."""
        meta_path = project_path / "draft_meta_info.json"
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read meta info: {e}")
            return {}
    
    def _read_content_data(self, project_path: Path) -> Dict[str, Any]:
        """Read draft_content.json."""
        content_path = project_path / "draft_content.json"
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read content data: {e}")
            return {}
    
    def _extract_media_assets(self, content_data: Dict[str, Any], project_name: str) -> List[MediaAsset]:
        """Extract media assets from project content."""
        assets = []
        
        # Look for materials in the content
        materials = content_data.get('materials', {})
        
        # Videos
        for video_info in materials.get('videos', []):
            if 'path' in video_info:
                asset = MediaAsset(
                    file_path=video_info['path'],
                    asset_type='video',
                    file_name=Path(video_info['path']).name,
                    duration=video_info.get('duration'),
                    resolution=(video_info.get('width'), video_info.get('height')),
                    usage_count=1,
                    projects_used_in=[project_name]
                )
                assets.append(asset)
        
        # Images
        for image_info in materials.get('images', []):
            if 'path' in image_info:
                asset = MediaAsset(
                    file_path=image_info['path'],
                    asset_type='image',
                    file_name=Path(image_info['path']).name,
                    resolution=(image_info.get('width'), image_info.get('height')),
                    usage_count=1,
                    projects_used_in=[project_name]
                )
                assets.append(asset)
        
        # Audio
        for audio_info in materials.get('audios', []):
            if 'path' in audio_info:
                asset = MediaAsset(
                    file_path=audio_info['path'],
                    asset_type='audio',
                    file_name=Path(audio_info['path']).name,
                    duration=audio_info.get('duration'),
                    usage_count=1,
                    projects_used_in=[project_name]
                )
                assets.append(asset)
        
        return assets
    
    def _extract_effects(self, content_data: Dict[str, Any], project_name: str) -> List[EffectInfo]:
        """Extract effects used in the project."""
        effects = []
        
        # Look through tracks for effects
        tracks = content_data.get('tracks', [])
        
        for track in tracks:
            # Video track effects
            if track.get('type') == 'video':
                for segment in track.get('segments', []):
                    # Video effects
                    for effect in segment.get('video_effects', []):
                        effect_info = EffectInfo(
                            effect_name=effect.get('name', 'Unknown'),
                            effect_type='video',
                            parameters=effect.get('params', {}),
                            usage_count=1,
                            projects_used_in=[project_name]
                        )
                        effects.append(effect_info)
                    
                    # Transitions
                    if 'transition' in segment:
                        transition = segment['transition']
                        effect_info = EffectInfo(
                            effect_name=transition.get('name', 'Unknown Transition'),
                            effect_type='transition',
                            parameters=transition.get('params', {}),
                            usage_count=1,
                            projects_used_in=[project_name]
                        )
                        effects.append(effect_info)
            
            # Audio track effects
            elif track.get('type') == 'audio':
                for segment in track.get('segments', []):
                    for effect in segment.get('audio_effects', []):
                        effect_info = EffectInfo(
                            effect_name=effect.get('name', 'Unknown'),
                            effect_type='audio',
                            parameters=effect.get('params', {}),
                            usage_count=1,
                            projects_used_in=[project_name]
                        )
                        effects.append(effect_info)
        
        return effects
    
    def _extract_text_elements(self, content_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text elements and their styling."""
        text_elements = []
        
        # Look for text in materials and tracks
        materials = content_data.get('materials', {})
        
        # Text materials
        for text_info in materials.get('texts', []):
            text_element = {
                'content': text_info.get('content', ''),
                'font_family': text_info.get('font_family'),
                'font_size': text_info.get('font_size'),
                'color': text_info.get('color'),
                'alignment': text_info.get('alignment'),
                'style': text_info.get('style', {}),
                'effects': text_info.get('effects', [])
            }
            text_elements.append(text_element)
        
        return text_elements
    
    def _extract_project_settings(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract project-level settings."""
        settings = {
            'resolution': {
                'width': content_data.get('canvas_config', {}).get('width'),
                'height': content_data.get('canvas_config', {}).get('height')
            },
            'frame_rate': content_data.get('canvas_config', {}).get('fps'),
            'duration': content_data.get('duration'),
            'color_space': content_data.get('color_space'),
            'audio_sample_rate': content_data.get('audio_sample_rate')
        }
        return settings
    
    def _extract_timeline_structure(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract timeline structure information."""
        tracks = content_data.get('tracks', [])
        
        structure = {
            'total_tracks': len(tracks),
            'video_tracks': [],
            'audio_tracks': [],
            'track_info': []
        }
        
        for i, track in enumerate(tracks):
            track_info = {
                'index': i,
                'type': track.get('type'),
                'segments_count': len(track.get('segments', [])),
                'total_duration': sum(seg.get('target_timerange', {}).get('duration', 0) 
                                    for seg in track.get('segments', []))
            }
            
            if track.get('type') == 'video':
                structure['video_tracks'].append(track_info)
            elif track.get('type') == 'audio':
                structure['audio_tracks'].append(track_info)
            
            structure['track_info'].append(track_info)
        
        return structure
    
    def _calculate_total_duration(self, content_data: Dict[str, Any]) -> Optional[float]:
        """Calculate total project duration."""
        return content_data.get('duration')
    
    def analyze_all_projects(self) -> List[ProjectAnalysis]:
        """Analyze all matching projects."""
        matching_projects = self.find_matching_projects()
        
        analyses = []
        for project_path in matching_projects:
            try:
                analysis = self.analyze_project(project_path)
                analyses.append(analysis)
                self.project_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze {project_path.name}: {e}")
        
        # Build asset and effects catalogs
        self._build_asset_catalog()
        self._build_effects_catalog()
        
        return analyses
    
    def _build_asset_catalog(self):
        """Build catalog of all assets across projects."""
        asset_usage = defaultdict(list)
        
        for analysis in self.project_analyses:
            for asset in analysis.media_assets:
                key = (asset.file_name, asset.asset_type)
                asset_usage[key].append(analysis.project_name)
        
        # Update usage counts
        for analysis in self.project_analyses:
            for asset in analysis.media_assets:
                key = (asset.file_name, asset.asset_type)
                asset.usage_count = len(asset_usage[key])
                asset.projects_used_in = asset_usage[key]
    
    def _build_effects_catalog(self):
        """Build catalog of all effects across projects."""
        effect_usage = defaultdict(list)
        
        for analysis in self.project_analyses:
            for effect in analysis.effects_used:
                key = (effect.effect_name, effect.effect_type)
                effect_usage[key].append(analysis.project_name)
        
        # Update usage counts
        for analysis in self.project_analyses:
            for effect in analysis.effects_used:
                key = (effect.effect_name, effect.effect_type)
                effect.usage_count = len(effect_usage[key])
                effect.projects_used_in = effect_usage[key]
    
    def generate_reuse_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for asset reuse in Weeks 3-5."""
        recommendations = {
            'highly_reused_assets': [],
            'consistent_effects': [],
            'visual_themes': [],
            'audio_patterns': [],
            'text_styling_patterns': []
        }
        
        # Find highly reused assets
        all_assets = []
        for analysis in self.project_analyses:
            all_assets.extend(analysis.media_assets)
        
        asset_freq = defaultdict(int)
        for asset in all_assets:
            asset_freq[asset.file_name] += 1
        
        # Assets used in multiple projects
        for asset_name, count in asset_freq.items():
            if count >= 2:
                matching_assets = [a for a in all_assets if a.file_name == asset_name]
                if matching_assets:
                    recommendations['highly_reused_assets'].append({
                        'asset_name': asset_name,
                        'usage_count': count,
                        'asset_type': matching_assets[0].asset_type,
                        'projects': matching_assets[0].projects_used_in
                    })
        
        # Find consistent effects
        all_effects = []
        for analysis in self.project_analyses:
            all_effects.extend(analysis.effects_used)
        
        effect_freq = defaultdict(int)
        for effect in all_effects:
            effect_freq[effect.effect_name] += 1
        
        for effect_name, count in effect_freq.items():
            if count >= 2:
                matching_effects = [e for e in all_effects if e.effect_name == effect_name]
                if matching_effects:
                    recommendations['consistent_effects'].append({
                        'effect_name': effect_name,
                        'usage_count': count,
                        'effect_type': matching_effects[0].effect_type,
                        'projects': matching_effects[0].projects_used_in
                    })
        
        return recommendations
    
    def generate_html_report(self, output_path: str):
        """Generate comprehensive HTML report."""
        logger.info(f"Generating HTML report to: {output_path}")
        
        # Prepare data
        recommendations = self.generate_reuse_recommendations()
        
        # Generate HTML report (similar to church analyzer but focused on production insights)
        html_content = self._create_html_report_content(recommendations)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Report generated: {output_path}")
    
    def _create_html_report_content(self, recommendations: Dict[str, Any]) -> str:
        """Create the HTML report content."""
        # Prepare summary data
        total_assets = sum(len(p.media_assets) for p in self.project_analyses)
        total_effects = sum(len(p.effects_used) for p in self.project_analyses)
        
        # Asset breakdown
        asset_types = defaultdict(int)
        for analysis in self.project_analyses:
            for asset in analysis.media_assets:
                asset_types[asset.asset_type] += 1
        
        # Project data for JavaScript
        projects_data = []
        for analysis in self.project_analyses:
            project_data = {
                'name': analysis.project_name,
                'duration': analysis.total_duration,
                'video_tracks': analysis.video_tracks,
                'audio_tracks': analysis.audio_tracks,
                'media_count': len(analysis.media_assets),
                'effects_count': len(analysis.effects_used),
                'text_elements': len(analysis.text_elements),
                'resolution': analysis.project_settings.get('resolution', {}),
                'creation_date': analysis.creation_date
            }
            projects_data.append(project_data)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Great Reconciliation CapCut Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-video: #ff6b6b;
            --accent-audio: #4ecdc4;
            --accent-image: #45b7d1;
            --accent-text: #96ceb4;
            --accent-effects: #feca57;
            --border-color: #30363d;
            --highlight: #ffd93d;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
            border-radius: 15px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }}
        
        h1 {{
            font-size: 3em;
            margin-bottom: 15px;
            background: linear-gradient(45deg, var(--accent-video), var(--accent-audio), var(--accent-image));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        
        .stats-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: var(--bg-secondary);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-projects {{ color: var(--accent-video); }}
        .stat-assets {{ color: var(--accent-audio); }}
        .stat-effects {{ color: var(--accent-effects); }}
        .stat-video {{ color: var(--accent-video); }}
        .stat-audio {{ color: var(--accent-audio); }}
        .stat-image {{ color: var(--accent-image); }}
        
        .section {{
            background: var(--bg-secondary);
            margin-bottom: 30px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }}
        
        .section-header {{
            background: var(--bg-tertiary);
            padding: 20px 30px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        .section-title {{
            font-size: 1.5em;
            margin-bottom: 5px;
        }}
        
        .section-description {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        .section-content {{
            padding: 30px;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}
        
        .project-card {{
            background: var(--bg-tertiary);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }}
        
        .project-card:hover {{
            border-color: var(--accent-video);
            box-shadow: 0 5px 20px rgba(255, 107, 107, 0.2);
        }}
        
        .project-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: var(--accent-video);
        }}
        
        .project-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .project-stat {{
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            background: var(--bg-primary);
            border-radius: 6px;
            font-size: 0.85em;
        }}
        
        .project-stat-label {{
            color: var(--text-secondary);
        }}
        
        .project-stat-value {{
            font-weight: bold;
        }}
        
        .recommendations-list {{
            list-style: none;
        }}
        
        .recommendation-item {{
            background: var(--bg-tertiary);
            margin-bottom: 15px;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--accent-image);
        }}
        
        .recommendation-title {{
            font-weight: bold;
            margin-bottom: 10px;
            color: var(--accent-image);
        }}
        
        .recommendation-details {{
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        .tag {{
            display: inline-block;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin: 2px;
        }}
        
        .tag-video {{ background: var(--accent-video); color: white; }}
        .tag-audio {{ background: var(--accent-audio); color: white; }}
        .tag-image {{ background: var(--accent-image); color: white; }}
        .tag-effect {{ background: var(--accent-effects); color: white; }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 2em; }}
            .stats-overview {{ grid-template-columns: 1fr; }}
            .projects-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Great Reconciliation CapCut Analysis</h1>
            <p class="subtitle">Production Analysis for The Great Reconciliation Series</p>
            <p class="subtitle">Analysis of {len(self.project_analyses)} CapCut projects completed</p>
            <p style="font-size: 0.9em; color: var(--text-secondary); margin-top: 10px;">
                Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </header>
        
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-value stat-projects">{len(self.project_analyses)}</div>
                <div class="stat-label">Projects Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-assets">{total_assets}</div>
                <div class="stat-label">Media Assets</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-effects">{total_effects}</div>
                <div class="stat-label">Effects Used</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-video">{asset_types.get('video', 0)}</div>
                <div class="stat-label">Video Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-audio">{asset_types.get('audio', 0)}</div>
                <div class="stat-label">Audio Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-image">{asset_types.get('image', 0)}</div>
                <div class="stat-label">Image Files</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2 class="section-title">Asset Distribution</h2>
                <p class="section-description">Breakdown of media assets across all projects</p>
            </div>
            <div class="section-content">
                <div class="chart-container">
                    <canvas id="assetChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2 class="section-title">Project Overview</h2>
                <p class="section-description">Detailed analysis of each CapCut project</p>
            </div>
            <div class="section-content">
                <div class="projects-grid" id="projectsGrid">
                    <!-- Projects will be populated by JavaScript -->
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-header">
                <h2 class="section-title">Reuse Recommendations for Weeks 3-5</h2>
                <p class="section-description">Assets and effects you should consider reusing in future episodes</p>
            </div>
            <div class="section-content">
                <div class="recommendations-content">
                    <h3 style="margin-bottom: 20px; color: var(--accent-image);">Highly Reused Assets</h3>
                    <ul class="recommendations-list" id="assetRecommendations">
                        <!-- Will be populated by JavaScript -->
                    </ul>
                    
                    <h3 style="margin: 30px 0 20px; color: var(--accent-effects);">Consistent Effects</h3>
                    <ul class="recommendations-list" id="effectRecommendations">
                        <!-- Will be populated by JavaScript -->
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Data from Python
        const projectsData = {json.dumps(projects_data, indent=2)};
        const assetTypes = {json.dumps(dict(asset_types), indent=2)};
        const recommendations = {json.dumps(recommendations, indent=2)};
        
        // Chart configuration
        Chart.defaults.color = '#8b949e';
        Chart.defaults.borderColor = '#30363d';
        
        // Asset Distribution Chart
        const assetCtx = document.getElementById('assetChart').getContext('2d');
        const assetChart = new Chart(assetCtx, {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(assetTypes),
                datasets: [{{
                    data: Object.values(assetTypes),
                    backgroundColor: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'],
                    borderWidth: 2,
                    borderColor: '#0d1117'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            usePointStyle: true,
                            padding: 20
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Populate projects grid
        function populateProjectsGrid() {{
            const grid = document.getElementById('projectsGrid');
            
            projectsData.forEach(project => {{
                const card = document.createElement('div');
                card.className = 'project-card';
                
                const duration = project.duration ? (project.duration / 60).toFixed(1) + ' min' : 'Unknown';
                const resolution = project.resolution && project.resolution.width ? 
                    `${{project.resolution.width}}x${{project.resolution.height}}` : 'Unknown';
                
                card.innerHTML = `
                    <div class="project-title">${{project.name}}</div>
                    <div class="project-stats">
                        <div class="project-stat">
                            <span class="project-stat-label">Duration:</span>
                            <span class="project-stat-value">${{duration}}</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-label">Resolution:</span>
                            <span class="project-stat-value">${{resolution}}</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-label">Video Tracks:</span>
                            <span class="project-stat-value">${{project.video_tracks}}</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-label">Audio Tracks:</span>
                            <span class="project-stat-value">${{project.audio_tracks}}</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-label">Media Assets:</span>
                            <span class="project-stat-value">${{project.media_count}}</span>
                        </div>
                        <div class="project-stat">
                            <span class="project-stat-label">Effects:</span>
                            <span class="project-stat-value">${{project.effects_count}}</span>
                        </div>
                    </div>
                `;
                
                grid.appendChild(card);
            }});
        }}
        
        // Populate recommendations
        function populateRecommendations() {{
            const assetRecs = document.getElementById('assetRecommendations');
            const effectRecs = document.getElementById('effectRecommendations');
            
            // Asset recommendations
            recommendations.highly_reused_assets.forEach(asset => {{
                const li = document.createElement('li');
                li.className = 'recommendation-item';
                li.innerHTML = `
                    <div class="recommendation-title">${{asset.asset_name}}</div>
                    <div class="recommendation-details">
                        <span class="tag tag-${{asset.asset_type}}">${{asset.asset_type}}</span>
                        Used in ${{asset.usage_count}} projects: ${{asset.projects.join(', ')}}
                    </div>
                `;
                assetRecs.appendChild(li);
            }});
            
            if (recommendations.highly_reused_assets.length === 0) {{
                assetRecs.innerHTML = '<p style="color: var(--text-secondary);">No highly reused assets found across projects.</p>';
            }}
            
            // Effect recommendations
            recommendations.consistent_effects.forEach(effect => {{
                const li = document.createElement('li');
                li.className = 'recommendation-item';
                li.innerHTML = `
                    <div class="recommendation-title">${{effect.effect_name}}</div>
                    <div class="recommendation-details">
                        <span class="tag tag-effect">${{effect.effect_type}}</span>
                        Used in ${{effect.usage_count}} projects: ${{effect.projects.join(', ')}}
                    </div>
                `;
                effectRecs.appendChild(li);
            }});
            
            if (recommendations.consistent_effects.length === 0) {{
                effectRecs.innerHTML = '<p style="color: var(--text-secondary);">No consistent effects found across projects.</p>';
            }}
        }}
        
        // Initialize
        populateProjectsGrid();
        populateRecommendations();
    </script>
</body>
</html>"""


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Great Reconciliation CapCut projects"
    )
    parser.add_argument(
        '--capcut-drafts',
        default='/mnt/d/Work/Asabaal Ventures/CapCut Projects/CapCut Drafts',
        help='Path to CapCut Drafts directory'
    )
    parser.add_argument(
        '--output-videos',
        default='/mnt/d/Work/Asabaal Ventures/The Great Reconciliation',
        help='Path to output videos directory'
    )
    parser.add_argument(
        '--output',
        default='great_reconciliation_analysis_report.html',
        help='Output HTML report path'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = GreatReconciliationAnalyzer(
        capcut_drafts_path=args.capcut_drafts,
        output_videos_path=args.output_videos
    )
    
    # Analyze all projects
    logger.info("Starting Great Reconciliation CapCut analysis...")
    analyses = analyzer.analyze_all_projects()
    
    # Generate report
    analyzer.generate_html_report(args.output)
    
    logger.info(f"\nAnalysis complete!")
    logger.info(f"Projects analyzed: {len(analyses)}")
    logger.info(f"Report saved to: {args.output}")


if __name__ == '__main__':
    main()