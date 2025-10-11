import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path

from asabaal_utils.video_processing.capcut_srt_integration import (
    SRTParser, CapCutProjectParser, VideoTimelineAnalyzer
)

class TestCapCutLyricTool(unittest.TestCase):
    """Test cases for the CapCut Lyric Tool."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample SRT file
        self.srt_content = """1
00:00:01,000 --> 00:00:05,000
This is the first lyric

2
00:00:10,000 --> 00:00:15,000
This is the second lyric

3
00:00:20,000 --> 00:00:25,000
This is the third lyric
"""
        self.srt_path = os.path.join(self.test_dir, "test.srt")
        with open(self.srt_path, "w", encoding="utf-8") as f:
            f.write(self.srt_content)
        
        # Create a sample CapCut project file
        self.capcut_content = {
            "materials": {
                "videos": [
                    {
                        "id": "video1",
                        "path": "/path/to/video1.mp4",
                        "duration": 10000000  # 10 seconds in microseconds
                    }
                ],
                "audios": [
                    {
                        "id": "audio1",
                        "path": "/path/to/audio1.mp3",
                        "duration": 30000000  # 30 seconds in microseconds
                    }
                ]
            },
            "tracks": [
                {
                    "segments": [
                        {
                            "material_id": "video1",
                            "type": "video",
                            "target_timerange": {
                                "start": 1000000,  # 1 second in microseconds
                                "duration": 4000000  # 4 seconds in microseconds
                            }
                        }
                    ]
                },
                {
                    "segments": [
                        {
                            "type": "text",
                            "text": {"content": "This is the first lyric"},
                            "target_timerange": {
                                "start": 1000000,  # 1 second in microseconds
                                "duration": 4000000  # 4 seconds in microseconds
                            }
                        }
                    ]
                }
            ]
        }
        
        self.capcut_path = os.path.join(self.test_dir, "draft_content.json")
        with open(self.capcut_path, "w", encoding="utf-8") as f:
            json.dump(self.capcut_content, f, indent=2)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_srt_parser(self):
        """Test the SRT parser functionality."""
        parser = SRTParser(self.srt_path)
        entries = parser.get_entries()
        
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["index"], 1)
        self.assertEqual(entries[0]["text"], "This is the first lyric")
        self.assertEqual(entries[0]["start_time"], 1.0)
        self.assertEqual(entries[0]["end_time"], 5.0)
    
    def test_capcut_parser(self):
        """Test the CapCut project parser functionality."""
        parser = CapCutProjectParser(self.capcut_path)
        video_clips = parser.get_video_clips()
        text_clips = parser.get_text_clips()
        
        self.assertEqual(len(video_clips), 1)
        self.assertEqual(video_clips[0]["start_time"], 1.0)
        self.assertEqual(video_clips[0]["duration"], 4.0)
        
        self.assertEqual(len(text_clips), 1)
        self.assertEqual(text_clips[0]["text"], "This is the first lyric")
    
    def test_analyzer(self):
        """Test the video timeline analyzer functionality."""
        analyzer = VideoTimelineAnalyzer(self.capcut_path, self.srt_path)
        analysis = analyzer.analyze_timeline()
        
        # Basic checks for the analysis structure
        self.assertIn("timeline_duration", analysis)
        self.assertIn("video_clips", analysis)
        self.assertIn("audio_clips", analysis)
        self.assertIn("text_clips", analysis)
        self.assertIn("lyrics", analysis)
        
        # Check video clips
        self.assertEqual(len(analysis["video_clips"]), 1)  # One video clip
        self.assertEqual(len(analysis["text_clips"]), 1)   # One text clip
        
        # Check if the missing lyrics report is generated correctly
        missing_report = analyzer.generate_missing_clips_report()
        self.assertIsInstance(missing_report, list)
        
        # Test SRT export (skip if no missing lyrics)
        missing_srt_path = os.path.join(self.test_dir, "missing.srt")
        analyzer.generate_missing_lyrics_srt(missing_srt_path)
        self.assertTrue(os.path.exists(missing_srt_path))


if __name__ == "__main__":
    unittest.main()