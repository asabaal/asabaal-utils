"""
Test suite for transcript enhancement pipeline.

This module tests the transcript enhancement functionality in the
transcript_processors module.
"""

import unittest
import os
from pathlib import Path
from asabaal_utils.video_processing.transcript_processors import (
    TranscriptEnhancementPipeline,
    FillerWordsProcessor,
    RepetitionHandler,
    SentenceBoundaryDetector,
    SemanticUnitPreserver
)


class TestFillerWordsProcessor(unittest.TestCase):
    """Test the filler words processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = FillerWordsProcessor()
        self.transcript_with_fillers = "hey everyone what's up so I'm here today to tell you that I have um I'm also here to tell you that I'm starting uh another project"
        
    def test_remove_all_policy(self):
        """Test that 'remove_all' policy removes all filler words."""
        self.processor.config = {"policy": "remove_all"}
        processed = self.processor.process(self.transcript_with_fillers)
        self.assertNotIn("um", processed)
        self.assertNotIn("uh", processed)
        
    def test_keep_all_policy(self):
        """Test that 'keep_all' policy keeps all filler words."""
        self.processor.config = {"policy": "keep_all"}
        processed = self.processor.process(self.transcript_with_fillers)
        self.assertIn("um", processed)
        self.assertIn("uh", processed)
        
    def test_context_sensitive_policy(self):
        """Test the context sensitive policy for handling filler words."""
        self.processor.config = {"policy": "context_sensitive"}
        processed = self.processor.process(self.transcript_with_fillers)
        # The context sensitive policy should still remove most fillers
        self.assertNotIn("um", processed)
        self.assertNotIn("uh", processed)
        
    def test_custom_filler_words(self):
        """Test with custom list of filler words."""
        custom_config = {
            "words": ["like", "you know"],
            "policy": "remove_all"
        }
        processor = FillerWordsProcessor(custom_config)
        transcript = "I was like really excited you know about the project"
        processed = processor.process(transcript)
        self.assertNotIn("like", processed)
        self.assertNotIn("you know", processed)
        
    def test_text_remains_coherent(self):
        """Test that text remains coherent after processing."""
        self.processor.config = {"policy": "remove_all"}
        # Check that spaces are properly handled
        processed = self.processor.process("I um have uh an idea")
        self.assertEqual("I have an idea", processed)


class TestRepetitionHandler(unittest.TestCase):
    """Test the repetition handler processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = RepetitionHandler()
        self.transcript_with_repetition = "so I'm here today to tell you that I have so I'm here today not only to give you an update on the only permits blessing um I'm also here to tell you that in I'm also here to tell you that I'm starting another project"
        
    def test_first_instance_strategy(self):
        """Test the first instance strategy for handling repetitions."""
        self.processor.config = {"strategy": "first_instance"}
        processed = self.processor.process(self.transcript_with_repetition)
        # Verify first instance of repeated phrase is kept
        self.assertIn("so I'm here today to tell you that", processed)
        # Check for reduction in duplicated phrases
        self.assertLess(processed.count("I'm also here to tell you that"), 
                      self.transcript_with_repetition.count("I'm also here to tell you that"))
        
    def test_cleanest_instance_strategy(self):
        """Test the cleanest instance strategy for handling repetitions."""
        self.processor.config = {"strategy": "cleanest_instance"}
        processed = self.processor.process(self.transcript_with_repetition)
        # Should retain one instance of the repeated phrase
        self.assertIn("I'm also here to tell you that", processed)
        # Count should be reduced
        original_count = self.transcript_with_repetition.count("I'm also here to tell you that")
        processed_count = processed.count("I'm also here to tell you that")
        self.assertLess(processed_count, original_count)
        
    def test_combine_strategy(self):
        """Test the combine strategy for handling repetitions."""
        self.processor.config = {"strategy": "combine"}
        processed = self.processor.process(self.transcript_with_repetition)
        # Should still contain key phrases but reduce repetition
        self.assertIn("I'm here today", processed)
        self.assertIn("tell you that", processed)
        # Total length should be reduced
        self.assertLess(len(processed), len(self.transcript_with_repetition))
        
    def test_min_phrase_length(self):
        """Test that minimum phrase length is respected."""
        # Set minimum phrase length to something high
        self.processor.config = {
            "strategy": "first_instance",
            "min_phrase_length": 10  # Very high to test, normal default is 3
        }
        # This text has a repetition but it's short
        text = "I have a cat I have a dog"
        processed = self.processor.process(text)
        # Short repetitions should be ignored
        self.assertEqual(text, processed)
        
    def test_max_distance(self):
        """Test that maximum distance between repetitions is respected."""
        self.processor.config = {
            "strategy": "first_instance",
            "max_distance": 5  # Very short to test, normal default is 100
        }
        # Create text with distant repetitions
        text = "I'll tell you now. " + "X " * 20 + "I'll tell you now again."
        processed = self.processor.process(text)
        # Distant repetitions should be ignored
        self.assertEqual(text, processed)


