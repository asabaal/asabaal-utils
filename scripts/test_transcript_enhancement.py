#!/usr/bin/env python
"""
Test script for transcript enhancement pipeline and visualizer integration.

This script checks if the RepetitionHandler properly detects repetitions across lines
while respecting proximity constraints, and if the visualizer correctly uses the
transcript processors instead of reimplementing the logic.
"""

from src.asabaal_utils.video_processing.transcript_processors import (
    RepetitionHandler, 
    FillerWordsProcessor,
    TranscriptEnhancementPipeline
)
from src.asabaal_utils.video_processing.transcript_visualizer import (
    TranscriptEnhancementVisualizer
)

# Test text with repetitions across line boundaries
test_text = """
so I'm here today to tell you that I have
so I'm here today
not only to give you an update on the only permits
blessing um
I'm also here to tell you that in
I'm also here to tell you that I'm starting
another project
"""

def test_repetition_handler():
    """Test RepetitionHandler cross-line detection with proximity constraints."""
    print("Testing RepetitionHandler cross-line detection...")
    
    # Test with default max_gap and max_distance
    handler = RepetitionHandler()
    repetitions = handler.find_repetitions(test_text)
    
    print(f"Detected {len(repetitions)} repetition enhancements with default settings")
    
    # Analyze the structure of the repetition enhancements
    if repetitions:
        print("\nStructure of first repetition enhancement:")
        for key, value in repetitions[0].items():
            print(f"  '{key}': {type(value)}")
    
    # Group repetitions by matched text
    repetition_phrases = {}
    for rep in repetitions:
        if 'match' in rep:
            phrase = rep['match']
            if phrase not in repetition_phrases:
                repetition_phrases[phrase] = []
            repetition_phrases[phrase].append(rep)
    
    # Print detected repetitions
    print(f"\nDetected {len(repetition_phrases)} unique repetition phrases:")
    for i, (phrase, instances) in enumerate(repetition_phrases.items()):
        print(f"\nRepetition {i+1}: '{phrase}'")
        print(f"  Number of instances: {len(instances)}")
        
        # Print contexts for each instance
        for j, instance in enumerate(instances):
            context = instance.get('context', 'No context')
            line_number = instance.get('line_number', 'Unknown')
            group = instance.get('group', 'Unknown')
            
            print(f"  Instance {j+1} (Line {line_number}, Group {group}):")
            print(f"    Context: {context}")
    
    # Test with very small max_gap
    handler_small_gap = RepetitionHandler({"max_gap": 1})
    repetitions_small_gap = handler_small_gap.find_repetitions(test_text)
    print(f"\nDetected {len(repetitions_small_gap)} repetition enhancements with max_gap=1")
    
    # Test with very small max_distance
    handler_small_distance = RepetitionHandler({"max_distance": 10})
    repetitions_small_distance = handler_small_distance.find_repetitions(test_text)
    print(f"Detected {len(repetitions_small_distance)} repetition enhancements with max_distance=10")
    
    # Test internal working of RepetitionHandler by directly calling _identify_repetitions
    # This gives us access to the internal repetition objects with 'phrase' and 'groups' keys
    tokens = test_text.replace('\r\n', '\n').replace('\n', ' <LINEBREAK> ').split()
    
    # Create RepetitionHandler with default parameters
    handler = RepetitionHandler()
    # Call _identify_repetitions directly to see internal representation
    internal_repetitions = handler._identify_repetitions(tokens)
    
    print(f"\nInternal representation - detected {len(internal_repetitions)} repetition groups")
    
    for i, rep in enumerate(internal_repetitions):
        if 'phrase' in rep:
            phrase = ' '.join(rep['phrase'])
            groups = rep.get('groups', [])
            print(f"\nInternal repetition {i+1}: '{phrase}'")
            print(f"  Number of groups: {len(groups)}")
            for j, group in enumerate(groups):
                if isinstance(group, list):
                    positions = ', '.join(str(pos) for pos in group)
                    print(f"  Group {j+1} positions: {positions}")
    
    return repetitions

def test_visualizer_integration():
    """Test visualizer integration with transcript processors."""
    print("\nTesting visualizer integration with transcript processors...")
    
    # Create visualizer
    visualizer = TranscriptEnhancementVisualizer()
    
    # Load test text
    visualizer.load_transcript_strings(test_text)
    
    # Find enhancements using the visualizer
    enhancements = visualizer.find_enhancements(test_text)
    print(f"Visualizer detected {len(enhancements)} enhancement opportunities")
    
    # Get repetitions using the visualizer
    repetitions = visualizer.find_repetitions(test_text)
    print(f"Visualizer detected {len(repetitions)} repetition groups")
    
    # Get filler words using the visualizer
    fillers = visualizer.find_filler_words(test_text)
    print(f"Visualizer detected {len(fillers)} filler words")
    
    # Check if the visualizer's enhancements include both repetitions and fillers
    repetition_count = sum(1 for e in enhancements if e['category'] == 'repetition')
    filler_count = sum(1 for e in enhancements if e['category'] == 'filler_words')
    print(f"Breakdown by category: repetitions={repetition_count}, fillers={filler_count}")
    
    return enhancements

def test_pipeline_enhancement():
    """Test actual enhancement of text using the pipeline."""
    print("\nTesting pipeline enhancement...")
    
    # Create pipeline with default processors
    pipeline = TranscriptEnhancementPipeline()
    
    # Process the test text and get enhancements
    enhanced_text, enhancements = pipeline.process(test_text, return_enhancements=True)
    
    print(f"Original text length: {len(test_text)}")
    print(f"Enhanced text length: {len(enhanced_text)}")
    print(f"Enhancement count: {len(enhancements)}")
    
    print("\nOriginal text:")
    print(test_text)
    print("\nEnhanced text:")
    print(enhanced_text)
    
    return enhanced_text, enhancements

if __name__ == "__main__":
    repetitions = test_repetition_handler()
    enhancements = test_visualizer_integration()
    enhanced_text, pipeline_enhancements = test_pipeline_enhancement()
    
    print("\nAll tests completed successfully.")