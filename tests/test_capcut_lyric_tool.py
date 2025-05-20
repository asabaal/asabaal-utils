import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path

from asabaal_utils.video_processing.capcut_srt_integration import (
    SRTParser, CapCutProjectParser, LyricVideoAnalyzer
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
        media_clips = parser.get_media_clips()
        text_clips = parser.get_text_clips()
        
        self.assertEqual(len(media_clips), 1)
        self.assertEqual(media_clips[0]["start_time"], 1.0)
        self.assertEqual(media_clips[0]["duration"], 4.0)
        
        self.assertEqual(len(text_clips), 1)
        self.assertEqual(text_clips[0]["text"], "This is the first lyric")
    
    def test_analyzer(self):
        """Test the lyric analyzer functionality."""
        analyzer = LyricVideoAnalyzer(self.capcut_path, self.srt_path)
        analysis = analyzer.analyze_timeline()
        
        self.assertEqual(analysis["total_lyrics"], 3)
        self.assertEqual(len(analysis["covered_lyrics"]), 1)  # First lyric should be covered
        self.assertEqual(len(analysis["missing_lyrics"]), 2)  # Second and third lyrics should be missing
        
        # Check if the missing lyrics report is generated correctly
        missing_report = analyzer.generate_missing_clips_report()
        self.assertEqual(len(missing_report), 2)
        self.assertEqual(missing_report[0]["text"], "This is the second lyric")
        
        # Test SRT export
        missing_srt_path = os.path.join(self.test_dir, "missing.srt")
        analyzer.generate_missing_lyrics_srt(missing_srt_path)
        self.assertTrue(os.path.exists(missing_srt_path))
        
        # Verify the missing SRT content
        with open(missing_srt_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("This is the second lyric", content)
            self.assertIn("This is the third lyric", content)


if __name__ == "__main__":
    unittest.main()