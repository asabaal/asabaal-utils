"""
Performance tests for transcript processors.

This module tests the performance characteristics of the transcript
enhancement pipeline under various loads.
"""

import unittest
import time
from asabaal_utils.video_processing.transcript_processors import (
    TranscriptEnhancementPipeline,
    FillerWordsProcessor,
    RepetitionHandler,
    SentenceBoundaryDetector,
    SemanticUnitPreserver
)


class TestPerformance(unittest.TestCase):
    """Test performance of the transcript processors."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Base transcript content with fillers and repetitions
        self.base_transcript = "um so I'm here today to tell you that I have "
        
    def test_small_transcript_performance(self):
        """Test performance with a small transcript."""
        # Generate a transcript of about 1,000 words
        transcript = self.base_transcript * 100
        
        pipeline = TranscriptEnhancementPipeline()
        
        start_time = time.time()
        processed = pipeline.process(transcript)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify processing completes within reasonable time
        # Should be very fast for small transcripts
        self.assertLess(processing_time, 1.0)  # Should process in under 1 second
        
        # Verify output size reduction
        self.assertLess(len(processed), len(transcript))
        
    def test_medium_transcript_performance(self):
        """Test performance with a medium-sized transcript."""
        # Generate a transcript of about 10,000 words
        transcript = self.base_transcript * 1000
        
        pipeline = TranscriptEnhancementPipeline()
        
        start_time = time.time()
        processed = pipeline.process(transcript)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify processing completes within reasonable time
        self.assertLess(processing_time, 5.0)  # Should process in under 5 seconds
        
        # Verify output size reduction
        self.assertLess(len(processed), len(transcript))
    
    def test_large_transcript_performance(self):
        """Test performance with a large transcript."""
        # Generate a transcript of about 50,000 words
        # This is a large transcript but should still be processed in reasonable time
        transcript = self.base_transcript * 5000
        
        pipeline = TranscriptEnhancementPipeline()
        
        start_time = time.time()
        processed = pipeline.process(transcript)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify processing completes within reasonable time
        # For larger transcripts, allow more time
        self.assertLess(processing_time, 30.0)  # Should process in under 30 seconds
        
        # Verify output size reduction
        self.assertLess(len(processed), len(transcript))
        
    def test_processor_scaling(self):
        """Test how performance scales with the number of processors."""
        # Generate a transcript of about 10,000 words
        transcript = self.base_transcript * 1000
        
        # Time with just one processor
        pipeline_one = TranscriptEnhancementPipeline(
            processors=[FillerWordsProcessor()]
        )
        
        start_time = time.time()
        pipeline_one.process(transcript)
        one_processor_time = time.time() - start_time
        
        # Time with all processors
        pipeline_all = TranscriptEnhancementPipeline()
        
        start_time = time.time()
        pipeline_all.process(transcript)
        all_processors_time = time.time() - start_time
        
        # Verify that adding more processors increases processing time, but not excessively
        # Processing time should scale roughly linearly with the number of processors
        # Allow a factor of 4x for all processors vs. one
        self.assertLess(all_processors_time, one_processor_time * 4 + 1)
        
    def test_different_processor_combinations(self):
        """Test performance with different combinations of processors."""
        # Generate a transcript of about 5,000 words
        transcript = self.base_transcript * 500
        
        processor_combinations = [
            # Just filler word processor
            [FillerWordsProcessor()],
            
            # Just repetition handler
            [RepetitionHandler()],
            
            # Filler words and repetition
            [FillerWordsProcessor(), RepetitionHandler()],
            
            # Semantic processors only
            [SentenceBoundaryDetector(), SemanticUnitPreserver()],
            
            # All processors
            [FillerWordsProcessor(), RepetitionHandler(), 
             SentenceBoundaryDetector(), SemanticUnitPreserver()]
        ]
        
        results = []
        
        for processors in processor_combinations:
            pipeline = TranscriptEnhancementPipeline(processors=processors)
            
            start_time = time.time()
            pipeline.process(transcript)
            processing_time = time.time() - start_time
            
            results.append({
                'processors': [p.__class__.__name__ for p in processors],
                'time': processing_time
            })
            
            # All combinations should complete in reasonable time
            self.assertLess(processing_time, 10.0)
        
        # Log results for informational purposes
        print("\nProcessor Combination Performance Results:")
        for result in results:
            print(f"{', '.join(result['processors'])}: {result['time']:.3f} seconds")


if __name__ == '__main__':
    unittest.main()