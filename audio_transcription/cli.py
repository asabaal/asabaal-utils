#!/usr/bin/env python3
"""
Audio Transcription CLI

Command-line interface for the audio transcription pipeline.
"""

import argparse
import sys
import time
from pathlib import Path

# Import local modules
try:
    from .config import TranscriptionConfig
    from .transcriber import process_media_file, VIDEO_EXTS, AUDIO_EXTS
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import TranscriptionConfig
    from transcriber import process_media_file, VIDEO_EXTS, AUDIO_EXTS


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Audio Transcription Pipeline - Transcribe audio/video files using faster-whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe a single file
  audio-transcribe video.mp4
  
  # Transcribe with custom output directory
  audio-transcribe --output ./transcripts audio.wav
  
  # Use larger model for better accuracy
  audio-transcribe --model medium --device cuda video.mp4
  
  # Enable WhisperX alignment and diarization
  audio-transcribe --whisperx --diarize meeting.mp4
  
  # Watch directory for new files
  audio-transcribe --watch ./inbox --output ./transcripts
        """
    )
    
    # Input options
    parser.add_argument(
        "files",
        nargs="*",
        help="Audio or video files to transcribe"
    )
    
    parser.add_argument(
        "--watch", "-w",
        type=Path,
        help="Watch directory for new media files (instead of processing specific files)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("./output"),
        help="Output directory for transcripts (default: ./output)"
    )
    
    # ASR model options
    parser.add_argument(
        "--model", "-m",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        default="small",
        help="Whisper model size (default: small)"
    )
    
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Processing device (default: auto)"
    )
    
    parser.add_argument(
        "--compute-type",
        choices=["auto", "int8", "float16", "float32"],
        default="auto",
        help="Compute type (default: auto)"
    )
    
    # Transcription options
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable voice activity detection"
    )
    
    parser.add_argument(
        "--beam-size",
        type=int,
        default=1,
        help="Beam search size (default: 1)"
    )
    
    # WhisperX options
    parser.add_argument(
        "--whisperx",
        action="store_true",
        help="Enable WhisperX word-level alignment"
    )
    
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization (requires --whisperx and HF token)"
    )
    
    # LLM post-processing options
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM post-processing"
    )
    
    parser.add_argument(
        "--llm-url",
        default="http://localhost:11434",
        help="LLM API base URL (default: http://localhost:11434)"
    )
    
    parser.add_argument(
        "--llm-model",
        default="llama3.1:8b",
        help="LLM model name (default: llama3.1:8b)"
    )
    
    parser.add_argument(
        "--llm-timeout",
        type=int,
        default=60,
        help="LLM request timeout in seconds (default: 60)"
    )
    
    return parser


def validate_files(files: list[Path]) -> list[Path]:
    """Validate that files exist and have supported extensions"""
    valid_files = []
    supported_exts = VIDEO_EXTS.union(AUDIO_EXTS)
    
    for file_path in files:
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            continue
        
        if file_path.suffix.lower() not in supported_exts:
            print(f"[ERROR] Unsupported file type: {file_path.suffix}")
            print(f"Supported video: {', '.join(sorted(VIDEO_EXTS))}")
            print(f"Supported audio: {', '.join(sorted(AUDIO_EXTS))}")
            continue
        
        valid_files.append(file_path)
    
    return valid_files


def process_files(files: list[Path], config: TranscriptionConfig) -> None:
    """Process multiple files with progress tracking"""
    if not files:
        print("[INFO] No valid files to process")
        return
    
    print(f"[INFO] Processing {len(files)} file(s)...")
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file_path.name}")
        try:
            output_dir = process_media_file(file_path, config)
            print(f"[SUCCESS] {file_path.name} → {output_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path.name}: {e}")


def watch_directory(watch_dir: Path, config: TranscriptionConfig) -> None:
    """Watch directory for new files and process them automatically"""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("[ERROR] watchdog package not installed. Install with: pip install watchdog")
        sys.exit(1)
    
    class TranscriptionHandler(FileSystemEventHandler):
        def __init__(self, config: TranscriptionConfig):
            self.config = config
            self.supported_exts = VIDEO_EXTS.union(AUDIO_EXTS)
        
        def on_created(self, event):
            if event.is_directory:
                return
            
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_exts:
                # Wait briefly for file copy to complete
                time.sleep(1.0)
                print(f"\n[NEW FILE] {file_path.name}")
                try:
                    process_media_file(file_path, self.config)
                except Exception as e:
                    print(f"[ERROR] Failed to process {file_path.name}: {e}")
    
    # Ensure directories exist
    config.ensure_dirs()
    
    print(f"[WATCH] Monitoring: {watch_dir}")
    print(f"[WATCH] Output: {config.outbox}")
    print("[WATCH] Press Ctrl+C to stop")
    
    observer = Observer()
    handler = TranscriptionHandler(config)
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[WATCH] Stopping...")
        observer.stop()
    observer.join()


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create configuration
    config = TranscriptionConfig(
        inbox=args.watch or Path("./inbox"),
        outbox=args.output,
        asr_model=args.model,
        device=args.device,
        compute_type=args.compute_type,
        use_vad=not args.no_vad,
        beam_size=args.beam_size,
        use_whisperx=args.whisperx,
        use_diarization=args.diarize,
        enable_llm_post=not args.no_llm,
        llm_base_url=args.llm_url,
        llm_model=args.llm_model,
        llm_timeout=args.llm_timeout,
    )
    
    # Validate diarization requires whisperx
    if args.diarize and not args.whisperx:
        print("[ERROR] --diarize requires --whisperx")
        sys.exit(1)
    
    # Ensure output directory exists
    config.outbox.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        # Watch mode
        if not args.watch.exists():
            print(f"[ERROR] Watch directory not found: {args.watch}")
            sys.exit(1)
        
        watch_directory(args.watch, config)
    else:
        # File processing mode
        if not args.files:
            print("[ERROR] No files specified. Use --watch to monitor a directory or provide file paths.")
            parser.print_help()
            sys.exit(1)
        
        # Convert to Path objects and validate
        files = [Path(f).expanduser().resolve() for f in args.files]
        valid_files = validate_files(files)
        
        if not valid_files:
            print("[ERROR] No valid files to process")
            sys.exit(1)
        
        process_files(valid_files, config)


if __name__ == "__main__":
    main()