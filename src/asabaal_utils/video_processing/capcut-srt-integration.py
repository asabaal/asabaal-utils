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
        self.media_clips = []
        self.text_clips = []
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
        """Extract all media clips from the timeline with their timestamps."""
        # The structure may vary based on CapCut version, this is a general approach
        
        # Extract materials first (these are the source files)
        materials = {}
        if 'materials' in self.project_data:
            for material in self.project_data['materials'].get('videos', []):
                if 'id' in material and 'path' in material:
                    materials[material['id']] = {
                        'path': material['path'],
                        'name': os.path.basename(material['path']),
                        'duration': material.get('duration', 0) / 1000000  # Convert microseconds to seconds
                    }
        
        # Extract audio materials
        if 'materials' in self.project_data and 'audios' in self.project_data['materials']:
            for audio in self.project_data['materials']['audios']:
                if 'id' in audio and 'path' in audio:
                    materials[audio['id']] = {
                        'path': audio['path'],
                        'name': os.path.basename(audio['path']),
                        'duration': audio.get('duration', 0) / 1000000,
                        'type': 'audio'
                    }
        
        # Extract timeline clips
        if 'tracks' in self.project_data:
            for track_index, track in enumerate(self.project_data['tracks']):
                for segment in track.get('segments', []):
                    
                    # For video/audio clips
                    if 'material_id' in segment:
                        material_id = segment['material_id']
                        material_info = materials.get(material_id, {})
                        
                        clip = {
                            'track_index': track_index,
                            'material_id': material_id,
                            'material_path': material_info.get('path', ''),
                            'material_name': material_info.get('name', ''),
                            'start_time': segment.get('target_timerange', {}).get('start', 0) / 1000000,  # Convert to seconds
                            'duration': segment.get('target_timerange', {}).get('duration', 0) / 1000000,  # Convert to seconds
                            'type': segment.get('type', 'unknown')
                        }
                        
                        clip['end_time'] = clip['start_time'] + clip['duration']
                        self.media_clips.append(clip)
                    
                    # For text clips (captions/titles)
                    elif segment.get('type') in ['text', 'caption', 'subtitle']:
                        clip = {
                            'track_index': track_index,
                            'start_time': segment.get('target_timerange', {}).get('start', 0) / 1000000,
                            'duration': segment.get('target_timerange', {}).get('duration', 0) / 1000000,
                            'type': segment.get('type', 'text'),
                            'text': segment.get('text', {}).get('content', '')
                        }
                        
                        clip['end_time'] = clip['start_time'] + clip['duration']
                        self.text_clips.append(clip)
    
    def get_media_clips(self) -> List[Dict]:
        """Return all media clips from the timeline."""
        return self.media_clips
    
    def get_text_clips(self) -> List[Dict]:
        """Return all text clips from the timeline."""
        return self.text_clips


class LyricVideoAnalyzer:
    """
    Analyzes CapCut projects and SRT files to identify missing media clips for a lyric video.
    """
    def __init__(self, capcut_project_path: str, srt_file_path: str):
        self.capcut_parser = CapCutProjectParser(capcut_project_path)
        self.srt_parser = SRTParser(srt_file_path)
        self.media_clips = self.capcut_parser.get_media_clips()
        self.text_clips = self.capcut_parser.get_text_clips()
        self.lyrics = self.srt_parser.get_entries()
    
    def analyze_timeline(self) -> Dict:
        """
        Analyze the timeline to identify covered and missing lyric sections.
        Returns a dictionary with analysis results.
        """
        # Sort clips and lyrics by start time
        sorted_media = sorted(self.media_clips, key=lambda x: x['start_time'])
        sorted_lyrics = sorted(self.lyrics, key=lambda x: x['start_time'])
        
        covered_lyrics = []
        missing_lyrics = []
        
        # Check each lyric entry to see if it's covered by media
        for lyric in sorted_lyrics:
            covered = False
            covering_clips = []
            
            for clip in sorted_media:
                # Check if the clip covers the lyric timerange
                if (clip['start_time'] <= lyric['start_time'] and 
                    clip['end_time'] >= lyric['end_time']):
                    covered = True
                    covering_clips.append(clip)
                # Check if the clip partially covers the lyric
                elif (clip['start_time'] < lyric['end_time'] and 
                      clip['end_time'] > lyric['start_time']):
                    covering_clips.append(clip)
            
            if covered and covering_clips:
                covered_lyrics.append({
                    'lyric': lyric,
                    'covering_clips': covering_clips
                })
            else:
                missing_lyrics.append({
                    'lyric': lyric,
                    'partial_clips': covering_clips
                })
        
        # Now check for text clips that match lyrics
        matched_text_clips = []
        unmatched_text_clips = list(self.text_clips)
        
        for lyric in sorted_lyrics:
            matched = False
            
            for i, text_clip in enumerate(unmatched_text_clips):
                # Check if text content matches (approximately)
                if self._text_similarity(lyric['text'], text_clip.get('text', '')) > 0.7:
                    matched = True
                    matched_text_clips.append({
                        'lyric': lyric,
                        'text_clip': text_clip
                    })
                    unmatched_text_clips.pop(i)
                    break
        
        return {
            'covered_lyrics': covered_lyrics,
            'missing_lyrics': missing_lyrics,
            'matched_text_clips': matched_text_clips,
            'unmatched_text_clips': unmatched_text_clips,
            'total_lyrics': len(sorted_lyrics),
            'coverage_percentage': round(len(covered_lyrics) / len(sorted_lyrics) * 100, 2) if sorted_lyrics else 0
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


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze CapCut project and SRT files for lyric video creation')
    parser.add_argument('--capcut', required=True, help='Path to CapCut draft_content.json file')
    parser.add_argument('--srt', required=True, help='Path to SRT lyric file')
    parser.add_argument('--output', help='Output file for analysis report (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        analyzer = LyricVideoAnalyzer(args.capcut, args.srt)
        analysis = analyzer.analyze_timeline()
        missing_clips = analyzer.generate_missing_clips_report()
        
        report = {
            'analysis_summary': {
                'total_lyrics': analysis['total_lyrics'],
                'covered_lyrics': len(analysis['covered_lyrics']),
                'missing_lyrics': len(analysis['missing_lyrics']),
                'coverage_percentage': analysis['coverage_percentage']
            },
            'missing_clips': missing_clips
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {args.output}")
        else:
            print(json.dumps(report, indent=2))
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
