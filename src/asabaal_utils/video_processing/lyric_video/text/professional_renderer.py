"""
Professional Text Renderer for Asabaal Utils Lyric Video Creator
Integrates advanced text animation features with the existing system
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import math
from scipy import interpolate
import json
import time

from ..text.renderer import TextRenderer, TextStyle
from ..text.animations import AnimationType, AnimationState


# ==================== INTEGRATED KINETIC TYPOGRAPHY ====================

@dataclass
class CharacterTransform:
    """Per-character transform state"""
    position: Tuple[float, float]
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    opacity: float = 1.0
    skew: Tuple[float, float] = (0.0, 0.0)
    color: Optional[Tuple[int, int, int]] = None
    glow_intensity: float = 0.0
    blur: float = 0.0
    
    def to_matrix(self) -> np.ndarray:
        """Convert transform to 3x3 transformation matrix"""
        T = np.array([[1, 0, self.position[0]],
                      [0, 1, self.position[1]],
                      [0, 0, 1]], dtype=np.float32)
        
        angle_rad = math.radians(self.rotation)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        R = np.array([[cos_a, -sin_a, 0],
                      [sin_a, cos_a, 0],
                      [0, 0, 1]], dtype=np.float32)
        
        S = np.array([[self.scale[0], 0, 0],
                      [0, self.scale[1], 0],
                      [0, 0, 1]], dtype=np.float32)
        
        Sk = np.array([[1, math.tan(math.radians(self.skew[0])), 0],
                       [math.tan(math.radians(self.skew[1])), 1, 0],
                       [0, 0, 1]], dtype=np.float32)
        
        return T @ R @ Sk @ S


class KineticTypography:
    """Advanced per-character animation system integrated with lyric videos"""
    
    def __init__(self):
        self.character_states: List[CharacterTransform] = []
        self.character_bounds: List[Tuple[int, int, int, int]] = []
        self.text: str = ""
        self.base_position: Tuple[int, int] = (0, 0)
        

    def _get_character_metrics(self, font, font_scale: float, thickness: int = 2):
        """Get actual character metrics for smart spacing"""
        if hasattr(self, '_char_metrics_cache'):
            return self._char_metrics_cache
            
        # These are measured actual widths and offsets for common characters
        # at font_scale 2.5 - we'll scale proportionally
        base_scale = 2.5
        scale_factor = font_scale / base_scale
        
        base_metrics = {
            'A': {'actual': 42, 'offset': 7},
            'B': {'actual': 36, 'offset': 9},
            'C': {'actual': 40, 'offset': 7},
            'D': {'actual': 40, 'offset': 9},
            'E': {'actual': 36, 'offset': 9},
            'F': {'actual': 32, 'offset': 9},
            'G': {'actual': 43, 'offset': 7},
            'H': {'actual': 38, 'offset': 9},
            'I': {'actual': 3, 'offset': 9},
            'J': {'actual': 30, 'offset': 2},
            'K': {'actual': 38, 'offset': 9},
            'L': {'actual': 33, 'offset': 9},
            'M': {'actual': 45, 'offset': 9},
            'N': {'actual': 38, 'offset': 9},
            'O': {'actual': 43, 'offset': 7},
            'P': {'actual': 36, 'offset': 9},
            'Q': {'actual': 43, 'offset': 7},
            'R': {'actual': 38, 'offset': 9},
            'S': {'actual': 38, 'offset': 7},
            'T': {'actual': 39, 'offset': 2},
            'U': {'actual': 38, 'offset': 9},
            'V': {'actual': 42, 'offset': 2},
            'W': {'actual': 57, 'offset': 2},
            'X': {'actual': 42, 'offset': 2},
            'Y': {'actual': 42, 'offset': 2},
            'Z': {'actual': 38, 'offset': 7},
            # Lowercase
            'i': {'actual': 5, 'offset': 8},
            'l': {'actual': 3, 'offset': 9},
            # Numbers
            '1': {'actual': 16, 'offset': 14},
            # Punctuation
            '.': {'actual': 8, 'offset': 9},
            ',': {'actual': 8, 'offset': 9},
            '!': {'actual': 8, 'offset': 9},
            '?': {'actual': 30, 'offset': 7},
            ':': {'actual': 8, 'offset': 9},
            ';': {'actual': 8, 'offset': 9},
            "'": {'actual': 3, 'offset': 9},
            '"': {'actual': 23, 'offset': 9},
            ' ': {'actual': 0, 'offset': 0},  # Space
        }
        
        # Scale metrics to current font size
        metrics = {}
        for char, data in base_metrics.items():
            metrics[char] = {
                'actual': int(data['actual'] * scale_factor),
                'offset': int(data['offset'] * scale_factor)
            }
        
        # For unknown characters, fall back to OpenCV measurements
        self._char_metrics_cache = metrics
        return metrics


    def prepare_text(self, text: str, font, font_scale: float, 
                    base_position: Tuple[int, int]):
        """Prepare text with smart manual character spacing"""
        self.text = text
        self.character_states.clear()
        self.character_bounds.clear()
        
        # Get character metrics
        metrics = self._get_character_metrics(font, font_scale)
        
        # Calculate positions using actual widths
        positions = []
        current_x = 0
        char_spacing = int(font_scale * 3)  # Base spacing between characters
        
        for i, char in enumerate(text):
            if char in metrics:
                # Use known metrics
                char_metrics = metrics[char]
                actual_width = char_metrics['actual']
                offset = char_metrics['offset']
            else:
                # Fall back to OpenCV for unknown characters
                (opencv_width, height), _ = cv2.getTextSize(char, font, font_scale, 2)
                # Estimate actual width as 75% of OpenCV width
                actual_width = int(opencv_width * 0.75)
                offset = int(opencv_width * 0.15)
            
            # Store position adjusted for offset
            positions.append({
                'draw_x': current_x - offset,
                'actual_x': current_x,
                'width': actual_width
            })
            
            # Move to next character
            current_x += actual_width + char_spacing
        
        # Remove last spacing
        if positions:
            total_width = current_x - char_spacing
        else:
            total_width = 0
        
        # Center the text
        start_x = base_position[0] - total_width // 2
        self.base_position = (start_x, base_position[1])
        
        # Create character states with corrected positions
        for i, (char, pos_data) in enumerate(zip(text, positions)):
            # Character bounds relative to text start
            self.character_bounds.append((
                pos_data['actual_x'], 0, 
                pos_data['width'], 50  # Approximate height
            ))
            
            # Absolute position for drawing
            char_pos = (start_x + pos_data['draw_x'], base_position[1])
            self.character_states.append(CharacterTransform(position=char_pos))


    def animate_wave(self, progress: float, amplitude: float = 30, frequency: float = 2.0, 
                     speed: float = 2.0, vertical: bool = True):
        """Animate characters in a wave pattern"""
        for i, state in enumerate(self.character_states):
            phase = (i / len(self.text)) * frequency * math.pi
            offset = amplitude * math.sin(phase + progress * speed * math.pi * 2)
            
            if vertical:
                state.position = (state.position[0], self.base_position[1] + offset)
            else:
                state.position = (self.base_position[0] + self.character_bounds[i][0] + offset, 
                                state.position[1])
    
    def animate_cascade(self, progress: float, delay_factor: float = 0.05, 
                       drop_height: float = 200):
        """Cascade animation with staggered timing"""
        for i, state in enumerate(self.character_states):
            # Avoid division by zero
            denominator = 1 - delay_factor * len(self.text)
            if denominator <= 0:
                denominator = 0.1  # Fallback to prevent division by zero
            char_progress = max(0, min(1, (progress - i * delay_factor) / denominator))
            eased_progress = self._ease_out_bounce(char_progress)
            
            start_y = self.base_position[1] - drop_height
            end_y = self.base_position[1]
            
            state.position = (self.base_position[0] + self.character_bounds[i][0],
                            start_y + (end_y - start_y) * eased_progress)
            state.opacity = char_progress
            state.rotation = (1 - eased_progress) * 360
    
    def animate_spiral(self, progress: float, radius: float = 100, rotations: float = 2.0):
        """Animate characters in a spiral pattern"""
        center_x = self.base_position[0] + sum(b[2] for b in self.character_bounds) // 2
        center_y = self.base_position[1]
        
        for i, state in enumerate(self.character_states):
            t = (i / len(self.text)) + progress * rotations
            angle = t * 2 * math.pi
            
            r = radius * (1 - progress) + 10
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            
            state.position = (x, y)
            state.rotation = math.degrees(angle) + 90
            state.scale = (1 - progress * 0.5, 1 - progress * 0.5)
            state.opacity = max(0, 1 - progress)
    
    def animate_glitch(self, progress: float, intensity: float = 1.0):
        """Digital glitch effect"""
        for i, state in enumerate(self.character_states):
            if np.random.random() < intensity * 0.3:
                state.position = (
                    self.base_position[0] + self.character_bounds[i][0] + np.random.randint(-20, 20) * intensity,
                    self.base_position[1] + np.random.randint(-10, 10) * intensity
                )
                if np.random.random() < 0.5:
                    state.color = (255, 0, 0) if np.random.random() < 0.5 else (0, 255, 255)
                state.scale = (1 + np.random.uniform(-0.2, 0.2) * intensity,
                             1 + np.random.uniform(-0.2, 0.2) * intensity)
            else:
                state.position = (self.base_position[0] + self.character_bounds[i][0], 
                                self.base_position[1])
                state.color = None
                state.scale = (1.0, 1.0)
    
    def _ease_out_bounce(self, t: float) -> float:
        """Bounce easing function"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    def render(self, frame: np.ndarray, font, font_scale: float, thickness: int = 2,
               base_color: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
        """Render kinetic text to frame"""
        result = frame.copy()
        
        for i, (char, state) in enumerate(zip(self.text, self.character_states)):
            if state.opacity <= 0:
                continue
            
            char_size = cv2.getTextSize(char, font, font_scale, thickness)[0]
            # Make buffer larger to accommodate rotations and scaling
            buffer_multiplier = 4 if state.rotation != 0 or state.scale != (1.0, 1.0) else 3
            char_img = np.zeros((char_size[1] * buffer_multiplier, char_size[0] * buffer_multiplier, 4), dtype=np.uint8)
            
            color = state.color if state.color else base_color
            
            # For narrow characters like 'I', we need better centering
            # Get the actual text bounds to center properly
            (text_width, text_height), baseline = cv2.getTextSize(char, font, font_scale, thickness)
            
            # Center character in buffer - but account for OpenCV's text positioning
            # OpenCV draws from bottom-left, and narrow chars like 'I' need special handling
            center_x = (char_img.shape[1] - text_width) // 2
            center_y = (char_img.shape[0] + text_height) // 2
            
            # No offset needed - positioning is handled in prepare_text
            cv2.putText(char_img, char, (center_x, center_y), 
                       font, font_scale, (*color, int(255 * state.opacity)), thickness)
            
            if state.blur > 0:
                char_img = cv2.GaussianBlur(char_img, (0, 0), state.blur)
            
            if state.glow_intensity > 0:
                glow = cv2.GaussianBlur(char_img, (21, 21), 0)
                char_img = cv2.addWeighted(char_img, 1.0, glow, state.glow_intensity, 0)
            
            transform_matrix = state.to_matrix()
            h, w = char_img.shape[:2]
            transformed = cv2.warpAffine(char_img, transform_matrix[:2], (frame.shape[1], frame.shape[0]))
            
            alpha = transformed[:, :, 3:4] / 255.0
            for c in range(3):
                result[:, :, c] = result[:, :, c] * (1 - alpha[:, :, 0]) + transformed[:, :, c] * alpha[:, :, 0]
        
        return result


