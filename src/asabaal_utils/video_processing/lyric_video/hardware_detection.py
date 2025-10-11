"""Hardware detection for GPU acceleration support."""

import subprocess
import platform
import logging
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class GPUType(Enum):
    """Supported GPU types for acceleration."""
    NVIDIA = "nvidia"
    INTEL = "intel"
    AMD = "amd"
    NONE = "none"


@dataclass
class GPUInfo:
    """GPU information for hardware acceleration."""
    gpu_type: GPUType
    name: str
    driver_version: Optional[str] = None
    cuda_version: Optional[str] = None
    memory_mb: Optional[int] = None
    
    @property
    def supports_nvenc(self) -> bool:
        """Check if GPU supports NVENC encoding."""
        return self.gpu_type == GPUType.NVIDIA
        
    @property
    def supports_quicksync(self) -> bool:
        """Check if GPU supports Intel QuickSync."""
        return self.gpu_type == GPUType.INTEL
        
    @property
    def supports_amf(self) -> bool:
        """Check if GPU supports AMD AMF."""
        return self.gpu_type == GPUType.AMD


class HardwareDetector:
    """Detect available hardware acceleration capabilities."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self._gpu_info: Optional[GPUInfo] = None
        self._ffmpeg_encoders: Optional[List[str]] = None
        
    def detect_gpu(self) -> Optional[GPUInfo]:
        """Detect available GPU and capabilities."""
        if self._gpu_info is not None:
            return self._gpu_info
            
        logger.info("Detecting GPU capabilities...")
        
        # Try NVIDIA first
        nvidia_info = self._detect_nvidia()
        if nvidia_info:
            self._gpu_info = nvidia_info
            return self._gpu_info
            
        # Try Intel
        intel_info = self._detect_intel()
        if intel_info:
            self._gpu_info = intel_info
            return self._gpu_info
            
        # Try AMD
        amd_info = self._detect_amd()
        if amd_info:
            self._gpu_info = amd_info
            return self._gpu_info
            
        logger.warning("No GPU detected, will use CPU-only processing")
        self._gpu_info = GPUInfo(gpu_type=GPUType.NONE, name="CPU Only")
        return self._gpu_info
        
    def get_available_encoders(self) -> List[str]:
        """Get list of available FFmpeg hardware encoders."""
        if self._ffmpeg_encoders is not None:
            return self._ffmpeg_encoders
            
        encoders = []
        
        try:
            # Query FFmpeg for available encoders
            result = subprocess.run(
                ["ffmpeg", "-encoders"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check for hardware encoders
                hw_encoders = {
                    "h264_nvenc": "NVIDIA H.264",
                    "hevc_nvenc": "NVIDIA H.265",
                    "h264_qsv": "Intel QuickSync H.264",
                    "hevc_qsv": "Intel QuickSync H.265",
                    "h264_amf": "AMD AMF H.264",
                    "hevc_amf": "AMD AMF H.265",
                    "h264_videotoolbox": "Apple VideoToolbox H.264",
                    "hevc_videotoolbox": "Apple VideoToolbox H.265"
                }
                
                for encoder, name in hw_encoders.items():
                    if encoder in output:
                        encoders.append(encoder)
                        logger.info(f"Found hardware encoder: {name} ({encoder})")
                        
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg.")
        except Exception as e:
            logger.error(f"Error detecting FFmpeg encoders: {e}")
            
        self._ffmpeg_encoders = encoders
        return encoders
        
    def _detect_nvidia(self) -> Optional[GPUInfo]:
        """Detect NVIDIA GPU using nvidia-smi."""
        try:
            # Check if nvidia-smi exists
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    parts = output.split(", ")
                    if len(parts) >= 3:
                        name = parts[0]
                        driver = parts[1]
                        memory_str = parts[2].replace(" MiB", "")
                        memory_mb = int(memory_str) if memory_str.isdigit() else None
                        
                        # Try to get CUDA version
                        cuda_version = self._get_cuda_version()
                        
                        logger.info(f"Detected NVIDIA GPU: {name}")
                        return GPUInfo(
                            gpu_type=GPUType.NVIDIA,
                            name=name,
                            driver_version=driver,
                            cuda_version=cuda_version,
                            memory_mb=memory_mb
                        )
                        
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Error detecting NVIDIA GPU: {e}")
            
        return None
        
    def _detect_intel(self) -> Optional[GPUInfo]:
        """Detect Intel GPU."""
        if self.platform == "linux":
            try:
                # Check for Intel GPU in lspci
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Intel' in line and ('Graphics' in line or 'GPU' in line):
                            # Extract GPU name
                            parts = line.split(': ', 1)
                            if len(parts) > 1:
                                name = parts[1].strip()
                                logger.info(f"Detected Intel GPU: {name}")
                                return GPUInfo(
                                    gpu_type=GPUType.INTEL,
                                    name=name
                                )
                                
            except Exception as e:
                logger.debug(f"Error detecting Intel GPU: {e}")
                
        elif self.platform == "darwin":
            # macOS detection would go here
            pass
            
        return None
        
    def _detect_amd(self) -> Optional[GPUInfo]:
        """Detect AMD GPU."""
        if self.platform == "linux":
            try:
                # Check for AMD GPU in lspci
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'AMD' in line and ('Graphics' in line or 'GPU' in line or 'Radeon' in line):
                            # Extract GPU name
                            parts = line.split(': ', 1)
                            if len(parts) > 1:
                                name = parts[1].strip()
                                logger.info(f"Detected AMD GPU: {name}")
                                return GPUInfo(
                                    gpu_type=GPUType.AMD,
                                    name=name
                                )
                                
            except Exception as e:
                logger.debug(f"Error detecting AMD GPU: {e}")
                
        return None
        
    def _get_cuda_version(self) -> Optional[str]:
        """Get CUDA version if available."""
        try:
            result = subprocess.run(
                ["nvcc", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line:
                        parts = line.split('release ')
                        if len(parts) > 1:
                            version = parts[1].split(',')[0]
                            return version
                            
        except FileNotFoundError:
            pass
            
        return None
        
    def recommend_encoding_settings(self) -> dict:
        """Recommend encoding settings based on hardware."""
        gpu = self.detect_gpu()
        encoders = self.get_available_encoders()
        
        settings = {
            "encoder": "libx264",  # Default software encoder
            "preset": "medium",
            "crf": 23,
            "gpu_acceleration": False
        }
        
        if gpu and gpu.gpu_type != GPUType.NONE:
            # Try to use hardware encoder
            if gpu.supports_nvenc and "h264_nvenc" in encoders:
                settings.update({
                    "encoder": "h264_nvenc",
                    "preset": "p4",  # Balanced preset for NVENC
                    "gpu_acceleration": True,
                    "rc": "vbr",  # Rate control
                    "cq": 23  # Constant quality
                })
            elif gpu.supports_quicksync and "h264_qsv" in encoders:
                settings.update({
                    "encoder": "h264_qsv",
                    "preset": "medium",
                    "gpu_acceleration": True,
                    "global_quality": 23
                })
            elif gpu.supports_amf and "h264_amf" in encoders:
                settings.update({
                    "encoder": "h264_amf",
                    "quality": "balanced",
                    "gpu_acceleration": True,
                    "rc": "vbr_peak",
                    "qp": 23
                })
                
        return settings