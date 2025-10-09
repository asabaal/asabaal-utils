"""
Configuration for audio transcription pipeline
"""

from pathlib import Path
from typing import Optional

# Directory configuration
DEFAULT_INBOX = Path("./inbox")
DEFAULT_OUTBOX = Path("./output")

# ASR model settings
DEFAULT_ASR_MODEL = "small"  # Options: tiny, base, small, medium, large-v3
DEFAULT_DEVICE = "auto"  # Options: auto, cpu, cuda
DEFAULT_COMPUTE_TYPE = "auto"  # Options: auto, int8, float16, float32

# Transcription settings
DEFAULT_USE_VAD = True  # Voice Activity Detection
DEFAULT_BEAM_SIZE = 1  # Beam search size (higher = more accurate but slower)

# WhisperX features (requires whisperx installation)
DEFAULT_USE_WHISPERX = True  # Enable word-level alignment and diarization
DEFAULT_USE_DIARIZATION = False  # Speaker diarization (requires HF token)

# LLM post-processing (optional)
DEFAULT_ENABLE_LLM_POST = True  # Enable LLM-based summarization
DEFAULT_LLM_BASE_URL = "http://localhost:11434"  # Ollama default
DEFAULT_LLM_MODEL = "llama3.1:8b"  # Model name
DEFAULT_LLM_TIMEOUT = 60  # Timeout in seconds


class TranscriptionConfig:
    """Configuration class for audio transcription pipeline"""
    
    def __init__(
        self,
        inbox: Optional[Path] = None,
        outbox: Optional[Path] = None,
        asr_model: str = DEFAULT_ASR_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        use_vad: bool = DEFAULT_USE_VAD,
        beam_size: int = DEFAULT_BEAM_SIZE,
        use_whisperx: bool = DEFAULT_USE_WHISPERX,
        use_diarization: bool = DEFAULT_USE_DIARIZATION,
        enable_llm_post: bool = DEFAULT_ENABLE_LLM_POST,
        llm_base_url: str = DEFAULT_LLM_BASE_URL,
        llm_model: str = DEFAULT_LLM_MODEL,
        llm_timeout: int = DEFAULT_LLM_TIMEOUT,
    ):
        self.inbox = inbox or DEFAULT_INBOX
        self.outbox = outbox or DEFAULT_OUTBOX
        self.asr_model = asr_model
        self.device = device
        self.compute_type = compute_type
        self.use_vad = use_vad
        self.beam_size = beam_size
        self.use_whisperx = use_whisperx
        self.use_diarization = use_diarization
        self.enable_llm_post = enable_llm_post
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model
        self.llm_timeout = llm_timeout
    
    def ensure_dirs(self):
        """Create inbox and outbox directories if they don't exist"""
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)