# ==================== INTEGRATED PRECISION SYNC ====================

@dataclass
class SyncPoint:
    """Precise synchronization point"""
    time: float
    label: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Syllable:
    """Syllable with timing information"""
    text: str
    start_time: float
    end_time: float
    phoneme: Optional[str] = None
    stress: float = 0.5


class PrecisionSyncSystem:
    """Advanced synchronization system integrated with audio analysis"""
    
    def __init__(self):
        self.sync_points: List[SyncPoint] = []
        self.syllables: List[Syllable] = []
        self.bpm: Optional[float] = None
        self.offset: float = 0.0
        self.fps: float = 30.0
        
    def set_bpm(self, bpm: float, offset: float = 0.0):
        """Set BPM for beat synchronization"""
        self.bpm = bpm
        self.offset = offset
        
    def add_sync_point(self, time: float, label: str, **data):
        """Add a synchronization point"""
        self.sync_points.append(SyncPoint(time, label, data))
        self.sync_points.sort(key=lambda x: x.time)
        
    def add_syllable(self, text: str, start_time: float, end_time: float, 
                     phoneme: Optional[str] = None, stress: float = 0.5):
        """Add syllable timing"""
        self.syllables.append(Syllable(text, start_time, end_time, phoneme, stress))
        
    def generate_beat_sync_points(self, duration: float):
        """Generate sync points at musical beats"""
        if not self.bpm:
            return
            
        beat_duration = 60.0 / self.bpm
        current_time = self.offset
        beat_count = 1
        
        while current_time < duration:
            bar = (beat_count - 1) // 4 + 1
            beat_in_bar = (beat_count - 1) % 4 + 1
            
            self.add_sync_point(
                current_time,
                f"beat_{beat_count}",
                bar=bar,
                beat=beat_in_bar,
                is_downbeat=(beat_in_bar == 1)
            )
            
            current_time += beat_duration
            beat_count += 1
    
    def get_sync_at_time(self, time: float) -> Optional[SyncPoint]:
        """Get sync point at or just before given time"""
        for i in range(len(self.sync_points) - 1, -1, -1):
            if self.sync_points[i].time <= time:
                return self.sync_points[i]
        return None
    
    def get_syllable_at_time(self, time: float) -> Optional[Syllable]:
        """Get active syllable at given time"""
        for syllable in self.syllables:
            if syllable.start_time <= time <= syllable.end_time:
                return syllable
        return None


