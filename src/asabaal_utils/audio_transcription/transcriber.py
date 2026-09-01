"""
Core transcription functionality
"""

import json
import shlex
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import List, Optional

# Import local modules - handle both relative and absolute imports
try:
    from .config import TranscriptionConfig
    from .models import Transcript, Segment, Word
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import TranscriptionConfig
    from models import Transcript, Segment, Word


# Audio processing constants
AUDIO_RATE = 16000
AUDIO_MONO = 1

# Supported file extensions
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}


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


def pick_device_and_compute(config: TranscriptionConfig) -> tuple[str, str]:
    """Determine optimal device and compute type"""
    dev = ("cuda" if gpu_available() else "cpu") if config.device == "auto" else config.device
    if config.compute_type == "auto":
        if dev == "cuda":
            ctype = "float16"
        else:
            ctype = "int8"  # good default for CPU to save RAM
    else:
        ctype = config.compute_type
    return dev, ctype


def extract_audio(src: Path, dst: Path) -> None:
    """Extract and normalize audio from video/audio file"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    # normalize to mono 16k PCM WAV
    cmd = f'ffmpeg -y -i "{src}" -ac {AUDIO_MONO} -ar {AUDIO_RATE} -c:a pcm_s16le "{dst}"'
    run_command(cmd)


def transcribe_with_faster_whisper(wav_path: Path, config: TranscriptionConfig) -> Transcript:
    """Transcribe audio using faster-whisper"""
    from faster_whisper import WhisperModel
    
    device, compute_type = pick_device_and_compute(config)
    model = WhisperModel(config.asr_model, device=device, compute_type=compute_type)
    
    segments_iter, info = model.transcribe(
        str(wav_path),
        vad_filter=config.use_vad,
        beam_size=config.beam_size
    )

    segments = []
    dur = 0.0
    for seg in segments_iter:
        segments.append(Segment(start=seg.start, end=seg.end, text=seg.text.strip()))
        if seg.end:
            dur = max(dur, seg.end)

    return Transcript(language=getattr(info, "language", None), duration=dur, segments=segments)


def align_and_diarize_whisperx(wav_path: Path, tr: Transcript, config: TranscriptionConfig) -> Transcript:
    """Apply WhisperX alignment and optional diarization"""
    try:
        import whisperx
    except ImportError:
        raise ImportError("WhisperX not installed. Install with: pip install whisperx")
    
    device, compute_type = pick_device_and_compute(config)

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
    if config.use_diarization:
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


def llm_postprocess(outdir: Path, tr: Transcript, config: TranscriptionConfig) -> None:
    """Apply LLM post-processing for summarization"""
    if not config.enable_llm_post:
        return
    
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
            "model": config.llm_model,
            "prompt": prompt + "\n\nTRANSCRIPT:\n" + full_text,
            "stream": False
        }
        r = requests.post(
            f"{config.llm_base_url}/api/generate", 
            json=payload, 
            timeout=config.llm_timeout
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


def process_media_file(file_path: Path, config: TranscriptionConfig) -> Path:
    """Process a single media file and return output directory"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stem = file_path.stem
    outdir = config.outbox / stem
    outdir.mkdir(parents=True, exist_ok=True)

    # 1) Extract audio
    wav_path = outdir / "audio_16k_mono.wav"
    print(f"[ffmpeg] extracting audio → {wav_path.name}")
    extract_audio(file_path, wav_path)

    # 2) Transcribe
    print("[ASR] faster-whisper transcribing…")
    tr = transcribe_with_faster_whisper(wav_path, config)
    print(f"[ASR] language={tr.language} duration≈{tr.duration:.1f}s segments={len(tr.segments)}")

    # 3) Optional alignment/diarization
    if config.use_whisperx:
        print("[ALIGN] WhisperX aligning (and diarizing if enabled)…")
        try:
            tr = align_and_diarize_whisperx(wav_path, tr, config)
        except Exception as e:
            print(f"[WARNING] WhisperX processing failed: {e}")

    # 4) Write artifacts
    write_transcript_outputs(outdir, tr)

    # 5) Optional LLM post-processing
    llm_postprocess(outdir, tr, config)

    print(f"[DONE] Outputs in {outdir}")
    return outdir