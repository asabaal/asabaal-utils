#!/usr/bin/env python
from src.asabaal_utils.video_processing.transcript_processors import (
    FillerWordsProcessor,
    RepetitionHandler,
    SentenceBoundaryDetector,
    SemanticUnitPreserver,
    TranscriptEnhancementPipeline,
    enhance_transcript,
    extract_enhanced_clips
)

print("Transcript Enhancement System Components:")
print(f"- FillerWordsProcessor: {FillerWordsProcessor}")
print(f"- RepetitionHandler: {RepetitionHandler}")
print(f"- SentenceBoundaryDetector: {SentenceBoundaryDetector}")
print(f"- SemanticUnitPreserver: {SemanticUnitPreserver}")
print(f"- TranscriptEnhancementPipeline: {TranscriptEnhancementPipeline}")
print(f"- enhance_transcript: {enhance_transcript}")
print(f"- extract_enhanced_clips: {extract_enhanced_clips}")

# Check pipeline creation with custom processors
processors = [
    FillerWordsProcessor({"policy": "remove_all"}),
    RepetitionHandler({"strategy": "first_instance"}),
]
pipeline = TranscriptEnhancementPipeline(processors=processors)
print(f"\nPipeline created with {len(pipeline.processors)} processors")
print(f"- Processor types: {[type(p).__name__ for p in pipeline.processors]}")

# Test enhancing a simple transcript
test_transcript = "Um, I'm also here to um, I'm also here to tell you that I'm starting another project"
enhanced = enhance_transcript(test_transcript)
print(f"\nOriginal: {test_transcript}")
print(f"Enhanced: {enhanced}")

# Create a custom pipeline with just filler word handling
filler_processor = FillerWordsProcessor({"policy": "remove_all"})
custom_pipeline = TranscriptEnhancementPipeline(processors=[filler_processor])
filler_only = custom_pipeline.process(test_transcript)
print(f"Filler-only enhanced: {filler_only}")

print("\nCheck CLI function imports")
from src.asabaal_utils.video_processing.cli import extract_clips_cli
print(f"- extract_clips_cli: {extract_clips_cli.__doc__}")

# Check parameter passing in extract_clips_cli
import inspect
sig = inspect.signature(extract_enhanced_clips)
print(f"\nParameters in extract_enhanced_clips:")
for param_name, param in sig.parameters.items():
    print(f"- {param_name}: {param.default}")