# ==================== INTEGRATED PATH AND LAYOUT ====================

class TextPath:
    """Define custom paths for text animation"""
    
    @staticmethod
    def create_arc(center: Tuple[float, float], radius: float, 
                   start_angle: float, end_angle: float, num_points: int = 50) -> List[Tuple[float, float]]:
        """Create an arc path"""
        angles = np.linspace(math.radians(start_angle), math.radians(end_angle), num_points)
        points = []
        for angle in angles:
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        return points
    
    @staticmethod
    def create_bezier(control_points: List[Tuple[float, float]], num_points: int = 50) -> List[Tuple[float, float]]:
        """Create a bezier curve path"""
        control_points = np.array(control_points)
        t = np.linspace(0, 1, num_points)
        
        if len(control_points) == 4:
            t = t.reshape(-1, 1)
            curve = ((1-t)**3 * control_points[0] +
                     3*(1-t)**2*t * control_points[1] +
                     3*(1-t)*t**2 * control_points[2] +
                     t**3 * control_points[3])
        else:
            tck, u = interpolate.splprep([control_points[:, 0], control_points[:, 1]], s=0, k=min(3, len(control_points)-1))
            curve = np.array(interpolate.splev(t, tck)).T
            
        return [(x, y) for x, y in curve]
    
    @staticmethod
    def create_spiral(center: Tuple[float, float], start_radius: float, 
                      end_radius: float, rotations: float, num_points: int = 100) -> List[Tuple[float, float]]:
        """Create a spiral path"""
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            angle = t * rotations * 2 * math.pi
            radius = start_radius + (end_radius - start_radius) * t
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        return points


