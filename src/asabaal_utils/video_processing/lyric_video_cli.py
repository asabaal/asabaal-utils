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
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --start-time 30 --duration 60 --output test.mp4
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --structure-file song_structure.json --output video.mp4
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --font-family "Bebas Neue" --output video.mp4
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --bespoke-style neon --output video.mp4
  create-lyric-video --audio song.mp3 --lyrics lyrics.srt --music-genre rock --song-mood energetic --output video.mp4
  create-lyric-video --list-fonts  # Show all available fonts and styles
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
                        help="Override font family (e.g., 'Bebas Neue', 'Montserrat Bold', 'Dancing Script')")
    parser.add_argument("--font-size", type=int,
                        help="Override font size")
    parser.add_argument("--text-color",
                        help="Override text color (hex format, e.g., #FFFFFF)")
    parser.add_argument("--bespoke-style",
                        choices=["neon", "graffiti", "chrome", "fire", "ice", "gold", "hologram", "matrix", "basic"],
                        help="Use bespoke generated font style instead of regular fonts")
    parser.add_argument("--font-style", 
                        help="Auto-suggest font based on style (modern, bold, elegant, tech, etc.)")
    parser.add_argument("--music-genre",
                        help="Auto-suggest font based on music genre (rock, pop, classical, electronic, etc.)")
    parser.add_argument("--song-mood",
                        help="Auto-suggest bespoke style based on song mood (energetic, calm, mysterious, etc.)")
    parser.add_argument("--list-fonts", action="store_true",
                        help="List all available fonts and styles, then exit")
    parser.add_argument("--sync-to-beats", action="store_true", default=True,
                        help="Synchronize animations to audio beats (default: enabled)")
    parser.add_argument("--no-sync-to-beats", action="store_false", dest="sync_to_beats",
                        help="Disable beat synchronization")
    parser.add_argument("--system-info", action="store_true",
                        help="Show system information and available hardware acceleration")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")
    parser.add_argument("--start-time", type=float, default=0.0,
                        help="Start time in seconds for testing specific sections (default: 0.0)")
    parser.add_argument("--end-time", type=float,
                        help="End time in seconds for testing specific sections (optional)")
    parser.add_argument("--duration", type=float,
                        help="Duration in seconds (alternative to --end-time)")
    parser.add_argument("--structure-file",
                        help="Path to song structure file (JSON, YAML, or text format) for custom section definitions")
    
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
        
        # Validate and process time range arguments
        start_time = args.start_time
        end_time = None
        
        if args.end_time and args.duration:
            raise ValueError("Cannot specify both --end-time and --duration. Use one or the other.")
        
        if args.end_time:
            end_time = args.end_time
            if end_time <= start_time:
                raise ValueError(f"End time ({end_time}s) must be greater than start time ({start_time}s)")
        elif args.duration:
            if args.duration <= 0:
                raise ValueError(f"Duration must be positive, got {args.duration}s")
            end_time = start_time + args.duration
        
        if start_time < 0:
            raise ValueError(f"Start time must be non-negative, got {start_time}s")
        
        # Create generator
        generator = LyricVideoGenerator(resolution=resolution, fps=args.fps)
        
        # Show system info if requested
        if args.system_info:
            info = generator.get_system_info()
            print("System Information:")
            print(json.dumps(info, indent=2))
            return 0
        
        # List fonts if requested
        if args.list_fonts:
            from .lyric_video.text.fonts import FontManager
            font_manager = FontManager()
            
            print("🎨 Available Font Styles and Options:\n")
            
            # Available font categories
            styles = font_manager.get_available_font_styles()
            for category, fonts in styles.items():
                print(f"📁 {category}:")
                for font in fonts[:10]:  # Limit to first 10 to avoid spam
                    print(f"   • {font}")
                if len(fonts) > 10:
                    print(f"   ... and {len(fonts) - 10} more")
                print()
            
            # Bespoke styles with descriptions
            print("✨ Bespoke Font Styles (procedurally generated):")
            for style in font_manager.font_generator.list_available_styles():
                description = font_manager.font_generator.get_style_description(style)
                print(f"   • {style}: {description}")
            print()
            
            # Font recommendations by category
            print("🎭 Font Categories:")
            categories = font_manager.list_downloadable_fonts_by_category()
            for category, fonts in categories.items():
                print(f"   • {category}: {', '.join(fonts[:3])}{'...' if len(fonts) > 3 else ''}")
            print()
            
            print("💡 Usage Examples:")
            print("   --font-family 'Bebas Neue'")
            print("   --bespoke-style neon")
            print("   --music-genre rock")
            print("   --song-mood energetic")
            print("   --font-style bold")
            
            return 0
        
        # Prepare custom config with intelligent font selection
        custom_config = {}
        
        # Font auto-suggestion and configuration
        font_manager = None
        selected_font = args.font_family
        selected_bespoke_style = args.bespoke_style
        
        # Auto-suggest fonts based on user input
        if args.music_genre or args.song_mood or args.font_style:
            from .lyric_video.text.fonts import FontManager
            font_manager = FontManager()
            
            if args.music_genre and not selected_font:
                selected_font = font_manager.suggest_font_for_genre(args.music_genre)
                print(f"🎵 Auto-selected font for {args.music_genre} genre: {selected_font}")
            
            if args.song_mood and not selected_bespoke_style:
                selected_bespoke_style = font_manager.suggest_bespoke_style_for_mood(args.song_mood)
                print(f"🎭 Auto-selected bespoke style for {args.song_mood} mood: {selected_bespoke_style}")
            
            if args.font_style and not selected_font:
                selected_font = font_manager.font_loader.suggest_font_for_style(args.font_style)
                print(f"✨ Auto-selected font for {args.font_style} style: {selected_font}")
        
        # Configure text settings
        if selected_font or args.font_size or args.text_color or selected_bespoke_style:
            custom_config["text_config"] = {}
            
            if selected_font:
                custom_config["text_config"]["font_family"] = selected_font
                
            if selected_bespoke_style:
                custom_config["text_config"]["bespoke_style"] = selected_bespoke_style
                print(f"🎨 Using bespoke style: {selected_bespoke_style}")
                
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
        if start_time > 0 or end_time:
            if end_time:
                duration_info = f"{end_time - start_time:.1f}s"
                print(f"Time range: {start_time:.1f}s to {end_time:.1f}s (duration: {duration_info})")
            else:
                print(f"Start time: {start_time:.1f}s (to end of audio)")
        if args.background:
            print(f"Background: {args.background}")
        elif args.background_clips_dir:
            print(f"Background clips directory: {args.background_clips_dir}")
        elif args.text_only:
            print("Mode: Text overlay only (transparent background)")
        if args.structure_file:
            print(f"Structure file: {args.structure_file}")
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
            text_only_output=args.text_only,
            start_time=start_time if start_time > 0 else None,
            end_time=end_time,
            structure_file=args.structure_file
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