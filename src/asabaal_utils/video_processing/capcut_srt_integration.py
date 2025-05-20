import json
import re
import os
from datetime import timedelta
from typing import Dict, List, Tuple, Optional, Any


class SRTParser:
    """
    Parser for SRT subtitle files that extracts timestamps and text content.
    """
    def __init__(self, srt_file_path: str):
        self.srt_file_path = srt_file_path
        self.entries = []
        self._parse()
    
    def _parse(self):
        """Parse the SRT file and extract subtitle entries."""
        with open(self.srt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split the content by blank lines to get individual subtitle blocks
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            # Extract index
            index = int(lines[0])
            
            # Extract timestamps
            timestamp_line = lines[1]
            timestamp_pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})'
            match = re.match(timestamp_pattern, timestamp_line)
            
            if not match:
                continue
                
            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
            
            start_time = timedelta(hours=h1, minutes=m1, seconds=s1, milliseconds=ms1).total_seconds()
            end_time = timedelta(hours=h2, minutes=m2, seconds=s2, milliseconds=ms2).total_seconds()
            
            # Extract text (could be multiple lines)
            text = ' '.join(lines[2:])
            
            self.entries.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'text': text
            })
    
    def get_entries(self) -> List[Dict]:
        """Return all parsed subtitle entries."""
        return self.entries


class CapCutProjectParser:
    """
    Parser for CapCut draft_content.json files to extract timeline media information.
    """
    def __init__(self, project_file_path: str):
        self.project_file_path = project_file_path
        self.project_data = None
        self.video_clips = []  # Only video/image clips
        self.audio_clips = []  # Only audio clips
        self.text_clips = []   # Only text/caption clips
        self._parse()
    
    def _parse(self):
        """Parse the CapCut project file and extract timeline information."""
        with open(self.project_file_path, 'r', encoding='utf-8') as f:
            self.project_data = json.load(f)
        
        # Extract timeline information
        if not self.project_data or 'materials' not in self.project_data:
            raise ValueError("Invalid CapCut project file structure")
        
        # Find all tracks in the timeline
        self._extract_timeline_clips()
    
    def _extract_timeline_clips(self):
        """Extract all clips from the timeline with their timestamps, categorized by type."""
        # The structure may vary based on CapCut version, this is a general approach
        
        # Extract materials first (these are the source files)
        materials = {}
        if 'materials' in self.project_data:
            # Video materials
            for material in self.project_data['materials'].get('videos', []):
                if 'id' in material:
                    materials[material['id']] = {
                        'path': material.get('path', ''),
                        'name': os.path.basename(material.get('path', 'unknown')) if material.get('path') else 'video_material',
                        'duration': material.get('duration', 0) / 1000000,  # Convert microseconds to seconds
                        'type': 'video',
                        'media_type': 'video'  # Clear media type classification
                    }
            
            # Image materials
            for material in self.project_data['materials'].get('images', []):
                if 'id' in material:
                    materials[material['id']] = {
                        'path': material.get('path', ''),
                        'name': os.path.basename(material.get('path', 'unknown')) if material.get('path') else 'image_material',
                        'duration': 0,  # Images don't have duration
                        'type': 'image',
                        'media_type': 'video'  # Images count as video for timeline coverage
                    }
            
            # Audio materials
            for audio in self.project_data['materials'].get('audios', []):
                if 'id' in audio:
                    materials[audio['id']] = {
                        'path': audio.get('path', ''),
                        'name': os.path.basename(audio.get('path', 'unknown')) if audio.get('path') else 'audio_material',
                        'duration': audio.get('duration', 0) / 1000000,
                        'type': 'audio',
                        'media_type': 'audio'  # Clear media type classification
                    }
        
        # Extract timeline clips
        if 'tracks' in self.project_data:
            for track_index, track in enumerate(self.project_data['tracks']):
                for segment_index, segment in enumerate(track.get('segments', [])):
                    
                    # Common properties for all segment types
                    start_time = segment.get('target_timerange', {}).get('start', 0) / 1000000  # Convert to seconds
                    duration = segment.get('target_timerange', {}).get('duration', 0) / 1000000  # Convert to seconds
                    end_time = start_time + duration
                    
                    # For media clips with material_id
                    if 'material_id' in segment:
                        material_id = segment['material_id']
                        material_info = materials.get(material_id, {})
                        media_type = material_info.get('media_type', 'unknown')
                        
                        clip = {
                            'track_index': track_index,
                            'segment_index': segment_index,
                            'material_id': material_id,
                            'material_path': material_info.get('path', ''),
                            'material_name': material_info.get('name', ''),
                            'start_time': start_time,
                            'duration': duration,
                            'end_time': end_time,
                            'type': segment.get('type', material_info.get('type', 'unknown')),
                            'media_type': media_type
                        }
                        
                        # Categorize clips by type
                        if media_type == 'video':
                            self.video_clips.append(clip)
                        elif media_type == 'audio':
                            self.audio_clips.append(clip)
                    
                    # For text clips (captions/titles)
                    elif segment.get('type') in ['text', 'caption', 'subtitle']:
                        clip = {
                            'track_index': track_index,
                            'segment_index': segment_index,
                            'start_time': start_time,
                            'duration': duration,
                            'end_time': end_time,
                            'type': segment.get('type', 'text'),
                            'text': segment.get('text', {}).get('content', ''),
                            'media_type': 'text'
                        }
                        
                        self.text_clips.append(clip)
    
    def get_video_clips(self) -> List[Dict]:
        """Return only video/image clips from the timeline."""
        return self.video_clips
    
    def get_audio_clips(self) -> List[Dict]:
        """Return only audio clips from the timeline."""
        return self.audio_clips
    
    def get_text_clips(self) -> List[Dict]:
        """Return only text clips from the timeline."""
        return self.text_clips
        
    def get_all_clips(self) -> List[Dict]:
        """Return all clips from the timeline (video, audio, and text)."""
        return self.video_clips + self.audio_clips + self.text_clips