class AdvancedTextLayout:
    """Advanced text layout engine"""
    
    def __init__(self):
        self.kerning_pairs: Dict[Tuple[str, str], float] = {
            ('A', 'V'): -0.1, ('A', 'W'): -0.1, ('A', 'Y'): -0.1,
            ('V', 'A'): -0.1, ('W', 'A'): -0.1, ('Y', 'A'): -0.1,
            ('T', 'o'): -0.05, ('T', 'a'): -0.05, ('T', 'e'): -0.05,
        }
    
    def layout_on_path(self, text: str, path: List[Tuple[float, float]], 
                      font, font_scale: float) -> List[Tuple[str, Tuple[float, float], float]]:
        """Layout text along a path"""
        if not path or not text:
            return []
        
        total_length = 0
        char_widths = []
        for char in text:
            width = cv2.getTextSize(char, font, font_scale, 2)[0][0]
            char_widths.append(width)
            total_length += width
        
        path_length = 0
        for i in range(1, len(path)):
            dx = path[i][0] - path[i-1][0]
            dy = path[i][1] - path[i-1][1]
            path_length += math.sqrt(dx*dx + dy*dy)
        
        char_positions = []
        current_length = 0
        path_index = 0
        path_progress = 0
        
        for i, (char, width) in enumerate(zip(text, char_widths)):
            target_length = (current_length + width/2) / total_length * path_length
            
            while path_index < len(path) - 1:
                segment_start = path[path_index]
                segment_end = path[path_index + 1]
                dx = segment_end[0] - segment_start[0]
                dy = segment_end[1] - segment_start[1]
                segment_length = math.sqrt(dx*dx + dy*dy)
                
                if path_progress + segment_length >= target_length:
                    t = (target_length - path_progress) / segment_length
                    x = segment_start[0] + t * dx
                    y = segment_start[1] + t * dy
                    angle = math.degrees(math.atan2(dy, dx))
                    char_positions.append((char, (x, y), angle))
                    break
                
                path_progress += segment_length
                path_index += 1
            
            current_length += width
        
        return char_positions


