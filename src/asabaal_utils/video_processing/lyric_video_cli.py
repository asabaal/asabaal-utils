"""Standalone CLI for lyric video generation."""

import argparse
import logging
import sys
import json
from pathlib import Path

from .lyric_video import LyricVideoGenerator


def setup_logging(level=logging.INFO):
    """Set up logging."""
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def create_lyric_video_cli():
    """CLI for creating lyric videos."""
    parser = argparse.ArgumentParser(
        description="Create automated lyric videos with synchronized text and audio-reactive effects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --output video.mp4
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --background bg.mp4 --template modern --output video.mp4
  create-lyric-video --audio song.mp3 --lyrics "Manual lyrics here" --quality fast --output video.mp4
        """
    )
    
    parser.add_argument("--audio", required=True,
                        help="Path to audio file (MP3, WAV, FLAC, etc.)")
    parser.add_argument("--lyrics", required=True,
                        help="Path to lyrics file (SRT, LRC) or raw text")
    parser.add_argument("--output", required=True,
                        help="Output video file path")
    parser.add_argument("--background",
                        help="Path to background video file (optional)")
    parser.add_argument("--background-clips-dir",
                        help="Path to directory of background video clips for beat-based switching")
    parser.add_argument("--text-only", action="store_true",
                        help="Generate transparent text overlay only (no background)")
    parser.add_argument("--template", default="default",
                        help="Template name or path to template JSON (default: 'default')")
    parser.add_argument("--resolution", default="1920x1080",
                        help="Output resolution in WIDTHxHEIGHT format (default: 1920x1080)")
    parser.add_argument("--fps", type=float, default=30.0,
                        help="Output frame rate (default: 30.0)")
    parser.add_argument("--quality", choices=["fast", "balanced", "high_quality"], default="balanced",
                        help="Encoding quality preset (default: balanced)")
    parser.add_argument("--font-family", 
                        help="Override font family")
    parser.add_argument("--font-size", type=int,
                        help="Override font size")
    parser.add_argument("--text-color",
                        help="Override text color (hex format, e.g., #FFFFFF)")
    parser.add_argument("--sync-to-beats", action="store_true", default=True,
                        help="Synchronize animations to audio beats (default: enabled)")
    parser.add_argument("--no-sync-to-beats", action="store_false", dest="sync_to_beats",
                        help="Disable beat synchronization")
    parser.add_argument("--system-info", action="store_true",
                        help="Show system information and available hardware acceleration")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    
    args = parser.parse_args()
    
    # Set log level
    setup_logging(getattr(logging, args.log_level))
    
    try:
        # Parse resolution
        try:
            width, height = map(int, args.resolution.split('x'))
            resolution = (width, height)
        except ValueError:
            raise ValueError(f"Invalid resolution format: {args.resolution}. Use WIDTHxHEIGHT (e.g., 1920x1080)")
        
        # Create generator
        generator = LyricVideoGenerator(resolution=resolution, fps=args.fps)
        
        # Show system info if requested
        if args.system_info:
            info = generator.get_system_info()
            print("System Information:")
            print(json.dumps(info, indent=2))
            return 0
        
        # Prepare custom config
        custom_config = {}
        if args.font_family or args.font_size or args.text_color:
            custom_config["text_config"] = {}
            if args.font_family:
                custom_config["text_config"]["font_family"] = args.font_family
            if args.font_size:
                custom_config["text_config"]["font_size"] = args.font_size
            if args.text_color:
                # Convert hex color to RGB tuple
                color_hex = args.text_color.lstrip('#')
                if len(color_hex) == 6:
                    r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                    custom_config["text_config"]["color"] = [r, g, b]
                    
        if not args.sync_to_beats:
            custom_config["animation_config"] = {"sync_to_beats": False}
            
        if args.quality != "balanced":
            custom_config["quality_preset"] = args.quality
        
        print(f"Creating lyric video...")
        print(f"Audio: {args.audio}")
        print(f"Lyrics: {args.lyrics}")
        print(f"Output: {args.output}")
        print(f"Resolution: {resolution[0]}x{resolution[1]}")
        print(f"FPS: {args.fps}")
        if args.background:
            print(f"Background: {args.background}")
        elif args.background_clips_dir:
            print(f"Background clips directory: {args.background_clips_dir}")
        elif args.text_only:
            print("Mode: Text overlay only (transparent background)")
        print(f"Template: {args.template}")
        print()
        
        # Generate video
        output_path = generator.create_video(
            audio_path=args.audio,
            lyrics_path=args.lyrics,
            output_path=args.output,
            background_video=args.background,
            background_clips_dir=args.background_clips_dir,
            template=args.template,
            custom_config=custom_config if custom_config else None,
            text_only_output=args.text_only
        )
        
        print(f"\n✅ Lyric video created successfully: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
    except Exception as e:
        logging.error(f"Error creating lyric video: {e}", exc_info=True)
        print(f"❌ Error creating lyric video: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(create_lyric_video_cli())