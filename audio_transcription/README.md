# Audio Transcription Pipeline

A comprehensive audio transcription tool using faster-whisper with optional WhisperX alignment, diarization, and LLM post-processing.

## Features

- **Fast transcription** using faster-whisper (optimized OpenAI Whisper)
- **Multiple input formats**: MP4, MOV, MKV, AVI, M4V, WAV, MP3, M4A, AAC, FLAC, OGG
- **Multiple output formats**: Plain text, JSON, SRT captions, WebVTT captions
- **Optional WhisperX integration**: Word-level alignment and speaker diarization
- **LLM post-processing**: Automatic summarization and content analysis
- **Watch mode**: Monitor directories for new files
- **GPU acceleration**: CUDA support when available
- **Configurable**: Multiple model sizes and processing options

## Installation

1. Install the base dependencies:
```bash
pip install -r requirements.txt
```

2. For GPU support, install PyTorch with CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. Optional: Install WhisperX for advanced features:
```bash
pip install whisperx
```

## Quick Start

### Basic Usage

```bash
# Transcribe a single file
python audio_transcription/transcribe.py video.mp4

# Transcribe with custom output directory
python audio_transcription/transcribe.py --output ./transcripts audio.wav

# Use larger model for better accuracy
python audio_transcription/transcribe.py --model medium --device cuda video.mp4
```

### Advanced Features

```bash
# Enable WhisperX alignment and diarization
python audio_transcription/transcribe.py --whisperx --diarize meeting.mp4

# Watch directory for new files
python audio_transcription/transcribe.py --watch ./inbox --output ./transcripts

# Disable LLM post-processing for faster processing
python audio_transcription/transcribe.py --no-llm video.mp4
```

## Command Line Options

### Input Options
- `files`: Audio or video files to transcribe
- `--watch, -w`: Watch directory for new media files

### Output Options
- `--output, -o`: Output directory (default: ./output)

### Model Options
- `--model, -m`: Whisper model size (tiny, base, small, medium, large-v3)
- `--device`: Processing device (auto, cpu, cuda)
- `--compute-type`: Compute type (auto, int8, float16, float32)

### Transcription Options
- `--no-vad`: Disable voice activity detection
- `--beam-size`: Beam search size (default: 1)

### WhisperX Options
- `--whisperx`: Enable WhisperX word-level alignment
- `--diarize`: Enable speaker diarization (requires HF token)

### LLM Options
- `--no-llm`: Disable LLM post-processing
- `--llm-url`: LLM API base URL (default: http://localhost:11434)
- `--llm-model`: LLM model name (default: llama3.1:8b)
- `--llm-timeout`: LLM request timeout in seconds (default: 60)

## Output Files

For each input file, the pipeline generates:

- `transcript.txt`: Plain text transcript
- `transcript.json`: Detailed JSON with timing information
- `captions.srt`: SRT format captions
- `captions.vtt`: WebVTT format captions
- `audio_16k_mono.wav`: Processed audio file
- `postprocess.json`: LLM-generated summary and analysis (if enabled)

## Model Sizes

| Model | Size | Relative Speed | Accuracy |
|-------|------|----------------|----------|
| tiny | 39M | ~32x | ~60% |
| base | 74M | ~16x | ~75% |
| small | 244M | ~6x | ~85% |
| medium | 769M | ~2x | ~90% |
| large-v3 | 1550M | 1x | ~95% |

## Examples

### Transcribe a Podcast Episode
```bash
python audio_transcription/transcribe.py \
  --model medium \
  --whisperx \
  --llm-model llama3.1:8b \
  podcast_episode.mp4
```

### Process Meeting Recordings
```bash
python audio_transcription/transcribe.py \
  --model large-v3 \
  --device cuda \
  --whisperx \
  --diarize \
  --output ./meeting_transcripts \
  meeting_recording.mp4
```

### Batch Processing with Watch Mode
```bash
# Start watching for new files
python audio_transcription/transcribe.py \
  --watch ./inbox \
  --output ./transcripts \
  --model small \
  --whisperx

# In another terminal, copy files to inbox
cp *.mp4 ./inbox/
```

## Configuration

The tool can be configured through command-line arguments or by using the Python API directly. See `audio_transcription/config.py` for default values.

## Troubleshooting

### GPU Not Detected
Ensure NVIDIA drivers and CUDA toolkit are installed:
```bash
nvidia-smi  # Should show GPU information
```

### WhisperX Installation Issues
WhisperX has complex dependencies. If installation fails:
```bash
pip install whisperx --no-deps
# Then install dependencies manually based on your system
```

### Memory Issues
- Use smaller model sizes (`tiny`, `base`, `small`)
- Set `--compute-type int8` for CPU processing
- Close other memory-intensive applications

### LLM Post-Processing Fails
Ensure your LLM service is running:
```bash
# For Ollama
ollama serve

# Test connection
curl http://localhost:11434/api/generate
```

## API Usage

You can also use the transcription pipeline programmatically:

```python
from audio_transcription.config import TranscriptionConfig
from audio_transcription.transcriber import process_media_file

# Create configuration
config = TranscriptionConfig(
    asr_model="medium",
    use_whisperx=True,
    enable_llm_post=False
)

# Process a file
output_dir = process_media_file(Path("video.mp4"), config)
print(f"Transcription saved to: {output_dir}")
```

## License

This project is part of the asabaal-utils repository.