# ==================== INTEGRATED 3D TRANSFORMS ====================

class Transform3D:
    """3D transformation system for text"""
    
    @staticmethod
    def apply_3d_transform(image: np.ndarray, rotation: Tuple[float, float, float],
                          translation: Tuple[float, float, float] = (0, 0, 0),
                          scale: float = 1.0, perspective: bool = True) -> np.ndarray:
        """Apply 3D transformation to image"""
        h, w = image.shape[:2]
        
        corners_3d = np.array([
            [-w/2, -h/2, 0],
            [w/2, -h/2, 0],
            [w/2, h/2, 0],
            [-w/2, h/2, 0]
        ]) * scale
        
        # Apply rotation
        rx, ry, rz = [math.radians(angle) for angle in rotation]
        
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(rx), -math.sin(rx)],
            [0, math.sin(rx), math.cos(rx)]
        ])
        
        Ry = np.array([
            [math.cos(ry), 0, math.sin(ry)],
            [0, 1, 0],
            [-math.sin(ry), 0, math.cos(ry)]
        ])
        
        Rz = np.array([
            [math.cos(rz), -math.sin(rz), 0],
            [math.sin(rz), math.cos(rz), 0],
            [0, 0, 1]
        ])
        
        R = Rz @ Ry @ Rx
        rotated = corners_3d @ R.T
        
        rotated += np.array(translation)
        
        camera_distance = 500
        rotated[:, 2] += camera_distance
        
        if perspective:
            projected = rotated.copy()
            projected[:, 0] = (projected[:, 0] / projected[:, 2]) * camera_distance + w/2
            projected[:, 1] = (projected[:, 1] / projected[:, 2]) * camera_distance + h/2
        else:
            projected = rotated + np.array([w/2, h/2, 0])
        
        src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst_pts = np.float32(projected[:, :2])
        
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        transformed = cv2.warpPerspective(image, M, (w, h))
        
        return transformed


# ==================== INTEGRATED TIMELINE ====================

@dataclass
class Keyframe:
    """Animation keyframe"""
    time: float
    value: Any
    interpolation: str = "linear"
    bezier_handles: Optional[Tuple[float, float, float, float]] = None


