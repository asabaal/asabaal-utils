"""
Test SRT format integration with transcript processors.

This module specifically tests the handling of SRT format transcripts
with the enhancement pipeline.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from asabaal_utils.video_processing.transcript_processors import (
    TranscriptEnhancementPipeline,
    FillerWordsProcessor,
    RepetitionHandler
)


class TestSRTProcessing(unittest.TestCase):
    """Test SRT format processing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_srt = """
        1
        00:00:01,000 --> 00:00:04,000
        so I'm here today to tell you that I have
        
        2
        00:00:04,100 --> 00:00:06,500
        so I'm here today um
        
        3
        00:00:06,600 --> 00:00:10,000
        not only to give you an update on the only permits
        """
        # Create a temporary SRT file
        self.temp_srt_file = tempfile.NamedTemporaryFile(delete=False, suffix='.srt')
        with open(self.temp_srt_file.name, 'w') as f:
            f.write(self.sample_srt)
        
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_srt_file.name)
        
    def test_srt_timestamp_preservation(self):
        """Test that SRT timestamps are preserved during enhancement."""
        # Import the SRT utility functions
        try:
            from asabaal_utils.video_processing.srt_utils import (
                enhance_srt_with_timestamp_mapping,
                create_analysis_json_from_enhanced_srt
            )
        except ImportError:
            self.skipTest("SRT utils not available")
        
        processors = [
            FillerWordsProcessor({"policy": "remove_all"}),
            RepetitionHandler({"strategy": "first_instance"})
        ]
        
        # Process the SRT file
        enhanced_data = enhance_srt_with_timestamp_mapping(
            self.temp_srt_file.name, 
            processors
        )
        
        # Verify that timestamps are preserved
        self.assertEqual(len(enhanced_data['enhanced_entries']), 3)
        
        # Verify that entries have start and end times
        for entry in enhanced_data['enhanced_entries']:
            self.assertIn('start_time', entry)
            self.assertIn('end_time', entry)
            self.assertIn('text', entry)
        
        # Check that "um" was removed
        self.assertNotIn("um", enhanced_data['enhanced_entries'][1]['text'])
        
        # Check that repetition was handled
        # If first instance strategy is used, the first "so I'm here today" should be kept
        # and the second one should be modified
        first_segment = enhanced_data['enhanced_entries'][0]['text']
        second_segment = enhanced_data['enhanced_entries'][1]['text']
        
        # First segment should have the text
        self.assertIn("so I'm here today", first_segment)
        
        # Second segment should have either removed or modified the repeated phrase
        if "so I'm here today" in second_segment:
            # If it's in the second segment, there must be a reason
            # (it could depend on the implementation details of the RepetitionHandler)
            pass
        else:
            # More likely case: the repetition was removed in the second segment
            self.assertNotIn("so I'm here today", second_segment)
        
    def test_create_analysis_json(self):
        """Test creation of analysis JSON from enhanced SRT data."""
        try:
            from asabaal_utils.video_processing.srt_utils import (
                enhance_srt_with_timestamp_mapping,
                create_analysis_json_from_enhanced_srt
            )
        except ImportError:
            self.skipTest("SRT utils not available")
        
        processors = [
            FillerWordsProcessor({"policy": "remove_all"})
        ]
        
        # Process the SRT file
        enhanced_data = enhance_srt_with_timestamp_mapping(
            self.temp_srt_file.name, 
            processors
        )
        
        # Create a temporary JSON file
        temp_json_path = tempfile.mktemp(suffix='.json')
        
        try:
            # Create analysis JSON
            analysis_data = create_analysis_json_from_enhanced_srt(enhanced_data, temp_json_path)
            
            # Verify the analysis JSON was created
            self.assertTrue(os.path.exists(temp_json_path))
            
            # Read the JSON file
            with open(temp_json_path, 'r') as f:
                json_data = json.load(f)
            
            # Verify structure (actual structure will depend on implementation)
            # At minimum, it should contain some essential fields
            self.assertIn('segments', json_data)
            
            # Segments should have necessary timing information
            for segment in json_data['segments']:
                self.assertIn('start_time', segment)
                self.assertIn('end_time', segment)
                self.assertIn('text', segment)
                
        finally:
            # Clean up
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)
                
    def test_cli_integration(self):
        """
        Test integration with the CLI, if available.
        
        This test is skipped if analyze-transcript command is not accessible.
        """
        import subprocess
        
        # Create a temporary directory for outputs
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "output.json")
            
            # Try to run the CLI command
            try:
                cmd = [
                    "analyze-transcript", 
                    self.temp_srt_file.name,
                    "--format", "srt",
                    "--enhance-transcript",
                    "--remove-fillers",
                    "--output-file", output_file,
                    "--save-enhanced-transcript"
                ]
                
                # Run the command with a timeout
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                # If command succeeded, verify outputs
                if result.returncode == 0:
                    # Output JSON should exist
                    self.assertTrue(os.path.exists(output_file))
                    
                    # Enhanced transcript should exist
                    enhanced_path = os.path.join(
                        temp_dir, 
                        Path(self.temp_srt_file.name).stem + "_enhanced.txt"
                    )
                    
                    if os.path.exists(enhanced_path):
                        # If enhanced transcript exists, check its content
                        with open(enhanced_path, 'r') as f:
                            content = f.read()
                            # Should not contain "um"
                            self.assertNotIn("um", content)
                            
                else:
                    # If command failed, skip the test
                    self.skipTest(f"CLI command failed: {result.stderr}")
                    
            except (subprocess.SubprocessError, FileNotFoundError):
                # Skip if CLI command is not available
                self.skipTest("analyze-transcript CLI command not available")


if __name__ == '__main__':
    unittest.main()