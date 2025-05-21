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
        similarity_threshold: float = 0.85,
        ffmpeg_path: str = "ffmpeg",
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
        self.similarity_threshold = similarity_threshold
        self.ffmpeg_path = ffmpeg_path
        
        # Create output directory if needed
        if output_dir is None:
            self.output_dir = tempfile.mkdtemp(prefix="clip_previews_")
            logger.info(f"Created temporary thumbnail directory: {self.output_dir}")
        else:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            logger.info(f"Saving thumbnails to: {self.output_dir}")
        
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
        
        # Use frame extractor to extract the frame
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
        Find groups of duplicate clips based on image similarity.
        
        Returns:
            List of lists, where each inner list contains indices of similar clips
        """
        n_clips = len(self.clip_features)
        if n_clips == 0:
            return []
        
        # Create a feature matrix
        feature_matrix = np.vstack(self.clip_features)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(feature_matrix)
        
        # Find duplicates (clips with similarity above threshold)
        duplicates = []
        processed = set()
        
        for i in range(n_clips):
            if i in processed:
                continue
                
            # Find clips similar to clip i
            similar_indices = [i]
            for j in range(i+1, n_clips):
                if j not in processed and similarity_matrix[i, j] >= self.similarity_threshold:
                    similar_indices.append(j)
            
            # If we found duplicates, add them to the result
            if len(similar_indices) > 1:
                duplicates.append(similar_indices)
                processed.update(similar_indices)
            else:
                processed.add(i)
        
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
        
        return {
            'clips': self.clips,
            'duplicates': self.duplicate_groups,
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
        html_content = self._generate_html_dashboard(include_base64)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard saved to {output_file}")
        return output_file
    
    def _generate_html_dashboard(self, include_base64: bool = False) -> str:
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
        body {{ padding: 20px; }}
        .clip-card {{ margin-bottom: 20px; }}
        .thumbnail {{ width: 100%; height: auto; object-fit: contain; }}
        .stats-card {{ margin-bottom: 20px; }}
        .duplicate-group {{ background-color: #f8f9fa; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .clip-card.is-duplicate {{ border: 2px solid #dc3545; }}
        .filters {{ margin-bottom: 20px; }}
        .timeline-visualization {{ margin-top: 30px; margin-bottom: 30px; overflow-x: auto; }}
        .timeline-track {{ height: 40px; position: relative; background-color: #f8f9fa; margin-bottom: 5px; }}
        .timeline-clip {{ position: absolute; height: 100%; background-color: #0d6efd; opacity: 0.7; overflow: hidden; font-size: 10px; color: white; }}
        .timeline-clip.is-duplicate {{ background-color: #dc3545; }}
        .clip-label {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px; color: white; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="mb-4">Video Clip Dashboard</h1>
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
        
        <div class="timeline-visualization">
            <h3>Timeline Visualization</h3>
"""

        # Add timeline visualization
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
                
                html += f'                <div class="timeline-clip {is_duplicate_class}" style="left: {start_percent}%; width: {width_percent}%;" title="{material_name} ({clip.get("start_time", 0):.2f}s - {clip.get("start_time", 0) + clip.get("duration", 0):.2f}s)" data-clip-id="{clip_id}">\n'
                html += f'                    <div class="clip-label">{material_name}</div>\n'
                html += f'                </div>\n'
            
            html += '            </div>\n'

        html += """
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
        document.querySelectorAll('.timeline-clip').forEach(clip => {
            clip.addEventListener('click', function() {
                const clipId = this.getAttribute('data-clip-id');
                const clipCard = document.querySelector(`.clip-card[data-clip-id="${clipId}"]`);
                if (clipCard) {
                    clipCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    clipCard.classList.add('highlight');
                    setTimeout(() => {
                        clipCard.classList.remove('highlight');
                    }, 2000);
                }
            });
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
        html = f'            <div class="col-md-3 clip-card {is_duplicate}" data-clip-id="{clip_id}" data-extraction-method="{extraction_method}">\n'
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
    similarity_threshold: float = 0.85,
    wsl_path_prefix: Optional[str] = None,  # Kept for backward compatibility but no longer needed
    ffmpeg_path: str = "ffmpeg"
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
        similarity_threshold=similarity_threshold,
        ffmpeg_path=ffmpeg_path
    )
    
    # Process clips and generate dashboard
    dashboard_path = os.path.join(output_dir, dashboard_file)
    generator.process_clips(timeline_data, wsl_path_prefix=wsl_path_prefix)
    generator.generate_dashboard(timeline_data, dashboard_path, include_base64, wsl_path_prefix=wsl_path_prefix)
    
    return dashboard_path