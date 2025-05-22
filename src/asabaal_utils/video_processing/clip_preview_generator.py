"""
Clip preview generator for video timeline analysis.

This module provides utilities for generating thumbnail previews of video clips
and creating visual dashboards showing clip usage and duplicates.
"""

import os
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import json
import base64
from datetime import datetime
import hashlib
from collections import defaultdict

from .path_utils import convert_path_to_current_os, resolve_media_path, get_available_wsl_mounts
from .frame_extractor import FrameExtractor

import numpy as np
from tqdm import tqdm
import subprocess
from PIL import Image, ImageStat
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)


class ClipPreviewGenerator:
    """
    Generates thumbnail previews for video clips and identifies duplicated clips.
    
    This class extracts frames from video clips at specific timestamps, 
    analyzes them for similarity, and creates a visual dashboard showing
    clip usage and duplication.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        thumbnail_width: int = 320,
        thumbnail_height: int = 180,
        output_format: str = "jpg",
        output_quality: int = 85,
        similarity_threshold: float = None,  # No longer used - kept for backward compatibility
        ffmpeg_path: str = "ffmpeg",
        frame_extraction_method: str = "one_third_point",
    ):
        """
        Initialize the clip preview generator.
        
        Args:
            output_dir: Directory to save thumbnail images (if None, creates a temp dir)
            thumbnail_width: Width of thumbnail images in pixels
            thumbnail_height: Height of thumbnail images in pixels
            output_format: Format to save thumbnails (jpg, png)
            output_quality: Output quality (0-100) for JPEG format
            similarity_threshold: Threshold for considering clips as duplicates (0-1)
        """
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
        self.output_format = output_format.lower()
        self.output_quality = output_quality
        self.ffmpeg_path = ffmpeg_path
        
        # Create output directory if needed
        if output_dir is None:
            self.output_dir = tempfile.mkdtemp(prefix="clip_previews_")
            logger.info(f"Created temporary thumbnail directory: {self.output_dir}")
        else:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Saving thumbnails to: {self.output_dir}")
        
        # Frame extraction method to use (controls which part of the clip is sampled)
        self.frame_extraction_method = frame_extraction_method
        
        # Initialize frame extractor
        self.frame_extractor = FrameExtractor(
            output_dir=self.output_dir,
            output_width=self.thumbnail_width,
            output_height=self.thumbnail_height,
            output_format=self.output_format,
            output_quality=self.output_quality,
            ffmpeg_path=self.ffmpeg_path
        )
        
        # Initialize clip data structures
        self.clips = []
        self.clip_features = []
        self.duplicate_groups = []
    
    def _extract_clip_frame(
        self, 
        video_path: str, 
        start_time: float,
        duration: float,
        clip_id: str,
        wsl_path_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract a representative frame from a video clip.
        
        Args:
            video_path: Path to the video file
            start_time: Start time of the clip in seconds
            duration: Duration of the clip in seconds
            clip_id: Unique identifier for the clip
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            Dictionary with clip preview information
            
        Note:
            This method uses the FrameExtractor module for robust frame extraction.
        """
        # Determine frame timestamp (prefer 1/3 into the clip for a representative frame)
        frame_time = start_time + (duration / 3)
        
        # Use frame extractor to extract the frame, using the specified method
        extraction_result = self.frame_extractor.extract_frame_with_method(
            video_path=video_path,
            timestamp=frame_time,
            method_id=self.frame_extraction_method,
            frame_id=f"clip_{clip_id.replace(':', '_')}",
            duration=duration,
            wsl_path_prefix=wsl_path_prefix
        )
        
        # If the specified method fails, try with default fallback behavior
        if not extraction_result['success']:
            logger.info(f"Specific method '{self.frame_extraction_method}' failed, trying fallback methods")
            extraction_result = self.frame_extractor.extract_frame(
                video_path=video_path,
                timestamp=frame_time,
                frame_id=f"clip_{clip_id.replace(':', '_')}",
                duration=duration,
                wsl_path_prefix=wsl_path_prefix
            )
        
        # Check if extraction was successful
        if extraction_result['success']:
            # Extract features for similarity comparison
            img = Image.open(extraction_result['frame_path'])
            features = self._extract_image_features(img)
            
            # Map frame extractor result to our expected output format
            return {
                'clip_id': clip_id,
                'thumbnail_path': extraction_result['frame_path'],
                'features': features,
                'has_thumbnail': True,
                'frame_time': frame_time,
                'start_time': start_time,
                'duration': duration,
                'original_path': video_path,
                'resolved_path': extraction_result['resolved_path'],
                'extraction_method': extraction_result['method_used'],
                'extraction_success': True,
                'frame_quality': extraction_result['quality_info']['quality'],
                'frame_brightness': extraction_result['quality_info']['brightness'],
                'is_black_frame': extraction_result['quality_info']['is_black']
            }
        else:
            # If frame extraction failed but we got a dummy image
            if extraction_result['frame_path'] and os.path.exists(extraction_result['frame_path']):
                # Try to extract features from the dummy image
                try:
                    img = Image.open(extraction_result['frame_path'])
                    features = self._extract_image_features(img)
                except Exception:
                    # If we can't even extract features, use zeros
                    features = np.zeros(64 * 36 * 3)
                
                return {
                    'clip_id': clip_id,
                    'thumbnail_path': extraction_result['frame_path'],
                    'features': features,
                    'has_thumbnail': True,
                    'frame_time': frame_time,
                    'start_time': start_time,
                    'duration': duration,
                    'original_path': video_path,
                    'resolved_path': extraction_result['resolved_path'],
                    'is_dummy': True,
                    'extraction_method': 'dummy',
                    'extraction_success': False,
                    'error': extraction_result.get('error', 'Frame extraction failed')
                }
            else:
                # Complete failure - no thumbnail
                return {
                    'clip_id': clip_id,
                    'thumbnail_path': None,
                    'features': None,
                    'has_thumbnail': False,
                    'original_path': video_path,
                    'resolved_path': extraction_result.get('resolved_path', None),
                    'error': extraction_result.get('error', 'Unknown error'),
                    'extraction_method': 'failed',
                    'extraction_success': False
                }
    
    def _extract_image_features(self, img: Image.Image) -> np.ndarray:
        """
        Extract features from an image for similarity comparison.
        
        Args:
            img: PIL Image to analyze
            
        Returns:
            Numpy array of image features
        """
        try:
            # Define standard dimensions for feature extraction
            feature_width = 64
            feature_height = 36
            
            # Convert to smaller size for faster processing
            small_img = img.resize((feature_width, feature_height), Image.LANCZOS)
            
            # Convert to numpy array and flatten
            img_array = np.array(small_img)
            
            # Check if we got the expected shape (height, width, 3)
            if len(img_array.shape) != 3 or img_array.shape[2] != 3:
                # If image is grayscale or has alpha channel, convert to RGB
                if len(img_array.shape) == 2:  # Grayscale
                    # Convert grayscale to RGB
                    rgb_img = Image.new("RGB", small_img.size)
                    rgb_img.paste(small_img)
                    img_array = np.array(rgb_img)
                elif img_array.shape[2] == 4:  # RGBA
                    # Remove alpha channel
                    img_array = img_array[:, :, :3]
                else:
                    # Create a dummy array of the right shape
                    img_array = np.zeros((feature_height, feature_width, 3), dtype=np.uint8)
            
            # Normalize the features
            features = img_array.reshape(-1) / 255.0
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting image features: {e}")
            
            # Return a zero vector of the correct size
            return np.zeros(feature_width * feature_height * 3)
    
    def _find_duplicate_clips(self) -> List[List[int]]:
        """
        Find groups of duplicate clips based on media filename.
        
        This identifies duplicates by checking for the same source video file,
        rather than analyzing image content similarity.
        
        Returns:
            List of lists, where each inner list contains indices of clips with the same source file
        """
        # Group clips by their material path (source video file)
        path_to_indices = {}
        
        for i, clip in enumerate(self.clips):
            # Get the original material path (source video file)
            material_path = clip.get('material_path', '')
            if not material_path:
                continue
                
            # Get just the filename without path
            material_filename = os.path.basename(material_path)
            
            # Add to the appropriate group
            if material_filename not in path_to_indices:
                path_to_indices[material_filename] = []
            path_to_indices[material_filename].append(i)
        
        # Create list of duplicate groups (only include groups with more than one clip)
        duplicates = [indices for filename, indices in path_to_indices.items() if len(indices) > 1]
        
        # Log duplicate findings
        for i, group in enumerate(duplicates):
            filenames = [os.path.basename(self.clips[idx].get('material_path', 'unknown')) for idx in group]
            logger.info(f"Duplicate group {i+1}: Found {len(group)} instances of {filenames[0]}")
        
        return duplicates
    
    def process_clips(self, timeline_data: Dict[str, Any], wsl_path_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Process video clips from timeline data to generate previews and find duplicates.
        
        Args:
            timeline_data: Timeline data from VideoTimelineAnalyzer.analyze_timeline()
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            Dictionary with thumbnail and duplicate information
        """
        video_clips = timeline_data.get('video_clips', [])
        if not video_clips:
            logger.warning("No video clips found in timeline data")
            return {
                'clips': [],
                'duplicates': [],
                'unused_media': [],
                'timestamp': datetime.now().isoformat()
            }
        
        # Reset internal state
        self.clips = []
        self.clip_features = []
        
        # Process each clip
        logger.info(f"Generating previews for {len(video_clips)} clips")
        for i, clip in enumerate(tqdm(video_clips, desc="Generating clip previews")):
            material_path = clip.get('material_path', '')
            start_time = clip.get('start_time', 0)
            duration = clip.get('duration', 0)
            clip_id = f"{i:04d}_{start_time:.2f}"
            
            # Extract frame and features
            clip_data = self._extract_clip_frame(
                video_path=material_path,
                start_time=start_time,
                duration=duration,
                clip_id=clip_id,
                wsl_path_prefix=wsl_path_prefix
            )
            
            # Add original clip data
            for key, value in clip.items():
                clip_data[key] = value
            
            self.clips.append(clip_data)
            
            # Add features for similarity comparison
            if clip_data['features'] is not None:
                self.clip_features.append(clip_data['features'])
            else:
                # Create empty feature vector with correct dimensions
                feature_size = 64 * 36 * 3  # This should match the size in _extract_image_features
                self.clip_features.append(np.zeros(feature_size))
        
        # Find duplicates
        duplicate_indices = self._find_duplicate_clips()
        
        # Create duplicate groups with clip data
        self.duplicate_groups = []
        for indices in duplicate_indices:
            group = [self.clips[i] for i in indices]
            self.duplicate_groups.append(group)
        
        # Mark clips as duplicates
        duplicate_clip_ids = set()
        for group in self.duplicate_groups:
            for clip in group:
                duplicate_clip_ids.add(clip['clip_id'])
        
        for clip in self.clips:
            clip['is_duplicate'] = clip['clip_id'] in duplicate_clip_ids
        
        # Identify unused media files if timeline_data contains media_pool
        unused_media = []
        if 'media_pool' in timeline_data and isinstance(timeline_data['media_pool'], list):
            # Find all files in the media pool
            all_media = self._extract_all_media(timeline_data['media_pool'])
            
            # Find all used media files from clips
            used_media_paths = set()
            for clip in self.clips:
                material_path = clip.get('material_path', '')
                if material_path:
                    # Normalize path for comparison
                    norm_path = os.path.normpath(material_path)
                    used_media_paths.add(norm_path)
                    
                    # Also add just the filename to catch relative paths
                    filename = os.path.basename(material_path)
                    used_media_paths.add(filename)
            
            # Identify unused media
            for media in all_media:
                # Check if any of the potential paths for this media are in used_media_paths
                is_used = False
                for path in [media.get('path', ''), os.path.basename(media.get('path', ''))]:  
                    if path and path in used_media_paths:
                        is_used = True
                        break
                
                if not is_used:
                    unused_media.append(media)
        
        return {
            'clips': self.clips,
            'duplicates': self.duplicate_groups,
            'unused_media': unused_media,
            'timestamp': datetime.now().isoformat(),
            'output_dir': self.output_dir,
            'path_conversion_info': {
                'wsl_path_prefix': wsl_path_prefix,
                'available_mounts': get_available_wsl_mounts()
            }
        }
    
    def generate_dashboard(
        self, 
        timeline_data: Dict[str, Any],
        output_file: str,
        include_base64: bool = False,
        wsl_path_prefix: Optional[str] = None
    ) -> str:
        """
        Generate an HTML dashboard showing clips and duplicates.
        
        Args:
            timeline_data: Timeline data from VideoTimelineAnalyzer.analyze_timeline()
            output_file: Path to save the HTML dashboard
            include_base64: If True, embed thumbnails directly in HTML
            wsl_path_prefix: Optional WSL path prefix for Windows paths
            
        Returns:
            Path to the saved HTML dashboard
        """
        # Process clips if not already processed
        if not self.clips:
            self.process_clips(timeline_data, wsl_path_prefix=wsl_path_prefix)
        
        # Generate HTML content
        html_content = self._generate_html_dashboard(include_base64, timeline_data)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {output_file}")
        return output_file
    
    def _extract_all_media(self, media_pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all media files from the media pool.
        
        Args:
            media_pool: List of media items from the timeline data
            
        Returns:
            List of media file information dictionaries
        """
        all_media = []
        
        for media_item in media_pool:
            # Extract basic media information
            media_path = media_item.get('path', '')
            if not media_path:
                continue
                
            media_name = os.path.basename(media_path)
            media_type = media_item.get('type', 'unknown')
            
            # Determine media type from file extension if not specified
            if media_type == 'unknown':
                ext = os.path.splitext(media_path)[1].lower()
                if ext in ['.mp4', '.mov', '.avi', '.mkv']:
                    media_type = 'video'
                elif ext in ['.mp3', '.wav', '.m4a', '.aac']:
                    media_type = 'audio'
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    media_type = 'image'
            
            # Extract duration if available
            duration = None
            if 'duration' in media_item:
                # Convert to seconds if in microseconds
                if media_item['duration'] > 10000:  # Likely in microseconds
                    duration = media_item['duration'] / 1000000
                else:
                    duration = media_item['duration']
            
            # Create media info dictionary
            media_info = {
                'path': media_path,
                'name': media_name,
                'type': media_type,
                'duration': duration,
                'id': media_item.get('id', None)
            }
            
            all_media.append(media_info)
        
        return all_media
        
    def _generate_html_dashboard(self, include_base64: bool = False, timeline_data: Dict[str, Any] = None) -> str:
        """
        Generate HTML content for the dashboard.
        
        Args:
            include_base64: If True, embed thumbnails directly in HTML
            
        Returns:
            HTML content as a string
        """
        # Get basic statistics
        total_clips = len(self.clips)
        duplicate_clips = sum(1 for clip in self.clips if clip.get('is_duplicate', False))
        unique_clips = total_clips - duplicate_clips
        
        # Get extraction method statistics
        primary_method_count = sum(1 for clip in self.clips if clip.get('extraction_method') == 'primary')
        fallback_methods_count = sum(1 for clip in self.clips if clip.get('extraction_method', '').startswith('fallback_'))
        dummy_images_count = sum(1 for clip in self.clips if clip.get('extraction_method') in ['dummy', 'emergency_dummy'])
        failed_extractions = sum(1 for clip in self.clips if clip.get('extraction_method') in ['failed', 'all_fallbacks_failed', 'not_attempted'])
        
        # Get frame quality statistics
        high_quality_frames = sum(1 for clip in self.clips if clip.get('frame_quality') == 'high')
        low_quality_frames = sum(1 for clip in self.clips if clip.get('frame_quality') == 'low')
        poor_quality_frames = sum(1 for clip in self.clips if clip.get('frame_quality') == 'poor')
        black_frames = sum(1 for clip in self.clips if clip.get('is_black_frame', False))
        
        # Get statistics for specific fallback methods if any were used
        fallback_methods = {}
        for clip in self.clips:
            method = clip.get('extraction_method', '')
            if method.startswith('fallback_'):
                method_name = method.replace('fallback_', '')
                fallback_methods[method_name] = fallback_methods.get(method_name, 0) + 1
        
        # Get thumbnail paths for clips
        valid_clips = [clip for clip in self.clips if clip.get('has_thumbnail', False)]
        
        # Create HTML header
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Clip Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{  
            --bg-color: #fff;
            --text-color: #333;
            --card-bg: #fff;
            --card-border: #ddd;
            --track-bg: #f8f9fa;
            --group-bg: #f8f9fa;
            --unique-border: #28a745;
            --duplicate-border: #dc3545;
            --primary-color: #0d6efd;
            --tooltip-color: #212529;
        }}
        
        [data-bs-theme="dark"] {{  
            --bg-color: #222;
            --text-color: #eee;
            --card-bg: #333;
            --card-border: #444;
            --track-bg: #444;
            --group-bg: #383838;
            --unique-border: #198754;
            --duplicate-border: #dc3545;
            --primary-color: #0d6efd;
            --tooltip-color: #f8f9fa;
        }}
        
        body {{ 
            padding: 20px; 
            background-color: var(--bg-color); 
            color: var(--text-color);
        }}
        .navbar {{ margin-bottom: 20px; background-color: var(--primary-color); }}
        .clip-card {{ margin-bottom: 20px; }}
        .card {{ background-color: var(--card-bg); border-color: var(--card-border); }}
        .card-body {{ color: var(--text-color); }}
        .list-group-item {{ background-color: var(--card-bg); color: var(--text-color); border-color: var(--card-border); }}
        .thumbnail {{ width: 100%; height: auto; object-fit: contain; }}
        .stats-card {{ margin-bottom: 20px; }}
        .duplicate-group {{ background-color: var(--group-bg); padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .clip-card.is-duplicate {{ border: 2px solid var(--duplicate-border); }}
        .filters {{ margin-bottom: 20px; }}
        .timeline-container {{ margin-bottom: 50px; }}
        .timeline-visualization {{ margin-top: 15px; margin-bottom: 15px; overflow-x: auto; }}
        .timeline-track {{ height: 80px; position: relative; background-color: var(--track-bg); margin-bottom: 10px; border-radius: 4px; }}
        .timeline-track-simple {{ height: 40px; position: relative; background-color: var(--track-bg); margin-bottom: 5px; border-radius: 4px; }}
        .timeline-clip {{ 
            position: absolute; 
            height: 100%; 
            background-color: rgba(0,0,0,0.3); 
            overflow: hidden; 
            border-radius: 4px;
            border: 2px solid var(--primary-color); 
        }}
        .timeline-clip.is-duplicate {{ 
            border-width: 3px;
        }}
        .timeline-clip-simple {{ 
            position: absolute; 
            height: 100%; 
            border-radius: 4px;
            opacity: 0.85; 
            color: white;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            text-shadow: 0 0 3px black, 0 0 3px black, 0 0 3px black, 0 0 3px black;
            transition: all 0.2s ease;
        }}
        .timeline-clip-simple:hover {{
            opacity: 1;
            transform: scaleY(1.1);
            z-index: 100;
            box-shadow: 0 0 8px rgba(255,255,255,0.5);
        }}
        .duplicate-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            padding: 3px 8px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .legend-item:hover {{
            transform: scale(1.05);
        }}
        .timeline-clip img {{ 
            width: 100%; 
            height: 100%; 
            object-fit: cover; 
            opacity: 0.85; 
        }}
        .timeline-clip-marker {{ 
            position: absolute; 
            top: -15px; 
            width: 30px; 
            height: 15px; 
            border-radius: 3px 3px 0 0; 
            text-align: center; 
            font-weight: bold; 
            color: white; 
            font-size: 10px; 
            line-height: 15px; 
        }}
        .clip-label {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px; color: white; }}
        .theme-toggle {{ cursor: pointer; }}
        .highlight {{ box-shadow: 0 0 15px 5px var(--primary-color) !important; }}
        .hover-highlight {{ box-shadow: 0 0 10px 3px rgba(255,255,255,0.7) !important; }}
    </style>
</head>
<body data-bs-theme="dark">
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand">Video Clip Dashboard</span>
            <div class="d-flex">
                <div class="form-check form-switch">
                    <input class="form-check-input theme-toggle" type="checkbox" id="themeToggle">
                    <label class="form-check-label text-light" for="themeToggle">Dark Mode</label>
                </div>
            </div>
        </div>
    </nav>
    <div class="container-fluid">
"""
        
        # Add statistics card
        html += f"""
        <div class="row stats-card">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Clip Statistics</h5>
                        <div class="row">
                            <div class="col-md-3">
                                <p><strong>Total Clips:</strong> {total_clips}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong>Unique Clips:</strong> {unique_clips}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong>Duplicate Clips:</strong> {duplicate_clips}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong>Successful Extractions:</strong> {primary_method_count + fallback_methods_count}</p>
                            </div>
                        </div>
                        <h5 class="card-title mt-3">Extraction Statistics</h5>
                        <div class="row">
                            <div class="col-md-3">
                                <p><strong class="text-success">Primary Method:</strong> {primary_method_count}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-warning">Fallback Methods:</strong> {fallback_methods_count}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-danger">Dummy Images:</strong> {dummy_images_count}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-danger">Failed Extractions:</strong> {failed_extractions}</p>
                            </div>
                        </div>
                        
                        <h5 class="card-title mt-3">Frame Quality</h5>
                        <div class="row">
                            <div class="col-md-3">
                                <p><strong class="text-success">High Quality:</strong> {high_quality_frames}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-warning">Low Quality:</strong> {low_quality_frames}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-danger">Poor Quality:</strong> {poor_quality_frames}</p>
                            </div>
                            <div class="col-md-3">
                                <p><strong class="text-danger">Black Frames:</strong> {black_frames}</p>
                            </div>
                        </div>
"""

        # Add fallback methods information if available
        if fallback_methods:
            html += """
                        <div class="mt-2">
                            <p><strong>Fallback Methods Used:</strong></p>
                            <ul class="list-group">
"""
            for method, count in fallback_methods.items():
                html += f'                                <li class="list-group-item d-flex justify-content-between align-items-center">{method} <span class="badge bg-warning rounded-pill">{count}</span></li>\n'
            
            html += """
                            </ul>
                        </div>
"""
        
        # Close the statistics card
        html += """
                    </div>
                </div>
            </div>
        </div>
"""
        
        # Add filters section
        html += """
        <div class="row filters">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Filters</h5>
                        <div class="row">
                            <div class="col-md-4">
                                <h6>By Clip Type:</h6>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-all" checked>
                                    <label class="form-check-label" for="show-all">All Clips</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-unique">
                                    <label class="form-check-label" for="show-unique">Unique Clips Only</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-duplicates">
                                    <label class="form-check-label" for="show-duplicates">Duplicate Clips Only</label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>By Extraction Method:</h6>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-all-extraction" checked>
                                    <label class="form-check-label" for="show-all-extraction">All Methods</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-primary">
                                    <label class="form-check-label" for="show-primary">Primary Only</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-fallback">
                                    <label class="form-check-label" for="show-fallback">Fallbacks Only</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-failed">
                                    <label class="form-check-label" for="show-failed">Failed Only</label>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>By Frame Quality:</h6>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-all-quality" checked>
                                    <label class="form-check-label" for="show-all-quality">All Quality</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-high-quality">
                                    <label class="form-check-label" for="show-high-quality">High Only</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-low-quality">
                                    <label class="form-check-label" for="show-low-quality">Low Only</label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input class="form-check-input" type="checkbox" id="show-poor-quality">
                                    <label class="form-check-label" for="show-poor-quality">Poor Only</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timeline-container">
            <h3>Timeline Visualization</h3>
            <p class="text-muted">Thumbnail view with colored markers for duplicate groups</p>
            <div class="timeline-visualization">
"""

        # Add thumbnail timeline visualization
        max_track_index = max(clip.get('track_index', 0) for clip in self.clips) if self.clips else 0
        for track in range(max_track_index + 1):
            html += f'            <div class="timeline-track" id="track-{track}">\n'
            track_clips = [clip for clip in self.clips if clip.get('track_index', 0) == track]
            
            # Find the max end time for scaling
            max_end_time = max(clip.get('start_time', 0) + clip.get('duration', 0) for clip in self.clips) if self.clips else 0
            
            for clip in track_clips:
                start_percent = (clip.get('start_time', 0) / max_end_time) * 100 if max_end_time > 0 else 0
                width_percent = (clip.get('duration', 0) / max_end_time) * 100 if max_end_time > 0 else 0
                is_duplicate_class = "is-duplicate" if clip.get('is_duplicate', False) else ""
                clip_id = clip.get('clip_id', 'unknown')
                material_name = clip.get('material_name', 'Unknown')
                
                # Get the thumbnail path for this clip
                thumbnail_path = clip.get('thumbnail_path', '')
                thumbnail_exists = thumbnail_path and os.path.exists(thumbnail_path)
                
                # Determine if this clip is part of a duplicate group and which group
                duplicate_group_id = -1
                duplicate_marker = ''
                if clip.get('is_duplicate', False):
                    # Find which duplicate group this clip belongs to
                    for i, group in enumerate(self.duplicate_groups):
                        group_clip_ids = [c.get('clip_id') for c in group]
                        if clip_id in group_clip_ids:
                            duplicate_group_id = i
                            duplicate_marker = chr(65 + (i % 26))  # A, B, C, etc.
                            break
                
                # Generate a unique color for this duplicate group
                marker_style = ''
                border_style = ''
                if duplicate_group_id >= 0:
                    # Use hue rotation to generate distinct colors
                    hue = (duplicate_group_id * 137) % 360  # Golden angle to distribute colors
                    color = f'hsl({hue}, 80%, 45%)'
                    marker_style = f'background-color: {color};'
                    border_style = f'border-color: {color};'
                
                # Set clip style with custom border color for duplicates
                clip_style = f'left: {start_percent}%; width: {width_percent}%;'
                if border_style and is_duplicate_class:
                    clip_style += border_style
                    
                html += f'                <div class="timeline-clip {is_duplicate_class}" style="{clip_style}" title="{material_name} ({clip.get("start_time", 0):.2f}s - {clip.get("start_time", 0) + clip.get("duration", 0):.2f}s)" data-clip-id="{clip_id}">\n'
                
                # Add marker for duplicate group
                if duplicate_marker:
                    html += f'                    <div class="timeline-clip-marker" style="{marker_style}">{duplicate_marker}</div>\n'
                
                # Add thumbnail if available
                if thumbnail_exists:
                    # Get relative path for the thumbnail
                    rel_path = os.path.relpath(thumbnail_path, os.path.dirname(self.output_dir))
                    html += f'                    <img src="{rel_path}" alt="{material_name}" />\n'
                else:
                    html += f'                    <div class="clip-label">{material_name}</div>\n'
                
                html += f'                </div>\n'
            
            html += '            </div>\n'

        html += """
            </div>
        </div>
        
        <div class="timeline-container">
            <h3>Color-Coded Timeline</h3>
            <p class="text-muted">Simplified view with each duplicate group shown in a unique color</p>
            <div class="duplicate-legend"></div>
            <div class="timeline-visualization">
"""

        # Add color-coded timeline visualization
        for track in range(max_track_index + 1):
            html += f'            <div class="timeline-track-simple" id="simple-track-{track}">\n'
            track_clips = [clip for clip in self.clips if clip.get('track_index', 0) == track]
            
            for clip in track_clips:
                start_percent = (clip.get('start_time', 0) / max_end_time) * 100 if max_end_time > 0 else 0
                width_percent = (clip.get('duration', 0) / max_end_time) * 100 if max_end_time > 0 else 0
                clip_id = clip.get('clip_id', 'unknown')
                material_name = clip.get('material_name', 'Unknown')
                
                # Determine color and label based on duplicate group
                bg_color = "var(--primary-color)"
                label = ""
                duplicate_group_id = -1
                
                if clip.get('is_duplicate', False):
                    # Find which duplicate group this clip belongs to
                    for i, group in enumerate(self.duplicate_groups):
                        group_clip_ids = [c.get('clip_id') for c in group]
                        if clip_id in group_clip_ids:
                            duplicate_group_id = i
                            label = chr(65 + (i % 26))  # A, B, C, etc.
                            break
                    
                    if duplicate_group_id >= 0:
                        # Use hue rotation to generate distinct colors
                        hue = (duplicate_group_id * 137) % 360  # Golden angle to distribute colors
                        bg_color = f"hsl({hue}, 80%, 45%)"
                
                # Create the color-coded clip
                # Add data-duplicate-group attribute for easier group identification
                duplicate_group_label = label if label else ""
                html += f'                <div class="timeline-clip-simple" style="left: {start_percent}%; width: {width_percent}%; background-color: {bg_color};" title="{material_name} ({clip.get("start_time", 0):.2f}s - {clip.get("start_time", 0) + clip.get("duration", 0):.2f}s)" data-clip-id="{clip_id}" data-duplicate-group="{duplicate_group_label}">\n'
                
                # Add label if it's a duplicate
                if label:
                    html += f'                    {label}\n'
                
                html += f'                </div>\n'
            
            html += '            </div>\n'

        html += """
            </div>
        </div>
        
        <h3>Duplicate Clip Groups</h3>
"""

        # Add duplicate groups
        if self.duplicate_groups:
            for i, group in enumerate(self.duplicate_groups):
                html += f'        <div class="duplicate-group" id="duplicate-group-{i}">\n'
                html += f'            <h4>Duplicate Group {i+1} ({len(group)} clips)</h4>\n'
                html += '            <div class="row">\n'
                
                for clip in group:
                    html += self._generate_clip_card_html(clip, include_base64)
                
                html += '            </div>\n'
                html += '        </div>\n'
        else:
            html += '        <p>No duplicate clips found.</p>\n'
        
        # Add unused media section if available
        unused_media = timeline_data.get('unused_media', [])
        if unused_media:
            html += '        <h3>Unused Media Files</h3>\n'
            html += '        <p class="text-muted">These files are in your project\'s media pool but are not used in the timeline</p>\n'
            
            # Group by type
            media_by_type = defaultdict(list)
            for media in unused_media:
                media_type = media.get('type', 'unknown')
                media_by_type[media_type].append(media)
            
            # Create a card for each type
            for media_type, media_list in media_by_type.items():
                html += f'        <div class="card mb-4">\n'
                html += f'            <div class="card-header bg-warning">\n'
                html += f'                <h5 class="card-title mb-0">Unused {media_type.title()} Files ({len(media_list)})</h5>\n'
                html += '            </div>\n'
                html += '            <div class="card-body">\n'
                html += '                <div class="table-responsive">\n'
                html += '                    <table class="table table-striped">\n'
                html += '                        <thead>\n'
                html += '                            <tr>\n'
                html += '                                <th>Name</th>\n'
                html += '                                <th>Path</th>\n'
                html += '                                <th>Duration</th>\n'
                html += '                            </tr>\n'
                html += '                        </thead>\n'
                html += '                        <tbody>\n'
                
                for media in sorted(media_list, key=lambda x: x.get('name', '')):
                    name = media.get('name', 'Unknown')
                    path = media.get('path', 'Unknown')
                    duration = media.get('duration', None)
                    duration_str = f"{duration:.2f}s" if duration is not None else "N/A"
                    
                    html += '                            <tr>\n'
                    html += f'                                <td>{name}</td>\n'
                    html += f'                                <td>{path}</td>\n'
                    html += f'                                <td>{duration_str}</td>\n'
                    html += '                            </tr>\n'
                
                html += '                        </tbody>\n'
                html += '                    </table>\n'
                html += '                </div>\n'
                html += '            </div>\n'
                html += '        </div>\n'
        else:
            html += '        <h3>Unused Media Files</h3>\n'
            html += '        <p>No unused media files detected. All files in your project are used in the timeline.</p>\n'

        html += """
        <h3>All Clips</h3>
        <div class="row" id="all-clips">
"""

        # Add all clips
        for clip in self.clips:
            html += self._generate_clip_card_html(clip, include_base64)

        html += """
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Theme toggle functionality
        document.getElementById('themeToggle').addEventListener('change', function() {
            if (this.checked) {
                document.body.setAttribute('data-bs-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.setAttribute('data-bs-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
        
        // Load saved theme preference or use dark mode by default
        document.addEventListener('DOMContentLoaded', function() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'light') {
                document.getElementById('themeToggle').checked = false;
                document.body.setAttribute('data-bs-theme', 'light');
            } else {
                // Dark mode is default
                document.getElementById('themeToggle').checked = true;
                document.body.setAttribute('data-bs-theme', 'dark');
            }
        });
        
        // Current filter state
        let currentDuplicateFilter = 'all';
        let currentExtractionFilter = 'all';
        let currentQualityFilter = 'all';
        
        // Filter by duplicate status
        document.getElementById('show-all').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-unique').checked = false;
                document.getElementById('show-duplicates').checked = false;
                currentDuplicateFilter = 'all';
                applyFilters();
            }
        });
        
        document.getElementById('show-unique').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all').checked = false;
                document.getElementById('show-duplicates').checked = false;
                currentDuplicateFilter = 'unique';
                applyFilters();
            }
        });
        
        document.getElementById('show-duplicates').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all').checked = false;
                document.getElementById('show-unique').checked = false;
                currentDuplicateFilter = 'duplicates';
                applyFilters();
            }
        });
        
        // Filter by extraction method
        document.getElementById('show-all-extraction').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-primary').checked = false;
                document.getElementById('show-fallback').checked = false;
                document.getElementById('show-failed').checked = false;
                currentExtractionFilter = 'all';
                applyFilters();
            }
        });
        
        document.getElementById('show-primary').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-extraction').checked = false;
                document.getElementById('show-fallback').checked = false;
                document.getElementById('show-failed').checked = false;
                currentExtractionFilter = 'primary';
                applyFilters();
            }
        });
        
        document.getElementById('show-fallback').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-extraction').checked = false;
                document.getElementById('show-primary').checked = false;
                document.getElementById('show-failed').checked = false;
                currentExtractionFilter = 'fallback';
                applyFilters();
            }
        });
        
        document.getElementById('show-failed').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-extraction').checked = false;
                document.getElementById('show-primary').checked = false;
                document.getElementById('show-fallback').checked = false;
                currentExtractionFilter = 'failed';
                applyFilters();
            }
        });
        
        // Filter by frame quality
        document.getElementById('show-all-quality').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-high-quality').checked = false;
                document.getElementById('show-low-quality').checked = false;
                document.getElementById('show-poor-quality').checked = false;
                currentQualityFilter = 'all';
                applyFilters();
            }
        });
        
        document.getElementById('show-high-quality').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-quality').checked = false;
                document.getElementById('show-low-quality').checked = false;
                document.getElementById('show-poor-quality').checked = false;
                currentQualityFilter = 'high';
                applyFilters();
            }
        });
        
        document.getElementById('show-low-quality').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-quality').checked = false;
                document.getElementById('show-high-quality').checked = false;
                document.getElementById('show-poor-quality').checked = false;
                currentQualityFilter = 'low';
                applyFilters();
            }
        });
        
        document.getElementById('show-poor-quality').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('show-all-quality').checked = false;
                document.getElementById('show-high-quality').checked = false;
                document.getElementById('show-low-quality').checked = false;
                currentQualityFilter = 'poor';
                applyFilters();
            }
        });
        
        function applyFilters() {
            const allClips = document.querySelectorAll('.clip-card');
            
            allClips.forEach(clip => {
                let showByDuplicateFilter = false;
                let showByExtractionFilter = false;
                let showByQualityFilter = false;
                
                // Check duplicate filter
                if (currentDuplicateFilter === 'all') {
                    showByDuplicateFilter = true;
                } else if (currentDuplicateFilter === 'unique') {
                    showByDuplicateFilter = !clip.classList.contains('is-duplicate');
                } else if (currentDuplicateFilter === 'duplicates') {
                    showByDuplicateFilter = clip.classList.contains('is-duplicate');
                }
                
                // Check extraction filter
                if (currentExtractionFilter === 'all') {
                    showByExtractionFilter = true;
                } else {
                    const extractionMethod = clip.querySelector('[data-extraction-method]');
                    if (extractionMethod) {
                        const method = extractionMethod.getAttribute('data-extraction-method');
                        
                        if (currentExtractionFilter === 'primary') {
                            showByExtractionFilter = method === 'primary';
                        } else if (currentExtractionFilter === 'fallback') {
                            showByExtractionFilter = method.startsWith('fallback_');
                        } else if (currentExtractionFilter === 'failed') {
                            showByExtractionFilter = method === 'failed' || 
                                                    method === 'dummy' || 
                                                    method === 'emergency_dummy' ||
                                                    method === 'all_fallbacks_failed' ||
                                                    method === 'not_attempted';
                        }
                    }
                }
                
                // Check quality filter
                if (currentQualityFilter === 'all') {
                    showByQualityFilter = true;
                } else {
                    const qualityElem = clip.querySelector('[data-frame-quality]');
                    if (qualityElem) {
                        const quality = qualityElem.getAttribute('data-frame-quality');
                        showByQualityFilter = quality === currentQualityFilter;
                    }
                }
                
                // Show only if all filters match
                clip.style.display = (showByDuplicateFilter && showByExtractionFilter && showByQualityFilter) ? 'block' : 'none';
            });
        }
        
        // Timeline interactivity
        function handleClipClick(element) {
            const clipId = element.getAttribute('data-clip-id');
            
            // Highlight corresponding clip on other timeline
            document.querySelectorAll(`.timeline-clip[data-clip-id="${clipId}"], .timeline-clip-simple[data-clip-id="${clipId}"]`).forEach(item => {
                item.classList.add('highlight');
                setTimeout(() => {
                    item.classList.remove('highlight');
                }, 2000);
            });
            
            // Scroll to clip card
            const clipCard = document.querySelector(`.clip-card[data-clip-id="${clipId}"]`);
            if (clipCard) {
                clipCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                clipCard.classList.add('highlight');
                setTimeout(() => {
                    clipCard.classList.remove('highlight');
                }, 2000);
            }
        }
        
        // Add click handlers to all timeline clips
        document.querySelectorAll('.timeline-clip, .timeline-clip-simple').forEach(clip => {
            clip.addEventListener('click', function() {
                handleClipClick(this);
            });
        });
        
        // Create legend for duplicate groups
        function createDuplicateLegend() {
            const legendContainer = document.querySelector('.duplicate-legend');
            if (!legendContainer) return;
            
            // Get all unique duplicate groups
            const groupMarkers = {};
            document.querySelectorAll('.timeline-clip-marker').forEach(marker => {
                const groupId = marker.textContent;
                const color = marker.style.backgroundColor;
                if (groupId && color && !groupMarkers[groupId]) {
                    groupMarkers[groupId] = color;
                }
            });
            
            // Sort by group ID
            const sortedGroups = Object.keys(groupMarkers).sort();
            
            // Create legend items
            sortedGroups.forEach(groupId => {
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                legendItem.style.backgroundColor = groupMarkers[groupId];
                legendItem.textContent = `Group ${groupId}`;
                legendItem.setAttribute('data-group', groupId);
                legendContainer.appendChild(legendItem);
                
                // Add click handler to highlight all clips in this group
                legendItem.addEventListener('click', function() {
                    highlightGroupClips(groupId);
                });
            });
        }
        
        // Highlight all clips in a group
        function highlightGroupClips(groupId) {
            // Clear any existing highlights
            document.querySelectorAll('.highlight').forEach(el => {
                el.classList.remove('highlight');
            });
            
            // Find all clips with this group marker
            document.querySelectorAll(`.timeline-clip-marker`).forEach(marker => {
                if (marker.textContent === groupId) {
                    // Get the parent clip
                    const clip = marker.closest('.timeline-clip');
                    if (clip) {
                        const clipId = clip.getAttribute('data-clip-id');
                        
                        // Highlight this clip in both timelines
                        document.querySelectorAll(`.timeline-clip[data-clip-id="${clipId}"], .timeline-clip-simple[data-clip-id="${clipId}"]`).forEach(el => {
                            el.classList.add('highlight');
                        });
                        
                        // Also highlight the clip card
                        const clipCard = document.querySelector(`.clip-card[data-clip-id="${clipId}"]`);
                        if (clipCard) {
                            clipCard.classList.add('highlight');
                            clipCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }
            });
            
            // Keep the highlight for a longer time
            setTimeout(() => {
                document.querySelectorAll('.highlight').forEach(el => {
                    el.classList.remove('highlight');
                });
            }, 5000);
        }
        
        // Highlight all clips from same duplicate group when hovering
        document.querySelectorAll('.timeline-clip.is-duplicate, .timeline-clip-simple').forEach(clip => {
            clip.addEventListener('mouseenter', function() {
                const clipId = this.getAttribute('data-clip-id');
                const allClips = Array.from(document.querySelectorAll('.clip-card'));
                
                // Find which duplicate group this belongs to
                let duplicateGroupClips = [];
                let groupId = null;
                for (const card of allClips) {
                    if (card.classList.contains('is-duplicate') && 
                        (card.getAttribute('data-clip-id') === clipId || 
                         card.querySelector('.timeline-clip-marker')?.textContent === this.querySelector('.timeline-clip-marker')?.textContent)) {
                        duplicateGroupClips.push(card.getAttribute('data-clip-id'));
                        if (!groupId && this.querySelector('.timeline-clip-marker')) {
                            groupId = this.querySelector('.timeline-clip-marker').textContent;
                        }
                    }
                }
                
                // Highlight all clips in this group
                duplicateGroupClips.forEach(id => {
                    document.querySelectorAll(`.timeline-clip[data-clip-id="${id}"], .timeline-clip-simple[data-clip-id="${id}"]`)
                        .forEach(el => el.classList.add('hover-highlight'));
                });
                
                // Highlight the legend item if we found a group ID
                if (groupId) {
                    document.querySelector(`.legend-item[data-group="${groupId}"]`)?.classList.add('hover-highlight');
                }
            });
            
            clip.addEventListener('mouseleave', function() {
                document.querySelectorAll('.hover-highlight').forEach(el => {
                    el.classList.remove('hover-highlight');
                });
            });
        });
        // Initialize legend on page load
        document.addEventListener('DOMContentLoaded', function() {
            createDuplicateLegend();
        });
    </script>
</body>
</html>"""

        return html
    
    def _generate_clip_card_html(self, clip: Dict[str, Any], include_base64: bool = False) -> str:
        """
        Generate HTML for a single clip card.
        
        Args:
            clip: Clip data dictionary
            include_base64: If True, embed thumbnail as base64
            
        Returns:
            HTML content for the clip card
        """
        clip_id = clip.get('clip_id', 'unknown')
        material_name = clip.get('material_name', 'Unknown')
        start_time = clip.get('start_time', 0)
        duration = clip.get('duration', 0)
        end_time = start_time + duration
        track_index = clip.get('track_index', 0)
        has_thumbnail = clip.get('has_thumbnail', False)
        is_duplicate = 'is-duplicate' if clip.get('is_duplicate', False) else ''
        
        extraction_method = clip.get('extraction_method', 'unknown')
        html = f'            <div class="col-md-3 clip-card {is_duplicate}" data-clip-id="{clip_id}" data-extraction-method="{extraction_method}" data-material-path="{clip.get("material_path", "")}">\n'
        html += '                <div class="card h-100">\n'
        
        # Add thumbnail if available
        if has_thumbnail:
            thumbnail_path = clip.get('thumbnail_path', '')
            if include_base64 and os.path.exists(thumbnail_path):
                # Embed image as base64
                with open(thumbnail_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                img_format = 'jpeg' if self.output_format in ['jpg', 'jpeg'] else self.output_format
                html += f'                    <img src="data:image/{img_format};base64,{img_data}" class="card-img-top thumbnail" alt="{material_name}">\n'
            else:
                # Use relative path
                rel_path = os.path.relpath(thumbnail_path, os.path.dirname(self.output_dir))
                html += f'                    <img src="{rel_path}" class="card-img-top thumbnail" alt="{material_name}">\n'
        else:
            html += '                    <div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 180px;">\n'
            html += '                        <p class="text-muted">No thumbnail available</p>\n'
            html += '                    </div>\n'
        
        # Add clip info
        html += '                    <div class="card-body">\n'
        html += f'                        <h5 class="card-title">{material_name}</h5>\n'
        html += '                        <ul class="list-group list-group-flush">\n'
        html += f'                            <li class="list-group-item"><strong>Start:</strong> {start_time:.2f}s</li>\n'
        html += f'                            <li class="list-group-item"><strong>End:</strong> {end_time:.2f}s</li>\n'
        html += f'                            <li class="list-group-item"><strong>Duration:</strong> {duration:.2f}s</li>\n'
        html += f'                            <li class="list-group-item"><strong>Track:</strong> {track_index}</li>\n'
        
        # Add extraction method information
        extraction_method = clip.get('extraction_method', 'unknown')
        extraction_success = clip.get('extraction_success', False)
        
        if extraction_method == 'primary':
            extraction_text = 'Primary method'
            css_class = 'text-success'
        elif extraction_method.startswith('fallback_'):
            method_name = extraction_method.replace('fallback_', '')
            extraction_text = f'Fallback: {method_name}'
            css_class = 'text-warning'
        elif extraction_method in ['dummy', 'emergency_dummy']:
            extraction_text = 'Dummy image'
            css_class = 'text-danger'
        elif extraction_method in ['failed', 'all_fallbacks_failed', 'not_attempted']:
            extraction_text = extraction_method.replace('_', ' ').title()
            css_class = 'text-danger'
        else:
            extraction_text = extraction_method
            css_class = 'text-secondary'
            
        html += f'                            <li class="list-group-item {css_class}" data-extraction-method="{extraction_method}"><strong>Extraction:</strong> {extraction_text}</li>\n'
        
        # Add frame quality information
        frame_quality = clip.get('frame_quality', 'unknown')
        is_black_frame = clip.get('is_black_frame', False)
        frame_brightness = clip.get('frame_brightness', 0)
        
        if frame_quality == 'high':
            quality_css = 'text-success'
            quality_text = 'High quality'
        elif frame_quality == 'low':
            quality_css = 'text-warning'
            quality_text = f'Low quality (brightness: {frame_brightness:.1f})'
        elif frame_quality == 'poor':
            quality_css = 'text-danger'
            quality_text = f'Poor quality (brightness: {frame_brightness:.1f})'
            if is_black_frame:
                quality_text += ' - Black frame'
        else:
            quality_css = 'text-secondary'
            quality_text = 'Unknown quality'
            
        html += f'                            <li class="list-group-item {quality_css}" data-frame-quality="{frame_quality}"><strong>Quality:</strong> {quality_text}</li>\n'
            
        if is_duplicate:
            html += f'                            <li class="list-group-item text-danger"><strong>Status:</strong> Duplicate</li>\n'
        else:
            html += f'                            <li class="list-group-item text-success"><strong>Status:</strong> Unique</li>\n'
        html += '                        </ul>\n'
        html += '                    </div>\n'
        html += '                </div>\n'
        html += '            </div>\n'
        
        return html


def generate_clip_preview_dashboard(
    timeline_data: Dict[str, Any],
    output_dir: Optional[str] = None,
    dashboard_file: str = "clip_dashboard.html",
    include_base64: bool = False,
    thumbnail_width: int = 320,
    thumbnail_height: int = 180,
    similarity_threshold: float = None,  # No longer used - kept for backward compatibility
    wsl_path_prefix: Optional[str] = None,  # Kept for backward compatibility but no longer needed
    ffmpeg_path: str = "ffmpeg",
    frame_extraction_method: str = "one_third_point"  # Control which part of the clip is sampled
) -> str:
    """
    Generate a visual dashboard of video clips with thumbnails and duplicate detection.
    
    Args:
        timeline_data: Timeline data from VideoTimelineAnalyzer.analyze_timeline()
        output_dir: Directory to save dashboard and thumbnails (created if None)
        dashboard_file: Filename for the HTML dashboard
        include_base64: If True, embed thumbnails directly in HTML
        thumbnail_width: Width of thumbnails in pixels
        thumbnail_height: Height of thumbnails in pixels
        similarity_threshold: Threshold for considering clips as duplicates (0-1)
        wsl_path_prefix: Optional WSL path prefix for Windows paths (e.g., '/mnt')
                       If None, will try to auto-detect
        
    Returns:
        Path to the generated dashboard HTML file
    """
    # Auto-create output directory if not specified
    if output_dir is None:
        # Create a directory in the current working directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.getcwd(), f"clip_dashboard_{timestamp}")
        logger.info(f"Auto-created output directory: {output_dir}")
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create thumbnails directory inside the output directory
    thumbnails_dir = os.path.join(output_dir, "thumbnails")
    os.makedirs(thumbnails_dir, exist_ok=True)
    
    # If wsl_path_prefix is not provided, try to auto-detect
    if wsl_path_prefix is None and os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
        # We're in WSL, get the available mounts
        available_mounts = get_available_wsl_mounts()
        if available_mounts:
            wsl_path_prefix = available_mounts[0]
        else:
            wsl_path_prefix = '/mnt'  # Default
        logger.info(f"Auto-detected WSL path prefix: {wsl_path_prefix}")
    
    # Create generator
    generator = ClipPreviewGenerator(
        output_dir=thumbnails_dir,  # Store thumbnails in a subdirectory
        thumbnail_width=thumbnail_width,
        thumbnail_height=thumbnail_height,
        ffmpeg_path=ffmpeg_path,
        frame_extraction_method=frame_extraction_method
    )
    
    # Process clips and generate dashboard
    dashboard_path = os.path.join(output_dir, dashboard_file)
    generator.process_clips(timeline_data, wsl_path_prefix=wsl_path_prefix)
    generator.generate_dashboard(timeline_data, dashboard_path, include_base64, wsl_path_prefix=wsl_path_prefix)
    
    return dashboard_path