class Timeline:
    """Visual timeline system for animation"""
    
    def __init__(self, duration: float, fps: float = 30):
        self.duration = duration
        self.fps = fps
        self.tracks: Dict[str, List[Keyframe]] = {}
        
    def add_keyframe(self, track: str, time: float, value: Any, 
                     interpolation: str = "linear", bezier_handles=None):
        """Add keyframe to track"""
        if track not in self.tracks:
            self.tracks[track] = []
        
        keyframe = Keyframe(time, value, interpolation, bezier_handles)
        self.tracks[track].append(keyframe)
        self.tracks[track].sort(key=lambda k: k.time)
    
    def get_value(self, track: str, time: float) -> Any:
        """Get interpolated value at time"""
        if track not in self.tracks or not self.tracks[track]:
            return None
        
        keyframes = self.tracks[track]
        
        before = None
        after = None
        
        for kf in keyframes:
            if kf.time <= time:
                before = kf
            elif kf.time > time and after is None:
                after = kf
                break
        
        if before is None:
            return keyframes[0].value
        if after is None:
            return before.value
        
        if before.interpolation == "step":
            return before.value
        
        t = (time - before.time) / (after.time - before.time)
        
        if before.interpolation == "bezier" and before.bezier_handles:
            p0, p1, p2, p3 = 0, before.bezier_handles[1], before.bezier_handles[2], 1
            t = self._cubic_bezier(t, p0, p1, p2, p3)
        
        if isinstance(before.value, (int, float)):
            return before.value + t * (after.value - before.value)
        elif isinstance(before.value, tuple):
            return tuple(b + t * (a - b) for b, a in zip(before.value, after.value))
        else:
            return before.value if t < 0.5 else after.value
    
    def _cubic_bezier(self, t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """Calculate cubic bezier curve"""
        return (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3


# ==================== EXTENDED TEXT STYLE ====================

@dataclass
class ProfessionalTextStyle(TextStyle):
    """Extended text style with professional features"""
    # Professional additions
    kinetic_enabled: bool = False
    kinetic_animation: Optional[str] = None
    path_animation: Optional[Dict] = None
    transform_3d: Optional[Dict] = None
    precision_sync: Optional[Dict] = None
    use_timeline: bool = False


# ==================== PROFESSIONAL TEXT RENDERER ====================

class ProfessionalTextRenderer(TextRenderer):
    """Professional text renderer that extends the base TextRenderer"""
    
    def __init__(self, style: Optional[ProfessionalTextStyle] = None, resolution: Tuple[int, int] = (1920, 1080)):
        super().__init__()
        self.style = style or ProfessionalTextStyle()
        self.resolution = resolution
        self.kinetic = KineticTypography()
        self.sync_system = PrecisionSyncSystem()
        self.layout_engine = AdvancedTextLayout()
        self.timeline = Timeline(duration=10.0)  # Default duration
        
    def setup_from_config(self, config: Dict[str, Any]):
        """Setup renderer from configuration"""
        if "style" in config:
            style_config = config["style"]
            self.style = ProfessionalTextStyle(**style_config)
        
        if "sync" in config:
            sync_config = config["sync"]
            if "bpm" in sync_config:
                self.sync_system.set_bpm(sync_config["bpm"], sync_config.get("offset", 0))
            if "syllables" in sync_config:
                for syl in sync_config["syllables"]:
                    self.sync_system.add_syllable(**syl)
        
        if "timeline" in config:
            timeline_config = config["timeline"]
            self.timeline = Timeline(timeline_config.get("duration", 10.0))
            for track_name, keyframes in timeline_config.get("tracks", {}).items():
                for kf in keyframes:
                    self.timeline.add_keyframe(track_name, **kf)
    
    def render_professional_text(self, text: str, frame: np.ndarray, 
                               current_time: float, position: Tuple[int, int],
                               line_duration: Optional[float] = None) -> np.ndarray:
        """Render text with professional effects"""
        result = frame.copy()
        
        # Get font parameters
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.style.font_size / 48.0  # Normalize font scale
        
        # Check if kinetic animation is enabled
        if self.style.kinetic_enabled and self.style.kinetic_animation:
            self.kinetic.prepare_text(text, font, font_scale, position)
            
            # Get animation progress from timeline or calculate
            progress = self.timeline.get_value("kinetic_progress", current_time)
            if progress is None:
                # Use line duration if available, otherwise use a sensible default
                if line_duration and line_duration > 0:
                    progress = min(1.0, current_time / line_duration)
                else:
                    progress = (current_time % 2.0) / 2.0  # Fallback 2-second loop
            
            # Apply kinetic animation
            if self.style.kinetic_animation == "wave":
                self.kinetic.animate_wave(progress)
            elif self.style.kinetic_animation == "cascade":
                self.kinetic.animate_cascade(progress)
            elif self.style.kinetic_animation == "spiral":
                self.kinetic.animate_spiral(progress)
            elif self.style.kinetic_animation == "glitch":
                self.kinetic.animate_glitch(progress)
            
            result = self.kinetic.render(result, font, font_scale, 
                                       thickness=max(1, self.style.stroke_width),
                                       base_color=self.style.color)
        
        # Apply path animation if enabled
        elif self.style.path_animation:
            path_config = self.style.path_animation
            path_type = path_config.get("type", "arc")
            
            if path_type == "arc":
                path = TextPath.create_arc(**path_config.get("params", {}))
            elif path_type == "bezier":
                path = TextPath.create_bezier(**path_config.get("params", {}))
            else:
                path = TextPath.create_arc((position[0], position[1]), 200, -30, 30)
            
            char_positions = self.layout_engine.layout_on_path(text, path, font, font_scale)
            
            for char, pos, angle in char_positions:
                cv2.putText(result, char, (int(pos[0]), int(pos[1])), 
                           font, font_scale, self.style.color, 
                           max(1, self.style.stroke_width))
        
        # Apply 3D transform if enabled
        elif self.style.transform_3d:
            # Create text on temporary surface
            text_size = cv2.getTextSize(text, font, font_scale, 
                                       max(1, self.style.stroke_width))[0]
            text_img = np.zeros((text_size[1] * 2, text_size[0] * 2, 4), dtype=np.uint8)
            
            cv2.putText(text_img, text, (text_size[0]//2, int(text_size[1] * 1.5)), 
                       font, font_scale, (*self.style.color, 255), 
                       max(1, self.style.stroke_width))
            
            # Get 3D parameters from timeline or config
            rotation = self.style.transform_3d.get("rotation", (0, 0, 0))
            if self.style.use_timeline:
                rot_x = self.timeline.get_value("rotation_x", current_time) or rotation[0]
                rot_y = self.timeline.get_value("rotation_y", current_time) or rotation[1]
                rot_z = self.timeline.get_value("rotation_z", current_time) or rotation[2]
                rotation = (rot_x, rot_y, rot_z)
            
            # Apply 3D transform
            transformed = Transform3D.apply_3d_transform(text_img, rotation)
            
            # Composite onto result
            y1 = max(0, position[1] - text_size[1])
            y2 = min(result.shape[0], y1 + transformed.shape[0])
            x1 = max(0, position[0] - text_size[0]//2)
            x2 = min(result.shape[1], x1 + transformed.shape[1])
            
            if y2 > y1 and x2 > x1:
                roi = result[y1:y2, x1:x2]
                transformed_roi = transformed[:y2-y1, :x2-x1]
                
                if transformed_roi.shape[2] == 4:
                    alpha = transformed_roi[:, :, 3:4] / 255.0
                    for c in range(3):
                        roi[:, :, c] = roi[:, :, c] * (1 - alpha[:, :, 0]) + transformed_roi[:, :, c] * alpha[:, :, 0]
                else:
                    result[y1:y2, x1:x2] = transformed_roi[:, :, :3]
        
        else:
            # Use base renderer for standard text
            return super().render_lyric_line(
                line=text,
                frame=frame,
                y_position=position[1],
                animation_state=AnimationState(
                    position=position,
                    opacity=1.0,
                    scale=(1.0, 1.0),
                    rotation=0.0
                ),
                style=self.style
            )
        
        # Apply sync-based effects
        if self.style.precision_sync:
            sync_point = self.sync_system.get_sync_at_time(current_time)
            if sync_point and sync_point.data.get("is_downbeat"):
                # Add glow on downbeats
                glow = cv2.GaussianBlur(result, (31, 31), 0)
                result = cv2.addWeighted(result, 1.0, glow, 0.3, 0)
        
        return result
    
    def render_lyric_line(self, words: List, current_time: float, 
                         style: Any, animation_config: Any,
                         line_start: float, line_end: float,
                         audio_features: Optional[Dict] = None,
                         effects_config: Optional[Dict] = None) -> np.ndarray:
        """Override base method to use professional rendering"""
        # Extract text from words
        text = ' '.join([w.text for w in words])
        
        # Create a frame for rendering
        frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        # Calculate position
        x_position = self.resolution[0] // 2
        y_position = self._get_y_position(style.vertical_position)
        
        # Render with professional system
        line_duration = line_end - line_start
        result = self.render_professional_text(
            text=text,
            frame=frame,
            current_time=current_time - line_start,
            position=(x_position, y_position),
            line_duration=line_duration
        )
        
        # Convert to RGBA if needed
        if result.shape[2] == 3:
            rgba = np.zeros((result.shape[0], result.shape[1], 4), dtype=np.uint8)
            rgba[:, :, :3] = result
            rgba[:, :, 3] = 255  # Full opacity where text exists
            # Make black pixels transparent
            mask = np.all(result == [0, 0, 0], axis=2)
            rgba[mask, 3] = 0
            result = rgba
            
        return result
    
    def _get_y_position(self, vertical_position: str) -> int:
        """Get Y position based on vertical position setting."""
        if not hasattr(self, 'resolution'):
            self.resolution = (1920, 1080)  # Default
            
        height = self.resolution[1]
        
        if vertical_position == 'top':
            return int(height * 0.2)
        elif vertical_position == 'bottom':
            return int(height * 0.8)
        else:  # center
            return height // 2


# ==================== HELPER FUNCTIONS ====================

def create_professional_config(text: str, style: str = "kinetic_wave", 
                             bpm: float = 120, duration: float = 5.0) -> Dict[str, Any]:
    """Create a configuration for professional text rendering"""
    config = {
        "style": {
            "font_size": 72,
            "color": (255, 255, 255),
            "stroke_width": 3,
            "stroke_color": (0, 0, 0),
            "kinetic_enabled": False,
            "kinetic_animation": None,
            "path_animation": None,
            "transform_3d": None,
            "precision_sync": None,
            "use_timeline": False
        },
        "sync": {
            "bpm": bpm,
            "offset": 0.0,
            "syllables": []
        },
        "timeline": {
            "duration": duration,
            "tracks": {}
        }
    }
    
    # Configure based on style
    if style == "kinetic_wave":
        config["style"]["kinetic_enabled"] = True
        config["style"]["kinetic_animation"] = "wave"
        config["timeline"]["tracks"]["kinetic_progress"] = [
            {"time": 0.0, "value": 0.0},
            {"time": duration, "value": 1.0}  # Full animation cycle
        ]
    
    elif style == "kinetic_cascade":
        config["style"]["kinetic_enabled"] = True
        config["style"]["kinetic_animation"] = "cascade"
        config["timeline"]["tracks"]["kinetic_progress"] = [
            {"time": 0.0, "value": 0.0},
            {"time": min(1.5, duration), "value": 1.0, "interpolation": "bezier", "bezier_handles": (0, 0, 0.58, 1)}
        ]
    
    elif style == "3d_rotation":
        config["style"]["transform_3d"] = {"rotation": (0, 0, 0)}
        config["style"]["use_timeline"] = True
        config["timeline"]["tracks"]["rotation_y"] = [
            {"time": 0.0, "value": 0},
            {"time": duration, "value": 360}
        ]
    
    elif style == "path_arc":
        config["style"]["path_animation"] = {
            "type": "arc",
            "params": {
                "center": (640, 360),
                "radius": 200,
                "start_angle": -45,
                "end_angle": 45,
                "num_points": 100
            }
        }
    
    elif style == "beat_sync":
        config["style"]["precision_sync"] = {"enabled": True}
        config["sync"]["syllables"] = [
            {"text": word, "start_time": i * 0.5, "end_time": (i + 1) * 0.5}
            for i, word in enumerate(text.split())
        ]
    
    return config