class TestSentenceBoundaryDetector(unittest.TestCase):
    """Test the sentence boundary detector processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = SentenceBoundaryDetector()
        self.transcript_with_boundaries = "this initiative is all about changing the mindset of limitation to one of abundance and possibility. I don't believe that anything is impossible that's what the Bible says that all things are possible for god right"
        
    def test_sentence_boundary_detection(self):
        """Test basic sentence boundary detection."""
        processed = self.processor.process(self.transcript_with_boundaries)
        # The processed text should include boundary markers at sentences
        # Check that there's at least one boundary marker after a period
        self.assertIn(". |", processed)
        
    def test_identify_boundaries_rules(self):
        """Test rule-based boundary detection."""
        boundaries = self.processor._identify_boundaries_rules(self.transcript_with_boundaries)
        # Should identify the obvious period as a boundary
        self.assertTrue(any(b['position'] < len(self.transcript_with_boundaries) and
                          self.transcript_with_boundaries[b['position']-1] == '.'
                          for b in boundaries))
        
    def test_calculate_boundary_confidence(self):
        """Test boundary confidence calculation."""
        # Split text into words
        words = "This is a complete sentence. This is another.".split()
        
        # Test confidence at a period
        period_pos = 4  # "sentence."
        confidence = self.processor._calculate_boundary_confidence(period_pos, words)
        # Confidence should be high for proper sentence
        self.assertGreater(confidence, 0.5)
        
        # Test at a non-boundary
        non_boundary_pos = 2  # "a"
        confidence = self.processor._calculate_boundary_confidence(non_boundary_pos, words)
        # Confidence should be low for non-boundary
        self.assertLess(confidence, 0.5)
        
    def test_respect_punctuation(self):
        """Test that punctuation is respected as sentence boundaries."""
        text = "First sentence! Second sentence? Third sentence."
        processed = self.processor.process(text)
        # Each punctuation mark should create a boundary
        self.assertIn("! |", processed)
        self.assertIn("? |", processed)
        self.assertIn(". |", processed)


class TestSemanticUnitPreserver(unittest.TestCase):
    """Test the semantic unit preserver processor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = SemanticUnitPreserver()
        self.transcript_with_units = "there are three key reasons: first, the cost is too high. second, the timeline is unrealistic. third, we lack resources."
        
    def test_semantic_unit_preservation(self):
        """Test preservation of semantic units."""
        processed = self.processor.process(self.transcript_with_units)
        # Check that the semantic units are identified (marked in the output)
        self.assertIn("first", processed)
        self.assertIn("second", processed)
        self.assertIn("third", processed)
        # The output should contain markers for semantic units
        self.assertIn("[", processed)
        self.assertIn("]", processed)
        
    def test_identify_list_patterns(self):
        """Test identification of list patterns."""
        units = self.processor._identify_list_patterns(self.transcript_with_units)
        # Should identify a list with first, second, third
        self.assertTrue(len(units) > 0)
        # The first unit should be of type "list"
        self.assertEqual(units[0]['type'], 'list')
        
    def test_question_answer_pairs(self):
        """Test identification of question-answer pairs."""
        text = "What is the most important factor? The most important factor is user experience."
        units = self.processor._identify_question_answer_pairs(text)
        # Should identify a Q&A pair
        self.assertTrue(len(units) > 0)
        # The unit should be of type "qa_pair"
        self.assertEqual(units[0]['type'], 'qa_pair')
        
    def test_explanation_sequences(self):
        """Test identification of explanation sequences."""
        text = "The problem is performance degradation. The solution is to optimize the algorithm."
        units = self.processor._identify_explanation_sequences(text)
        # Should identify an explanation sequence
        self.assertTrue(len(units) > 0)
        # The unit should be of type "explanation"
        self.assertEqual(units[0]['type'], 'explanation')
        
    def test_topic_changes(self):
        """Test detection of topic changes."""
        text = "Let's talk about performance first. Now, moving on to security concerns."
        units = self.processor._detect_topic_changes(text)
        # Should identify a topic change at "Now"
        self.assertTrue(len(units) > 0)
        # The unit should be of type "topic_change"
        self.assertEqual(units[0]['type'], 'topic_change')