class VideoTimelineAnalyzer:
    """
    Analyzes CapCut projects to identify video coverage across the timeline.
    This focuses on showing which parts of the timeline are covered by video clips,
    and which parts have no video coverage.
    """
    def __init__(self, capcut_project_path: str, srt_file_path: str = None, debug: bool = False):
        self.capcut_parser = CapCutProjectParser(capcut_project_path)
        self.video_clips = self.capcut_parser.get_video_clips()  # Only consider video clips
        self.audio_clips = self.capcut_parser.get_audio_clips()
        self.text_clips = self.capcut_parser.get_text_clips()
        
        # SRT file is optional
        self.lyrics = []
        if srt_file_path:
            self.srt_parser = SRTParser(srt_file_path)
            self.lyrics = self.srt_parser.get_entries()
        
        # Also try to extract lyrics from text clips
        self._extract_lyrics_from_text_clips()
        
        self.debug = debug
        
        if self.debug:
            print(f"Loaded {len(self.video_clips)} video clips")
            print(f"Loaded {len(self.audio_clips)} audio clips")
            print(f"Loaded {len(self.text_clips)} text clips")
            print(f"Found {len(self.lyrics)} lyrics (from SRT and/or text clips)")
    
    def _extract_lyrics_from_text_clips(self):
        """Try to extract lyrics directly from text clips if no SRT file was provided."""
        if not self.lyrics and self.text_clips:
            # If we have no lyrics from SRT but have text clips, use them as lyrics
            for i, clip in enumerate(sorted(self.text_clips, key=lambda x: x['start_time'])):
                # Convert text clip to lyric format
                lyric = {
                    'index': i + 1,
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                    'duration': clip['duration'],
                    'text': clip['text'],
                    'source': 'text_clip'
                }
                self.lyrics.append(lyric)
    
    def analyze_timeline(self) -> Dict:
        """
        Analyze the timeline to identify video coverage.
        Returns a dictionary with analysis results focused on video coverage by timestamp.
        """
        # Sort clips by start time
        sorted_video = sorted(self.video_clips, key=lambda x: x['start_time'])
        sorted_audio = sorted(self.audio_clips, key=lambda x: x['start_time'])
        sorted_text = sorted(self.text_clips, key=lambda x: x['start_time'])
        sorted_lyrics = sorted(self.lyrics, key=lambda x: x['start_time']) if self.lyrics else []
        
        # Find the full timeline range
        all_start_times = []
        all_end_times = []
        
        # Add video clip times
        if sorted_video:
            all_start_times.extend([clip['start_time'] for clip in sorted_video])
            all_end_times.extend([clip['end_time'] for clip in sorted_video])
        
        # Add audio clip times
        if sorted_audio:
            all_start_times.extend([clip['start_time'] for clip in sorted_audio])
            all_end_times.extend([clip['end_time'] for clip in sorted_audio])
        
        # Add text clip times
        if sorted_text:
            all_start_times.extend([clip['start_time'] for clip in sorted_text])
            all_end_times.extend([clip['end_time'] for clip in sorted_text])
        
        # Add lyric times
        if sorted_lyrics:
            all_start_times.extend([lyric['start_time'] for lyric in sorted_lyrics])
            all_end_times.extend([lyric['end_time'] for lyric in sorted_lyrics])
        
        # Determine timeline bounds
        timeline_start = min(all_start_times) if all_start_times else 0
        timeline_end = max(all_end_times) if all_end_times else 0
        
        # Create a timeline of all objects
        timeline_objects = []
        
        # Add video clips to timeline (these are what we care about for coverage)
        for clip in sorted_video:
            timeline_objects.append({
                'type': 'video',
                'start_time': clip['start_time'],
                'end_time': clip['end_time'],
                'duration': clip['duration'],
                'object': clip
            })
        
        # Add audio clips (for reference)
        for clip in sorted_audio:
            timeline_objects.append({
                'type': 'audio',
                'start_time': clip['start_time'],
                'end_time': clip['end_time'],
                'duration': clip['duration'],
                'object': clip
            })
        
        # Add text clips (for reference)
        for clip in sorted_text:
            timeline_objects.append({
                'type': 'text',
                'start_time': clip['start_time'],
                'end_time': clip['end_time'],
                'duration': clip['duration'],
                'object': clip
            })
        
        # Add lyrics (if available)
        for lyric in sorted_lyrics:
            timeline_objects.append({
                'type': 'lyric',
                'start_time': lyric['start_time'],
                'end_time': lyric['end_time'],
                'duration': lyric['duration'],
                'object': lyric
            })
        
        # Sort all objects by start time
        timeline_objects = sorted(timeline_objects, key=lambda x: x['start_time'])
        
        # Create timeline segments by finding all unique time points
        time_points = set()
        for obj in timeline_objects:
            time_points.add(obj['start_time'])
            time_points.add(obj['end_time'])
        
        time_points = sorted(list(time_points))
        
        # Create timeline segments
        timeline_segments = []
        for i in range(len(time_points) - 1):
            start_time = time_points[i]
            end_time = time_points[i + 1]
            
            # Skip zero-duration segments
            if start_time == end_time:
                continue
                
            segment = {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'video_clips': [],
                'audio_clips': [],
                'text_clips': [],
                'lyrics': [],
                'has_video': False,
                'has_audio': False,
                'has_text': False,
                'has_lyrics': False,
                'status': 'uncovered'  # Will be updated below
            }
            
            # Find all objects that overlap with this segment
            for obj in timeline_objects:
                # Check if object overlaps with segment
                if (obj['start_time'] < end_time and obj['end_time'] > start_time):
                    if obj['type'] == 'video':
                        segment['video_clips'].append(obj['object'])
                        segment['has_video'] = True
                    elif obj['type'] == 'audio':
                        segment['audio_clips'].append(obj['object'])
                        segment['has_audio'] = True
                    elif obj['type'] == 'text':
                        segment['text_clips'].append(obj['object'])
                        segment['has_text'] = True
                    elif obj['type'] == 'lyric':
                        segment['lyrics'].append(obj['object'])
                        segment['has_lyrics'] = True
            
            # Determine segment status (focused solely on video coverage)
            if segment['has_video']:
                segment['status'] = 'covered'  # Covered by video
            else:
                segment['status'] = 'uncovered'  # No video coverage
                
            timeline_segments.append(segment)
        
        # Calculate timeline duration safely
        try:
            timeline_duration = timeline_end - timeline_start
        except TypeError:
            # Fallback if there's still an issue
            if self.debug:
                print(f"Warning: Error calculating timeline duration. Using fallback.")
                print(f"timeline_start: {timeline_start}, timeline_end: {timeline_end}")
            timeline_duration = 0
        
        # Analyze coverage
        covered_duration = sum(segment['duration'] for segment in timeline_segments if segment['has_video'])
        uncovered_duration = sum(segment['duration'] for segment in timeline_segments if not segment['has_video'])
        
        # Calculate video coverage percentage 
        try:
            video_coverage_percentage = round(covered_duration / timeline_duration * 100, 2) if timeline_duration > 0 else 0
        except (ZeroDivisionError, TypeError):
            video_coverage_percentage = 0
        
        # Group consecutive uncovered segments for easier reference
        uncovered_regions = []
        current_region = None
        
        for segment in timeline_segments:
            if segment['status'] == 'uncovered':
                if current_region is None:
                    # Start a new region
                    current_region = {
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'duration': segment['duration'],
                        'segments': [segment],
                        'lyrics': segment['lyrics'].copy() if segment['has_lyrics'] else []
                    }
                else:
                    # Extend current region
                    current_region['end_time'] = segment['end_time']
                    current_region['duration'] += segment['duration']
                    current_region['segments'].append(segment)
                    if segment['has_lyrics']:
                        current_region['lyrics'].extend(segment['lyrics'])
            else:
                # End current region if it exists
                if current_region is not None:
                    uncovered_regions.append(current_region)
                    current_region = None
        
        # Add the last region if it exists
        if current_region is not None:
            uncovered_regions.append(current_region)
        
        # Create a timeline map for quick visualization/understanding
        timeline_map = []
        map_resolution = min(100, len(timeline_segments))  # Use at most 100 segments for the map
        
        if map_resolution > 0 and timeline_segments:
            # Group segments into resolution buckets
            segment_duration = timeline_duration / map_resolution
            for i in range(map_resolution):
                start = timeline_start + i * segment_duration
                end = start + segment_duration
                
                # Find all segments that overlap with this bucket
                bucket_segments = []
                for segment in timeline_segments:
                    if segment['start_time'] < end and segment['end_time'] > start:
                        bucket_segments.append(segment)
                
                # Determine if this bucket has video coverage
                has_video = any(segment['has_video'] for segment in bucket_segments)
                
                timeline_map.append({
                    'start_time': start,
                    'end_time': end,
                    'has_video': has_video,
                    'status': 'covered' if has_video else 'uncovered'
                })
        
        return {
            'timeline_start': timeline_start,
            'timeline_end': timeline_end,
            'timeline_duration': timeline_duration,
            'timeline_segments': timeline_segments,
            'timeline_map': timeline_map,
            'uncovered_regions': uncovered_regions,
            'video_coverage_percentage': video_coverage_percentage,
            'covered_duration': covered_duration,
            'uncovered_duration': uncovered_duration,
            'video_clips': self.video_clips,
            'audio_clips': self.audio_clips,
            'text_clips': self.text_clips,
            'lyrics': self.lyrics if self.lyrics else []
        }
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity between two strings.
        Returns a score between 0 and 1.
        """
        if not text1 or not text2:
            return 0
        
        # Normalize text for comparison
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        # Simple containment check
        if t1 in t2 or t2 in t1:
            return 0.9
        
        # Count matching words
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        common_words = words1.intersection(words2)
        all_words = words1.union(words2)
        
        if not all_words:
            return 0
            
        return len(common_words) / len(all_words)
    
    def generate_missing_clips_report(self) -> List[Dict]:
        """
        Generate a report of lyrics that need clips added to the timeline.
        Returns a list of missing clips with suggested placements.
        """
        analysis = self.analyze_timeline()
        missing_lyrics = analysis['missing_lyrics']
        
        suggestions = []
        for item in missing_lyrics:
            lyric = item['lyric']
            
            suggestion = {
                'index': lyric['index'],
                'text': lyric['text'],
                'start_time': self._format_timestamp(lyric['start_time']),
                'end_time': self._format_timestamp(lyric['end_time']),
                'duration': round(lyric['duration'], 2),
                'suggested_placement': 'Add to timeline at ' + self._format_timestamp(lyric['start_time'])
            }
            
            # Check adjacent clips to suggest where this should go
            adjacent_clips = self._find_adjacent_clips(lyric['start_time'], lyric['end_time'])
            if adjacent_clips:
                suggestion['adjacent_clips'] = adjacent_clips
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to formatted timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
    
    def _find_adjacent_clips(self, start_time: float, end_time: float) -> List[Dict]:
        """Find clips that come immediately before or after the given time range."""
        before_clips = []
        after_clips = []
        
        for clip in self.media_clips:
            # Clip ends right before this lyric
            if abs(clip['end_time'] - start_time) < 1.0:  # Within 1 second
                before_clips.append({
                    'name': clip.get('material_name', 'Unknown clip'),
                    'end_time': self._format_timestamp(clip['end_time'])
                })
            
            # Clip starts right after this lyric
            if abs(clip['start_time'] - end_time) < 1.0:  # Within 1 second
                after_clips.append({
                    'name': clip.get('material_name', 'Unknown clip'),
                    'start_time': self._format_timestamp(clip['start_time'])
                })
        
        return {
            'before': before_clips,
            'after': after_clips
        }
    
    def generate_missing_lyrics_srt(self, output_path: str) -> None:
        """
        Generate an SRT file containing only the missing lyrics.
        
        Args:
            output_path: Path to the output SRT file
        """
        analysis = self.analyze_timeline()
        missing_lyrics = [item['lyric'] for item in analysis['missing_lyrics']]
        
        # Sort by start time
        missing_lyrics.sort(key=lambda x: x['start_time'])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, lyric in enumerate(missing_lyrics):
                # Convert timestamps to SRT format (HH:MM:SS,mmm)
                start_h = int(lyric['start_time'] // 3600)
                start_m = int((lyric['start_time'] % 3600) // 60)
                start_s = int(lyric['start_time'] % 60)
                start_ms = int((lyric['start_time'] % 1) * 1000)
                
                end_h = int(lyric['end_time'] // 3600)
                end_m = int((lyric['end_time'] % 3600) // 60)
                end_s = int(lyric['end_time'] % 60)
                end_ms = int((lyric['end_time'] % 1) * 1000)
                
                # Format the SRT entry
                f.write(f"{i+1}\n")
                f.write(f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> ")
                f.write(f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n")
                f.write(f"{lyric['text']}\n\n")