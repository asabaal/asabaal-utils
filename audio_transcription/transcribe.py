#!/usr/bin/env python3
"""
Audio Transcription CLI Tool

A comprehensive audio transcription tool using faster-whisper with optional
WhisperX alignment, diarization, and LLM post-processing.
"""

import argparse
import json
import shlex
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import BaseModel

# Configuration
DEFAULT_INBOX = Path("./inbox")
DEFAULT_OUTBOX = Path("./output")
DEFAULT_ASR_MODEL = "small"
DEFAULT_DEVICE = "auto"
DEFAULT_COMPUTE_TYPE = "auto"
DEFAULT_USE_VAD = True
DEFAULT_BEAM_SIZE = 1
DEFAULT_USE_WHISPERX = True
DEFAULT_USE_DIARIZATION = False
DEFAULT_ENABLE_LLM_POST = True
DEFAULT_LLM_BASE_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "llama3.1:8b"
DEFAULT_LLM_TIMEOUT = 60

# Audio processing constants
AUDIO_RATE = 16000
AUDIO_MONO = 1

# Supported file extensions
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}

# Data models
class Word(BaseModel):
    text: str
    start: Optional[float] = None
    end: Optional[float] = None

class Segment(BaseModel):
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    words: Optional[List[Word]] = None

class Transcript(BaseModel):
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: List[Segment]