class TestTranscriptEnhancementPipeline(unittest.TestCase):
    """Test the transcript enhancement pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = TranscriptEnhancementPipeline()
        self.complex_transcript = """
        hey everyone what's up
        so I'm here today to tell you that I have
        so I'm here today
        not only to give you an update on the only permits
        blessing um
        I'm also here to tell you that in
        I'm also here to tell you that I'm starting
        another project
        and this one is part of my initiative called Ask
        Seek Knock
        """
        
    def test_pipeline_with_default_processors(self):
        """Test the pipeline with default processors."""
        # Verify that default processors are correctly initialized
        self.assertGreaterEqual(len(self.pipeline.processors), 1)
        # Check processor types
        processor_types = [type(p) for p in self.pipeline.processors]
        self.assertIn(FillerWordsProcessor, processor_types)
        self.assertIn(RepetitionHandler, processor_types)
        
    def test_pipeline_with_custom_processors(self):
        """Test the pipeline with custom processors."""
        processors = [
            FillerWordsProcessor({"policy": "remove_all"}),
            RepetitionHandler({"strategy": "first_instance"})
        ]
        pipeline = TranscriptEnhancementPipeline(processors=processors)
        # Verify that custom processors are correctly set
        self.assertEqual(len(pipeline.processors), 2)
        self.assertIsInstance(pipeline.processors[0], FillerWordsProcessor)
        self.assertIsInstance(pipeline.processors[1], RepetitionHandler)
        
    def test_pipeline_processing(self):
        """Test the entire pipeline processing."""
        processed = self.pipeline.process(self.complex_transcript)
        
        # Verify filler words removed
        self.assertNotIn(" um ", processed)
        
        # Verify repetitions handled
        self.assertLess(processed.count("I'm here today"), 
                      self.complex_transcript.count("I'm here today"))
        self.assertLess(processed.count("I'm also here to tell you that"), 
                      self.complex_transcript.count("I'm also here to tell you that"))
        
        # Verify overall text improvement (shorter but maintaining meaning)
        self.assertLess(len(processed), len(self.complex_transcript))
        self.assertIn("Ask Seek Knock", processed)  # Important content preserved
        
    def test_processor_execution_order(self):
        """Test that processors are executed in the expected order."""
        # Create a special test processor class that logs execution order
        process_log = []
        
        class LoggingProcessor:
            def __init__(self, name):
                self.name = name
            
            def process(self, text):
                process_log.append(self.name)
                return text
        
        processors = [
            LoggingProcessor("processor1"),
            LoggingProcessor("processor2"),
            LoggingProcessor("processor3")
        ]
        
        pipeline = TranscriptEnhancementPipeline(processors=processors)
        pipeline.process("test text")
        
        # Verify processors executed in the expected order
        self.assertEqual(process_log, ["processor1", "processor2", "processor3"])
        
    def test_generate_report(self):
        """Test report generation during processing."""
        result, report = self.pipeline.process(self.complex_transcript, generate_report=True)
        
        # Verify report structure
        self.assertIn('processing_steps', report)
        self.assertIn('summary', report)
        
        # Verify summary contains expected metrics
        summary = report['summary']
        self.assertIn('original_length', summary)
        self.assertIn('enhanced_length', summary)
        
        # Original should be longer than enhanced
        self.assertGreater(summary['original_length'], summary['enhanced_length'])


class TestErrorHandling(unittest.TestCase):
    """Test error handling in the transcript processors."""
    
    def test_empty_transcript(self):
        """Test handling of empty transcripts."""
        pipeline = TranscriptEnhancementPipeline()
        result = pipeline.process("")
        self.assertEqual(result, "")
    
    def test_none_transcript(self):
        """Test handling of None input."""
        pipeline = TranscriptEnhancementPipeline()
        # Should handle None input gracefully, but might raise ValueError
        with self.assertRaises(Exception):
            pipeline.process(None)
    
    def test_processor_exception_handling(self):
        """Test handling of processor exceptions."""
        class BrokenProcessor:
            def process(self, text):
                raise ValueError("Simulated processing error")
        
        processors = [BrokenProcessor()]
        pipeline = TranscriptEnhancementPipeline(processors=processors)
        
        # Should propagate the exception
        with self.assertRaises(ValueError):
            pipeline.process("test text")


class TestRealWorldExamples(unittest.TestCase):
    """Test the pipeline with real-world examples from the transcript."""
    
    def test_example_1_filler_words_and_repetitions(self):
        """Test with Example 1: Filler Words and Repetitions."""
        transcript = """so I'm here today to tell you that I have
        so I'm here today
        not only to give you an update on the only permits
        blessing um
        I'm also here to tell you that in
        I'm also here to tell you that I'm starting
        another project"""
        
        pipeline = TranscriptEnhancementPipeline()
        processed = pipeline.process(transcript)
        
        # After processing, there should be fewer repetitions and no filler words
        self.assertLess(len(processed), len(transcript))
        self.assertNotIn("um", processed)
        self.assertLess(
            processed.count("I'm also here to tell you that"),
            transcript.count("I'm also here to tell you that")
        )
        
        # Important content is preserved
        self.assertIn("another project", processed)
        
    def test_example_2_sentence_structure(self):
        """Test with Example 2: Sentence Structure."""
        transcript = """this initiative is all about changing
        the mindset of limitation
        to one of abundance and possibility
        I don't believe that anything is impossible
        that's what the Bible says
        that all things are possible for god right"""
        
        pipeline = TranscriptEnhancementPipeline()
        processed = pipeline.process(transcript)
        
        # Important content should be preserved
        self.assertIn("mindset of limitation", processed)
        self.assertIn("abundance and possibility", processed)
        self.assertIn("all things are possible", processed)
        
        # Sentence boundaries should be detected
        # The SentenceBoundaryDetector would add markers
        self.assertNotEqual(processed, transcript)
        
    def test_example_3_complex_passage(self):
        """Test with Example 3: Complex Passage with Multiple Issues."""
        transcript = """and so what happened was
        when I was working on the debate
        I got stuck because my project got too big in CapCut
        it blew up to 20 gigabytes and well
        I couldn't load this project
        in my computer's memory anymore
        and I was unable to continue making progress on it
        so what was I gonna do well
        I reached out to the CapCut support team"""
        
        pipeline = TranscriptEnhancementPipeline()
        processed = pipeline.process(transcript)
        
        # Important content should be preserved
        self.assertIn("project got too big in CapCut", processed)
        self.assertIn("20 gigabytes", processed)
        self.assertIn("reached out to the CapCut support team", processed)
        
        # The enhancement should be measurable
        # Despite not having many obvious fillers, the semantic structure should be improved
        # This assertion is generic as the exact effect depends on the processor settings
        self.assertNotEqual(processed, transcript)


class TestProcessorCombinations(unittest.TestCase):
    """Test different combinations of processors."""
    
    def test_fillers_and_repetitions_only(self):
        """Test with only filler and repetition processors."""
        text = "um I think I think this is a good um good idea"
        
        processors = [
            FillerWordsProcessor(),
            RepetitionHandler()
        ]
        pipeline = TranscriptEnhancementPipeline(processors=processors)
        processed = pipeline.process(text)
        
        # Should remove "um" and handle "I think" repetition
        self.assertNotIn("um", processed)
        self.assertEqual(processed.count("I think"), 1)
        
    def test_sentence_and_semantic_only(self):
        """Test with only sentence boundary and semantic processors."""
        text = "First step is to analyze the data. Second step is to clean it. Third step is to model."
        
        processors = [
            SentenceBoundaryDetector(),
            SemanticUnitPreserver()
        ]
        pipeline = TranscriptEnhancementPipeline(processors=processors)
        processed = pipeline.process(text)
        
        # Semantic unit processor should mark the list pattern
        self.assertIn("[", processed)
        self.assertIn("]", processed)
        
        # Important content should be preserved
        self.assertIn("First step", processed)
        self.assertIn("Second step", processed)
        self.assertIn("Third step", processed)


# Entry point for running the tests
if __name__ == '__main__':
    unittest.main()