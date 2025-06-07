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
from .effects import MotionEffectRenderer, get_effect_by_name, get_effect_combination
from .section_manager import SectionManager, SectionType

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
        self.motion_effect_renderer = MotionEffectRenderer(resolution)
        self.section_manager = SectionManager()
        
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
                    text_only_output: bool = False,
                    start_time: Optional[float] = None,
                    end_time: Optional[float] = None,
                    structure_file: Optional[Union[str, Path]] = None) -> str:
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
            start_time: Optional start time in seconds for testing specific sections
            end_time: Optional end time in seconds for testing specific sections
            structure_file: Optional path to song structure file for custom section definitions
            
        Returns:
            Path to generated video
        """
        logger.info("Starting lyric video generation...")
        
        # Load configuration
        self.config = self._load_config(template, custom_config)
        
        # Analyze audio
        logger.info("Analyzing audio...")
        self.audio_features = self.audio_analyzer.analyze_audio(audio_path)
        
        # Apply time range filtering if specified
        if start_time is not None or end_time is not None:
            logger.info(f"Applying time range filter: {start_time}s to {end_time or 'end'}s")
            self.audio_features = self._filter_audio_features_by_time(
                self.audio_features, start_time, end_time
            )
            
        # Process lyrics
        logger.info("Processing lyrics...")
        self.lyrics = self.lyric_processor.parse_lyrics(lyrics_path)
        
        # Apply time range filtering to lyrics if specified
        if start_time is not None or end_time is not None:
            self.lyrics = self._filter_lyrics_by_time(self.lyrics, start_time, end_time)
        
        # Align lyrics to audio if requested
        if self.config['animation_config'].get('sync_to_beats', False):
            self.lyrics = self.lyric_processor.align_to_audio(
                self.audio_features,
                snap_to_beats=True,
                snap_to_onsets=True
            )
            
        # Load song sections for visual variation
        if structure_file:
            logger.info(f"Loading song sections from structure file: {structure_file}")
            detected_sections = self.section_manager.load_structure_from_file(
                structure_file, self.audio_features.duration
            )
        else:
            logger.info("Detecting song sections for visual variation...")
            detected_sections = self.section_manager.detect_sections_from_audio(
                self.audio_features, self.lyrics
            )
        self.section_manager.log_section_transitions(self.audio_features.duration)
            
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
            shadow_offset=tuple(text_config.get('shadow_offset', [2, 2])) if text_config.get('shadow_offset') else None,
            shadow_blur=text_config.get('shadow_blur', 5),
            shadow_opacity=text_config.get('shadow_opacity', 0.5),
            line_spacing=text_config.get('line_spacing', 1.2),
            alignment=text_config.get('alignment', 'center'),
            vertical_position=text_config.get('vertical_position', 'center'),
            dynamic_positioning=text_config.get('dynamic_positioning', False),
            motion_tracking=text_config.get('motion_tracking', False)
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
            
            # Detect motion in background and enhance it
            motion_features = {}
            if background is not None:
                motion_magnitude, motion_vector = self.compositor.detect_motion(background)
                motion_features = self.compositor.get_motion_features()
                # Enhance background with motion-based effects
                background = self.compositor.enhance_background_motion(background, motion_features)
            
            # Get audio features at current time
            audio_features = self.audio_features.get_features_at_time(current_time)
            
            # Merge motion features with audio features for text rendering
            if motion_features:
                audio_features.update(motion_features)
            
            # Find active lyrics
            active_line = None
            for line in self.lyrics:
                if line.is_active(current_time):
                    active_line = line
                    break
                    
            layers = []
            
            if active_line:
                # Get section-based effects configuration
                base_effects = {
                    'ambient_glow': True,
                    'dynamic_colors': True,
                    'lighting_effects': True,
                    'energy_bursts': True,
                    'wave_effect': False,
                    'chromatic_aberration': False
                }
                section_effects = self.section_manager.get_text_effects_config(current_time, base_effects)
                
                # Apply section-based style modifications
                style_mods = self.section_manager.get_text_style_modifications(current_time, style)
                modified_style = style
                if style_mods.get('dynamic_positioning'):
                    modified_style.dynamic_positioning = True
                if style_mods.get('motion_tracking'):
                    modified_style.motion_tracking = True
                if 'vertical_position' in style_mods:
                    modified_style.vertical_position = style_mods['vertical_position']
                
                # Render text for current line with section-based configuration
                text_img = self.text_renderer.render_lyric_line(
                    words=active_line.words,
                    current_time=current_time,
                    style=modified_style,
                    animation_config=animation_config,
                    line_start=active_line.start_time,
                    line_end=active_line.end_time,
                    audio_features=audio_features,
                    effects_config=section_effects
                )
                
                # Apply motion effects to text
                text_img = self._apply_motion_effects(text_img, current_time, active_line, audio_features)
                
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
    
    def _apply_motion_effects(self, text_img: np.ndarray, current_time: float, 
                            active_line, audio_features: Dict) -> np.ndarray:
        """Apply motion effects to text image."""
        if 'motion_effects' not in self.config:
            return text_img
            
        motion_config = self.config['motion_effects']
        
        # Apply individual effects
        for effect_config in motion_config.get('individual_effects', []):
            effect_name = effect_config['name']
            effect_duration = effect_config.get('duration', 1.0)
            effect_timing = effect_config.get('timing', 'active')
            
            # Calculate effect start time based on timing
            if effect_timing == 'entrance':
                effect_start = active_line.start_time
            elif effect_timing == 'exit':
                effect_start = active_line.end_time - effect_duration
            elif effect_timing == 'beat_trigger':
                # Only apply on beats
                if not audio_features.get('on_beat', False):
                    continue
                effect_start = current_time
            else:  # 'active'
                effect_start = active_line.start_time
            
            # Calculate relative time for this effect
            effect_time = current_time - effect_start
            
            # Skip if outside effect duration
            if effect_time < 0 or effect_time > effect_duration:
                continue
                
            # Get effect from library
            try:
                motion_effect = get_effect_by_name(effect_name, effect_duration)
                text_img = self.motion_effect_renderer.apply_effect(
                    text_img, motion_effect, effect_time, audio_features
                )
            except Exception as e:
                logger.debug(f"Error applying motion effect {effect_name}: {e}")
                
        # Apply effect combination if specified
        combination_name = motion_config.get('effect_combination')
        if combination_name:
            try:
                effect_combination = get_effect_combination(combination_name)
                for motion_effect in effect_combination:
                    # Calculate effect time based on line timing
                    effect_time = current_time - active_line.start_time
                    if 0 <= effect_time <= motion_effect.duration:
                        text_img = self.motion_effect_renderer.apply_effect(
                            text_img, motion_effect, effect_time, audio_features
                        )
            except Exception as e:
                logger.debug(f"Error applying effect combination {combination_name}: {e}")
                
        return text_img
        
    def _filter_audio_features_by_time(self, audio_features: AudioFeatures, 
                                     start_time: Optional[float], 
                                     end_time: Optional[float]) -> AudioFeatures:
        """Filter audio features to a specific time range.
        
        Args:
            audio_features: Original audio features
            start_time: Start time in seconds (None for no start filter)
            end_time: End time in seconds (None for no end filter)
            
        Returns:
            Filtered audio features
        """
        # For now, return the original features but adjust the duration
        # In a full implementation, you'd filter the actual feature arrays
        filtered_features = audio_features
        
        if start_time is not None:
            # Shift timestamps by start_time
            filtered_features.start_offset = start_time
            
        if end_time is not None:
            # Truncate duration
            original_duration = audio_features.duration
            new_duration = end_time - (start_time or 0)
            filtered_features.duration = min(new_duration, original_duration)
            
        return filtered_features
        
    def _filter_lyrics_by_time(self, lyrics, start_time: Optional[float], 
                              end_time: Optional[float]):
        """Filter lyrics to a specific time range.
        
        Args:
            lyrics: List of lyric lines
            start_time: Start time in seconds (None for no start filter)
            end_time: End time in seconds (None for no end filter)
            
        Returns:
            Filtered lyrics list
        """
        if not lyrics:
            return lyrics
            
        filtered_lyrics = []
        start_offset = start_time or 0
        
        for line in lyrics:
            # Check if line overlaps with the time range
            line_start = line.start_time
            line_end = line.end_time
            
            # Skip lines that are completely before the start time
            if end_time and line_start >= end_time:
                continue
                
            # Skip lines that are completely after the end time  
            if start_time and line_end <= start_time:
                continue
                
            # Adjust line timing relative to the new start
            adjusted_line = line.copy() if hasattr(line, 'copy') else line
            adjusted_line.start_time = max(0, line_start - start_offset)
            adjusted_line.end_time = line_end - start_offset
            
            # Adjust word timings if they exist
            if hasattr(adjusted_line, 'words') and adjusted_line.words:
                for word in adjusted_line.words:
                    if hasattr(word, 'start_time'):
                        word.start_time = max(0, word.start_time - start_offset)
                    if hasattr(word, 'end_time'):
                        word.end_time = word.end_time - start_offset
                        
            filtered_lyrics.append(adjusted_line)
            
        return filtered_lyrics
                
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