# Utility functions
def run_command(cmd: str) -> str:
    """Execute a shell command and return stdout"""
    proc = subprocess.run(
        shlex.split(cmd), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {cmd}\n{proc.stdout}")
    return proc.stdout

def format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp"""
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=float(seconds))
    total_seconds = int(td.total_seconds())
    ms = int((td.total_seconds() - total_seconds) * 1000)
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"

def format_vtt_time(seconds: float) -> str:
    """Format seconds as WebVTT timestamp"""
    if seconds < 0:
        seconds = 0
    td = timedelta(seconds=float(seconds))
    total_seconds = int(td.total_seconds())
    ms = int((td.total_seconds() - total_seconds) * 1000)
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    return f"{hh:02}:{mm:02}:{ss:02}.{ms:03}"

def gpu_available() -> bool:
    """Check if GPU is available"""
    try:
        out = run_command("nvidia-smi -L")
        return "GPU" in out
    except Exception:
        return False

def pick_device_and_compute(device: str, compute_type: str) -> tuple[str, str]:
    """Determine optimal device and compute type"""
    dev = ("cuda" if gpu_available() else "cpu") if device == "auto" else device
    if compute_type == "auto":
        if dev == "cuda":
            ctype = "float16"
        else:
            ctype = "int8"  # good default for CPU to save RAM
    else:
        ctype = compute_type
    return dev, ctype

def extract_audio(src: Path, dst: Path) -> None:
    """Extract and normalize audio from video/audio file"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    # normalize to mono 16k PCM WAV
    cmd = f'ffmpeg -y -i "{src}" -ac {AUDIO_MONO} -ar {AUDIO_RATE} -c:a pcm_s16le "{dst}"'
    run_command(cmd)

def transcribe_with_faster_whisper(wav_path: Path, model_name: str, device: str, compute_type: str, use_vad: bool, beam_size: int) -> Transcript:
    """Transcribe audio using faster-whisper"""
    from faster_whisper import WhisperModel
    
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    
    segments_iter, info = model.transcribe(
        str(wav_path),
        vad_filter=use_vad,
        beam_size=beam_size
    )

    segments = []
    dur = 0.0
    for seg in segments_iter:
        segments.append(Segment(start=seg.start, end=seg.end, text=seg.text.strip()))
        if seg.end:
            dur = max(dur, seg.end)

    return Transcript(language=getattr(info, "language", None), duration=dur, segments=segments)

def align_and_diarize_whisperx(wav_path: Path, tr: Transcript, device: str, compute_type: str, use_diarization: bool) -> Transcript:
    """Apply WhisperX alignment and optional diarization"""
    try:
        import whisperx
    except ImportError:
        raise ImportError("WhisperX not installed. Install with: pip install whisperx")
    
    # alignment model
    align_model, metadata = whisperx.load_align_model(
        language_code=tr.language or "en",
        device=device
    )

    # convert segments -> whisperx format
    wx_segments = [{"start": s.start, "end": s.end, "text": s.text} for s in tr.segments]

    # word-level alignment
    result_aligned = whisperx.align(
        wx_segments,
        align_model,
        metadata,
        str(wav_path),
        device,
        return_char_alignments=False
    )

    # diarization (optional)
    if use_diarization:
        try:
            # Try to import DiarizationPipeline - it may not be available in all whisperx versions
            if hasattr(whisperx, 'DiarizationPipeline'):
                diarize_model = whisperx.DiarizationPipeline(use_auth_token=True)  # requires HF token in env
                diarize_segments = diarize_model(str(wav_path))
                # assign speakers to words
                result_aligned = whisperx.assign_word_speakers(diarize_segments, result_aligned)
            else:
                print("[WARNING] DiarizationPipeline not available in this whisperx version")
        except Exception as e:
            print(f"[WARNING] Diarization failed: {e}")

    # build back into our schema
    new_segments: List[Segment] = []
    for seg in result_aligned["segments"]:
        words = [Word(text=w.get("word", "").strip(),
                      start=w.get("start"),
                      end=w.get("end")) for w in seg.get("words", []) if w.get("word")]
        speaker = seg.get("speaker")
        new_segments.append(Segment(
            start=seg.get("start", 0.0),
            end=seg.get("end", 0.0),
            text=seg.get("text", "").strip(),
            speaker=speaker,
            words=words if words else None
        ))
    tr.segments = new_segments
    return tr

def llm_postprocess(outdir: Path, tr: Transcript, llm_base_url: str, llm_model: str, llm_timeout: int) -> None:
    """Apply LLM post-processing for summarization"""
    try:
        import requests
        full_text = "\n".join(s.text for s in tr.segments if s.text)
        prompt = (
            "You are an assistant that generates:\n"
            "1) A 1-paragraph summary\n"
            "2) 5 concise chapter titles with timestamps if available\n"
            "3) 3 social captions (<= 120 chars each)\n\n"
            "Return JSON with keys: summary, chapters, captions.\n"
        )
        payload = {
            "model": llm_model,
            "prompt": prompt + "\n\nTRANSCRIPT:\n" + full_text,
            "stream": False
        }
        r = requests.post(
            f"{llm_base_url}/api/generate", 
            json=payload, 
            timeout=llm_timeout
        )
        r.raise_for_status()
        data = r.json()
        content = data.get("response", "")
        # try parse JSON from content
        try:
            js = json.loads(content)
        except Exception:
            js = {"raw": content}
        (outdir / "postprocess.json").write_text(json.dumps(js, indent=2), encoding="utf-8")
    except Exception as e:
        (outdir / "postprocess_error.txt").write_text(str(e), encoding="utf-8")

def write_transcript_outputs(outdir: Path, tr: Transcript) -> None:
    """Write all transcript output formats"""
    
    # Write plain text
    (outdir / "transcript.txt").write_text(
        "\n".join(s.text for s in tr.segments if s.text).strip() + "\n",
        encoding="utf-8"
    )

    # Write JSON
    (outdir / "transcript.json").write_text(
        tr.model_dump_json(indent=2),
        encoding="utf-8"
    )

    # Write SRT
    srt_lines = []
    for i, s in enumerate(tr.segments, start=1):
        srt_lines.append(str(i))
        srt_lines.append(f"{format_srt_time(s.start)} --> {format_srt_time(s.end)}")
        prefix = f"{s.speaker}: " if s.speaker else ""
        srt_lines.append(prefix + s.text)
        srt_lines.append("")  # blank line
    (outdir / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    # Write VTT
    vtt_lines = ["WEBVTT", ""]
    for s in tr.segments:
        vtt_lines.append(f"{format_vtt_time(s.start)} --> {format_vtt_time(s.end)}")
        prefix = f"{s.speaker}: " if s.speaker else ""
        vtt_lines.append(prefix + s.text)
        vtt_lines.append("")
    (outdir / "captions.vtt").write_text("\n".join(vtt_lines), encoding="utf-8")

def process_media_file(file_path: Path, config: dict) -> Path:
    """Process a single media file and return output directory"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stem = file_path.stem
    outbox = config['outbox']
    outdir = outbox / stem
    outdir.mkdir(parents=True, exist_ok=True)

    # 1) Extract audio
    wav_path = outdir / "audio_16k_mono.wav"
    print(f"[ffmpeg] extracting audio → {wav_path.name}")
    extract_audio(file_path, wav_path)

    # 2) Transcribe
    print("[ASR] faster-whisper transcribing…")
    device, compute_type = pick_device_and_compute(config['device'], config['compute_type'])
    tr = transcribe_with_faster_whisper(
        wav_path, config['asr_model'], device, compute_type, 
        config['use_vad'], config['beam_size']
    )
    print(f"[ASR] language={tr.language} duration≈{tr.duration:.1f}s segments={len(tr.segments)}")

    # 3) Optional alignment/diarization
    if config['use_whisperx']:
        print("[ALIGN] WhisperX aligning (and diarizing if enabled)…")
        try:
            tr = align_and_diarize_whisperx(wav_path, tr, device, compute_type, config['use_diarization'])
        except Exception as e:
            print(f"[WARNING] WhisperX processing failed: {e}")

    # 4) Write artifacts
    write_transcript_outputs(outdir, tr)

    # 5) Optional LLM post-processing
    if config['enable_llm_post']:
        llm_postprocess(outdir, tr, config['llm_base_url'], config['llm_model'], config['llm_timeout'])

    print(f"[DONE] Outputs in {outdir}")
    return outdir

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Audio Transcription Pipeline - Transcribe audio/video files using faster-whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe a single file
  python transcribe.py video.mp4
  
  # Transcribe with custom output directory
  python transcribe.py --output ./transcripts audio.wav
  
  # Use larger model for better accuracy
  python transcribe.py --model medium --device cuda video.mp4
  
  # Enable WhisperX alignment and diarization
  python transcribe.py --whisperx --diarize meeting.mp4
  
  # Watch directory for new files
  python transcribe.py --watch ./inbox --output ./transcripts
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
        default=DEFAULT_OUTBOX,
        help="Output directory for transcripts (default: ./output)"
    )
    
    # ASR model options
    parser.add_argument(
        "--model", "-m",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        default=DEFAULT_ASR_MODEL,
        help="Whisper model size (default: small)"
    )
    
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default=DEFAULT_DEVICE,
        help="Processing device (default: auto)"
    )
    
    parser.add_argument(
        "--compute-type",
        choices=["auto", "int8", "float16", "float32"],
        default=DEFAULT_COMPUTE_TYPE,
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
        default=DEFAULT_BEAM_SIZE,
        help="Beam search size (default: 1)"
    )
    
    # WhisperX options
    parser.add_argument(
        "--whisperx",
        action="store_true",
        default=DEFAULT_USE_WHISPERX,
        help="Enable WhisperX word-level alignment"
    )
    
    parser.add_argument(
        "--diarize",
        action="store_true",
        default=DEFAULT_USE_DIARIZATION,
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
        default=DEFAULT_LLM_BASE_URL,
        help="LLM API base URL (default: http://localhost:11434)"
    )
    
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="LLM model name (default: llama3.1:8b)"
    )
    
    parser.add_argument(
        "--llm-timeout",
        type=int,
        default=DEFAULT_LLM_TIMEOUT,
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

def process_files(files: list[Path], config: dict) -> None:
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

class TranscriptionHandler(FileSystemEventHandler):
    def __init__(self, config: dict):
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

def watch_directory(watch_dir: Path, config: dict) -> None:
    """Watch directory for new files and process them automatically"""
    # Ensure directories exist
    watch_dir.mkdir(parents=True, exist_ok=True)
    config['outbox'].mkdir(parents=True, exist_ok=True)
    
    print(f"[WATCH] Monitoring: {watch_dir}")
    print(f"[WATCH] Output: {config['outbox']}")
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
    config = {
        'outbox': args.output,
        'asr_model': args.model,
        'device': args.device,
        'compute_type': args.compute_type,
        'use_vad': not args.no_vad,
        'beam_size': args.beam_size,
        'use_whisperx': args.whisperx,
        'use_diarization': args.diarize,
        'enable_llm_post': not args.no_llm,
        'llm_base_url': args.llm_url,
        'llm_model': args.llm_model,
        'llm_timeout': args.llm_timeout,
    }
    
    # Validate diarization requires whisperx
    if args.diarize and not args.whisperx:
        print("[ERROR] --diarize requires --whisperx")
        sys.exit(1)
    
    # Ensure output directory exists
    config['outbox'].mkdir(parents=True, exist_ok=True)
    
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