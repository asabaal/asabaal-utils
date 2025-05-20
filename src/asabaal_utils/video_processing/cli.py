"""
Command-line interface for video processing utilities.

This module provides a CLI for the video processing utilities.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from .clip_extractor import extract_clips_from_json
from .silence_detector import remove_silence
from .transcript_analyzer import analyze_transcript
from .thumbnail_generator import generate_thumbnails
from .color_analyzer import analyze_video_colors
from .jump_cut_detector import detect_jump_cuts, smooth_jump_cuts
from .video_summarizer import create_video_summary, SummaryStyle
from .capcut_srt_integration import VideoTimelineAnalyzer
from .timeline_visualizer import visualize_video_coverage, generate_uncovered_regions_report, generate_clip_details_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def remove_silence_cli():
    """CLI entry point for silence removal."""
    parser = argparse.ArgumentParser(description="Remove silence from video files")
    parser.add_argument("input_file", help="Path to input video file")
    parser.add_argument("output_file", help="Path to output video file")
    parser.add_argument("--threshold-db", type=float, default=-40.0,
                        help="Threshold in dB below which audio is considered silence (default: -40.0)")
    parser.add_argument("--min-silence", type=float, default=0.5,
                        help="Minimum duration of silence to remove in seconds (default: 0.5)")
    parser.add_argument("--min-sound", type=float, default=0.3,
                        help="Minimum duration of sound to keep in seconds (default: 0.3)")
    parser.add_argument("--padding", type=float, default=0.1,
                        help="Padding around non-silent segments in seconds (default: 0.1)")
    parser.add_argument("--chunk-size", type=float, default=0.05,
                        help="Size of audio chunks for analysis in seconds (default: 0.05)")
    parser.add_argument("--aggressive", action="store_true",
                        help="Use aggressive silence rejection algorithms")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    # Memory management options
    memory_group = parser.add_argument_group('Memory Management Options')
    memory_group.add_argument("--strategy", 
                        choices=["auto", "full_quality", "reduced_resolution", "chunked", "segment", "streaming"],
                        default="auto",
                        help="Processing strategy to use (default: auto)")
    memory_group.add_argument("--segment-count", type=int, default=None,
                        help="Number of segments to split video into when using segment strategy")
    memory_group.add_argument("--chunk-duration", type=float, default=None,
                        help="Duration of each chunk in seconds when using chunked strategy")
    memory_group.add_argument("--resolution-scale", type=float, default=None,
                        help="Scale factor for resolution when using reduced_resolution strategy (0.25-0.75)")
    memory_group.add_argument("--disable-memory-adaptation", action="store_true",
                        help="Disable memory-adaptive processing entirely")
    memory_group.add_argument("--disable-ffmpeg", action="store_true",
                        help="Disable direct FFmpeg implementation and use MoviePy instead")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Determine whether to use memory adaptation
        use_memory_adaptation = not args.disable_memory_adaptation
        
        # Determine whether to use FFmpeg implementation
        use_ffmpeg = not args.disable_ffmpeg

        # Prepare memory management options
        memory_options = {}
        if args.strategy != "auto":
            memory_options["strategy"] = args.strategy
        if args.segment_count is not None:
            memory_options["segment_count"] = args.segment_count
        if args.chunk_duration is not None:
            memory_options["chunk_duration"] = args.chunk_duration
        if args.resolution_scale is not None:
            memory_options["resolution_scale"] = args.resolution_scale
        
        result = remove_silence(
            input_file=args.input_file,
            output_file=args.output_file,
            threshold_db=args.threshold_db,
            min_silence_duration=args.min_silence,
            min_sound_duration=args.min_sound,
            padding=args.padding,
            chunk_size=args.chunk_size,
            aggressive_silence_rejection=args.aggressive,
            use_memory_adaptation=use_memory_adaptation,
            use_ffmpeg=use_ffmpeg,
            **memory_options,
        )
        
        # Handle both direct return values and dictionary result from memory adaptation
        if isinstance(result, tuple) and len(result) == 3:
            # Direct implementation return value
            original_duration, output_duration, time_saved = result
            print(f"\nSilence removal complete:")
            print(f"- Original duration: {original_duration:.2f}s")
            print(f"- Output duration: {output_duration:.2f}s")
            print(f"- Time saved: {time_saved:.2f}s ({100 * time_saved / original_duration:.1f}%)")
            print(f"- Output file: {os.path.abspath(args.output_file)}")
        elif isinstance(result, dict):
            # Memory adaptation result
            if result.get("status") == "success":
                print(f"\nSilence removal complete (using {result.get('processing_mode', 'adaptive')} mode):")
                inner_result = result.get("result")
                if isinstance(inner_result, tuple) and len(inner_result) == 3:
                    original_duration, output_duration, time_saved = inner_result
                    print(f"- Original duration: {original_duration:.2f}s")
                    print(f"- Output duration: {output_duration:.2f}s")
                    print(f"- Time saved: {time_saved:.2f}s ({100 * time_saved / original_duration:.1f}%)")
                print(f"- Output file: {os.path.abspath(args.output_file)}")
            else:
                # Processing failed
                logger.error(f"Processing failed: {result.get('message', 'Unknown error')}")
                return 1
        else:
            # Unexpected return value
            logger.error(f"Unexpected result from silence removal: {result}")
            return 1
        
        return 0
    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        return 1


def analyze_transcript_cli():
    """CLI entry point for transcript analysis."""
    parser = argparse.ArgumentParser(description="Analyze video transcripts for optimal clip splits")
    parser.add_argument("transcript_file", help="Path to transcript file")
    parser.add_argument("--output-file", help="Path to output JSON file with suggestions")
    parser.add_argument("--format", default="capcut", choices=["capcut", "json", "srt"],
                        help="Format of the transcript file (default: capcut)")
    parser.add_argument("--min-clip-duration", type=float, default=10.0,
                        help="Minimum clip duration in seconds (default: 10.0)")
    parser.add_argument("--max-clip-duration", type=float, default=60.0,
                        help="Maximum clip duration in seconds (default: 60.0)")
    parser.add_argument("--topic-change-threshold", type=float, default=0.3,
                        help="Topic change detection threshold (default: 0.3)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    # Add transcript enhancement options
    enhancement_group = parser.add_argument_group('Transcript Enhancement Options')
    enhancement_group.add_argument("--enhance-transcript", action="store_true",
                    help="Apply transcript enhancement before analysis")
    enhancement_group.add_argument("--remove-fillers", action="store_true",
                    help="Remove filler words like 'um', 'uh', etc.")
    enhancement_group.add_argument("--handle-repetitions", action="store_true",
                    help="Remove or consolidate repeated phrases")
    enhancement_group.add_argument("--respect-sentences", action="store_true",
                    help="Optimize clip boundaries to respect sentence boundaries")
    enhancement_group.add_argument("--preserve-semantic-units", action="store_true",
                    help="Preserve semantic units like explanations and lists")
    enhancement_group.add_argument("--filler-policy", 
                    choices=["remove_all", "keep_all", "context_sensitive"],
                    default="remove_all", help="Policy for handling filler words")
    enhancement_group.add_argument("--repetition-strategy", 
                    choices=["first_instance", "cleanest_instance", "combine"],
                    default="first_instance", help="Strategy for handling repetitions")
    # Add option to save enhanced transcript
    enhancement_group.add_argument("--save-enhanced-transcript", action="store_true",
                    help="Save the enhanced transcript as a plain text file")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # If no output file is specified, create one based on the input file
        if not args.output_file:
            input_path = Path(args.transcript_file)
            output_path = input_path.with_suffix('.clips.json')
            args.output_file = str(output_path)
        
        # Configure processors for enhancement if requested
        if args.enhance_transcript:
            from .transcript_processors import TranscriptEnhancementPipeline, FillerWordsProcessor, RepetitionHandler, SentenceBoundaryDetector, SemanticUnitPreserver
            
            # Configure which processors to use
            processors = []
            if args.remove_fillers:
                processors.append(FillerWordsProcessor({
                    "policy": args.filler_policy
                }))
            
            if args.handle_repetitions:
                processors.append(RepetitionHandler({
                    "strategy": args.repetition_strategy
                }))
            
            if args.respect_sentences:
                processors.append(SentenceBoundaryDetector())
            
            if args.preserve_semantic_units:
                processors.append(SemanticUnitPreserver())
            
            # If no specific processors were selected but enhancement is on,
            # use all processors with default settings
            if not processors and args.enhance_transcript:
                pipeline = TranscriptEnhancementPipeline()
                processors = None
            
            # Special handling for SRT format
            if args.format.lower() == "srt":
                # For SRT format, use specialized timestamp-aware enhancement
                from .srt_utils import enhance_srt_with_timestamp_mapping, create_analysis_json_from_enhanced_srt
                import tempfile
                
                # Use our specialized SRT enhancement function that preserves timestamp mappings
                enhanced_data = enhance_srt_with_timestamp_mapping(
                    args.transcript_file, 
                    processors
                )
                
                # Create a temporary JSON file for analysis that preserves the timestamp mappings
                temp_json_path = tempfile.mktemp(suffix='.json')
                analysis_data = create_analysis_json_from_enhanced_srt(enhanced_data, temp_json_path)
                
                print(f"Applied timestamp-aware enhancement to {len(enhanced_data['enhanced_entries'])} SRT entries")
                transcript_file_to_analyze = temp_json_path
                
                # Override format to tell the analyzer this is a special JSON format
                transcript_format = "enhanced_srt_json"
                
                # Save enhanced transcript as plain text if requested
                if args.save_enhanced_transcript:
                    # Determine path for enhanced transcript
                    output_dir = Path(args.output_file).parent
                    enhanced_transcript_filename = Path(args.transcript_file).stem + "_enhanced.txt"
                    enhanced_transcript_path = str(output_dir / enhanced_transcript_filename)
                    
                    # Extract plain text from the enhanced SRT data
                    enhanced_text = ""
                    for entry in enhanced_data['enhanced_entries']:
                        enhanced_text += entry['text'] + " "
                    
                    # Save the enhanced text
                    with open(enhanced_transcript_path, 'w', encoding='utf-8') as f:
                        f.write(enhanced_text)
                    
                    print(f"Saved enhanced transcript text to: {enhanced_transcript_path}")
            else:
                # For other formats, use standard enhancement
                pipeline = TranscriptEnhancementPipeline(processors=processors)
                
                # Read the transcript
                with open(args.transcript_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                
                # Process the transcript
                enhanced_transcript = pipeline.process(transcript_content)
                
                # Save enhanced transcript as plain text if requested
                if args.save_enhanced_transcript:
                    # Determine path for enhanced transcript
                    output_dir = Path(args.output_file).parent
                    # Always use .txt extension
                    enhanced_transcript_filename = Path(args.transcript_file).stem + "_enhanced.txt"
                    enhanced_transcript_path = str(output_dir / enhanced_transcript_filename)
                    
                    # Save the enhanced transcript as plain text
                    with open(enhanced_transcript_path, 'w', encoding='utf-8') as f:
                        # For JSON format inputs, we need to extract the plain text
                        if args.format.lower() == "json" or args.format.lower() == "capcut":
                            import json
                            try:
                                # Try to parse as JSON
                                json_data = json.loads(enhanced_transcript)
                                # Extract text from the structure based on common patterns
                                plain_text = ""
                                if isinstance(json_data, list):
                                    for item in json_data:
                                        if isinstance(item, dict) and 'text' in item:
                                            plain_text += item['text'] + " "
                                elif isinstance(json_data, dict):
                                    # Try to find text fields
                                    if 'text' in json_data:
                                        plain_text = json_data['text']
                                    elif 'segments' in json_data and isinstance(json_data['segments'], list):
                                        for segment in json_data['segments']:
                                            if isinstance(segment, dict) and 'text' in segment:
                                                plain_text += segment['text'] + " "
                                
                                # If we successfully extracted text, use it
                                if plain_text:
                                    f.write(plain_text)
                                else:
                                    # If we couldn't extract text, fall back to the full enhanced transcript
                                    f.write(enhanced_transcript)
                            except json.JSONDecodeError:
                                # If not valid JSON, just write it as is
                                f.write(enhanced_transcript)
                        else:
                            # For TXT and other formats, write as is
                            f.write(enhanced_transcript)
                    
                    print(f"Saved enhanced transcript text to: {enhanced_transcript_path}")
                
                # Create a temporary file with the correct extension for the format
                suffix_map = {"capcut": ".json", "json": ".json", "txt": ".txt"}
                suffix = suffix_map.get(args.format, ".txt")
                
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix, encoding='utf-8') as f:
                    f.write(enhanced_transcript)
                    enhanced_transcript_path = f.name
                
                transcript_file_to_analyze = enhanced_transcript_path
                transcript_format = args.format
                print(f"Applied transcript enhancement before analysis")
        else:
            # No enhancement, use original file and format
            transcript_file_to_analyze = args.transcript_file
            transcript_format = args.format
        
        # Perform the transcript analysis
        suggestions = analyze_transcript(
            transcript_file=transcript_file_to_analyze,
            output_file=args.output_file,
            transcript_format=transcript_format,
            min_clip_duration=args.min_clip_duration,
            max_clip_duration=args.max_clip_duration,
            topic_change_threshold=args.topic_change_threshold,
        )
        
        # Clean up temporary file if created
        if args.enhance_transcript and 'transcript_file_to_analyze' in locals() and transcript_file_to_analyze != args.transcript_file:
            import os
            try:
                os.unlink(transcript_file_to_analyze)
            except:
                pass
        
        print(f"\nTranscript analysis complete:")
        print(f"- Found {len(suggestions)} suggested clips")
        print(f"- Suggestions saved to: {os.path.abspath(args.output_file)}")
        
        # Print a summary of the suggestions
        for i, suggestion in enumerate(suggestions):
            start_min = int(suggestion['start_time'] // 60)
            start_sec = int(suggestion['start_time'] % 60)
            end_min = int(suggestion['end_time'] // 60)
            end_sec = int(suggestion['end_time'] % 60)
            
            print(f"\nClip {i+1}: {suggestion['topic']}")
            print(f"- Time: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                  f"({suggestion['duration']:.1f}s)")
            
            # Print a short excerpt of the text
            text = suggestion['text']
            if len(text) > 100:
                text = text[:97] + "..."
            print(f"- Text: {text}")
        
        return 0
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}", exc_info=True)
        return 1

def generate_thumbnails_cli():
    """CLI entry point for thumbnail generation."""
    parser = argparse.ArgumentParser(description="Generate thumbnail candidates from video files")
    parser.add_argument("video_file", help="Path to input video file")
    parser.add_argument("--output-dir", help="Directory to save thumbnail images (default: creates a temp dir)")
    parser.add_argument("--count", type=int, default=10,
                        help="Number of thumbnail candidates to generate (default: 10)")
    parser.add_argument("--min-interval", type=float, default=1.0,
                        help="Minimum interval between thumbnails in seconds (default: 1.0)")
    parser.add_argument("--skip-start", type=float, default=0.05,
                        help="Percentage of video to skip from start (default: 0.05, i.e., 5%%)")
    parser.add_argument("--skip-end", type=float, default=0.05,
                        help="Percentage of video to skip from end (default: 0.05, i.e., 5%%)")
    parser.add_argument("--format", default="jpg", choices=["jpg", "png"],
                        help="Output image format (default: jpg)")
    parser.add_argument("--quality", type=int, default=90,
                        help="JPEG quality (1-100, default: 90)")
    parser.add_argument("--metadata-file", 
                        help="Path to save thumbnail metadata as JSON (default: <output_dir>/thumbnails.json)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Create default output directory based on video file name if not specified
        if not args.output_dir:
            video_path = Path(args.video_file)
            args.output_dir = str(video_path.with_suffix('_thumbnails'))
        
        # Create default metadata file if not specified
        if not args.metadata_file:
            metadata_path = os.path.join(args.output_dir, "thumbnails.json")
            args.metadata_file = metadata_path
        
        # Generate thumbnails
        thumbnails = generate_thumbnails(
            video_path=args.video_file,
            output_dir=args.output_dir,
            frames_to_extract=args.count,
            min_frame_interval=args.min_interval,
            skip_start_percent=args.skip_start,
            skip_end_percent=args.skip_end,
            output_format=args.format,
            output_quality=args.quality,
            metadata_file=args.metadata_file
        )
        
        print(f"\nThumbnail generation complete:")
        print(f"- Generated {len(thumbnails)} thumbnail candidates")
        print(f"- Saved to: {os.path.abspath(args.output_dir)}")
        print(f"- Metadata: {os.path.abspath(args.metadata_file)}")
        
        # Print thumbnail information
        print("\nThumbnail candidates (sorted by quality):")
        sorted_thumbnails = sorted(thumbnails, key=lambda x: x['quality_score'], reverse=True)
        
        for i, thumb in enumerate(sorted_thumbnails):
            print(f"\n{i+1}. {os.path.basename(thumb['frame_path'])}")
            print(f"   Time: {thumb['timestamp_str']} - "
                  f"Quality: {thumb['quality_score']:.3f}")
            print(f"   Brightness: {thumb['metrics']['brightness']:.2f}, "
                  f"Contrast: {thumb['metrics']['contrast']:.2f}, "
                  f"Colorfulness: {thumb['metrics']['colorfulness']:.2f}")
        
        return 0
    except Exception as e:
        logger.error(f"Error generating thumbnails: {e}", exc_info=True)
        return 1


def analyze_colors_cli():
    """CLI entry point for video color analysis."""
    parser = argparse.ArgumentParser(description="Analyze color themes and palettes in videos")
    parser.add_argument("video_file", help="Path to input video file")
    parser.add_argument("--output-dir", help="Directory to save color analysis outputs (default: creates a temp dir)")
    parser.add_argument("--palette-size", type=int, default=5,
                        help="Number of colors to extract for the palette (default: 5)")
    parser.add_argument("--sample-rate", type=float, default=1.0,
                        help="Frames per second to sample (default: 1.0)")
    parser.add_argument("--segment-duration", type=float, default=10.0,
                        help="Duration of each segment in seconds (default: 10.0)")
    parser.add_argument("--skip-start", type=float, default=0.05,
                        help="Percentage of video to skip from start (default: 0.05, i.e., 5%%)")
    parser.add_argument("--skip-end", type=float, default=0.05,
                        help="Percentage of video to skip from end (default: 0.05, i.e., 5%%)")
    parser.add_argument("--no-palette-image", action="store_true",
                        help="Skip creation of palette image")
    parser.add_argument("--no-segments", action="store_true",
                        help="Skip segment-by-segment analysis")
    parser.add_argument("--segment-images", action="store_true",
                        help="Create palette images for each segment")
    parser.add_argument("--metadata-file", 
                        help="Path to save color analysis as JSON (default: <output_dir>/color_analysis.json)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Create default output directory based on video file name if not specified
        if not args.output_dir:
            video_path = Path(args.video_file)
            args.output_dir = str(video_path.with_suffix('_colors'))
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Create default metadata file if not specified
        if not args.metadata_file:
            metadata_path = os.path.join(args.output_dir, "color_analysis.json")
            args.metadata_file = metadata_path
        
        # Analyze colors
        results = analyze_video_colors(
            video_path=args.video_file,
            output_dir=args.output_dir,
            palette_size=args.palette_size,
            frame_sample_rate=args.sample_rate,
            segment_duration=args.segment_duration,
            create_palette_image=not args.no_palette_image,
            create_segments=not args.no_segments,
            segment_palette_images=args.segment_images,
            metadata_file=args.metadata_file
        )
        
        theme = results["theme"]
        segments = results.get("segments", [])
        
        print(f"\nVideo color analysis complete:")
        print(f"- Analyzed: {os.path.basename(args.video_file)}")
        print(f"- Color theme type: {theme['theme_type']}")
        print(f"- Dominant colors: {', '.join(theme['color_names'])}")
        print(f"- Emotional associations: {', '.join(theme['emotions'])}")
        print(f"- Results saved to: {os.path.abspath(args.output_dir)}")
        
        if theme["color_palette_path"]:
            print(f"- Color palette image: {os.path.abspath(theme['color_palette_path'])}")
        
        print(f"- Metadata: {os.path.abspath(args.metadata_file)}")
        
        # Print color information
        print("\nDominant colors:")
        for i, (name, hex_code, pct) in enumerate(zip(
            theme["color_names"], 
            theme["color_hex"], 
            theme["color_percentages"]
        )):
            print(f"  {i+1}. {name} ({hex_code}) - {pct*100:.1f}%")
        
        if segments:
            print(f"\nSegment analysis: {len(segments)} segments")
            print(f"  Use --no-segments to skip segment analysis")
            print(f"  See the metadata JSON for detailed segment information")
        
        return 0
    except Exception as e:
        logger.error(f"Error analyzing video colors: {e}", exc_info=True)
        return 1


def detect_jump_cuts_cli():
    """CLI entry point for jump cut detection."""
    parser = argparse.ArgumentParser(description="Detect jump cuts in videos")
    parser.add_argument("video_file", help="Path to input video file")
    parser.add_argument("--output-dir", help="Directory to save detection outputs (default: creates a temp dir)")
    parser.add_argument("--sensitivity", type=float, default=0.5,
                        help="Detection sensitivity (0.0-1.0, default: 0.5)")
    parser.add_argument("--min-interval", type=float, default=0.5,
                        help="Minimum interval between detected cuts in seconds (default: 0.5)")
    parser.add_argument("--sample-rate", type=float, default=10.0,
                        help="Frames per second to analyze (default: 10.0)")
    parser.add_argument("--skip-start", type=float, default=0.0,
                        help="Percentage of video to skip from start (default: 0.0)")
    parser.add_argument("--skip-end", type=float, default=0.0,
                        help="Percentage of video to skip from end (default: 0.0)")
    parser.add_argument("--no-save-frames", action="store_true",
                        help="Skip saving frames before and after jump cuts")
    parser.add_argument("--metadata-file", 
                        help="Path to save jump cut metadata as JSON (default: <output_dir>/jump_cuts.json)")
    parser.add_argument("--smooth-output", 
                        help="Path to save a new video with smoothed transitions (optional)")
    parser.add_argument("--high-confidence-only", action="store_true",
                        help="Apply transitions only to high-confidence jump cuts")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Create default output directory based on video file name if not specified
        if not args.output_dir:
            video_path = Path(args.video_file)
            args.output_dir = str(video_path.with_suffix('_jump_cuts'))
        
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Create default metadata file if not specified
        if not args.metadata_file:
            metadata_path = os.path.join(args.output_dir, "jump_cuts.json")
            args.metadata_file = metadata_path
        
        # Detect jump cuts
        jump_cuts = detect_jump_cuts(
            video_path=args.video_file,
            output_dir=args.output_dir,
            sensitivity=args.sensitivity,
            min_jump_interval=args.min_interval,
            frame_sample_rate=args.sample_rate,
            save_frames=not args.no_save_frames,
            metadata_file=args.metadata_file
        )
        
        print(f"\nJump cut detection complete:")
        print(f"- Analyzed: {os.path.basename(args.video_file)}")
        print(f"- Found {len(jump_cuts)} jump cuts")
        print(f"- Results saved to: {os.path.abspath(args.output_dir)}")
        print(f"- Metadata: {os.path.abspath(args.metadata_file)}")
        
        # Print jump cut information
        if jump_cuts:
            print("\nDetected jump cuts:")
            # Sort by confidence
            sorted_cuts = sorted(jump_cuts, key=lambda x: x['confidence'], reverse=True)
            
            for i, cut in enumerate(sorted_cuts):
                print(f"\n{i+1}. At {cut['timestamp_str']} - "
                      f"Confidence: {cut['confidence']:.2f}")
                print(f"   Suggested transition: {cut['suggested_transition']} ({cut['transition_duration']:.1f}s)")
                
                if not args.no_save_frames and cut['frame_before'] and cut['frame_after']:
                    print(f"   Frames: {os.path.basename(cut['frame_before'])} → "
                          f"{os.path.basename(cut['frame_after'])}")
        
        # Apply smoothing if requested
        if args.smooth_output:
            print(f"\nApplying transitions to create smoothed video...")
            
            smooth_jump_cuts(
                video_path=args.video_file,
                output_path=args.smooth_output,
                jump_cuts_data=jump_cuts,
                apply_all_transitions=not args.high_confidence_only
            )
            
            print(f"- Smoothed video saved to: {os.path.abspath(args.smooth_output)}")
        
        return 0
    except Exception as e:
        logger.error(f"Error detecting jump cuts: {e}", exc_info=True)
        return 1


def create_summary_cli():
    """CLI entry point for content-aware video summarization."""
    parser = argparse.ArgumentParser(description="Create content-aware video summaries")
    parser.add_argument("video_file", help="Path to input video file")
    parser.add_argument("output_file", help="Path to output summary video file")
    parser.add_argument("--target-duration", type=float, default=60.0,
                       help="Target duration in seconds for the summary (default: 60.0)")
    parser.add_argument("--style", default="overview", 
                        choices=[s.value for s in SummaryStyle],
                        help="Style of summary to create (default: overview)")
    parser.add_argument("--segment-length", type=float, default=3.0,
                       help="Base length of segments to consider in seconds (default: 3.0)")
    parser.add_argument("--skip-start", type=float, default=0.05,
                        help="Percentage of video to skip from start (default: 0.05, i.e., 5%%)")
    parser.add_argument("--skip-end", type=float, default=0.05,
                        help="Percentage of video to skip from end (default: 0.05, i.e., 5%%)")
    parser.add_argument("--no-favor-beginning", action="store_true",
                        help="Don't give preference to content from the beginning of the video")
    parser.add_argument("--no-favor-ending", action="store_true",
                        help="Don't give preference to content from the end of the video")
    parser.add_argument("--metadata-file", 
                        help="Path to save summary metadata as JSON (default: <output_dir>/summary.json)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    # Memory management options
    memory_group = parser.add_argument_group('Memory Management Options')
    memory_group.add_argument("--strategy", 
                        choices=["auto", "full_quality", "reduced_resolution", "chunked", "segment", "streaming"],
                        default="auto",
                        help="Processing strategy to use (default: auto)")
    memory_group.add_argument("--segment-count", type=int, default=None,
                        help="Number of segments to split video into when using segment strategy")
    memory_group.add_argument("--chunk-duration", type=float, default=None,
                        help="Duration of each chunk in seconds when using chunked strategy")
    memory_group.add_argument("--resolution-scale", type=float, default=None,
                        help="Scale factor for resolution when using reduced_resolution strategy (0.25-0.75)")
    memory_group.add_argument("--disable-memory-adaptation", action="store_true",
                        help="Disable memory-adaptive processing entirely")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Create output directory if it doesn't exist
        output_path = Path(args.output_file)
        output_dir = output_path.parent
        os.makedirs(output_dir, exist_ok=True)
        
        # Create default metadata file if not specified
        if not args.metadata_file:
            metadata_file = output_path.with_suffix('.json')
            args.metadata_file = str(metadata_file)
        
        # Determine whether to use memory adaptation
        use_memory_adaptation = not args.disable_memory_adaptation

        # Prepare memory management options
        memory_options = {}
        if args.strategy != "auto":
            memory_options["strategy"] = args.strategy
        if args.segment_count is not None:
            memory_options["segment_count"] = args.segment_count
        if args.chunk_duration is not None:
            memory_options["chunk_duration"] = args.chunk_duration
        if args.resolution_scale is not None:
            memory_options["resolution_scale"] = args.resolution_scale
            
        # Create video summary
        segments = create_video_summary(
            video_path=args.video_file,
            output_path=args.output_file,
            target_duration=args.target_duration,
            summary_style=args.style,
            segment_length=args.segment_length,
            favor_beginning=not args.no_favor_beginning,
            favor_ending=not args.no_favor_ending,
            metadata_file=args.metadata_file,
            use_memory_adaptation=use_memory_adaptation,
            **memory_options
        )
        
        print(f"\nVideo summarization complete:")
        print(f"- Analyzed: {os.path.basename(args.video_file)}")
        print(f"- Created summary with {len(segments)} segments")
        print(f"- Summary style: {args.style}")
        print(f"- Target duration: {args.target_duration:.1f}s")
        print(f"- Actual duration: {sum(s['duration'] for s in segments):.1f}s")
        print(f"- Summary saved to: {os.path.abspath(args.output_file)}")
        print(f"- Metadata: {os.path.abspath(args.metadata_file)}")
        
        # Print segments
        print("\nIncluded segments:")
        for i, segment in enumerate(segments):
            print(f"\n{i+1}. {segment['timestamp_str']} ({segment['duration']:.1f}s)")
            print(f"   Category: {segment['category']}")
            print(f"   Score: {segment['score']:.3f}")
            if segment['is_peak']:
                print(f"   Peak moment")
            if segment['is_representative']:
                print(f"   Representative section")
        
        return 0
    except Exception as e:
        logger.error(f"Error creating video summary: {e}", exc_info=True)
        return 1

def extract_clips_cli():
    """CLI entry point for clip extraction from transcript analysis."""
    parser = argparse.ArgumentParser(description="Extract video clips based on transcript analysis")
    parser.add_argument("video_file", help="Path to source video file")
    parser.add_argument("json_file", help="Path to JSON file with clip suggestions")
    parser.add_argument("--output-dir", help="Directory to save extracted clips")
    parser.add_argument("--clip-prefix", default="clip",
                        help="Prefix for output clip filenames (default: 'clip')")
    parser.add_argument("--top-n", type=int, default=None,
                        help="Only extract the top N clips by importance score")
    parser.add_argument("--min-score", type=float, default=None,
                        help="Only extract clips with importance score above this value")
    parser.add_argument("--min-duration", type=float, default=None,
                        help="Only extract clips longer than this duration in seconds")
    parser.add_argument("--max-duration", type=float, default=None,
                        help="Only extract clips shorter than this duration in seconds")
    parser.add_argument("--padding", type=float, default=0.5,
                        help="Add padding in seconds before/after each clip (default: 0.5)")
    parser.add_argument("--disable-ffmpeg", action="store_true",
                        help="Disable direct FFmpeg implementation and use MoviePy instead")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    # Transcript enhancement options
    enhancement_group = parser.add_argument_group('Transcript Enhancement Options')
    enhancement_group.add_argument("--enhance-transcript", action="store_true",
                        help="Apply transcript enhancement before extracting clips")
    enhancement_group.add_argument("--remove-fillers", action="store_true",
                        help="Remove filler words like 'um', 'uh', etc.")
    enhancement_group.add_argument("--handle-repetitions", action="store_true",
                        help="Remove or consolidate repeated phrases")
    enhancement_group.add_argument("--respect-sentences", action="store_true",
                        help="Optimize clip boundaries to respect sentence boundaries")
    enhancement_group.add_argument("--preserve-semantic-units", action="store_true",
                        help="Preserve semantic units like explanations and lists")
    enhancement_group.add_argument("--filler-policy", choices=["remove_all", "keep_all", "context_sensitive"],
                        default="remove_all", help="Policy for handling filler words (default: remove_all)")
    enhancement_group.add_argument("--repetition-strategy", choices=["first_instance", "cleanest_instance", "combine"],
                        default="first_instance", help="Strategy for handling repetitions (default: first_instance)")
    
    parser.add_argument("--transcript-file", help="Path to transcript file (SRT, TXT, etc.) to analyze instead of using JSON")
    parser.add_argument("--transcript-format", default="srt", choices=["srt", "txt", "capcut"],
                    help="Format of the transcript file when using --transcript-file")
    parser.add_argument("--min-clip-duration", type=float, default=10.0,
                    help="Minimum clip duration when analyzing transcript (default: 10.0)")
    parser.add_argument("--max-clip-duration", type=float, default=60.0,
                    help="Maximum clip duration when analyzing transcript (default: 60.0)")
    parser.add_argument("--topic-change-threshold", type=float, default=0.3,
                    help="Topic change detection threshold when analyzing transcript (default: 0.3)")

    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Determine whether to use FFmpeg implementation
        use_ffmpeg = not args.disable_ffmpeg
        
        # Check if we should analyze transcript directly
        if args.transcript_file:
            # First analyze the transcript
            from .transcript_analyzer import analyze_transcript
            
            # Apply enhancement if requested
            transcript_file_to_analyze = args.transcript_file
            if args.enhance_transcript:
                from .transcript_processors import TranscriptEnhancementPipeline, FillerWordsProcessor, RepetitionHandler, SentenceBoundaryDetector, SemanticUnitPreserver
                
                # Configure processors
                processors = []
                if args.remove_fillers:
                    processors.append(FillerWordsProcessor({
                        "policy": args.filler_policy
                    }))
                if args.handle_repetitions:
                    processors.append(RepetitionHandler({
                        "strategy": args.repetition_strategy
                    }))
                if args.respect_sentences:
                    processors.append(SentenceBoundaryDetector())
                if args.preserve_semantic_units:
                    processors.append(SemanticUnitPreserver())
                
                # Use all processors with default settings if none specified
                if not processors:
                    pipeline = TranscriptEnhancementPipeline()
                else:
                    pipeline = TranscriptEnhancementPipeline(processors=processors)
                
                # Process the transcript
                with open(args.transcript_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                
                enhanced_transcript = pipeline.process(transcript_content)
                
                # Save to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
                    f.write(enhanced_transcript)
                    transcript_file_to_analyze = f.name
                
                print(f"Applied transcript enhancement before analysis")
            
            # Create temp file for JSON output
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f:
                json_output_path = f.name
            
            print(f"Analyzing transcript to identify clips...")
            suggestions = analyze_transcript(
                transcript_file=transcript_file_to_analyze,
                output_file=json_output_path,
                transcript_format=args.transcript_format,
                min_clip_duration=args.min_clip_duration,
                max_clip_duration=args.max_clip_duration,
                topic_change_threshold=args.topic_change_threshold,
            )
            
            # Use the generated JSON file for clip extraction
            json_file_to_use = json_output_path
        else:
            # Use the provided JSON file
            json_file_to_use = args.json_file
        
        # Extract clips as before, but use the possibly newly generated JSON
        if args.enhance_transcript and json_file_to_use == args.json_file:
            # Use enhanced clip extraction as before if directly using JSON
            from .transcript_processors import extract_enhanced_clips
            # [rest of your existing enhanced extraction code]
        else:
            # Extract clips directly
            clips = extract_clips_from_json(
                video_file=args.video_file,
                json_file=json_file_to_use,
                output_dir=args.output_dir,
                clip_prefix=args.clip_prefix,
                top_n=args.top_n,
                min_score=args.min_score,
                min_duration=args.min_duration,
                max_duration=args.max_duration,
                add_padding=args.padding,
                use_ffmpeg=use_ffmpeg,
            )
        
        # Clean up temporary files
        if args.transcript_file and 'json_output_path' in locals():
            try:
                os.unlink(json_output_path)
            except:
                pass
        if args.enhance_transcript and 'transcript_file_to_analyze' in locals() and transcript_file_to_analyze != args.transcript_file:
            try:
                os.unlink(transcript_file_to_analyze)
            except:
                pass
        
        print(f"\nClip extraction complete:")
        print(f"- Extracted {len(clips)} clips from {os.path.basename(args.video_file)}")
        
        if clips:
            output_dir = os.path.dirname(clips[0]['output_file'])
            print(f"- Clips saved to: {os.path.abspath(output_dir)}")
            
            # Print information about each clip
            print("\nExtracted clips:")
            for clip in clips:
                start_min = int(clip['extracted_start'] // 60)
                start_sec = int(clip['extracted_start'] % 60)
                end_min = int(clip['extracted_end'] // 60)
                end_sec = int(clip['extracted_end'] % 60)
                
                print(f"\nClip {clip['clip_id']}: {clip['topic']}")
                print(f"- Time: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} "
                      f"({clip['duration']:.1f}s)")
                print(f"- File: {os.path.basename(clip['output_file'])}")
                print(f"- Score: {clip['importance_score']:.2f}")
        
        return 0
    except Exception as e:
        logger.error(f"Error extracting clips: {e}", exc_info=True)
        return 1

def capcut_timeline_cli():
    """CLI entry point for CapCut Video Timeline Tool."""
    parser = argparse.ArgumentParser(description="Analyze CapCut projects for video timeline coverage")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand to run")
    
    # Analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a CapCut project for video coverage")
    analyze_parser.add_argument("--capcut", required=True, help="Path to CapCut draft_content.json file")
    analyze_parser.add_argument("--srt", required=False, help="Optional path to SRT file for timestamp reference")
    analyze_parser.add_argument("--output", help="Output file for analysis report (default: stdout)")
    analyze_parser.add_argument("--debug", action="store_true", help="Enable debug logging for detailed analysis information")
    
    # Visualize subcommand
    visualize_parser = subparsers.add_parser("visualize", help="Visualize the video coverage from an analysis report")
    visualize_parser.add_argument("--report", required=True, help="Path to analysis report JSON file")
    visualize_parser.add_argument("--output", help="Output image file path (PNG)")
    visualize_parser.add_argument("--uncovered-report", help="Generate and save a detailed report of uncovered regions")
    visualize_parser.add_argument("--clip-details", help="Generate and save a detailed report of all video clips")
    visualize_parser.add_argument("--dpi", type=int, default=300, help="DPI for output image")
    visualize_parser.add_argument("--no-clip-labels", action="store_true", help="Hide clip labels on the timeline")
    
    # All-in-one subcommand
    all_parser = subparsers.add_parser("all", help="Run analyze and visualize in one step")
    all_parser.add_argument("--capcut", required=True, help="Path to CapCut draft_content.json file")
    all_parser.add_argument("--srt", required=False, help="Optional path to SRT file for timestamp reference")
    all_parser.add_argument("--output-dir", required=True, help="Directory to save all output files")
    all_parser.add_argument("--debug", action="store_true", help="Enable debug logging for detailed analysis information")
    all_parser.add_argument("--dpi", type=int, default=300, help="DPI for output images")
    all_parser.add_argument("--figsize", default="14,10", help="Figure size in inches, comma-separated (width,height)")
    all_parser.add_argument("--no-clip-labels", action="store_true", help="Hide clip labels on the timeline visualization")
    
    # Add common options
    for subparser in [analyze_parser, visualize_parser, all_parser]:
        subparser.add_argument("--log-level", default="INFO",
                            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                            help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        if not args.subcommand:
            parser.print_help()
            return 1
        
        if args.subcommand == "analyze":
            # Analyze CapCut project for video coverage
            analyzer = VideoTimelineAnalyzer(args.capcut, args.srt, debug=args.debug)
            report = analyzer.analyze_timeline()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(report, f, indent=2)
                print(f"Analysis report saved to {args.output}")
            else:
                import json
                print(json.dumps(report, indent=2))
                
        elif args.subcommand == "visualize":
            # Visualize timeline from report
            import json
            with open(args.report, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            visualize_video_coverage(
                report, 
                args.output, 
                dpi=args.dpi,
                show_clip_labels=not args.no_clip_labels
            )
            print(f"Timeline visualization saved to {args.output}")
            
            # Generate uncovered regions report if requested
            if args.uncovered_report:
                generate_uncovered_regions_report(report, args.uncovered_report)
                print(f"Uncovered regions report saved to {args.uncovered_report}")
            
            # Generate clip details report if requested
            if args.clip_details:
                generate_clip_details_report(report, args.clip_details)
                print(f"Clip details report saved to {args.clip_details}")
            
        elif args.subcommand == "all":
            # Create output directory if it doesn't exist
            os.makedirs(args.output_dir, exist_ok=True)
            
            # Set up paths for output files
            report_path = os.path.join(args.output_dir, "video_coverage_analysis.json")
            visualization_path = os.path.join(args.output_dir, "video_coverage_timeline.png")
            uncovered_report_path = os.path.join(args.output_dir, "uncovered_regions_report.md")
            clip_details_path = os.path.join(args.output_dir, "clip_details_report.md")
            
            # Step 1: Analyze
            analyzer = VideoTimelineAnalyzer(args.capcut, args.srt, debug=args.debug)
            report = analyzer.analyze_timeline()
            
            # Save full report
            with open(report_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(report, f, indent=2)
            print(f"Analysis report saved to {report_path}")
            
            # Step 2: Parse figsize if provided
            figsize = (14, 10)  # Default
            if args.figsize:
                try:
                    width, height = map(float, args.figsize.split(','))
                    figsize = (width, height)
                except:
                    print(f"Warning: Could not parse figsize '{args.figsize}', using default (14,10)")
            
            # Step 3: Visualize
            visualize_video_coverage(
                report, 
                visualization_path,
                dpi=args.dpi,
                figsize=figsize,
                show_clip_labels=not args.no_clip_labels
            )
            print(f"Timeline visualization saved to {visualization_path}")
            
            # Step 4: Generate uncovered regions report
            generate_uncovered_regions_report(report, uncovered_report_path)
            print(f"Uncovered regions report saved to {uncovered_report_path}")
            
            # Step 5: Generate clip details report
            generate_clip_details_report(report, clip_details_path)
            print(f"Clip details report saved to {clip_details_path}")
            
            # Print summary
            timeline_duration = report['duration']
            covered_duration = sum([segment['duration'] for segment in report['covered_segments']])
            uncovered_duration = sum([segment['duration'] for segment in report['uncovered_segments']])
            coverage_percentage = (covered_duration / timeline_duration) * 100 if timeline_duration > 0 else 0
            
            print(f"\nVideo Timeline Coverage Analysis Summary:")
            print(f"- Total duration: {int(timeline_duration // 60):02d}:{int(timeline_duration % 60):02d} ({timeline_duration:.1f}s)")
            print(f"- Video coverage: {coverage_percentage:.1f}% of timeline has video clips")
            print(f"- Video clip count: {len(report['video_clips'])} clips across {report['track_count']} tracks")
            print(f"- Uncovered regions: {len(report['uncovered_segments'])} regions ({uncovered_duration:.1f}s total)")
            print(f"- All outputs saved to: {os.path.abspath(args.output_dir)}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Error processing CapCut Video Timeline Tool command: {e}", exc_info=True)
        return 1


def main():
    """Main entry point for CLI commands."""
    if len(sys.argv) < 2:
        print("Error: Please specify a command")
        print("Available commands: remove-silence, analyze-transcript, extract-clips, capcut-timeline, etc.")
        sys.exit(1)
        
    command = sys.argv[0] if '/' not in sys.argv[0] else sys.argv[0].split('/')[-1]
    
    if command == "remove-silence" or "remove_silence" in command:
        sys.exit(remove_silence_cli())
    elif command == "analyze-transcript" or "analyze_transcript" in command:
        sys.exit(analyze_transcript_cli())
    elif command == "generate-thumbnails" or "generate_thumbnails" in command:
        sys.exit(generate_thumbnails_cli())
    elif command == "analyze-colors" or "analyze_colors" in command:
        sys.exit(analyze_colors_cli())
    elif command == "detect-jump-cuts" or "detect_jump_cuts" in command:
        sys.exit(detect_jump_cuts_cli())
    elif command == "create-summary" or "create_summary" in command:
        sys.exit(create_summary_cli())
    elif command == "extract-clips" or "extract_clips" in command:
        sys.exit(extract_clips_cli())
    elif command == "capcut-timeline" or "capcut_timeline" in command:
        sys.exit(capcut_timeline_cli())
    else:
        print(f"Error: Unknown command: {command}")
        print("Available commands: remove-silence, analyze-transcript, extract-clips, capcut-timeline, etc.")
        sys.exit(1)

if __name__ == "__main__":
    main()
