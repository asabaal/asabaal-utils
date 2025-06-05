"""Main lyric video generator pipeline."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Union, Generator, Tuple
import numpy as np

from .audio import AudioAnalyzer, AudioFeatures
from .lyrics import LyricProcessor
from .text import TextRenderer, TextStyle, AnimationConfig, AnimationType, AnimationEasing
from .compositor import VideoCompositor, CompositeLayer
from .encoder import OutputEncoder
from .hardware_detection import HardwareDetector

logger = logging.getLogger(__name__)


class LyricVideoGenerator:
    """Main pipeline for generating lyric videos."""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080), fps: float = 30.0):
        """Initialize generator.
        
        Args:
            resolution: Output resolution (width, height)
            fps: Output frame rate
        """
        self.resolution = resolution
        self.fps = fps
        
        # Initialize components
        self.audio_analyzer = AudioAnalyzer()
        self.lyric_processor = LyricProcessor()
        self.text_renderer = TextRenderer(resolution)
        self.compositor = VideoCompositor(resolution, fps)
        self.encoder = OutputEncoder(resolution, fps)
        
        # State
        self.audio_features: Optional[AudioFeatures] = None
        self.lyrics = None
        self.config = None
        
    def create_video(self, audio_path: Union[str, Path],
                    lyrics_path: Union[str, Path],
                    output_path: Union[str, Path],
                    background_video: Optional[Union[str, Path]] = None,
                    background_clips_dir: Optional[Union[str, Path]] = None,
                    template: str = "default",
                    custom_config: Optional[Dict] = None,
                    text_only_output: bool = False) -> str:
        """Create lyric video.
        
        Args:
            audio_path: Path to audio file
            lyrics_path: Path to lyrics file (SRT/LRC) or text
            output_path: Output video path
            background_video: Optional single background video
            background_clips_dir: Optional directory of background clips for beat-based switching
            template: Template name or path to template JSON
            custom_config: Custom configuration overrides
            text_only_output: If True, output transparent text overlay only
            
        Returns:
            Path to generated video
        """
        logger.info("Starting lyric video generation...")
        
        # Load configuration
        self.config = self._load_config(template, custom_config)
        
        # Analyze audio
        logger.info("Analyzing audio...")
        self.audio_features = self.audio_analyzer.analyze_audio(audio_path)
        
        # Process lyrics
        logger.info("Processing lyrics...")
        self.lyrics = self.lyric_processor.parse_lyrics(lyrics_path)
        
        # Align lyrics to audio if requested
        if self.config['animation_config'].get('sync_to_beats', False):
            self.lyrics = self.lyric_processor.align_to_audio(
                self.audio_features,
                snap_to_beats=True,
                snap_to_onsets=True
            )
            
        # Load background video(s) if provided
        if background_clips_dir:
            logger.info(f"Loading background clips from directory: {background_clips_dir}")
            self.compositor.load_background_clips_from_directory(background_clips_dir)
        elif background_video:
            logger.info(f"Loading single background video: {background_video}")
            self.compositor.load_background_video(background_video)
            
        # Generate frames
        frame_generator = self._generate_frames(text_only_output)
        
        # Encode video
        logger.info("Encoding video...")
        success = self.encoder.encode_video(
            frame_generator,
            audio_path,
            output_path,
            quality_preset=self.config.get('quality_preset', 'balanced')
        )
        
        if success:
            logger.info(f"Lyric video generated successfully: {output_path}")
            return str(output_path)
        else:
            raise RuntimeError("Video encoding failed")
            
    def _load_config(self, template: str, custom_config: Optional[Dict] = None) -> Dict:
        """Load configuration from template and custom overrides."""
        # Try to load template
        config = {}
        
        if template == "default":
            # Use default configuration
            config = {
                "video_config": {
                    "resolution": list(self.resolution),
                    "fps": self.fps,
                    "duration_padding": 2.0
                },
                "text_config": {
                    "font_family": "Arial",
                    "font_size": 72,
                    "color": (255, 255, 255),
                    "stroke_color": (0, 0, 0),
                    "stroke_width": 3,
                    "glow_radius": 10,
                    "glow_color": (0, 255, 0),
                    "alignment": "center"
                },
                "animation_config": {
                    "entrance_type": "fade_in",
                    "exit_type": "fade_out",
                    "sync_to_beats": True,
                    "duration": 0.5,
                    "easing": "ease_out"
                },
                "audio_reactive": {
                    "enable_beat_sync": True,
                    "enable_frequency_reactive": True
                }
            }
        else:
            # Try to load from file
            template_path = Path(template)
            if not template_path.exists():
                # Try in templates directory
                template_path = Path(__file__).parent.parent / "templates" / f"{template}.json"
                
            if template_path.exists():
                with open(template_path) as f:
                    config = json.load(f)
            else:
                logger.warning(f"Template {template} not found, using default")
                return self._load_config("default", custom_config)
                
        # Apply custom overrides
        if custom_config:
            config = self._merge_configs(config, custom_config)
            
        return config
        
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _generate_frames(self, text_only_output: bool = False) -> Generator[np.ndarray, None, None]:
        """Generate video frames."""
        if not self.audio_features or not self.lyrics:
            raise ValueError("Audio and lyrics must be loaded before generating frames")
            
        # Create text style from config
        text_config = self.config['text_config']
        style = TextStyle(
            font_family=text_config.get('font_family', 'Arial'),
            font_size=text_config.get('font_size', 72),
            color=tuple(text_config.get('color', [255, 255, 255])),
            stroke_width=text_config.get('stroke_width', 3),
            stroke_color=tuple(text_config.get('stroke_color', [0, 0, 0])),
            glow_radius=text_config.get('glow_radius', 10),
            glow_color=tuple(text_config.get('glow_color', [0, 255, 0])) if text_config.get('glow_color') else None,
            alignment=text_config.get('alignment', 'center')
        )
        
        # Create animation config
        anim_config_dict = self.config['animation_config']
        animation_config = AnimationConfig(
            entrance_type=getattr(AnimationType, anim_config_dict.get('entrance_type', 'FADE_IN').upper()),
            exit_type=getattr(AnimationType, anim_config_dict.get('exit_type', 'FADE_OUT').upper()),
            easing=getattr(AnimationEasing, anim_config_dict.get('easing', 'EASE_OUT').upper()),
            duration=anim_config_dict.get('duration', 0.5),
            sync_to_beats=anim_config_dict.get('sync_to_beats', True)
        )
        
        # Calculate video duration
        video_duration = self.audio_features.duration + self.config['video_config'].get('duration_padding', 2.0)
        total_frames = int(video_duration * self.fps)
        
        logger.info(f"Generating {total_frames} frames ({video_duration:.1f}s @ {self.fps}fps)")
        
        for frame_num in range(total_frames):
            current_time = frame_num / self.fps
            
            # Get background frame (pass beat times for smart switching)
            background = None if text_only_output else self.compositor.get_background_frame(
                current_time, 
                beat_times=self.audio_features.beats.times
            )
            
            # Get audio features at current time
            audio_features = self.audio_features.get_features_at_time(current_time)
            
            # Find active lyrics
            active_line = None
            for line in self.lyrics:
                if line.is_active(current_time):
                    active_line = line
                    break
                    
            layers = []
            
            if active_line:
                # Render text for current line
                text_img = self.text_renderer.render_lyric_line(
                    words=active_line.words,
                    current_time=current_time,
                    style=style,
                    animation_config=animation_config,
                    line_start=active_line.start_time,
                    line_end=active_line.end_time,
                    audio_features=audio_features
                )
                
                # Add text as layer
                if text_img.shape[0] > 0 and text_img.shape[1] > 0:
                    layers.append(CompositeLayer(
                        image=text_img,
                        position=(0, 0),
                        opacity=1.0
                    ))
                    
            # Composite frame
            frame = self.compositor.composite_frame(background, layers)
            
            # Apply audio-reactive effects
            if self.config['audio_reactive'].get('enable_frequency_reactive', False):
                frame = self.compositor.apply_audio_reactive_effects(frame, audio_features)
                
            yield frame
            
            # Progress logging
            if frame_num % (self.fps * 5) == 0:  # Every 5 seconds
                progress = (frame_num / total_frames) * 100
                logger.info(f"Generated {frame_num}/{total_frames} frames ({progress:.1f}%)")
                
    def get_system_info(self) -> Dict:
        """Get system information for debugging."""
        hardware = HardwareDetector()
        gpu_info = hardware.detect_gpu()
        
        return {
            'resolution': self.resolution,
            'fps': self.fps,
            'gpu_info': {
                'type': gpu_info.gpu_type.value if gpu_info else None,
                'name': gpu_info.name if gpu_info else None,
                'supports_acceleration': gpu_info.gpu_type.value != 'none' if gpu_info else False
            },
            'encoding_info': self.encoder.get_encoding_info()
        }